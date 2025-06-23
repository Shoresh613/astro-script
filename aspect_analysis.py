"""
Aspect analysis functions for the astro script.
Contains functions for calculating, scoring, and analyzing astrological aspects.
"""

from math import sin, cos, radians, exp, pi
from constants import *


def calculate_adjustment_factor(
    magnitude: float, min_factor: float = 0.8, max_factor: float = 1.2
) -> float:
    """
    Calculate the adjustment factor based on the magnitude using a logistic function.

    Args:
        magnitude: The magnitude value to adjust
        min_factor: The minimum adjustment factor
        max_factor: The maximum adjustment factor

    Returns:
        float: The clamped adjustment factor
    """
    # Logistic function parameters
    A = max_factor - min_factor  # Controls the range (max_factor - min_factor)
    B = 0.4  # Controls the steepness
    C = 3.45  # Shifts the function horizontally (based on median magnitude)
    D = 0.5  # Shifts the function vertically (min_factor)

    # Calculate the adjustment factor using the logistic function
    adjustment_factor = A / (1 + exp(-B * (magnitude - C))) + D

    # Clamp the adjustment factor to the specified range
    adjustment_factor = max(min(adjustment_factor, max_factor), min_factor)

    return adjustment_factor


def angle_influence(angle: float) -> float:
    """
    Calculate the influence of an aspect based on its angle difference from exactness.

    Args:
        angle: angle difference from exact aspect

    Returns:
        float: influence factor
    """
    # Convert angle to absolute value for symmetry
    angle = abs(angle)
    tweaking_factor = 0.8  # Factor to adjust the influence of angles

    if angle <= 3:
        return (2 - angle / 3) * tweaking_factor
    elif angle <= 10:
        return (1 - (angle - 3) / 7) * tweaking_factor
    else:
        return 0


def calculate_aspect_score(aspect: str, angle: float, magnitude: float = None) -> float:
    """
    Calculate the score for an aspect based on type, angle, and optional magnitude.

    Args:
        aspect: aspect name (e.g., "Conjunction", "Trine")
        angle: angle difference from exact aspect
        magnitude: optional magnitude for adjustment

    Returns:
        float: calculated aspect score
    """
    # Get base score from aspect type
    all_aspects = {**MAJOR_ASPECTS, **MINOR_ASPECTS}

    if aspect not in all_aspects:
        return 0

    base_score = all_aspects[aspect].get("Score", 0)

    # Apply angle influence
    angle_factor = angle_influence(angle)

    # Apply magnitude adjustment if provided
    if magnitude is not None:
        magnitude_factor = calculate_adjustment_factor(magnitude)
    else:
        magnitude_factor = 1.0

    # Calculate final score
    final_score = base_score * angle_factor * magnitude_factor

    return round(final_score, 2)


def check_aspect(
    planet_long: float, star_long: float, aspect_angle: float, orb: float
) -> dict:
    """
    Check if two celestial bodies form a specific aspect within orb.

    Args:
        planet_long: longitude of first body
        star_long: longitude of second body
        aspect_angle: the aspect angle to check for
        orb: allowable orb

    Returns:
        dict: aspect information if found, None otherwise
    """
    # Calculate angular difference
    diff = abs(planet_long - star_long)
    if diff > 180:
        diff = 360 - diff

    # Check if within orb of aspect
    aspect_diff = abs(diff - aspect_angle)

    if aspect_diff <= orb:
        return {
            "angle_diff": aspect_diff,
            "exact_angle": diff,
            "within_orb": True,
            "orb_used": orb,
        }

    return None


