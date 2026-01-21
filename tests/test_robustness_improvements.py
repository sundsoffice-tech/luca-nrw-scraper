"""
Tests for robustness improvements: backoff, validators, graceful_shutdown, memory_guard.
"""

import asyncio
import pytest
import time
from unittest.mock import Mock, patch, MagicMock

# Import modules to test
from luca_scraper.http.backoff import (
    retry_with_backoff,
    calculate_backoff_delay,
    RetryExhausted,
)
from luca_scraper.validators import (
    URLValidator,
    DataValidator,
    ValidationError,
)
from luca_scraper.graceful_shutdown import GracefulShutdown, get_shutdown_handler
from luca_scraper.memory_guard import MemoryGuard, get_memory_guard


class TestBackoff:
    """Tests for exponential backoff with jitter."""
    
    @pytest.mark.asyncio
    async def test_retry_with_backoff_success_first_attempt(self):
        """Test that successful first attempt doesn't retry."""
        async def func():
            return "success"
        
        result = await retry_with_backoff(
            func,
            max_retries=3,
            base_delay=0.1
        )
        
        assert result == "success"
    
    @pytest.mark.asyncio
    async def test_retry_with_backoff_eventual_success(self):
        """Test that function succeeds after retries."""
        attempt_count = 0
        
        async def func():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 3:
                raise TimeoutError("Timeout")
            return "success"
        
        result = await retry_with_backoff(
            func,
            max_retries=3,
            base_delay=0.1,
            retryable_exceptions=(TimeoutError,)
        )
        
        assert result == "success"
        assert attempt_count == 3
    
    @pytest.mark.asyncio
    async def test_retry_with_backoff_exhausted(self):
        """Test that all retries fail and exception is raised."""
        async def func():
            raise TimeoutError("Always fails")
        
        with pytest.raises(TimeoutError):
            await retry_with_backoff(
                func,
                max_retries=2,
                base_delay=0.1,
                retryable_exceptions=(TimeoutError,)
            )
    
    @pytest.mark.asyncio
    async def test_retry_with_backoff_non_retryable_exception(self):
        """Test that non-retryable exceptions are not retried."""
        attempt_count = 0
        
        async def func():
            nonlocal attempt_count
            attempt_count += 1
            raise ValueError("Non-retryable")
        
        with pytest.raises(ValueError):
            await retry_with_backoff(
                func,
                max_retries=3,
                base_delay=0.1,
                retryable_exceptions=(TimeoutError,)
            )
        
        assert attempt_count == 1  # Should fail immediately
    
    def test_calculate_backoff_delay(self):
        """Test backoff delay calculation."""
        # Test exponential increase
        delay0 = calculate_backoff_delay(0, base_delay=1.0, jitter=False)
        delay1 = calculate_backoff_delay(1, base_delay=1.0, jitter=False)
        delay2 = calculate_backoff_delay(2, base_delay=1.0, jitter=False)
        
        assert delay0 == 1.0
        assert delay1 == 2.0
        assert delay2 == 4.0
    
    def test_calculate_backoff_delay_with_max(self):
        """Test max delay cap."""
        delay = calculate_backoff_delay(10, base_delay=1.0, max_delay=10.0, jitter=False)
        assert delay == 10.0


class TestURLValidator:
    """Tests for URL validation."""
    
    def test_validate_valid_url(self):
        """Test valid URL passes validation."""
        assert URLValidator.validate("https://example.com")
        assert URLValidator.validate("http://example.com/path")
    
    def test_validate_invalid_scheme(self):
        """Test invalid scheme raises error."""
        # Javascript: is caught by dangerous pattern first
        with pytest.raises(ValidationError, match="dangerous pattern"):
            URLValidator.validate("javascript:alert(1)")
        
        with pytest.raises(ValidationError, match="scheme.*not allowed"):
            URLValidator.validate("ftp://example.com")
    
    def test_validate_dangerous_patterns(self):
        """Test dangerous patterns are rejected."""
        with pytest.raises(ValidationError, match="dangerous pattern"):
            URLValidator.validate("javascript:alert(1)")
    
    def test_validate_url_too_long(self):
        """Test URL length limit."""
        long_url = "https://example.com/" + "a" * 3000
        with pytest.raises(ValidationError, match="exceeds maximum length"):
            URLValidator.validate(long_url)
    
    def test_sanitize_url(self):
        """Test URL sanitization removes fragments."""
        url = "https://example.com/path?query=1#fragment"
        sanitized = URLValidator.sanitize(url)
        assert "#" not in sanitized
        assert "query=1" in sanitized
    
    def test_is_safe(self):
        """Test is_safe method doesn't raise exceptions."""
        assert URLValidator.is_safe("https://example.com")
        assert not URLValidator.is_safe("javascript:alert(1)")
        assert not URLValidator.is_safe("")


