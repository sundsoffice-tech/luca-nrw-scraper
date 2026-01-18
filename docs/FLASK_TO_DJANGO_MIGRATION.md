# Flask to Django CRM Migration Guide

## Overview

The LUCA NRW Scraper has successfully migrated from a Flask-based dashboard to a comprehensive Django CRM system. This document provides details about the migration, endpoint mapping, and instructions for developers.

## Migration Summary

### What Changed

**Removed:**
- `/dashboard/` folder - Legacy Flask dashboard application
- `/start_dashboard.py` - Flask dashboard launcher script
- `flask-cors` dependency from `requirements.txt` (only used by dashboard)
- Dashboard schema initialization from `luca_scraper/database.py`
- Dashboard imports from `scriptname.py`
- API cost tracking calls to `dashboard.db_schema.track_api_cost()`

**Retained:**
- `flask` dependency - Still needed for the basic scraper UI (`python scriptname.py --ui`)

**Added:**
- `/telis_recruitment/` - Full-featured Django CRM (already exists)
- This migration documentation

### Why Migrate?

The Django CRM (`telis_recruitment`) provides:
- **Superior Architecture**: Django's robust ORM, admin interface, and REST framework
- **Enhanced Features**: Role-based permissions, activity tracking, team management
- **Better Scalability**: Production-ready with proper authentication and security
- **Unified System**: Single source of truth for lead management
- **Modern UI/UX**: Professional dashboard with responsive design

## Endpoint Mapping

### Flask Dashboard → Django CRM

| Flask Endpoint (Old) | Django CRM Endpoint (New) | Description |
|---------------------|---------------------------|-------------|
| `http://127.0.0.1:5056/` | `http://127.0.0.1:8000/crm/` | Main dashboard |
| `http://127.0.0.1:5056/leads` | `http://127.0.0.1:8000/crm/leads/` | Lead management |
| `http://127.0.0.1:5056/analytics` | `http://127.0.0.1:8000/crm/analytics/` | Analytics & reports |
| `http://127.0.0.1:5056/settings` | `http://127.0.0.1:8000/crm/settings/` | Configuration |
| `http://127.0.0.1:5056/api/stats` | `http://127.0.0.1:8000/crm/api/stats/` | Statistics API |
| `http://127.0.0.1:5056/api/export/csv` | `http://127.0.0.1:8000/crm/api/export/csv/` | CSV export |
| N/A | `http://127.0.0.1:8000/crm/scraper/` | Scraper control (Admin only) |
| N/A | `http://127.0.0.1:8000/admin/` | Django admin interface |

### Scraper Control Endpoints

The Django CRM includes an integrated scraper control panel with the following API endpoints:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/crm/api/scraper/start/` | POST | Start scraper with parameters |
| `/crm/api/scraper/stop/` | POST | Stop running scraper |
| `/crm/api/scraper/status/` | GET | Get current scraper status |
| `/crm/api/scraper/logs/` | GET | Live log stream (SSE) |
| `/crm/api/export/csv/` | GET | Export leads as CSV |
| `/crm/api/export/excel/` | GET | Export leads as Excel |

## Developer Instructions

### Getting Started with Django CRM

1. **Navigate to Django CRM directory:**
   ```bash
   cd telis_recruitment
   ```

2. **Create and activate virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env file with your configuration
   ```

5. **Initialize database:**
   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   ```

6. **Start development server:**
   ```bash
   python manage.py runserver
   ```

7. **Access the system:**
   - CRM Dashboard: http://127.0.0.1:8000/crm/
   - Admin Interface: http://127.0.0.1:8000/admin/
   - Scraper Control: http://127.0.0.1:8000/crm/scraper/

### Key Differences for Developers

#### Database Schema

**Flask (Old):**
- Dashboard used custom SQLite tables in the same database as the scraper
- Schema managed by `dashboard.db_schema.py`
- Manual SQL queries and connections

**Django CRM (New):**
- Django ORM with proper models and migrations
- Separate concerns: scraper DB for raw data, Django DB for CRM operations
- Automatic schema management via migrations

#### API Integration

**Flask (Old):**
```python
# Old way - NO LONGER WORKS
from dashboard.db_schema import track_api_cost
track_api_cost(con, provider='openai', tokens_input=100, tokens_output=50)
```

**Django CRM (New):**
```python
# New way - use Django REST API
import requests
response = requests.post(
    'http://127.0.0.1:8000/crm/api/usage/',
    json={'provider': 'openai', 'tokens_input': 100, 'tokens_output': 50},
    headers={'Authorization': 'Token YOUR_API_TOKEN'}
)
```

Or use the Django models directly if working within the Django project:
```python
from leads.models import APIUsage
APIUsage.objects.create(
    provider='openai',
    tokens_input=100,
    tokens_output=50,
    model='gpt-4o-mini'
)
```

#### Starting the Scraper

**Flask (Old):**
```bash
python start_dashboard.py  # NO LONGER EXISTS
```

**Django CRM (New):**
```bash
# Option 1: Use the web interface
# Navigate to http://127.0.0.1:8000/crm/scraper/ and click "Start Scraper"

