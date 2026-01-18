# LUCA Command Center - Production Deployment Guide

This guide covers deploying LUCA Command Center (Django CRM) to various cloud platforms.

## Table of Contents

- [Deployment Overview](#deployment-overview)
- [Railway (Easiest)](#railway-deployment)
- [Render](#render-deployment)
- [Fly.io](#flyio-deployment)
- [Hetzner VPS](#hetzner-vps-deployment)
- [Custom Domain & SSL](#custom-domain--ssl)
- [Database Backups](#database-backups)
- [Monitoring](#monitoring)

---

## Deployment Overview

### Platform Comparison

| Platform | Difficulty | Cost (Starter) | SQLite Support | Auto-Deploy | Best For |
|----------|-----------|----------------|----------------|-------------|----------|
| **Railway** | ⭐ Easy | ~$5/mo | ✅ Yes | ✅ Yes | Quick start, GitHub integration |
| **Render** | ⭐⭐ Medium | $7/mo | ✅ Yes | ✅ Yes | Reliable, good docs |
| **Fly.io** | ⭐⭐⭐ Advanced | ~$3/mo | ✅ Yes | ✅ Yes | Docker-native, flexible |
| **Hetzner VPS** | ⭐⭐⭐ Advanced | €4.15/mo | ✅ Yes | ❌ No | Full control, best value |

### Pre-Deployment Checklist

- [ ] `.env` configured with production settings
- [ ] `DEBUG=False` in `.env`
- [ ] `SECRET_KEY` set to a strong random value
- [ ] `ALLOWED_HOSTS` includes your domain
- [ ] `CSRF_TRUSTED_ORIGINS` includes your domain with protocol
- [ ] Static files collected: `python manage.py collectstatic`
- [ ] All migrations applied: `python manage.py migrate`
- [ ] Superuser created: `python manage.py createsuperuser`

---

## Railway Deployment

Railway is the easiest platform for deploying Django apps with excellent GitHub integration.

### Step 1: Prepare Your Repository

Ensure these files are in your repository root:
- ✅ `Procfile`
- ✅ `requirements.txt`
- ✅ `telis_recruitment/requirements.txt`
- ✅ `.env.example`

### Step 2: Create Railway Account

1. Visit [railway.app](https://railway.app)
2. Sign up with GitHub
3. Click "New Project"

### Step 3: Deploy from GitHub

1. Click "Deploy from GitHub repo"
2. Select `sundsoffice-tech/luca-nrw-scraper`
3. Railway will automatically detect the Django app

### Step 4: Configure Environment Variables

In Railway dashboard → Variables:

```bash
SECRET_KEY=your-generated-secret-key-here
DEBUG=False
ALLOWED_HOSTS=your-app.railway.app
CSRF_TRUSTED_ORIGINS=https://your-app.railway.app
DJANGO_SETTINGS_MODULE=telis.settings_prod

# Optional: Add your API keys
OPENAI_API_KEY=sk-...
BREVO_API_KEY=xkeysib-...
```

### Step 5: Configure Build & Deploy

Railway auto-detects the `Procfile`. If needed, customize:

**Settings → Deploy:**
- Build Command: `pip install -r requirements.txt && pip install -r telis_recruitment/requirements.txt && cd telis_recruitment && python manage.py collectstatic --noinput`
- Start Command: Uses `Procfile` automatically

### Step 6: Setup Database Persistence

Railway ephemeral filesystem requires volume for SQLite:

**Settings → Volumes:**
1. Click "New Volume"
2. Mount path: `/app/telis_recruitment`
3. This persists `db.sqlite3`

### Step 7: Create Superuser

Use Railway's shell:

```bash
cd telis_recruitment
python manage.py createsuperuser
```

### Step 8: Access Your App

Your app will be available at: `https://your-app.railway.app/crm/`

### Railway Tips

- **Auto-Deploy:** Push to GitHub = automatic deployment
- **Logs:** Railway dashboard → Deployments → View logs
- **Cost:** ~$5/month for 500 hours, scales automatically
- **Custom Domain:** Settings → Domains → Add custom domain

---

## Render Deployment

Render offers reliable hosting with a generous free tier (with limitations).

### Step 1: Create Render Account

1. Visit [render.com](https://render.com)
2. Sign up with GitHub

### Step 2: Create Web Service

1. Dashboard → "New +" → "Web Service"
2. Connect your GitHub repository
3. Configure:
   - **Name:** luca-command-center
   - **Region:** Choose closest to your users
   - **Branch:** main
   - **Root Directory:** (leave empty)
   - **Runtime:** Python 3
   - **Build Command:**
     ```bash
     pip install -r requirements.txt && pip install -r telis_recruitment/requirements.txt && cd telis_recruitment && python manage.py collectstatic --noinput
     ```
   - **Start Command:**
     ```bash
     cd telis_recruitment && gunicorn --bind 0.0.0.0:$PORT telis.wsgi:application
     ```

### Step 3: Environment Variables

Add in Render dashboard:

```bash
PYTHON_VERSION=3.11.0
SECRET_KEY=your-generated-secret-key
DEBUG=False
ALLOWED_HOSTS=your-app.onrender.com
CSRF_TRUSTED_ORIGINS=https://your-app.onrender.com
DJANGO_SETTINGS_MODULE=telis.settings_prod
```

### Step 4: Add Persistent Disk

**Important:** Render's free tier has ephemeral storage. For persistent SQLite:

1. Dashboard → Disks
2. Add disk:
   - **Name:** luca-db
   - **Mount Path:** `/app/telis_recruitment`
   - **Size:** 1 GB (free)

### Step 5: Deploy

Click "Create Web Service" - Render will build and deploy.

### Step 6: Run Migrations

Once deployed, use Render shell:

```bash
cd telis_recruitment
python manage.py migrate
python manage.py createsuperuser
```

### Step 7: Access Your App

Available at: `https://your-app.onrender.com/crm/`

### Render Tips

- **Free Tier:** Apps spin down after 15 min of inactivity (slow cold starts)
- **Paid Tier:** $7/month for always-on service
- **Auto-Deploy:** Enabled by default on git push
- **Logs:** Dashboard → Logs
- **Custom Domain:** Settings → Custom Domain

---

## Fly.io Deployment

Fly.io is Docker-native and offers excellent performance with global edge deployment.

### Step 1: Install Fly CLI

```bash
# Mac
brew install flyctl

# Linux
curl -L https://fly.io/install.sh | sh

# Windows
powershell -Command "iwr https://fly.io/install.ps1 -useb | iex"
```

### Step 2: Login to Fly

```bash
flyctl auth login
```

### Step 3: Create fly.toml

Create `fly.toml` in repository root:

```toml
app = "luca-command-center"

[build]
  dockerfile = "Dockerfile"

[env]
  PORT = "8000"
  DJANGO_SETTINGS_MODULE = "telis.settings_prod"

[http_service]
  internal_port = 8000
  force_https = true
  auto_stop_machines = true
  auto_start_machines = true
  min_machines_running = 0

[[mounts]]
  source = "luca_data"
  destination = "/app/telis_recruitment"

[[vm]]
  cpu_kind = "shared"
  cpus = 1
  memory_mb = 256
```

### Step 4: Create App

```bash
flyctl apps create luca-command-center
```

### Step 5: Create Volume

```bash
flyctl volumes create luca_data --region fra --size 1
```

### Step 6: Set Secrets

```bash
flyctl secrets set SECRET_KEY="your-secret-key"
flyctl secrets set DEBUG=False
flyctl secrets set ALLOWED_HOSTS="luca-command-center.fly.dev"
flyctl secrets set CSRF_TRUSTED_ORIGINS="https://luca-command-center.fly.dev"
```

### Step 7: Deploy

```bash
flyctl deploy
```

### Step 8: Run Initial Setup

```bash
flyctl ssh console
cd telis_recruitment
python manage.py migrate
python manage.py createsuperuser
exit
```

### Step 9: Access Your App

Available at: `https://luca-command-center.fly.dev/crm/`

### Fly.io Tips

- **Cost:** ~$3/month for minimal setup
- **Scaling:** Can scale to multiple regions
- **Logs:** `flyctl logs`
- **SSH:** `flyctl ssh console`
- **Custom Domain:** `flyctl certs add yourdomain.com`

---

## Hetzner VPS Deployment

For full control and best value, deploy to a Hetzner Cloud VPS.

### Step 1: Create Hetzner Account

1. Visit [hetzner.com/cloud](https://www.hetzner.com/cloud)
2. Create account and add payment method

### Step 2: Create Server

1. Choose location (Nuremberg, Helsinki, or Falkenstein for Europe)
2. Select "Ubuntu 22.04"
3. Server type: **CX11** (€4.15/month)
4. Add SSH key
5. Create server

### Step 3: Initial Server Setup

```bash
# SSH into server
ssh root@your-server-ip

# Update system
apt update && apt upgrade -y

# Install required packages
apt install -y python3 python3-pip python3-venv nginx certbot python3-certbot-nginx git curl

# Create app user
adduser --disabled-password --gecos "" luca
usermod -aG sudo luca
su - luca
```

### Step 4: Clone and Setup App

```bash
# Clone repository
git clone https://github.com/sundsoffice-tech/luca-nrw-scraper.git
cd luca-nrw-scraper

# Run install script
./install.sh

# Configure environment
nano .env
# Set production values (DEBUG=False, etc.)
```

### Step 5: Setup Gunicorn Service

Create `/etc/systemd/system/luca.service`:

```ini
[Unit]
Description=LUCA Command Center Gunicorn
After=network.target

[Service]
User=luca
Group=www-data
WorkingDirectory=/home/luca/luca-nrw-scraper/telis_recruitment
Environment="PATH=/home/luca/luca-nrw-scraper/venv/bin"
ExecStart=/home/luca/luca-nrw-scraper/venv/bin/gunicorn --workers 3 --bind unix:/home/luca/luca-nrw-scraper/luca.sock telis.wsgi:application

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl enable luca
sudo systemctl start luca
sudo systemctl status luca
```

### Step 6: Configure Nginx

Create `/etc/nginx/sites-available/luca`:

```nginx
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;

    client_max_body_size 50M;

    location = /favicon.ico { access_log off; log_not_found off; }
    
    location /static/ {
        alias /home/luca/luca-nrw-scraper/telis_recruitment/staticfiles/;
    }
    
    location /media/ {
        alias /home/luca/luca-nrw-scraper/telis_recruitment/media/;
    }

    location / {
        proxy_pass http://unix:/home/luca/luca-nrw-scraper/luca.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable site:

```bash
sudo ln -s /etc/nginx/sites-available/luca /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Step 7: Setup SSL with Let's Encrypt

```bash
sudo certbot --nginx -d your-domain.com -d www.your-domain.com
```

### Step 8: Update .env for Production

```bash
cd /home/luca/luca-nrw-scraper
nano .env
```

Update:
```bash
DEBUG=False
ALLOWED_HOSTS=your-domain.com,www.your-domain.com
CSRF_TRUSTED_ORIGINS=https://your-domain.com,https://www.your-domain.com
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_HSTS_SECONDS=31536000
```

Restart:
```bash
sudo systemctl restart luca
```

### Hetzner Tips

- **Cost:** €4.15/month for CX11
- **Backups:** Enable in Hetzner Cloud Console (+20% cost)
- **Firewall:** Configure in Hetzner dashboard (allow 80, 443, 22)
- **Updates:** `ssh luca@server && cd luca-nrw-scraper && git pull && ./install.sh && sudo systemctl restart luca`

---

## Custom Domain & SSL

### Railway

1. Settings → Domains
2. Add custom domain
3. Add CNAME record: `your-app.railway.app`
4. SSL automatically provisioned

### Render

1. Settings → Custom Domain
2. Add domain
3. Update DNS:
   - CNAME: `your-app.onrender.com`
4. SSL automatically provisioned

### Fly.io

```bash
flyctl certs add yourdomain.com
flyctl certs show yourdomain.com
# Add DNS records as shown
```

### Hetzner/VPS

Already covered in Step 7 of Hetzner deployment (Certbot).

---

## Database Backups

### Automated Backup Script

Create `/home/luca/backup-luca-db.sh` (Hetzner/VPS):

```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/home/luca/backups"
DB_PATH="/home/luca/luca-nrw-scraper/telis_recruitment/db.sqlite3"

mkdir -p $BACKUP_DIR

# Create backup
cp $DB_PATH "$BACKUP_DIR/db_$DATE.sqlite3"

# Compress
gzip "$BACKUP_DIR/db_$DATE.sqlite3"

# Keep only last 30 days
find $BACKUP_DIR -name "db_*.gz" -mtime +30 -delete

echo "Backup completed: db_$DATE.sqlite3.gz"
```

Make executable and add to cron:

```bash
chmod +x /home/luca/backup-luca-db.sh

# Add to crontab (daily at 2 AM)
crontab -e
# Add: 0 2 * * * /home/luca/backup-luca-db.sh
```

### Manual Backup

```bash
# Download from server
scp luca@server:/home/luca/luca-nrw-scraper/telis_recruitment/db.sqlite3 ./backup-$(date +%Y%m%d).sqlite3

# Docker
docker cp luca-command-center:/app/telis_recruitment/db.sqlite3 ./backup-$(date +%Y%m%d).sqlite3
```

### Restore Database

```bash
# Upload to server
scp ./backup.sqlite3 luca@server:/home/luca/luca-nrw-scraper/telis_recruitment/db.sqlite3

# Docker
docker cp ./backup.sqlite3 luca-command-center:/app/telis_recruitment/db.sqlite3
docker-compose restart web
```

---

## Monitoring

### Check Application Health

All platforms:
```bash
curl https://your-app.com/admin/login/
# Should return 200 OK
```

### View Logs

**Railway:** Dashboard → Deployments → Logs

**Render:** Dashboard → Logs

**Fly.io:**
```bash
flyctl logs
```

**Hetzner/VPS:**
```bash
# Application logs
sudo journalctl -u luca -f

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Setup Monitoring (Hetzner/VPS)

Install and configure basic monitoring:

```bash
# Install monitoring tools
apt install -y htop iotop

# Check resources
htop
df -h
free -m
```

---

## Support & Troubleshooting

### Common Issues

**1. Static files not loading:**
- Ensure `collectstatic` runs during build
- Check `STATIC_ROOT` in settings
- Verify Whitenoise is installed

**2. Database connection errors:**
- Check volume/disk is properly mounted
- Verify `db.sqlite3` has correct permissions

**3. 502 Bad Gateway:**
- Application not running or crashed
- Check logs for errors
- Verify gunicorn is binding correctly

**4. CSRF/CORS errors:**
- Update `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS`
- Include protocol (https://) in CSRF origins

### Get Help

- GitHub Issues: [Report a problem](https://github.com/sundsoffice-tech/luca-nrw-scraper/issues)
- Documentation: [Installation Guide](INSTALLATION.md)
- Check platform-specific docs:
  - [Railway Docs](https://docs.railway.app)
  - [Render Docs](https://render.com/docs)
  - [Fly.io Docs](https://fly.io/docs)

---

## Next Steps

- Set up automated backups
- Configure monitoring/alerts
- Setup CI/CD for automatic deployments
- Configure CDN for static files (optional)
- Set up log aggregation (optional)
- Consider PostgreSQL for larger datasets (optional)

---

**Note:** This guide focuses on SQLite deployments for simplicity. For high-traffic production use, consider migrating to PostgreSQL or MySQL.
