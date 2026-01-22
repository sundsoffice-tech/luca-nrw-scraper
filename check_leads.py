import sqlite3
con = sqlite3.connect('scraper. db')
cur = con.cursor()

# Die 2 echten Leads anzeigen
print('=== ECHTE LEADS ===')
cur.execute("SELECT id, name, email, telefon, quelle, score FROM leads WHERE name != '_probe_'")
for row in cur.fetchall():
    print(row)

# Prüfe ob es eine Tabelle für failed/rejected leads gibt
print('\n=== ALLE TABELLEN ===')
cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
for t in cur.fetchall():
    print(t[0])

con.close()
