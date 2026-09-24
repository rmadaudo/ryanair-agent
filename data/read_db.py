import sqlite3

conn = sqlite3.connect('./fares.db')
cur = conn.cursor()
cur.execute("SELECT * FROM daily_prices;")
print(cur.fetchall())
conn.close()