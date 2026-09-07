import sqlite3

conn = sqlite3.connect("db/ip_sakti.db")
cursor = conn.cursor()

cursor.execute("SELECT doc_id, source_id, source_url FROM documents")
rows = cursor.fetchall()

print("SQLite db/ip_sakti.db documents table:")
for r in rows:
    print(f"Doc ID: {r[0]} | Source ID: {r[1]} | Source URL: {r[2]}")

conn.close()
