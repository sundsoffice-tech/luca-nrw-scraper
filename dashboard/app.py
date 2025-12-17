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
    app = create_app()
    print(f"🎯 LUCA Control Center starting on http://127.0.0.1:5056")
    app.run(host='127.0.0.1', port=5056, debug=True)