# Option 2: Use the command line
cd ..  # Return to root directory
python scriptname.py --once --industry recruiter --qpi 6

# Option 3: Use the API
curl -X POST http://127.0.0.1:8000/crm/api/scraper/start/ \
  -H "Authorization: Token YOUR_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"industry": "recruiter", "qpi": 6}'
```

### Code Migration Examples

#### Example 1: Checking Dashboard Status

**Before (Flask):**
```python
import requests
response = requests.get('http://127.0.0.1:5056/api/stats')
stats = response.json()
```

**After (Django):**
```python
import requests
response = requests.get('http://127.0.0.1:8000/crm/api/stats/')
stats = response.json()
```

#### Example 2: Exporting Leads

**Before (Flask):**
```python
# Access via Flask endpoint
url = 'http://127.0.0.1:5056/api/export/csv'
```

**After (Django):**
```python
# Access via Django CRM endpoint with authentication
url = 'http://127.0.0.1:8000/crm/api/export/csv/'
headers = {'Authorization': 'Token YOUR_API_TOKEN'}
response = requests.get(url, headers=headers)
```

### Testing Your Migration

1. **Verify scraper runs without errors:**
   ```bash
   python scriptname.py --once --industry recruiter --qpi 2
   ```

2. **Check for import errors:**
   ```bash
   python -c "import scriptname; print('No import errors!')"
   ```

3. **Verify Django CRM is accessible:**
   ```bash
   cd telis_recruitment
   python manage.py check
   python manage.py runserver
   # Visit http://127.0.0.1:8000/crm/
   ```

4. **Run existing tests:**
   ```bash
   cd telis_recruitment
   python manage.py test
   ```

## Rollback Instructions (Emergency Only)

If you need to temporarily rollback to the Flask dashboard:

1. **Checkout the previous commit:**
   ```bash
   git log --oneline  # Find commit before migration
   git checkout <commit-hash> -- dashboard/
   git checkout <commit-hash> -- start_dashboard.py
   ```

2. **Restore Flask dependencies:**
   ```bash
   pip install flask>=2.3.2 flask-cors>=4.0.0
   ```

3. **Start Flask dashboard:**
   ```bash
   python start_dashboard.py
   ```

**Note:** This is only for emergency situations. The Django CRM is the recommended solution going forward.

## Migration Benefits

### For Users
- ✅ Modern, responsive UI with better UX
- ✅ Role-based access control (Admin/Manager/Telefonist)
- ✅ Enhanced reporting and analytics
- ✅ Better data management and filtering
- ✅ Integrated scraper control panel
- ✅ Production-ready authentication and security

### For Developers
- ✅ Django ORM instead of raw SQL
- ✅ Built-in admin interface
- ✅ Django REST Framework for APIs
- ✅ Proper migrations for schema changes
- ✅ Better code organization and structure
- ✅ Extensive Django ecosystem and plugins
- ✅ Better testing infrastructure

### For Operations
- ✅ Production-ready with gunicorn/nginx
- ✅ Better logging and monitoring
- ✅ Easier deployment and scaling
- ✅ Database flexibility (PostgreSQL, MySQL, etc.)
- ✅ Built-in security features (CSRF, XSS protection)

## Support

For questions or issues related to the Django CRM:
- See [telis_recruitment/README.md](../telis_recruitment/README.md)
- Check [telis_recruitment/SCRAPER_INTEGRATION.md](../telis_recruitment/SCRAPER_INTEGRATION.md)
- Create an issue in the repository

## Important Notes

### Scraper Basic UI vs. Flask Dashboard

**The scraper's built-in UI (`python scriptname.py --ui`) is NOT the same as the removed Flask dashboard:**

- **Scraper Basic UI** (`--ui` mode):
  - Simple control interface for starting/stopping scraper runs
  - Built into `scriptname.py`
  - Runs on port 5055
  - Still available and functional
  - Uses Flask for basic HTTP serving (retained in requirements.txt)
  
- **Flask Dashboard** (removed):
  - Full-featured control center on port 5056
  - Separate application in `/dashboard/` folder
  - Had KPI tracking, analytics, settings, etc.
  - Completely replaced by Django CRM

**If you need full dashboard functionality, use the Django CRM instead of the basic scraper UI.**

## Changelog

- **2026-01-18**: Completed migration from Flask to Django CRM
  - Removed Flask dashboard (`/dashboard/`)
  - Removed `start_dashboard.py`
  - Updated `README.md` with Django CRM instructions
  - Removed `flask-cors` from `requirements.txt` (kept `flask` for basic scraper UI)
  - Cleaned up dashboard imports from scraper code
  - Created this migration guide
