import sqlite3

def make_id_primary_key(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check if the table already exists and the id column is already a primary key
    cursor.execute("PRAGMA table_info(myapp_event);")
    columns = cursor.fetchall()
    
    id_is_primary_key = any(col[1] == 'id' and col[5] == 1 for col in columns)
    
    if id_is_primary_key:
        print("The 'id' column is already a primary key.")
        conn.close()
        return

    # Rename the existing table
    cursor.execute("ALTER TABLE myapp_event RENAME TO myapp_event_old;")
    
    # Recreate the table with 'id' as the primary key
    cursor.execute('''
        CREATE TABLE myapp_event (
            id INTEGER PRIMARY KEY,
            location TEXT,
            datetime TEXT,
            timezone TEXT,
            latitude REAL,
            longitude REAL,
            altitude REAL,
            notime INTEGER,
            name TEXT
        );
    ''')

    # Copy the data from the old table to the new table
    cursor.execute('''
        INSERT INTO myapp_event (id, location, datetime, timezone, latitude, longitude, altitude, notime, name)
        SELECT id, location, datetime, timezone, latitude, longitude, altitude, notime, name
        FROM myapp_event_old;
    ''')

    # Drop the old table
    cursor.execute("DROP TABLE myapp_event_old;")

    # Commit the changes and close the connection
    conn.commit()
    conn.close()

    print("The 'id' column has been set as the primary key.")

# Usage
db_path = 'db.sqlite3'  # Replace with your actual database path
make_id_primary_key(db_path)
