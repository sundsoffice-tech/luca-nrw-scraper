# Architecture Overview

This document maps the core modules that comprise the LUCA NRW pipeline and how data flows from the scraper to the CRM UI.

## Module Map

### Scraper orchestrator
- The CLI glue code, argument parsing, and configuration checks live in `luca_scraper/cli.py:1`, exposing switches such as `--industry`, `--mode`, `--qpi`, `--force`, and the `--ui` entry point.
- Search query generation, including default, niche, and industry-specific query banks, is centralized in `luca_scraper/search/manager.py:1`.
- Portal-specific crawlers are exposed via the `luca_scraper/crawlers` package, which consistently exports `crawl_<portal>_listings_async`, `extract_<portal>_detail_async`, and (when needed) `crawl_<portal>_portal_async` helpers (`luca_scraper/crawlers/__init__.py:1`).

### Parser
- Contact extraction heuristics, validation, and domain-aware filtering are gathered in `luca_scraper/parser/contacts.py:1`.
- Context analysis that distinguishes candidates, business inquiries, and job ads lives in `luca_scraper/parser/context.py:1`.
- Name heuristics and deduplication helpers are exported from `luca_scraper/parser/names.py:1`, completing the parser layer.

### Scoring
- Dynamic scoring constants and utility helpers control base scores, portal reputations, and phone source boosts for all leads (`luca_scraper/scoring/dynamic_scoring.py:1`).
- Quality assessment, deduplication, and signal extraction (phone, email, WhatsApp, job hints) are handled by `luca_scraper/scoring/quality.py:1`.
- Validation and classification rules — including job-ad blocking and candidate-focused signals — are implemented in `luca_scraper/scoring/validation.py:1`.
- Telefonbuch enrichment, phone normalization, and caching live in `luca_scraper/scoring/enrichment.py:1` to raise data quality before persistence.

### Database
- A thread-safe SQLite connection manager plus transaction helper ensure the schema is initialized and accessible (`luca_scraper/database.py:28` and `luca_scraper/database.py:100`).
- Tables include `leads`, `runs`, `queries_done`, `urls_seen`, and the shared `telefonbuch_cache`; schema maintenance (ALTER TABLE, indexes) happens in `_ensure_schema`.

### CRM UI
- Django’s `scraper_control` app exposes the admin dashboard, SSE log stream, and API endpoints at `/crm/scraper/` (`telis_recruitment/scraper_control/views.py:77`, `telis_recruitment/scraper_control/views.py:103`, `telis_recruitment/scraper_control/views.py:138`, `telis_recruitment/scraper_control/views.py:176`, `telis_recruitment/scraper_control/views.py:204`).
- The singleton `ProcessManager` handles scraper lifecycle, retry/circuit-breaker logic, and ties back to `ScraperConfig`, `ScraperRun`, and `ScraperLog` models (`telis_recruitment/scraper_control/process_manager.py:31`, `telis_recruitment/scraper_control/process_manager.py:533`, `telis_recruitment/scraper_control/process_manager.py:905`, `telis_recruitment/scraper_control/models.py:8`, `telis_recruitment/scraper_control/models.py:311`, `telis_recruitment/scraper_control/models.py:461`).
- The CRM lead model mirrors scraper fields (phone, email, score, status, AI summary, etc.) and drives the UI pages and reports (`telis_recruitment/leads/models.py:5`). `SyncStatus` tracks the last imported lead ID (`telis_recruitment/leads/models.py:298`).
- Import helpers (`telis_recruitment/leads/management/commands/import_scraper_db.py:31`) and the watch wrapper (`telis_recruitment/leads/management/commands/sync_scraper_db.py:33`) incrementally load `scraper.db` rows into the Django database so the CRM UI always reflects the latest scraped contacts.

## Data Flow
1. **Query construction → portal crawl:** The CLI (`luca_scraper/cli.py:1`) triggers `search.manager` (`luca_scraper/search/manager.py:1`), then invokes the portal crawl helpers exported in `luca_scraper/crawlers/__init__.py:1`.
2. **Parsing:** Raw HTML is fed into the parser layer (`contacts`, `context`, `names`) to produce structured lead dictionaries (`luca_scraper/parser/contacts.py:1`, `luca_scraper/parser/context.py:1`, `luca_scraper/parser/names.py:1`).
3. **Scoring & enrichment:** Parsed leads flow through scoring constants, quality filters, validation rules, and optional telefonbuch enrichment before being marked with `score`, `confidence`, `lead_type`, and boolean gates (`luca_scraper/scoring/dynamic_scoring.py:1`, `luca_scraper/scoring/quality.py:1`, `luca_scraper/scoring/validation.py:1`, `luca_scraper/scoring/enrichment.py:1`).
4. **Persistence:** Leads are written to `scraper.db` via the shared SQLite helpers (`luca_scraper/database.py:28`, `luca_scraper/database.py:100`).
5. **CRM sync & surface:** The Django CRM imports fresh rows through `import_scraper_db` (`telis_recruitment/leads/management/commands/import_scraper_db.py:31`) and monitors the sync state (`telis_recruitment/leads/models.py:298`) so the `Lead` model (`telis_recruitment/leads/models.py:5`) can power dashboards and exports.
6. **Control surface:** Admins start/stop the scraper through `scraper_control.views` (`telis_recruitment/scraper_control/views.py:138`) which routes commands to `ProcessManager` (`telis_recruitment/scraper_control/process_manager.py:533`) and records logs (`telis_recruitment/scraper_control/models.py:461`).

## Interfaces
- **Configuration sync:** `luca_scraper/config.py` tries to load Django-managed settings via `telis_recruitment/scraper_control/config_loader.py:12` before falling back to environment variables and defaults (`luca_scraper/config.py:68`, `luca_scraper/config.py:141`, `luca_scraper/config.py:197`), keeping CRM-controlled modes, portals, and feature flags authoritative.
- **Process orchestration:** `scraper_control.views` sanitizes API requests and delegates to the single `ProcessManager` (`telis_recruitment/scraper_control/views.py:138`, `telis_recruitment/scraper_control/process_manager.py:533`, `telis_recruitment/scraper_control/process_manager.py:905`), so the Django UI never talks directly to the scraper threads.
- **Shared database file:** All scraper output lands in `scraper.db` (`luca_scraper/database.py:28`), and the CRM imports from the same file through `import_scraper_db` (`telis_recruitment/leads/management/commands/import_scraper_db.py:31`), optionally running `sync_scraper_db` (`telis_recruitment/leads/management/commands/sync_scraper_db.py:33`) on a schedule.
- **Observability:** `ScraperRun`, `ScraperConfig`, and `ScraperLog` (`telis_recruitment/scraper_control/models.py:311`, `telis_recruitment/scraper_control/models.py:8`, `telis_recruitment/scraper_control/models.py:461`) persist runtime metadata that the CRM dashboard surfaces via SSE and table views.