def calculate_aspect_duration(
    planet_positions: dict, planet: str, degrees_to_travel: float
) -> str:
    """
    Calculate how long it takes for a planet to travel a certain number of degrees.

    Args:
        planet_positions: dictionary of planet positions with speeds
        planet: planet name
        degrees_to_travel: degrees to travel

    Returns:
        str: formatted duration string
    """
    if planet not in planet_positions:
        return "Unknown"

    speed = planet_positions[planet].get("speed", 0)

    if speed == 0:
        return "Stationary"

    # Calculate days
    days = abs(degrees_to_travel / speed)

    if days < 1:
        hours = days * 24
        return f"{hours:.1f}h"
    elif days < 30:
        return f"{days:.1f}d"
    elif days < 365:
        months = days / 30.44
        return f"{months:.1f}m"
    else:
        years = days / 365.25
        return f"{years:.1f}y"


def find_exact_aspects_in_timeframe(
    start_date,
    end_date,
    latitude: float,
    longitude: float,
    altitude: float,
    orbs: dict,
    center: str = "geocentric",
    step_days: float = 1,
    output_type: str = "text",
) -> list:
    """
    Find exact aspects within a specific timeframe.

    Args:
        start_date: start datetime
        end_date: end datetime
        latitude: latitude in degrees
        longitude: longitude in degrees
        altitude: altitude in meters
        orbs: orb dictionary
        center: calculation center
        step_days: step size in days
        output_type: output format

    Returns:
        list: list of exact aspects found
    """
    from datetime import timedelta
    from astro_calculations import calculate_planet_positions

    exact_aspects = []
    current_date = start_date

    while current_date <= end_date:
        # Calculate positions for current date
        positions = calculate_planet_positions(
            current_date, latitude, longitude, altitude, center
        )

        # Check for aspects between all planet pairs
        planets = list(positions.keys())

        for i, planet1 in enumerate(planets):
            if planet1 in ["house_cusps"]:
                continue

            for planet2 in planets[i + 1 :]:
                if planet2 in ["house_cusps"]:
                    continue

                # Calculate aspect
                diff = abs(
                    positions[planet1]["longitude"] - positions[planet2]["longitude"]
                )
                if diff > 180:
                    diff = 360 - diff

                # Check major aspects
                for aspect_name, aspect_data in MAJOR_ASPECTS.items():
                    aspect_angle = aspect_data["Degrees"]
                    orb = orbs.get("Major", 8)

                    if abs(diff - aspect_angle) <= 0.1:  # Very tight orb for "exact"
                        exact_aspects.append(
                            {
                                "date": current_date,
                                "planet1": planet1,
                                "planet2": planet2,
                                "aspect": aspect_name,
                                "angle_diff": abs(diff - aspect_angle),
                                "longitude1": positions[planet1]["longitude"],
                                "longitude2": positions[planet2]["longitude"],
                            }
                        )

        current_date += timedelta(days=step_days)

    return exact_aspects


def calculate_planetary_aspects(
    planet_positions: dict, orbs: dict, output_type: str, aspect_types: list = None
) -> dict:
    """
    Calculate all planetary aspects in a chart.

    Args:
        planet_positions: dictionary of planet positions
        orbs: orb values for different aspect types
        output_type: output format
        aspect_types: list of aspect types to include

    Returns:
        dict: calculated aspects
    """
    if aspect_types is None:
        aspect_types = ["major", "minor"]

    aspects = {}
    planets = list(planet_positions.keys())

    # Remove non-planet keys
    planets = [p for p in planets if p not in ["house_cusps"]]

    for i, planet1 in enumerate(planets):
        for planet2 in planets[i + 1 :]:
            # Calculate angular difference
            long1 = planet_positions[planet1]["longitude"]
            long2 = planet_positions[planet2]["longitude"]

            diff = abs(long1 - long2)
            if diff > 180:
                diff = 360 - diff

            # Check major aspects
            if "major" in aspect_types:
                for aspect_name, aspect_data in MAJOR_ASPECTS.items():
                    aspect_angle = aspect_data["Degrees"]
                    orb = orbs.get("Major", 8)

                    angle_diff = abs(diff - aspect_angle)
                    if angle_diff <= orb:
                        key = (planet1, planet2)
                        aspects[key] = {
                            "aspect_name": aspect_name,
                            "angle_diff": angle_diff,
                            "exact_angle": diff,
                            "orb_used": orb,
                            "is_major": True,
                            "score": calculate_aspect_score(aspect_name, angle_diff),
                        }
                        break  # Only one aspect per planet pair

            # Check minor aspects if no major aspect found
            if "minor" in aspect_types and (planet1, planet2) not in aspects:
                for aspect_name, aspect_data in MINOR_ASPECTS.items():
                    aspect_angle = aspect_data["Degrees"]
                    orb = orbs.get("Minor", 4)

                    angle_diff = abs(diff - aspect_angle)
                    if angle_diff <= orb:
                        key = (planet1, planet2)
                        aspects[key] = {
                            "aspect_name": aspect_name,
                            "angle_diff": angle_diff,
                            "exact_angle": diff,
                            "orb_used": orb,
                            "is_major": False,
                            "score": calculate_aspect_score(aspect_name, angle_diff),
                        }
                        break  # Only one aspect per planet pair

    return aspects


