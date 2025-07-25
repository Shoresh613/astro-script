import sqlite3
import json
import logging
import os


def check_and_fix_schema():
    """Check if the database has the correct schema and fix it if necessary"""
    try:
        conn = sqlite3.connect("db.sqlite3")
        cursor = conn.cursor()

        # Check if the myapp_event table has the correct schema
        cursor.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name='myapp_event'"
        )
        result = cursor.fetchone()

        if result and "PRIMARY KEY (name, random_column)" in result[0]:
            # Schema is incorrect, need to recreate the table
            logging.info("Detected incorrect schema, recreating database...")
            conn.close()

            # Backup existing database if it has data
            if os.path.exists("db.sqlite3"):
                import shutil

                shutil.copy("db.sqlite3", "db.sqlite3.backup")
                logging.info("Created backup: db.sqlite3.backup")

            # Remove the problematic database file
            os.remove("db.sqlite3")
            return True

        conn.close()
        return False

    except sqlite3.Error as e:
        logging.error(f"Database error: {e}")
        return True  # Force recreation on any error


# Initialize the database and create tables if they don't exist
def initialize_db():
    # Check and fix schema if necessary
    schema_fixed = check_and_fix_schema()

    conn = sqlite3.connect("db.sqlite3")
    cursor = conn.cursor()
    # Create the myapp_event table
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS myapp_event (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        location TEXT,
        datetime TEXT,
        timezone TEXT,
        latitude REAL,
        longitude REAL,
        altitude REAL,
        notime INTEGER DEFAULT FALSE,
        random_column TEXT NULL,
        name TEXT NOT NULL,
        UNIQUE(name, random_column)
    )
    """
    )

    # Create the myapp_location table
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS myapp_location (
        location_name TEXT PRIMARY KEY,
        latitude REAL,
        longitude REAL,
        altitude REAL
    )
    """
    )

    # Create the myapp_defaults table
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS myapp_usersettings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        setting_name TEXT NOT NULL,
        guid TEXT NULL,
        settings TEXT NOT NULL,
        UNIQUE(setting_name, guid));
    """
    )

    conn.commit()
    conn.close()


# Function to add or update an event in the database
def update_event(
    name, location, datetime_str, timezone, latitude, longitude, altitude, notime, guid
):
    conn = sqlite3.connect("db.sqlite3")
    cursor = conn.cursor()

    # only for debug
    # print(f"name={name} location={location} datetime_str={datetime_str} timezone={timezone} latitude={latitude} longitude={longitude} altitude={altitude} notime={notime} guid={guid}")
    result = get_event(name, guid)
    if result:
        # print(f"DEBUG: get_event() result{result}")        cursor.execute(
        """
        UPDATE myapp_event
        SET location = ?,
            datetime = ?,
            timezone = ?,
            latitude = ?,
            longitude = ?,
            altitude = ?,
            notime = ?,
            random_column = ?
        WHERE name = ? AND random_column = ?
        """,
        (
            location,
            datetime_str,
            timezone,
            latitude,
            longitude,
            altitude,
            notime,
            str(guid),
            name,
            str(guid),
        ),
    else:
        if guid:
            cursor.execute(
                """
            
            INSERT INTO myapp_event (location, datetime, timezone, latitude, longitude, altitude, notime, random_column, name)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(random_column, name) DO UPDATE SET
            location=excluded.location,
            datetime=excluded.datetime,
            timezone=excluded.timezone,
            latitude=excluded.latitude,
            longitude=excluded.longitude,
            altitude=excluded.altitude,
            notime=excluded.notime,
            random_column=excluded.random_column,
            name=excluded.name
            """,
                (
                    location,
                    datetime_str,
                    timezone,
                    latitude,
                    longitude,
                    altitude,
                    notime,
                    str(guid),
                    name,
                ),
            )
        else:
            cursor.execute(
                """
            
            INSERT INTO myapp_event (location, datetime, timezone, latitude, longitude, altitude, notime, name)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(random_column, name) DO UPDATE SET
            location=excluded.location,
            datetime=excluded.datetime,
            timezone=excluded.timezone,
            latitude=excluded.latitude,
            longitude=excluded.longitude,
            altitude=excluded.altitude,
            notime=excluded.notime,
            name=excluded.name
            """,
                (
                    location,
                    datetime_str,
                    timezone,
                    latitude,
                    longitude,
                    altitude,
                    notime,
                    name,
                ),
            )

    conn.commit()
    conn.close()


def get_event(name, guid=None):
    """
    Retrieve event data from the database based on the given name and optional GUID.
    Args:
        name (str): The name of the event.
        guid (str, optional): The GUID of the event. Defaults to None.
    Returns:
        dict or None: A dictionary containing the event data if found, or None if not found.
    Raises:
        sqlite3.Error: If an error occurs while accessing the database.
    """
    try:
        with sqlite3.connect("db.sqlite3") as conn:
            cursor = conn.cursor()

            if guid:
                cursor.execute(
                    "SELECT location, datetime, timezone, latitude, longitude, altitude, notime FROM myapp_event WHERE name = ? AND random_column = ?",
                    (
                        name,
                        guid,
                    ),
                )
            else:
                cursor.execute(
                    "SELECT location, datetime, timezone, latitude, longitude, altitude, notime FROM myapp_event WHERE name = ?",
                    (name,),
                )

            event_data = cursor.fetchone()

            if not event_data:
                return None

            location, datetime, timezone, latitude, longitude, altitude, notime = (
                event_data
            )

            event = {
                "name": name,
                "location": location,
                "datetime": datetime,
                "timezone": timezone,
                "latitude": latitude,
                "longitude": longitude,
                "altitude": altitude,
                "notime": notime,
            }

            return event

    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
        return None


def read_saved_names(guid=None, db_filename="db.sqlite3"):
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
            # print(f"DEBUG - read_saved_names() guid: {guid}")
            cursor.execute(
                f"SELECT name FROM myapp_event WHERE random_column=?", (guid,)
            )
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


def remove_saved_names(
    names_to_remove, output_type, guid=None, db_filename="db.sqlite3"
):
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
                cursor.execute(
                    "DELETE FROM myapp_event WHERE name IN ({}) AND random_column=?".format(
                        ",".join("?" * len(valid_names))
                    ),
                    (*valid_names, guid),
                )
            else:
                cursor.execute(
                    "DELETE FROM myapp_event WHERE name IN ({})".format(
                        ",".join("?" * len(valid_names))
                    ),
                    valid_names,
                )

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
    if output_type in ("text", "html"):
        if invalid_names:
            print(
                f"\nThe following names are not saved events: {', '.join(invalid_names)}.\n"
            )
        if valid_names:
            print(
                f"\nThe following names have been removed: {', '.join(valid_names)}.\n"
            )
    else:
        if invalid_names:
            to_return += f"\nThe following names are not saved events: {', '.join(invalid_names)}.\n"
        if valid_names:
            to_return += (
                f"\nThe following names have been removed: {', '.join(valid_names)}.\n"
            )

    return to_return


# Function to save a location in the database
def save_location(location_name, latitude, longitude, altitude):
    conn = sqlite3.connect("db.sqlite3")
    cursor = conn.cursor()

    cursor.execute(
        """
    INSERT INTO myapp_location (location_name, latitude, longitude, altitude)
    VALUES (?, ?, ?, ?)
    ON CONFLICT(location_name) DO UPDATE SET
    latitude=excluded.latitude,
    longitude=excluded.longitude,
    altitude=excluded.altitude
    """,
        (location_name, latitude, longitude, altitude),
    )

    conn.commit()
    conn.close()


# Function to load a location from the database
def load_location(location_name):
    conn = sqlite3.connect("db.sqlite3")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT latitude, longitude, altitude FROM myapp_location WHERE location_name = ?",
        (location_name,),
    )
    location = cursor.fetchone()

    conn.close()
    return location


# Function to save default settings in the database
def store_defaults(defaults):
    """
    Stores the given default settings into the myapp_defaults table.
    """
    guid = defaults["GUID"] if defaults["GUID"] is not None else ""

    conn = sqlite3.connect("db.sqlite3")
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO myapp_usersettings (setting_name, guid, settings) 
        VALUES (?, ?, ?)
        ON CONFLICT(setting_name, guid) 
        DO UPDATE SET 
            settings = excluded.settings
    """,
        (defaults["Name"], guid, json.dumps(defaults)),
    )

    conn.commit()
    conn.close()


def read_defaults(settings_name, guid="", db_filename="db.sqlite3"):
    """
    Reads the default settings from the myapp_defaults table and returns a dictionary with the values.

    Args:
    settings_name (str): The name of the default settings to use.
    guid (str): The GUID of the user.
    db_filename (str): The path to the SQLite database file.

    Returns:
    dict: A dictionary with the retrieved default settings.
    """
    conn = sqlite3.connect(db_filename)
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT 
                settings
            FROM myapp_usersettings
            WHERE setting_name = ? AND (guid IS NULL OR guid = ?)
        """,
            (settings_name, guid),
        )

        row = cursor.fetchone()

        if row:
            defaults = json.loads(row[0])
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
