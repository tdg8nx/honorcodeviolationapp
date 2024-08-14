import os
from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp
from django.test import TestCase
from django.core.exceptions import ValidationError
from .models import HonorCodeViolation
from datetime import date
from django.urls import reverse
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth.models import User
from django.contrib.auth.models import Group
from mainapp.forms import HonorCodeViolationForm

class HonorCodeViolationModelTests(TestCase):
    #validates string representation of honor code violation
    def test_model_str(self):
        violation = HonorCodeViolation(name="Test Name", date_of_incident=date.today(), description="Test Description")
        self.assertEqual(str(violation), f"Violation by Test Name on {date.today()}")

    #validates model throws ValidationError when an invalid date format is provided
    def test_invalid_date(self):
        violation = HonorCodeViolation(date_of_incident="not a date", description="Test")
        with self.assertRaises(ValidationError):
            violation.full_clean()

class IndexViewTests(TestCase):
    #sets up necessary objects for tests
    def setUp(self):
        site = Site.objects.create(domain='test.com', name='test')
        app = SocialApp.objects.create(provider='google', name='Google', client_id='client_id', secret='secret', key='')
        app.sites.add(site)
        settings.SITE_ID = site.id

    #verifies that the index view is accessible
    def test_index_view_status_code(self):
        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)
    #tests admin access without authentication to check if model incorrectly allows access to admin site
    def test_admin_login_view_access_without_authentication(self):
        response = self.client.get(reverse('admin_dashboard_url'))
        self.assertEqual(response.status_code, 200)
class UserLoginAndFileUploadTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.client.login(username='testuser', password='12345')

    #ensures that once logged in, user can access the user dashboard
    def test_login_screen(self):
        response = self.client.get(reverse('user_dashboard_url'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'user_dashboard.html')

    #validates file upload functionality for .txt files
    def test_upload_txt_file(self):
        test_file_path = os.path.join(settings.BASE_DIR, 'mainapp', 'test_files', 'test.txt')

        with open(test_file_path, 'rb') as file:
            response = self.client.post(reverse('user_dashboard_url'), {
                'name': 'Test Name',
                'date_of_incident': '2024-03-01',
                'description': 'Test Description',
                'file': SimpleUploadedFile(file.name, file.read(), content_type='text/plain'),
            })
            self.assertEqual(response.status_code, 302)

    #validates file upload functionality for .pdf files
    def test_upload_pdf_file(self):
        test_file_path = os.path.join(settings.BASE_DIR, 'mainapp', 'test_files', 'test.pdf')

        with open(test_file_path, 'rb') as file:
            response = self.client.post(reverse('user_dashboard_url'), {
                'name': 'Test Name',
                'date_of_incident': '2024-03-01',
                'description': 'Test Description',
                'file': SimpleUploadedFile(file.name, file.read(), content_type='application/pdf'),
            })
            self.assertEqual(response.status_code, 302)

    #validates file upload functionality for .jpg files
    def test_upload_jpg_file(self):
        test_file_path = os.path.join(settings.BASE_DIR, 'mainapp', 'test_files', 'test.jpg')

        with open(test_file_path, 'rb') as file:
            response = self.client.post(reverse('user_dashboard_url'), {
                'name': 'Test Name',
                'date_of_incident': '2024-03-01',
                'description': 'Test Description',
                'file': SimpleUploadedFile(file.name, file.read(), content_type='image/jpeg'),
            })
            self.assertEqual(response.status_code, 302)

    #ensures user cannot enter empty form submission
    def test_empty_field_submission(self):
        post_url = reverse('user_dashboard_url')
        response = self.client.post(post_url, {
            'name': '',
            'date_of_incident': '',
            'description': '',
        })

        form = response.context['form']
        self.assertFalse(form.is_valid(), "Form should be invalid if required fields are missing.")


        self.assertNotIn('name', form.errors, "Unexpected validation error for 'name' field.")
        self.assertIn('date_of_incident', form.errors, "Expected 'date_of_incident' field error not found.")
        self.assertIn('This field is required.', form.errors['date_of_incident'],
                      "Missing or incorrect error message for 'date_of_incident' field.")
        self.assertIn('description', form.errors, "Expected 'description' field error not found.")
        self.assertIn('This field is required.', form.errors['description'],
                      "Missing or incorrect error message for 'description' field.")
class RoleBasedAccessTests(TestCase):
    def setUp(self):
        self.site_admin = User.objects.create_user(username='siteadmin', password='testpass123')
        site_admin_group = Group.objects.create(name='Site Admin')
        site_admin_group.user_set.add(self.site_admin)
        self.assertTrue(self.site_admin.groups.filter(name='Site Admin').exists())

    #test common user access to admin-specific page (should not be allowed)
    def test_common_user_access(self):
        self.client.login(username='commonuser', password='testpass123')
        response = self.client.get(reverse('admin_account_details'))
        self.assertNotEqual(response.status_code, 200)

    #test admin access to admin specific page (should be allowed)
    def test_site_admin_access(self):
        self.client.login(username='siteadmin', password='testpass123')
        response = self.client.get(reverse('admin_account_details'))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse('admin:index'))
        self.assertNotEqual(response.status_code, 200)


class AnonymousSubmissionTests(TestCase):
    #verify that no information about anonymous users are retained
    def test_anonymous_submission_no_user_retained(self):
        test_file_path = os.path.join(settings.BASE_DIR, 'mainapp', 'test_files', 'test.txt')
        submit_url = reverse('user_dashboard_url')

        with open(test_file_path, 'rb') as file:
            response = self.client.post(submit_url, {
                'text': 'Anonymous report content',
                'file': SimpleUploadedFile(file.name, file.read(), content_type='text/plain')
            }, follow=True)

        self.assertIn(response.status_code, [200, 302])

        violation = HonorCodeViolation.objects.last()
        if violation:
            self.assertIsNone(violation.user, "User should be None for anonymous submissions")
            self.assertEqual(violation.description, 'Anonymous report content')

#create integration tests here

#consider using selenium after testing document is turned in -- communicate with team