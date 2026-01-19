"""
Scraper control views for Django CRM.
Handles scraper start/stop/status and live logs.
"""

import json
import time
from django.http import JsonResponse, StreamingHttpResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from .scraper_manager import get_manager
from .models import ScraperRun, ScraperConfig
from .permissions import IsAdmin, CanControlScraper
import logging

logger = logging.getLogger(__name__)

# Cache valid industries at module level to avoid repeated computation
_VALID_INDUSTRIES = None

def get_valid_industries():
    """Get valid industries from ScraperConfig, with caching."""
    global _VALID_INDUSTRIES
    if _VALID_INDUSTRIES is None:
        from scraper_control.models import ScraperConfig as ControlScraperConfig
        _VALID_INDUSTRIES = [c[0] for c in ControlScraperConfig.INDUSTRY_CHOICES]
    return _VALID_INDUSTRIES


@login_required
def scraper_page(request):
    """
    Scraper control page - shows interface for starting/stopping scraper
    and viewing live logs.
    
    Only accessible by Admin users.
    """
    # Check if user is Admin
    is_admin = request.user.groups.filter(name='Admin').exists() or request.user.is_superuser
    
    if not is_admin:
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("Sie haben keine Berechtigung, auf diese Seite zuzugreifen.")
    
    # Get scraper config
    config = ScraperConfig.get_config()
    
    # Get recent runs
    recent_runs = ScraperRun.objects.all()[:10]
    
    # Get current status
    manager = get_manager()
    scraper_status = manager.get_status()
    
    context = {
        'user_role': 'Admin' if is_admin else 'User',
        'config': config,
        'recent_runs': recent_runs,
        'scraper_status': scraper_status,
    }
    
    return render(request, 'crm/scraper.html', context)


@api_view(['POST'])
@permission_classes([IsAdmin])
def scraper_start(request):
    """
    Start the scraper with given parameters.
    
    POST data:
    {
        "industry": "recruiter|candidates|talent_hunt|all|handelsvertreter|...",
        "qpi": 15,
        "mode": "standard|aggressive|snippet_only|learning",
        "smart": true,
        "force": false,
        "once": true,
        "dry_run": false
    }
    """
    try:
        valid_industries = get_valid_industries()
        
        params = request.data
        
        # Validate parameters
        industry = params.get('industry', 'recruiter')
        if industry not in valid_industries:
            return Response({
                'success': False,
                'error': f'Ungültige Industry: {industry}. Erlaubt: {valid_industries}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        qpi = params.get('qpi', 15)
        try:
            qpi = int(qpi)
            if qpi < 1 or qpi > 100:
                raise ValueError
        except (ValueError, TypeError):
            return Response({
                'success': False,
                'error': 'QPI muss zwischen 1 und 100 liegen'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Start scraper
        manager = get_manager()
        result = manager.start(params, user=request.user)
        
        if result['success']:
            return Response(result, status=status.HTTP_200_OK)
        else:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"Error starting scraper: {e}", exc_info=True)
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAdmin])
def scraper_stop(request):
    """
    Stop the running scraper.
    """
    try:
        manager = get_manager()
        result = manager.stop()
        
        if result['success']:
            return Response(result, status=status.HTTP_200_OK)
        else:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"Error stopping scraper: {e}", exc_info=True)
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAdmin])
def scraper_status(request):
    """
    Get current scraper status.
    
    Returns:
    {
        "status": "running|stopped|error",
        "pid": 12345,
        "run_id": 1,
        "uptime_seconds": 120,
        "cpu_percent": 45.2,
        "memory_mb": 128.5,
        "leads_found": 10,
        "leads_saved": 8,
        "leads_rejected": 2,
        "params": {...}
    }
    """
    try:
        manager = get_manager()
        status_info = manager.get_status()
        
        return Response(status_info, status=status.HTTP_200_OK)
            
    except Exception as e:
        logger.error(f"Error getting scraper status: {e}", exc_info=True)
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@require_GET
@login_required
def scraper_logs(request):
    """
    Stream live logs via Server-Sent Events (SSE).
    
    Only accessible by Admin users.
    """
    # Check if user is Admin
    is_admin = request.user.groups.filter(name='Admin').exists() or request.user.is_superuser
    
    if not is_admin:
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("Keine Berechtigung")
    
    def event_stream():
        """Generator for SSE events"""
        manager = get_manager()
        last_log_count = 0
        
        # Send initial message
        yield f"data: {json.dumps({'type': 'connected', 'message': 'Verbunden mit Log-Stream'})}\n\n"
        
        # Stream logs
        while True:
            try:
                # Get new logs
                logs = manager.get_logs(lines=1000)
                
                # Send only new logs
                if len(logs) > last_log_count:
                    new_logs = logs[last_log_count:]
                    for log_entry in new_logs:
                        data = {
                            'type': 'log',
                            'timestamp': log_entry.get('timestamp', ''),
                            'message': log_entry.get('message', '')
                        }
                        yield f"data: {json.dumps(data)}\n\n"
                    last_log_count = len(logs)
                
                # Check if scraper is still running
                if not manager.is_running():
                    yield f"data: {json.dumps({'type': 'stopped', 'message': 'Scraper gestoppt'})}\n\n"
                    break
                
                # Wait before checking again
                time.sleep(1)
                
            except GeneratorExit:
                # Client disconnected
                break
            except Exception as e:
                logger.error(f"Error in log stream: {e}")
                yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
                break
    
    response = StreamingHttpResponse(event_stream(), content_type='text/event-stream')
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'
    return response


