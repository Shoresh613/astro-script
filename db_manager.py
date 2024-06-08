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
    print(f"DEBUG: get_event() name={name} guid={guid}")
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
