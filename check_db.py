import sqlite3
con = sqlite3.connect('scraper.db')
cur = con.cursor()

# Alle Tabellen
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
print('Tabellen:', [t[0] for t in cur.fetchall()])

# Leads zaehlen
cur.execute('SELECT COUNT(*) FROM leads')
print(f'Leads gesamt: {cur.fetchone()[0]}')

# Letzte 5 Leads
cur.execute('SELECT * FROM leads ORDER BY id DESC LIMIT 5')
cols = [d[0] for d in cur. description]
print('Spalten:', cols)
for row in cur.fetchall():
    print(dict(zip(cols, row)))
