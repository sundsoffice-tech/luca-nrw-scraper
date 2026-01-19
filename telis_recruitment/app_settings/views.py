from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import UserPreferences, SystemSettings


@login_required
def settings_dashboard(request):
    """Main settings dashboard"""
    user_prefs, _ = UserPreferences.objects.get_or_create(user=request.user)
    system_settings = SystemSettings.get_settings()
    
    # Check if user is admin
    is_admin = request.user.groups.filter(name='Admin').exists()
    
    context = {
        'user_prefs': user_prefs,
        'system_settings': system_settings,
        'is_admin': is_admin,
    }
    
    return render(request, 'app_settings/dashboard.html', context)


@login_required
def user_preferences_view(request):
    """User-specific preferences"""
    user_prefs, _ = UserPreferences.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        # Update user preferences
        user_prefs.theme = request.POST.get('theme', 'dark')
        user_prefs.language = request.POST.get('language', 'de')
        user_prefs.email_notifications = request.POST.get('email_notifications') == 'on'
        user_prefs.items_per_page = int(request.POST.get('items_per_page', 25))
        user_prefs.default_lead_view = request.POST.get('default_lead_view', 'list')
        user_prefs.save()
        
        messages.success(request, 'Ihre Einstellungen wurden erfolgreich gespeichert.')
        return redirect('app_settings:user-preferences')
    
    context = {
        'user_prefs': user_prefs,
    }
    
    return render(request, 'app_settings/user_preferences.html', context)


@login_required
def system_settings_view(request):
    """System-wide settings (admin only)"""
    # Check if user is admin
    if not request.user.groups.filter(name='Admin').exists():
        messages.error(request, 'Sie haben keine Berechtigung für diese Seite.')
        return redirect('app_settings:dashboard')
    
    system_settings = SystemSettings.get_settings()
    
    if request.method == 'POST':
        # Update system settings
        system_settings.site_name = request.POST.get('site_name', 'TELIS CRM')
        system_settings.site_url = request.POST.get('site_url', '')
        system_settings.admin_email = request.POST.get('admin_email', '')
        system_settings.enable_email_module = request.POST.get('enable_email_module') == 'on'
        system_settings.enable_scraper = request.POST.get('enable_scraper') == 'on'
        system_settings.enable_ai_features = request.POST.get('enable_ai_features') == 'on'
        system_settings.enable_landing_pages = request.POST.get('enable_landing_pages') == 'on'
        system_settings.maintenance_mode = request.POST.get('maintenance_mode') == 'on'
        system_settings.maintenance_message = request.POST.get('maintenance_message', '')
        system_settings.session_timeout_minutes = int(request.POST.get('session_timeout_minutes', 60))
        system_settings.max_login_attempts = int(request.POST.get('max_login_attempts', 5))
        system_settings.save()
        
        messages.success(request, 'Systemeinstellungen wurden erfolgreich gespeichert.')
        return redirect('app_settings:system-settings')
    
    context = {
        'system_settings': system_settings,
    }
    
    return render(request, 'app_settings/system_settings.html', context)


@login_required
def integrations_view(request):
    """Integration settings overview"""
    # Check if user is admin
    if not request.user.groups.filter(name='Admin').exists():
        messages.error(request, 'Sie haben keine Berechtigung für diese Seite.')
        return redirect('app_settings:dashboard')
    
    context = {
        'has_brevo': True,  # Check if Brevo is configured
        'has_ai': True,     # Check if AI is configured
    }
    
    return render(request, 'app_settings/integrations.html', context)
