import sqlite3

# Path to your SQLite database file
db_path = 'db.sqlite3'

def add_column_via_table_recreation():
    # Connect to the SQLite database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Step 1: Create the new table with the additional column 'altitude'
    cursor.execute('''
    CREATE TABLE myapp_event_new AS
    SELECT
        id,
        location,
        datetime,
        timezone,
        latitude,
        longitude,
        NULL AS altitude,  -- Add the new column here
        notime,
        random_column,
        name
    FROM
        myapp_event
    WHERE
        1 = 0  -- Creates an empty table with the same structure
    ''')

    # Step 2: Copy data from the old table to the new table
    cursor.execute('''
    INSERT INTO myapp_event_new (id, location, datetime, timezone, latitude, longitude, altitude, notime, random_column, name)
    SELECT id, location, datetime, timezone, latitude, longitude, NULL, notime, random_column, name
    FROM myapp_event;
    ''')

    # Step 3: Drop the old table
    cursor.execute("DROP TABLE myapp_event")

    # Step 4: Rename the new table to the original table name
    cursor.execute("ALTER TABLE myapp_event_new RENAME TO myapp_event")

    # Commit the transaction and close the connection
    conn.commit()
    conn.close()

    print("Added 'altitude' column to 'myapp_event' table.")

# Execute the function to modify the table
add_column_via_table_recreation()
