"""
Data management functions for the astro script.
Contains functions for loading/saving events and database operations.
"""

import json
import os
from datetime import datetime
import pytz

try:
    from . import db_manager
except ImportError:
    import db_manager


def load_event(name: str, guid: str = None) -> dict:
    """
    Load event data from database or JSON file.

    Args:
        name: event name to load
        guid: optional GUID for specific event

    Returns:
        dict: event data if found, None otherwise
    """
    # Try database first
    try:
        event_data = db_manager.get_event(name, guid)
        if event_data:
            return event_data
    except Exception as e:
        print(f"Error loading from database: {e}")

    # Fallback to JSON file
    return load_event_from_json(name)


def save_event(event_data: dict) -> bool:
    """
    Save event data to database and JSON file.

    Args:
        event_data: event data to save

    Returns:
        bool: success status
    """
    success = True

    # Save to database using update_event function
    try:
        db_manager.update_event(
            event_data.get("name", ""),
            event_data.get("location", ""),
            event_data.get("datetime", ""),
            event_data.get("timezone", ""),
            event_data.get("latitude", 0),
            event_data.get("longitude", 0),
            event_data.get("altitude", 0),
            event_data.get("notime", False),
            event_data.get("guid", ""),
        )
    except Exception as e:
        print(f"Error saving to database: {e}")
        success = False

    # Save to JSON as backup
    try:
        save_event_to_json(event_data)
    except Exception as e:
        print(f"Error saving to JSON: {e}")
        success = False

    return success


def load_event_from_json(name: str, filename: str = "saved_events.json") -> dict:
    """
    Load event from JSON file.

    Args:
        name: event name
        filename: JSON filename

    Returns:
        dict: event data if found
    """
    try:
        if os.path.exists(filename):
            with open(filename, "r", encoding="utf-8") as f:
                events = json.load(f)
                return events.get(name)
    except Exception as e:
        print(f"Error loading from JSON: {e}")

    return None


def save_event_to_json(event_data: dict, filename: str = "saved_events.json") -> bool:
    """
    Save event to JSON file.

    Args:
        event_data: event data to save
        filename: JSON filename

    Returns:
        bool: success status
    """
    try:
        # Load existing events
        events = {}
        if os.path.exists(filename):
            with open(filename, "r", encoding="utf-8") as f:
                events = json.load(f)

        # Add/update event
        name = event_data.get("name", "Unknown")
        events[name] = event_data

        # Save back to file
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(events, f, indent=2, ensure_ascii=False, default=str)

        return True
    except Exception as e:
        print(f"Error saving to JSON: {e}")
        return False


def list_saved_events() -> list:
    """
    List all saved events.

    Returns:
        list: list of saved event names
    """
    events = []

    # From database
    try:
        db_events = db_manager.read_saved_names()
        if db_events:
            events.extend([event["name"] for event in db_events if "name" in event])
    except Exception as e:
        print(f"Error listing database events: {e}")

    # From JSON file
    try:
        json_events = list_json_events()
        # Add any that aren't already in the list
        for event in json_events:
            if event not in events:
                events.append(event)
    except Exception as e:
        print(f"Error listing JSON events: {e}")

    return sorted(events)


def list_json_events(filename: str = "saved_events.json") -> list:
    """
    List events from JSON file.

    Args:
        filename: JSON filename

    Returns:
        list: list of event names
    """
    try:
        if os.path.exists(filename):
            with open(filename, "r", encoding="utf-8") as f:
                events = json.load(f)
                return list(events.keys())
    except Exception as e:
        print(f"Error listing JSON events: {e}")

    return []


def delete_event(name: str, guid: str = None) -> bool:
    """
    Delete an event from database and JSON file.

    Args:
        name: event name
        guid: optional GUID

    Returns:
        bool: success status
    """
    success = True

    # Delete from database
    try:
        db_manager.remove_saved_names(name, guid)
    except Exception as e:
        print(f"Error deleting from database: {e}")
        success = False

    # Delete from JSON
    try:
        delete_event_from_json(name)
    except Exception as e:
        print(f"Error deleting from JSON: {e}")
        success = False

    return success


def delete_event_from_json(name: str, filename: str = "saved_events.json") -> bool:
    """
    Delete event from JSON file.

    Args:
        name: event name
        filename: JSON filename

    Returns:
        bool: success status
    """
    try:
        if os.path.exists(filename):
            with open(filename, "r", encoding="utf-8") as f:
                events = json.load(f)

            if name in events:
                del events[name]

                with open(filename, "w", encoding="utf-8") as f:
                    json.dump(events, f, indent=2, ensure_ascii=False, default=str)

                return True
    except Exception as e:
        print(f"Error deleting from JSON: {e}")

    return False


