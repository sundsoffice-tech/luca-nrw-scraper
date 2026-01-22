import sqlite3
con = sqlite3.connect('scraper.db')
cur = con.cursor()

print('=== LEADS NACH DEM RUN ===')
cur.execute("SELECT COUNT(*) FROM leads WHERE name != '_probe_'")
print(f'Echte Leads: {cur.fetchone()[0]}')

cur.execute("SELECT id, name, telefon, quelle FROM leads WHERE name != '_probe_' ORDER BY id DESC LIMIT 10")
for row in cur.fetchall():
    print(row)

con.close()
