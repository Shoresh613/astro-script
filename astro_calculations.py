"""
Astronomical calculation functions for the astro script.
Contains core functions for calculating planet positions, houses, and astronomical data.
"""

from datetime import datetime, timedelta
import pytz
import os
from math import sin, cos, radians, exp, pi
import swisseph as swe

# Import constants
from constants import *

# Set ephemeris path
EPHE = os.getenv("PRODUCTION_EPHE")
if EPHE:
    swe.set_ephe_path(EPHE)
else:
    if os.name == "nt":
        swe.set_ephe_path(".\ephe")
    else:
        swe.set_ephe_path("./ephe")


def get_delta_t(date):
    """
    Calculate Delta T for a given date.

    Args:
        date: datetime object

    Returns:
        float: Delta T value
    """
    # Convert datetime to Julian date
    year = date.year
    month = date.month
    day = date.day
    hour = date.hour + date.minute / 60.0 + date.second / 3600.0

    jd = swe.julday(year, month, day, hour)
    delta_t = swe.deltat(jd)
    return delta_t


def get_pluto_ecliptic(
    date: datetime, latitude: float, longitude: float, altitude: float = 0
):
    """
    Calculate Pluto's ecliptic position.

    Args:
        date: datetime object
        latitude: latitude in degrees
        longitude: longitude in degrees
        altitude: altitude in meters

    Returns:
        tuple: (longitude, latitude) in degrees
    """
    year = date.year
    month = date.month
    day = date.day
    hour = date.hour + date.minute / 60.0 + date.second / 3600.0

    jd = swe.julday(year, month, day, hour)

    # Set geographic location
    swe.set_topo(longitude, latitude, altitude)

    # Calculate Pluto position
    pluto_pos, ret_flag = swe.calc_ut(jd, swe.PLUTO)

    return pluto_pos[0], pluto_pos[1]


def find_next_same_degree(
    start_date: datetime,
    longitude: float,
    latitude: float,
    altitude: float,
    planet: int,
    target_degree: float,
    center: str = "geocentric",
):
    """
    Find the next time a planet reaches a specific degree.

    Args:
        start_date: Starting datetime
        longitude: longitude in degrees
        latitude: latitude in degrees
        altitude: altitude in meters
        planet: Swiss ephemeris planet constant
        target_degree: target degree to find
        center: calculation center (geocentric/heliocentric)

    Returns:
        datetime: when planet reaches target degree
    """

    def get_next_degree(next_dt, longitude, latitude, altitude, center):
        year = next_dt.year
        month = next_dt.month
        day = next_dt.day
        hour = next_dt.hour + next_dt.minute / 60.0 + next_dt.second / 3600.0

        jd = swe.julday(year, month, day, hour)

        if center == "heliocentric":
            flag = swe.FLG_HELIOCENTRIC
        else:
            flag = swe.FLG_GEOCENTRIC
            swe.set_topo(longitude, latitude, altitude)

        pos, ret_flag = swe.calc_ut(jd, planet, flag)
        return pos[0]

    # Initial setup
    current_date = start_date
    max_iterations = 365 * 5  # 5 years max
    iteration = 0

    while iteration < max_iterations:
        current_pos = get_next_degree(
            current_date, longitude, latitude, altitude, center
        )

        # Check if we've reached the target degree (within 0.1 degree)
        if abs(current_pos - target_degree) < 0.1:
            return current_date

        # Move forward by 1 day
        current_date += timedelta(days=1)
        iteration += 1

    # If not found, return None
    return None


def convert_to_utc(local_datetime, local_timezone):
    """
    Convert local datetime to UTC.

    Args:
        local_datetime: datetime in local timezone
        local_timezone: pytz timezone object

    Returns:
        datetime: UTC datetime
    """
    if local_timezone is None:
        local_timezone = pytz.utc

    if isinstance(local_timezone, str):
        local_timezone = pytz.timezone(local_timezone)

    # Localize the datetime to the specified timezone
    localized_dt = local_timezone.localize(local_datetime)

    # Convert to UTC
    utc_dt = localized_dt.astimezone(pytz.utc)

    return utc_dt.replace(tzinfo=None)


