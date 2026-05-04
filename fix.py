from database import get_conn

conn = get_conn()

# Show all driving license FAQs
rows = conn.execute(
    "SELECT id, question FROM faqs WHERE category='Driving License'"
).fetchall()

print("Driving License FAQs:")
for r in rows:
    print(r[0], r[1][:60])

# Delete wrong duplicate
conn.execute("DELETE FROM faqs WHERE id = 14")
conn.commit()
print("\nDeleted ID 14!")
conn.close()