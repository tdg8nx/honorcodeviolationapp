"""
URL configuration for mysite project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from django.contrib.auth.views import LogoutView
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

from mainapp import views
from mainapp.views import AdminLoginView, UserLoginView, IndexView, UserViolationsView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('violations/<int:id>/', views.violation_detail, name='violation_detail'),
    path('', IndexView.as_view(), name='index'),
    path('user-login/', UserLoginView.as_view(), name='user_dashboard_url'),
    path('admin-login/', AdminLoginView.as_view(), name='admin_dashboard_url'),
    path('accounts/', include('allauth.urls')),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('violations/<int:id>/resolve/', views.mark_resolved, name='mark_resolved'),
    path('account_details/', views.account_details, name='account_details'),
    path('admin_account_details/', views.admin_account_details, name='admin_account_details'),
    path('my-violations/', UserViolationsView.as_view(), name='user_violations'),
    path('violations/<int:id>/delete/', views.DeleteViolationView.as_view(), name='violation_delete'),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
