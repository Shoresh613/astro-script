import json
import os
import sqlite3
from pathlib import Path


DEFAULT_SETTINGS_NAME = "default"
LEGACY_DEFAULT_SETTINGS_NAME = "defaults"


def _django_db_path():
    try:
        from django.conf import settings

        if settings.configured:
            db_name = settings.DATABASES.get("default", {}).get("NAME")
            if db_name:
                return Path(db_name)
    except Exception:
        pass
    return None


def _default_db_path():
    env_path = os.getenv("ASTROSCRIPT_DB_PATH")
    if env_path:
        return Path(env_path)
    return _django_db_path() or Path("db.sqlite3")


DB_PATH = _default_db_path()


def connect(db_filename=None):
    db_path = DB_PATH if db_filename in (None, "db.sqlite3") else db_filename
    return sqlite3.connect(str(db_path))


def normalize_settings_name(settings_name):
    normalized = (settings_name or DEFAULT_SETTINGS_NAME).strip()
    if not normalized or normalized == LEGACY_DEFAULT_SETTINGS_NAME:
        return DEFAULT_SETTINGS_NAME
    return normalized


def check_and_fix_schema():
    """Compatibility hook kept non-destructive for embedded/Django use."""

    return False


def _table_columns(conn, table_name):
    cursor = conn.cursor()
    try:
        cursor.execute(f"PRAGMA table_info({table_name})")
    except sqlite3.OperationalError:
        return set()
    return {row[1] for row in cursor.fetchall()}


def _event_where_clause(guid):
    if guid:
        return "name = ? AND random_column = ?", (guid,)
    return "name = ? AND (random_column IS NULL OR random_column = '')", ()


def _coerce_update_event_args(altitude, notime, guid):
    if isinstance(altitude, bool) and (guid is None):
        if notime not in (False, None):
            guid = notime
        notime = altitude
        altitude = None
    return altitude, bool(notime), guid


def initialize_db():
    with connect() as conn:
        cursor = conn.cursor()
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
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS myapp_usersettings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                setting_name TEXT NOT NULL,
                guid TEXT NULL,
                settings TEXT NOT NULL,
                UNIQUE(setting_name, guid)
            )
            """
        )


def update_event(
    name,
    location,
    datetime_str,
    timezone,
    latitude,
    longitude,
    altitude=None,
    notime=False,
    guid=None,
):
    altitude, notime, guid = _coerce_update_event_args(altitude, notime, guid)
    guid_value = str(guid) if guid else None
    location_key = f"{latitude},{longitude}" if location == "Davison chart" else location
    if location_key:
        save_location(location_key, latitude, longitude, altitude)

    with connect() as conn:
        cursor = conn.cursor()
        event_columns = _table_columns(conn, "myapp_event")
        has_altitude_column = "altitude" in event_columns
        where_clause, extra_where_params = _event_where_clause(guid_value)
        cursor.execute(
            f"SELECT 1 FROM myapp_event WHERE {where_clause} LIMIT 1",
            (name, *extra_where_params),
        )
        exists = cursor.fetchone() is not None

        if exists:
            fields = [
                ("location", location),
                ("datetime", datetime_str),
                ("timezone", timezone),
                ("latitude", latitude),
                ("longitude", longitude),
                ("notime", int(notime)),
                ("random_column", guid_value),
            ]
            if has_altitude_column:
                fields.insert(5, ("altitude", altitude))
            assignments = ", ".join(f"{field} = ?" for field, _value in fields)
            values = [value for _field, value in fields]
            cursor.execute(
                f"UPDATE myapp_event SET {assignments} WHERE {where_clause}",
                (*values, name, *extra_where_params),
            )
            return

        columns = [
            "location",
            "datetime",
            "timezone",
            "latitude",
            "longitude",
            "notime",
            "random_column",
            "name",
        ]
        values = [
            location,
            datetime_str,
            timezone,
            latitude,
            longitude,
            int(notime),
            guid_value,
            name,
        ]
        if has_altitude_column:
            columns.insert(5, "altitude")
            values.insert(5, altitude)
        placeholders = ", ".join("?" for _column in columns)
        cursor.execute(
            f"INSERT INTO myapp_event ({', '.join(columns)}) VALUES ({placeholders})",
            values,
        )


def _location_altitude(cursor, location, latitude, longitude):
    location_key = f"{latitude},{longitude}" if location == "Davison chart" else location
    if not location_key:
        return None
    cursor.execute(
        "SELECT altitude FROM myapp_location WHERE location_name = ?",
        (str(location_key),),
    )
    row = cursor.fetchone()
    return row[0] if row else None


def get_event(name, guid=None):
    try:
        with connect() as conn:
            cursor = conn.cursor()
            event_columns = _table_columns(conn, "myapp_event")
            has_altitude_column = "altitude" in event_columns
            columns = "location, datetime, timezone, latitude, longitude"
            if has_altitude_column:
                columns += ", altitude"
            columns += ", notime"

            if guid:
                cursor.execute(
                    f"""
                    SELECT {columns}
                    FROM myapp_event
                    WHERE name = ? AND random_column = ?
                    LIMIT 1
                    """,
                    (name, str(guid)),
                )
            else:
                cursor.execute(
                    f"""
                    SELECT {columns}
                    FROM myapp_event
                    WHERE name = ?
                    LIMIT 1
                    """,
                    (name,),
                )

            event_data = cursor.fetchone()
            if not event_data:
                return None

            if has_altitude_column:
                location, datetime, timezone, latitude, longitude, altitude, notime = event_data
            else:
                location, datetime, timezone, latitude, longitude, notime = event_data
                altitude = _location_altitude(cursor, location, latitude, longitude)

            if altitude is None:
                altitude = _location_altitude(cursor, location, latitude, longitude)

            return {
                "name": name,
                "location": location,
                "datetime": datetime,
                "timezone": timezone,
                "latitude": latitude,
                "longitude": longitude,
                "altitude": altitude,
                "notime": notime,
            }
    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
        return None


def read_saved_names(guid=None, db_filename="db.sqlite3"):
    try:
        with connect(db_filename) as conn:
            cursor = conn.cursor()
            if guid:
                cursor.execute(
                    "SELECT name FROM myapp_event WHERE random_column = ? ORDER BY name",
                    (str(guid),),
                )
            else:
                cursor.execute("SELECT name FROM myapp_event ORDER BY name")
            return [row[0] for row in cursor.fetchall()]
    except sqlite3.OperationalError as e:
        print(f"Database error: {e}")
        return []
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return []


def remove_saved_names(names_to_remove, output_type, guid=None, db_filename="db.sqlite3"):
    existing_names = set(read_saved_names(guid, db_filename))
    names_to_remove = set(names_to_remove)
    invalid_names = list(names_to_remove - existing_names)
    valid_names = list(names_to_remove - set(invalid_names))

    if valid_names:
        try:
            with connect(db_filename) as conn:
                cursor = conn.cursor()
                placeholders = ",".join("?" for _name in valid_names)
                if guid:
                    cursor.execute(
                        f"""
                        DELETE FROM myapp_event
                        WHERE name IN ({placeholders}) AND random_column = ?
                        """,
                        (*valid_names, str(guid)),
                    )
                else:
                    cursor.execute(
                        f"DELETE FROM myapp_event WHERE name IN ({placeholders})",
                        valid_names,
                    )
        except sqlite3.OperationalError as e:
            print(f"Database error: {e}")
            return f"Database error: {e}"
        except Exception as e:
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
            to_return += (
                f"\nThe following names are not saved events: "
                f"{', '.join(invalid_names)}.\n"
            )
        if valid_names:
            to_return += (
                f"\nThe following names have been removed: "
                f"{', '.join(valid_names)}.\n"
            )

    return to_return


def save_location(location_name, latitude, longitude, altitude):
    with connect() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO myapp_location (location_name, latitude, longitude, altitude)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(location_name) DO UPDATE SET
                latitude = excluded.latitude,
                longitude = excluded.longitude,
                altitude = COALESCE(excluded.altitude, myapp_location.altitude)
            """,
            (location_name, latitude, longitude, altitude),
        )


