"""
API views for Mailbox app
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.utils import timezone
import uuid
import logging

from .models import (
    EmailAccount, EmailConversation, Email,
    EmailLabel, EmailSignature, QuickReply
)
from .serializers import (
    EmailAccountSerializer,
    EmailConversationListSerializer,
    EmailConversationDetailSerializer,
    EmailListSerializer,
    EmailDetailSerializer,
    EmailLabelSerializer,
    EmailSignatureSerializer,
    QuickReplySerializer,
    EmailComposeSerializer,
    EmailReplySerializer
)
from .services.email_sender import EmailSenderService
from .services.email_receiver import EmailReceiverService
from .services.threading import EmailThreadingService
from .services.webhook_handlers import BrevoWebhookHandler

logger = logging.getLogger(__name__)


class EmailAccountViewSet(viewsets.ModelViewSet):
    """API für Email-Accounts"""
    serializer_class = EmailAccountSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # Return user's own accounts and shared accounts
        return EmailAccount.objects.filter(
            owner=self.request.user
        ) | EmailAccount.objects.filter(
            shared_with=self.request.user
        )
    
    @action(detail=True, methods=['post'])
    def sync(self, request, pk=None):
        """Synchronize emails from this account"""
        account = self.get_object()
        
        try:
            receiver = EmailReceiverService(account)
            emails = receiver.fetch_new_emails()
            receiver.disconnect()
            
            return Response({
                'success': True,
                'fetched_count': len(emails),
                'message': f'{len(emails)} neue Emails abgerufen'
            })
        except Exception as e:
            logger.error(f"Error syncing account {account.id}: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ConversationViewSet(viewsets.ModelViewSet):
    """API für Konversationen"""
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # Get user's accounts
        user_accounts = EmailAccount.objects.filter(
            owner=self.request.user
        ) | EmailAccount.objects.filter(
            shared_with=self.request.user
        )
        
        return EmailConversation.objects.filter(
            account__in=user_accounts
        )
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return EmailConversationDetailSerializer
        return EmailConversationListSerializer
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Mark conversation as read"""
        conversation = self.get_object()
        conversation.is_read = True
        conversation.save(update_fields=['is_read'])
        
        # Mark all inbound messages as read
        conversation.messages.filter(
            direction=Email.Direction.INBOUND,
            is_read=False
        ).update(is_read=True)
        
        return Response({'success': True})
    
    @action(detail=True, methods=['post'])
    def mark_unread(self, request, pk=None):
        """Mark conversation as unread"""
        conversation = self.get_object()
        conversation.is_read = False
        conversation.save(update_fields=['is_read'])
        
        return Response({'success': True})
    
    @action(detail=True, methods=['post'])
    def star(self, request, pk=None):
        """Toggle star on conversation"""
        conversation = self.get_object()
        conversation.is_starred = not conversation.is_starred
        conversation.save(update_fields=['is_starred'])
        
        return Response({'success': True, 'is_starred': conversation.is_starred})
    
    @action(detail=True, methods=['post'])
    def archive(self, request, pk=None):
        """Toggle archive on conversation"""
        conversation = self.get_object()
        conversation.is_archived = not conversation.is_archived
        conversation.save(update_fields=['is_archived'])
        
        return Response({'success': True, 'is_archived': conversation.is_archived})
    
    @action(detail=True, methods=['post'])
    def assign(self, request, pk=None):
        """Assign conversation to user"""
        conversation = self.get_object()
        user_id = request.data.get('user_id')
        
        if user_id:
            from django.contrib.auth.models import User
            try:
                user = User.objects.get(id=user_id)
                conversation.assigned_to = user
                conversation.save(update_fields=['assigned_to'])
                return Response({'success': True})
            except User.DoesNotExist:
                return Response({
                    'success': False,
                    'error': 'User not found'
                }, status=status.HTTP_404_NOT_FOUND)
        else:
            # Unassign
            conversation.assigned_to = None
            conversation.save(update_fields=['assigned_to'])
            return Response({'success': True})


