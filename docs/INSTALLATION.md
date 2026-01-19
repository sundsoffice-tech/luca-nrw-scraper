# LUCA Command Center - Installation Guide

This guide covers multiple installation methods for the LUCA Command Center Django CRM system.

## Table of Contents

- [Docker Installation (Recommended)](#docker-installation-recommended)
- [Manual Installation](#manual-installation)
- [Environment Configuration](#environment-configuration)
- [First Start](#first-start)
- [Troubleshooting](#troubleshooting)

---

## Docker Installation (Recommended)

The easiest way to get started is using Docker.

### Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+

### Quick Start

1. **Clone the repository:**
   ```bash
   git clone https://github.com/sundsoffice-tech/luca-nrw-scraper.git
   cd luca-nrw-scraper
   ```

2. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your settings (see Environment Configuration section)
   nano .env
   ```

3. **Build and start:**
   ```bash
   docker-compose up -d
   ```

4. **Create admin user:**
   ```bash
   docker-compose exec web python manage.py createsuperuser
   ```

5. **Access the application:**
   - CRM Dashboard: http://localhost:8000/crm/
   - Admin Interface: http://localhost:8000/admin/

### Docker Commands

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f web

# Stop services
docker-compose down

# Rebuild after code changes
docker-compose up -d --build

# Run migrations
docker-compose exec web python manage.py migrate

# Collect static files
docker-compose exec web python manage.py collectstatic --noinput

# Create superuser
docker-compose exec web python manage.py createsuperuser

# Access Django shell
docker-compose exec web python manage.py shell
```

### Running the Scraper with Docker

The scraper can be run as an optional service:

```bash
# Run scraper once
docker-compose --profile scraper up scraper

# Run with custom parameters (edit docker-compose.yml first)
docker-compose --profile scraper up scraper
```

---

## Manual Installation

### Prerequisites

- Python 3.9 or higher
- pip (Python package manager)
- Git

### Linux/Mac Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/sundsoffice-tech/luca-nrw-scraper.git
   cd luca-nrw-scraper
   ```

2. **Run the installation script:**
   ```bash
   ./install.sh
   ```

   The script will:
   - Create a virtual environment
   - Install all dependencies
   - Copy `.env.example` to `.env`
   - Run database migrations
   - Collect static files
   - Optionally create a superuser

3. **Activate virtual environment:**
   ```bash
   source venv/bin/activate
   ```

4. **Start the server:**
   ```bash
   cd telis_recruitment
   python manage.py runserver
   ```

### Windows Installation

1. **Clone the repository:**
   ```cmd
   git clone https://github.com/sundsoffice-tech/luca-nrw-scraper.git
   cd luca-nrw-scraper
   ```

2. **Run the installation script:**
   ```cmd
   install.bat
   ```

   The script will perform the same steps as the Linux/Mac version.

3. **Activate virtual environment:**
   ```cmd
   venv\Scripts\activate.bat
   ```

4. **Start the server:**
   ```cmd
   cd telis_recruitment
   python manage.py runserver
   ```

### Manual Step-by-Step Installation

If you prefer manual control:

1. **Create virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Linux/Mac
   # or
   venv\Scripts\activate.bat  # Windows
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   pip install -r telis_recruitment/requirements.txt
   ```

3. **Setup environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

4. **Run migrations:**
   ```bash
   cd telis_recruitment
   python manage.py migrate
   ```

5. **Collect static files:**
   ```bash
   python manage.py collectstatic --noinput
   ```

6. **Create superuser:**
   ```bash
   python manage.py createsuperuser
   ```

7. **Start development server:**
   ```bash
   python manage.py runserver
   ```

---

## Environment Configuration

Edit the `.env` file with your specific settings:

### Required Settings

```bash
# Generate a secure secret key
SECRET_KEY=your-very-secure-secret-key-here

# Set to False in production
DEBUG=False

# Your domain(s)
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# For CSRF protection
CSRF_TRUSTED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

### Generate Secret Key

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### API Keys (Optional)

```bash
# For AI features
OPENAI_API_KEY=sk-...
PERPLEXITY_API_KEY=pplx-...

# For email automation
BREVO_API_KEY=xkeysib-...
```

### Scraper Configuration

```bash
SCRAPER_MODE=once
SCRAPER_QPI=6
SCRAPER_DATE_RESTRICT=d30
SCRAPER_DEFAULT_INDUSTRY=recruiter
```

---

## First Start

### 1. Create Your First Admin User

```bash
# Docker
docker-compose exec web python manage.py createsuperuser

# Manual installation
cd telis_recruitment
python manage.py createsuperuser
```

### 2. Access the CRM

Open your browser and visit:
- **CRM Dashboard**: http://localhost:8000/crm/
- **Admin Panel**: http://localhost:8000/admin/

### 3. Configure AI Providers (Optional)

1. Log in to the admin panel
2. Navigate to **AI Configuration** → **AI Providers**
3. Add your API keys for OpenAI, Perplexity, or other providers
4. Configure AI models and prompt templates

### 4. Setup User Roles

1. Navigate to **System** → **Groups**
2. Run the setup command:
   ```bash
   python manage.py setup_groups
   ```
3. Assign users to appropriate groups (Admin, Manager, Telefonist)

---

## Troubleshooting

### Common Issues

#### 1. Port 8000 Already in Use

**Problem:** `Error: That port is already in use.`

**Solution:**
```bash
# Find and kill the process using port 8000
# Linux/Mac
lsof -ti:8000 | xargs kill -9

# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Or use a different port
python manage.py runserver 0.0.0.0:8080
```

#### 2. Static Files Not Loading

**Problem:** CSS/JS files not loading in production.

**Solution:**
```bash
# Collect static files again
python manage.py collectstatic --noinput --clear

# Check STATIC_ROOT in settings
# Make sure Whitenoise is configured correctly
```

For more issues, see the [Troubleshooting Guide](TROUBLESHOOTING.md).

### Database Commands

```bash
# Backup database
cp telis_recruitment/db.sqlite3 telis_recruitment/db.sqlite3.backup

# Restore database
cp telis_recruitment/db.sqlite3.backup telis_recruitment/db.sqlite3

# Reset database (CAUTION: Deletes all data!)
rm telis_recruitment/db.sqlite3
python manage.py migrate
python manage.py createsuperuser
```

### Logs

View application logs:

```bash
# Docker
docker-compose logs -f web

# Manual installation (development server shows logs in terminal)
cd telis_recruitment
python manage.py runserver
```

---

## Next Steps

After successful installation:

1. **🚀 Get Started:** Follow the [QUICKSTART Guide](QUICKSTART.md) for your first scraper run (20 minutes)
2. **⚙️ Optimize Configuration:** Check [Configuration Profiles](CONFIGURATION_PROFILES.md) (Safe/Balanced/Aggressive modes)
3. **🔧 Fine-tune Settings:** Configure AI providers in the admin panel
4. **📊 Import Leads:** Import existing leads if you have them
5. **🤖 Automate:** Set up automated scraper runs
6. **🚀 Deploy:** For production, read [DEPLOYMENT.md](DEPLOYMENT.md)

### Configuration Profiles

Choose the right profile for your use case:
- **Safe Mode (QPI=6):** First tests, no API keys needed → [Details](CONFIGURATION_PROFILES.md#safe-mode)
- **Balanced Mode (QPI=12):** Daily production use → [Details](CONFIGURATION_PROFILES.md#balanced-mode)
- **Aggressive Mode (QPI=20):** Maximum throughput, proxy recommended → [Details](CONFIGURATION_PROFILES.md#aggressive-mode)

---

## Troubleshooting

For detailed troubleshooting by symptoms, see the **[🆘 Troubleshooting Guide](TROUBLESHOOTING.md)**.

The guide includes solutions for:
- [I'm getting 0 leads](TROUBLESHOOTING.md#ich-bekomme-0-leads)
- [Login/Session not working](TROUBLESHOOTING.md#loginsession-klappt-nicht)
- [Too many 403/blocks](TROUBLESHOOTING.md#zu-viele-403blockaden)
- [CRM shows nothing](TROUBLESHOOTING.md#crm-zeigt-nichts-an)
- [Scraper runs but doesn't save](TROUBLESHOOTING.md#scraper-läuft-aber-speichert-nicht)

### Common Installation Issues

#### 1. Port 8000 Already in Use

**Problem:** `Error: That port is already in use.`

**Solution:**
```bash
# Find and kill the process using port 8000
# Linux/Mac
lsof -ti:8000 | xargs kill -9

# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Or use a different port
python manage.py runserver 0.0.0.0:8080
```

#### 2. Static Files Not Loading

See [Troubleshooting Guide](TROUBLESHOOTING.md#static-files-not-loading) for full details.

#### 3. Docker Container Fails

See [Troubleshooting Guide](TROUBLESHOOTING.md#docker-container-fails) for full details.

---

## Support

For issues and questions:
- **[🆘 Troubleshooting Guide](TROUBLESHOOTING.md)** - Solve problems by symptoms
- Check existing [GitHub Issues](https://github.com/sundsoffice-tech/luca-nrw-scraper/issues)
- Create a new issue with detailed information
- Review the [README.md](../README.md) for feature documentation