def calculate_aspects_takes_two(
    positions1: dict, positions2: dict, orbs: dict, aspect_types: list = None
) -> dict:
    """
    Calculate aspects between two sets of planet positions (e.g., synastry, transits).

    Args:
        positions1: first set of planet positions
        positions2: second set of planet positions
        orbs: orb values
        aspect_types: aspect types to include

    Returns:
        dict: calculated aspects between the two charts
    """
    if aspect_types is None:
        aspect_types = ["major", "minor"]

    aspects = {}

    planets1 = [p for p in positions1.keys() if p not in ["house_cusps"]]
    planets2 = [p for p in positions2.keys() if p not in ["house_cusps"]]

    for planet1 in planets1:
        for planet2 in planets2:
            # Calculate angular difference
            long1 = positions1[planet1]["longitude"]
            long2 = positions2[planet2]["longitude"]

            diff = abs(long1 - long2)
            if diff > 180:
                diff = 360 - diff

            # Check major aspects
            if "major" in aspect_types:
                for aspect_name, aspect_data in MAJOR_ASPECTS.items():
                    aspect_angle = aspect_data["Degrees"]
                    orb = orbs.get("Major", 8)

                    angle_diff = abs(diff - aspect_angle)
                    if angle_diff <= orb:
                        key = (planet1, planet2)
                        aspects[key] = {
                            "aspect_name": aspect_name,
                            "angle_diff": angle_diff,
                            "exact_angle": diff,
                            "orb_used": orb,
                            "is_major": True,
                            "score": calculate_aspect_score(aspect_name, angle_diff),
                        }
                        break

            # Check minor aspects if no major aspect found
            if "minor" in aspect_types and (planet1, planet2) not in aspects:
                for aspect_name, aspect_data in MINOR_ASPECTS.items():
                    aspect_angle = aspect_data["Degrees"]
                    orb = orbs.get("Minor", 4)

                    angle_diff = abs(diff - aspect_angle)
                    if angle_diff <= orb:
                        key = (planet1, planet2)
                        aspects[key] = {
                            "aspect_name": aspect_name,
                            "angle_diff": angle_diff,
                            "exact_angle": diff,
                            "orb_used": orb,
                            "is_major": False,
                            "score": calculate_aspect_score(aspect_name, angle_diff),
                        }
                        break

    return aspects


def coord_in_minutes(longitude: float, output_type: str) -> str:
    """
    Convert longitude coordinate to minutes format.

    Args:
        longitude: longitude in degrees
        output_type: output format

    Returns:
        str: formatted coordinate string
    """
    degree_symbol = "&deg;" if output_type == "html" else "°"

    # Convert to absolute value
    abs_long = abs(longitude)

    # Extract degrees and minutes
    degrees = int(abs_long)
    minutes = (abs_long - degrees) * 60

    return f"{degrees}{degree_symbol}{minutes:05.2f}'"
