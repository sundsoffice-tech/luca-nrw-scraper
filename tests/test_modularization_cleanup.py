"""
Test Modularization and Cleanup
================================
Tests for the finalized modularization and code cleanup.
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_cli_validate_config_import():
    """Test that validate_config can be imported from luca_scraper.cli."""
    from luca_scraper.cli import validate_config
    assert callable(validate_config), "validate_config should be callable"


def test_cli_parse_args_import():
    """Test that parse_args can be imported from luca_scraper.cli."""
    from luca_scraper.cli import parse_args
    assert callable(parse_args), "parse_args should be callable"


def test_cli_imports_from_luca_scraper():
    """Test that CLI functions can be imported from luca_scraper package."""
    from luca_scraper import validate_config, parse_args, print_banner, print_help
    assert callable(validate_config), "validate_config should be accessible from luca_scraper"
    assert callable(parse_args), "parse_args should be accessible from luca_scraper"
    assert callable(print_banner), "print_banner should be accessible from luca_scraper"
    assert callable(print_help), "print_help should be accessible from luca_scraper"


def test_scriptname_uses_luca_scraper_cli():
    """Test that scriptname delegates to luca_scraper.cli when available."""
    from scriptname import validate_config, parse_args
    assert callable(validate_config), "validate_config should be callable from scriptname"
    assert callable(parse_args), "parse_args should be callable from scriptname"


def test_backward_compatibility_script_module():
    """Test that script.py provides backward compatibility."""
    from script import validate_config, parse_args
    assert callable(validate_config), "validate_config should be accessible from script"
    assert callable(parse_args), "parse_args should be accessible from script"


def test_validate_config_accepts_log_func():
    """Test that validate_config accepts an optional log function."""
    from luca_scraper.cli import validate_config
    
    # Should work without log_func
    try:
        validate_config()
        success_no_log = True
    except Exception as e:
        success_no_log = False
        print(f"Error without log_func: {e}")
    
    assert success_no_log, "validate_config should work without log_func"
    
    # Should work with log_func
    logged = []
    def mock_log(level, message, **kwargs):
        logged.append({'level': level, 'message': message, 'kwargs': kwargs})
    
    try:
        validate_config(log_func=mock_log)
        success_with_log = True
    except Exception as e:
        success_with_log = False
        print(f"Error with log_func: {e}")
    
    assert success_with_log, "validate_config should work with log_func"


def test_config_centralization():
    """Test that config is centralized in luca_scraper.config."""
    from luca_scraper.config import (
        OPENAI_API_KEY, GCS_KEYS, GCS_CXS, GCS_API_KEY, GCS_CX,
        DB_PATH, HTTP_TIMEOUT, MAX_FETCH_SIZE, USER_AGENT
    )
    
    # Should be able to import all config constants
    assert DB_PATH is not None, "DB_PATH should be defined"
    assert HTTP_TIMEOUT is not None, "HTTP_TIMEOUT should be defined"
    assert MAX_FETCH_SIZE is not None, "MAX_FETCH_SIZE should be defined"
    assert USER_AGENT is not None, "USER_AGENT should be defined"
    
    # Check that scriptname uses the same config
    import scriptname
    if scriptname._LUCA_SCRAPER_AVAILABLE:
        assert scriptname.OPENAI_API_KEY == OPENAI_API_KEY, "scriptname should use luca_scraper config"
        assert scriptname.DB_PATH == DB_PATH, "scriptname should use luca_scraper DB_PATH"


def test_no_placeholder_implementation():
    """Test that validate_config is fully implemented, not a placeholder."""
    from luca_scraper.cli import validate_config
    import inspect
    
    # Get source code
    source = inspect.getsource(validate_config)
    
    # Should not contain placeholder comments
    assert "Placeholder" not in source, "validate_config should not be a placeholder"
    
    # Should have actual validation logic
    assert "errs" in source, "validate_config should have error collection logic"
    assert "OPENAI_API_KEY" in source, "validate_config should validate OPENAI_API_KEY"
    assert "GCS_KEYS" in source or "GCS_CXS" in source, "validate_config should validate GCS config"
    
    # Check the module imports
    import luca_scraper.cli as cli_module
    module_source = inspect.getsource(cli_module)
    assert "from .config import" in module_source or "from luca_scraper.config import" in module_source, \
        "CLI module should import from centralized config"


def test_script_py_deprecation_notice():
    """Test that script.py has deprecation notice."""
    script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'script.py')
    with open(script_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    assert "DEPRECATION" in content or "backward compatibility" in content.lower(), \
        "script.py should have deprecation or backward compatibility notice"


if __name__ == "__main__":
    print("=" * 60)
    print("Testing Modularization and Cleanup")
    print("=" * 60)
    
    tests = [
        ("CLI validate_config import", test_cli_validate_config_import),
        ("CLI parse_args import", test_cli_parse_args_import),
        ("CLI imports from luca_scraper", test_cli_imports_from_luca_scraper),
        ("scriptname uses luca_scraper CLI", test_scriptname_uses_luca_scraper_cli),
        ("Backward compatibility (script.py)", test_backward_compatibility_script_module),
        ("validate_config accepts log_func", test_validate_config_accepts_log_func),
        ("Config centralization", test_config_centralization),
        ("No placeholder implementation", test_no_placeholder_implementation),
        ("script.py deprecation notice", test_script_py_deprecation_notice),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            test_func()
            print(f"✓ {name}")
            passed += 1
        except AssertionError as e:
            print(f"✗ {name}: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {name}: Unexpected error: {e}")
            failed += 1
    
    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    if failed > 0:
        sys.exit(1)
    else:
        print("\n✅ All tests passed!")
