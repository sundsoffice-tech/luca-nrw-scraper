#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Convenience script to start the LUCA Control Center dashboard.
"""

import os
import sys

if __name__ == '__main__':
    # Add current directory to path
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    from dashboard.app import create_app
    
    # Use scraper.db in the same directory
    db_path = os.path.join(os.path.dirname(__file__), 'scraper.db')
    
    # Create and run app
    app = create_app(db_path=db_path)
    
    print(f"🎯 LUCA Control Center starting...")
    print(f"📊 Dashboard: http://127.0.0.1:5056")
    print(f"📁 Database: {db_path}")
    print(f"\nPress Ctrl+C to stop")
    
    app.run(host='127.0.0.1', port=5056, debug=False)
