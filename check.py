import sqlite3
conn = sqlite3.connect('chatbot.db')
rows = conn.execute("SELECT id, question FROM faqs WHERE category='Driving License'").fetchall()
for r in rows:
    print(r)