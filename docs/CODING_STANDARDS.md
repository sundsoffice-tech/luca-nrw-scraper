# Coding Standards

These guidelines keep logging, error handling, and crawler naming consistent across the scraper + CRM stack.

## Logging conventions
- Always instantiate a module-level logger via `logging.getLogger(__name__)` (`luca_scraper/config.py:80`, `telis_recruitment/scraper_control/views.py:22`, `telis_recruitment/scraper_control/process_manager.py:21`). This keeps log statements attributable to their source module.
- Prefer structured messages with contextual keywords (URL, status, portal) and the appropriate level: `debug` for churny data (e.g., config load results in `luca_scraper/config.py:197`), `info` for state changes, `warning` for recoverable misconfigurations, and `error` when responding with a 500 or when a process aborts (see `telis_recruitment/scraper_control/views.py:103`, `telis_recruitment/scraper_control/views.py:138`, `telis_recruitment/scraper_control/views.py:176`).
- For the low-level HTTP/crawler loops that run outside the Django stack, reuse helper loggers (e.g., `luca_scraper/http/retry.py:31`) so that timestamps and JSON context stay consistent inside the CLI output stream.

## Error-handling rules
- Wrap Django-facing API handlers in `try/except` blocks that log the exception (`exc_info=True`) and surface a controlled JSON error response (`telis_recruitment/scraper_control/views.py:103`, `telis_recruitment/scraper_control/views.py:138`, `telis_recruitment/scraper_control/views.py:176`).
- When a failure touches the scraper subprocess, route it through the `ProcessManager` circuit breaker, retry counters, and log buffers defined before `ProcessManager.start` (`telis_recruitment/scraper_control/process_manager.py:31`, `telis_recruitment/scraper_control/process_manager.py:533`). Captured exceptions should increment the appropriate counters in that class instead of bubbling uncaught to the scheduler.
- Use the shared transaction context manager so that database writes either commit or rollback cleanly (`luca_scraper/database.py:84`). The manager already logs rollbacks and propagates the exception after rolling back, preserving both logging and correctness.
- Always sanitize third-party input earlier (see `_sanitize_scraper_params` in `telis_recruitment/scraper_control/views.py:138`) before passing it into the subprocess launcher. Invalid arguments should raise `ValueError` so that the view can respond with a 400 instead of crashing.

## Naming schema for new crawlers
- Each portal lives in its own module under `luca_scraper/crawlers/`. Match the naming pattern from the existing exports (`crawl_<portal>_listings_async`, `extract_<portal>_detail_async`, `crawl_<portal>_portal_async`) and register the functions alongside the other portals in `luca_scraper/crawlers/__init__.py:1`, `luca_scraper/crawlers/__init__.py:31`.
- Document the module with a short summary of the portal it targets and the kind of listings it covers so the initializer can stay understandable.
- If you need a reusable interface instead of plain functions, extend `BaseCrawler` (`luca_scraper/crawlers/base.py:13`) and expose the instance methods via the module-level helpers.
- Refer to `get_portal_config` when pulling URLs, rate limits, or `is_active` flags so that run-time configuration stays centralized (`luca_scraper/config.py:691`); if the portal should be configurable from the CRM, ensure it appears in `telis_recruitment/scraper_control/models.py:8` so admins can toggle it via the Django UI.