def calculate_individual_house_position(
    planet_longitude: float, house_cusps: list, house_system: str = "P"
) -> int:
    """
    Calculate which house a planet is in based on its longitude.

    Args:
        planet_longitude: planet's ecliptic longitude
        house_cusps: list of 12 house cusp positions
        house_system: house system to use

    Returns:
        int: house number (1-12)
    """
    for house in range(12):
        next_house = (house + 1) % 12
        cusp = house_cusps[house]
        next_cusp = house_cusps[next_house]

        if cusp < next_cusp:
            if cusp <= planet_longitude < next_cusp:
                return house + 1
        else:  # Crosses 0 degrees
            if planet_longitude >= cusp or planet_longitude < next_cusp:
                return house + 1

    return 1  # Default to first house


def calculate_house_positions(
    date: datetime,
    latitude: float,
    longitude: float,
    altitude: float = 0,
    house_system: str = "P",
    center: str = "geocentric",
) -> tuple:
    """
    Calculate house positions and cusps.

    Args:
        date: datetime for calculation
        latitude: latitude in degrees
        longitude: longitude in degrees
        altitude: altitude in meters
        house_system: house system to use
        center: calculation center

    Returns:
        tuple: (house_cusps, ascendant, midheaven)
    """
    year = date.year
    month = date.month
    day = date.day
    hour = date.hour + date.minute / 60.0 + date.second / 3600.0

    jd = swe.julday(year, month, day, hour)

    # Set geographic location
    swe.set_topo(longitude, latitude, altitude)

    # Calculate houses
    houses, ascmc = swe.houses(jd, latitude, longitude, house_system.encode())

    return houses, ascmc[0], ascmc[1]  # houses, ASC, MC


