"""
Support views for diagnostics and troubleshooting.
"""

import os
import tempfile
from datetime import datetime
from pathlib import Path

from django.contrib.auth.decorators import login_required
from django.http import FileResponse, HttpResponse
from django.shortcuts import render
from django.core.management import call_command
from django.conf import settings


@login_required
def support_bundle_view(request):
    """
    View to generate and download a support bundle.
    
    Allows users to download a ZIP file containing:
    - System information
    - Configuration status (sanitized)
    - Database statistics
    - Version information
    - Django checks
    """
    if request.method == 'POST':
        # Generate support bundle
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Create temporary file for the bundle
        with tempfile.NamedTemporaryFile(
            delete=False, 
            suffix='.zip',
            prefix=f'support_bundle_{timestamp}_'
        ) as tmp_file:
            bundle_path = tmp_file.name
        
        try:
            # Generate the bundle using management command
            include_logs = request.POST.get('include_logs') == 'on'
            
            # Suppress output to devnull
            import subprocess
            
            call_command(
                'create_support_bundle',
                output=bundle_path,
                include_logs=include_logs,
                stdout=subprocess.DEVNULL
            )
            
            # Return the file as download
            response = FileResponse(
                open(bundle_path, 'rb'),
                content_type='application/zip',
                as_attachment=True,
                filename=f'support_bundle_{timestamp}.zip'
            )
            
            # Note: Temporary file cleanup is handled by the OS or should be done
            # via scheduled cleanup. FileResponse will close the file handle.
            
            return response
            
        except Exception as e:
            # Clean up on error
            if os.path.exists(bundle_path):
                os.unlink(bundle_path)
            
            return HttpResponse(
                f'Error generating support bundle: {str(e)}',
                status=500
            )
    
    # GET request - show the form
    context = {}
    return render(request, 'support/bundle.html', context)


@login_required
def system_health_view(request):
    """
    View to display system health information.
    """
    # Import here to avoid errors if psutil is not installed
    try:
        import psutil
        
        health_info = {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_percent': psutil.disk_usage('/').percent,
            'available': True,
        }
    except ImportError:
        health_info = {
            'available': False,
            'message': 'psutil not installed - install with: pip install psutil'
        }
    
    context = {
        'health': health_info,
        'debug': settings.DEBUG,
    }
    
    return render(request, 'support/health.html', context)
