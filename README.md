Zweck: NRW-Vertriebsleads automatisch finden, bewerten, exportieren.

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

## 📚 Documentation

- **[Installation Guide](docs/INSTALLATION.md)** - Complete installation instructions (Docker, manual, troubleshooting)
- **[Deployment Guide](docs/DEPLOYMENT.md)** - Production deployment to Railway, Render, Fly.io, Hetzner
- **[Django CRM Details](telis_recruitment/README.md)** - Detailed Django CRM documentation

## 📸 Screenshots

![Dashboard Main](https://github.com/user-attachments/assets/42f913bb-b1da-4b7e-b034-d352ef41bf65)
*Main dashboard with KPIs, charts, and live logs*

![Settings Page](https://github.com/user-attachments/assets/38823f05-d1f3-4fbe-af0a-65b4662e9ed8)
*Settings page for configuration management*
