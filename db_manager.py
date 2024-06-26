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
        notime INTEGER DEFAULT FALSE,
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

    # Create the myapp_defaults table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS myapp_defaults (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        setting_name TEXT NOT NULL,
        guid TEXT NULL,
        location TEXT NULL,
        timezone TEXT NULL,
        imprecise_aspects TEXT NULL,
        minor_aspects BOOLEAN NULL,
        show_brief_aspects BOOLEAN NULL,
        show_score BOOLEAN NULL,
        orb_major FLOAT NULL,
        orb_minor FLOAT NULL,
        orb_fixed_star FLOAT NULL,
        orb_transit_fast FLOAT NULL,
        orb_transit_slow FLOAT NULL,
        orb_synastry_fast FLOAT NULL,
        orb_synastry_slow FLOAT NULL,
        degree_in_minutes BOOLEAN NULL,
        node TEXT NULL,
        all_stars BOOLEAN NULL,
        house_system TEXT NULL,
        house_cusps BOOLEAN NULL,
        hide_planetary_positions BOOLEAN NULL,
        hide_planetary_aspects BOOLEAN NULL,
        hide_fixed_star_aspects BOOLEAN NULL,
        hide_asteroid_aspects BOOLEAN NULL,
        transits_timezone TEXT NULL,
        transits_location TEXT NULL,
        output_type TEXT NULL
    )
    ''')

    conn.commit()
    conn.close()

# Function to add or update an event in the database
def update_event(name, location, datetime_str, timezone, latitude, longitude, notime, guid):
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    
    #only for debug
    print(f"name={name} location={location} datetime_str={datetime_str} timezone={timezone} latitude={latitude} longitude= {longitude} guid={guid}")    
    result = get_event(name, guid)
    if result:
        print(f"DEBUG: get_event() result{result}")
        cursor.execute('''
        UPDATE myapp_event
        SET location = ?,
            datetime = ?,
            timezone = ?,
            latitude = ?,
            longitude = ?,
            notime = ?,
            random_column = ?
        WHERE name = ? AND random_column = ?
        ''', (location, datetime_str, timezone, latitude, longitude, notime, str(guid), name, str(guid)))
    else:
        if guid:
            cursor.execute('''
            
            INSERT INTO myapp_event (location, datetime, timezone, latitude, longitude, notime, random_column, name)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
            location=excluded.location,
            datetime=excluded.datetime,
            timezone=excluded.timezone,
            latitude=excluded.latitude,
            longitude=excluded.longitude,
            notime=excluded.notime,
            random_column=excluded.guid,
            name=excluded.name
            ''', (location, datetime_str, timezone, latitude, longitude, notime, str(guid), name))
        else:
            cursor.execute('''
            
            INSERT INTO myapp_event (location, datetime, timezone, latitude, longitude, notime, name)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
            location=excluded.location,
            datetime=excluded.datetime,
            timezone=excluded.timezone,
            latitude=excluded.latitude,
            longitude=excluded.longitude,
            notime=excluded.notime,
            name=excluded.name
            ''', (location, datetime_str, timezone, latitude, longitude, notime, name))

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
        cursor.execute('SELECT notime FROM myapp_event WHERE name = ? AND random_column = ?', (name, guid,))
        notime = cursor.fetchone()
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
        cursor.execute('SELECT notime FROM myapp_event WHERE name = ?', (name,))
        notime = cursor.fetchone()

    conn.close()

    if datetime:
        event = {
            'name': name,
            'location': location[0],
            'datetime': datetime[0],
            'timezone': timezone[0],
            'latitude': latitude[0],
            'longitude': longitude[0],
            'notime': notime[0]
        }
        return event
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
            conn = sqlite3.connect(db_filename)
            cursor = conn.cursor()

            if guid:
                cursor.execute("DELETE FROM myapp_event WHERE name IN ({}) AND random_column=?".format(
                    ','.join('?' * len(valid_names))), (*valid_names, guid))
            else:
                cursor.execute("DELETE FROM myapp_event WHERE name IN ({})".format(
                    ','.join('?' * len(valid_names))), valid_names)

            conn.commit()
            
            conn.close()

        except sqlite3.OperationalError as e:
            print(f"Database error: {e}")
            return f"Database error: {e}"
        except Exception as e:
            # General exception handling, useful for debugging
            print(f"An unexpected error occurred: {e}")
            return f"An unexpected error occurred: {e}"

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

# Function to save default settings in the database
def store_defaults(defaults):
                #     setting_name, userid=None, location=None, timezone=None, imprecise_aspects=None,
                #    minor_aspects=None, show_brief_aspects=None, show_score=None, orb_major=None,
                #    orb_minor=None, orb_fixed_star=None, orb_transit_fast=None, orb_transit_slow=None,
                #    orb_synastry_fast=None, orb_synastry_slow=None, degree_in_minutes=None, node=None,
                #    all_stars=None, house_system=None, house_cusps=None, hide_planetary_positions=None,
                #    hide_planetary_aspects=None, hide_fixed_star_aspects=None, hide_asteroid_aspects=None,
                #    transits_timezone=None, transits_location=None, output_type=None):
    """
    Stores the given default settings into the myapp_defaults table.
    """

    conn = sqlite3.connect("db.sqlite3")
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO myapp_defaults (
            setting_name, guid, location, timezone, imprecise_aspects, minor_aspects, show_brief_aspects, 
            show_score, orb_major, orb_minor, orb_fixed_star, orb_transit_fast, orb_transit_slow, 
            orb_synastry_fast, orb_synastry_slow, degree_in_minutes, node, all_stars, house_system, 
            house_cusps, hide_planetary_positions, hide_planetary_aspects, hide_fixed_star_aspects, 
            hide_asteroid_aspects, transits_timezone, transits_location, output_type
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
    defaults["Name"], defaults["GUID"], defaults["Location"], defaults["Timezone"], defaults["Imprecise Aspects"], defaults["Minor Aspects"], defaults["Show Brief Aspects"], 
    defaults["Show Score"], defaults["Orb Major"], defaults["Orb Minor"], defaults["Orb Fixed Star"], defaults["Orb Transit Fast"], defaults["Orb Transit Slow"], 
    defaults["Orb Synastry Fast"], defaults["Orb Synastry Slow"], defaults["Degree In Minutes"], defaults["Node"], defaults["All Stars"], defaults["House System"], 
    defaults["House Cusps"], defaults["Hide Planetary Positions"], defaults["Hide Planetary Aspects"], defaults["Hide Fixed Star Aspects"], 
    defaults["Hide Asteroid Aspects"], defaults["Transits Timezone"], defaults["Transits Location"], defaults["Output Type"]
    ))

    conn.commit()
    conn.close()

import sqlite3

def read_defaults(use_defaults, guid=None, db_filename='db.sqlite3'):
    """
    Reads the default settings from the myapp_defaults table and returns a dictionary with the values.

    Args:
    use_defaults (str): The name of the default settings to use.
    guid (str): The GUID of the user.
    db_filename (str): The path to the SQLite database file.

    Returns:
    dict: A dictionary with the retrieved default settings.
    """
    conn = sqlite3.connect(db_filename)
    cursor = conn.cursor()

    try:
        cursor.execute('''
            SELECT 
                location, timezone, imprecise_aspects, minor_aspects, show_brief_aspects, show_score, 
                orb_major, orb_minor, orb_fixed_star, orb_transit_fast, orb_transit_slow, 
                orb_synastry_fast, orb_synastry_slow, degree_in_minutes, node, all_stars, 
                house_system, house_cusps, hide_planetary_positions, hide_planetary_aspects, 
                hide_fixed_star_aspects, hide_asteroid_aspects, transits_timezone, transits_location, output_type
            FROM myapp_defaults
            WHERE setting_name = ? AND (guid IS NULL OR guid = ?)
        ''', (use_defaults, guid))
        
        row = cursor.fetchone()

        if row:
            defaults = {
                "Location": row[0] if row[0] is not None else None,
                "Timezone": row[1] if row[1] is not None else None,
                "Imprecise Aspects": row[2] if row[2] is not None else None,
                "Minor Aspects": row[3] if row[3] is not None else None,
                "Show Brief Aspects": row[4] if row[4] is not None else None,
                "Show Score": row[5] if row[5] is not None else None,
                "Orb Major": row[6] if row[6] is not None else None,
                "Orb Minor": row[7] if row[7] is not None else None,
                "Orb Fixed Star": row[8] if row[8] is not None else None,
                "Orb Transit Fast": row[9] if row[9] is not None else None,
                "Orb Transit Slow": row[10] if row[10] is not None else None,
                "Orb Synastry Fast": row[11] if row[11] is not None else None,
                "Orb Synastry Slow": row[12] if row[12] is not None else None,
                "Degree in Minutes": row[13] if row[13] is not None else None,
                "Node": row[14] if row[14] is not None else None,
                "All Stars": row[15] if row[15] is not None else None,
                "House System": row[16] if row[16] is not None else None,
                "House Cusps": row[17] if row[17] is not None else None,
                "Hide Planetary Positions": row[18] if row[18] is not None else None,
                "Hide Planetary Aspects": row[19] if row[19] is not None else None,
                "Hide Fixed Star Aspects": row[20] if row[20] is not None else None,
                "Hide Asteroid Aspects": row[21] if row[21] is not None else None,
                "Transits Timezone": row[22] if row[22] is not None else None,
                "Transits Location": row[23] if row[23] is not None else None,
                "Output Type": row[24] if row[24] is not None else None
            }
        else:
            defaults = {}
        
    except sqlite3.OperationalError as e:
        print(f"Database error: {e}")
        defaults = {}
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        defaults = {}

    conn.close()
    return defaults
