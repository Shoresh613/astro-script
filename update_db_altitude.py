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

# Function to ensure the 'id' column is the primary key
def ensure_primary_key(table_name):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check if the id column is the primary key
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()

    id_is_primary_key = any(col[1] == 'id' and col[5] == 1 for col in columns)
    
    if not id_is_primary_key:
        # Rename the existing table
        cursor.execute(f"ALTER TABLE {table_name} RENAME TO {table_name}_old;")
        
        # Recreate the table with 'id' as the primary key
        column_definitions = []
        for col in columns:
            if col[1] == 'id':
                column_definitions.append(f"{col[1]} {col[2]} PRIMARY KEY")
            else:
                column_definitions.append(f"{col[1]} {col[2]}")
        
        cursor.execute(f'''
            CREATE TABLE {table_name} (
                {", ".join(column_definitions)}
            );
        ''')

        # Copy data from the old table to the new table
        column_names = [col[1] for col in columns]
        cursor.execute(f'''
            INSERT INTO {table_name} ({", ".join(column_names)})
            SELECT {", ".join(column_names)}
            FROM {table_name}_old;
        ''')

        # Drop the old table
        cursor.execute(f"DROP TABLE {table_name}_old;")
        print(f"'id' column is now the primary key in '{table_name}' table.")
    else:
        print(f"'id' column is already the primary key in '{table_name}' table.")

    conn.commit()
    conn.close()

# Function to add the altitude column after the location column and populate it with values
def add_and_populate_altitude(table_name, location_column='location'):
    # Ensure 'id' is the primary key before proceeding
    ensure_primary_key(table_name)

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
