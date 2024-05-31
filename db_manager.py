import sqlite3
from datetime import datetime

# Initialize the database and create tables if they don't exist
def initialize_db():
    conn = sqlite3.connect('events.db')
    cursor = conn.cursor()
    
    # Create the events table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS events (
        name TEXT PRIMARY KEY,
        location TEXT,
        datetime TEXT,
        timezone TEXT,
        latitude REAL,
        longitude REAL
    )
    ''')
    
    # Create the locations table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS locations (
        location_name TEXT PRIMARY KEY,
        latitude REAL,
        longitude REAL
    )
    ''')
    
    conn.commit()
    conn.close()

# Function to add or update an event in the database
def update_event(name, location, datetime_str, timezone, latitude, longitude):
    conn = sqlite3.connect('events.db')
    cursor = conn.cursor()
    
    cursor.execute('''
    INSERT INTO events (name, location, datetime, timezone, latitude, longitude)
    VALUES (?, ?, ?, ?, ?, ?)
    ON CONFLICT(name) DO UPDATE SET
    location=excluded.location,
    datetime=excluded.datetime,
    timezone=excluded.timezone,
    latitude=excluded.latitude,
    longitude=excluded.longitude
    ''', (name, location, datetime_str, timezone, latitude, longitude))
    
    conn.commit()
    conn.close()

# Function to retrieve an event by name
def get_event(name):
    conn = sqlite3.connect('events.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM events WHERE name = ?', (name,))
    event = cursor.fetchone()
    
    conn.close()
    return event

# Function to save a location in the database
def save_location(location_name, latitude, longitude):
    conn = sqlite3.connect('events.db')
    cursor = conn.cursor()
    
    cursor.execute('''
    INSERT INTO locations (location_name, latitude, longitude)
    VALUES (?, ?, ?)
    ON CONFLICT(location_name) DO UPDATE SET
    latitude=excluded.latitude,
    longitude=excluded.longitude
    ''', (location_name, latitude, longitude))
    
    conn.commit()
    conn.close()

# Function to load a location from the database
def load_location(location_name):
    conn = sqlite3.connect('events.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT latitude, longitude FROM locations WHERE location_name = ?', (location_name,))
    location = cursor.fetchone()
    
    conn.close()
    return location
