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
                # Enhanced metrics
                'links_checked': run.links_checked,
                'leads_accepted': run.leads_accepted,
                'leads_rejected': run.leads_rejected,
                'block_rate': run.block_rate,
                'timeout_rate': run.timeout_rate,
                'avg_request_time_ms': run.avg_request_time_ms,
                'success_rate': run.success_rate,
                'lead_acceptance_rate': run.lead_acceptance_rate,
            })
        
        return Response(data, status=http_status.HTTP_200_OK)
            
    except Exception as e:
        logger.error(f"Error getting scraper runs: {e}", exc_info=True)
        return Response({
            'success': False,
            'error': str(e)
        }, status=http_status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def api_logs_filtered(request):
    """
    GET /crm/scraper/api/logs/
    
    Get filtered logs with enhanced filtering options.
    
    Query params:
    - run_id: Filter by run ID
    - portal: Filter by portal/source
    - level: Filter by log level (DEBUG, INFO, WARN, ERROR, CRITICAL)
    - start_date: Filter from date (ISO format)
    - end_date: Filter to date (ISO format)
    - limit: Max results (default 100)
    """
    try:
        from .models import ScraperLog
        from django.db.models import Q
        from datetime import datetime
        
        logs = ScraperLog.objects.all()
        
        # Apply filters
        run_id = request.query_params.get('run_id')
        if run_id:
            logs = logs.filter(run_id=run_id)
        
        portal = request.query_params.get('portal')
        if portal:
            logs = logs.filter(portal__icontains=portal)
        
        level = request.query_params.get('level')
        if level:
            logs = logs.filter(level=level.upper())
        
        start_date = request.query_params.get('start_date')
        if start_date:
            try:
                start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                logs = logs.filter(created_at__gte=start_dt)
            except ValueError:
                pass
        
        end_date = request.query_params.get('end_date')
        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                logs = logs.filter(created_at__lte=end_dt)
            except ValueError:
                pass
        
        # Limit results
        limit = int(request.query_params.get('limit', 100))
        logs = logs[:limit]
        
        data = []
        for log in logs:
            data.append({
                'id': log.id,
                'run_id': log.run_id,
                'level': log.level,
                'portal': log.portal,
                'message': log.message,
                'created_at': log.created_at.isoformat(),
            })
        
        return Response(data, status=http_status.HTTP_200_OK)
            
    except Exception as e:
        logger.error(f"Error getting filtered logs: {e}", exc_info=True)
        return Response({
            'success': False,
            'error': str(e)
        }, status=http_status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def api_errors_filtered(request):
    """
    GET /crm/scraper/api/errors/
    
    Get filtered errors with classification.
    
    Query params:
    - run_id: Filter by run ID
    - error_type: Filter by error type
    - severity: Filter by severity
    - portal: Filter by portal/source
    - start_date: Filter from date (ISO format)
    - end_date: Filter to date (ISO format)
    - limit: Max results (default 100)
    """
    try:
        from .models import ErrorLog
        from datetime import datetime
        
        errors = ErrorLog.objects.all()
        
        # Apply filters
        run_id = request.query_params.get('run_id')
        if run_id:
            errors = errors.filter(run_id=run_id)
        
        error_type = request.query_params.get('error_type')
        if error_type:
            errors = errors.filter(error_type=error_type)
        
        severity = request.query_params.get('severity')
        if severity:
            errors = errors.filter(severity=severity)
        
        portal = request.query_params.get('portal')
        if portal:
            errors = errors.filter(portal__icontains=portal)
        
        start_date = request.query_params.get('start_date')
        if start_date:
            try:
                start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                errors = errors.filter(created_at__gte=start_dt)
            except ValueError:
                pass
        
        end_date = request.query_params.get('end_date')
        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                errors = errors.filter(last_occurrence__lte=end_dt)
            except ValueError:
                pass
        
        # Limit results
        limit = int(request.query_params.get('limit', 100))
        errors = errors[:limit]
        
        data = []
        for error in errors:
            data.append({
                'id': error.id,
                'run_id': error.run_id,
                'error_type': error.error_type,
                'error_type_display': error.get_error_type_display(),
                'severity': error.severity,
                'severity_display': error.get_severity_display(),
                'portal': error.portal,
                'url': error.url,
                'message': error.message,
                'count': error.count,
                'created_at': error.created_at.isoformat(),
                'last_occurrence': error.last_occurrence.isoformat(),
            })
        
        return Response(data, status=http_status.HTTP_200_OK)
            
    except Exception as e:
        logger.error(f"Error getting filtered errors: {e}", exc_info=True)
        return Response({
            'success': False,
            'error': str(e)
        }, status=http_status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def api_update_rate_limit(request):
    """
    POST /crm/scraper/api/control/rate-limit/
    
    Update rate limits live.
    
    POST data:
    {
        "portal": "portal_name",  # optional, if not provided updates global config
        "rate_limit_seconds": 5.0
    }
    """
    try:
        portal = request.data.get('portal')
        rate_limit = request.data.get('rate_limit_seconds')
        
        if rate_limit is None:
            return Response({
                'success': False,
                'error': 'rate_limit_seconds ist erforderlich'
            }, status=http_status.HTTP_400_BAD_REQUEST)
        
        try:
            rate_limit = float(rate_limit)
            if rate_limit < 0.5 or rate_limit > 60:
                return Response({
                    'success': False,
                    'error': 'rate_limit_seconds muss zwischen 0.5 und 60 liegen'
                }, status=http_status.HTTP_400_BAD_REQUEST)
        except (ValueError, TypeError):
            return Response({
                'success': False,
                'error': 'Ungültiger Wert für rate_limit_seconds'
            }, status=http_status.HTTP_400_BAD_REQUEST)
        
        if portal:
            # Update specific portal
            from .models import PortalSource
            try:
                portal_obj = PortalSource.objects.get(name=portal)
                portal_obj.rate_limit_seconds = rate_limit
                portal_obj.save()
                
                logger.info(f"Updated rate limit for portal {portal} to {rate_limit}s by {request.user.username}")
                
                return Response({
                    'success': True,
                    'message': f'Rate Limit für {portal} auf {rate_limit}s gesetzt'
                }, status=http_status.HTTP_200_OK)
            except PortalSource.DoesNotExist:
                return Response({
                    'success': False,
                    'error': f'Portal {portal} nicht gefunden'
                }, status=http_status.HTTP_404_NOT_FOUND)
        else:
            # Update global config
            config = ScraperConfig.get_config()
            config.sleep_between_queries = rate_limit
            config.updated_by = request.user
            config.save()
            
            logger.info(f"Updated global rate limit to {rate_limit}s by {request.user.username}")
            
            return Response({
                'success': True,
                'message': f'Globales Rate Limit auf {rate_limit}s gesetzt'
            }, status=http_status.HTTP_200_OK)
            
    except Exception as e:
        logger.error(f"Error updating rate limit: {e}", exc_info=True)
        return Response({
            'success': False,
            'error': str(e)
        }, status=http_status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def api_toggle_portal(request):
    """
    POST /crm/scraper/api/control/portal/toggle/
    
    Enable or disable a portal.
    
    POST data:
    {
        "portal": "portal_name",
        "active": true/false
    }
    """
    try:
        from .models import PortalSource
        
        portal = request.data.get('portal')
        active = request.data.get('active')
        
        if not portal:
            return Response({
                'success': False,
                'error': 'Portal-Name ist erforderlich'
            }, status=http_status.HTTP_400_BAD_REQUEST)
        
        if active is None:
            return Response({
                'success': False,
                'error': 'active ist erforderlich (true/false)'
            }, status=http_status.HTTP_400_BAD_REQUEST)
        
        try:
            portal_obj = PortalSource.objects.get(name=portal)
            portal_obj.is_active = bool(active)
            portal_obj.save()
            
            status_text = "aktiviert" if active else "deaktiviert"
            logger.info(f"Portal {portal} {status_text} by {request.user.username}")
            
            return Response({
                'success': True,
                'message': f'Portal {portal} {status_text}'
            }, status=http_status.HTTP_200_OK)
        except PortalSource.DoesNotExist:
            return Response({
                'success': False,
                'error': f'Portal {portal} nicht gefunden'
            }, status=http_status.HTTP_404_NOT_FOUND)
            
    except Exception as e:
        logger.error(f"Error toggling portal: {e}", exc_info=True)
        return Response({
            'success': False,
            'error': str(e)
        }, status=http_status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def api_portals_status(request):
    """
    GET /crm/scraper/api/control/portals/
    
    Get status of all portals including circuit breaker states.
    """
    try:
        from .models import PortalSource
        from django.utils import timezone
        
        portals = PortalSource.objects.all()
        
        data = []
        for portal in portals:
            # Check if circuit breaker should be reset
            if portal.circuit_breaker_tripped and portal.circuit_breaker_reset_at:
                if timezone.now() >= portal.circuit_breaker_reset_at:
                    portal.circuit_breaker_tripped = False
                    portal.circuit_breaker_reset_at = None
                    portal.consecutive_errors = 0
                    portal.save()
            
            data.append({
                'name': portal.name,
                'display_name': portal.display_name,
                'is_active': portal.is_active,
                'rate_limit_seconds': portal.rate_limit_seconds,
                'max_results': portal.max_results,
                'circuit_breaker_enabled': portal.circuit_breaker_enabled,
                'circuit_breaker_tripped': portal.circuit_breaker_tripped,
                'circuit_breaker_reset_at': portal.circuit_breaker_reset_at.isoformat() if portal.circuit_breaker_reset_at else None,
                'consecutive_errors': portal.consecutive_errors,
                'circuit_breaker_threshold': portal.circuit_breaker_threshold,
            })
        
        return Response(data, status=http_status.HTTP_200_OK)
            
    except Exception as e:
        logger.error(f"Error getting portals status: {e}", exc_info=True)
        return Response({
            'success': False,
            'error': str(e)
        }, status=http_status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def api_reset_circuit_breaker(request):
    """
    POST /crm/scraper/api/control/circuit-breaker/reset/
    
    Manually reset circuit breaker for a portal.
    
    POST data:
    {
        "portal": "portal_name"
    }
    """
    try:
        from .models import PortalSource
        
        portal = request.data.get('portal')
        
        if not portal:
            return Response({
                'success': False,
                'error': 'Portal-Name ist erforderlich'
            }, status=http_status.HTTP_400_BAD_REQUEST)
        
        try:
            portal_obj = PortalSource.objects.get(name=portal)
            portal_obj.circuit_breaker_tripped = False
            portal_obj.circuit_breaker_reset_at = None
            portal_obj.consecutive_errors = 0
            portal_obj.save()
            
            logger.info(f"Circuit breaker reset for portal {portal} by {request.user.username}")
            
            return Response({
                'success': True,
                'message': f'Circuit Breaker für {portal} zurückgesetzt'
            }, status=http_status.HTTP_200_OK)
        except PortalSource.DoesNotExist:
            return Response({
                'success': False,
                'error': f'Portal {portal} nicht gefunden'
            }, status=http_status.HTTP_404_NOT_FOUND)
            
    except Exception as e:
        logger.error(f"Error resetting circuit breaker: {e}", exc_info=True)
        return Response({
            'success': False,
            'error': str(e)
        }, status=http_status.HTTP_500_INTERNAL_SERVER_ERROR)
