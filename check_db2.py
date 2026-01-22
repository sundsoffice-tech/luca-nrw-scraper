import sqlite3
con = sqlite3.connect('scraper. db')
cur = con.cursor()

# Echte Leads (nicht _probe_)
cur.execute("SELECT COUNT(*) FROM leads WHERE name != '_probe_' AND name IS NOT NULL")
print(f'Echte Leads: {cur. fetchone()[0]}')

# Leads mit Telefon
cur.execute("SELECT COUNT(*) FROM leads WHERE telefon IS NOT NULL AND telefon != ''")
print(f'Leads mit Telefon: {cur.fetchone()[0]}')

# URLs die gecrawlt wurden
cur.execute("SELECT COUNT(*) FROM urls_seen")
print(f'URLs gecrawlt: {cur.fetchone()[0]}')

# Portal Performance Daten
cur.execute("SELECT * FROM learning_portal_metrics ORDER BY total_runs DESC LIMIT 5")
cols = [d[0] for d in cur. description]
print('\nPortal Metrics:')
for row in cur.fetchall():
    print(dict(zip(cols, row)))
