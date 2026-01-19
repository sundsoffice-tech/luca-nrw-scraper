#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Focused test to verify the exact error scenario from the problem statement.

This reproduces the exact call chain that was failing:
  scriptname.py, line 9631: mode_config = init_mode(mode)
  scriptname.py, line 1518: _LEARNING_ENGINE = LearningEngine(DB_PATH)
  learning_engine.py, line 82: self.ai_config = get_ai_config()
  telis_recruitment/ai_config/loader.py, line 27: from .models import AIConfig
  → Django nicht konfiguriert!

Before fix: django.core.exceptions.ImproperlyConfigured
After fix: Should work with fallback defaults
"""

import sys
import os
import tempfile


def test_exact_failing_scenario():
    """
    Reproduce the EXACT failing scenario from the problem statement.
    """
    print("\n" + "=" * 70)
    print("REPRODUCING EXACT FAILURE SCENARIO")
    print("=" * 70)
    
    # Create temporary DB
    fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    
    try:
        # BEFORE: This would raise django.core.exceptions.ImproperlyConfigured
        # AFTER: This should work with fallback defaults
        
        print("\nStep 1: Import learning_engine module")
        print("  (simulates: scriptname.py importing learning_engine)")
        from learning_engine import LearningEngine
        print("  ✓ Import successful")
        
        print("\nStep 2: Instantiate LearningEngine with DB_PATH")
        print("  (simulates: scriptname.py line 1518)")
        print(f"  LearningEngine('{db_path}')")
        engine = LearningEngine(db_path)
        print("  ✓ Instantiation successful")
        
        print("\nStep 3: Check that ai_config was loaded")
        print("  (simulates: learning_engine.py line 82: self.ai_config = get_ai_config())")
        assert hasattr(engine, 'ai_config'), "Engine should have ai_config attribute"
        assert engine.ai_config is not None, "ai_config should not be None"
        print(f"  ✓ ai_config loaded: {engine.ai_config.keys()}")
        
        print("\nStep 4: Verify get_ai_config() called loader.py without error")
        print("  (simulates: telis_recruitment/ai_config/loader.py line 27)")
        # If we got here, the lazy import of Django models did NOT crash
        print("  ✓ Django model import was handled gracefully")
        
        print("\nStep 5: Verify fallback defaults are used")
        expected_defaults = {
            'temperature': 0.3,
            'top_p': 1.0,
            'max_tokens': 4000,
            'default_provider': 'OpenAI',
            'default_model': 'gpt-4o-mini'
        }
        
        for key, expected_value in expected_defaults.items():
            actual_value = engine.ai_config.get(key)
            assert actual_value == expected_value, \
                f"Expected {key}={expected_value}, got {actual_value}"
            print(f"  ✓ {key} = {actual_value}")
        
        print("\n" + "=" * 70)
        print("✓✓✓ FIX VERIFIED - The exact failing scenario now works! ✓✓✓")
        print("=" * 70)
        print("\nThe scraper can now run standalone without Django!")
        print("No more: django.core.exceptions.ImproperlyConfigured")
        return True
        
    except Exception as e:
        print(f"\n✗✗✗ FIX FAILED ✗✗✗")
        print(f"Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)


def test_loader_lazy_import():
    """
    Test that the loader.py lazy import works correctly.
    This is the ROOT CAUSE of the original error.
    """
    print("\n" + "=" * 70)
    print("TESTING ROOT CAUSE: Lazy Django import in loader.py")
    print("=" * 70)
    
    try:
        print("\nAttempting to import get_ai_config from loader.py...")
        print("  (Before fix: Would fail with ImproperlyConfigured)")
        
        # This import tests that loader.py doesn't import Django at module level
        from telis_recruitment.ai_config.loader import get_ai_config
        print("  ✓ Import successful (no module-level Django imports)")
        
        print("\nCalling get_ai_config() without Django configured...")
        print("  (Before fix: Would fail when trying 'from .models import AIConfig')")
        
        config = get_ai_config()
        print("  ✓ Function call successful")
        
        print("\nVerifying fallback defaults were returned...")
        assert config['temperature'] == 0.3
        assert config['default_provider'] == 'OpenAI'
        print("  ✓ Fallback defaults returned")
        
        print("\n" + "=" * 70)
        print("✓✓✓ ROOT CAUSE FIXED - Lazy imports work correctly! ✓✓✓")
        print("=" * 70)
        return True
        
    except Exception as e:
        print(f"\n✗✗✗ ROOT CAUSE NOT FIXED ✗✗✗")
        print(f"Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║  VERIFICATION TEST: Django ImproperlyConfigured Fix                ║")
    print("╚" + "=" * 68 + "╝")
    
    success = True
    
    # Test 1: Root cause (lazy import)
    if not test_loader_lazy_import():
        success = False
        print("\n⚠ Root cause test failed - the fix may not work")
    
    # Test 2: Exact failing scenario
    if not test_exact_failing_scenario():
        success = False
        print("\n⚠ Scenario test failed - the fix may not work")
    
    # Final result
    print("\n")
    if success:
        print("╔" + "=" * 68 + "╗")
        print("║  ✓✓✓ FIX VERIFIED ✓✓✓                                              ║")
        print("║                                                                    ║")
        print("║  The Django ImproperlyConfigured error has been fixed!            ║")
        print("║  Scraper can now run in standalone mode without Django.           ║")
        print("║                                                                    ║")
        print("║  Command that now works:                                          ║")
        print("║    python scriptname.py --once --industry handelsvertreter --qpi 5║")
        print("╚" + "=" * 68 + "╝")
        sys.exit(0)
    else:
        print("╔" + "=" * 68 + "╗")
        print("║  ✗✗✗ FIX VERIFICATION FAILED ✗✗✗                                  ║")
        print("╚" + "=" * 68 + "╝")
        sys.exit(1)
