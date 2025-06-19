import sqlite3

conn = sqlite3.connect("db.sqlite3")
cursor = conn.cursor()

# Check what's stored for Mikael
cursor.execute(
    "SELECT name, location, latitude, longitude, altitude FROM myapp_event WHERE name = ?",
    ("Mikael",),
)
result = cursor.fetchone()

if result:
    print("Event data for Mikael:")
    print(f"Name: {result[0]}")
    print(f"Location: {result[1]}")
    print(f"Latitude: {result[2]}")
    print(f"Longitude: {result[3]}")
    print(f"Altitude: {result[4]}")
else:
    print("No event found for Mikael")

conn.close()
