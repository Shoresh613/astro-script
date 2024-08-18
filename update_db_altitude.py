import sqlite3
import requests

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

# Function to add the altitude column to a table and populate it with values
def add_and_populate_altitude(table_name):
    # Connect to the SQLite database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Step 1: Add the altitude column by creating a new table and copying data
    cursor.execute(f'''
    CREATE TABLE {table_name}_new AS
    SELECT
        *,
        NULL AS altitude  -- Add the new column here
    FROM
        {table_name}
    WHERE
        1 = 0  -- Creates an empty table with the same structure
    ''')

    # Copy existing data into the new table
    columns = cursor.execute(f"PRAGMA table_info({table_name})").fetchall()
    column_names = [column[1] for column in columns]
    cursor.execute(f'''
    INSERT INTO {table_name}_new ({", ".join(column_names)}, altitude)
    SELECT {", ".join(column_names)}, NULL
    FROM {table_name};
    ''')

    # Drop the old table and rename the new one
    cursor.execute(f"DROP TABLE {table_name}")
    cursor.execute(f"ALTER TABLE {table_name}_new RENAME TO {table_name}")

    # Commit the transaction
    conn.commit()

    # Step 2: Populate the altitude column with valid values
    cursor.execute(f"SELECT id, latitude, longitude FROM {table_name} WHERE altitude IS NULL")
    rows = cursor.fetchall()

    for row in rows:
        id, latitude, longitude = row
        altitude = get_altitude(latitude, longitude)

        if altitude is not None:
            cursor.execute(f"UPDATE {table_name} SET altitude = ? WHERE id = ?", (altitude, id))
            print(f"Updated {table_name} id {id} with altitude {altitude} meters")

    # Commit the changes and close the connection
    conn.commit()
    conn.close()

    print(f"Altitude column added and populated in '{table_name}' table.")

# Execute the function for both tables
add_and_populate_altitude('myapp_event')
add_and_populate_altitude('myapp_location')
