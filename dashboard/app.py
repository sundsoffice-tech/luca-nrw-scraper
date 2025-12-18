# -*- coding: utf-8 -*-
"""
LUCA Control Center - Main Dashboard Application
"""

import os
import sys
import json
import queue
import threading
import time
from flask import Flask, render_template, jsonify, request, Response, send_file
from flask_cors import CORS

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dashboard.db_schema import ensure_dashboard_schema, initialize_default_search_modes, initialize_default_settings
from dashboard.api import stats, costs, modes, settings
from dashboard.scraper_control import get_controller
from dashboard.scheduler import get_scheduler

# Database path
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'scraper.db')

# Global log queue for SSE
log_queue = queue.Queue(maxsize=1000)


def create_app(db_path: str = None) -> Flask:
    """
    Create and configure the Flask dashboard application.
    
    Args:
        db_path: Path to SQLite database (optional)
        
    Returns:
        Configured Flask application
    """
    global DB_PATH
    if db_path:
        DB_PATH = db_path
    
    app = Flask(__name__, 
                template_folder='templates',
                static_folder='static')
    CORS(app)
    
    # Initialize database schema
    import sqlite3
    con = sqlite3.connect(DB_PATH)
    ensure_dashboard_schema(con)
    initialize_default_search_modes(con)
    initialize_default_settings(con)
    con.close()
    
    # ==================== Routes ====================
    
    @app.route('/')
    def index():
        """Render main dashboard page."""
        return render_template('dashboard.html')
    
    @app.route('/analytics')
    def analytics():
        """Render analytics page."""
        return render_template('analytics.html')
    
    @app.route('/settings')
    def settings_page():
        """Render settings page."""
        return render_template('settings.html')
    
    @app.route('/leads')
    def leads_page():
        """Render leads management page."""
        return render_template('leads.html')
    
    # ==================== API Routes ====================
    
    @app.route('/api/stats')
    def api_stats():
        """Get dashboard statistics/KPIs."""
        try:
            data = stats.get_stats(DB_PATH)
            return jsonify(data)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/costs')
    def api_costs():
        """Get API cost breakdown."""
        try:
            data = costs.get_costs(DB_PATH)
            return jsonify(data)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/costs/chart')
    def api_costs_chart():
        """Get cost data formatted for charts."""
        try:
            days = int(request.args.get('days', 7))
            data = costs.get_cost_chart_data(DB_PATH, days)
            return jsonify(data)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/charts/leads')
    def api_charts_leads():
        """Get lead history chart data."""
        try:
            days = int(request.args.get('days', 7))
            data = stats.get_leads_history(DB_PATH, days)
            return jsonify(data)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/charts/sources')
    def api_charts_sources():
        """Get top sources chart data."""
        try:
            limit = int(request.args.get('limit', 10))
            data = stats.get_top_sources(DB_PATH, limit)
            return jsonify(data)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/mode', methods=['GET', 'POST'])
    def api_mode():
        """Get or set search mode."""
        try:
            if request.method == 'GET':
                current = modes.get_current_mode(DB_PATH)
                available = modes.get_all_modes(DB_PATH)
                return jsonify({
                    'current_mode': current,
                    'available_modes': available
                })
            else:
                data = request.get_json()
                mode_key = data.get('mode')
                if not mode_key:
                    return jsonify({'error': 'mode parameter required'}), 400
                
                success = modes.set_active_mode(DB_PATH, mode_key)
                if success:
                    # Log mode change
                    log_queue.put(json.dumps({
                        'timestamp': time.time(),
                        'level': 'INFO',
                        'message': f'Search mode changed to: {mode_key}'
                    }))
                    return jsonify({'success': True, 'mode': mode_key})
                else:
                    return jsonify({'error': 'Invalid mode or database error'}), 400
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/settings', methods=['GET', 'POST'])
    def api_settings():
        """Get or update settings."""
        try:
            if request.method == 'GET':
                data = settings.get_all_settings(DB_PATH)
                definitions = settings.get_setting_definitions()
                return jsonify({
                    'settings': data,
                    'definitions': definitions
                })
            else:
                data = request.get_json()
                results = settings.update_settings_bulk(DB_PATH, data)
                
                # Log settings change
                log_queue.put(json.dumps({
                    'timestamp': time.time(),
                    'level': 'INFO',
                    'message': f'Settings updated: {", ".join(data.keys())}'
                }))
                
                return jsonify({'success': True, 'results': results})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/stream/logs')
    def api_stream_logs():
        """Server-Sent Events stream for live logs."""
        def generate():
            while True:
                try:
                    # Get log entry from queue with timeout
                    log_entry = log_queue.get(timeout=1)
                    yield f"data: {log_entry}\n\n"
                except queue.Empty:
                    # Send keepalive comment
                    yield ": keepalive\n\n"
                    time.sleep(0.5)
        
        return Response(generate(), mimetype='text/event-stream')
    
    @app.route('/api/export/csv')
    def api_export_csv():
        """Export leads as CSV."""
        try:
            import csv
            import io
            import sqlite3
            
            con = sqlite3.connect(DB_PATH)
            con.row_factory = sqlite3.Row
            cur = con.cursor()
            
            cur.execute("SELECT * FROM leads ORDER BY id DESC")
            rows = cur.fetchall()
            
            if not rows:
                con.close()
                return jsonify({'error': 'No leads to export'}), 404
            
            # Create CSV in memory
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=rows[0].keys())
            writer.writeheader()
            for row in rows:
                writer.writerow(dict(row))
            
            con.close()
            
            # Create response
            output.seek(0)
            return Response(
                output.getvalue(),
                mimetype='text/csv',
                headers={'Content-Disposition': 'attachment;filename=leads.csv'}
            )
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    # ==================== Scraper Control API ====================
    
    @app.route('/api/scraper/start', methods=['POST'])
    def api_scraper_start():
        """Start the scraper with given parameters."""
        try:
            params = request.get_json() or {}
            controller = get_controller()
            result = controller.start(params)
            
            if result.get('success'):
                # Log start event
                log_queue.put(json.dumps({
                    'timestamp': time.time(),
                    'level': 'INFO',
                    'message': f'Scraper started with PID {result.get("pid")}'
                }))
            
            return jsonify(result)
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/scraper/stop', methods=['POST'])
    def api_scraper_stop():
        """Stop the running scraper."""
        try:
            controller = get_controller()
            result = controller.stop()
            
            if result.get('success'):
                log_queue.put(json.dumps({
                    'timestamp': time.time(),
                    'level': 'INFO',
                    'message': 'Scraper stopped'
                }))
            
            return jsonify(result)
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/scraper/pause', methods=['POST'])
    def api_scraper_pause():
        """Pause the running scraper."""
        try:
            controller = get_controller()
            result = controller.pause()
            
            if result.get('success'):
                log_queue.put(json.dumps({
                    'timestamp': time.time(),
                    'level': 'INFO',
                    'message': 'Scraper paused'
                }))
            
            return jsonify(result)
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/scraper/resume', methods=['POST'])
    def api_scraper_resume():
        """Resume the paused scraper."""
        try:
            controller = get_controller()
            result = controller.resume()
            
            if result.get('success'):
                log_queue.put(json.dumps({
                    'timestamp': time.time(),
                    'level': 'INFO',
                    'message': 'Scraper resumed'
                }))
            
            return jsonify(result)
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/scraper/reset', methods=['POST'])
    def api_scraper_reset():
        """Reset URL cache and queries."""
        try:
            controller = get_controller()
            result = controller.reset(DB_PATH)
            
            if result.get('success'):
                log_queue.put(json.dumps({
                    'timestamp': time.time(),
                    'level': 'INFO',
                    'message': 'Cache and queries reset'
                }))
            
            return jsonify(result)
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/scraper/status', methods=['GET'])
    def api_scraper_status():
        """Get current scraper status."""
        try:
            controller = get_controller()
            status = controller.get_status()
            return jsonify(status)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    # ==================== Scheduler API ====================
    
    @app.route('/api/scheduler', methods=['GET'])
    def api_scheduler_get():
        """Get scheduler configuration."""
        try:
            def dummy_start(params):
                # This will be called by scheduler
                controller = get_controller()
                return controller.start(params)
            
            scheduler = get_scheduler(DB_PATH, dummy_start)
            config = scheduler.get_config()
            
            # Calculate next run for display
            next_run = scheduler.calculate_next_run(config)
            if next_run:
                config['next_run_display'] = next_run.strftime('%Y-%m-%d %H:%M')
            
            return jsonify(config)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/scheduler', methods=['POST'])
    def api_scheduler_update():
        """Update scheduler configuration."""
        try:
            config = request.get_json() or {}
            
            def dummy_start(params):
                controller = get_controller()
                return controller.start(params)
            
            scheduler = get_scheduler(DB_PATH, dummy_start)
            result = scheduler.update_config(config)
            
            # Log change
            log_queue.put(json.dumps({
                'timestamp': time.time(),
                'level': 'INFO',
                'message': f'Scheduler updated: {"enabled" if config.get("enabled") else "disabled"}'
            }))
            
            return jsonify(result)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    # ==================== Leads API ====================
    
    @app.route('/api/leads', methods=['GET'])
    def api_leads_get():
        """Get leads with pagination and filtering."""
        try:
            import sqlite3
            
            page = int(request.args.get('page', 1))
            per_page = int(request.args.get('per_page', 50))
            search = request.args.get('search', '')
            status = request.args.get('status', '')
            date_from = request.args.get('date_from', '')
            
            con = sqlite3.connect(DB_PATH)
            con.row_factory = sqlite3.Row
            cur = con.cursor()
            
            # Build query
            where_clauses = []
            params = []
            
            if search:
                where_clauses.append("(name LIKE ? OR company LIKE ? OR mobile_number LIKE ?)")
                search_pattern = f"%{search}%"
                params.extend([search_pattern, search_pattern, search_pattern])
            
            if status:
                where_clauses.append("status = ?")
                params.append(status)
            
            if date_from:
                where_clauses.append("DATE(created_at) >= ?")
                params.append(date_from)
            
            where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
            
            # Get total count
            count_query = f"SELECT COUNT(*) FROM leads WHERE {where_sql}"
            cur.execute(count_query, params)
            total = cur.fetchone()[0]
            
            # Get paginated data
            offset = (page - 1) * per_page
            data_query = f"SELECT * FROM leads WHERE {where_sql} ORDER BY id DESC LIMIT ? OFFSET ?"
            cur.execute(data_query, params + [per_page, offset])
            rows = cur.fetchall()
            
            leads = [dict(row) for row in rows]
            
            con.close()
            
            return jsonify({
                'leads': leads,
                'total': total,
                'page': page,
                'per_page': per_page,
                'pages': (total + per_page - 1) // per_page
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/leads/<int:lead_id>/status', methods=['PUT'])
    def api_lead_update_status(lead_id):
        """Update lead status."""
        try:
            import sqlite3
            
            data = request.get_json() or {}
            new_status = data.get('status')
            
            if not new_status:
                return jsonify({'error': 'status parameter required'}), 400
            
            con = sqlite3.connect(DB_PATH)
            cur = con.cursor()
            
            cur.execute("""
                UPDATE leads SET status = ? WHERE id = ?
            """, (new_status, lead_id))
            
            con.commit()
            con.close()
            
            return jsonify({'success': True, 'status': new_status})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/leads/export/<format>', methods=['GET'])
    def api_leads_export(format):
        """Export leads in various formats."""
        try:
            import sqlite3
            import csv
            import io
            
            # Get filters from query string
            search = request.args.get('search', '')
            status = request.args.get('status', '')
            
            con = sqlite3.connect(DB_PATH)
            con.row_factory = sqlite3.Row
            cur = con.cursor()
            
            # Build query with filters
            where_clauses = []
            params = []
            
            if search:
                where_clauses.append("(name LIKE ? OR company LIKE ?)")
                search_pattern = f"%{search}%"
                params.extend([search_pattern, search_pattern])
            
            if status:
                where_clauses.append("status = ?")
                params.append(status)
            
            where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
            query = f"SELECT * FROM leads WHERE {where_sql} ORDER BY id DESC"
            
            cur.execute(query, params)
            rows = cur.fetchall()
            
            if not rows:
                con.close()
                return jsonify({'error': 'No leads to export'}), 404
            
            if format == 'csv':
                output = io.StringIO()
                writer = csv.DictWriter(output, fieldnames=rows[0].keys())
                writer.writeheader()
                for row in rows:
                    writer.writerow(dict(row))
                
                con.close()
                output.seek(0)
                return Response(
                    output.getvalue(),
                    mimetype='text/csv',
                    headers={'Content-Disposition': 'attachment;filename=leads.csv'}
                )
            
            elif format == 'xlsx':
                # XLSX export using openpyxl directly
                from openpyxl import Workbook
                from openpyxl.styles import Font
                
                wb = Workbook()
                ws = wb.active
                ws.title = "Leads"
                
                # Write header
                headers = list(rows[0].keys())
                ws.append(headers)
                
                # Style header
                for cell in ws[1]:
                    cell.font = Font(bold=True)
                
                # Write data
                for row in rows:
                    ws.append(list(row))
                
                con.close()
                
                output = io.BytesIO()
                wb.save(output)
                output.seek(0)
                
                return Response(
                    output.getvalue(),
                    mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    headers={'Content-Disposition': 'attachment;filename=leads.xlsx'}
                )
            
            elif format == 'pdf':
                # Simple PDF export using reportlab
                from reportlab.lib.pagesizes import A4
                from reportlab.lib import colors
                from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
                from reportlab.lib.styles import getSampleStyleSheet
                
                output = io.BytesIO()
                doc = SimpleDocTemplate(output, pagesize=A4)
                elements = []
                
                # Title
                styles = getSampleStyleSheet()
                title = Paragraph("LUCA - Lead Export", styles['Title'])
                elements.append(title)
                
                # Prepare data for table
                # Limit to 100 rows for PDF to keep file size reasonable
                PDF_EXPORT_LIMIT = 100
                data = [list(rows[0].keys())]  # Header
                for row in rows[:PDF_EXPORT_LIMIT]:
                    data.append([str(v) if v is not None else '' for v in row])
                
                # Create table
                table = Table(data)
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 8),
                    ('FONTSIZE', (0, 1), (-1, -1), 6),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                
                elements.append(table)
                doc.build(elements)
                
                con.close()
                output.seek(0)
                return Response(
                    output.getvalue(),
                    mimetype='application/pdf',
                    headers={'Content-Disposition': 'attachment;filename=leads.pdf'}
                )
            
            else:
                con.close()
                return jsonify({'error': 'Invalid format'}), 400
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    # ==================== Health API ====================
    
    @app.route('/api/health', methods=['GET'])
    def api_health():
        """Get system health information."""
        try:
            import sqlite3
            import os
            
            health_info = {
                'api_keys': {
                    'openai': 'unknown',
                    'google_cse': 'unknown',
                    'perplexity': 'unknown'
                },
                'circuit_breaker': [],
                'last_errors': [],
                'db_size_mb': 0,
                'uptime_hours': 0
            }
            
            # Check API keys from environment
            if os.getenv('OPENAI_API_KEY'):
                health_info['api_keys']['openai'] = 'configured'
            else:
                health_info['api_keys']['openai'] = 'missing'
            
            if os.getenv('GOOGLE_CSE_API_KEY'):
                health_info['api_keys']['google_cse'] = 'configured'
            else:
                health_info['api_keys']['google_cse'] = 'missing'
            
            if os.getenv('PERPLEXITY_API_KEY'):
                health_info['api_keys']['perplexity'] = 'configured'
            else:
                health_info['api_keys']['perplexity'] = 'missing'
            
            # Get database size
            if os.path.exists(DB_PATH):
                db_size_bytes = os.path.getsize(DB_PATH)
                health_info['db_size_mb'] = round(db_size_bytes / 1024 / 1024, 2)
            
            # Get recent errors from runs table
            try:
                con = sqlite3.connect(DB_PATH)
                con.row_factory = sqlite3.Row
                cur = con.cursor()
                
                cur.execute("""
                    SELECT id, status, error_message, started_at
                    FROM runs
                    WHERE status = 'error' OR error_message IS NOT NULL
                    ORDER BY id DESC
                    LIMIT 5
                """)
                
                error_rows = cur.fetchall()
                health_info['last_errors'] = [dict(row) for row in error_rows]
                
                con.close()
            except:
                pass
            
            return jsonify(health_info)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    return app


def add_log_entry(level: str, message: str):
    """
    Add a log entry to the queue for SSE streaming.
    
    Args:
        level: Log level (INFO, WARNING, ERROR)
        message: Log message
    """
    try:
        log_queue.put(json.dumps({
            'timestamp': time.time(),
            'level': level,
            'message': message
        }), block=False)
    except queue.Full:
        pass  # Drop message if queue is full


if __name__ == '__main__':
    import os
    app = create_app()
    debug_mode = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    print(f"🎯 LUCA Control Center starting on http://127.0.0.1:5056")
    print(f"⚠️  Debug mode: {debug_mode}")
    if not debug_mode:
        print(f"⚠️  This is a development server. Use a production WSGI server for production.")
    app.run(host='127.0.0.1', port=5056, debug=debug_mode)
