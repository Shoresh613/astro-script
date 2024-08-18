import requests
import sqlite3

# Path to your SQLite database file
db_path = 'db.sqlite3'

# Function to get altitude from the Open-Elevation API
def get_altitude(lat, lon):
    try:
        url = f'https://api.open-elevation.com/api/v1/lookup?locations={lat},{lon}'
        response = requests.get(url)
        results = response.json()['results']
        if results:
            return results[0]['elevation']
        return None
    except Exception as e:
        print(f"Error getting altitude: {e}")
        return None

# Connect to the SQLite database
connection = sqlite3.connect(db_path)
cursor = connection.cursor()

# Fetch rows that need altitude values
cursor.execute("SELECT id, latitude, longitude FROM myapp_event WHERE altitude IS NULL")
rows = cursor.fetchall()

# Update the altitude for each row
for row in rows:
    id, latitude, longitude = row
    altitude = get_altitude(latitude, longitude)
    
    if altitude is not None:
        cursor.execute("UPDATE myapp_event SET altitude = ? WHERE id = ?", (altitude, id))
        print(f"Updated id {id} with altitude {altitude} meters")

# Commit changes and close the connection
connection.commit()
cursor.close()
connection.close()

print("Altitude update completed.")
