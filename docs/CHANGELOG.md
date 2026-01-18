# Changelog

All notable changes to the LUCA NRW Scraper project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Removed - 2026-01-18

#### Flask Dashboard and Static Landing Removal

**Context**: The project has fully migrated to Django CRM as the primary user interface, replacing the legacy Flask dashboard and static landing page.

**What was removed:**
- `/dashboard.py` - Standalone Flask-based learning dashboard script
  - Provided CLI-based visualization of scraper metrics, portal performance, and learning statistics
  - Superseded by Django CRM's integrated dashboard with superior UI/UX
  
- `/landing/` directory - Static HTML/CSS/JS landing page
  - `landing/index.html` - Main landing page HTML
  - `landing/styles.css` - Landing page styles
  - `landing/script.js` - Landing page JavaScript
  - `landing/assets/` - Image assets
  - `landing/README.md` - Landing page documentation
  - Replaced by Django Pages app with GrapesJS visual editor

**What was updated:**
- `/README.md` - Updated to emphasize Django CRM as primary interface
  - Reorganized Quick Start section to prioritize Django CRM
  - Enhanced feature list to include all Django CRM capabilities:
    - Dashboard KPIs and real-time statistics
    - Integrated scraper control panel
    - Lead management with advanced filtering
    - Landing page builder (GrapesJS)
    - AI configuration interface
    - Brevo integration for email automation
  - Clarified that command-line scraper remains available for standalone operations
  
- `/.gitignore` - Added missing entries
  - `venv/` - Virtual environment directory
  - `staticfiles/` - Django static files collection directory
  
- `/example_login_usage.py` - Removed reference to `dashboard.py` in next steps output

**Migration Path:**
- Users of `dashboard.py` should now use:
  - Django CRM Dashboard: `http://127.0.0.1:8000/crm/`
  - Django Admin Interface: `http://127.0.0.1:8000/admin/`
  
- Users of `/landing/` static site should now use:
  - Django Pages app: `http://127.0.0.1:8000/crm/pages/`
  - Published pages: `http://127.0.0.1:8000/p/home/`
  - Visual page editor available in Django CRM

**Why this change:**
- **Unified Architecture**: Single Django-based system for all functionality
- **Better Features**: Django CRM provides superior user experience with:
  - Role-based access control (Admin/Manager/Telefonist)
  - Real-time scraper monitoring and control
  - Advanced lead management and analytics
  - Visual landing page builder
  - REST API for integrations
- **Easier Maintenance**: One codebase to maintain instead of multiple separate systems
- **Production Ready**: Django provides enterprise-grade security, scalability, and deployment options

**Impact:**
- `python dashboard.py` command is no longer available
- Static landing page URLs are no longer served from `/landing/`
- All dashboard and landing page functionality is now accessed through Django CRM

**References:**
- Full migration guide: `/docs/FLASK_TO_DJANGO_MIGRATION.md`
- Django CRM documentation: `/telis_recruitment/README.md`
- Scraper integration guide: `/telis_recruitment/SCRAPER_INTEGRATION.md`

**Dependencies:**
- No changes to `requirements.txt` - Flask is retained for basic scraper UI mode (`python scriptname.py --ui`)
- `flask-cors` was previously removed as it was only used by the deprecated Flask dashboard

---

## Historical Context

Prior to this change:
- The project had three separate interfaces:
  1. Command-line scraper with basic Flask UI (`--ui` mode)
  2. Flask-based dashboard (`dashboard.py`) for metrics visualization
  3. Static landing page (`/landing/`) for public-facing content
  4. Django CRM for lead management

After this change:
- The project has two interfaces:
  1. Command-line scraper with basic Flask UI (`--ui` mode) - for standalone scraper operations
  2. Django CRM - unified interface for all dashboard, lead management, and landing page functionality

This consolidation improves maintainability, user experience, and aligns with modern web application best practices.
