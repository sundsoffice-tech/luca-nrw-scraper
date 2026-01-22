import sqlite3

con = sqlite3.connect('scraper.db')
cur = con.cursor()

print('=== PORTAL METRICS SUMME ===')
cur.execute('SELECT portal, SUM(leads_found), SUM(leads_with_phone) FROM learning_portal_metrics GROUP BY portal')
for row in cur.fetchall():
    print(f'{row[0]}: {row[1]} gefunden, {row[2]} mit Telefon')

print('\n=== RUNS TABELLE ===')
cur.execute('SELECT COUNT(*) FROM runs')
print(f'Anzahl Runs: {cur.fetchone()[0]}')

cur.execute('SELECT id, status, leads_found FROM runs ORDER BY id DESC LIMIT 5')
cols = [d[0] for d in cur.description]
for row in cur.fetchall():
    print(dict(zip(cols, row)))

con.close()
