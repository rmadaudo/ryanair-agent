import sqlite3

conn = sqlite3.connect('./fares.db')
cur = conn.cursor()
cur.execute("DELETE FROM daily_prices;")
print(conn.commit())
conn.close()
