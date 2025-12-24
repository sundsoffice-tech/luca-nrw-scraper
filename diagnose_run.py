import subprocess
import time
import json
import sqlite3
from datetime import datetime
from pathlib import Path

print("=" * 70)
print("DIAGNOSE-RUN GESTARTET - 30 MINUTEN VOLLGAS")
print(f"Start: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 70)

start_time = time.time()
duration_seconds = 30 * 60  # 30 Minuten

metrics = {
    "start":  datetime.now().isoformat(),
    "runs": 0,
    "total_leads_saved": 0,
    "errors": [],
    "warnings": [],
    "skipped_portals": {},
    "skipped_queries": 0,
    "http_errors": {"403": 0, "429": 0, "5xx": 0, "timeout": 0},
    "portal_results": {},
    "rejected_leads": [],
}

log_file = Path("diagnose_run.log")
log_file.write_text("")

def parse_log_line(line):
    global metrics
    
    if "[LEARNING] Skipping" in line:
        portal = line.split("Skipping")[1].split("(")[0].strip()
        metrics["skipped_portals"][portal] = metrics["skipped_portals"].get(portal, 0) + 1
    
    if "Query bereits erledigt (skip)" in line:
        metrics["skipped_queries"] += 1
    
    if "status" in line. lower() or "error" in line.lower():
        if "403" in line: 
            metrics["http_errors"]["403"] += 1
        if "429" in line:
            metrics["http_errors"]["429"] += 1
        if "500" in line or "502" in line or "503" in line:
            metrics["http_errors"]["5xx"] += 1
    
    if "timeout" in line.lower():
        metrics["http_errors"]["timeout"] += 1
    
    if "Leads extrahiert" in line or "crawl complete" in line:
        for p in ["Kleinanzeigen", "Quoka", "Markt", "DHD24", "Freelancermap", "Freelance"]:
            if p.lower() in line.lower():
                try:
                    if '"count": ' in line:
                        count = int(line.split('"count":')[1].split("}")[0].split(",")[0].strip())
                        metrics["portal_results"][p] = metrics["portal_results"].get(p, 0) + count
                except:
                    pass
    
    if "Lead abgelehnt" in line:
        metrics["rejected_leads"].append(line. strip()[:100])
    
    if "[ERROR" in line or "[FATAL" in line: 
        metrics["errors"].append(line.strip()[:150])
    
    if "[WARN" in line:
        metrics["warnings"]. append(line.strip()[:150])
    
    if "Run #" in line and "gestartet" in line:
        metrics["runs"] += 1
    
    if "neue Leads gespeichert" in line: 
        try:
            count = int(line.split('"count": ')[1].split("}")[0].split(",")[0].strip())
            metrics["total_leads_saved"] += count
        except: 
            pass

print("\nStarte Scraper-Loop fuer 30 Minuten.. .\n")

try:
    run_number = 0
    while time.time() - start_time < duration_seconds:
        run_number += 1
        elapsed_min = int((time.time() - start_time) / 60)
        remaining_min = 30 - elapsed_min
        
        print(f"\n{'='*60}")
        print(f"DIAGNOSE RUN #{run_number} | {elapsed_min} Min vergangen | {remaining_min} Min uebrig")
        print(f"{'='*60}\n")
        
        process = subprocess.Popen(
            ["python", "scriptname. py", "--once", "--industry", "candidates", "--qpi", "25", "--smart"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            if line: 
                print(line, end="")
                parse_log_line(line)
                with open(log_file, "a", encoding="utf-8") as f:
                    f.write(line)
        
        process.wait()
        
        # Status zwischen Runs
        print(f"\n--- Run #{run_number} beendet ---")
        print(f"    Leads bisher: {metrics['total_leads_saved']}")
        print(f"    Errors bisher: {len(metrics['errors'])}")
        print(f"    Skipped Queries:  {metrics['skipped_queries']}")
        
        if time.time() - start_time < duration_seconds:
            print("\n--- Pause 15 Sek vor naechstem Run ---\n")
            time.sleep(15)

except KeyboardInterrupt:
    print("\n\nManuell abgebrochen!")

metrics["end"] = datetime.now().isoformat()
metrics["duration_minutes"] = round((time. time() - start_time) / 60, 1)
metrics["total_runs"] = run_number

try: 
    conn = sqlite3.connect("scraper.db")
    metrics["db_total_leads"] = conn.execute("SELECT COUNT(*) FROM leads").fetchone()[0]
    metrics["db_today_leads"] = conn.execute(
        "SELECT COUNT(*) FROM leads WHERE date(scraped_at) = date('now')"
    ).fetchone()[0]
    metrics["db_unique_sources"] = conn.execute(
        "SELECT COUNT(DISTINCT source_url) FROM leads"
    ).fetchone()[0]
    conn.close()
except Exception as e: 
    metrics["db_error"] = str(e)

# ============================================
# REPORT
# ============================================
print("\n\n")
print("=" * 70)
print("DIAGNOSE-REPORT NACH 30 MINUTEN")
print("=" * 70)

print(f"""
============ LAUFZEIT ============
  Gesamtdauer: {metrics['duration_minutes']} Minuten
  Anzahl Runs: {metrics['total_runs']}
  Start: {metrics['start']}
  Ende: {metrics['end']}

============ LEADS ============
  Neu gespeichert: {metrics['total_leads_saved']}
  Abgelehnt: {len(metrics['rejected_leads'])}
  In DB gesamt: {metrics. get('db_total_leads', 'N/A')}
  Heute neu: {metrics. get('db_today_leads', 'N/A')}
  Unique Sources: {metrics. get('db_unique_sources', 'N/A')}

============ PORTAL-ERGEBNISSE ============""")

if metrics['portal_results']:
    for portal, count in sorted(metrics['portal_results'].items(), key=lambda x: -x[1]):
        status = "[OK]" if count > 0 else "[FAIL]"
        print(f"  {status} {portal}: {count} Leads")
else:
    print("  Keine Portal-Daten gesammelt")

print("\n============ GESKIPPTE PORTALE ============")
if metrics['skipped_portals']:
    for portal, count in metrics['skipped_portals']. items():
        print(f"  [SKIP] {portal}: {count}x geskippt")
else:
    print("  Keine Portale geskippt - SUPER!")

print(f"""
============ QUERIES ============
  Geskippt (Cache): {metrics['skipped_queries']}
  
============ HTTP-FEHLER ============
  403 (Forbidden/Blocked): {metrics['http_errors']['403']}
  429 (Rate Limit): {metrics['http_errors']['429']}
  5xx (Server Error): {metrics['http_errors']['5xx']}
  Timeout: {metrics['http_errors']['timeout']}

============ ERRORS ({len(metrics['errors'])} total) ============""")

error_counts = {}
for err in metrics['errors']:
    key = err[: 60]
    error_counts[key] = error_counts.get(key, 0) + 1

for err, count in sorted(error_counts.items(), key=lambda x: -x[1])[:10]:
    print(f"  [{count}x] {err}...")

print(f"\n============ WARNINGS ({len(metrics['warnings'])} total) ============")

warning_counts = {}
for w in metrics['warnings']:
    key = w[:60]
    warning_counts[key] = warning_counts.get(key, 0) + 1

for w, count in sorted(warning_counts. items(), key=lambda x: -x[1])[:10]:
    print(f"  [{count}x] {w}...")

print("\n============ ABGELEHNTE LEADS ============")
rejection_reasons = {}
for r in metrics['rejected_leads']: 
    key = r[:50]
    rejection_reasons[key] = rejection_reasons.get(key, 0) + 1

if rejection_reasons:
    for reason, count in sorted(rejection_reasons.items(), key=lambda x: -x[1])[:10]:
        print(f"  [{count}x] {reason}...")
else:
    print("  Keine Leads abgelehnt")

print("\n" + "=" * 70)
print("HANDLUNGSEMPFEHLUNGEN")
print("=" * 70)

recommendations = []

if metrics['skipped_portals']: 
    recommendations.append("HOCH: Portal-Skipping Logik fixen - Portale werden zu frueh deaktiviert")

if metrics['skipped_queries'] > metrics['total_runs'] * 10:
    recommendations.append("HOCH: Query-Cache zuruecksetzen - zu viele Queries werden geskippt")

if metrics['http_errors']['403'] > 5:
    recommendations.append("MITTEL: VPN einrichten fuer geblockte Seiten (403 Errors)")

if metrics['http_errors']['429'] > 5:
    recommendations.append("MITTEL: Rate-Limiting erhoehen - zu viele 429 Errors")

if metrics['http_errors']['timeout'] > 10:
    recommendations.append("MITTEL: Timeout-Werte erhoehen oder Netzwerk pruefen")

if len(metrics['rejected_leads']) > metrics['total_leads_saved'] * 2:
    recommendations.append("MITTEL: Lead-Validierung lockern - zu viele Ablehnungen")

if metrics['total_leads_saved'] == 0 and metrics['total_runs'] > 2:
    recommendations.append("KRITISCH: Keine Leads gespeichert trotz mehrerer Runs!")

if not metrics['portal_results']:
    recommendations.append("KRITISCH: Keine Portal-Ergebnisse - Crawler funktioniert nicht")

if not recommendations:
    recommendations.append("System laeuft gut!  Weiter beobachten.")

for i, rec in enumerate(recommendations, 1):
    print(f"  {i}. {rec}")

# Report speichern
report_file = Path(f"diagnose_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
with open(report_file, "w", encoding="utf-8") as f:
    json.dump(metrics, f, indent=2, ensure_ascii=False)

print(f"\n{'='*70}")
print(f"Report gespeichert: {report_file}")
print(f"Log-Datei: {log_file}")
print(f"{'='*70}")