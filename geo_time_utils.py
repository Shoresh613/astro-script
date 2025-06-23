"""
Geographic and time utility functions for the astro script.
Contains functions for coordinate lookups, timezone handling, and location management.
"""

import pytz
from datetime import datetime, timedelta
from geopy.geocoders import Nominatim
import requests
import urllib3
import json
import os

# Disable SSL warnings for unverified HTTPS requests (open-elevation.com has SSL issues)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

try:
    from timezonefinder import TimezoneFinder

    tz_finder_installed = True
except ImportError:
    tz_finder_installed = False

# Global timezone finder instance
if tz_finder_installed:
    tf = TimezoneFinder()


def get_coordinates(location_name: str) -> tuple:
    """
    Get coordinates for a location name using geopy.

    Args:
        location_name: name of location to look up

    Returns:
        tuple: (latitude, longitude, altitude, formatted_address)
    """
    try:
        geolocator = Nominatim(user_agent="astro_script")
        location = geolocator.geocode(location_name, timeout=10)

        if location:
            latitude = location.latitude
            longitude = location.longitude
            address = location.address

            # Try to get altitude
            altitude = get_altitude(latitude, longitude, location_name)

            return latitude, longitude, altitude, address
        else:
            raise ValueError(f"Location '{location_name}' not found")

    except Exception as e:
        print(f"Error getting coordinates for {location_name}: {e}")
        return None, None, 0, None


def get_altitude(lat: float, lon: float, location_name: str) -> float:
    """
    Get altitude for coordinates using various APIs.

    Args:
        lat: latitude
        lon: longitude
        location_name: location name for fallback

    Returns:
        float: altitude in meters
    """
    try:
        # Try Open Elevation API first
        url = f"https://api.open-elevation.com/api/v1/lookup?locations={lat},{lon}"
        # Disable SSL verification to handle expired certificates
        response = requests.get(url, verify=False, timeout=5)

        if response.status_code == 200:
            data = response.json()
            if data.get("results"):
                return float(data["results"][0]["elevation"])

    except Exception as e:
        print(f"Error getting altitude: {e}")

    # Return 0 as default
    return 0.0


def get_timezone_for_coordinates(latitude: float, longitude: float) -> str:
    """
    Get timezone for coordinates using TimezoneFinder.

    Args:
        latitude: latitude in degrees
        longitude: longitude in degrees

    Returns:
        str: timezone name
    """
    if not tz_finder_installed:
        return "UTC"

    try:
        timezone_name = tf.timezone_at(lat=latitude, lng=longitude)
        return timezone_name if timezone_name else "UTC"
    except Exception as e:
        print(f"Error finding timezone: {e}")
        return "UTC"


def convert_lmt_to_standard(
    local_datetime: datetime, longitude: float, timezone_name: str = None
) -> datetime:
    """
    Convert Local Mean Time to standard timezone time.

    Args:
        local_datetime: datetime in Local Mean Time
        longitude: longitude in degrees
        timezone_name: target timezone name

    Returns:
        datetime: converted datetime
    """
    # Calculate LMT offset (4 minutes per degree from Greenwich)
    lmt_offset_minutes = longitude * 4
    lmt_offset = timedelta(minutes=lmt_offset_minutes)

    # Convert LMT to UTC
    utc_datetime = local_datetime - lmt_offset

    # If timezone specified, convert to that timezone
    if timezone_name:
        try:
            target_tz = pytz.timezone(timezone_name)
            utc_tz = pytz.utc

            # Localize UTC time and convert to target timezone
            utc_localized = utc_tz.localize(utc_datetime)
            local_time = utc_localized.astimezone(target_tz)

            return local_time.replace(tzinfo=None)
        except Exception as e:
            print(f"Error converting timezone: {e}")

    return utc_datetime


def parse_date(date_string: str) -> datetime:
    """
    Parse various date string formats.

    Args:
        date_string: date string to parse

    Returns:
        datetime: parsed datetime
    """
    # Handle special cases
    if date_string.lower() == "now":
        return datetime.now()

    # Common date formats to try
    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d",
        "%d/%m/%Y %H:%M:%S",
        "%d/%m/%Y %H:%M",
        "%d/%m/%Y",
        "%m/%d/%Y %H:%M:%S",
        "%m/%d/%Y %H:%M",
        "%m/%d/%Y",
        "%Y/%m/%d %H:%M:%S",
        "%Y/%m/%d %H:%M",
        "%Y/%m/%d",
        "%d-%m-%Y %H:%M:%S",
        "%d-%m-%Y %H:%M",
        "%d-%m-%Y",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(date_string, fmt)
        except ValueError:
            continue

    raise ValueError(f"Unable to parse date: {date_string}")


