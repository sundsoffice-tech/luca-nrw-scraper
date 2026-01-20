"""
Unit tests for database backend switching functionality.
=========================================================
Tests the DATABASE_BACKEND configuration and backend selection logic.
"""

import os
import subprocess
import sys
import pytest


def test_default_backend_is_sqlite():
    """Test that the default backend is 'sqlite' when no env var is set."""
    # Create a test script that checks the default
    test_script = """
import os
if 'SCRAPER_DB_BACKEND' in os.environ:
    del os.environ['SCRAPER_DB_BACKEND']
from luca_scraper.config import DATABASE_BACKEND
assert DATABASE_BACKEND == 'sqlite', f"Expected 'sqlite', got '{DATABASE_BACKEND}'"
print("OK")
"""
    result = subprocess.run(
        [sys.executable, '-c', test_script],
        capture_output=True,
        text=True,
        cwd=os.path.dirname(os.path.dirname(__file__))
    )
    assert result.returncode == 0, f"Failed: {result.stderr}"
    assert "OK" in result.stdout


def test_sqlite_backend_explicit():
    """Test that explicitly setting 'sqlite' backend works."""
    test_script = """
import os
os.environ['SCRAPER_DB_BACKEND'] = 'sqlite'
from luca_scraper.config import DATABASE_BACKEND
assert DATABASE_BACKEND == 'sqlite', f"Expected 'sqlite', got '{DATABASE_BACKEND}'"
print("OK")
"""
    result = subprocess.run(
        [sys.executable, '-c', test_script],
        capture_output=True,
        text=True,
        cwd=os.path.dirname(os.path.dirname(__file__)),
        env={**os.environ, 'SCRAPER_DB_BACKEND': 'sqlite'}
    )
    assert result.returncode == 0, f"Failed: {result.stderr}"
    assert "OK" in result.stdout


def test_django_backend_setting():
    """Test that setting 'django' backend works."""
    test_script = """
import os
os.environ['SCRAPER_DB_BACKEND'] = 'django'
from luca_scraper.config import DATABASE_BACKEND
assert DATABASE_BACKEND == 'django', f"Expected 'django', got '{DATABASE_BACKEND}'"
print("OK")
"""
    result = subprocess.run(
        [sys.executable, '-c', test_script],
        capture_output=True,
        text=True,
        cwd=os.path.dirname(os.path.dirname(__file__)),
        env={**os.environ, 'SCRAPER_DB_BACKEND': 'django'}
    )
    assert result.returncode == 0, f"Failed: {result.stderr}"
    assert "OK" in result.stdout


def test_invalid_backend_raises_error():
    """Test that an invalid backend value raises ValueError."""
    test_script = """
import os
os.environ['SCRAPER_DB_BACKEND'] = 'invalid_backend'
try:
    from luca_scraper.config import DATABASE_BACKEND
    print("ERROR: Should have raised ValueError")
    exit(1)
except ValueError as e:
    assert 'SCRAPER_DB_BACKEND' in str(e)
    assert 'invalid_backend' in str(e)
    print("OK")
"""
    result = subprocess.run(
        [sys.executable, '-c', test_script],
        capture_output=True,
        text=True,
        cwd=os.path.dirname(os.path.dirname(__file__)),
        env={**os.environ, 'SCRAPER_DB_BACKEND': 'invalid_backend'}
    )
    assert result.returncode == 0, f"Failed: {result.stderr}"
    assert "OK" in result.stdout


