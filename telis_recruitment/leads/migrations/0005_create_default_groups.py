"""
Data migration to create default user groups and assign superusers to Admin group.

This migration ensures that:
1. The three required groups (Admin, Manager, Telefonist) exist
2. All superusers are automatically added to the Admin group
"""

from django.db import migrations


def create_groups_and_assign_superusers(apps, schema_editor):
    """Create default groups and assign superusers to Admin group."""
    Group = apps.get_model('auth', 'Group')
    User = apps.get_model('auth', 'User')
    Permission = apps.get_model('auth', 'Permission')
    ContentType = apps.get_model('contenttypes', 'ContentType')
    
    # Get content types for our models
    try:
        lead_ct = ContentType.objects.get(app_label='leads', model='lead')
        calllog_ct = ContentType.objects.get(app_label='leads', model='calllog')
        emaillog_ct = ContentType.objects.get(app_label='leads', model='emaillog')
    except ContentType.DoesNotExist:
        # Models don't exist yet, skip permission assignment
        return
    
    # === CREATE ADMIN GROUP ===
    admin_group, created = Group.objects.get_or_create(name='Admin')
    
    # Admin gets all permissions on Lead, CallLog, EmailLog
    admin_permissions = Permission.objects.filter(
        content_type__in=[lead_ct, calllog_ct, emaillog_ct]
    )
    admin_group.permissions.set(admin_permissions)
    
    # Also add user management permissions
    try:
        user_ct = ContentType.objects.get(app_label='auth', model='user')
        user_permissions = Permission.objects.filter(content_type=user_ct)
        admin_group.permissions.add(*user_permissions)
    except ContentType.DoesNotExist:
        pass
    
    # === CREATE MANAGER GROUP ===
    manager_group, created = Group.objects.get_or_create(name='Manager')
    
    # Manager can view all leads, view/add call logs and email logs
    manager_permissions = Permission.objects.filter(
        content_type__in=[lead_ct, calllog_ct, emaillog_ct],
        codename__in=[
            'view_lead',
            'change_lead',
            'view_calllog',
            'add_calllog',
            'view_emaillog',
            'add_emaillog',
        ]
    )
    manager_group.permissions.set(manager_permissions)
    
    # === CREATE TELEFONIST GROUP ===
    telefonist_group, created = Group.objects.get_or_create(name='Telefonist')
    
    # Telefonist can view assigned leads, add call logs
    telefonist_permissions = Permission.objects.filter(
        content_type__in=[lead_ct, calllog_ct],
        codename__in=[
            'view_lead',
            'view_calllog',
            'add_calllog',
        ]
    )
    telefonist_group.permissions.set(telefonist_permissions)
    
    # === ADD SUPERUSERS TO ADMIN GROUP ===
    superusers = User.objects.filter(is_superuser=True)
    for superuser in superusers:
        if not superuser.groups.filter(name='Admin').exists():
            superuser.groups.add(admin_group)


def reverse_migration(apps, schema_editor):
    """Reverse the migration by removing the groups."""
    Group = apps.get_model('auth', 'Group')
    # We don't delete groups on reverse to avoid data loss
    # Groups will remain but can be manually deleted if needed
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('leads', '0004_scraperrun_scraperconfig'),
        ('auth', '__latest__'),
        ('contenttypes', '__latest__'),
    ]

    operations = [
        migrations.RunPython(create_groups_and_assign_superusers, reverse_migration),
    ]
