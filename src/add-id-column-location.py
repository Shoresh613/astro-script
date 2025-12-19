import sqlite3

# Path to your SQLite database file
db_path = 'db.sqlite3'

def add_id_column(table_name):
    # Connect to the SQLite database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Step 1: Create a new table with an id column as the first column
    cursor.execute(f'''
    CREATE TABLE {table_name}_new (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        location_name TEXT,
        latitude REAL,
        longitude REAL,
        altitude REAL
    )
    ''')

    # Step 2: Copy data from the old table to the new table
    cursor.execute(f'''
    INSERT INTO {table_name}_new (location_name, latitude, longitude, altitude)
    SELECT location_name, latitude, longitude, altitude
    FROM {table_name};
    ''')

    # Step 3: Drop the old table
    cursor.execute(f"DROP TABLE {table_name}")

    # Step 4: Rename the new table to the original table name
    cursor.execute(f"ALTER TABLE {table_name}_new RENAME TO {table_name}")

    # Commit the transaction and close the connection
    conn.commit()
    conn.close()

    print(f"'id' column added and populated in '{table_name}' table.")

# Execute the function for the myapp_location table
add_id_column('myapp_location')