class TestDataValidator:
    """Tests for data validation."""
    
    def test_validate_email_valid(self):
        """Test valid email passes validation."""
        assert DataValidator.validate_email("test@example.com")
        assert DataValidator.validate_email("user.name+tag@example.co.uk")
    
    def test_validate_email_invalid(self):
        """Test invalid email raises error."""
        with pytest.raises(ValidationError):
            DataValidator.validate_email("invalid")
        
        with pytest.raises(ValidationError):
            DataValidator.validate_email("@example.com")
    
    def test_validate_phone_valid(self):
        """Test valid phone passes validation."""
        assert DataValidator.validate_phone("+49 123 4567890")
        assert DataValidator.validate_phone("01234567890")
    
    def test_validate_phone_invalid(self):
        """Test invalid phone raises error."""
        with pytest.raises(ValidationError):
            DataValidator.validate_phone("abc")
        
        with pytest.raises(ValidationError):
            DataValidator.validate_phone("123")  # Too short
    
    def test_validate_lead_with_email(self):
        """Test lead with email is valid."""
        assert DataValidator.validate_lead({"email": "test@example.com"})
    
    def test_validate_lead_with_phone(self):
        """Test lead with phone is valid."""
        assert DataValidator.validate_lead({"phone": "+49 123 4567890"})
    
    def test_validate_lead_without_contact(self):
        """Test lead without contact info is invalid."""
        with pytest.raises(ValidationError, match="at least one contact method"):
            DataValidator.validate_lead({"name": "John Doe"})
    
    def test_sanitize_email(self):
        """Test email sanitization."""
        assert DataValidator.sanitize_email("  TEST@EXAMPLE.COM  ") == "test@example.com"
    
    def test_sanitize_phone(self):
        """Test phone sanitization."""
        assert DataValidator.sanitize_phone("+49 (123) 456-7890") == "+491234567890"


class TestGracefulShutdown:
    """Tests for graceful shutdown handler."""
    
    def test_singleton_pattern(self):
        """Test that GracefulShutdown is a singleton."""
        instance1 = get_shutdown_handler()
        instance2 = get_shutdown_handler()
        assert instance1 is instance2
    
    def test_track_and_untrack_task(self):
        """Test task tracking."""
        shutdown = get_shutdown_handler()
        
        initial_count = shutdown.get_active_tasks_count()
        
        shutdown.track_task("task1")
        assert shutdown.get_active_tasks_count() == initial_count + 1
        
        shutdown.untrack_task("task1")
        assert shutdown.get_active_tasks_count() == initial_count
    
    def test_register_cleanup(self):
        """Test cleanup callback registration."""
        shutdown = get_shutdown_handler()
        
        callback_called = False
        
        def cleanup_callback():
            nonlocal callback_called
            callback_called = True
        
        shutdown.register_cleanup(cleanup_callback)
        
        # Execute cleanup manually (don't trigger full shutdown in tests)
        shutdown._execute_cleanups()
        
        assert callback_called
    
    def test_is_shutdown_requested(self):
        """Test shutdown request flag."""
        shutdown = get_shutdown_handler()
        
        # Initially not requested
        initial_state = shutdown.is_shutdown_requested()
        
        # Note: We don't actually trigger shutdown in tests
        assert isinstance(initial_state, bool)


class TestMemoryGuard:
    """Tests for memory guard."""
    
    def test_get_memory_usage(self):
        """Test memory usage statistics."""
        guard = MemoryGuard()
        stats = guard.get_memory_usage()
        
        assert 'rss_mb' in stats
        assert 'vms_mb' in stats
        assert 'percent' in stats
        assert 'available_mb' in stats
        assert 'total_mb' in stats
        
        assert stats['rss_mb'] > 0
        assert 0 <= stats['percent'] <= 100
    
    def test_check_and_collect(self):
        """Test memory check and garbage collection."""
        guard = MemoryGuard(memory_threshold_percent=99.0)  # High threshold
        
        # Should not trigger GC with normal memory usage
        result = guard.check_and_collect()
        assert isinstance(result, bool)
    
    def test_is_memory_critical(self):
        """Test critical memory check."""
        guard = MemoryGuard(critical_threshold_percent=99.0)  # High threshold
        
        # Should not be critical with normal memory usage
        assert not guard.is_memory_critical()
    
    def test_singleton_pattern(self):
        """Test that get_memory_guard returns same instance."""
        guard1 = get_memory_guard()
        guard2 = get_memory_guard()
        assert guard1 is guard2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
