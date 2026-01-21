"""
Exponential backoff with jitter for retry logic.

Provides robust retry mechanisms with configurable exponential backoff
and jitter to avoid thundering herd problems.
"""

import asyncio
import random
from typing import Callable, TypeVar, Awaitable, Tuple, Optional

T = TypeVar('T')


def log(level: str, msg: str, **ctx):
    """Simple logging function."""
    import json
    from datetime import datetime
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ctx_str = (" " + json.dumps(ctx, ensure_ascii=False)) if ctx else ""
    print(f"[{ts}] [{level.upper():7}] {msg}{ctx_str}", flush=True)


async def retry_with_backoff(
    func: Callable[..., Awaitable[T]],
    *args,
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    retryable_exceptions: Tuple = (Exception,),
    **kwargs
) -> T:
    """
    Retry an async function with exponential backoff and optional jitter.
    
    Features:
    - Exponential backoff: delay = base_delay * (exponential_base ^ attempt)
    - Jitter: ±25% random variation to avoid thundering herd
    - Configurable retryable exceptions
    - Detailed logging of retry attempts
    
    Args:
        func: Async function to retry
        *args: Positional arguments for func
        max_retries: Maximum number of retry attempts (default: 3)
        base_delay: Base delay in seconds (default: 1.0)
        max_delay: Maximum delay in seconds (default: 60.0)
        exponential_base: Base for exponential calculation (default: 2.0)
        jitter: Whether to add random jitter to delay (default: True)
        retryable_exceptions: Tuple of exceptions that trigger retry (default: all)
        **kwargs: Keyword arguments for func
        
    Returns:
        Result from successful function call
        
    Raises:
        Last exception if all retries fail
        
    Example:
        >>> result = await retry_with_backoff(
        ...     fetch_data,
        ...     url="https://example.com",
        ...     max_retries=3,
        ...     base_delay=1.0,
        ...     retryable_exceptions=(TimeoutError, ConnectionError)
        ... )
    """
    last_exception: Optional[Exception] = None
    
    for attempt in range(max_retries + 1):
        try:
            result = await func(*args, **kwargs)
            
            # Log successful retry if this wasn't the first attempt
            if attempt > 0:
                log("info", f"Retry successful after {attempt} attempt(s)")
            
            return result
            
        except retryable_exceptions as e:
            last_exception = e
            
            # If this was the last attempt, raise the exception
            if attempt >= max_retries:
                log(
                    "error",
                    f"All {max_retries + 1} attempts failed",
                    exception=str(e),
                    exception_type=type(e).__name__
                )
                raise
            
            # Calculate delay with exponential backoff
            delay = min(base_delay * (exponential_base ** attempt), max_delay)
            
            # Add jitter (±25% variation)
            if jitter:
                jitter_factor = random.uniform(0.75, 1.25)
                delay *= jitter_factor
            
            log(
                "warn",
                f"Attempt {attempt + 1}/{max_retries + 1} failed, retrying in {delay:.2f}s",
                exception=str(e),
                exception_type=type(e).__name__,
                delay_seconds=delay
            )
            
            # Wait before retrying
            await asyncio.sleep(delay)
    
    # This should never be reached, but just in case
    if last_exception:
        raise last_exception
    raise RuntimeError("Retry logic failed without exception")


def calculate_backoff_delay(
    attempt: int,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True
) -> float:
    """
    Calculate backoff delay for a given attempt number.
    
    Useful for preview or when you need the delay value without retrying.
    
    Args:
        attempt: Current attempt number (0-indexed)
        base_delay: Base delay in seconds (default: 1.0)
        max_delay: Maximum delay in seconds (default: 60.0)
        exponential_base: Base for exponential calculation (default: 2.0)
        jitter: Whether to add random jitter to delay (default: True)
        
    Returns:
        Calculated delay in seconds
        
    Example:
        >>> delay = calculate_backoff_delay(attempt=2, base_delay=1.0)
        >>> # Returns ~4.0 seconds (1.0 * 2^2) with jitter
    """
    # Calculate base exponential delay
    delay = min(base_delay * (exponential_base ** attempt), max_delay)
    
    # Add jitter (±25% variation)
    if jitter:
        jitter_factor = random.uniform(0.75, 1.25)
        delay *= jitter_factor
    
    return delay


class RetryExhausted(Exception):
    """Raised when all retry attempts have been exhausted."""
    
    def __init__(self, attempts: int, last_exception: Optional[Exception] = None):
        self.attempts = attempts
        self.last_exception = last_exception
        super().__init__(
            f"Retry exhausted after {attempts} attempts. "
            f"Last exception: {last_exception}"
        )
