Zweck: NRW-Vertriebsleads automatisch finden, bewerten, exportieren.

## 🚀 Quick Start

### 🎯 Django CRM (Primary Interface)
Professional Django-based CRM system for managing leads, controlling the scraper, and accessing all features.

**Quick Start:**
```bash
cd telis_recruitment
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
# Open http://127.0.0.1:8000/crm/
```

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

## 📸 Screenshots

![Dashboard Main](https://github.com/user-attachments/assets/42f913bb-b1da-4b7e-b034-d352ef41bf65)
*Main dashboard with KPIs, charts, and live logs*

![Settings Page](https://github.com/user-attachments/assets/38823f05-d1f3-4fbe-af0a-65b4662e9ed8)
*Settings page for configuration management*
