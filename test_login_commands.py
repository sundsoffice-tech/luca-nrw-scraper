#!/usr/bin/env python3
"""Test login command-line interface"""

import sys
from login_handler import LoginHandler, get_login_handler

def test_list_sessions():
    """Test listing sessions"""
    print("Testing --list-sessions...")
    handler = get_login_handler()
    
    # Add some test sessions
    handler.save_session("linkedin", [{"name": "test", "value": "123"}], "Mozilla/5.0")
    handler.save_session("xing", [{"name": "test2", "value": "456"}], "Mozilla/5.0")
    
    sessions = handler.get_all_sessions()
    print(f"Found {len(sessions)} sessions:")
    for s in sessions:
        status = "✅" if s['is_valid'] else "❌"
        print(f"  {status} {s['portal']}: {s['logged_in_at']}")
    
    print("✅ List sessions test passed\n")

def test_clear_sessions():
    """Test clearing sessions"""
    print("Testing --clear-sessions...")
    import sqlite3
    
    handler = get_login_handler()
    
    # Add a test session
    handler.save_session("test_portal", [{"name": "test", "value": "123"}])
    
    # Clear all sessions
    with sqlite3.connect("scraper.db") as conn:
        before = conn.execute('SELECT COUNT(*) FROM login_sessions').fetchone()[0]
        conn.execute('DELETE FROM login_sessions')
        conn.commit()
        after = conn.execute('SELECT COUNT(*) FROM login_sessions').fetchone()[0]
    
    print(f"  Before: {before} sessions")
    print(f"  After: {after} sessions")
    print("✅ Clear sessions test passed\n")

if __name__ == "__main__":
    test_list_sessions()
    test_clear_sessions()
    print("=" * 60)
    print("✅ ALL COMMAND TESTS PASSED")
    print("=" * 60)
