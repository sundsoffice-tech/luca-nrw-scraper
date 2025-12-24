import sqlite3

conn = sqlite3.connect('scraper.db')
c = conn.cursor()

print("=== LEADS MIT TELEFON ===")
c.execute("SELECT COUNT(*) FROM leads WHERE telefon IS NOT NULL AND telefon != ''")
print(f"Mit Telefon: {c. fetchone()[0]}")

c.execute("SELECT COUNT(*) FROM leads WHERE telefon IS NULL OR telefon = ''")
print(f"Ohne Telefon: {c.fetchone()[0]}")

print("\n=== LETZTE 15 LEADS ===")
c.execute("SELECT name, telefon, substr(quelle,1,60) FROM leads ORDER BY id DESC LIMIT 15")
for r in c.fetchall():
    name = str(r[0])[: 30] if r[0] else "UNBEKANNT"
    phone = str(r[1]) if r[1] else "KEINE"
    source = str(r[2]) if r[2] else ""
    print(f"{name} | {phone} | {source}")

print("\n=== QUELLEN-STATISTIK ===")
c.execute('''
    SELECT 
        CASE 
            WHEN quelle LIKE '%kleinanzeigen%' THEN 'Kleinanzeigen'
            WHEN quelle LIKE '%markt. de%' THEN 'Markt.de'
            WHEN quelle LIKE '%quoka%' THEN 'Quoka'
            WHEN quelle LIKE '%kalaydo%' THEN 'Kalaydo'
            WHEN quelle LIKE '%meinestadt%' THEN 'Meinestadt'
            WHEN quelle LIKE '%xing%' THEN 'XING'
            WHEN quelle LIKE '%linkedin%' THEN 'LinkedIn'
            ELSE 'Andere'
        END as source,
        COUNT(*) as count
    FROM leads 
    GROUP BY source 
    ORDER BY count DESC
''')
for r in c.fetchall():
    print(f"{r[0]}: {r[1]}")

print("\n=== PHONE TYPE ===")
c.execute("SELECT phone_type, COUNT(*) FROM leads GROUP BY phone_type")
for r in c.fetchall():
    ptype = r[0] if r[0] else "unbekannt"
    print(f"{ptype}: {r[1]}")

print("\n=== BEISPIEL TELEFONNUMMERN ===")
c.execute("SELECT telefon FROM leads WHERE telefon IS NOT NULL AND telefon != '' LIMIT 10")
for r in c.fetchall():
    print(r[0])

conn.close()
