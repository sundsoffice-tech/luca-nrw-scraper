from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'leads', views.LeadViewSet)
router.register(r'call-logs', views.CallLogViewSet)
router.register(r'email-logs', views.EmailLogViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('import-csv/', views.import_csv, name='import-csv'),
    path('health/', views.api_health, name='api-health'),
    path('opt-in/', views.opt_in, name='opt-in'),
]