def create_event_data(
    name: str,
    date: datetime,
    latitude: float,
    longitude: float,
    altitude: float = 0,
    timezone: str = "UTC",
    location: str = "",
    notime: bool = False,
    guid: str = None,
) -> dict:
    """
    Create standardized event data dictionary.

    Args:
        name: event name
        date: event datetime
        latitude: latitude in degrees
        longitude: longitude in degrees
        altitude: altitude in meters
        timezone: timezone name
        location: location description
        notime: whether time is unknown
        guid: optional GUID

    Returns:
        dict: standardized event data
    """
    return {
        "name": name,
        "datetime": date.isoformat() if isinstance(date, datetime) else str(date),
        "latitude": float(latitude),
        "longitude": float(longitude),
        "altitude": float(altitude),
        "timezone": timezone,
        "location": location,
        "notime": int(notime),
        "guid": guid,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }


def validate_event_data(event_data: dict) -> bool:
    """
    Validate event data structure.

    Args:
        event_data: event data to validate

    Returns:
        bool: True if valid
    """
    required_fields = ["name", "datetime", "latitude", "longitude", "timezone"]

    # Check required fields exist
    for field in required_fields:
        if field not in event_data:
            return False

    # Validate data types and ranges
    try:
        # Validate coordinates
        lat = float(event_data["latitude"])
        lon = float(event_data["longitude"])

        if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
            return False

        # Validate datetime
        if isinstance(event_data["datetime"], str):
            datetime.fromisoformat(event_data["datetime"])

        # Validate timezone
        tz = pytz.timezone(event_data["timezone"])

        return True
    except Exception:
        return False


def migrate_json_to_database(filename: str = "saved_events.json") -> int:
    """
    Migrate events from JSON file to database.

    Args:
        filename: JSON filename

    Returns:
        int: number of events migrated
    """
    migrated_count = 0

    try:
        if not os.path.exists(filename):
            return 0

        with open(filename, "r", encoding="utf-8") as f:
            events = json.load(f)

        for name, event_data in events.items():
            try:
                # Ensure event_data has required fields
                if "name" not in event_data:
                    event_data["name"] = name  # Validate and save to database
                if validate_event_data(event_data):
                    save_event(event_data)
                    migrated_count += 1
                else:
                    print(f"Invalid event data for {name}, skipping migration")
            except Exception as e:
                print(f"Error migrating event {name}: {e}")

    except Exception as e:
        print(f"Error during migration: {e}")

    return migrated_count


def backup_database_to_json(filename: str = "database_backup.json") -> bool:
    """
    Backup database events to JSON file.

    Args:
        filename: backup filename

    Returns:
        bool: success status
    """
    try:
        events_data = db_manager.read_saved_names()

        # Convert to name-keyed dictionary
        events_dict = {}
        if events_data:
            for event in events_data:
                name = event.get("name", "Unknown")
                # Get full event data
                full_event = db_manager.get_event(name, event.get("guid"))
                if full_event:
                    events_dict[name] = full_event

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(events_dict, f, indent=2, ensure_ascii=False, default=str)

        return True
    except Exception as e:
        print(f"Error backing up database: {e}")
        return False


def get_event_statistics() -> dict:
    """
    Get statistics about saved events.

    Returns:
        dict: event statistics
    """
    try:
        events_data = db_manager.read_saved_names()

        if not events_data:
            return {
                "total_events": 0,
                "events_with_time": 0,
                "events_without_time": 0,
                "timezone_distribution": {},
            }

        total_events = len(events_data)
        events_with_time = 0
        events_without_time = 0
        timezone_counts = {}

        for event_summary in events_data:
            name = event_summary.get("name", "")
            guid = event_summary.get("guid", "")

            # Get full event data
            full_event = db_manager.get_event(name, guid)
            if full_event:
                if not full_event.get("notime", False):
                    events_with_time += 1
                else:
                    events_without_time += 1

                tz = full_event.get("timezone", "Unknown")
                timezone_counts[tz] = timezone_counts.get(tz, 0) + 1

        return {
            "total_events": total_events,
            "events_with_time": events_with_time,
            "events_without_time": events_without_time,
            "timezone_distribution": timezone_counts,
        }
    except Exception as e:
        print(f"Error getting statistics: {e}")
        return {}
