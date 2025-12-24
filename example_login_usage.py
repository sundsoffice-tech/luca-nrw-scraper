#!/usr/bin/env python3
"""
Example: Using the Login Handler
Demonstrates how to use the human-in-the-loop login system
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from login_handler import LoginHandler, get_login_handler


def example_1_basic_usage():
    """Example 1: Basic login detection and session management"""
    print("=" * 60)
    print("Example 1: Basic Usage")
    print("=" * 60)
    
    handler = get_login_handler()
    
    # Simulate a login-required response
    response_text = "Bitte anmelden um fortzufahren"
    status_code = 200
    url = "https://www.linkedin.com/in/someprofile"
    
    print(f"\n1. Checking if login is required...")
    print(f"   URL: {url}")
    print(f"   Status: {status_code}")
    print(f"   Response contains: '{response_text}'")
    
    if handler.detect_login_required(response_text, status_code, url):
        print("   ✅ Login required detected!")
        
        portal = handler.get_portal_from_url(url)
        print(f"   Portal identified: {portal}")
        
        # Check if we have a valid session
        if handler.has_valid_session(portal):
            print(f"   ✅ Valid session exists for {portal}")
            cookies = handler.get_session_cookies(portal)
            print(f"   Loaded {len(cookies)} cookies")
        else:
            print(f"   ⚠️  No valid session for {portal}")
            print(f"   To login: python scriptname.py --login {portal}")
    else:
        print("   ✅ No login required")
    
    print()


def example_2_session_management():
    """Example 2: Creating and managing sessions"""
    print("=" * 60)
    print("Example 2: Session Management")
    print("=" * 60)
    
    handler = get_login_handler()
    
    # Create a test session
    test_cookies = [
        {"name": "session_id", "value": "abc123", "domain": ".example.com"},
        {"name": "user_token", "value": "xyz789", "domain": ".example.com"}
    ]
    
    print("\n1. Creating test session...")
    handler.save_session("example_portal", test_cookies, "Mozilla/5.0")
    print("   ✅ Session saved")
    
    print("\n2. Retrieving session...")
    loaded_cookies = handler.get_session_cookies("example_portal")
    print(f"   ✅ Loaded {len(loaded_cookies)} cookies:")
    for cookie in loaded_cookies:
        print(f"      - {cookie['name']}: {cookie['value'][:10]}...")
    
    print("\n3. Checking session validity...")
    is_valid = handler.has_valid_session("example_portal")
    print(f"   ✅ Session is {'valid' if is_valid else 'invalid'}")
    
    print("\n4. Listing all sessions...")
    sessions = handler.get_all_sessions()
    print(f"   Found {len(sessions)} session(s):")
    for s in sessions:
        status = "✅" if s['is_valid'] else "❌"
        print(f"   {status} {s['portal']}: {s['logged_in_at']}")
    
    print("\n5. Invalidating session...")
    handler.invalidate_session("example_portal")
    print("   ✅ Session invalidated")
    
    is_valid_after = handler.has_valid_session("example_portal")
    print(f"   Session is now: {'valid' if is_valid_after else 'invalid'}")
    
    print()


def example_3_portal_detection():
    """Example 3: Portal detection from URLs"""
    print("=" * 60)
    print("Example 3: Portal Detection")
    print("=" * 60)
    
    handler = get_login_handler()
    
    test_urls = [
        "https://www.linkedin.com/in/johndoe",
        "https://www.xing.com/profile/janedoe",
        "https://www.kleinanzeigen.de/s-stellengesuche/vertrieb",
        "https://de.indeed.com/jobs?q=sales",
        "https://www.unknown-website.com/page",
    ]
    
    print("\nDetecting portals from URLs:")
    for url in test_urls:
        portal = handler.get_portal_from_url(url)
        if portal:
            print(f"   ✅ {url}")
            print(f"      → Portal: {portal}")
        else:
            print(f"   ❓ {url}")
            print(f"      → Portal: Unknown")
    
    print()


def example_4_login_patterns():
    """Example 4: Login pattern detection"""
    print("=" * 60)
    print("Example 4: Login Pattern Detection")
    print("=" * 60)
    
    handler = get_login_handler()
    
    test_cases = [
        # (text, status_code, url, should_detect)
        ("Bitte anmelden um fortzufahren", 200, "https://example.com", True),
        ("Please log in to continue", 200, "https://example.com", True),
        ("CAPTCHA verification required", 200, "https://example.com", True),
        ("", 403, "https://example.com", True),
        ("", 200, "https://example.com/login", True),
        ("Welcome to our website", 200, "https://example.com", False),
    ]
    
    print("\nTesting login detection patterns:")
    for i, (text, status, url, expected) in enumerate(test_cases, 1):
        detected = handler.detect_login_required(text, status, url)
        match = "✅" if detected == expected else "❌"
        print(f"\n   {match} Test {i}:")
        if text:
            print(f"      Text: '{text[:40]}...'")
        print(f"      Status: {status}")
        print(f"      URL: {url}")
        print(f"      Expected: {expected}, Got: {detected}")
    
    print()


def main():
    """Run all examples"""
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 10 + "LOGIN HANDLER USAGE EXAMPLES" + " " * 20 + "║")
    print("╚" + "═" * 58 + "╝")
    print()
    
    example_1_basic_usage()
    example_2_session_management()
    example_3_portal_detection()
    example_4_login_patterns()
    
    print("=" * 60)
    print("Examples completed!")
    print("=" * 60)
    print("\nNext steps:")
    print("  1. Try: python scriptname.py --login linkedin")
    print("  2. Try: python scriptname.py --list-sessions")
    print("  3. Try: python dashboard.py")
    print("  4. Read: LOGIN_SYSTEM_GUIDE.md")
    print()


if __name__ == "__main__":
    main()
