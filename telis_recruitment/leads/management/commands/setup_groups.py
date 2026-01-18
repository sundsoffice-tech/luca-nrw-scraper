"""
Management command to set up user groups and permissions for TELIS CRM.

Usage:
    python manage.py setup_groups

This command is idempotent and can be run multiple times without issues.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from leads.models import Lead, CallLog, EmailLog


class Command(BaseCommand):
    help = 'Sets up user groups (Admin, Manager, Telefonist) with appropriate permissions'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Setting up user groups...'))
        
        # Get content types
        lead_ct = ContentType.objects.get_for_model(Lead)
        calllog_ct = ContentType.objects.get_for_model(CallLog)
        emaillog_ct = ContentType.objects.get_for_model(EmailLog)
        
        # === ADMIN GROUP ===
        admin_group, created = Group.objects.get_or_create(name='Admin')
        if created:
            self.stdout.write(self.style.SUCCESS('✓ Created Admin group'))
        else:
            self.stdout.write('✓ Admin group already exists')
        
        # Admin gets all permissions on Lead, CallLog, EmailLog
        admin_permissions = Permission.objects.filter(
            content_type__in=[lead_ct, calllog_ct, emaillog_ct]
        )
        admin_group.permissions.set(admin_permissions)
        
        # Also add user management permissions
        from django.contrib.auth.models import User
        user_ct = ContentType.objects.get_for_model(User)
        user_permissions = Permission.objects.filter(content_type=user_ct)
        admin_group.permissions.add(*user_permissions)
        
        self.stdout.write(f'  → Assigned {admin_permissions.count()} permissions to Admin')
        
        # === MANAGER GROUP ===
        manager_group, created = Group.objects.get_or_create(name='Manager')
        if created:
            self.stdout.write(self.style.SUCCESS('✓ Created Manager group'))
        else:
            self.stdout.write('✓ Manager group already exists')
        
        # Manager can view all leads, view/add call logs and email logs
        manager_permissions = Permission.objects.filter(
            content_type__in=[lead_ct, calllog_ct, emaillog_ct],
            codename__in=[
                'view_lead',
                'change_lead',  # For status updates and assignments
                'view_calllog',
                'add_calllog',
                'view_emaillog',
                'add_emaillog',
            ]
        )
        manager_group.permissions.set(manager_permissions)
        self.stdout.write(f'  → Assigned {manager_permissions.count()} permissions to Manager')
        
        # === TELEFONIST GROUP ===
        telefonist_group, created = Group.objects.get_or_create(name='Telefonist')
        if created:
            self.stdout.write(self.style.SUCCESS('✓ Created Telefonist group'))
        else:
            self.stdout.write('✓ Telefonist group already exists')
        
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
        self.stdout.write(f'  → Assigned {telefonist_permissions.count()} permissions to Telefonist')
        
        # === ADD SUPERUSERS TO ADMIN GROUP ===
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Adding superusers to Admin group...')
        from django.contrib.auth.models import User
        superusers = User.objects.filter(is_superuser=True)
        superusers_added = 0
        for superuser in superusers:
            if not superuser.groups.filter(name='Admin').exists():
                superuser.groups.add(admin_group)
                superusers_added += 1
                self.stdout.write(self.style.SUCCESS(f'  ✓ Added superuser "{superuser.username}" to Admin group'))
            else:
                self.stdout.write(f'  → Superuser "{superuser.username}" already in Admin group')
        
        if superusers_added == 0 and superusers.count() == 0:
            self.stdout.write(self.style.WARNING('  ⚠ No superusers found. Create one with: python manage.py createsuperuser'))
        
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('✅ User groups setup complete!'))
        self.stdout.write('\nGroup Summary:')
        self.stdout.write(f'  • Admin: Full access ({admin_group.permissions.count()} permissions)')
        self.stdout.write(f'  • Manager: Reports + team overview ({manager_group.permissions.count()} permissions)')
        self.stdout.write(f'  • Telefonist: Assigned leads only ({telefonist_group.permissions.count()} permissions)')
        self.stdout.write(f'\nSuperusers in Admin group: {superusers.filter(groups__name="Admin").count()}')
