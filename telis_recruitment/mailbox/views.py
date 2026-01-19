"""
Web views for Mailbox app
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.core.paginator import Paginator

from .models import EmailAccount, EmailConversation, Email, EmailSignature, QuickReply
from email_templates.models import EmailTemplate


@login_required
def inbox(request):
    """
    Hauptansicht: Posteingang
    
    Supports filtering by:
    - folder: all, unread, starred, sent, drafts, scheduled, trash
    - search query
    """
    # Get user's accounts
    user_accounts = EmailAccount.objects.filter(
        owner=request.user, is_active=True
    ) | EmailAccount.objects.filter(
        shared_with=request.user, is_active=True
    )
    
    # Get filter parameters
    folder = request.GET.get('folder', 'all')
    search = request.GET.get('search', '')
    account_id = request.GET.get('account', '')
    
    # Base queryset
    conversations = EmailConversation.objects.filter(
        account__in=user_accounts
    ).select_related('account', 'lead', 'assigned_to')
    
    # Apply filters
    if folder == 'unread':
        conversations = conversations.filter(is_read=False)
    elif folder == 'starred':
        conversations = conversations.filter(is_starred=True)
    elif folder == 'sent':
        # Show conversations with outbound messages
        conversations = conversations.filter(last_outbound_at__isnull=False)
    elif folder == 'trash':
        conversations = conversations.filter(status=EmailConversation.Status.TRASH)
    else:  # 'all'
        conversations = conversations.exclude(status=EmailConversation.Status.TRASH)
    
    # Apply account filter
    if account_id:
        conversations = conversations.filter(account_id=account_id)
    
    # Apply search
    if search:
        conversations = conversations.filter(
            subject__icontains=search
        ) | conversations.filter(
            contact_email__icontains=search
        )
    
    # Paginate
    paginator = Paginator(conversations, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'folder': folder,
        'search': search,
        'accounts': user_accounts,
        'selected_account': account_id,
    }
    
    return render(request, 'mailbox/inbox.html', context)


@login_required
def conversation_detail(request, conversation_id):
    """Konversations-Thread anzeigen"""
    conversation = get_object_or_404(EmailConversation, id=conversation_id)
    
    # Check access
    user_accounts = EmailAccount.objects.filter(
        owner=request.user
    ) | EmailAccount.objects.filter(
        shared_with=request.user
    )
    
    if conversation.account not in user_accounts:
        messages.error(request, "Sie haben keine Berechtigung für diese Konversation.")
        return redirect('mailbox:inbox')
    
    # Get messages in conversation
    emails = conversation.messages.all().select_related(
        'account', 'template_used'
    ).prefetch_related('attachments')
    
    # Mark as read
    if not conversation.is_read:
        conversation.is_read = True
        conversation.save(update_fields=['is_read'])
        
        # Mark inbound messages as read
        conversation.messages.filter(
            direction=Email.Direction.INBOUND,
            is_read=False
        ).update(is_read=True)
    
    context = {
        'conversation': conversation,
        'emails': emails,
    }
    
    return render(request, 'mailbox/thread_view.html', context)


@login_required
def compose(request):
    """Neue Email schreiben"""
    # Get user's accounts
    accounts = EmailAccount.objects.filter(
        owner=request.user, is_active=True
    )
    
    # Get templates
    templates = EmailTemplate.objects.filter(is_active=True)
    
    # Get signatures
    signatures = EmailSignature.objects.filter(user=request.user)
    
    # Get quick replies
    quick_replies = QuickReply.objects.filter(
        owner=request.user
    ) | QuickReply.objects.filter(is_shared=True)
    
    # Pre-fill from query params
    to_email = request.GET.get('to', '')
    lead_id = request.GET.get('lead', '')
    
    context = {
        'accounts': accounts,
        'templates': templates,
        'signatures': signatures,
        'quick_replies': quick_replies,
        'to_email': to_email,
        'lead_id': lead_id,
    }
    
    return render(request, 'mailbox/compose.html', context)


@login_required
def reply(request, email_id):
    """Auf Email antworten"""
    email = get_object_or_404(Email, id=email_id)
    conversation = email.conversation
    
    # Check access
    user_accounts = EmailAccount.objects.filter(
        owner=request.user
    ) | EmailAccount.objects.filter(
        shared_with=request.user
    )
    
    if conversation.account not in user_accounts:
        messages.error(request, "Sie haben keine Berechtigung für diese Email.")
        return redirect('mailbox:inbox')
    
    # Redirect to conversation with reply mode
    return redirect('mailbox:conversation', conversation_id=conversation.id)


@login_required
def forward(request, email_id):
    """Email weiterleiten"""
    email = get_object_or_404(Email, id=email_id)
    
    # Check access
    user_accounts = EmailAccount.objects.filter(
        owner=request.user
    ) | EmailAccount.objects.filter(
        shared_with=request.user
    )
    
    if email.account not in user_accounts:
        messages.error(request, "Sie haben keine Berechtigung für diese Email.")
        return redirect('mailbox:inbox')
    
    # Redirect to compose with forward data
    return redirect('mailbox:compose')


@login_required
def account_settings(request):
    """Email-Account Einstellungen"""
    accounts = EmailAccount.objects.filter(owner=request.user)
    
    context = {
        'accounts': accounts,
    }
    
    return render(request, 'mailbox/settings.html', context)


@login_required
def signatures(request):
    """Signaturen verwalten"""
    user_signatures = EmailSignature.objects.filter(user=request.user)
    
    context = {
        'signatures': user_signatures,
    }
    
    return render(request, 'mailbox/signatures.html', context)


@login_required
def quick_replies_view(request):
    """Schnellantworten verwalten"""
    user_quick_replies = QuickReply.objects.filter(owner=request.user)
    shared_quick_replies = QuickReply.objects.filter(is_shared=True).exclude(owner=request.user)
    
    context = {
        'user_quick_replies': user_quick_replies,
        'shared_quick_replies': shared_quick_replies,
    }
    
    return render(request, 'mailbox/quick_replies.html', context)
