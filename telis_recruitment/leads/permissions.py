"""
Permission classes for role-based access control in TELIS CRM.

Three user groups with different access levels:
- Admin: Full access
- Manager: Reports and team overview
- Telefonist: Only assigned leads and call functionality
"""

from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):
    """
    Permission class for Admin users.
    
    Admins have full access to:
    - View, edit, delete all leads
    - Manage users (create, edit, deactivate)
    - Change scraper settings
    - View reports/analytics
    - System settings
    
    Superusers always have access.
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and \
               (request.user.is_superuser or \
                request.user.groups.filter(name='Admin').exists())


class IsManager(BasePermission):
    """
    Permission class for Manager users.
    
    Managers can:
    - View all leads (read-only, except status updates)
    - View team performance
    - View reports/analytics
    - Assign leads to Telefonisten
    - No user management
    
    Superusers always have access.
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and \
               (request.user.is_superuser or \
                request.user.groups.filter(name__in=['Admin', 'Manager']).exists())


class IsTelefonist(BasePermission):
    """
    Permission class for Telefonist users.
    
    Telefonisten can:
    - View only assigned leads
    - Call leads and log results
    - View their own statistics
    - No admin functions
    
    Superusers always have access.
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and \
               (request.user.is_superuser or \
                request.user.groups.filter(name__in=['Admin', 'Manager', 'Telefonist']).exists())

