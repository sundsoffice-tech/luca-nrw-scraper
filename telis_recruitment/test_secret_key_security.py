"""
Test SECRET_KEY security enforcement in settings.py

This test ensures that the Django application fails to start when:
1. SECRET_KEY environment variable is not set
2. SECRET_KEY is set to an insecure placeholder value
3. SECRET_KEY is too short
"""

import os
import sys
import pytest
from pathlib import Path


def test_missing_secret_key():
    """Test that settings raises ValueError when SECRET_KEY is missing"""
    # Save current SECRET_KEY
    original_key = os.environ.get('SECRET_KEY')
    
    try:
        # Remove SECRET_KEY from environment
        if 'SECRET_KEY' in os.environ:
            del os.environ['SECRET_KEY']
        
        # Force reload of settings module
        if 'telis.settings' in sys.modules:
            del sys.modules['telis.settings']
        
        # Attempting to import settings should raise ValueError
        with pytest.raises(ValueError, match="SECRET_KEY environment variable is not set"):
            import telis.settings
    finally:
        # Restore original SECRET_KEY
        if original_key:
            os.environ['SECRET_KEY'] = original_key
        # Clean up module cache
        if 'telis.settings' in sys.modules:
            del sys.modules['telis.settings']


def test_insecure_placeholder_key():
    """Test that settings raises ValueError for insecure placeholder keys"""
    # This list matches INSECURE_KEYS in settings.py
    insecure_keys = [
        'django-insecure-please-change-me-in-production',
        'your-secret-key-here',
        'changeme',
        'insecure',
    ]
    
    # Also test keys starting with 'django-insecure-'
    additional_insecure = [
        'django-insecure-test123',
        'django-insecure-another-key',
    ]
    
    # Save current SECRET_KEY
    original_key = os.environ.get('SECRET_KEY')
    
    # Test explicit INSECURE_KEYS list
    for insecure_key in insecure_keys:
        try:
            # Set insecure key
            os.environ['SECRET_KEY'] = insecure_key
            
            # Force reload of settings module
            if 'telis.settings' in sys.modules:
                del sys.modules['telis.settings']
            
            # Attempting to import settings should raise ValueError
            with pytest.raises(ValueError, match="SECRET_KEY is set to an insecure value"):
                import telis.settings
        finally:
            # Restore original SECRET_KEY
            if original_key:
                os.environ['SECRET_KEY'] = original_key
            # Clean up module cache
            if 'telis.settings' in sys.modules:
                del sys.modules['telis.settings']
    
    # Test keys starting with 'django-insecure-'
    for insecure_key in additional_insecure:
        try:
            # Set insecure key
            os.environ['SECRET_KEY'] = insecure_key
            
            # Force reload of settings module
            if 'telis.settings' in sys.modules:
                del sys.modules['telis.settings']
            
            # Attempting to import settings should raise ValueError
            with pytest.raises(ValueError, match="SECRET_KEY is set to an insecure value"):
                import telis.settings
        finally:
            # Restore original SECRET_KEY
            if original_key:
                os.environ['SECRET_KEY'] = original_key
            # Clean up module cache
            if 'telis.settings' in sys.modules:
                del sys.modules['telis.settings']


def test_short_secret_key():
    """Test that settings raises ValueError when SECRET_KEY is too short"""
    # Save current SECRET_KEY
    original_key = os.environ.get('SECRET_KEY')
    
    try:
        # Set a short key (less than 50 characters)
        os.environ['SECRET_KEY'] = 'short-key-12345'
        
        # Force reload of settings module
        if 'telis.settings' in sys.modules:
            del sys.modules['telis.settings']
        
        # Attempting to import settings should raise ValueError
        with pytest.raises(ValueError, match="SECRET_KEY must be at least 50 characters long"):
            import telis.settings
    finally:
        # Restore original SECRET_KEY
        if original_key:
            os.environ['SECRET_KEY'] = original_key
        # Clean up module cache
        if 'telis.settings' in sys.modules:
            del sys.modules['telis.settings']


def test_valid_secret_key():
    """Test that settings loads successfully with a valid SECRET_KEY"""
    # Save current SECRET_KEY
    original_key = os.environ.get('SECRET_KEY')
    
    try:
        # Generate a valid key (50+ characters, doesn't start with 'django-insecure-')
        # Using a safe prefix that won't be rejected by future validation logic
        valid_key = 'prod-secure-key-' + 'a' * 50 + '-valid-production-key-12345'
        os.environ['SECRET_KEY'] = valid_key
        
        # Force reload of settings module
        if 'telis.settings' in sys.modules:
            del sys.modules['telis.settings']
        
        # Should import successfully
        import telis.settings
        
        # Verify the key was set correctly
        assert telis.settings.SECRET_KEY == valid_key
    finally:
        # Restore original SECRET_KEY
        if original_key:
            os.environ['SECRET_KEY'] = original_key
        # Clean up module cache
        if 'telis.settings' in sys.modules:
            del sys.modules['telis.settings']


if __name__ == '__main__':
    # Run tests with pytest
    pytest.main([__file__, '-v'])
