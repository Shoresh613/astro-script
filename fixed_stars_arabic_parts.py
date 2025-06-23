"""
Fixed stars and Arabic parts calculations for the astro script.
Contains functions for calculating fixed star positions and Arabic parts.
"""

import swisseph as swe
import csv
import os
from datetime import datetime
from constants import *


def get_fixed_star_position(star_name: str, jd: float) -> tuple:
    """
    Get the position of a fixed star at a given Julian date.

    Args:
        star_name: name of the fixed star
        jd: Julian date

    Returns:
        tuple: (longitude, latitude) or None if not found
    """
    try:
        # Swiss Ephemeris uses specific star names
        star_id = swe.fixstar_name(star_name)
        if star_id:
            pos, ret_flag = swe.fixstar_ut(star_name, jd)
            return pos[0], pos[1]  # longitude, latitude
    except:
        pass

    return None, None


def read_fixed_stars(all_stars: bool = False) -> dict:
    """
    Read fixed star data from file.

    Args:
        all_stars: whether to include all stars or just astrologically significant ones

    Returns:
        dict: star data
    """
    stars = {}

    # Determine which file to read
    if all_stars:
        filename = "ephe/fixed_stars_all.csv"
    else:
        filename = "ephe/astrologically_known_fixed_stars.csv"

    if not os.path.exists(filename):
        return stars

    try:
        with open(filename, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                star_name = row.get("name", "").strip()
                if star_name:
                    stars[star_name] = {
                        "magnitude": float(row.get("magnitude", 0)),
                        "longitude": float(row.get("longitude", 0)),
                        "latitude": float(row.get("latitude", 0)),
                        "designation": row.get("designation", ""),
                        "constellation": row.get("constellation", ""),
                    }
    except Exception as e:
        print(f"Error reading fixed stars: {e}")

    return stars


def calculate_aspects_to_fixed_stars(
    planet_positions: dict, jd: float, orb: float = 2.0, all_stars: bool = False
) -> list:
    """
    Calculate aspects between planets and fixed stars.

    Args:
        planet_positions: planet position data
        jd: Julian date for star positions
        orb: orb for aspects
        all_stars: whether to use all stars or just significant ones

    Returns:
        list: list of star aspects
    """
    star_aspects = []

    # Read fixed star data
    stars = read_fixed_stars(all_stars)

    # Major aspects to check
    aspects_to_check = [
        ("Conjunction", 0),
        ("Opposition", 180),
        ("Trine", 120),
        ("Square", 90),
        ("Sextile", 60),
    ]

    for planet, planet_data in planet_positions.items():
        if planet in ["house_cusps"]:
            continue

        planet_long = planet_data["longitude"]

        for star_name, star_data in stars.items():
            # Get current star position
            star_long, star_lat = get_fixed_star_position(star_name, jd)

            if star_long is None:
                # Use stored position if current calculation fails
                star_long = star_data["longitude"]

            # Check for aspects
            for aspect_name, aspect_angle in aspects_to_check:
                diff = abs(planet_long - star_long)
                if diff > 180:
                    diff = 360 - diff

                angle_diff = abs(diff - aspect_angle)

                if angle_diff <= orb:
                    star_aspects.append(
                        {
                            "planet": planet,
                            "star": star_name,
                            "aspect": aspect_name,
                            "orb": angle_diff,
                            "planet_longitude": planet_long,
                            "star_longitude": star_long,
                            "magnitude": star_data.get("magnitude", 0),
                            "constellation": star_data.get("constellation", ""),
                        }
                    )

    # Sort by orb (tightest first)
    star_aspects.sort(key=lambda x: x["orb"])

    return star_aspects


def calculate_part_of_fortune(
    sun_pos: float, moon_pos: float, asc_pos: float, is_daytime: bool
) -> float:
    """
    Calculate the Part of Fortune.

    Args:
        sun_pos: Sun longitude
        moon_pos: Moon longitude
        asc_pos: Ascendant longitude
        is_daytime: whether it's a day chart

    Returns:
        float: Part of Fortune longitude
    """
    if is_daytime:
        # Day formula: Asc + Moon - Sun
        pof = asc_pos + moon_pos - sun_pos
    else:
        # Night formula: Asc + Sun - Moon
        pof = asc_pos + sun_pos - moon_pos

    # Normalize to 0-360 range
    return pof % 360


def calculate_part_of_spirit(
    sun_pos: float, moon_pos: float, asc_pos: float, is_daytime: bool
) -> float:
    """
    Calculate the Part of Spirit.

    Args:
        sun_pos: Sun longitude
        moon_pos: Moon longitude
        asc_pos: Ascendant longitude
        is_daytime: whether it's a day chart

    Returns:
        float: Part of Spirit longitude
    """
    if is_daytime:
        # Day formula: Asc + Sun - Moon
        pos = asc_pos + sun_pos - moon_pos
    else:
        # Night formula: Asc + Moon - Sun
        pos = asc_pos + moon_pos - sun_pos

    return pos % 360


def calculate_part_of_love(asc_pos: float, venus_pos: float, sun_pos: float) -> float:
    """
    Calculate the Part of Love.

    Args:
        asc_pos: Ascendant longitude
        venus_pos: Venus longitude
        sun_pos: Sun longitude

    Returns:
        float: Part of Love longitude
    """
    # Formula: Asc + Venus - Sun
    pol = asc_pos + venus_pos - sun_pos
    return pol % 360


def add_arabic_parts(
    date: datetime, latitude: float, longitude: float, positions: dict, output: str
) -> dict:
    """
    Calculate various Arabic parts.

    Args:
        date: date for calculation
        latitude: latitude
        longitude: longitude
        positions: planet positions
        output: output format

    Returns:
        dict: calculated Arabic parts
    """
    arabic_parts = {}

    # Get required positions
    sun_pos = positions.get("Sun", {}).get("longitude")
    moon_pos = positions.get("Moon", {}).get("longitude")
    asc_pos = positions.get("Ascendant", {}).get("longitude")
    venus_pos = positions.get("Venus", {}).get("longitude")
    mars_pos = positions.get("Mars", {}).get("longitude")
    jupiter_pos = positions.get("Jupiter", {}).get("longitude")
    saturn_pos = positions.get("Saturn", {}).get("longitude")
    mercury_pos = positions.get("Mercury", {}).get("longitude")

    if not all([sun_pos is not None, moon_pos is not None, asc_pos is not None]):
        return arabic_parts

    # Determine if it's a day chart (Sun above horizon)
    # Simplified check - in a full implementation you'd check house positions
    is_daytime = True  # Default assumption

    # Calculate basic parts
    arabic_parts["Part of Fortune"] = calculate_part_of_fortune(
        sun_pos, moon_pos, asc_pos, is_daytime
    )

    arabic_parts["Part of Spirit"] = calculate_part_of_spirit(
        sun_pos, moon_pos, asc_pos, is_daytime
    )

    if venus_pos is not None:
        arabic_parts["Part of Love"] = calculate_part_of_love(
            asc_pos, venus_pos, sun_pos
        )

    # Additional parts if planets are available
    if mars_pos is not None:
        # Part of Passion: Asc + Mars - Venus
        if venus_pos is not None:
            passion = asc_pos + mars_pos - venus_pos
            arabic_parts["Part of Passion"] = passion % 360

    if jupiter_pos is not None:
        # Part of Success: Asc + Jupiter - Sun
        success = asc_pos + jupiter_pos - sun_pos
        arabic_parts["Part of Success"] = success % 360

    if saturn_pos is not None:
        # Part of Karma: Asc + Saturn - Sun
        karma = asc_pos + saturn_pos - sun_pos
        arabic_parts["Part of Karma"] = karma % 360

    if mercury_pos is not None:
        # Part of Commerce: Asc + Mercury - Sun
        commerce = asc_pos + mercury_pos - sun_pos
        arabic_parts["Part of Commerce"] = commerce % 360

    return arabic_parts


def get_decan_ruler(
    longitude: float, zodiac_sign: str, classic_rulers: bool = False
) -> str:
    """
    Get the decan ruler for a position.

    Args:
        longitude: longitude in sign
        zodiac_sign: zodiac sign name
        classic_rulers: use classical rulers

    Returns:
        str: decan ruler planet
    """
    # Each decan is 10 degrees
    degree_in_sign = longitude % 30

    if degree_in_sign < 10:
        decan = 1
    elif degree_in_sign < 20:
        decan = 2
    else:
        decan = 3

    # Decan rulers by sign and decan (traditional system)
    decan_rulers = {
        "Aries": ["Mars", "Sun", "Jupiter"],
        "Taurus": ["Venus", "Mercury", "Saturn"],
        "Gemini": ["Mercury", "Venus", "Uranus"],
        "Cancer": ["Moon", "Mars", "Jupiter"],
        "Leo": ["Sun", "Jupiter", "Mars"],
        "Virgo": ["Mercury", "Saturn", "Venus"],
        "Libra": ["Venus", "Uranus", "Mercury"],
        "Scorpio": ["Mars", "Neptune", "Moon"],
        "Sagittarius": ["Jupiter", "Mars", "Sun"],
        "Capricorn": ["Saturn", "Venus", "Mercury"],
        "Aquarius": ["Uranus", "Mercury", "Venus"],
        "Pisces": ["Neptune", "Moon", "Mars"],
    }

    if classic_rulers:
        # Classical rulers (no outer planets)
        classical_decan_rulers = {
            "Aries": ["Mars", "Sun", "Jupiter"],
            "Taurus": ["Venus", "Mercury", "Saturn"],
            "Gemini": ["Mercury", "Venus", "Saturn"],
            "Cancer": ["Moon", "Mars", "Jupiter"],
            "Leo": ["Sun", "Jupiter", "Mars"],
            "Virgo": ["Mercury", "Saturn", "Venus"],
            "Libra": ["Venus", "Saturn", "Mercury"],
            "Scorpio": ["Mars", "Jupiter", "Moon"],
            "Sagittarius": ["Jupiter", "Mars", "Sun"],
            "Capricorn": ["Saturn", "Venus", "Mercury"],
            "Aquarius": ["Saturn", "Mercury", "Venus"],
            "Pisces": ["Jupiter", "Moon", "Mars"],
        }
        rulers = classical_decan_rulers
    else:
        rulers = decan_rulers

    sign_rulers = rulers.get(zodiac_sign, ["Unknown", "Unknown", "Unknown"])
    return sign_rulers[decan - 1]


def moon_phase(date: datetime) -> dict:
    """
    Calculate moon phase information.

    Args:
        date: date for calculation

    Returns:
        dict: moon phase data
    """
    from astro_calculations import (
        get_illuminated_fraction_of_moon,
        julian_date_from_unix_time,
    )
    import time

    # Convert to Julian date
    timestamp = time.mktime(date.timetuple())
    jd = julian_date_from_unix_time(timestamp)

    # Get illuminated fraction
    illumination = get_illuminated_fraction_of_moon(jd)
    illumination_percent = illumination * 100

    # Determine phase name
    if illumination_percent < 1:
        phase_name = "New Moon"
    elif illumination_percent < 25:
        phase_name = "Waxing Crescent"
    elif illumination_percent < 50:
        phase_name = "First Quarter"
    elif illumination_percent < 75:
        phase_name = "Waxing Gibbous"
    elif illumination_percent < 99:
        phase_name = "Full Moon"
    else:
        phase_name = "Waning Gibbous"

    return {
        "phase": phase_name,
        "illumination": illumination_percent,
        "julian_date": jd,
    }


def datetime_ruled_by(date):
    """
    Calculate planetary hours and rulers for a datetime - matches original exactly.

    Args:
        date: datetime to check

    Returns:
        tuple: (weekday_name, day_planet, hour_planet)
    """
    # Chaldean order of the planets
    planets = ["Saturn", "Jupiter", "Mars", "Sun", "Venus", "Mercury", "Moon"]

    # Starting with Saturn on the first hour of the first day (Saturday)
    current_planet_index = 0

    first_hour_planets = []
    for day in range(7):
        first_hour_planets.append(planets[current_planet_index % 7])
        # Move to the planet of the 25th hour, which will be the first hour of the next day
        current_planet_index += 24

    # Mapping the first hour planets to their corresponding weekdays
    weekdays = [
        "Saturday",
        "Sunday",
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
    ]
    weekday_planet_mapping = dict(zip(weekdays, first_hour_planets))

    day_of_week = (date.weekday() - 5) % 7  # Adjust the weekday to start from Saturday

    # Get the weekday name and the planet ruling that day
    weekday_name = weekdays[day_of_week]
    day_planet = weekday_planet_mapping[weekday_name]

    # Calculate the planetary hour
    # Assuming the day starts at 6:00 AM with the first hour ruled by the day's planet
    hour_offset = (
        date.hour - 6
    ) % 24  # Adjust hour for planetary hours starting at 6 AM
    if hour_offset < 0:
        hour_offset += 24  # Adjust for hours before 6 AM

    # Find the planet for the given hour
    hour_planet_index = (planets.index(day_planet) + hour_offset) % 7
    hour_planet = planets[hour_planet_index]

    return weekday_name, day_planet, hour_planet
