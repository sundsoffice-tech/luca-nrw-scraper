Zweck: NRW-Vertriebsleads automatisch finden, bewerten, exportieren.

## 🚀 Quick Start

### Scraper
```bash
# Single run with specific parameters
python scriptname.py --once --industry recruiter --qpi 6 --daterestrict d30

# Talent Hunt Mode (NEW - Find active sales professionals)
python scriptname.py --once --industry talent_hunt --qpi 15

# Start scraper with basic UI
python scriptname.py --ui
```

### 🎯 Django CRM (Recommended)
Professional Django-based CRM system for managing and processing leads from the LUCA NRW Scraper.

**Quick Start:**
```bash
cd telis_recruitment

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup database
python manage.py migrate
python manage.py createsuperuser

# Start the server
python manage.py runserver
```

**Access:**
- CRM Dashboard: http://127.0.0.1:8000/crm/
- Admin Interface: http://127.0.0.1:8000/admin/
- Scraper Control: http://127.0.0.1:8000/crm/scraper/ (Admin only)
- API Endpoints: http://127.0.0.1:8000/api/

**Features:**
- 📊 Real-time KPIs and statistics
- 🤖 Integrated scraper control panel (start/stop with live monitoring)
- 👥 Lead management with filtering and search
- 📈 Activity feed and team performance overview
- 📥 CSV/Excel export with advanced filters
- 🔐 Role-based permissions (Admin/Manager/Telefonist)

See [telis_recruitment/README.md](telis_recruitment/README.md) for detailed documentation.

> **Note:** The legacy Flask dashboard has been removed. All dashboard functionality is now available in the Django CRM.

## 📸 Screenshots

![Dashboard Main](https://github.com/user-attachments/assets/42f913bb-b1da-4b7e-b034-d352ef41bf65)
*Main dashboard with KPIs, charts, and live logs*

![Settings Page](https://github.com/user-attachments/assets/38823f05-d1f3-4fbe-af0a-65b4662e9ed8)
*Settings page for configuration management*
