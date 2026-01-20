# LUCA NRW Scraper

[![Version](https://img.shields.io/badge/version-2.4.0-blue.svg)](CHANGELOG.md)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Django](https://img.shields.io/badge/django-4.2-success.svg)](https://www.djangoproject.com/)

**Professional Lead Generation & CRM System for NRW Sales Teams**

Zweck: NRW-Vertriebsleads automatisch finden, bewerten, exportieren.

## 📋 Latest Release

**Current Version**: v2.4.0 ([Release Notes](RELEASE_NOTES.md) | [Changelog](CHANGELOG.md))

### Key Highlights
- 🔒 Enhanced security with SSL/TLS validation by default
- 📋 Configuration profiles for production, high-volume, and debug modes
- 📦 Support bundle system for diagnostics
- 🛡️ Comprehensive security checklist for production deployments

## 🚀 Quick Start

### 🐳 Docker (Recommended)
The fastest way to get started with LUCA Command Center:

```bash
# Clone and setup
git clone https://github.com/sundsoffice-tech/luca-nrw-scraper.git
cd luca-nrw-scraper
cp .env.example .env

# Edit .env with your settings (required: SECRET_KEY)
nano .env

# Start with Docker
docker-compose up -d

# Create admin user
docker-compose exec web python manage.py createsuperuser

# Access: http://localhost:8000/crm/
```

See [docs/INSTALLATION.md](docs/INSTALLATION.md) for detailed installation instructions and [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for production deployment guides.

### 🔧 Manual Installation

**Linux/Mac:**
```bash
./install.sh
```

**Windows:**
```cmd
install.bat
```

Then start the server:
```bash
source venv/bin/activate  # Linux/Mac
# or venv\Scripts\activate.bat for Windows
cd telis_recruitment
python manage.py runserver
```

### 🎯 Django CRM (Primary Interface)
Professional Django-based CRM system for managing leads, controlling the scraper, and accessing all features.

**Access Points:**
- **CRM Dashboard**: http://127.0.0.1:8000/crm/ - Main interface with KPIs and lead management
- **Admin Interface**: http://127.0.0.1:8000/admin/ - Django admin panel
- **Scraper Control**: http://127.0.0.1:8000/crm/scraper/ - Start/stop scraper with live monitoring
- **AI Configuration**: http://127.0.0.1:8000/admin/ai_config/ - Configure AI provider settings
- **Landing Page Builder**: http://127.0.0.1:8000/crm/pages/ - Visual page editor (GrapesJS)
- **API Endpoints**: http://127.0.0.1:8000/api/ - REST API for integrations

**Features:**
- 📊 **Dashboard KPIs**: Real-time statistics and performance metrics
- 🤖 **Integrated Scraper Control**: Start/stop scraper with live log monitoring
- 👥 **Lead Management**: Advanced filtering, search, and bulk actions
- 📈 **Analytics & Reports**: Activity feed and team performance overview
- 📥 **Export Options**: CSV/Excel export with advanced filters
- 🔐 **Role-Based Access**: Admin/Manager/Telefonist permissions
- 🌐 **Landing Page Builder**: Create and manage public landing pages
- 📧 **Brevo Integration**: Email automation and contact sync

See [telis_recruitment/README.md](telis_recruitment/README.md) for detailed documentation.

### ⚙️ Configuration Profiles

LUCA includes pre-configured environment profiles for different deployment scenarios:

```bash
# Production Safe (recommended for live deployments)
cp configs/production.env .env

# High Volume (for bulk lead generation)
cp configs/high-volume.env .env

# Debug Mode (for development and troubleshooting)
cp configs/debug.env .env
```

Each profile is optimized for specific use cases with appropriate security and performance settings.
See [configs/README.md](configs/README.md) for detailed profile documentation.

### 🗄️ Database Backend Configuration

LUCA supports two database backends that can be switched via environment variable:

- **SQLite** (default): Lightweight, file-based database suitable for standalone usage
- **Django ORM**: Integration with Django CRM system for unified data management

```bash
# Use SQLite backend (default)
export SCRAPER_DB_BACKEND=sqlite

# Use Django ORM backend (for CRM integration)
export SCRAPER_DB_BACKEND=django
```

**When to use each backend:**
- **SQLite**: Standalone scraper, development, testing, small-scale deployments
- **Django**: Production CRM deployments, centralized data management, team collaboration

See [docs/CONFIGURATION_PROFILES.md](docs/CONFIGURATION_PROFILES.md) for detailed backend configuration.

### Command-Line Scraper
For standalone scraper operations without the CRM interface:
```bash
# Single run with specific parameters
python scriptname.py --once --industry recruiter --qpi 6 --daterestrict d30

# Talent Hunt Mode (Find active sales professionals)
python scriptname.py --once --industry talent_hunt --qpi 15

# Start scraper with basic UI (minimal web interface)
python scriptname.py --ui
```

## Adaptive Throttling & Metrics

The scraper relies on the waterfall throttling strategy (`wasserfall.py`) to adjust aggressiveness based on the phone-find rate and host health. We only step toward `moderate` or `aggressive` once the feedback loop proves the current crawl can sustain a higher load, and we step back when drops or backoffs spike so that monitored hosts remain usable.

### Adaptive Mode API

- `WasserfallManager.increment_run()` counts each dispatch to enforce the minimum number of runs before evaluating a mode change so we avoid rapid oscillations.
- `WasserfallManager.check_and_transition()` compares the measured phone-find rate against `phone_find_rate_threshold` and inspects the ratio of backed-off hosts before committing to a transition; every upward move is justified by a stable signal.
- `transition_mode(direction, reason)` records the rationale (phone rate, backoff counts, run history) so callers always understand why the system shifted gears.

```python
from wasserfall import WasserfallManager
from metrics import get_metrics_store

metrics = get_metrics_store()
manager = WasserfallManager(metrics, initial_mode="moderate")

# Each dispatcher run increments the counter before we evaluate a transition.
manager.increment_run()
transition = manager.check_and_transition()
if transition:
    print("Mode switched:", transition["from_mode"], "→", transition["to_mode"])
```

### Metrics Signals for Transitions

- `calculate_phone_find_rate()` produces the lead-to-fetch ratio that triggers upward transitions, emphasizing throughput quality instead of raw volume.
- `get_backedoff_hosts()` ensures we see a small fraction of hosts already backed off so we can protect the fleet before pushing toward `aggressive`.
- `record_drop(...)`, `set_host_backoff(...)`, and `record_query(...)` allow other modules to feed actionable evidence into the next evaluation cycle, keeping the heuristics synchronized without duplicating storage.

These APIs let both the scraper and CRM dashboards share the same metrics store (`metrics.py`) for reporting and debugging while keeping the waterfall rules declarative.

## 📚 Documentation

### 🎯 Onboarding (Neu!)
- **[⚡ QUICKSTART (20 Min)](docs/QUICKSTART.md)** - Von 0 zu deinen ersten Leads
- **[⚙️ Configuration Profiles](docs/CONFIGURATION_PROFILES.md)** - Safe/Balanced/Aggressive Modi
- **[🆘 Troubleshooting](docs/TROUBLESHOOTING.md)** - Problemlösung nach Symptomen

### 📖 Setup & Deployment
- **[Installation Guide](docs/INSTALLATION.md)** - Complete installation instructions (Docker, manual)
- **[Deployment Guide](docs/DEPLOYMENT.md)** - Production deployment to Railway, Render, Fly.io, Hetzner
- **[Configuration Profiles](docs/CONFIGURATION_PROFILES.md)** - Environment configuration for different scenarios
- **[Security Checklist](docs/SECURITY_CHECKLIST.md)** - Production security requirements and best practices
- **[Release Process](docs/RELEASE_PROCESS.md)** - How we version and release LUCA
- **[Django CRM Details](telis_recruitment/README.md)** - Detailed Django CRM documentation

## 🔐 Security & Production

LUCA is built with security and production-readiness in mind:

- ✅ **Secure by Default**: SSL/TLS validation enabled, secure cookie settings
- ✅ **Configuration Profiles**: Pre-configured profiles for production, high-volume, and debug
- ✅ **Role-Based Access Control**: Admin, Manager, Operator, and Viewer roles
- ✅ **Security Checklist**: Comprehensive checklist for production deployments
- ✅ **Support Bundle**: One-click diagnostics export for troubleshooting
- ✅ **No Secrets in Logs**: Automatic sanitization of sensitive data

See [docs/SECURITY_CHECKLIST.md](docs/SECURITY_CHECKLIST.md) for the complete security guide.

## 📦 Support & Diagnostics

LUCA includes built-in support tools:

1. **Support Bundle**: Generate a comprehensive diagnostics package
   ```bash
   python manage.py create_support_bundle
   ```
   Or use the UI: CRM → Support → Support Bundle

2. **System Health**: Monitor system resources and configuration
   - Access via CRM → Support → System Health

3. **Comprehensive Logging**: Structured logging for troubleshooting
   - Logs are sanitized to remove sensitive data

## 🚀 Version History

See [CHANGELOG.md](CHANGELOG.md) for detailed version history and [RELEASE_NOTES.md](RELEASE_NOTES.md) for user-facing release information.

### Recent Releases

- **v2.4.0** (2026-01-19): Enhanced security, configuration profiles, support system
- **v2.3.0**: Django CRM dashboard, landing page builder, Brevo integration

## 📸 Screenshots

![Dashboard Main](https://github.com/user-attachments/assets/42f913bb-b1da-4b7e-b034-d352ef41bf65)
*Main dashboard with KPIs, charts, and live logs*

![Settings Page](https://github.com/user-attachments/assets/38823f05-d1f3-4fbe-af0a-65b4662e9ed8)
*Settings page for configuration management*
