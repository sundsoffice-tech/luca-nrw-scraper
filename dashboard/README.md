# LUCA Control Center - Dashboard

> **⚠️ DEPRECATED - This Flask dashboard is being replaced by the Django CRM system**
> 
> **New Location:** All scraper control, monitoring, and export features have been migrated to the Django CRM at `/crm/scraper/`
> 
> **Migration Date:** January 2026
> 
> **Why the change?**
> - Unified dashboard with integrated lead management
> - Better authentication and permission system
> - Consistent UI/UX with the rest of the CRM
> - Easier maintenance with single Django codebase
> 
> **For new features and scraper control, please use:**
> - Django CRM: `http://localhost:8000/crm/scraper/` (requires login)
> - Full documentation in `/telis_recruitment/README.md`
> 
> This Flask dashboard will be kept for reference but is no longer actively maintained.

---

Professional web-based dashboard for the LUCA NRW Scraper, providing real-time monitoring, KPI tracking, API cost management, and configuration options.

## Features

### 📊 KPI Dashboard (Main Page)
- **Leads gesamt**: Total cumulative lead count
- **API-Kosten heute**: OpenAI token consumption in EUR for today
- **Erfolgsrate**: Percentage of leads with mobile phone numbers
- **Leads heute**: New leads from the last 24 hours
- **Budget tracking**: Visual progress bar for monthly API budget
- **Live charts**: Lead history over 7/30 days and top performing sources

### 💰 Analytics Page
- **API Cost History**: Line chart showing costs over time by provider
- **Cost Breakdown**: Detailed breakdowns by provider and endpoint
- **Export Options**: Download leads as CSV

### ⚙️ Settings Page
- **Budget Management**: Set monthly API cost limits
- **Region Filter**: Geographic focus (NRW, DE, DACH, EU)
- **Industry Filter**: Target specific industries
- **Domain Blacklist/Whitelist**: Control which sources to use
- **Confidence Score**: Minimum quality threshold for leads

### 🔍 Search Modes
Five different scraping modes with varying API intensity:
- **Standard**: Balanced search with moderate API usage
- **Headhunter**: Focus on LinkedIn/Xing and recruiter topics
- **Aggressive**: Maximum depth, all sources (high API usage)
- **Snippet Only**: Fast scan without deep crawl (minimal API usage)
- **Learning**: AI-optimized queries based on historical success

### 📡 Live Logging
- Server-Sent Events (SSE) for real-time log streaming
- Color-coded log levels (INFO, WARNING, ERROR)
- Automatic scrolling to latest entries

## Architecture

```
dashboard/
├── __init__.py
├── app.py                 # Main Flask application
├── db_schema.py          # Database schema and cost tracking
├── README.md             # This file
├── api/                  # API endpoints
│   ├── __init__.py
│   ├── stats.py         # KPI metrics
│   ├── costs.py         # Cost tracking
│   ├── modes.py         # Search mode management
│   └── settings.py      # Configuration management
├── templates/            # HTML templates
│   ├── base.html        # Base template with navigation
│   ├── dashboard.html   # Main dashboard view
│   ├── analytics.html   # Cost analytics
│   └── settings.html    # Settings page
└── static/              # Static assets (CSS/JS/images)
    ├── css/
    ├── js/
    └── img/
```

## Database Schema

### api_costs Table
Tracks all API calls and their costs:
```sql
CREATE TABLE api_costs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    provider TEXT NOT NULL,        -- 'openai', 'google_cse', 'bing'
    endpoint TEXT,                 -- 'chat/completions', 'search'
    tokens_input INTEGER DEFAULT 0,
    tokens_output INTEGER DEFAULT 0,
    cost_eur REAL DEFAULT 0.0,
    run_id INTEGER,
    model TEXT,
    metadata TEXT
);
```

### search_modes Table
Stores available search mode configurations:
```sql
CREATE TABLE search_modes (
    mode_key TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    deep_crawl INTEGER DEFAULT 1,
    max_depth INTEGER DEFAULT 2,
    use_ai_extraction INTEGER DEFAULT 1,
    snippet_jackpot_only INTEGER DEFAULT 0,
    query_limit INTEGER DEFAULT 15,
    preferred_sources TEXT,
    use_learned_patterns INTEGER DEFAULT 0,
    is_active INTEGER DEFAULT 0
);
```

