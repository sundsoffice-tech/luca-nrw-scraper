"""
Scraper control views and API endpoints.
Handles scraper start/stop/status and live logs via SSE.
"""

import json
import time
from django.http import JsonResponse, StreamingHttpResponse
from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.http import require_GET
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework import status as http_status
from .process_manager import get_manager
from .models import ScraperRun, ScraperConfig, ScraperLog
import logging

logger = logging.getLogger(__name__)


@staff_member_required
def scraper_dashboard(request):
    """
    Scraper control dashboard page.
    Shows interface for starting/stopping scraper and viewing live logs.
    """
    # Get scraper config
    config = ScraperConfig.get_config()
    
    # Get recent runs
    recent_runs = ScraperRun.objects.all()[:10]
    
    # Get current status
    manager = get_manager()
    scraper_status = manager.get_status()
    
    context = {
        'config': config,
        'recent_runs': recent_runs,
        'scraper_status': scraper_status,
    }
    
    return render(request, 'scraper_control/dashboard.html', context)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def api_scraper_status(request):
    """
    GET /crm/scraper/api/scraper/status/
    
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
        "api_cost": 2.50,
        "params": {...}
    }
    """
    try:
        manager = get_manager()
        status_info = manager.get_status()
        
        return Response(status_info, status=http_status.HTTP_200_OK)
            
    except Exception as e:
        logger.error(f"Error getting scraper status: {e}", exc_info=True)
        return Response({
            'success': False,
            'error': str(e)
        }, status=http_status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def api_scraper_start(request):
    """
    POST /crm/scraper/api/scraper/start/
    
    Start the scraper with validated parameters.
    
    POST data:
    {
        "industry": "recruiter|candidates|talent_hunt|all|nrw|social|solar|telekom|versicherung|bau|ecom|household",
        "qpi": 15,
        "mode": "standard|learning|aggressive|snippet_only",
        "daterestrict": "d30",
        "smart": true,
        "force": false,
        "once": true,
        "dry_run": false
    }
    """
    try:
        # Get available choices from model
        from .models import ScraperConfig
        valid_industries = [c[0] for c in ScraperConfig.INDUSTRY_CHOICES]
        valid_modes = [c[0] for c in ScraperConfig.MODE_CHOICES]
        
        params = request.data.copy()  # Mutable copy - request.data is immutable, we need to modify for parameter sanitization
        
        # Validate and set defaults for industry
        industry = params.get('industry', 'recruiter')
        if industry not in valid_industries:
            return Response({
                'success': False,
                'error': f'Ungültige Industry: {industry}. Erlaubt: {", ".join(valid_industries)}'
            }, status=http_status.HTTP_400_BAD_REQUEST)
        
        # Validate and sanitize mode with fallback
        mode = params.get('mode', 'standard')
        if mode not in valid_modes:
            logger.warning(f"Unknown mode '{mode}', falling back to 'standard'")
            params['mode'] = 'standard'
        
        # Validate and clamp QPI
        qpi = params.get('qpi', 15)
        try:
            qpi = int(qpi)
            qpi = max(1, min(100, qpi))  # Clamp between 1 and 100
            params['qpi'] = qpi
        except (ValueError, TypeError):
            logger.warning(f"Invalid QPI value '{qpi}', using default 15")
            params['qpi'] = 15
        
        # Check parameter dependencies
        if params.get('dry_run') and params.get('mode') == 'aggressive':
            logger.warning("dry_run + aggressive mode is not recommended, falling back to standard")
            params['mode'] = 'standard'
        
        # Start scraper with validated params
        manager = get_manager()
        result = manager.start(params, user=request.user)
        
        if result['success']:
            return Response(result, status=http_status.HTTP_200_OK)
        else:
            return Response(result, status=http_status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"Error starting scraper: {e}", exc_info=True)
        return Response({
            'success': False,
            'error': str(e)
        }, status=http_status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def api_scraper_stop(request):
    """
    POST /crm/scraper/api/scraper/stop/
    
    Stop the running scraper.
    """
    try:
        manager = get_manager()
        result = manager.stop()
        
        if result['success']:
            return Response(result, status=http_status.HTTP_200_OK)
        else:
            return Response(result, status=http_status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"Error stopping scraper: {e}", exc_info=True)
        return Response({
            'success': False,
            'error': str(e)
        }, status=http_status.HTTP_500_INTERNAL_SERVER_ERROR)


@require_GET
@staff_member_required
def api_scraper_logs_stream(request):
    """
    GET /crm/scraper/api/scraper/logs/stream/
    
    Stream live logs via Server-Sent Events (SSE).
    """
    def event_stream():
        """Generator for SSE events"""
        manager = get_manager()
        last_log_id = 0
        
        # Send initial message
        yield f"data: {json.dumps({'type': 'connected', 'message': 'Verbunden mit Log-Stream'})}\n\n"
        
        # Get current run ID
        status_info = manager.get_status()
        run_id = status_info.get('run_id')
        
        if not run_id:
            yield f"data: {json.dumps({'type': 'info', 'message': 'Kein aktiver Scraper-Lauf'})}\n\n"
            return
        
        # Stream logs
        while True:
            try:
                # Get new logs from database
                new_logs = ScraperLog.objects.filter(
                    run_id=run_id,
                    id__gt=last_log_id
                ).order_by('id')[:50]  # Batch of 50 logs at a time
                
                # Send new logs
                for log_entry in new_logs:
                    data = {
                        'type': 'log',
                        'level': log_entry.level,
                        'timestamp': log_entry.created_at.isoformat(),
                        'message': log_entry.message
                    }
                    yield f"data: {json.dumps(data)}\n\n"
                    last_log_id = log_entry.id
                
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
@permission_classes([IsAdminUser])
def api_scraper_config(request):
    """
    GET /crm/scraper/api/scraper/config/
    
    Get current scraper configuration.
    """
    try:
        config = ScraperConfig.get_config()
        
        return Response({
            'industry': config.industry,
            'mode': config.mode,
            'qpi': config.qpi,
            'daterestrict': config.daterestrict,
            'smart': config.smart,
            'force': config.force,
            'once': config.once,
            'dry_run': config.dry_run,
            'updated_at': config.updated_at.isoformat() if config.updated_at else None,
            'updated_by': config.updated_by.username if config.updated_by else None,
        }, status=http_status.HTTP_200_OK)
            
    except Exception as e:
        logger.error(f"Error getting scraper config: {e}", exc_info=True)
        return Response({
            'success': False,
            'error': str(e)
        }, status=http_status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT'])
@permission_classes([IsAdminUser])
def api_scraper_config_update(request):
    """
    PUT /crm/scraper/api/scraper/config/
    
    Update scraper configuration.
    
    PUT data:
    {
        "industry": "recruiter",
        "mode": "standard",
        "qpi": 15,
        "daterestrict": "d30",
        "smart": true,
        "force": false,
        "once": true,
        "dry_run": false
    }
    """
    try:
        config = ScraperConfig.get_config()
        
        # Update fields
        if 'industry' in request.data:
            config.industry = request.data['industry']
        if 'mode' in request.data:
            config.mode = request.data['mode']
        if 'qpi' in request.data:
            config.qpi = int(request.data['qpi'])
        if 'daterestrict' in request.data:
            config.daterestrict = request.data['daterestrict']
        if 'smart' in request.data:
            config.smart = bool(request.data['smart'])
        if 'force' in request.data:
            config.force = bool(request.data['force'])
        if 'once' in request.data:
            config.once = bool(request.data['once'])
        if 'dry_run' in request.data:
            config.dry_run = bool(request.data['dry_run'])
        
        config.updated_by = request.user
        config.save()
        
        return Response({
            'success': True,
            'message': 'Konfiguration aktualisiert'
        }, status=http_status.HTTP_200_OK)
            
    except Exception as e:
        logger.error(f"Error updating scraper config: {e}", exc_info=True)
        return Response({
            'success': False,
            'error': str(e)
        }, status=http_status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def api_scraper_runs(request):
    """
    GET /crm/scraper/api/scraper/runs/
    
    Get list of recent scraper runs.
    """
    try:
        runs = ScraperRun.objects.all()[:20]
        
        data = []
        for run in runs:
            duration = run.duration
            duration_seconds = int(duration.total_seconds()) if duration else 0
            
            data.append({
                'id': run.id,
                'status': run.status,
                'started_at': run.started_at.isoformat(),
                'finished_at': run.finished_at.isoformat() if run.finished_at else None,
                'duration_seconds': duration_seconds,
                'leads_found': run.leads_found,
                'api_cost': float(run.api_cost),
                'started_by': run.started_by.username if run.started_by else None,
                'pid': run.pid,
            })
        
        return Response(data, status=http_status.HTTP_200_OK)
            
    except Exception as e:
        logger.error(f"Error getting scraper runs: {e}", exc_info=True)
        return Response({
            'success': False,
            'error': str(e)
        }, status=http_status.HTTP_500_INTERNAL_SERVER_ERROR)
