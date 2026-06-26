import json
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path


DEFAULT_SETTINGS_NAME = "default"
LEGACY_DEFAULT_SETTINGS_NAME = "defaults"

EVENT_TABLE = "myapp_astroscript_event"
LOCATION_TABLE = "myapp_astroscript_location"
SETTING_TABLE = "myapp_astroscript_setting"


def _django_connection():
    try:
        from django.conf import settings
        from django.db import connection

        if settings.configured:
            return connection
    except Exception:
        pass
    return None


def _default_db_path():
    env_path = os.getenv("ASTROSCRIPT_DB_PATH")
    if env_path:
        return Path(env_path)
    return Path("db.sqlite3")


DB_PATH = _default_db_path()


def connect(db_filename=None):
    db_path = DB_PATH if db_filename in (None, "db.sqlite3") else db_filename
    return sqlite3.connect(str(db_path))


@contextmanager
def _cursor(db_filename=None):
    django_connection = _django_connection()
    if django_connection is not None and db_filename in (None, "db.sqlite3"):
        with django_connection.cursor() as cursor:
            yield cursor, "%s", True
        return

    with connect(db_filename) as conn:
        yield conn.cursor(), "?", False


def normalize_settings_name(settings_name):
    normalized = (settings_name or DEFAULT_SETTINGS_NAME).strip()
    if not normalized or normalized == LEGACY_DEFAULT_SETTINGS_NAME:
        return DEFAULT_SETTINGS_NAME
    return normalized


def check_and_fix_schema():
    """Compatibility hook kept non-destructive for embedded/Django use."""

    return False


