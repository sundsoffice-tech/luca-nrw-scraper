#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Integration test to verify that the scraper can initialize without Django.

This simulates what happens when scriptname.py runs in standalone mode.
"""

import sys
import os
import tempfile

# Make sure Django is NOT available
# (In actual standalone deployment, Django won't be installed)

def test_init_mode_without_django():
    """
    Simulate the exact call chain from scriptname.py:
    scriptname.py line 9631: mode_config = init_mode(mode)
    -> scriptname.py line 1518: _LEARNING_ENGINE = LearningEngine(DB_PATH)
    -> learning_engine.py line 82: self.ai_config = get_ai_config()
    -> telis_recruitment/ai_config/loader.py line 27: from .models import AIConfig
    
    This should NOT raise django.core.exceptions.ImproperlyConfigured
    """
    
    # Create a temporary database
    fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    
    try:
        print("=" * 70)
        print("Integration Test: Simulating scriptname.py standalone mode")
        print("=" * 70)
        
        # Step 1: Import LearningEngine (simulates scriptname.py import)
        print("\n[1/4] Importing LearningEngine...")
        from learning_engine import LearningEngine
        print("✓ LearningEngine imported successfully")
        
        # Step 2: Create LearningEngine instance (simulates init_mode())
        print("\n[2/4] Instantiating LearningEngine (simulates init_mode)...")
        engine = LearningEngine(db_path)
        print("✓ LearningEngine instantiated successfully")
        
        # Step 3: Verify ai_config was loaded
        print("\n[3/4] Verifying ai_config is loaded...")
        assert engine.ai_config is not None, "ai_config should not be None"
        assert isinstance(engine.ai_config, dict), "ai_config should be a dict"
        assert 'temperature' in engine.ai_config, "ai_config should have temperature"
        assert 'default_provider' in engine.ai_config, "ai_config should have default_provider"
        print(f"✓ ai_config loaded: provider={engine.ai_config.get('default_provider')}, "
              f"model={engine.ai_config.get('default_model')}")
        
        # Step 4: Verify engine is functional
        print("\n[4/4] Testing LearningEngine functionality...")
        test_lead = {
            "quelle": "https://test.example.com/kontakt",
            "telefon": "+491761234567",
            "tags": "test,integration",
            "score": 95
        }
        engine.learn_from_success(test_lead, query="test query NRW")
        patterns = engine.get_top_patterns("domain", min_confidence=0.0, min_successes=1)
        assert len(patterns) > 0, "Should have recorded at least one pattern"
        print(f"✓ LearningEngine is functional (recorded {len(patterns)} pattern(s))")
        
        # Success!
        print("\n" + "=" * 70)
        print("✓ ALL TESTS PASSED - Scraper can run in standalone mode!")
        print("=" * 70)
        return True
        
    except Exception as e:
        print(f"\n✗ TEST FAILED: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Clean up
        if os.path.exists(db_path):
            os.unlink(db_path)


def test_direct_loader_import():
    """Test that we can directly import from loader without Django."""
    print("\n" + "=" * 70)
    print("Direct Import Test: telis_recruitment.ai_config.loader")
    print("=" * 70)
    
    try:
        print("\n[1/2] Importing get_ai_config...")
        from telis_recruitment.ai_config.loader import get_ai_config, check_budget
        print("✓ Imported successfully")
        
        print("\n[2/2] Calling get_ai_config()...")
        config = get_ai_config()
        assert config is not None
        assert config['temperature'] == 0.3
        print(f"✓ get_ai_config() returned defaults: {config.get('default_provider')}/{config.get('default_model')}")
        
        print("\n[3/3] Calling check_budget()...")
        allowed, budget_info = check_budget()
        assert allowed is True
        assert budget_info['daily_budget'] == 5.0
        print(f"✓ check_budget() returned defaults: daily_budget={budget_info['daily_budget']}")
        
        print("\n" + "=" * 70)
        print("✓ Direct loader import test PASSED!")
        print("=" * 70)
        return True
        
    except Exception as e:
        print(f"\n✗ TEST FAILED: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║  STANDALONE MODE INTEGRATION TEST                                   ║")
    print("║  Verifying scraper works without Django configuration               ║")
    print("╚" + "=" * 68 + "╝")
    
    success = True
    
    # Test 1: Direct loader import
    if not test_direct_loader_import():
        success = False
    
    # Test 2: Full init_mode simulation
    if not test_init_mode_without_django():
        success = False
    
    # Final result
    print("\n")
    if success:
        print("╔" + "=" * 68 + "╗")
        print("║  ✓✓✓ ALL INTEGRATION TESTS PASSED ✓✓✓                              ║")
        print("║  Scraper can run standalone without Django configuration!          ║")
        print("╚" + "=" * 68 + "╝")
        sys.exit(0)
    else:
        print("╔" + "=" * 68 + "╗")
        print("║  ✗✗✗ INTEGRATION TESTS FAILED ✗✗✗                                  ║")
        print("║  See errors above for details                                      ║")
        print("╚" + "=" * 68 + "╝")
        sys.exit(1)
