Zweck: NRW-Vertriebsleads automatisch finden, bewerten, exportieren.

## 🚀 Quick Start

### Scraper
```bash
# Single run with specific parameters
python scriptname.py --once --industry recruiter --qpi 6 --daterestrict d30

# Start scraper with basic UI
python scriptname.py --ui
```

### 🎯 Dashboard (NEW!)
Professional control center for monitoring and managing the scraper:

```bash
# Start the LUCA Control Center dashboard
python3 -m dashboard.app
```

Then open http://127.0.0.1:5056 in your browser.

**Dashboard Features:**
- 📊 Real-time KPI tracking (leads, costs, success rate)
- 💰 API cost monitoring and budget management
- 📈 Interactive charts (lead history, top sources, cost trends)
- 🔍 5 search modes (Standard, Headhunter, Aggressive, Snippet Only, Learning)
- ⚙️ Configurable settings (budget, regions, filters)
- 📡 Live log streaming
- 📥 CSV export

See [dashboard/README.md](dashboard/README.md) for detailed documentation.

## 📸 Screenshots

![Dashboard Main](https://github.com/user-attachments/assets/42f913bb-b1da-4b7e-b034-d352ef41bf65)
*Main dashboard with KPIs, charts, and live logs*

![Settings Page](https://github.com/user-attachments/assets/38823f05-d1f3-4fbe-af0a-65b4662e9ed8)
*Settings page for configuration management*
