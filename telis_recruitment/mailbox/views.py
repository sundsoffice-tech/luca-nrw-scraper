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
    from django.db.models import Q
    
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
    
    # Get unread count
    unread_count = EmailConversation.objects.filter(
        account__in=user_accounts,
        is_read=False
    ).exclude(status=EmailConversation.Status.TRASH).count()
    
    # Get user's labels
    from .models import EmailLabel
    labels = EmailLabel.objects.filter(
        Q(owner=request.user) | Q(is_system=True)
    )
    
    context = {
        'page_obj': page_obj,
        'folder': folder,
        'search': search,
        'accounts': user_accounts,
        'selected_account': account_id,
        'unread_count': unread_count,
        'labels': labels,
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
    
    if request.method == 'POST':
        from django.utils.html import strip_tags
        from .services.email_sender import EmailSenderService
        from .services.threading import EmailThreadingService
        import uuid
        
        # Get form data
        account_id = request.POST.get('account')
        to_emails = request.POST.get('to', '')
        cc_emails = request.POST.get('cc', '')
        subject = request.POST.get('subject', '')
        body_html = request.POST.get('body', '')
        action = request.POST.get('action', 'send')
        
        try:
            # Get account
            account = EmailAccount.objects.get(id=account_id, owner=request.user)
            
            # Parse email addresses
            to_list = [{'email': e.strip(), 'name': ''} for e in to_emails.split(',') if e.strip()]
            cc_list = [{'email': e.strip(), 'name': ''} for e in cc_emails.split(',') if e.strip()]
            
            if not to_list:
                messages.error(request, 'Bitte geben Sie mindestens einen Empfänger an.')
                return redirect('mailbox:compose')
            
            # Generate message ID
            message_id = f"<{uuid.uuid4()}@{account.email_address.split('@')[1]}>"
            
            # Find or create conversation
            conversation = EmailThreadingService.find_or_create_conversation(
                account=account,
                message_id=message_id,
                in_reply_to='',
                references='',
                subject=subject,
                from_email=account.email_address,
                to_emails=[e['email'] for e in to_list],
            )
            
            # Create email
            email = Email.objects.create(
                conversation=conversation,
                account=account,
                direction=Email.Direction.OUTBOUND,
                status=Email.Status.DRAFT if action == 'draft' else Email.Status.QUEUED,
                message_id=message_id,
                from_email=account.email_address,
                from_name=account.name,
                to_emails=to_list,
                cc_emails=cc_list,
                subject=subject,
                body_html=body_html,
                body_text=strip_tags(body_html),
                snippet=strip_tags(body_html)[:200],
            )
            
            # Handle attachments
            files = request.FILES.getlist('attachments')
            for f in files:
                from .models import EmailAttachment
                EmailAttachment.objects.create(
                    email=email,
                    file=f,
                    filename=f.name,
                    content_type=f.content_type,
                    size=f.size
                )
            
            # Send email if not draft
            if action == 'send':
                sender = EmailSenderService(account)
                success = sender.send_email(email)
                
                if success:
                    # Update conversation stats
                    EmailThreadingService.update_conversation_stats(conversation)
                    messages.success(request, 'Email erfolgreich gesendet!')
                    return redirect('mailbox:inbox')
                else:
                    messages.error(request, f'Fehler beim Senden: {email.status_detail}')
            else:
                messages.success(request, 'Email als Entwurf gespeichert.')
                return redirect('mailbox:inbox')
                
        except EmailAccount.DoesNotExist:
            messages.error(request, 'Ungültiges Email-Konto ausgewählt.')
        except Exception as e:
            messages.error(request, f'Fehler: {str(e)}')
    
    # GET request - show form
    # Get templates
    from email_templates.models import EmailTemplate
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
    original_email = get_object_or_404(Email, id=email_id)
    conversation = original_email.conversation
    
    # Check access
    user_accounts = EmailAccount.objects.filter(
        owner=request.user
    ) | EmailAccount.objects.filter(
        shared_with=request.user
    )
    
    if conversation.account not in user_accounts:
        messages.error(request, "Sie haben keine Berechtigung für diese Email.")
        return redirect('mailbox:inbox')
    
    if request.method == 'POST':
        from django.utils.html import strip_tags
        from .services.email_sender import EmailSenderService
        from .services.threading import EmailThreadingService
        import uuid
        
        body_html = request.POST.get('body', '')
        action = request.POST.get('action', 'send')
        
        try:
            # Generate message ID
            message_id = f"<{uuid.uuid4()}@{conversation.account.email_address.split('@')[1]}>"
            
            # Build references
            references = original_email.references
            if original_email.message_id:
                references = f"{references} {original_email.message_id}".strip()
            
            # Create reply email
            reply_email = Email.objects.create(
                conversation=conversation,
                account=conversation.account,
                direction=Email.Direction.OUTBOUND,
                status=Email.Status.DRAFT if action == 'draft' else Email.Status.QUEUED,
                message_id=message_id,
                in_reply_to=original_email.message_id,
                references=references,
                from_email=conversation.account.email_address,
                from_name=conversation.account.name,
                to_emails=[{'email': original_email.from_email, 'name': original_email.from_name}],
                subject=f"Re: {original_email.subject}" if not original_email.subject.startswith('Re:') else original_email.subject,
                body_html=body_html,
                body_text=strip_tags(body_html),
                snippet=strip_tags(body_html)[:200],
            )
            
            # Handle attachments
            files = request.FILES.getlist('attachments')
            for f in files:
                from .models import EmailAttachment
                EmailAttachment.objects.create(
                    email=reply_email,
                    file=f,
                    filename=f.name,
                    content_type=f.content_type,
                    size=f.size
                )
            
            # Send email if not draft
            if action == 'send':
                sender = EmailSenderService(conversation.account)
                success = sender.send_email(reply_email)
                
                if success:
                    # Update conversation stats
                    EmailThreadingService.update_conversation_stats(conversation)
                    messages.success(request, 'Antwort erfolgreich gesendet!')
                    return redirect('mailbox:conversation', conversation_id=conversation.id)
                else:
                    messages.error(request, f'Fehler beim Senden: {reply_email.status_detail}')
            else:
                messages.success(request, 'Antwort als Entwurf gespeichert.')
                return redirect('mailbox:conversation', conversation_id=conversation.id)
                
        except Exception as e:
            messages.error(request, f'Fehler: {str(e)}')
    
    # GET - show reply form with quoted original
    quoted_html = f"""
    <br><br>
    <div style="border-left: 2px solid #ccc; padding-left: 10px; margin-left: 10px; color: #666;">
        <p>Am {original_email.sent_at or original_email.received_at} schrieb {original_email.from_name or original_email.from_email}:</p>
        {original_email.body_html or original_email.body_text}
    </div>
    """
    
    # Get signatures
    signatures = EmailSignature.objects.filter(user=request.user)
    
    context = {
        'original_email': original_email,
        'conversation': conversation,
        'quoted_content': quoted_html,
        'signatures': signatures,
    }
    return render(request, 'mailbox/reply.html', context)


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
