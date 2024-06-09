import sqlite3
from datetime import datetime

# Initialize the database and create tables if they don't exist
def initialize_db():
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    
    # Create the myapp_event table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS myapp_event (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        location TEXT,
        datetime TEXT,
        timezone TEXT,
        latitude REAL,
        longitude REAL,
        random_column TEXT NULL,
        name TEXT NOT NULL
    )
    ''')
    
    # Create the myapp_location table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS myapp_location (
        location_name TEXT PRIMARY KEY,
        latitude REAL,
        longitude REAL
    )
    ''')
    
    conn.commit()
    conn.close()

# Function to add or update an event in the database
def update_event(name, location, datetime_str, timezone, latitude, longitude, guid):
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    
    #only for debug
    print(f"name={name} location={location} datetime_str={datetime_str} timezone={timezone} latitude={latitude} longitude= {longitude} guid={guid}")    
    
    if guid:
        cursor.execute('''
        
        INSERT INTO myapp_event (location, datetime, timezone, latitude, longitude, random_column, name)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
        location=excluded.location,
        datetime=excluded.datetime,
        timezone=excluded.timezone,
        latitude=excluded.latitude,
        longitude=excluded.longitude,
        random_column=excluded.guid,
        name=excluded.name
        ''', (location, datetime_str, timezone, latitude, longitude, str(guid), name))
    else:
        cursor.execute('''
        
        INSERT INTO myapp_event (location, datetime, timezone, latitude, longitude, name)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
        location=excluded.location,
        datetime=excluded.datetime,
        timezone=excluded.timezone,
        latitude=excluded.latitude,
        longitude=excluded.longitude,
        name=excluded.name
        ''', (location, datetime_str, timezone, latitude, longitude, name))

    conn.commit()
    conn.close()

# Function to retrieve an event by name
def get_event(name, guid=None):
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    # print(f"DEBUG: get_event() name={name} guid={guid}")
    if guid:
        cursor.execute('SELECT location FROM myapp_event WHERE name = ? AND random_column = ?', (name, guid,))
        location = cursor.fetchone()
        cursor.execute('SELECT datetime FROM myapp_event WHERE name = ? AND random_column = ?', (name, guid,))
        datetime = cursor.fetchone()
        cursor.execute('SELECT timezone FROM myapp_event WHERE name = ? AND random_column = ?', (name, guid,))
        timezone = cursor.fetchone()
        cursor.execute('SELECT latitude FROM myapp_event WHERE name = ? AND random_column = ?', (name, guid,))
        latitude = cursor.fetchone()
        cursor.execute('SELECT longitude FROM myapp_event WHERE name = ? AND random_column = ?', (name, guid,))
        longitude = cursor.fetchone()
    else:
        cursor.execute('SELECT location FROM myapp_event WHERE name = ?', (name,))
        location = cursor.fetchone()
        cursor.execute('SELECT datetime FROM myapp_event WHERE name = ?', (name,))
        datetime = cursor.fetchone()
        cursor.execute('SELECT timezone FROM myapp_event WHERE name = ?', (name,))
        timezone = cursor.fetchone()
        cursor.execute('SELECT latitude FROM myapp_event WHERE name = ?', (name,))
        latitude = cursor.fetchone()
        cursor.execute('SELECT longitude FROM myapp_event WHERE name = ?', (name,))
        longitude = cursor.fetchone()

    conn.close()

    if datetime:
        event = {
            'name': name,
            'location': location[0],
            'datetime': datetime[0],
            'timezone': timezone[0],
            'latitude': latitude[0],
            'longitude': longitude[0]
        }
        return event
    else:
        return None


