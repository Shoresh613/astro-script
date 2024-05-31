import sqlite3
from datetime import datetime

# Initialize the database and create tables if they don't exist
def initialize_db():
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    
    # Create the myapp_event table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS myapp_event (
        name TEXT PRIMARY KEY,
        location TEXT,
        datetime TEXT,
        timezone TEXT,
        latitude REAL,
        longitude REAL,
        random_column TEXT NULL
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
def update_event(name, location, datetime_str, timezone, latitude, longitude):
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    
    cursor.execute('''
    INSERT INTO myapp_event (name, location, datetime, timezone, latitude, longitude)
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
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM myapp_event WHERE name = ?', (name,))
    event = cursor.fetchone()
    
    conn.close()
    return event

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
