"""API URL Configuration for Email Templates"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# REST API Router
router = DefaultRouter()
router.register(r'templates', views.EmailTemplateViewSet, basename='template')
router.register(r'versions', views.EmailTemplateVersionViewSet, basename='version')
router.register(r'send-logs', views.EmailSendLogViewSet, basename='sendlog')
router.register(r'flows', views.EmailFlowViewSet, basename='flow')

urlpatterns = [
    path('', include(router.urls)),
]