def load_location(location_name):
    with connect() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT latitude, longitude, altitude
            FROM myapp_location
            WHERE location_name = ?
            """,
            (location_name,),
        )
        return cursor.fetchone()


def store_defaults(defaults):
    guid = defaults.get("GUID") or ""
    defaults["Name"] = normalize_settings_name(defaults.get("Name"))

    with connect() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO myapp_usersettings (setting_name, guid, settings)
            VALUES (?, ?, ?)
            ON CONFLICT(setting_name, guid) DO UPDATE SET
                settings = excluded.settings
            """,
            (defaults["Name"], guid, json.dumps(defaults)),
        )


def list_settings_profiles(guid="", db_filename="db.sqlite3"):
    settings_names = [DEFAULT_SETTINGS_NAME]
    try:
        with connect(db_filename) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT setting_name
                FROM myapp_usersettings
                WHERE guid IS NULL OR guid = '' OR guid = ?
                ORDER BY LOWER(setting_name)
                """,
                (guid or "",),
            )
            for (setting_name,) in cursor.fetchall():
                normalized_name = normalize_settings_name(setting_name)
                if normalized_name not in settings_names:
                    settings_names.append(normalized_name)
    except sqlite3.OperationalError as e:
        print(f"Database error: {e}")

    return [DEFAULT_SETTINGS_NAME] + sorted(
        [name for name in settings_names if name != DEFAULT_SETTINGS_NAME],
        key=str.lower,
    )


def delete_settings_profile(settings_name, guid="", db_filename="db.sqlite3"):
    normalized_name = normalize_settings_name(settings_name)
    if normalized_name == DEFAULT_SETTINGS_NAME:
        return False

    with connect(db_filename) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            DELETE FROM myapp_usersettings
            WHERE setting_name = ? AND guid = ?
            """,
            (normalized_name, guid or ""),
        )
        return cursor.rowcount > 0


def read_defaults(settings_name, guid="", db_filename="db.sqlite3"):
    normalized_name = normalize_settings_name(settings_name)
    candidate_names = [normalized_name]
    if normalized_name == DEFAULT_SETTINGS_NAME:
        candidate_names.append(LEGACY_DEFAULT_SETTINGS_NAME)

    try:
        with connect(db_filename) as conn:
            cursor = conn.cursor()
            for candidate_name in candidate_names:
                cursor.execute(
                    """
                    SELECT settings
                    FROM myapp_usersettings
                    WHERE setting_name = ?
                        AND (guid IS NULL OR guid = '' OR guid = ?)
                    ORDER BY CASE WHEN guid = ? THEN 0 ELSE 1 END
                    LIMIT 1
                    """,
                    (candidate_name, guid or "", guid or ""),
                )
                row = cursor.fetchone()
                if row:
                    return json.loads(row[0])
    except sqlite3.OperationalError as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    return {}