def load_saved_locations(filename: str = "saved_locations.json") -> dict:
    """
    Load saved locations from JSON file.

    Args:
        filename: filename to load from

    Returns:
        dict: saved locations data
    """
    try:
        if os.path.exists(filename):
            with open(filename, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading saved locations: {e}")

    return {}


def save_location(location_data: dict, filename: str = "saved_locations.json") -> bool:
    """
    Save location data to JSON file.

    Args:
        location_data: location data to save
        filename: filename to save to

    Returns:
        bool: success status
    """
    try:
        # Load existing data
        saved_locations = load_saved_locations(filename)

        # Add new location
        name = location_data.get("name", "Unknown")
        saved_locations[name] = location_data

        # Save back to file
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(saved_locations, f, indent=2, ensure_ascii=False)

        return True
    except Exception as e:
        print(f"Error saving location: {e}")
        return False


def get_location_info(location_name: str) -> dict:
    """
    Get comprehensive location information.

    Args:
        location_name: name of location

    Returns:
        dict: location information
    """
    # First check saved locations
    saved_locations = load_saved_locations()
    if location_name in saved_locations:
        return saved_locations[location_name]

    # Get fresh coordinates
    lat, lon, alt, address = get_coordinates(location_name)

    if lat is None:
        return None

    # Get timezone
    timezone_name = get_timezone_for_coordinates(lat, lon)

    location_info = {
        "name": location_name,
        "latitude": lat,
        "longitude": lon,
        "altitude": alt,
        "address": address,
        "timezone": timezone_name,
    }

    # Save for future use
    save_location(location_info)

    return location_info


def validate_coordinates(latitude: float, longitude: float) -> bool:
    """
    Validate coordinate values.

    Args:
        latitude: latitude to validate
        longitude: longitude to validate

    Returns:
        bool: True if valid
    """
    if not isinstance(latitude, (int, float)) or not isinstance(
        longitude, (int, float)
    ):
        return False

    if not (-90 <= latitude <= 90):
        return False

    if not (-180 <= longitude <= 180):
        return False

    return True


def get_utc_offset(timezone_name: str, date: datetime) -> timedelta:
    """
    Get UTC offset for a timezone at a specific date.

    Args:
        timezone_name: timezone name
        date: date to check offset for

    Returns:
        timedelta: UTC offset
    """
    try:
        tz = pytz.timezone(timezone_name)
        localized_date = tz.localize(date)
        return localized_date.utcoffset()
    except Exception as e:
        print(f"Error getting UTC offset: {e}")
        return timedelta(0)


def list_common_timezones() -> list:
    """
    Get list of common timezone names.

    Returns:
        list: common timezone names
    """
    common_timezones = [
        "UTC",
        "US/Eastern",
        "US/Central",
        "US/Mountain",
        "US/Pacific",
        "Europe/London",
        "Europe/Paris",
        "Europe/Berlin",
        "Europe/Rome",
        "Europe/Madrid",
        "Europe/Stockholm",
        "Asia/Tokyo",
        "Asia/Shanghai",
        "Asia/Kolkata",
        "Australia/Sydney",
        "Australia/Melbourne",
        "America/New_York",
        "America/Chicago",
        "America/Denver",
        "America/Los_Angeles",
        "America/Toronto",
        "America/Vancouver",
        "America/Mexico_City",
        "America/Sao_Paulo",
        "America/Argentina/Buenos_Aires",
        "Africa/Cairo",
        "Africa/Johannesburg",
        "Asia/Dubai",
        "Asia/Singapore",
        "Pacific/Auckland",
    ]

    return sorted(common_timezones)


def format_coordinates(latitude: float, longitude: float) -> str:
    """
    Format coordinates for display.

    Args:
        latitude: latitude in degrees
        longitude: longitude in degrees

    Returns:
        str: formatted coordinate string
    """
    lat_dir = "N" if latitude >= 0 else "S"
    lon_dir = "E" if longitude >= 0 else "W"

    lat_abs = abs(latitude)
    lon_abs = abs(longitude)

    return f"{lat_abs:.4f}°{lat_dir}, {lon_abs:.4f}°{lon_dir}"


def distance_between_coordinates(
    lat1: float, lon1: float, lat2: float, lon2: float
) -> float:
    """
    Calculate distance between two coordinate points using Haversine formula.

    Args:
        lat1, lon1: first coordinate pair
        lat2, lon2: second coordinate pair

    Returns:
        float: distance in kilometers
    """
    from math import radians, sin, cos, sqrt, atan2

    # Convert to radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    # Earth's radius in kilometers
    R = 6371.0

    distance = R * c
    return distance


def coord_in_minutes(longitude, output_type):
    """
    Convert a celestial longitude into degrees, minutes, and seconds format.

    This function is used to translate a decimal longitude (such as the position of a planet in the ecliptic coordinate system) into a format that is more commonly used in astrological and astronomical contexts, expressing the longitude in terms of degrees, minutes, and seconds.

    Parameters:
    - longitude (float): The ecliptic longitude to be converted, in decimal degrees.
    - output_type (str): The output type ("html", "text", etc.)

    Returns:
    - str: The formatted string representing the longitude in degrees, minutes, and seconds (D°M'S'').
    """
    import os

    degrees = int(longitude)  # Extract whole degrees
    minutes = int((longitude - degrees) * 60)  # Extract whole minutes
    seconds = int(((longitude - degrees) * 60 - minutes) * 60)  # Extract whole seconds

    degree_symbol = " " if (os.name == "nt" and output_type == "html") else "°"

    neg = ""
    if minutes < 0:
        minutes = abs(minutes)
        seconds = abs(seconds)
        neg = "-"
    return f"{neg}{degrees}{degree_symbol}{minutes}'{seconds}\""