class EmailViewSet(viewsets.ModelViewSet):
    """API für einzelne Emails"""
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # Get user's accounts
        user_accounts = EmailAccount.objects.filter(
            owner=self.request.user
        ) | EmailAccount.objects.filter(
            shared_with=self.request.user
        )
        
        return Email.objects.filter(
            account__in=user_accounts
        )
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return EmailDetailSerializer
        return EmailListSerializer
    
    @action(detail=False, methods=['post'])
    def send(self, request):
        """Send a new email"""
        serializer = EmailComposeSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        
        try:
            # Get account
            account = EmailAccount.objects.get(
                id=data['account_id'],
                owner=request.user
            )
            
            # Generate message ID
            message_id = f"<{uuid.uuid4()}@{account.email_address.split('@')[1]}>"
            
            # Convert email lists to proper format
            to_emails = [{'email': email, 'name': ''} for email in data['to_emails']]
            cc_emails = [{'email': email, 'name': ''} for email in data.get('cc_emails', [])]
            bcc_emails = [{'email': email, 'name': ''} for email in data.get('bcc_emails', [])]
            
            # Find or create conversation
            conversation = EmailThreadingService.find_or_create_conversation(
                account=account,
                message_id=message_id,
                in_reply_to=data.get('in_reply_to', ''),
                references='',
                subject=data['subject'],
                from_email=account.email_address,
                to_emails=data['to_emails'],
            )
            
            # Create email record
            email = Email.objects.create(
                conversation=conversation,
                account=account,
                direction=Email.Direction.OUTBOUND,
                message_id=message_id,
                in_reply_to=data.get('in_reply_to', ''),
                from_email=account.email_address,
                from_name=account.name,
                to_emails=to_emails,
                cc_emails=cc_emails,
                bcc_emails=bcc_emails,
                subject=data['subject'],
                body_html=data.get('body_html', ''),
                body_text=data.get('body_text', ''),
                status=Email.Status.QUEUED,
                scheduled_for=data.get('scheduled_for'),
            )
            
            # Send email
            sender = EmailSenderService(account)
            success = sender.send_email(email)
            
            if success:
                # Update conversation stats
                EmailThreadingService.update_conversation_stats(conversation)
                
                serializer = EmailDetailSerializer(email, context={'request': request})
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                return Response({
                    'success': False,
                    'error': 'Failed to send email'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except EmailAccount.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Account not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'])
    def reply(self, request, pk=None):
        """Reply to an email"""
        original_email = self.get_object()
        serializer = EmailReplySerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        
        try:
            # Generate message ID
            message_id = f"<{uuid.uuid4()}@{original_email.account.email_address.split('@')[1]}>"
            
            # Build references
            references = original_email.references
            if original_email.message_id:
                references = f"{references} {original_email.message_id}".strip()
            
            # Create reply email
            reply_email = Email.objects.create(
                conversation=original_email.conversation,
                account=original_email.account,
                direction=Email.Direction.OUTBOUND,
                message_id=message_id,
                in_reply_to=original_email.message_id,
                references=references,
                from_email=original_email.account.email_address,
                from_name=original_email.account.name,
                to_emails=[{'email': original_email.from_email, 'name': original_email.from_name}],
                subject=f"Re: {original_email.subject}" if not original_email.subject.startswith('Re:') else original_email.subject,
                body_html=data.get('body_html', ''),
                body_text=data.get('body_text', ''),
                status=Email.Status.QUEUED,
            )
            
            # Send email
            sender = EmailSenderService(original_email.account)
            success = sender.send_email(reply_email)
            
            if success:
                # Update conversation stats
                EmailThreadingService.update_conversation_stats(original_email.conversation)
                
                serializer = EmailDetailSerializer(reply_email, context={'request': request})
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                return Response({
                    'success': False,
                    'error': 'Failed to send reply'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except Exception as e:
            logger.error(f"Error sending reply: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class EmailLabelViewSet(viewsets.ModelViewSet):
    """API für Email-Labels"""
    serializer_class = EmailLabelSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return EmailLabel.objects.filter(
            owner=self.request.user
        ) | EmailLabel.objects.filter(is_system=True)


class EmailSignatureViewSet(viewsets.ModelViewSet):
    """API für Email-Signaturen"""
    serializer_class = EmailSignatureSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return EmailSignature.objects.filter(user=self.request.user)


class QuickReplyViewSet(viewsets.ModelViewSet):
    """API für Schnellantworten"""
    serializer_class = QuickReplySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return QuickReply.objects.filter(
            owner=self.request.user
        ) | QuickReply.objects.filter(is_shared=True)


@csrf_exempt
@api_view(['POST'])
def brevo_webhook(request):
    """
    Brevo Webhook Endpoint
    
    Receives webhook events from Brevo and processes them.
    """
    try:
        event_data = request.data
        
        # TODO: Validate webhook signature
        # if 'X-Brevo-Signature' in request.headers:
        #     signature = request.headers['X-Brevo-Signature']
        #     # Validate signature
        
        # Process event
        success = BrevoWebhookHandler.handle_event(event_data)
        
        if success:
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False}, status=400)
            
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