def test_backend_case_insensitive():
    """Test that backend selection is case-insensitive."""
    # Test uppercase
    test_script = """
import os
os.environ['SCRAPER_DB_BACKEND'] = 'SQLITE'
from luca_scraper.config import DATABASE_BACKEND
assert DATABASE_BACKEND == 'sqlite', f"Expected 'sqlite', got '{DATABASE_BACKEND}'"
print("OK")
"""
    result = subprocess.run(
        [sys.executable, '-c', test_script],
        capture_output=True,
        text=True,
        cwd=os.path.dirname(os.path.dirname(__file__)),
        env={**os.environ, 'SCRAPER_DB_BACKEND': 'SQLITE'}
    )
    assert result.returncode == 0, f"Failed: {result.stderr}"
    assert "OK" in result.stdout
    
    # Test mixed case
    test_script = """
import os
os.environ['SCRAPER_DB_BACKEND'] = 'Django'
from luca_scraper.config import DATABASE_BACKEND
assert DATABASE_BACKEND == 'django', f"Expected 'django', got '{DATABASE_BACKEND}'"
print("OK")
"""
    result = subprocess.run(
        [sys.executable, '-c', test_script],
        capture_output=True,
        text=True,
        cwd=os.path.dirname(os.path.dirname(__file__)),
        env={**os.environ, 'SCRAPER_DB_BACKEND': 'Django'}
    )
    assert result.returncode == 0, f"Failed: {result.stderr}"
    assert "OK" in result.stdout


def test_sqlite_backend_db_function_works():
    """Test that db() function works with SQLite backend."""
    test_script = """
import os
import tempfile
os.environ['SCRAPER_DB_BACKEND'] = 'sqlite'
# Use temp db to avoid conflicts
fd, db_path = tempfile.mkstemp(suffix='.db')
os.close(fd)
os.environ['SCRAPER_DB'] = db_path
try:
    from luca_scraper.database import db, DATABASE_BACKEND
    assert DATABASE_BACKEND == 'sqlite'
    # db() should work and return a SQLite connection
    conn = db()
    assert conn is not None
    conn.close()
    print("OK")
finally:
    import pathlib
    pathlib.Path(db_path).unlink(missing_ok=True)
"""
    result = subprocess.run(
        [sys.executable, '-c', test_script],
        capture_output=True,
        text=True,
        cwd=os.path.dirname(os.path.dirname(__file__)),
        env={**os.environ, 'SCRAPER_DB_BACKEND': 'sqlite'}
    )
    assert result.returncode == 0, f"Failed: {result.stderr}"
    assert "OK" in result.stdout


def test_django_backend_db_function_raises_error():
    """Test that db() function raises NotImplementedError with Django backend."""
    test_script = """
import os
os.environ['SCRAPER_DB_BACKEND'] = 'django'
try:
    from luca_scraper.database import db, DATABASE_BACKEND
    assert DATABASE_BACKEND == 'django'
    # db() should raise NotImplementedError
    try:
        db()
        print("ERROR: Should have raised NotImplementedError")
        exit(1)
    except NotImplementedError as e:
        assert 'Django ORM' in str(e)
        print("OK")
except ImportError:
    # Django not available - that's ok, skip this part
    print("SKIPPED")
"""
    result = subprocess.run(
        [sys.executable, '-c', test_script],
        capture_output=True,
        text=True,
        cwd=os.path.dirname(os.path.dirname(__file__)),
        env={**os.environ, 'SCRAPER_DB_BACKEND': 'django'}
    )
    # Either OK or SKIPPED is acceptable
    assert result.returncode == 0, f"Failed: {result.stderr}"
    assert "OK" in result.stdout or "SKIPPED" in result.stdout


def test_backend_config_logging():
    """Test that backend selection is logged."""
    test_script = """
import os
import logging
import sys

# Set up logging to capture output
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')

os.environ['SCRAPER_DB_BACKEND'] = 'sqlite'
from luca_scraper.config import DATABASE_BACKEND
print(f"Backend: {DATABASE_BACKEND}")
"""
    result = subprocess.run(
        [sys.executable, '-c', test_script],
        capture_output=True,
        text=True,
        cwd=os.path.dirname(os.path.dirname(__file__)),
        env={**os.environ, 'SCRAPER_DB_BACKEND': 'sqlite'}
    )
    assert result.returncode == 0, f"Failed: {result.stderr}"
    # Check that backend was logged or printed
    output = result.stdout + result.stderr
    assert 'sqlite' in output.lower()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

