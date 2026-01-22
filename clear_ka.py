import sqlite3
con = sqlite3.connect('scraper.db')
cur = con.cursor()

# Nur Kleinanzeigen URLs loeschen fuer Test
cur.execute("DELETE FROM urls_seen WHERE url LIKE '%kleinanzeigen%'")
deleted = cur.rowcount
con.commit()
print(f'Kleinanzeigen URLs geloescht: {deleted}')

con.close()