def read_saved_names(guid=None, db_filename='db.sqlite3'):
    """
    Reads the names of saved events from a SQLite database and returns a list of event names.
    Checks if the user is authenticated before proceeding.

    Args:
    guid (uuid): .
    db_filename (str): The path to the SQLite database file.

    Returns:
    list: A list of names of saved events, or an empty list if the user is not authenticated.
    """
    # print(f"DEBUG - guid: {str(guid)}")
    try:
        
        # Connect to the SQLite database
        conn = sqlite3.connect(db_filename)
        cursor = conn.cursor()
        
        # Execute a query to retrieve the names of the events
        if guid:
            print(f"DEBUG - read_saved_names() guid: {guid}")
            cursor.execute(f"SELECT name FROM myapp_event WHERE random_column=?", (guid, ))
        else:
            cursor.execute("SELECT name FROM myapp_event")
        rows = cursor.fetchall()
        
        # Extract the names from the query result
        names = [row[0] for row in rows]
        
        # Close the database connection
        conn.close()
        
        return names
    except sqlite3.OperationalError as e:
        # Handle operational errors such as missing tables or database files
        print(f"Database error: {e}")
        return []
    except Exception as e:
        # General exception handling, useful for debugging
        print(f"An unexpected error occurred: {e}")
        return []

import sqlite3

def remove_saved_names(names_to_remove, output_type, guid=None, db_filename='db.sqlite3'):
    """
    Removes the specified names of saved events from a SQLite database.
    Checks if the user is authenticated before proceeding.

    Args:
    names_to_remove (list of str): The names of the saved events to remove.
    output_type (str): The type of output expected (e.g., 'json', 'text').
    guid (uuid, optional): The user's GUID. Defaults to None.
    db_filename (str): The path to the SQLite database file. Defaults to 'db.sqlite3'.

    Returns:
    str: A string message indicating the result of the removal operation.
    """
    existing_names = set(read_saved_names(guid, db_filename))
    names_to_remove = set(names_to_remove)

    # Check if the names to remove are valid
    invalid_names = names_to_remove - existing_names
    valid_names = names_to_remove - invalid_names

    invalid_names = list(invalid_names)
    valid_names = list(valid_names)

    if valid_names:
        try:
            # Connect to the SQLite database
            conn = sqlite3.connect(db_filename)
            cursor = conn.cursor()

            # If guid is provided, ensure the removal operation is scoped to the specific user
            if guid:
                cursor.execute("DELETE FROM myapp_event WHERE name IN ({}) AND random_column=?".format(
                    ','.join('?' * len(valid_names))), (*valid_names, guid))
            else:
                cursor.execute("DELETE FROM myapp_event WHERE name IN ({})".format(
                    ','.join('?' * len(valid_names))), valid_names)

            # Commit the transaction
            conn.commit()
            
            # Close the database connection
            conn.close()

        except sqlite3.OperationalError as e:
            # Handle operational errors such as missing tables or database files
            print(f"Database error: {e}")
            return f"Database error: {e}"
        except Exception as e:
            # General exception handling, useful for debugging
            print(f"An unexpected error occurred: {e}")
            return f"An unexpected error occurred: {e}"

    # Prepare the result message based on the output type
    to_return = ""
    if output_type in ('text', 'html'):
        if invalid_names:
            print(f"\nThe following names are not saved events: {', '.join(invalid_names)}.\n")
        if valid_names:
            print(f"\nThe following names have been removed: {', '.join(valid_names)}.\n")
    else:
        if invalid_names:
            to_return += f"\nThe following names are not saved events: {', '.join(invalid_names)}.\n"
        if valid_names:
            to_return += f"\nThe following names have been removed: {', '.join(valid_names)}.\n"

    return to_return

# Function to save a location in the database
def save_location(location_name, latitude, longitude):
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    
    cursor.execute('''
    INSERT INTO myapp_location (location_name, latitude, longitude)
    VALUES (?, ?, ?)
    ON CONFLICT(location_name) DO UPDATE SET
    latitude=excluded.latitude,
    longitude=excluded.longitude
    ''', (location_name, latitude, longitude))
    
    conn.commit()
    conn.close()

# Function to load a location from the database
def load_location(location_name):
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    
    cursor.execute('SELECT latitude, longitude FROM myapp_location WHERE location_name = ?', (location_name,))
    location = cursor.fetchone()
    
    conn.close()
    return location
