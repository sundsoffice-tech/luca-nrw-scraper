#!/usr/bin/env python3
"""
Tests for Login Handler
"""

import os
import json
import sqlite3
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest

# Import the module under test
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from login_handler import LoginHandler, get_login_handler, check_and_handle_login


@pytest.fixture
def temp_db():
    """Create a temporary database for testing"""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    try:
        os.unlink(path)
    except:
        pass


@pytest.fixture
def handler(temp_db):
    """Create a LoginHandler instance with temporary database"""
    return LoginHandler(db_path=temp_db)


class TestLoginDetection:
    """Test login requirement detection"""
    
    def test_detect_403_status(self, handler):
        """Should detect login required for 403 status code"""
        result = handler.detect_login_required("", 403, "https://example.com")
        assert result is True
    
    def test_detect_401_status(self, handler):
        """Should detect login required for 401 status code"""
        result = handler.detect_login_required("", 401, "https://example.com")
        assert result is True
    
    def test_detect_429_status(self, handler):
        """Should detect login required for 429 (rate limit) status code"""
        result = handler.detect_login_required("", 429, "https://example.com")
        assert result is True
    
    def test_detect_login_text_german(self, handler):
        """Should detect German login text"""
        text = "Bitte anmelden um fortzufahren"
        result = handler.detect_login_required(text, 200, "https://example.com")
        assert result is True
    
    def test_detect_login_text_english(self, handler):
        """Should detect English login text"""
        text = "Please log in to continue"
        result = handler.detect_login_required(text, 200, "https://example.com")
        assert result is True
    
    def test_detect_captcha(self, handler):
        """Should detect captcha requirement"""
        text = "Please complete the CAPTCHA to continue"
        result = handler.detect_login_required(text, 200, "https://example.com")
        assert result is True
    
    def test_detect_login_url(self, handler):
        """Should detect login from URL pattern"""
        result = handler.detect_login_required("", 200, "https://example.com/login")
        assert result is True
    
    def test_no_login_required(self, handler):
        """Should not detect login when not required"""
        text = "Welcome to our site"
        result = handler.detect_login_required(text, 200, "https://example.com")
        assert result is False


class TestPortalDetection:
    """Test portal name detection from URLs"""
    
    def test_detect_kleinanzeigen(self, handler):
        """Should detect kleinanzeigen portal"""
        url = "https://www.kleinanzeigen.de/s-stellengesuche/123"
        result = handler.get_portal_from_url(url)
        assert result == "kleinanzeigen"
    
    def test_detect_linkedin(self, handler):
        """Should detect LinkedIn portal"""
        url = "https://www.linkedin.com/in/username"
        result = handler.get_portal_from_url(url)
        assert result == "linkedin"
    
    def test_detect_xing(self, handler):
        """Should detect XING portal"""
        url = "https://www.xing.com/profile/test"
        result = handler.get_portal_from_url(url)
        assert result == "xing"
    
    def test_detect_indeed(self, handler):
        """Should detect Indeed portal"""
        url = "https://de.indeed.com/jobs"
        result = handler.get_portal_from_url(url)
        assert result == "indeed"
    
    def test_unknown_portal(self, handler):
        """Should return None for unknown portal"""
        url = "https://www.unknown-site.com/page"
        result = handler.get_portal_from_url(url)
        assert result is None


class TestSessionManagement:
    """Test session storage and retrieval"""
    
    def test_save_and_load_session(self, handler):
        """Should save and load session cookies"""
        cookies = [
            {"name": "session_id", "value": "abc123", "domain": ".linkedin.com"},
            {"name": "user_token", "value": "xyz789", "domain": ".linkedin.com"}
        ]
        
        handler.save_session("linkedin", cookies, "Mozilla/5.0")
        loaded = handler.get_session_cookies("linkedin")
        
        assert loaded is not None
        assert len(loaded) == 2
        assert loaded[0]["name"] == "session_id"
        assert loaded[0]["value"] == "abc123"
    
    def test_session_validity_check(self, handler):
        """Should correctly check session validity"""
        cookies = [{"name": "test", "value": "123"}]
        handler.save_session("test_portal", cookies)
        
        assert handler.has_valid_session("test_portal") is True
        assert handler.has_valid_session("nonexistent_portal") is False
    
    def test_invalidate_session(self, handler):
        """Should invalidate session"""
        cookies = [{"name": "test", "value": "123"}]
        handler.save_session("test_portal", cookies)
        
        assert handler.has_valid_session("test_portal") is True
        
        handler.invalidate_session("test_portal")
        assert handler.has_valid_session("test_portal") is False
    
    def test_session_expiration(self, handler, temp_db):
        """Should detect expired sessions"""
        cookies = [{"name": "test", "value": "123"}]
        
        # Manually insert an expired session
        expired_date = (datetime.now() - timedelta(days=1)).isoformat()
        with sqlite3.connect(temp_db) as conn:
            conn.execute('''
                INSERT INTO login_sessions 
                (portal, cookies_json, user_agent, logged_in_at, expires_at, is_valid)
                VALUES (?, ?, ?, datetime('now'), ?, 1)
            ''', ("expired_portal", json.dumps(cookies), "test", expired_date))
            conn.commit()
        
        # Should detect as not valid due to expiration
        assert handler.has_valid_session("expired_portal") is False
    
    def test_get_all_sessions(self, handler):
        """Should retrieve all sessions"""
        cookies1 = [{"name": "test1", "value": "123"}]
        cookies2 = [{"name": "test2", "value": "456"}]
        
        handler.save_session("portal1", cookies1)
        handler.save_session("portal2", cookies2)
        
        sessions = handler.get_all_sessions()
        assert len(sessions) >= 2
        
        portals = [s["portal"] for s in sessions]
        assert "portal1" in portals
        assert "portal2" in portals


class TestDatabaseIntegration:
    """Test database schema and operations"""
    
    def test_database_initialization(self, temp_db):
        """Should create login_sessions table on init"""
        handler = LoginHandler(db_path=temp_db)
        
        with sqlite3.connect(temp_db) as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='login_sessions'"
            )
            tables = cursor.fetchall()
            assert len(tables) == 1
    
    def test_session_backup_file(self, handler, tmp_path):
        """Should create backup JSON file for sessions"""
        # Temporarily change sessions directory
        old_sessions_dir = handler.sessions_dir
        handler.sessions_dir = Path(tmp_path)
        
        try:
            cookies = [{"name": "test", "value": "123"}]
            handler.save_session("test_portal", cookies, "Mozilla/5.0")
            
            backup_file = handler.sessions_dir / "test_portal_cookies.json"
            assert backup_file.exists()
            
            with open(backup_file) as f:
                data = json.load(f)
                assert data["portal"] == "test_portal"
                assert len(data["cookies"]) == 1
        finally:
            handler.sessions_dir = old_sessions_dir


class TestHelperFunctions:
    """Test module-level helper functions"""
    
    def test_get_login_handler_singleton(self):
        """Should return singleton instance"""
        handler1 = get_login_handler()
        handler2 = get_login_handler()
        assert handler1 is handler2
    
    def test_check_and_handle_login_no_login_required(self, handler):
        """Should return None when no login required"""
        text = "Normal page content"
        result = check_and_handle_login(text, 200, "https://example.com")
        assert result is None
    
    def test_check_and_handle_login_unknown_portal(self, handler):
        """Should return None for unknown portal"""
        text = "Please log in"
        result = check_and_handle_login(text, 200, "https://unknown-site.com")
        assert result is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
