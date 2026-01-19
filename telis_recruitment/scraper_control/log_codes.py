"""
Structured Log Event Codes for Scraper Monitoring.

This module provides standardized log event codes that can be used for:
- Grafana/Kibana visualization and alerting
- Structured log parsing and analysis
- Consistent error classification

Usage:
    from .log_codes import LogEvent, LogLevel
    
    # Create a structured log event
    event = LogEvent.CRAWL_START
    logger.info(f"{event.code}: {event.description}", extra={'event_code': event.code})
"""

from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional


class LogLevel(str, Enum):
    """Standard log levels for structured logging."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogCategory(str, Enum):
    """Categories for log events."""
    LIFECYCLE = "LIFECYCLE"    # Process start/stop events
    CRAWL = "CRAWL"            # Crawling operations
    EXTRACTION = "EXTRACTION"  # Data extraction events
    NETWORK = "NETWORK"        # Network/HTTP events
    DATABASE = "DATABASE"      # Database operations
    CIRCUIT_BREAKER = "CIRCUIT_BREAKER"  # Circuit breaker events
    VALIDATION = "VALIDATION"  # Data validation events
    SECURITY = "SECURITY"      # Security-related events
    PERFORMANCE = "PERFORMANCE"  # Performance metrics


@dataclass(frozen=True)
class LogEventDef:
    """Definition of a structured log event."""
    code: str
    description: str
    level: LogLevel
    category: LogCategory


class LogEvent(Enum):
    """
    Standardized log event codes for scraper monitoring.
    
    Format: CATEGORY_ACTION (e.g., CRAWL_START, EXTRACTION_FAIL)
    
    These codes can be used for:
    - Grafana dashboards and alerting
    - Kibana log analysis
    - Automated monitoring systems
    """
    
    # ==================== LIFECYCLE EVENTS ====================
    SCRAPER_START = LogEventDef(
        "SCRAPER_START",
        "Scraper process started",
        LogLevel.INFO,
        LogCategory.LIFECYCLE
    )
    SCRAPER_STOP = LogEventDef(
        "SCRAPER_STOP",
        "Scraper process stopped gracefully",
        LogLevel.INFO,
        LogCategory.LIFECYCLE
    )
    SCRAPER_KILL = LogEventDef(
        "SCRAPER_KILL",
        "Scraper process forcefully terminated",
        LogLevel.WARN,
        LogCategory.LIFECYCLE
    )
    SCRAPER_CRASH = LogEventDef(
        "SCRAPER_CRASH",
        "Scraper process crashed unexpectedly",
        LogLevel.ERROR,
        LogCategory.LIFECYCLE
    )
    SCRAPER_EARLY_EXIT = LogEventDef(
        "SCRAPER_EARLY_EXIT",
        "Scraper exited prematurely (likely startup error)",
        LogLevel.ERROR,
        LogCategory.LIFECYCLE
    )
    
    # ==================== CRAWL EVENTS ====================
    CRAWL_START = LogEventDef(
        "CRAWL_START",
        "Started crawling a portal/source",
        LogLevel.INFO,
        LogCategory.CRAWL
    )
    CRAWL_COMPLETE = LogEventDef(
        "CRAWL_COMPLETE",
        "Completed crawling a portal/source",
        LogLevel.INFO,
        LogCategory.CRAWL
    )
    CRAWL_SKIP = LogEventDef(
        "CRAWL_SKIP",
        "Skipped crawling (already done or disabled)",
        LogLevel.DEBUG,
        LogCategory.CRAWL
    )
    CRAWL_PARTIAL = LogEventDef(
        "CRAWL_PARTIAL",
        "Crawl completed with partial results",
        LogLevel.WARN,
        LogCategory.CRAWL
    )
    
    # ==================== EXTRACTION EVENTS ====================
    EXTRACTION_START = LogEventDef(
        "EXTRACTION_START",
        "Started data extraction from page",
        LogLevel.DEBUG,
        LogCategory.EXTRACTION
    )
    EXTRACTION_SUCCESS = LogEventDef(
        "EXTRACTION_SUCCESS",
        "Successfully extracted data",
        LogLevel.INFO,
        LogCategory.EXTRACTION
    )
    EXTRACTION_FAIL = LogEventDef(
        "EXTRACTION_FAIL",
        "Failed to extract data from page",
        LogLevel.ERROR,
        LogCategory.EXTRACTION
    )
    EXTRACTION_PARTIAL = LogEventDef(
        "EXTRACTION_PARTIAL",
        "Partial data extraction (some fields missing)",
        LogLevel.WARN,
        LogCategory.EXTRACTION
    )
    EXTRACTION_NO_DATA = LogEventDef(
        "EXTRACTION_NO_DATA",
        "No extractable data found on page",
        LogLevel.DEBUG,
        LogCategory.EXTRACTION
    )
    
    # ==================== NETWORK EVENTS ====================
    HTTP_REQUEST = LogEventDef(
        "HTTP_REQUEST",
        "HTTP request sent",
        LogLevel.DEBUG,
        LogCategory.NETWORK
    )
    HTTP_SUCCESS = LogEventDef(
        "HTTP_SUCCESS",
        "HTTP request successful",
        LogLevel.DEBUG,
        LogCategory.NETWORK
    )
    HTTP_ERROR = LogEventDef(
        "HTTP_ERROR",
        "HTTP request failed",
        LogLevel.ERROR,
        LogCategory.NETWORK
    )
    HTTP_TIMEOUT = LogEventDef(
        "HTTP_TIMEOUT",
        "HTTP request timed out",
        LogLevel.WARN,
        LogCategory.NETWORK
    )
    HTTP_BLOCK_403 = LogEventDef(
        "HTTP_BLOCK_403",
        "Request blocked (403 Forbidden)",
        LogLevel.WARN,
        LogCategory.NETWORK
    )
    HTTP_RATE_LIMIT = LogEventDef(
        "HTTP_RATE_LIMIT",
        "Rate limit hit (429 Too Many Requests)",
        LogLevel.WARN,
        LogCategory.NETWORK
    )
    HTTP_CAPTCHA = LogEventDef(
        "HTTP_CAPTCHA",
        "Captcha challenge detected",
        LogLevel.WARN,
        LogCategory.NETWORK
    )
    
    # ==================== DATABASE EVENTS ====================
    DB_CONNECT = LogEventDef(
        "DB_CONNECT",
        "Database connection established",
        LogLevel.DEBUG,
        LogCategory.DATABASE
    )
    DB_DISCONNECT = LogEventDef(
        "DB_DISCONNECT",
        "Database connection closed",
        LogLevel.DEBUG,
        LogCategory.DATABASE
    )
    DB_ERROR = LogEventDef(
        "DB_ERROR",
        "Database operation failed",
        LogLevel.ERROR,
        LogCategory.DATABASE
    )
    LEAD_SAVED = LogEventDef(
        "LEAD_SAVED",
        "Lead saved to database",
        LogLevel.INFO,
        LogCategory.DATABASE
    )
    LEAD_DUPLICATE = LogEventDef(
        "LEAD_DUPLICATE",
        "Duplicate lead skipped",
        LogLevel.DEBUG,
        LogCategory.DATABASE
    )
    
    # ==================== CIRCUIT BREAKER EVENTS ====================
    CB_TRIGGERED = LogEventDef(
        "CB_TRIGGERED",
        "Circuit breaker triggered for portal",
        LogLevel.WARN,
        LogCategory.CIRCUIT_BREAKER
    )
    CB_RESET = LogEventDef(
        "CB_RESET",
        "Circuit breaker reset",
        LogLevel.INFO,
        LogCategory.CIRCUIT_BREAKER
    )
    CB_HALF_OPEN = LogEventDef(
        "CB_HALF_OPEN",
        "Circuit breaker in half-open state (testing)",
        LogLevel.DEBUG,
        LogCategory.CIRCUIT_BREAKER
    )
    
    # ==================== VALIDATION EVENTS ====================
    VALIDATION_PASS = LogEventDef(
        "VALIDATION_PASS",
        "Data validation passed",
        LogLevel.DEBUG,
        LogCategory.VALIDATION
    )
    VALIDATION_FAIL = LogEventDef(
        "VALIDATION_FAIL",
        "Data validation failed",
        LogLevel.WARN,
        LogCategory.VALIDATION
    )
    SCORE_BELOW_THRESHOLD = LogEventDef(
        "SCORE_BELOW_THRESHOLD",
        "Lead score below minimum threshold",
        LogLevel.DEBUG,
        LogCategory.VALIDATION
    )
    
    # ==================== SECURITY EVENTS ====================
    SSL_WARNING = LogEventDef(
        "SSL_WARNING",
        "SSL certificate validation issue",
        LogLevel.WARN,
        LogCategory.SECURITY
    )
    AUTH_FAIL = LogEventDef(
        "AUTH_FAIL",
        "Authentication failed",
        LogLevel.ERROR,
        LogCategory.SECURITY
    )
    
    # ==================== PERFORMANCE EVENTS ====================
    PERF_SLOW_REQUEST = LogEventDef(
        "PERF_SLOW_REQUEST",
        "Request took longer than expected",
        LogLevel.WARN,
        LogCategory.PERFORMANCE
    )
    PERF_MEMORY_HIGH = LogEventDef(
        "PERF_MEMORY_HIGH",
        "Memory usage above threshold",
        LogLevel.WARN,
        LogCategory.PERFORMANCE
    )
    
    @property
    def code(self) -> str:
        """Get the event code string."""
        return self.value.code
    
    @property
    def description(self) -> str:
        """Get the event description."""
        return self.value.description
    
    @property
    def level(self) -> LogLevel:
        """Get the default log level."""
        return self.value.level
    
    @property
    def category(self) -> LogCategory:
        """Get the event category."""
        return self.value.category


def format_structured_log(
    event: LogEvent,
    message: str,
    portal: str = "",
    url: str = "",
    extra: Optional[dict] = None
) -> dict:
    """
    Format a structured log entry for monitoring systems.
    
    Args:
        event: The LogEvent enum value
        message: Additional context message
        portal: Portal/source name (optional)
        url: Related URL (optional)
        extra: Additional key-value pairs (optional)
        
    Returns:
        Dictionary suitable for structured logging/JSON output
        
    Example:
        >>> log_data = format_structured_log(
        ...     LogEvent.EXTRACTION_FAIL,
        ...     "Could not parse contact info",
        ...     portal="stepstone",
        ...     url="https://example.com/job/123"
        ... )
        >>> logger.error(log_data['message'], extra=log_data)
    """
    log_data = {
        "event_code": event.code,
        "event_category": event.category.value,
        "level": event.level.value,
        "message": f"[{event.code}] {message}",
        "description": event.description,
    }
    
    if portal:
        log_data["portal"] = portal
    if url:
        log_data["url"] = url
    if extra:
        log_data.update(extra)
    
    return log_data


# Export event codes as constants for easy import
SCRAPER_START = LogEvent.SCRAPER_START
SCRAPER_STOP = LogEvent.SCRAPER_STOP
SCRAPER_CRASH = LogEvent.SCRAPER_CRASH
SCRAPER_EARLY_EXIT = LogEvent.SCRAPER_EARLY_EXIT
CRAWL_START = LogEvent.CRAWL_START
CRAWL_COMPLETE = LogEvent.CRAWL_COMPLETE
EXTRACTION_SUCCESS = LogEvent.EXTRACTION_SUCCESS
EXTRACTION_FAIL = LogEvent.EXTRACTION_FAIL
HTTP_ERROR = LogEvent.HTTP_ERROR
HTTP_TIMEOUT = LogEvent.HTTP_TIMEOUT
HTTP_RATE_LIMIT = LogEvent.HTTP_RATE_LIMIT
CB_TRIGGERED = LogEvent.CB_TRIGGERED
CB_RESET = LogEvent.CB_RESET
LEAD_SAVED = LogEvent.LEAD_SAVED
VALIDATION_FAIL = LogEvent.VALIDATION_FAIL
