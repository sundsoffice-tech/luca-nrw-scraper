# -*- coding: utf-8 -*-
"""
Test for UnboundLocalError fix in ActiveLearningEngine usage.

This test validates that the global declaration of ActiveLearningEngine
prevents UnboundLocalError when the variable is accessed before any 
local assignment in the run_scrape_once_async function.
"""

import pytest
import sys
import os

# Add the parent directory to the path to import scriptname
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_activelearningengine_import():
    """Test that ActiveLearningEngine can be imported from scriptname module."""
    # This test ensures that the import at module level works
    from scriptname import ActiveLearningEngine
    
    # ActiveLearningEngine should either be a class or None (if import failed)
    assert ActiveLearningEngine is None or callable(ActiveLearningEngine)


def test_activelearningengine_global_declaration():
    """Test that ActiveLearningEngine is properly declared as global in run_scrape_once_async."""
    import inspect
    from scriptname import run_scrape_once_async
    
    # Get the source code of the function
    source = inspect.getsource(run_scrape_once_async)
    
    # Check that the function contains a global declaration for ActiveLearningEngine
    # This prevents UnboundLocalError when the variable is accessed before assignment
    assert 'global' in source and 'ActiveLearningEngine' in source, \
        "ActiveLearningEngine should be declared as global in run_scrape_once_async"
    
    # Verify the global declaration appears early in the function (before usage)
    lines = source.split('\n')
    global_line = None
    usage_line = None
    
    for i, line in enumerate(lines):
        if 'global' in line and 'ActiveLearningEngine' in line:
            global_line = i
        if global_line is None and 'ActiveLearningEngine is not None' in line:
            usage_line = i
    
    assert global_line is not None, "Global declaration for ActiveLearningEngine not found"
    if usage_line is not None:
        assert global_line < usage_line, \
            "Global declaration should appear before first usage of ActiveLearningEngine"


def test_no_local_import_in_function():
    """Test that there's no local import of ActiveLearningEngine that would cause UnboundLocalError."""
    import inspect
    from scriptname import run_scrape_once_async
    
    # Get the source code of the function
    source = inspect.getsource(run_scrape_once_async)
    lines = source.split('\n')
    
    # Check for problematic patterns
    global_declared = False
    for i, line in enumerate(lines):
        # Check if global is declared
        if 'global' in line and 'ActiveLearningEngine' in line:
            global_declared = True
        
        # Check for local import without proper handling
        if 'from ai_learning_engine import ActiveLearningEngine' in line:
            # This is only OK if it's after global declaration and properly conditional
            assert global_declared, \
                f"Line {i}: Local import of ActiveLearningEngine found without global declaration"


def test_activelearningengine_none_check():
    """Test that ActiveLearningEngine usage is protected with None checks."""
    import inspect
    from scriptname import run_scrape_once_async
    
    # Get the source code of the function
    source = inspect.getsource(run_scrape_once_async)
    
    # When ActiveLearningEngine is used, it should be checked for None
    # This pattern ensures robustness when the import fails
    if 'ActiveLearningEngine(' in source:
        # Should have a None check before instantiation
        assert 'ActiveLearningEngine is not None' in source, \
            "ActiveLearningEngine should be checked for None before use"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