def initialize_db():
    if _django_connection() is not None:
        return

    with connect() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {EVENT_TABLE} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                location TEXT,
                datetime TEXT NOT NULL,
                timezone TEXT,
                latitude REAL,
                longitude REAL,
                altitude REAL,
                notime INTEGER DEFAULT 0,
                guid TEXT NOT NULL DEFAULT '',
                UNIQUE(name, guid)
            )
            """
        )
        cursor.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {LOCATION_TABLE} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                location_name TEXT NOT NULL UNIQUE,
                latitude REAL,
                longitude REAL,
                altitude REAL
            )
            """
        )
        cursor.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {SETTING_TABLE} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                setting_name TEXT NOT NULL,
                guid TEXT NOT NULL DEFAULT '',
                settings TEXT NOT NULL,
                UNIQUE(setting_name, guid)
            )
            """
        )


def _coerce_update_event_args(altitude, notime, guid):
    if isinstance(altitude, bool) and guid is None:
        if notime not in (False, None):
            guid = notime
        notime = altitude
        altitude = None
    return altitude, bool(notime), guid


def _guid_value(guid):
    return str(guid) if guid else ""


def _fetchone(cursor):
    return cursor.fetchone()


def _upsert_location(cursor, placeholder, location_name, latitude, longitude, altitude):
    cursor.execute(
        f"SELECT id, altitude FROM {LOCATION_TABLE} WHERE location_name = {placeholder}",
        [location_name],
    )
    row = _fetchone(cursor)
    if row:
        existing_altitude = row[1]
        cursor.execute(
            f"""
            UPDATE {LOCATION_TABLE}
            SET latitude = {placeholder},
                longitude = {placeholder},
                altitude = {placeholder}
            WHERE location_name = {placeholder}
            """,
            [
                latitude,
                longitude,
                altitude if altitude is not None else existing_altitude,
                location_name,
            ],
        )
        return

    cursor.execute(
        f"""
        INSERT INTO {LOCATION_TABLE}
            (location_name, latitude, longitude, altitude)
        VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder})
        """,
        [location_name, latitude, longitude, altitude],
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
    guid = _guid_value(guid)
    location_key = f"{latitude},{longitude}" if location == "Davison chart" else location
    if location_key:
        save_location(location_key, latitude, longitude, altitude)

    with _cursor() as (cursor, placeholder, _using_django):
        cursor.execute(
            f"""
            SELECT id
            FROM {EVENT_TABLE}
            WHERE name = {placeholder} AND guid = {placeholder}
            LIMIT 1
            """,
            [name, guid],
        )
        row = _fetchone(cursor)
        values = [
            location,
            datetime_str,
            timezone,
            latitude,
            longitude,
            altitude,
            int(notime),
            guid,
            name,
        ]
        if row:
            cursor.execute(
                f"""
                UPDATE {EVENT_TABLE}
                SET location = {placeholder},
                    datetime = {placeholder},
                    timezone = {placeholder},
                    latitude = {placeholder},
                    longitude = {placeholder},
                    altitude = {placeholder},
                    notime = {placeholder},
                    guid = {placeholder}
                WHERE name = {placeholder} AND guid = {placeholder}
                """,
                [*values, guid],
            )
            return

        cursor.execute(
            f"""
            INSERT INTO {EVENT_TABLE}
                (location, datetime, timezone, latitude, longitude, altitude, notime, guid, name)
            VALUES (
                {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder},
                {placeholder}, {placeholder}, {placeholder}, {placeholder}
            )
            """,
            values,
        )


def get_event(name, guid=None):
    guid = _guid_value(guid)
    try:
        with _cursor() as (cursor, placeholder, _using_django):
            cursor.execute(
                f"""
                SELECT name, location, datetime, timezone, latitude, longitude, altitude, notime
                FROM {EVENT_TABLE}
                WHERE name = {placeholder} AND guid = {placeholder}
                LIMIT 1
                """,
                [name, guid],
            )
            row = _fetchone(cursor)
            if not row:
                return None

            (
                event_name,
                location,
                datetime,
                timezone,
                latitude,
                longitude,
                altitude,
                notime,
            ) = row
            if altitude is None:
                location_key = (
                    f"{latitude},{longitude}" if location == "Davison chart" else location
                )
                if location_key:
                    cursor.execute(
                        f"""
                        SELECT altitude
                        FROM {LOCATION_TABLE}
                        WHERE location_name = {placeholder}
                        LIMIT 1
                        """,
                        [str(location_key)],
                    )
                    location_row = _fetchone(cursor)
                    altitude = location_row[0] if location_row else None

            return {
                "name": event_name,
                "location": location,
                "datetime": datetime,
                "timezone": timezone,
                "latitude": latitude,
                "longitude": longitude,
                "altitude": altitude,
                "notime": notime,
            }
    except Exception as e:
        print(f"An error occurred: {e}")
        return None


def read_events(guid=None, db_filename="db.sqlite3"):
    guid = _guid_value(guid)
    try:
        with _cursor(db_filename) as (cursor, placeholder, _using_django):
            if guid:
                cursor.execute(
                    f"""
                    SELECT name, location, datetime, timezone, latitude, longitude, altitude, notime, guid
                    FROM {EVENT_TABLE}
                    WHERE guid = {placeholder}
                    ORDER BY name
                    """,
                    [guid],
                )
            else:
                cursor.execute(
                    f"""
                    SELECT name, location, datetime, timezone, latitude, longitude, altitude, notime, guid
                    FROM {EVENT_TABLE}
                    ORDER BY name
                    """
                )
            return [
                {
                    "name": row[0],
                    "location": row[1],
                    "datetime": row[2],
                    "timezone": row[3],
                    "latitude": row[4],
                    "longitude": row[5],
                    "altitude": row[6],
                    "notime": row[7],
                    "guid": row[8],
                }
                for row in cursor.fetchall()
            ]
    except Exception as e:
        print(f"Database error: {e}")
        return []


def read_saved_names(guid=None, db_filename="db.sqlite3"):
    return [event["name"] for event in read_events(guid, db_filename)]


def delete_names_for_guid(names_to_remove, guid=None, db_filename="db.sqlite3"):
    names_to_remove = list(names_to_remove)
    if not names_to_remove:
        return 0

    guid = _guid_value(guid)
    try:
        with _cursor(db_filename) as (cursor, placeholder, _using_django):
            placeholders = ", ".join(placeholder for _name in names_to_remove)
            if guid:
                cursor.execute(
                    f"""
                    DELETE FROM {EVENT_TABLE}
                    WHERE name IN ({placeholders}) AND guid = {placeholder}
                    """,
                    [*names_to_remove, guid],
                )
            else:
                cursor.execute(
                    f"DELETE FROM {EVENT_TABLE} WHERE name IN ({placeholders})",
                    names_to_remove,
                )
            return cursor.rowcount
    except Exception as e:
        print(f"Database error: {e}")
        return 0


def remove_saved_names(names_to_remove, output_type, guid=None, db_filename="db.sqlite3"):
    existing_names = set(read_saved_names(guid, db_filename))
    names_to_remove = set(names_to_remove)
    invalid_names = list(names_to_remove - existing_names)
    valid_names = list(names_to_remove - set(invalid_names))

    if valid_names:
        delete_names_for_guid(valid_names, guid, db_filename)

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


def delete_events_for_guid(guid="", db_filename="db.sqlite3"):
    guid = _guid_value(guid)
    try:
        with _cursor(db_filename) as (cursor, placeholder, _using_django):
            cursor.execute(
                f"DELETE FROM {EVENT_TABLE} WHERE guid = {placeholder}",
                [guid],
            )
            return cursor.rowcount
    except Exception as e:
        print(f"Database error: {e}")
        return 0


def save_location(location_name, latitude, longitude, altitude):
    with _cursor() as (cursor, placeholder, _using_django):
        _upsert_location(cursor, placeholder, location_name, latitude, longitude, altitude)


def load_location(location_name):
    with _cursor() as (cursor, placeholder, _using_django):
        cursor.execute(
            f"""
            SELECT latitude, longitude, altitude
            FROM {LOCATION_TABLE}
            WHERE location_name = {placeholder}
            LIMIT 1
            """,
            [location_name],
        )
        return _fetchone(cursor)


def read_locations(db_filename="db.sqlite3"):
    try:
        with _cursor(db_filename) as (cursor, _placeholder, _using_django):
            cursor.execute(
                f"""
                SELECT location_name, latitude, longitude, altitude
                FROM {LOCATION_TABLE}
                ORDER BY location_name
                """
            )
            return [
                {
                    "location_name": row[0],
                    "latitude": row[1],
                    "longitude": row[2],
                    "altitude": row[3],
                }
                for row in cursor.fetchall()
            ]
    except Exception as e:
        print(f"Database error: {e}")
        return []


def store_defaults(defaults):
    guid = _guid_value(defaults.get("GUID"))
    settings_name = normalize_settings_name(defaults.get("Name"))
    defaults = dict(defaults)
    defaults["GUID"] = guid
    defaults["Name"] = settings_name

    with _cursor() as (cursor, placeholder, _using_django):
        settings_json = json.dumps(defaults, default=str)
        cursor.execute(
            f"""
            SELECT id
            FROM {SETTING_TABLE}
            WHERE setting_name = {placeholder} AND guid = {placeholder}
            LIMIT 1
            """,
            [settings_name, guid],
        )
        if _fetchone(cursor):
            cursor.execute(
                f"""
                UPDATE {SETTING_TABLE}
                SET settings = {placeholder}
                WHERE setting_name = {placeholder} AND guid = {placeholder}
                """,
                [settings_json, settings_name, guid],
            )
            return

        cursor.execute(
            f"""
            INSERT INTO {SETTING_TABLE} (setting_name, guid, settings)
            VALUES ({placeholder}, {placeholder}, {placeholder})
            """,
            [settings_name, guid, settings_json],
        )


def store_settings_row(settings_name, guid, settings):
    settings_name = normalize_settings_name(settings_name)
    settings_data = settings if isinstance(settings, dict) else json.loads(settings or "{}")
    settings_data["Name"] = settings_name
    settings_data["GUID"] = _guid_value(guid)
    store_defaults(settings_data)


def read_settings(guid=None, db_filename="db.sqlite3"):
    guid = _guid_value(guid)
    try:
        with _cursor(db_filename) as (cursor, placeholder, _using_django):
            if guid:
                cursor.execute(
                    f"""
                    SELECT setting_name, guid, settings
                    FROM {SETTING_TABLE}
                    WHERE guid = {placeholder}
                    ORDER BY setting_name
                    """,
                    [guid],
                )
            else:
                cursor.execute(
                    f"""
                    SELECT setting_name, guid, settings
                    FROM {SETTING_TABLE}
                    ORDER BY setting_name
                    """
                )
            return [
                {
                    "setting_name": row[0],
                    "guid": row[1],
                    "settings": json.loads(row[2]),
                }
                for row in cursor.fetchall()
            ]
    except Exception as e:
        print(f"Database error: {e}")
        return []


def list_settings_profiles(guid="", db_filename="db.sqlite3"):
    settings_names = [DEFAULT_SETTINGS_NAME]
    guid = _guid_value(guid)
    try:
        with _cursor(db_filename) as (cursor, placeholder, _using_django):
            cursor.execute(
                f"""
                SELECT setting_name
                FROM {SETTING_TABLE}
                WHERE guid = '' OR guid = {placeholder}
                ORDER BY LOWER(setting_name)
                """,
                [guid],
            )
            for (setting_name,) in cursor.fetchall():
                normalized_name = normalize_settings_name(setting_name)
                if normalized_name not in settings_names:
                    settings_names.append(normalized_name)
    except Exception as e:
        print(f"Database error: {e}")

    return [DEFAULT_SETTINGS_NAME] + sorted(
        [name for name in settings_names if name != DEFAULT_SETTINGS_NAME],
        key=str.lower,
    )


def delete_settings_profile(settings_name, guid="", db_filename="db.sqlite3"):
    normalized_name = normalize_settings_name(settings_name)
    if normalized_name == DEFAULT_SETTINGS_NAME:
        return False

    guid = _guid_value(guid)
    try:
        with _cursor(db_filename) as (cursor, placeholder, _using_django):
            cursor.execute(
                f"""
                DELETE FROM {SETTING_TABLE}
                WHERE setting_name = {placeholder} AND guid = {placeholder}
                """,
                [normalized_name, guid],
            )
            return cursor.rowcount > 0
    except Exception as e:
        print(f"Database error: {e}")
        return False


def delete_settings_for_guid(guid="", db_filename="db.sqlite3"):
    guid = _guid_value(guid)
    try:
        with _cursor(db_filename) as (cursor, placeholder, _using_django):
            cursor.execute(
                f"DELETE FROM {SETTING_TABLE} WHERE guid = {placeholder}",
                [guid],
            )
            return cursor.rowcount
    except Exception as e:
        print(f"Database error: {e}")
        return 0


def read_defaults(settings_name, guid="", db_filename="db.sqlite3"):
    normalized_name = normalize_settings_name(settings_name)
    candidate_names = [normalized_name]
    if normalized_name == DEFAULT_SETTINGS_NAME:
        candidate_names.append(LEGACY_DEFAULT_SETTINGS_NAME)

    guid = _guid_value(guid)
    try:
        with _cursor(db_filename) as (cursor, placeholder, _using_django):
            for candidate_name in candidate_names:
                cursor.execute(
                    f"""
                    SELECT settings
                    FROM {SETTING_TABLE}
                    WHERE setting_name = {placeholder}
                        AND (guid = {placeholder} OR guid = '')
                    ORDER BY CASE WHEN guid = {placeholder} THEN 0 ELSE 1 END
                    LIMIT 1
                    """,
                    [candidate_name, guid, guid],
                )
                row = _fetchone(cursor)
                if row:
                    return json.loads(row[0])
    except Exception as e:
        print(f"Database error: {e}")
    return {}
