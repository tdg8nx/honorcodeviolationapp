from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.views import View
from allauth.socialaccount.models import SocialAccount
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView

from django.shortcuts import render, redirect
from .forms import HonorCodeViolationForm
from .models import HonorCodeViolation

from django.core.mail import send_mail

# Imported + printed on view!
from django.contrib.sites.shortcuts import get_current_site


def violation_detail(request, id):
    violation = get_object_or_404(HonorCodeViolation, id=id)
    if violation.status == 'new':
        violation.status = 'in_progress'
        violation.save()
    return render(request, 'violation_detail.html', {'violation': violation})


def mark_resolved(request, id):
    violation = get_object_or_404(HonorCodeViolation, id=id)
    if request.method == 'POST':
        resolution_notes = request.POST.get('resolution_notes')
        violation.resolution_notes = resolution_notes
        violation.status = 'resolved'

        if violation.user and violation.user.is_authenticated:
            send_mail(
                'Form Reviewed',
                'Your form has been reviewed:\n Resolution Notes: ' + resolution_notes,
                'anhtuleschool@gmail.com',  # From email
                [violation.user.email],  # To email list
                fail_silently=True,
            )
        violation.save()
    return HttpResponseRedirect(reverse('admin_dashboard_url'))


@login_required
def account_details(request):
    return render(request, 'account_details.html', {'user': request.user})


@login_required
def admin_account_details(request):
    return render(request, 'admin_account_details.html', {'user': request.user})


class UserViolationsView(LoginRequiredMixin, ListView):
    model = HonorCodeViolation
    template_name = 'user_violations.html'
    context_object_name = 'violations'

    def get_queryset(self):
        return HonorCodeViolation.objects.filter(user=self.request.user)


class DeleteViolationView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        violation = get_object_or_404(HonorCodeViolation, pk=self.kwargs['id'], user=request.user)
        violation.delete()
        messages.add_message(request, messages.SUCCESS, 'Violation has been deleted.')
        return redirect('user_violations')


class IndexView(View):
    def get(self, request):
        is_site_admin = request.user.groups.filter(name='site_admin').exists()
        current_site = get_current_site(request)
        context = {
            'is_site_admin': is_site_admin,
            'current_site': current_site
        }
        return render(request, 'index.html', context)


class UserLoginView(View):
    def get(self, request):
        form = HonorCodeViolationForm()
        return render(request, 'user_dashboard.html', {'form': form})

    def post(self, request):
        form = HonorCodeViolationForm(request.POST, request.FILES)
        if form.is_valid():
            violation = form.save(commit=False)  # Save the form temporarily without committing to the database
            if request.user.is_authenticated:
                violation.user = request.user  # Set the user of the violation to the currently logged-in user
            violation.save()  # Now save the violation to the database

            if request.user.is_authenticated:
                send_mail(
                    'Form Received',
                    'Your form has been received.',
                    'anhtuleschool@gmail.com',  # From email
                    [request.user.email],  # To email list
                    fail_silently=True,)

            return redirect('index')  # Redirect to a confirmation page or back to form
        return render(request, 'user_dashboard.html', {'form': form})


class AdminLoginView(View):
    def get(self, request):
        violations = HonorCodeViolation.objects.all()
        
        # sort violations by date
        violations = sorted(violations, key=lambda x: x.date_of_incident, reverse=True)

        return render(request, 'admin_dashboard.html', {'violations': violations})