### dashboard_settings Table
Stores user-configurable settings:
```sql
CREATE TABLE dashboard_settings (
    key TEXT PRIMARY KEY,
    value TEXT,
    value_type TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## API Endpoints

### Statistics
- `GET /api/stats` - Get all KPI metrics
- `GET /api/charts/leads?days=7` - Get lead history chart data
- `GET /api/charts/sources?limit=10` - Get top sources chart data

### Costs
- `GET /api/costs` - Get cost breakdown (today, week, month, by provider, by endpoint)
- `GET /api/costs/chart?days=7` - Get cost chart data for visualization

### Search Modes
- `GET /api/mode` - Get current mode and all available modes
- `POST /api/mode` - Set active search mode
  ```json
  {"mode": "aggressive"}
  ```

### Settings
- `GET /api/settings` - Get all settings and their definitions
- `POST /api/settings` - Update multiple settings
  ```json
  {
    "budget_limit_eur": 1500,
    "region_filter": "DE",
    "industry_filter": ["sales", "vertrieb"]
  }
  ```

### Live Logs
- `GET /api/stream/logs` - Server-Sent Events stream for live logs

### Export
- `GET /api/export/csv` - Download all leads as CSV file

## Installation & Usage

### Requirements
```bash
pip install flask flask-cors
```

All other dependencies (Chart.js, Tailwind CSS) are loaded via CDN.

### Running the Dashboard

#### Standalone Mode
```bash
cd /path/to/luca-nrw-scraper
python3 -m dashboard.app
```

The dashboard will start on `http://127.0.0.1:5056`

#### Custom Database Path
```python
from dashboard.app import create_app

app = create_app(db_path='/path/to/custom/scraper.db')
app.run(host='0.0.0.0', port=5056)
```

### Integration with Scraper

The dashboard automatically initializes when the scraper's `db()` function is called. Cost tracking is integrated into the OpenAI API calls in `scriptname.py`.

To add logging to the dashboard from the scraper:
```python
from dashboard.app import add_log_entry

add_log_entry('INFO', 'Starting scraper run #123')
add_log_entry('WARNING', 'Rate limit approaching')
add_log_entry('ERROR', 'Failed to fetch URL')
```

## Cost Tracking

### OpenAI Pricing (as of December 2024)
- **gpt-4o**: €0.0025 per 1K input tokens, €0.01 per 1K output tokens
- **gpt-4o-mini**: €0.00015 per 1K input tokens, €0.0006 per 1K output tokens
- **gpt-3.5-turbo**: €0.0005 per 1K input tokens, €0.0015 per 1K output tokens

Costs are automatically tracked for each OpenAI API call and displayed in the dashboard.

## Search Mode Configuration

Search modes control the behavior of the scraper. To get the current mode configuration in your code:

```python
from dashboard.api.modes import get_mode_config_for_scraper

config = get_mode_config_for_scraper(DB_PATH)
# Returns: {
#     'mode_key': 'standard',
#     'deep_crawl': True,
#     'max_depth': 2,
#     'use_ai_extraction': True,
#     'query_limit': 15,
#     ...
# }
```

## Security Considerations

1. **Production Deployment**: Use a production WSGI server (gunicorn, uwsgi) instead of Flask's development server
   - Set `FLASK_DEBUG=false` in production
   - Example: `gunicorn -w 4 -b 127.0.0.1:5056 'dashboard.app:create_app()'`

2. **CDN Resources**: Currently using CDN for Tailwind CSS and Chart.js
   - For production, consider hosting these libraries locally
   - Or add Subresource Integrity (SRI) hashes to CDN links
   - Example: `<script src="https://cdn.jsdelivr.net/npm/chart.js" integrity="sha384-..." crossorigin="anonymous"></script>`

3. **Authentication**: Add authentication middleware for production use
   - Consider Flask-Login or OAuth integration
   - Protect sensitive API endpoints

4. **API Rate Limiting**: Implement rate limiting on API endpoints
   - Use Flask-Limiter or similar library
   - Prevent abuse of costly operations

5. **CORS Configuration**: Restrict CORS origins in production
   - Currently allows all origins for development
   - Set specific allowed origins in production

6. **Database Access**: Ensure proper file permissions on scraper.db
   - Database file should not be web-accessible
   - Use appropriate filesystem permissions

7. **Pricing Data**: OpenAI pricing is hardcoded in `db_schema.py`
   - Update pricing values when OpenAI changes rates
   - Consider moving to a configuration file or database table

## Troubleshooting

### Dashboard not loading
- Check that Flask is installed: `pip install flask flask-cors`
- Verify the database path is correct
- Check console logs for errors

### Cost tracking not working
- Ensure the dashboard schema is initialized (happens automatically on first `db()` call)
- Verify OpenAI API calls are returning usage data
- Check database write permissions

### Live logs not appearing
- Verify SSE connection in browser console
- Check that logs are being added via `add_log_entry()`
- Some browsers/proxies may block SSE connections

## Future Enhancements

- PDF report generation for investors
- Email alerts for budget thresholds
- Advanced filtering and search in leads table
- Webhook integrations
- Multi-user support with authentication
- Historical trend analysis
- A/B testing for search modes

## License

Part of the LUCA NRW Scraper project.
