#!/usr/bin/env python3
"""
Simple manual tests for Login Handler (without pytest dependency)
"""

import os
import sys
import tempfile
import json
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from login_handler import LoginHandler, get_login_handler, check_and_handle_login


def test_login_detection():
    """Test login requirement detection"""
    print("Testing login detection...")
    
    # Create temporary database
    fd, temp_db = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    
    try:
        handler = LoginHandler(db_path=temp_db)
        
        # Test 403 status
        assert handler.detect_login_required("", 403, "https://example.com") is True
        print("  ✓ Detected 403 status")
        
        # Test login text
        assert handler.detect_login_required("Bitte anmelden", 200, "https://example.com") is True
        print("  ✓ Detected login text (German)")
        
        assert handler.detect_login_required("Please log in", 200, "https://example.com") is True
        print("  ✓ Detected login text (English)")
        
        # Test captcha
        assert handler.detect_login_required("CAPTCHA verification", 200, "https://example.com") is True
        print("  ✓ Detected captcha")
        
        # Test login URL
        assert handler.detect_login_required("", 200, "https://example.com/login") is True
        print("  ✓ Detected login URL")
        
        # Test no login required
        assert handler.detect_login_required("Normal content", 200, "https://example.com") is False
        print("  ✓ No false positive")
        
        print("✅ Login detection tests passed\n")
    finally:
        try:
            os.unlink(temp_db)
        except:
            pass


def test_portal_detection():
    """Test portal name detection"""
    print("Testing portal detection...")
    
    fd, temp_db = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    
    try:
        handler = LoginHandler(db_path=temp_db)
        
        # Test various portals
        assert handler.get_portal_from_url("https://www.kleinanzeigen.de/s-stellengesuche/123") == "kleinanzeigen"
        print("  ✓ Detected kleinanzeigen")
        
        assert handler.get_portal_from_url("https://www.linkedin.com/in/username") == "linkedin"
        print("  ✓ Detected LinkedIn")
        
        assert handler.get_portal_from_url("https://www.xing.com/profile/test") == "xing"
        print("  ✓ Detected XING")
        
        assert handler.get_portal_from_url("https://de.indeed.com/jobs") == "indeed"
        print("  ✓ Detected Indeed")
        
        assert handler.get_portal_from_url("https://www.unknown-site.com") is None
        print("  ✓ Unknown portal returns None")
        
        print("✅ Portal detection tests passed\n")
    finally:
        try:
            os.unlink(temp_db)
        except:
            pass


def test_session_management():
    """Test session storage and retrieval"""
    print("Testing session management...")
    
    fd, temp_db = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    
    try:
        handler = LoginHandler(db_path=temp_db)
        
        # Test save and load
        cookies = [
            {"name": "session_id", "value": "abc123", "domain": ".linkedin.com"},
            {"name": "user_token", "value": "xyz789", "domain": ".linkedin.com"}
        ]
        
        handler.save_session("linkedin", cookies, "Mozilla/5.0")
        loaded = handler.get_session_cookies("linkedin")
        
        assert loaded is not None
        assert len(loaded) == 2
        assert loaded[0]["name"] == "session_id"
        print("  ✓ Save and load session")
        
        # Test validity check
        assert handler.has_valid_session("linkedin") is True
        print("  ✓ Valid session detected")
        
        assert handler.has_valid_session("nonexistent") is False
        print("  ✓ Nonexistent session detected")
        
        # Test invalidation
        handler.invalidate_session("linkedin")
        assert handler.has_valid_session("linkedin") is False
        print("  ✓ Session invalidation works")
        
        # Test get all sessions
        handler.save_session("portal1", [{"name": "test1", "value": "123"}])
        handler.save_session("portal2", [{"name": "test2", "value": "456"}])
        
        sessions = handler.get_all_sessions()
        assert len(sessions) >= 2
        print(f"  ✓ Retrieved {len(sessions)} sessions")
        
        print("✅ Session management tests passed\n")
    finally:
        try:
            os.unlink(temp_db)
        except:
            pass


def test_database_schema():
    """Test database initialization"""
    print("Testing database schema...")
    
    fd, temp_db = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    
    try:
        import sqlite3
        
        handler = LoginHandler(db_path=temp_db)
        
        # Check table exists
        with sqlite3.connect(temp_db) as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='login_sessions'"
            )
            tables = cursor.fetchall()
            assert len(tables) == 1
            print("  ✓ login_sessions table created")
        
        # Check table structure
        with sqlite3.connect(temp_db) as conn:
            cursor = conn.execute("PRAGMA table_info(login_sessions)")
            columns = [row[1] for row in cursor.fetchall()]
            expected = ['portal', 'cookies_json', 'user_agent', 'logged_in_at', 'expires_at', 'is_valid']
            for col in expected:
                assert col in columns, f"Column {col} missing"
            print(f"  ✓ All {len(expected)} columns present")
        
        print("✅ Database schema tests passed\n")
    finally:
        try:
            os.unlink(temp_db)
        except:
            pass


def test_helper_functions():
    """Test module-level helper functions"""
    print("Testing helper functions...")
    
    # Test singleton
    handler1 = get_login_handler()
    handler2 = get_login_handler()
    assert handler1 is handler2
    print("  ✓ Singleton pattern works")
    
    # Test check_and_handle_login with no login required
    result = check_and_handle_login("Normal content", 200, "https://example.com")
    assert result is None
    print("  ✓ No action when login not required")
    
    # Test with unknown portal
    result = check_and_handle_login("Please log in", 200, "https://unknown-site.com")
    assert result is None
    print("  ✓ No action for unknown portal")
    
    print("✅ Helper function tests passed\n")


def main():
    """Run all tests"""
    print("=" * 60)
    print("LOGIN HANDLER TEST SUITE")
    print("=" * 60 + "\n")
    
    try:
        test_login_detection()
        test_portal_detection()
        test_session_management()
        test_database_schema()
        test_helper_functions()
        
        print("=" * 60)
        print("✅ ALL TESTS PASSED")
        print("=" * 60)
        return 0
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
