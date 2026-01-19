"""
Context processors for Mailbox app
"""

def unread_email_count(request):
    """
    Add unread email count to template context for sidebar badge.
    """
    count = 0
    
    if request.user.is_authenticated:
        try:
            from mailbox.models import EmailAccount, EmailConversation
            from django.db.models import Q
            
            # Get user's accounts
            user_accounts = EmailAccount.objects.filter(
                Q(owner=request.user) | Q(shared_with=request.user),
                is_active=True
            )
            
            # Count unread conversations
            count = EmailConversation.objects.filter(
                account__in=user_accounts,
                is_read=False
            ).exclude(
                status='trash'
            ).count()
        except (ImportError, AttributeError, Exception):
            # Silently fail if:
            # - mailbox app not installed (ImportError)
            # - models not properly configured (AttributeError)
            # - database issues (Exception as fallback)
            pass
    
    return {'unread_email_count': count}