def longitude_to_zodiac(longitude: float, output: str = "text") -> str:
    """
    Convert ecliptic longitude to zodiac sign and degree.

    Args:
        longitude: ecliptic longitude in degrees
        output: output format (text/html)

    Returns:
        str: formatted zodiac position
    """
    signs = [
        "Aries",
        "Taurus",
        "Gemini",
        "Cancer",
        "Leo",
        "Virgo",
        "Libra",
        "Scorpio",
        "Sagittarius",
        "Capricorn",
        "Aquarius",
        "Pisces",
    ]

    # Normalize longitude to 0-360 range
    longitude = longitude % 360

    # Calculate sign and degree
    sign_index = int(longitude // 30)
    degree = longitude % 30

    # Format degree
    deg = int(degree)
    min_val = int((degree - deg) * 60)
    sec = int(((degree - deg) * 60 - min_val) * 60)

    if output == "html":
        degree_symbol = "&deg;"
    else:
        degree_symbol = "°"

    return f"{deg}{degree_symbol}{min_val:02d}'{sec:02d}\" {signs[sign_index]}"


def is_planet_retrograde(planet: int, jd: float) -> bool:
    """
    Check if a planet is retrograde at a given Julian date.

    Args:
        planet: Swiss ephemeris planet constant
        jd: Julian date

    Returns:
        bool: True if retrograde
    """
    # Calculate planet position
    pos, ret_flag = swe.calc_ut(jd, planet)

    # Calculate position 1 day later
    pos_later, ret_flag_later = swe.calc_ut(jd + 1, planet)

    # Check if longitude is decreasing (retrograde)
    longitude_diff = pos_later[0] - pos[0]

    # Handle crossing 0 degrees
    if longitude_diff > 180:
        longitude_diff -= 360
    elif longitude_diff < -180:
        longitude_diff += 360

    return longitude_diff < 0


def calculate_planet_positions(
    date: datetime,
    latitude: float,
    longitude: float,
    altitude: float = 0,
    center: str = "geocentric",
    include_asteroids: bool = False,
    include_fixed_stars: bool = False,
) -> dict:
    """
    Calculate positions of all planets and celestial bodies.

    Args:
        date: datetime for calculation
        latitude: latitude in degrees
        longitude: longitude in degrees
        altitude: altitude in meters
        center: calculation center (geocentric/heliocentric)
        include_asteroids: whether to include asteroids
        include_fixed_stars: whether to include fixed stars

    Returns:
        dict: planet positions and data
    """
    year = date.year
    month = date.month
    day = date.day
    hour = date.hour + date.minute / 60.0 + date.second / 3600.0
    jd = swe.julday(year, month, day, hour)

    # Set calculation flags
    if center == "heliocentric":
        flag = swe.FLG_HELCTR
    else:
        flag = swe.FLG_TOPOCTR if center == "topocentric" else 0
        if center == "topocentric":
            swe.set_topo(longitude, latitude, altitude)

    positions = {}  # Calculate main planets
    planet_list = [
        (swe.SUN, "Sun"),
        (swe.MOON, "Moon"),
        (swe.MERCURY, "Mercury"),
        (swe.VENUS, "Venus"),
        (swe.MARS, "Mars"),
        (swe.JUPITER, "Jupiter"),
        (swe.SATURN, "Saturn"),
        (swe.URANUS, "Uranus"),
        (swe.NEPTUNE, "Neptune"),
        (swe.PLUTO, "Pluto"),
        (swe.CHIRON, "Chiron"),
        (swe.MEAN_APOG, "Lilith"),
        (swe.TRUE_NODE, "North Node"),
    ]

    for planet_id, planet_name in planet_list:
        try:
            pos, ret_flag = swe.calc_ut(jd, planet_id, flag)
            retrograde = is_planet_retrograde(planet_id, jd)

            positions[planet_name] = {
                "longitude": pos[0],
                "latitude": pos[1],
                "distance": pos[2],
                "speed": pos[3],
                "retrograde": retrograde,
            }
        except Exception as e:
            print(f"Error calculating {planet_name}: {e}")

    # Add South Node (opposite of North Node)
    if "North Node" in positions:
        positions["South Node"] = {
            "longitude": (positions["North Node"]["longitude"] + 180) % 360,
            "latitude": 0,
            "distance": 0,
            "speed": 0,
            "retrograde": False,
        }

    # Calculate house cusps and angles
    try:
        houses, ascmc = swe.houses(jd, latitude, longitude, b"P")
        positions["Ascendant"] = {
            "longitude": ascmc[0],
            "latitude": 0,
            "distance": 0,
            "speed": 0,
            "retrograde": False,
        }
        positions["Midheaven"] = {
            "longitude": ascmc[1],
            "latitude": 0,
            "distance": 0,
            "speed": 0,
            "retrograde": False,
        }
        positions["Descendant"] = {
            "longitude": (ascmc[0] + 180) % 360,
            "latitude": 0,
            "distance": 0,
            "speed": 0,
            "retrograde": False,
        }
        positions["IC"] = {
            "longitude": (ascmc[1] + 180) % 360,
            "latitude": 0,
            "distance": 0,
            "speed": 0,
            "retrograde": False,
        }

        # House cusps are handled separately in calculate_house_positions()

    except Exception as e:
        print(f"Error calculating houses: {e}")

    return positions


def calculate_sunrise_sunset(year: int, month: int, day: int, geopos: tuple) -> tuple:
    """
    Calculate sunrise and sunset times.

    Args:
        year: year
        month: month
        day: day
        geopos: (longitude, latitude, altitude)

    Returns:
        tuple: (sunrise_jd, sunset_jd) in Julian dates
    """
    longitude, latitude, altitude = geopos
    jd = swe.julday(year, month, day, 12.0)  # Noon

    # Calculate sunrise
    sunrise_result = swe.rise_trans(
        jd, swe.SUN, longitude, latitude, altitude, rsmi=swe.CALC_RISE
    )
    sunrise_jd = sunrise_result[1][0] if sunrise_result[0] == swe.OK else None

    # Calculate sunset
    sunset_result = swe.rise_trans(
        jd, swe.SUN, longitude, latitude, altitude, rsmi=swe.CALC_SET
    )
    sunset_jd = sunset_result[1][0] if sunset_result[0] == swe.OK else None

    return sunrise_jd, sunset_jd


def julian_date_from_unix_time(t: float) -> float:
    """Convert Unix timestamp to Julian date."""
    return t / 86400.0 + 2440587.5


def unix_time_from_julian_date(jd: float) -> float:
    """Convert Julian date to Unix timestamp."""
    return (jd - 2440587.5) * 86400.0


def constrain(d: float) -> float:
    """Constrain degrees to 0-360 range."""
    return d - 360 * int(d / 360)


def get_illuminated_fraction_of_moon(jd: float) -> float:
    """
    Calculate the illuminated fraction of the Moon.

    Args:
        jd: Julian date

    Returns:
        float: Illuminated fraction (0-1)
    """
    # Get Moon and Sun positions
    moon_pos, _ = swe.calc_ut(jd, swe.MOON)
    sun_pos, _ = swe.calc_ut(jd, swe.SUN)

    # Calculate phase angle
    moon_lon = moon_pos[0]
    sun_lon = sun_pos[0]

    phase_angle = abs(moon_lon - sun_lon)
    if phase_angle > 180:
        phase_angle = 360 - phase_angle

    # Calculate illuminated fraction
    illuminated_fraction = (1 + cos(radians(phase_angle))) / 2

    return illuminated_fraction
