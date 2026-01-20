"""
URL configuration for Mailbox app
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from . import api_views

app_name = 'mailbox'

# API Router
router = DefaultRouter()
router.register(r'accounts', api_views.EmailAccountViewSet, basename='account')
router.register(r'conversations', api_views.ConversationViewSet, basename='conversation')
router.register(r'emails', api_views.EmailViewSet, basename='email')
router.register(r'labels', api_views.EmailLabelViewSet, basename='label')
router.register(r'signatures', api_views.EmailSignatureViewSet, basename='signature')
router.register(r'quick-replies', api_views.QuickReplyViewSet, basename='quickreply')

urlpatterns = [
    # Web Views
    path('', views.inbox, name='inbox'),
    path('compose/', views.compose, name='compose'),
    path('conversation/<int:conversation_id>/', views.conversation_detail, name='conversation'),
    path('conversation/<int:conversation_id>/create-lead/', views.create_lead_from_conversation, name='conversation-create-lead'),
    path('reply/<int:email_id>/', views.reply, name='reply'),
    path('forward/<int:email_id>/', views.forward, name='forward'),
    path('settings/', views.account_settings, name='settings'),
    path('signatures/', views.signatures, name='signatures'),
    path('quick-replies/', views.quick_replies_view, name='quick-replies'),
    path('attachment/<int:attachment_id>/download/', views.download_attachment, name='attachment-download'),
    
    # API
    path('api/', include(router.urls)),
    
    # Webhooks
    path('webhooks/brevo/', api_views.brevo_webhook, name='brevo-webhook'),
]
