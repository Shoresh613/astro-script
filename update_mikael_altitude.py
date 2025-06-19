import sqlite3

# Update the Mikael event with the correct altitude
conn = sqlite3.connect("db.sqlite3")
cursor = conn.cursor()

# Update the altitude for Mikael
cursor.execute("UPDATE myapp_event SET altitude = ? WHERE name = ?", (45.0, "Mikael"))

print(f"Updated {cursor.rowcount} row(s)")

# Verify the update
cursor.execute(
    "SELECT name, location, latitude, longitude, altitude FROM myapp_event WHERE name = ?",
    ("Mikael",),
)
result = cursor.fetchone()

if result:
    print("Updated Mikael event:")
    print(f"Name: {result[0]}")
    print(f"Location: {result[1]}")
    print(f"Latitude: {result[2]}")
    print(f"Longitude: {result[3]}")
    print(f"Altitude: {result[4]}")
else:
    print("No event found for Mikael")

conn.commit()
conn.close()
