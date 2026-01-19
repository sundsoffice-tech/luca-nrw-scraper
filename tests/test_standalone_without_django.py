# -*- coding: utf-8 -*-
"""
Test that learning_engine works in standalone mode without Django.

This test ensures that the scraper can run without Django being configured,
which is the case when running standalone (not via Django server).
"""

import pytest
import os
import sys
import tempfile


def test_learning_engine_without_django():
    """Test that LearningEngine can be instantiated without Django."""
    # Ensure Django is NOT configured/available
    # This simulates the standalone environment
    
    # Create a temporary database
    fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    
    try:
        # Import and instantiate LearningEngine
        # This should NOT raise ImproperlyConfigured error
        from learning_engine import LearningEngine
        
        engine = LearningEngine(db_path)
        
        # Verify that ai_config was loaded with defaults
        assert engine.ai_config is not None
        assert 'temperature' in engine.ai_config
        assert 'default_provider' in engine.ai_config
        assert 'default_model' in engine.ai_config
        
        # Verify default values are present
        assert engine.ai_config['temperature'] == 0.3
        assert engine.ai_config['default_provider'] == 'OpenAI'
        assert engine.ai_config['default_model'] == 'gpt-4o-mini'
        
        # Verify that learning engine is functional
        lead_data = {
            "quelle": "https://example.com/test",
            "telefon": "+491761234567",
            "tags": "test",
            "score": 90
        }
        
        # This should not raise any errors
        engine.learn_from_success(lead_data, query="test query")
        
        # Verify patterns were recorded
        patterns = engine.get_top_patterns("domain", min_confidence=0.0, min_successes=1)
        assert len(patterns) > 0
        
    finally:
        # Clean up
        if os.path.exists(db_path):
            os.unlink(db_path)


def test_loader_get_ai_config_without_django():
    """Test that get_ai_config() works without Django configured."""
    # Import the loader function
    from telis_recruitment.ai_config.loader import get_ai_config
    
    # This should NOT raise ImproperlyConfigured error
    config = get_ai_config()
    
    # Verify defaults are returned
    assert config is not None
    assert config['temperature'] == 0.3
    assert config['top_p'] == 1.0
    assert config['max_tokens'] == 4000
    assert config['learning_rate'] == 0.01
    assert config['daily_budget'] == 5.0
    assert config['monthly_budget'] == 150.0
    assert config['confidence_threshold'] == 0.35
    assert config['retry_limit'] == 2
    assert config['timeout_seconds'] == 30
    assert config['default_provider'] == 'OpenAI'
    assert config['default_model'] == 'gpt-4o-mini'


def test_active_learning_engine_without_django():
    """Test that ActiveLearningEngine can be instantiated without Django."""
    # Create a temporary database
    fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    
    try:
        # First initialize base learning engine to create tables
        from learning_engine import LearningEngine, ActiveLearningEngine
        
        base_engine = LearningEngine(db_path)
        
        # Now instantiate ActiveLearningEngine
        # This should NOT raise any errors
        active_engine = ActiveLearningEngine(db_path)
        
        # Verify it's functional
        active_engine.record_portal_result(
            portal="test_portal",
            urls_crawled=100,
            leads_found=10,
            leads_with_phone=2,
            run_id=1
        )
        
        # Get stats (should not fail)
        stats = active_engine.get_portal_stats()
        assert "test_portal" in stats
        
    finally:
        # Clean up
        if os.path.exists(db_path):
            os.unlink(db_path)


def test_standalone_mode_simulation():
    """
    Simulate the exact scenario from the problem statement:
    scriptname.py calling init_mode() which instantiates LearningEngine.
    """
    # Create a temporary database
    fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    
    try:
        # Simulate what happens in scriptname.py at line 1518
        # when init_mode() is called
        from learning_engine import LearningEngine
        
        # This is the call that was failing
        engine = LearningEngine(db_path)
        
        # At line 82 in learning_engine.py, get_ai_config() is called
        # This should now work without Django
        assert engine.ai_config is not None
        assert isinstance(engine.ai_config, dict)
        
        # Verify the engine is fully functional
        assert hasattr(engine, 'db_path')
        assert hasattr(engine, 'ai_config')
        assert hasattr(engine, 'learn_from_success')
        assert hasattr(engine, 'get_top_patterns')
        
    finally:
        # Clean up
        if os.path.exists(db_path):
            os.unlink(db_path)


if __name__ == '__main__':
    # Run tests when executed directly
    pytest.main([__file__, '-v'])
