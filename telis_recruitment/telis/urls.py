"""
URL configuration for telis project.

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
from django.contrib.auth import views as auth_views
from django.urls import path, include
from leads.views import landing_page, phone_dashboard

urlpatterns = [
    # Public pages
    path('', landing_page, name='landing-page'),
    path('phone/', phone_dashboard, name='phone-dashboard'),
    
    # Public landing pages (pages app)
    path('p/', include('pages.public_urls')),
    
    # Authentication
    path('login/', auth_views.LoginView.as_view(template_name='auth/login.html'), name='login'),
    path('crm/login/', auth_views.LoginView.as_view(
        template_name='crm/login.html',
        redirect_authenticated_user=True
    ), name='crm-login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='crm-login'), name='logout'),
    
    # Scraper Control (new dedicated app)
    path('crm/scraper/', include('scraper_control.urls')),
    
    # Pages app (builder interface - staff only)
    path('crm/pages/', include('pages.urls')),
    
    # Email Templates (web interface)
    path('crm/email-templates/', include('email_templates.urls')),
    
    # Mailbox (email inbox/outbox system)
    path('crm/mailbox/', include('mailbox.urls')),
    
    # Reports (analytics and reporting)
    path('crm/reports/', include('reports.urls')),
    
    # CRM (protected)
    path('crm/', include('leads.crm_urls')),
    
    # API
    path('api/', include('leads.urls')),
    path('api/email-templates/', include('email_templates.api_urls')),
    
    # Django Admin
    path('admin/', admin.site.urls),
]
