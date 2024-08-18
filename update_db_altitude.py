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

# Function to add the altitude column after the location column and populate it with values
def add_and_populate_altitude(table_name, location_column='location'):
    # Connect to the SQLite database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Step 1: Get existing columns
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    column_names = [column[1] for column in columns]

    # Step 2: Determine the position of the location column
    location_index = column_names.index(location_column) + 1

    # Step 3: Reorder columns with altitude after the location column
    column_names.insert(location_index, 'altitude')
    column_definitions = [f"{col} {columns[column_names.index(col)][2]}" if col != 'altitude' else 'altitude REAL' for col in column_names]

    # Step 4: Create a new table with the altitude column in the desired position
    cursor.execute(f'''
    CREATE TABLE {table_name}_new (
        {", ".join(column_definitions)}
    )
    ''')

    # Step 5: Copy existing data to the new table
    existing_columns = [col for col in column_names if col != 'altitude']
    cursor.execute(f'''
    INSERT INTO {table_name}_new ({", ".join(existing_columns)}, altitude)
    SELECT {", ".join(existing_columns)}, NULL
    FROM {table_name};
    ''')

    # Step 6: Drop the old table and rename the new table to the original name
    cursor.execute(f"DROP TABLE {table_name}")
    cursor.execute(f"ALTER TABLE {table_name}_new RENAME TO {table_name}")

    # Commit the transaction
    conn.commit()

    # Step 7: Populate the altitude column with valid values
    cursor.execute(f"SELECT ROWID, latitude, longitude FROM {table_name} WHERE altitude IS NULL")
    rows = cursor.fetchall()

    for row in rows:
        rowid, latitude, longitude = row
        altitude = get_altitude(latitude, longitude)

        if altitude is not None:
            cursor.execute(f"UPDATE {table_name} SET altitude = ? WHERE ROWID = ?", (altitude, rowid))
            print(f"Updated {table_name} ROWID {rowid} with altitude {altitude} meters")

    # Commit the changes and close the connection
    conn.commit()
    conn.close()

    print(f"Altitude column added and populated in '{table_name}' table.")

# Execute the function for both tables
add_and_populate_altitude('myapp_event')
add_and_populate_altitude('myapp_location')