@api_view(['GET'])
@permission_classes([IsAdmin])
def scraper_config(request):
    """
    Get current scraper configuration.
    """
    try:
        config = ScraperConfig.get_config()
        
        return Response({
            'min_score': config.min_score,
            'max_results_per_domain': config.max_results_per_domain,
            'request_timeout': config.request_timeout,
            'pool_size': config.pool_size,
            'internal_depth_per_domain': config.internal_depth_per_domain,
            'allow_pdf': config.allow_pdf,
            'allow_insecure_ssl': config.allow_insecure_ssl,
        }, status=status.HTTP_200_OK)
            
    except Exception as e:
        logger.error(f"Error getting scraper config: {e}", exc_info=True)
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT'])
@permission_classes([IsAdmin])
def scraper_config_update(request):
    """
    Update scraper configuration.
    
    PUT data:
    {
        "min_score": 40,
        "max_results_per_domain": 3,
        "request_timeout": 12,
        "pool_size": 10,
        "internal_depth_per_domain": 2,
        "allow_pdf": true,
        "allow_insecure_ssl": false
    }
    """
    try:
        config = ScraperConfig.get_config()
        
        # Update fields
        if 'min_score' in request.data:
            config.min_score = int(request.data['min_score'])
        if 'max_results_per_domain' in request.data:
            config.max_results_per_domain = int(request.data['max_results_per_domain'])
        if 'request_timeout' in request.data:
            config.request_timeout = int(request.data['request_timeout'])
        if 'pool_size' in request.data:
            config.pool_size = int(request.data['pool_size'])
        if 'internal_depth_per_domain' in request.data:
            config.internal_depth_per_domain = int(request.data['internal_depth_per_domain'])
        if 'allow_pdf' in request.data:
            config.allow_pdf = bool(request.data['allow_pdf'])
        if 'allow_insecure_ssl' in request.data:
            config.allow_insecure_ssl = bool(request.data['allow_insecure_ssl'])
        
        config.updated_by = request.user
        config.save()
        
        return Response({
            'success': True,
            'message': 'Konfiguration aktualisiert'
        }, status=status.HTTP_200_OK)
            
    except Exception as e:
        logger.error(f"Error updating scraper config: {e}", exc_info=True)
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAdmin])
def scraper_runs(request):
    """
    Get list of recent scraper runs.
    """
    try:
        runs = ScraperRun.objects.all()[:20]
        
        data = []
        for run in runs:
            data.append({
                'id': run.id,
                'status': run.status,
                'started_at': run.started_at.isoformat(),
                'finished_at': run.finished_at.isoformat() if run.finished_at else None,
                'duration_seconds': run.duration_seconds,
                'leads_found': run.leads_found,
                'leads_saved': run.leads_saved,
                'leads_rejected': run.leads_rejected,
                'started_by': run.started_by.username if run.started_by else None,
            })
        
        return Response(data, status=status.HTTP_200_OK)
            
    except Exception as e:
        logger.error(f"Error getting scraper runs: {e}", exc_info=True)
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
