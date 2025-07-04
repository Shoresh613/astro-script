import swisseph as swe
from datetime import datetime, timedelta
import pytz
import os
import sys
import argparse
from math import sin, cos, radians, exp, pi
from geopy.geocoders import Nominatim
import requests
from tabulate import tabulate, SEPARATING_LINE

try:
    from . import version
    from . import db_manager
except:
    import version
    import db_manager
import csv
from colorama import init, Fore, Style
import copy
import json
from collections import OrderedDict

try:
    from timezonefinder import TimezoneFinder

    tz_finder_installed = True
except:
    tz_finder_installed = False

EPHE = os.getenv("PRODUCTION_EPHE")
if EPHE:
    swe.set_ephe_path(EPHE)
else:
    if os.name == "nt":
        swe.set_ephe_path(".\ephe")
    else:
        swe.set_ephe_path("./ephe")

# Initialize database
db_manager.initialize_db()

############### Constants ###############
ASPECT_TYPES = {
    "Conjunction": 0,
    "Opposition": 180,
    "Trine": 120,
    "Square": 90,
    "Sextile": 60,
}
MINOR_ASPECT_TYPES = {
    "Quincunx": 150,
    "Semi-Sextile": 30,
    "Semi-Square": 45,
    "Quintile": 72,
    "Bi-Quintile": 144,
    "Sesqui-Square": 135,
    "Septile": 51.4285714,
    "Novile": 40,
    "Decile": 36,
}
MAJOR_ASPECTS = {
    "Conjunction": {
        "Degrees": 0,
        "Score": 40,
        "Comment": "Impactful, varies by planets involved.",
    },
    "Opposition": {
        "Degrees": 180,
        "Score": 10,
        "Comment": "Polarities needing integration.",
    },
    "Square": {"Degrees": 90, "Score": 15, "Comment": "Tension and obstacles."},
    "Trine": {"Degrees": 120, "Score": 90, "Comment": "Promotes ease and talents."},
    "Sextile": {"Degrees": 60, "Score": 80, "Comment": "Opportunities and support."},
}

MINOR_ASPECTS = {
    "Semi-Square": {
        "Degrees": 45,
        "Score": 25,
        "Comment": "Friction and minor challenges.",
    },
    "Sesqui-Square": {
        "Degrees": 135,
        "Score": 20,
        "Comment": "Less intense square, irritation.",
    },
    "Semi-Sextile": {
        "Degrees": 30,
        "Score": 70,
        "Comment": "Slightly beneficial, subtle.",
    },
    "Quincunx": {
        "Degrees": 150,
        "Score": 30,
        "Comment": "Adjustment and misunderstandings.",
    },
    "Quintile": {"Degrees": 72, "Score": 75, "Comment": "Creativity and talent."},
    "Bi-Quintile": {
        "Degrees": 144,
        "Score": 75,
        "Comment": "Creative expression, like quintile.",
    },
    "Septile": {
        "Degrees": 51.4285714,
        "Score": 60,
        "Comment": "Spiritual insights, less tangible.",
    },
    "Novile": {
        "Degrees": 40,
        "Score": 65,
        "Comment": "Spiritual insights, harmonious.",
    },
    "Decile": {
        "Degrees": 36,
        "Score": 50,
        "Comment": "Growth opportunities, mild challenges.",
    },
}

ALL_ASPECTS = {**MAJOR_ASPECTS.copy(), **MINOR_ASPECTS}

# Dictionaries for hard and soft aspects based on the scores
HARD_ASPECTS = {name: info for name, info in ALL_ASPECTS.items() if info["Score"] < 50}
SOFT_ASPECTS = {name: info for name, info in ALL_ASPECTS.items() if info["Score"] >= 50}

# Movement per day for each planet in degrees
OFF_BY = {
    "Sun": 1,
    "Moon": 13.2,
    "Mercury": 1.2,
    "Venus": 1.2,
    "Earth": 1,
    "Mars": 0.5,
    "Jupiter": 0.2,
    "Saturn": 0.1,
    "Uranus": 0.04,
    "Neptune": 0.03,
    "Pluto": 0.01,
    "Chiron": 0.02,
    "North Node": 0.05,
    "South Node": 0.05,
    "True Node": 0.05,
    "Lilith": 0.05,
    "Ascendant": 360,
    "Midheaven": 360,
    "IC": 360,
    "DC": 360,
    "Juno": 0.1,
    "Vesta": 0.12,
    "Pallas": 0.09,
    "Pholus": 0.06,
    "Ceres": 0.08,
}

ALWAYS_EXCLUDE_IF_NO_TIME = [
    "Ascendant",
    "Midheaven",
    "IC",
    "DC",
]  # Aspects that are always excluded if no time of day is specified
HOUSE_SYSTEMS = {
    "Placidus": "P",
    "Koch": "K",
    "Porphyrius": "O",
    "Regiomontanus": "R",
    "Campanus": "C",
    "Equal (Ascendant cusp 1)": "A",
    "Equal (Aries cusp 1)": "E",
    "Vehlow equal": "V",
    "Axial rotation system/Meridian system/Zariel system": "X",
    "Horizon/Azimuthal system": "H",
    "Polich/Page/Topocentric": "T",
    "Alcabitius": "B",
    "Gauquelin sectors": "G",
    "Sripati": "S",
    "Morinus": "M",
}

PLANETS = {
    "Sun": swe.SUN,
    "Moon": swe.MOON,
    "Mercury": swe.MERCURY,
    "Venus": swe.VENUS,
    "Mars": swe.MARS,
    "Jupiter": swe.JUPITER,
    "Saturn": swe.SATURN,
    "Uranus": swe.URANUS,
    "Neptune": swe.NEPTUNE,
    "Pluto": swe.PLUTO,
    "Chiron": swe.CHIRON,
    "Lilith": swe.MEAN_APOG,
    "North Node": swe.TRUE_NODE,
}

PLANET_RETURN_DICT = {
    "Sun": {"constant": swe.SUN, "orbital_period_days": 365.25},
    "Moon": {"constant": swe.MOON, "orbital_period_days": 27.32},
    "Mercury": {"constant": swe.MERCURY, "orbital_period_days": 87.97},
    "Venus": {"constant": swe.VENUS, "orbital_period_days": 224.70},
    "Earth": {"constant": swe.EARTH, "orbital_period_days": 365},
    "Mars": {"constant": swe.MARS, "orbital_period_days": 686.98},  # 687 days
    "Jupiter": {
        "constant": swe.JUPITER,
        "orbital_period_days": 4332.59,  # (11.86 years)
    },
    "Saturn": {
        "constant": swe.SATURN,
        "orbital_period_days": 10759.22,  # (29.46 years)
    },
    "Uranus": {
        "constant": swe.URANUS,
        "orbital_period_days": 30685.49,  # (84.01 years)
    },
    "Neptune": {
        "constant": swe.NEPTUNE,
        "orbital_period_days": 60190.03,  # (164.8 years)
    },
    "Pluto": {"constant": swe.PLUTO, "orbital_period_days": 90560.00},  # (248 years)
}

ASTEROIDS = {
    "Ceres": swe.CERES,
    "Pholus": swe.PHOLUS,
    "Pallas": swe.PALLAS,
    "Juno": swe.JUNO,
    "Vesta": swe.VESTA,
}

ZODIAC_ELEMENTS = {
    "Aries": "Fire",
    "Taurus": "Earth",
    "Gemini": "Air",
    "Cancer": "Water",
    "Leo": "Fire",
    "Virgo": "Earth",
    "Libra": "Air",
    "Scorpio": "Water",
    "Sagittarius": "Fire",
    "Capricorn": "Earth",
    "Aquarius": "Air",
    "Pisces": "Water",
}

ZODIAC_MODALITIES = {
    "Cardinal": ["Aries", "Cancer", "Libra", "Capricorn"],
    "Fixed": ["Taurus", "Leo", "Scorpio", "Aquarius"],
    "Mutable": ["Gemini", "Virgo", "Sagittarius", "Pisces"],
}

ZODIAC_SIGN_TO_MODALITY = {
    "Aries": "Cardinal",
    "Taurus": "Fixed",
    "Gemini": "Mutable",
    "Cancer": "Cardinal",
    "Leo": "Fixed",
    "Virgo": "Mutable",
    "Libra": "Cardinal",
    "Scorpio": "Fixed",
    "Sagittarius": "Mutable",
    "Capricorn": "Cardinal",
    "Aquarius": "Fixed",
    "Pisces": "Mutable",
}

ZODIAC_DEGREES = {
    "Aries": 0,
    "Taurus": 30,
    "Gemini": 60,
    "Cancer": 90,
    "Leo": 120,
    "Virgo": 150,
    "Libra": 180,
    "Scorpio": 210,
    "Sagittarius": 240,
    "Capricorn": 270,
    "Aquarius": 300,
    "Pisces": 330,
}

# Dictionary definitions for planet dignity
RULERSHIP = {
    "Sun": "Leo",
    "Moon": "Cancer",
    "Mercury": ["Gemini", "Virgo"],
    "Venus": ["Taurus", "Libra"],
    "Mars": ["Aries", "Scorpio"],
    "Jupiter": ["Sagittarius", "Pisces"],
    "Saturn": ["Capricorn", "Aquarius"],
    "Uranus": "Aquarius",
    "Neptune": "Pisces",
    "Pluto": "Scorpio",
}

CLASSICAL_RULERSHIP = {
    "Sun": "Leo",
    "Moon": "Cancer",
    "Mercury": ["Gemini", "Virgo"],
    "Venus": ["Taurus", "Libra"],
    "Mars": ["Aries", "Scorpio"],
    "Jupiter": ["Sagittarius", "Pisces"],
    "Saturn": ["Capricorn", "Aquarius"],
}

FORMER_RULERS = {"Mars": "Scorpio", "Jupiter": "Pisces", "Saturn": "Aquarius"}

EXALTATION = {
    "Sun": "Aries",
    "Moon": "Taurus",
    "Mercury": "Virgo",
    "Venus": "Pisces",
    "Mars": "Capricorn",
    "Jupiter": "Cancer",
    "Saturn": "Libra",
    "Uranus": "Scorpio",
    "Neptune": "Leo",
    "Pluto": "Aquarius",
}

DETRIMENT = {
    "Sun": "Aquarius",
    "Moon": "Capricorn",
    "Mercury": ["Sagittarius", "Pisces"],
    "Venus": ["Aries", "Scorpio"],
    "Mars": ["Taurus", "Libra"],
    "Jupiter": ["Gemini", "Virgo"],
    "Saturn": ["Cancer", "Leo"],
    "Uranus": "Leo",
    "Neptune": "Virgo",
    "Pluto": "Taurus",
}

FALL = {
    "Sun": "Libra",
    "Moon": "Scorpio",
    "Mercury": "Pisces",
    "Venus": "Virgo",
    "Mars": "Cancer",
    "Jupiter": "Capricorn",
    "Saturn": "Aries",
    "Uranus": "Taurus",
    "Neptune": "Aquarius",
    "Pluto": "Leo",
}
# Global formatting variables set in main depending on output type
bold = "\033[1m"
nobold = "\033[0m"
br = "\n"
p = "\n"
h1 = ""
h2 = ""
h3 = ""
h4 = ""
h1_ = ""
h2_ = ""
h3_ = ""
h4_ = ""

############### Functions ###############


def calculate_adjustment_factor(magnitude, min_factor=0.8, max_factor=1.2):
    """
    Calculate the adjustment factor based on the magnitude using a logistic function.

    Parameters:
    - magnitude (float): The magnitude value to adjust.
    - min_factor (float): The minimum adjustment factor.
    - max_factor (float): The maximum adjustment factor.

    Returns:
    - float: The clamped adjustment factor.
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


def angle_influence(angle):
    # Convert angle to absolute value for symmetry
    angle = abs(angle)
    tweaking_factor = 0.8  # Factor to adjust the influence of angles

    if angle <= 3:
        return (2 - angle / 3) * tweaking_factor
    elif angle <= 10:
        return (1 - (angle - 3) / 7) * tweaking_factor
    else:
        return 0


# Assesses the score in terms of ease (100) or difficulty (0) of aspects based on magnitude of stars
def calculate_aspect_score(aspect, angle, magnitude=None):
    if aspect in MAJOR_ASPECTS:
        base_score = MAJOR_ASPECTS[aspect]["Score"]
    elif aspect in MINOR_ASPECTS:
        base_score = MINOR_ASPECTS[aspect]["Score"]
    else:
        return None  # Aspect not found
    adjustment_factor = 1

    # Adjust score based on magnitude (stars)
    if magnitude:
        adjustment_factor = calculate_adjustment_factor(float(magnitude), 0.9, 1.1)

    # Always take the angle of the aspect into account
    influence_factor = angle_influence(angle)
    if base_score > 50:
        adjusted_score = (
            50 + (base_score - 50) * influence_factor * adjustment_factor
        )  # Amplify harmoneous (>50) with higher magnitude
    else:
        adjusted_score = (
            50 - (50 - base_score) * influence_factor * adjustment_factor
        )  # Amplify less harmoneous aspect (>50)

    # Normalize to 0-100 scale
    score = min(max(0, adjusted_score), 100)

    return score


def life_path_number(birthdate):
    """
    Calculate the Life Path Number based on the birthdate.
    The birthdate should be a datetime.date object.
    """
    total = 0
    # Sum of the digits of the day
    for digit in str(birthdate.day):
        total += int(digit)
    # Sum of the digits of the month
    for digit in str(birthdate.month):
        total += int(digit)
    # Sum of the digits of the year
    for digit in str(birthdate.year):
        total += int(digit)

    # Reduce to a single digit or master number (11, 22, 33)
    return reduce_number(total)


def destiny_number(full_name):
    """
    Calculate the Destiny Number based on the full name.
    The full_name should be a string containing the first, middle, and last names.
    """
    # Pythagorean numerology letter to number mapping
    numerology_chart = {
        "A": 1,
        "J": 1,
        "S": 1,
        "B": 2,
        "K": 2,
        "T": 2,
        "C": 3,
        "L": 3,
        "U": 3,
        "D": 4,
        "M": 4,
        "V": 4,
        "E": 5,
        "N": 5,
        "W": 5,
        "F": 6,
        "O": 6,
        "X": 6,
        "G": 7,
        "P": 7,
        "Y": 7,
        "H": 8,
        "Q": 8,
        "Z": 8,
        "I": 9,
        "R": 9,
    }

    total = 0
    for char in full_name.upper():
        if char.isalpha():
            total += numerology_chart.get(char, 0)

    # Reduce to a single digit or master number (11, 22, 33)
    return reduce_number(total)


def reduce_number(number):
    """
    Reduce a number to a single digit or a master number (11, 22, 33).
    """
    while number > 9 and number not in [11, 22, 33]:
        number = sum(int(digit) for digit in str(number))
    return number


def get_davison_data(names, guid=None):
    datetimes = []
    longitudes = []
    latitudes = []
    altitudes = []

    ### NEED TO CHECK NOTIME FOR EVENTS HERE
    for name in names:
        name = name.strip()
        event = db_manager.get_event(name, guid)
        if event:
            datetime_str = event["datetime"]
            timezone_str = event["timezone"]
            # print(f'DEBUG: datetime:{event["datetime"]}')
            # print(f'DEBUG: timezone: {event["timezone"]}')
            if timezone_str == "LMT":
                timezone = "LMT"
            else:
                timezone = pytz.timezone(timezone_str)
            try:
                dt = datetime.strptime(datetime_str, "%Y-%m-%dT%H:%M")
            except ValueError as ex:
                try:
                    dt = datetime.strptime(datetime_str, "%Y-%m-%dT%H:%M:%S")
                except ValueError as ex:
                    print(f"Error parsing datetime for {name}: ({ex})")
            # dt_with_tz = timezone.localize(dt)
            utc_datetime = convert_to_utc(dt, timezone)
            datetimes.append(utc_datetime.astimezone(pytz.utc))
            # datetimes.append(dt_with_tz)
            longitudes.append(event["longitude"])
            latitudes.append(event["latitude"])
            altitudes.append(event["altitude"])
        else:
            print(
                f"\nNo data found for {name}. First create the event by specifying the event details including the name.\n"
            )

    if datetimes:
        total_seconds = sum(
            (
                dt.astimezone(pytz.utc) - datetime(1970, 1, 1, tzinfo=pytz.utc)
            ).total_seconds()
            for dt in datetimes
        )
        avg_seconds = total_seconds / len(datetimes)
        avg_datetime_utc = datetime(1970, 1, 1, tzinfo=pytz.utc) + timedelta(
            seconds=avg_seconds
        )
        avg_datetime_naive = avg_datetime_utc.replace(tzinfo=None)
    else:
        avg_datetime_str = "No datetimes to average"

    # Calculate the average longitude and latitude
    avg_longitude = (
        sum(longitudes) / len(longitudes) if longitudes else "No longitudes to average"
    )
    avg_latitude = (
        sum(latitudes) / len(latitudes) if latitudes else "No latitudes to average"
    )
    avg_altitude = (
        sum(altitudes) / len(altitudes) if altitudes else "No altitudes to average"
    )

    # Store the location in the db
    db_manager.save_location(
        str(avg_latitude) + "," + str(avg_longitude),
        avg_latitude,
        avg_longitude,
        avg_altitude,
    )

    return avg_datetime_naive, avg_longitude, avg_latitude, avg_altitude


def get_progressed_datetime(input_date: datetime, input_value):
    if input_value == "now":
        # Calculate the number of full years since input_date
        now = datetime.now()
        years_passed = now.year - input_date.year

        # Adjust if the current date is before the input_date in the current year
        if (now.month, now.day) < (input_date.month, input_date.day):
            years_passed -= 1

        new_date = input_date + timedelta(days=years_passed)

    elif isinstance(input_value, int):
        # Add the input_value as number of days to input_date
        new_date = input_date + timedelta(days=input_value)
    return new_date


def aspect_diff(angle1, angle2):
    diff = abs(angle1 - angle2) % 360
    return min(diff, 360 - diff)


def find_t_squares(planet_positions, orb_opposition=8, orb_square=6):
    unnecessary_points = [
        "Ascendant",
        "Midheaven",
        "IC",
        "DC",
        "North Node",
        "South Node",
    ]
    planets = [p for p in planet_positions.keys() if p not in unnecessary_points]

    t_squares = []

    for i, p1 in enumerate(planets):
        for j, p2 in enumerate(planets[i + 1 :], start=i + 1):
            opposition_diff = aspect_diff(
                planet_positions[p1]["longitude"], planet_positions[p2]["longitude"]
            )
            if abs(opposition_diff - 180) <= orb_opposition:
                for p3 in planets[j + 1 :]:
                    if p3 != p1 and p3 != p2:
                        square_diff1 = aspect_diff(
                            planet_positions[p1]["longitude"],
                            planet_positions[p3]["longitude"],
                        )
                        square_diff2 = aspect_diff(
                            planet_positions[p2]["longitude"],
                            planet_positions[p3]["longitude"],
                        )
                        if (
                            abs(square_diff1 - 90) <= orb_square
                            and abs(square_diff2 - 90) <= orb_square
                        ):
                            t_squares.append(
                                (
                                    p1,
                                    p2,
                                    p3,
                                    abs(180 - opposition_diff),
                                    abs(90 - square_diff1),
                                    abs(90 - square_diff2),
                                )
                            )
    return t_squares


def find_yod(planet_positions, orb_opposition=8, orb_square=6):
    unnecessary_points = [
        "Ascendant",
        "Midheaven",
        "IC",
        "DC",
        "North Node",
        "South Node",
    ]
    planets = [p for p in planet_positions.keys() if p not in unnecessary_points]

    fingers_of_god = []

    for i, p1 in enumerate(planets):
        for p2 in planets[i + 1 :]:
            opposition_diff = aspect_diff(
                planet_positions[p1]["longitude"], planet_positions[p2]["longitude"]
            )
            if abs(opposition_diff - 60) <= orb_opposition:
                for p3 in planets:
                    if p3 != p1 and p3 != p2:
                        square_diff1 = aspect_diff(
                            planet_positions[p1]["longitude"],
                            planet_positions[p3]["longitude"],
                        )
                        square_diff2 = aspect_diff(
                            planet_positions[p2]["longitude"],
                            planet_positions[p3]["longitude"],
                        )
                        if (
                            abs(square_diff1 - 150) <= orb_square
                            and abs(square_diff2 - 150) <= orb_square
                        ):
                            fingers_of_god.append(
                                (
                                    p1,
                                    p2,
                                    p3,
                                    abs(60 - opposition_diff),
                                    abs(150 - square_diff1),
                                    abs(150 - square_diff2),
                                )
                            )
    return fingers_of_god


def find_grand_crosses(planet_positions, orb=8):
    unnecessary_points = [
        "Ascendant",
        "Midheaven",
        "IC",
        "DC",
        "North Node",
        "South Node",
    ]
    planets = [p for p in planet_positions.keys() if p not in unnecessary_points]

    grand_crosses = []

    for i, p1 in enumerate(planets):
        for j, p2 in enumerate(planets[i + 1 :], start=i + 1):
            first_square_diff = aspect_diff(
                planet_positions[p1]["longitude"], planet_positions[p2]["longitude"]
            )
            if abs(first_square_diff - 90) <= orb:
                for k, p3 in enumerate(planets[j + 1 :], start=j + 1):
                    if p3 != p1 and p3 != p2:
                        second_square_diff = aspect_diff(
                            planet_positions[p2]["longitude"],
                            planet_positions[p3]["longitude"],
                        )
                        if abs(second_square_diff - 90) <= orb:
                            for l, p4 in enumerate(planets[k + 1 :], start=k + 1):
                                third_square_diff = aspect_diff(
                                    planet_positions[p3]["longitude"],
                                    planet_positions[p4]["longitude"],
                                )
                                fourth_square_diff = aspect_diff(
                                    planet_positions[p1]["longitude"],
                                    planet_positions[p4]["longitude"],
                                )
                                if (
                                    abs(third_square_diff - 90) <= orb
                                    and abs(fourth_square_diff - 90) <= orb
                                ):
                                    first_oppo_diff = aspect_diff(
                                        planet_positions[p1]["longitude"],
                                        planet_positions[p3]["longitude"],
                                    )
                                    second_oppo_diff = aspect_diff(
                                        planet_positions[p2]["longitude"],
                                        planet_positions[p4]["longitude"],
                                    )
                                    grand_crosses.append(
                                        (
                                            p1,
                                            p2,
                                            p3,
                                            p4,
                                            abs(90 - first_square_diff),
                                            abs(90 - second_square_diff),
                                            abs(90 - third_square_diff),
                                            abs(90 - fourth_square_diff),
                                            abs(180 - first_oppo_diff),
                                            abs(180 - second_oppo_diff),
                                        )
                                    )
    return grand_crosses


def find_grand_trines(planet_positions, orb=8):
    unnecessary_points = [
        "Ascendant",
        "Midheaven",
        "IC",
        "DC",
        "North Node",
        "South Node",
    ]
    planets = [p for p in planet_positions.keys() if p not in unnecessary_points]

    grand_trines = []

    for i, p1 in enumerate(planets):
        for j, p2 in enumerate(planets[i + 1 :], start=i + 1):
            first_trine_diff = aspect_diff(
                planet_positions[p1]["longitude"], planet_positions[p2]["longitude"]
            )
            if abs(first_trine_diff - 120) <= orb:
                for p3 in planets[j + 1 :]:
                    if p3 != p1 and p3 != p2:
                        second_trine_diff = aspect_diff(
                            planet_positions[p2]["longitude"],
                            planet_positions[p3]["longitude"],
                        )
                        third_trine_diff = aspect_diff(
                            planet_positions[p1]["longitude"],
                            planet_positions[p3]["longitude"],
                        )
                        if (
                            abs(second_trine_diff - 120) <= orb
                            and abs(third_trine_diff - 120) <= orb
                        ):
                            grand_trines.append(
                                (
                                    p1,
                                    p2,
                                    p3,
                                    abs(120 - first_trine_diff),
                                    abs(120 - second_trine_diff),
                                    abs(120 - third_trine_diff),
                                )
                            )
    return grand_trines


def find_kites(planet_positions, orb=8):
    unnecessary_points = [
        "Ascendant",
        "Midheaven",
        "IC",
        "DC",
        "North Node",
        "South Node",
    ]
    planets = [p for p in planet_positions.keys() if p not in unnecessary_points]

    kites = []

    for i, p1 in enumerate(planets):
        for j, p2 in enumerate(planets[i + 1 :], start=i + 1):
            first_trine_diff = aspect_diff(
                planet_positions[p1]["longitude"], planet_positions[p2]["longitude"]
            )
            if abs(first_trine_diff - 120) <= orb:
                for p3 in planets[j + 1 :]:
                    if p3 != p1 and p3 != p2:
                        second_trine_diff = aspect_diff(
                            planet_positions[p2]["longitude"],
                            planet_positions[p3]["longitude"],
                        )
                        third_trine_diff = aspect_diff(
                            planet_positions[p1]["longitude"],
                            planet_positions[p3]["longitude"],
                        )
                        if (
                            abs(second_trine_diff - 120) <= orb
                            and abs(third_trine_diff - 120) <= orb
                        ):
                            for p4 in planets:
                                if p4 != p1 and p4 != p2 and p4 != p3:
                                    oppo_diff1 = aspect_diff(
                                        planet_positions[p1]["longitude"],
                                        planet_positions[p4]["longitude"],
                                    )
                                    oppo_diff2 = aspect_diff(
                                        planet_positions[p2]["longitude"],
                                        planet_positions[p4]["longitude"],
                                    )
                                    oppo_diff3 = aspect_diff(
                                        planet_positions[p3]["longitude"],
                                        planet_positions[p4]["longitude"],
                                    )
                                    oppo_diff = min(
                                        abs(180 - oppo_diff1),
                                        abs(180 - oppo_diff2),
                                        abs(180 - oppo_diff3),
                                    )

                                    if (
                                        abs(oppo_diff1 - 180) <= orb
                                        or abs(oppo_diff2 - 180) <= orb
                                        or abs(oppo_diff3 - 180) <= orb
                                    ):
                                        kites.append(
                                            (
                                                p1,
                                                p2,
                                                p3,
                                                p4,
                                                abs(120 - first_trine_diff),
                                                abs(120 - second_trine_diff),
                                                abs(120 - third_trine_diff),
                                                oppo_diff,
                                            )
                                        )
    return kites


def assess_planet_strength(planet_signs, classic_rulership=False):
    strength_status = {}
    for planet, sign in planet_signs.items():
        if planet in (
            CLASSICAL_RULERSHIP if classic_rulership else RULERSHIP
        ) and sign == (
            CLASSICAL_RULERSHIP[planet] if classic_rulership else RULERSHIP[planet]
        ):
            strength_status[planet] = " Domicile"
        elif planet in FORMER_RULERS and sign == FORMER_RULERS[planet]:
            strength_status[planet] = " Co-Ruler"
        elif planet in EXALTATION and sign == EXALTATION[planet]:
            strength_status[planet] = " Exalted (Strong)"
        elif planet in DETRIMENT and sign == DETRIMENT[planet]:
            strength_status[planet] = " In Detriment (Weak)"
        elif planet in FALL and sign == FALL[planet]:
            strength_status[planet] = " In Fall (Very Weak)"
        else:
            strength_status[planet] = ""

    return strength_status


def check_degree(planet_signs, degrees_within_sign):
    degrees_within_sign = int(degrees_within_sign)
    strength_status = {}
    for planet, sign in planet_signs.items():
        strength_status[planet] = ""

        if degrees_within_sign == 29:
            strength_status[planet] = " Anaretic"
        elif degrees_within_sign == 0:
            strength_status[planet] = " Cusp"

        # Check Critical Degrees for different modalities
        if sign in ZODIAC_MODALITIES["Cardinal"] and degrees_within_sign in [0, 13, 16]:
            strength_status[planet] += " Critical"
        elif sign in ZODIAC_MODALITIES["Fixed"] and degrees_within_sign in [
            8,
            9,
            21,
            22,
        ]:
            strength_status[planet] += " Critical"
        elif sign in ZODIAC_MODALITIES["Mutable"] and degrees_within_sign in [4, 17]:
            strength_status[planet] += " Critical"

    return strength_status


# Function to check elevation based on house
def is_planet_elevated(planet_positions):
    elevated_status = {}
    for planet, house in planet_positions.items():
        if planet not in ["Ascendant", "Midheaven"]:
            if house == 10:
                elevated_status[planet] = "Angular, Elevated"
            elif house in [1, 4, 7]:
                elevated_status[planet] = "Angular"
            else:
                elevated_status[planet] = ""
        else:
            elevated_status[planet] = ""
    return elevated_status


def datetime_ruled_by(date):
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


def get_delta_t(date):
    # Calculate Delta T for the given date
    # jd = swe.julday(date.year, date.month, date.day)
    # delta_t = swe.deltat(jd)

    if date.year >= 1972:
        T = (date.year - 2000) / 100
        delta_t = (
            62.92 + 0.32217 * T + 0.005589 * T**2 - 0.0000274 * T**3 + 0.0000019 * T**4
        )
        return delta_t
    else:
        return 0


def get_pluto_ecliptic(
    date: datetime,
):
    """
    Calculate and print Pluto's ecliptic latitude for a given date.
    This function calculates the heliocentric position of Pluto for the given date
    and determines whether Pluto is above, below, or exactly on the ecliptic plane.
    Args:
        date (datetime): The date for which to calculate Pluto's position.
    Returns:
        None
    """
    # Hämta Plutos position
    jd = swe.julday(date.year, date.month, date.day)  # Omvandla till julianskt datum
    pluto_pos, ret = swe.calc_ut(
        jd, swe.PLUTO, swe.FLG_HELCTR
    )  # Heliocentrisk position

    # Extrahera latitud
    pluto_latitude = pluto_pos[1]  # Latitud i grader

    pluto_string = "Ecl: "
    if pluto_latitude > 0:
        pluto_string += "+"
    elif pluto_latitude < 0:
        pluto_string += "-"
    else:
        pluto_string += "On "
    pluto_string += f"{abs(pluto_latitude):.2f}° ({(pluto_latitude/17.16)*100:.2f}%)"

    return pluto_string


def find_next_same_degree(
    dt,
    planet_name,
    longitude,
    latitude,
    altitude,
    nextprev="next",
    center="topocentric",
):
    if planet_name.title() not in PLANET_RETURN_DICT:
        raise ValueError("Invalid planet name provided.")

    planet_info = PLANET_RETURN_DICT[planet_name.title()]
    planet = planet_info["constant"]
    orbital_period = planet_info["orbital_period_days"]

    julian_day = swe.julday(dt.year, dt.month, dt.day, dt.hour + dt.minute / 60.0)

    # Handle None altitude by defaulting to sea level (0.0)
    if altitude is None:
        altitude = 0.0

    if center == "topocentric":
        swe.set_topo(float(longitude), float(latitude), float(altitude))
        current_pos, _ = swe.calc(julian_day, planet, swe.FLG_TOPOCTR)
    elif center == "heliocentric":
        current_pos, _ = swe.calc_ut(julian_day, planet, swe.FLG_HELCTR)
    else:
        current_pos, _ = swe.calc_ut(julian_day, planet)

    current_degree = current_pos[0] % 360  # Normalize to 0-360 degrees

    if nextprev == "next":
        start_dt = datetime.now()
    else:
        start_dt = datetime.now() - timedelta(days=orbital_period)

    # Define the search interval (orbital period)
    end_dt = start_dt + timedelta(days=orbital_period)

    def get_next_degree(next_dt, longitude, latitude, altitude, center):
        julian_day_next = swe.julday(
            next_dt.year,
            next_dt.month,
            next_dt.day,
            next_dt.hour + next_dt.minute / 60.0,
        )

        if center == "topocentric":
            swe.set_topo(float(longitude), float(latitude), float(altitude))
            next_pos, _ = swe.calc(julian_day_next, planet, swe.FLG_TOPOCTR)
        elif center == "heliocentric":
            next_pos, _ = swe.calc_ut(julian_day_next, planet, swe.FLG_HELCTR)
        else:
            next_pos, _ = swe.calc_ut(julian_day_next, planet)

        return next_pos[0] % 360

    # Binary search-like approach to find the date with the same degree
    while (
        end_dt - start_dt
    ).total_seconds() > 30:  # While the interval is larger than 1/2 minute
        mid_dt = start_dt + (end_dt - start_dt) / 2
        next_degree = get_next_degree(mid_dt, longitude, latitude, altitude, center)

        if (
            abs(next_degree - current_degree) < 0.005
        ):  # Allow small tolerance due to precision
            return mid_dt

        if next_degree < current_degree:
            start_dt = mid_dt
        else:
            end_dt = mid_dt

    # If not found within the loop, return the closest approximation
    print("Exact return not found")
    return start_dt


def convert_to_utc(local_datetime, local_timezone):
    """
    Convert a naive datetime object to UTC using a specified timezone.

    Parameters:
    - local_datetime (datetime): A naive datetime object representing local time.
    - local_timezone (pytz.timezone): A timezone object representing the local timezone.

    Returns:
    - datetime: A datetime object converted to UTC.
    """
    # Ensure local_datetime is naive before localization
    if local_datetime.tzinfo is not None:
        raise ValueError("local_datetime should be naive (no timezone info).")

    # Localize the naive datetime object to the specified timezone
    local_datetime = local_timezone.localize(local_datetime)

    # Convert the timezone-aware datetime object to UTC
    utc_datetime = local_datetime.astimezone(pytz.utc)
    # delta_t_adjusted_utc = utc_datetime + timedelta(seconds=get_delta_t(utc_datetime))

    # utc_datetime = delta_t_adjusted_utc.astimezone(pytz.utc)

    return utc_datetime


def get_coordinates(location_name: str):
    """
    Returns the geographic coordinates (latitude, longitude) of a specified location name.

    Loads the coordinates from a JSON file if the location has been previously saved, othwerwise
    utilizes the Nominatim geocoder from the geopy library to convert a location name (such as a street address,
    city, or country) into geographic coordinates. The function is initialized with a user_agent named
    "AstroScript" for the Nominatim API, which has a limit of 1 request/second.
    Saves the coordinates to a JSON file, so that internet access and API calls are minimized.

    Parameters:
    - location_name (str): The name of the location for which to obtain geographic coordinates.

    Returns:
    - tuple: A tuple containing the latitude, longitude and altitude of the specified location.

    Note:
    - The accuracy of the coordinates returned depends on the specificity of the location name provided.
    - Ensure compliance with Nominatim's usage policy when using this function.
    """

    location_details = db_manager.load_location(location_name)
    if location_details:
        return (
            location_details[0],
            location_details[1],
            location_details[2],
        )  # Latitude, Longitude, Altitude
    else:
        try:
            geolocator = Nominatim(user_agent="AstroScript")
        except Exception as e:
            print(f"Error initializing geolocator: {e}")
            return None, None, None

        try:
            location = geolocator.geocode(location_name)
        except Exception as e:
            print(
                f"Error getting location {location_name}, check internet connection, spelling, choose nearby location, or specify place using --place and enter coordinates using --latitude, --longitude: {e}"
            )
            return None, None, None
        if location is None:
            db_manager.save_location(location_name, None, None, None)
            return None, None, None
        altitude = get_altitude(location.latitude, location.longitude, location_name)

        db_manager.save_location(
            location_name, location.latitude, location.longitude, altitude
        )

        return location.latitude, location.longitude, altitude


def calculate_individual_house_position(
    date, latitude, longitude, planet_longitude, h_sys="P"
):
    jd = swe.julday(date.year, date.month, date.day, date.hour + date.minute / 60.0)
    houses, ascmc = swe.houses(jd, latitude, longitude, h_sys.encode("utf-8"))

    house_num = 1  # Begin as house 1 in case nothing else matches
    # Check for each house from 1 to 11 (12 handled separately)
    for i, cusp in enumerate(houses):
        next_cusp = houses[(i + 1) % 12]

        # If at last house and next cusp is less than the current because of wrap-around
        if next_cusp < cusp:
            next_cusp += 360

        if cusp <= planet_longitude < next_cusp:
            house_num = i + 1
            break
        elif i == 11 and (planet_longitude >= cusp or planet_longitude < houses[0]):
            house_num = 12  # Assign to house 12 if nothing else matches
            break

    return house_num


def calculate_house_positions(
    date, latitude, longitude, altitude, planets_positions, notime=False, h_sys="P"
):
    """
    Calculate the house positions for a given datetime, latitude, and longitude, considering the positions of planets.

    Parameters:
    - date (datetime): The date and time for the calculation. Must include a time component; calculations at midnight may be less accurate.
    - latitude (float): The latitude of the location.
    - longitude (float): The longitude of the location.
    - planets_positions (dict): A dictionary containing planets and their ecliptic longitudes.
    - notime (bool): A flag indicating if the time of day is not specified. If True, houses can not be calculated accurately.

    Returns:
    - tuple:
        - house_positions (dict): A dictionary mapping each planet, including the Ascendant ('Ascendant') and Midheaven ('Midheaven'), to their house numbers.
        - house_cusps (list): The zodiac positions of the beginnings of each house.

    Raises:
    - ValueError: If the time component of the date is exactly midnight, which may result in less accurate calculations.
    """
    try:
        swe.set_topo(altitude, latitude, longitude)
    except Exception as e:
        print(f"Error setting topocentric coordinates: {e}")

    # Validate input date has a time component (convention to use 00:00:00 for unknown time )
    if notime:
        print("Warning: Time is not set. Houses cannot be reliably calculated.")

    jd = swe.julday(date.year, date.month, date.day, date.hour + date.minute / 60.0)
    houses, ascmc = swe.houses(jd, latitude, longitude, h_sys.encode("utf-8"))

    ascendant_long = ascmc[0]  # Ascendant is the first item in ascmc list
    midheaven_long = ascmc[1]  # Midheaven is the second item in ascmc list

    # Initialize dictionary with Ascendant and Midheaven
    house_positions = {
        "Ascendant": {"longitude": ascendant_long, "house": 1},
        "Midheaven": {
            "longitude": midheaven_long,
            "house": 10,
        },  # Midheaven is traditionally associated with the 10th house
    }

    # Assign planets to houses
    for planet, planet_info in planets_positions.items():
        planet_longitude = planet_info["longitude"] % 360
        house_num = 1  # Begin as house 1 in case nothing else matches
        # Check for each house from 1 to 11 (12 handled separately)
        for i, cusp in enumerate(houses):
            next_cusp = houses[(i + 1) % 12]

            # If at last house and next cusp is less than the current because of wrap-around
            if next_cusp < cusp:
                next_cusp += 360

            if cusp <= planet_longitude < next_cusp:
                house_num = i + 1
                break
            elif i == 11 and (planet_longitude >= cusp or planet_longitude < houses[0]):
                house_num = 12  # Assign to house 12 if nothing else matches
                break

        house_positions[planet] = {"longitude": planet_longitude, "house": house_num}

    # Always in same houses, so as not to inflate house counts
    keys_to_update = ["Ascendant", "Midheaven", "IC", "DC"]
    for key in keys_to_update:
        if key in house_positions:
            house_positions[key]["house"] = ""

    return (
        house_positions,
        houses[:13],
    )  # Return house positions and cusps (including Ascendant)


def longitude_to_zodiac(longitude, output):
    """
    Convert ecliptic longitude to its corresponding zodiac sign and precise degree.

    This function calculates the zodiac sign and the exact position (degrees, minutes, and seconds)
    of a given ecliptic longitude.

    Parameters:
    - longitude (float): The ecliptic longitude to convert, in degrees.

    Returns:
    - str: A string representing the zodiac sign and degree, formatted as 'Sign Degree°Minutes'Seconds"'.
           For example, "Aries 15°30'45''" represents 15 degrees, 30 minutes, and 45 seconds into Aries.
    """
    zodiac_signs = [
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
    sign_index = int(longitude // 30)
    degree = int(longitude % 30)
    minutes = int((longitude % 1) * 60)
    seconds = int((((longitude % 1) * 60) % 1) * 60)

    degree_symbol = "" if (os.name == "nt" and output == "html") else "°"

    return f"{zodiac_signs[sign_index]} {degree}{degree_symbol}{minutes}'{seconds}''"


def is_planet_retrograde(planet, jd):
    """
    Determine if a planet is retrograde on a given Julian Day (JD).

    Retrograde motion is when a planet appears to move backward in the sky from the perspective of Earth.
    This function checks the planet's motion by comparing its positions slightly before and after the given JD.
    A planet is considered retrograde if its ecliptic longitude decreases over time.

    Parameters:
    - planet (int): The planet's identifier for swisseph.
    - jd (float): Julian Day to check for retrograde motion.

    Returns:
    - bool: True if the planet is retrograde, False otherwise.
    """
    # Calculate the planet's position slightly before and after the given Julian Day
    pos_before = swe.calc_ut(jd - (10 / 1440), planet)[0]
    pos_after = swe.calc_ut(jd + (10 / 1440), planet)[0]

    # A planet is considered retrograde if its position (in longitude) decreases over time
    return pos_after[0] < pos_before[0]


def get_fixed_star_position(star_name, jd):
    """
    Retrieve the ecliptic longitude of a fixed star on a given Julian Day.

    Fixed stars' positions are relatively constant, but due to precession, their
    longitudes change very slowly over time. This function uses the Swiss Ephemeris
    to calculate the current position of a star given its name.

    Parameters:
    - star_name (str): The name of the fixed star.
    - jd (float): Julian Day for which to calculate the star's position.

    Returns:
    - float: The ecliptic longitude of the fixed star, or None if the star is not found.

    Raises:
    - ValueError: If the star name is not recognized by the Swiss Ephemeris.
    """
    try:
        star_info = swe.fixstar(star_name, jd)
        return star_info[0][0]  # Returning the longitude part of the position
    except:
        raise ValueError(f"Fixed star '{star_name}' not recognized.")


def check_aspect(planet_long, star_long, aspect_angle, orb):
    """
    Check if an aspect exists between two points based on their longitudes and calculate the difference
    from the exact aspect angle. This function helps in determining not only if an astrological aspect
    (e.g., conjunction, opposition) is present within a specified orb but also how much the actual angle
    is off from the desired aspect angle.

    Parameters:
    - planet_long (float): The ecliptic longitude of the planet.
    - star_long (float): The ecliptic longitude of the fixed star.
    - aspect_angle (float): The angle that defines the aspect (e.g., 90 degrees for a square).
    - orb (float): The maximum allowed deviation from the aspect_angle for the aspect to be considered valid.

    Returns:
    - tuple: A tuple containing a boolean and a float. The boolean indicates whether the aspect is within
             the allowed orb, and the float represents how much the actual angle is off from the aspect_angle.
    """
    angular_difference = (planet_long - star_long) % 360
    # Normalize the angle to <= 180 degrees for comparison
    if angular_difference > 180:
        angular_difference = 360 - angular_difference

    angle_off = angular_difference - aspect_angle
    return ((angle_off <= orb) and angle_off >= -orb), angle_off


def get_altitude(lat, lon, location_name):

    if location_name != "Davison chart":
        location_details = db_manager.load_location(location_name)
        if location_details:
            return location_details[2]  # Altitude

    try:
        url = f"https://api.open-elevation.com/api/v1/lookup?locations={lat},{lon}"
        response = requests.get(url)
        results = response.json()["results"]
        if results:
            return results[0]["elevation"]
    except Exception as e:
        print(f"Error getting altitude: {e}")
        return None


def calculate_aspects_to_fixed_stars(
    date, planet_positions, houses, orb=1.0, aspect_types=None, all_stars=False
):
    """
    List aspects between planets and fixed stars, considering the house placement of each fixed star
    and the angle difference from the exact aspect angle. This function enriches astrological analysis
    by providing detailed insights into the relationships between planets and stars, including how closely
    each aspect aligns with its ideal angular relationship.

    Parameters:
    - date (datetime): The date and time for the calculation.
    - planet_positions (dict): A dictionary of planets and their positions.
    - houses (list): A list of house cusp positions.
    - orb (float): Orb value for aspect consideration. Default is 1.0 degree.
    - aspect_types (dict, optional): A dictionary of aspect names and their angular distances.
                                     Defaults to common aspects if None.
    - all_stars (bool): Whether to include all stars or a predefined list of stars with known astrological meanings.

    Returns:
    - list: A list of tuples, each representing an aspect between a planet and a fixed star. Each tuple includes
            the planet name, star name, aspect name, the angle difference from the aspect angle, and the house of the fixed star.
    """
    if aspect_types is None:
        aspect_types = {
            "Conjunction": 0,
            "Opposition": 180,
            "Trine": 120,
            "Square": 90,
            "Sextile": 60,
        }

    fixed_stars = read_fixed_stars(all_stars)
    jd = swe.julday(date.year, date.month, date.day, date.hour)
    aspects = []

    for star_name in fixed_stars.keys():
        try:
            star_long = get_fixed_star_position(star_name, jd) % 360

            house_num = 1  # Begin as house 1 in case nothing else matches
            # Check for each house from 1 to 11 (12 handled separately)
            for i, cusp in enumerate(houses):
                next_cusp = houses[(i + 1) % 12]

                # If at last house and next cusp is less than the current because of wrap-around
                if next_cusp < cusp:
                    next_cusp += 360

                if cusp <= star_long < next_cusp:
                    house_num = i + 1
                    break
                elif i == 11 and (star_long >= cusp or star_long < houses[0]):
                    house_num = 12  # Assign to house 12 if nothing else matches
                    break

            for planet, data in planet_positions.items():
                planet_long = data["longitude"]
                for aspect_name, aspect_details in aspect_types.items():
                    aspect_angle, aspect_score, aspect_comment = aspect_details.values()
                    valid_aspect, angle_off = check_aspect(
                        planet_long, star_long, aspect_angle, orb
                    )
                    if valid_aspect:
                        aspects.append(
                            (
                                planet,
                                star_name,
                                aspect_name,
                                angle_off,
                                house_num,
                                aspect_score,
                                aspect_comment,
                            )
                        )
        except ValueError as e:
            print(f"Error processing star {star_name}: {e}")

    return aspects


def read_fixed_stars(all_stars=False):
    """
    Read and return a dictionary of fixed star names and their magnitudes from a predefined CSV file.
    This function can select between a comprehensive list of all fixed stars or a curated list of
    those known for their astrological significance based on the input parameter.

    Parameters:
    - all_stars (bool): Determines which list of fixed stars to read:
                        if True, reads a comprehensive list;
                        if False, reads a list of astrologically significant stars.

    Returns:
    - dict: A dictionary where keys are fixed star names and values are their magnitudes.

    Raises:
    - FileNotFoundError: If the specified file cannot be found.
    - IOError: If there is an issue reading from the file.
    """

    # If production env
    if EPHE:
        filename = (
            f"{EPHE}/fixed_stars_all.csv"
            if all_stars
            else f"{EPHE}/astrologically_known_fixed_stars.csv"
        )
    else:
        filename = (
            "./ephe/fixed_stars_all.csv"
            if all_stars
            else "./ephe/astrologically_known_fixed_stars.csv"
        )

    try:
        with open(filename, mode="r", newline="") as file:
            reader = csv.DictReader(file)
            fixed_stars = {row["Name"]: row["Magnitude"] for row in reader}
    except FileNotFoundError:
        raise FileNotFoundError(f"The file '{filename}' was not found.")
    except IOError as e:
        raise IOError(f"An error occurred while reading from '{filename}': {e}")

    return fixed_stars


def calculate_aspect_duration(planet_positions, planet2, degrees_to_travel):
    """
    Calculate the exact duration for which two planets are within a specified number of degrees of each other.

    Parameters:
    - planet_positions (dict): Dictionary with each celestial body as keys, containing their
      ecliptic longitude, zodiac sign, retrograde status, and speed.
    - planet2 (str): The second planet involved in the transit.
    - degrees_to_travel (float): The number of degrees representing the orb of the aspect.

    Returns:
    - str: Duration of the aspect in days, hours, and minutes.
    """
    if abs(planet_positions[planet2]["speed"]) == 0:
        planet_positions[planet2][
            "speed"
        ] = 0.0001  # This affects most transits that not okly last a few mimutes nowcindivating that something ia wrong. is the speed not set ok in the positions dict?
    days = degrees_to_travel / abs(planet_positions[planet2]["speed"])
    hours = int((days % 1) * 24)
    minutes = int(((days % 1) * 24 % 1) * 60)
    return_string = ""

    if days > 5:
        days = int(round(days))

    # Return formatted duration
    if days >= 1 and days < 2:
        return_string = f"{int(days)} day "
    elif days >= 2:
        return_string = f"{int(days)} days "
    if days < 5:  # Only show hours if less than 5 days
        if days % 1 >= 1:
            if hours >= 1 and hours < 2:
                return_string += f"and {int(hours)} hour"
            elif hours >= 2:
                return_string += f"and {int(hours)} hours"
        else:
            if hours >= 1 and hours < 2:
                return_string += f"{hours} hour"
            elif hours >= 2:
                return_string += f"{hours} hours"
    if days < 1 and hours < 1:
        if minutes >= 2:
            return_string += f"{minutes} minutes"
        elif 1 <= minutes < 2:
            return_string += f"{minutes} minute"
    return return_string if return_string else "Less than a minute"


def get_decan_ruler(longitude, zodiac_sign, classic_rulers):
    """
    Determine the decan ruler of a given zodiac sign based on the longitude of a planet.

    Each zodiac sign is divided into three decans, each spanning 10 degrees. The decan ruler
    is determined by the planet that rules the corresponding triplicity (element) of the zodiac sign.
    This function calculates the decan ruler based on the zodiac sign and the planet's longitude.

    Parameters:
    - longitude (float): The ecliptic longitude of the planet.
    - zodiac_sign (str): The zodiac sign of the planet.

    Returns:
    - str: The name of the planet ruling the decan of the zodiac sign.
    """
    if classic_rulers:
        decan_rulers = {  # In case there' will be an option for classical rulers
            "Aries": ["Mars", "Sun", "Jupiter"],
            "Taurus": ["Venus", "Mercury", "Saturn"],
            "Gemini": ["Mercury", "Venus", "Saturn"],
            "Cancer": ["Moon", "Mars", "Jupiter"],
            "Leo": ["Sun", "Jupiter", "Mars"],
            "Virgo": ["Mercury", "Saturn", "Venus"],
            "Libra": ["Venus", "Saturn", "Mercury"],
            "Scorpio": ["Mars", "Sun", "Venus"],
            "Sagittarius": ["Jupiter", "Mars", "Sun"],
            "Capricorn": ["Saturn", "Venus", "Mercury"],
            "Aquarius": ["Saturn", "Mercury", "Venus"],
            "Pisces": ["Jupiter", "Mars", "Sun"],
        }
    else:
        decan_rulers = {  # Including modern planets
            "Aries": ["Mars", "Sun", "Jupiter"],
            "Taurus": ["Venus", "Mercury", "Saturn"],
            "Gemini": ["Mercury", "Venus", "Uranus"],
            "Cancer": ["Moon", "Pluto", "Neptune"],
            "Leo": ["Sun", "Jupiter", "Mars"],
            "Virgo": ["Mercury", "Saturn", "Venus"],
            "Libra": ["Venus", "Uranus", "Mercury"],
            "Scorpio": ["Mars", "Neptune", "Moon"],
            "Sagittarius": ["Jupiter", "Mars", "Sun"],
            "Capricorn": ["Saturn", "Venus", "Mercury"],
            "Aquarius": ["Uranus", "Mercury", "Venus"],
            "Pisces": ["Neptune", "Moon", "Pluto"],
        }

    decan_index = (int(longitude) // 10) % 3
    return decan_rulers[zodiac_sign][decan_index]


def find_exact_aspects_in_timeframe(
    begin_date,
    end_date,
    latitude,
    longitude,
    altitude,
    orbs,
    center,
    step_days=1,
    output_type="html",
):
    """
    Finds exact aspects between planets within a given time frame.

    Parameters:
    - begin_date: The start date (datetime object) in UTC.
    - end_date: The end date (datetime object) in UTC.
    - latitude: Latitude of the location in degrees.
    - longitude: Longitude of the location in degrees.
    - altitude: Altitude of the location in meters.
    - step_days: The number of days to step through each iteration. Default is 1.
    - output_type: The type of output for the aspect angle (e.g., 'minutes').

    Returns:
    - A list of dictionaries, each representing an exact aspect found within the timeframe.
    """

    aspects_list = []

    # Loop through each date within the given range
    current_date = begin_date
    while current_date <= end_date:
        # Calculate the positions of all planets for the current date using the existing function
        planet_positions = calculate_planet_positions(
            current_date, latitude, longitude, altitude, output_type
        )

        # Calculate aspects for the current date
        aspects_found = calculate_planetary_aspects(
            planet_positions, orbs, output_type, aspect_types=MAJOR_ASPECTS
        )

        # If aspects are found, append them to the results list
        if aspects_found:
            for aspect, details in aspects_found.items():
                aspect_detail = {
                    "date": current_date.isoformat(),
                    "planet1": aspect[0],
                    "planet2": aspect[1],
                    "aspect": details["aspect_name"],
                    "angle_diff": details["angle_diff"],
                    "angle_diff_in_minutes": details["angle_diff_in_minutes"],
                    "is_imprecise": details["is_imprecise"],
                    "aspect_score": details["aspect_score"],
                    "aspect_comment": details["aspect_comment"],
                }
                aspects_list.append(aspect_detail)

        # Move to the next day
        current_date += timedelta(days=step_days)
    print(aspects_list)
    return aspects_list


def calculate_planet_positions(
    date,
    latitude,
    longitude,
    altitude,
    output,
    h_sys="P",
    mode="planets",
    center="topocentric",
    arabic_parts=False,
    all_stars=False,
    classic_rulers=False,
):
    """
    Calculate the ecliptic longitudes, signs, and retrograde status of celestial bodies
    at a given datetime, for a specified location. This includes the Sun, Moon, planets,
    Chiron, and the lunar nodes, along with the Ascendant (ASC) and Midheaven (MC).

    Parameters:
    - date (datetime): The datetime for which positions are calculated.
    - latitude (float): Latitude of the location in degrees.
    - longitude (float): Longitude of the location in degrees.

    Returns:
    - dict: A dictionary with each celestial body as keys, and dictionaries containing
      their ecliptic longitude, zodiac sign, and retrograde status ('R' if retrograde) as values.
    """
    # For some reason needs to be set again
    if EPHE:
        swe.set_ephe_path(EPHE)
    else:
        if os.name == "nt":
            swe.set_ephe_path(".\ephe")
        else:
            swe.set_ephe_path("./ephe")

    if center == "topocentric":
        # Handle None altitude by defaulting to sea level (0.0)
        if altitude is None:
            altitude = 0.0
        try:
            swe.set_topo(longitude, latitude, altitude)
        except Exception as e:
            print(f"Error setting topocentric coordinates: {e}")

    jd = swe.julday(
        date.year,
        date.month,
        date.day,
        date.hour + date.minute / 60.0 + date.second / 3600.0,
    )
    positions = {}
    if mode == "planets":
        PLANETS.pop(
            "South Node", None
        )  # None is the default value if the key doesn't exist
        PLANETS.pop("Fortune", None)
        PLANETS.pop("Spirit", None)
        PLANETS.pop("Love", None)
        PLANETS.pop("Marriage", None)
        PLANETS.pop("Friendship", None)
        PLANETS.pop("Death", None)
        PLANETS.pop("Commerce", None)
        PLANETS.pop("Passion", None)
        bodies = PLANETS
    elif mode == "asteroids":
        bodies = ASTEROIDS
    elif mode == "stars":
        fixed_stars = read_fixed_stars(all_stars=all_stars)

        for star_name in fixed_stars.keys():
            try:
                star_long = get_fixed_star_position(star_name, jd) % 360
                positions[star_name] = {
                    "longitude": star_long,
                    "zodiac_sign": longitude_to_zodiac(star_long, output).split()[0],
                    "retrograde": "",
                    "speed": 0,  # Speed of the fix star in degrees per day
                    "house": (
                        ""
                        if center == "Heliocentric"
                        else calculate_individual_house_position(
                            date, latitude, longitude, star_long, h_sys
                        )
                    ),
                }

                positions[star_name].update(
                    {
                        "decan_ruled_by": get_decan_ruler(
                            pos[0], positions[planet]["zodiac_sign"], classic_rulers
                        )
                    }
                )

            except Exception as e:
                pass
    if mode in ("planets", "asteroids"):
        for planet, id in bodies.items():
            if center == "topocentric":
                # Handle None altitude by defaulting to sea level (0.0)
                if altitude is None:
                    altitude = 0.0
                swe.set_topo(float(longitude), float(latitude), float(altitude))
                pos, ret = swe.calc_ut(jd, id, swe.FLG_TOPOCTR)
                pos_geo, ret_geo = swe.calc_ut(
                    jd, id
                )  # To get information about speed, retrograde etc.
                pos = list(pos)
                pos[3] = pos_geo[3]
                pos = tuple(pos)
            elif center == "heliocentric":
                pos, ret = swe.calc_ut(jd, id, swe.FLG_HELCTR)
                pos_geo, ret_geo = swe.calc_ut(jd, id)
                pos = list(pos)
                pos[3] = pos_geo[3] if planet != "Earth" else 0.9863
                pos = tuple(pos)
            else:
                pos, ret = swe.calc_ut(jd, id)

            if pos[3] < 0.001:
                retrograde_stationary = "R"
            elif pos[3] > 0.001:
                retrograde_stationary = ""
            else:
                retrograde_stationary = "S"

            positions[planet] = {
                "longitude": pos[0],
                "zodiac_sign": longitude_to_zodiac(pos[0], output).split()[0],
                "retrograde": "R" if pos[3] < 0 else "",
                "speed": pos[3],  # Speed of the planet in degrees per day
                "house": (
                    ""
                    if center == "Heliocentric"
                    else calculate_individual_house_position(
                        date, latitude, longitude, pos[0], h_sys
                    )
                ),
            }

            positions[planet].update(
                {
                    "decan_ruled_by": get_decan_ruler(
                        pos[0], positions[planet]["zodiac_sign"], classic_rulers
                    )
                }
            )

            if planet == "North Node":
                # Calculate the South Node
                south_node_longitude = (pos[0] + 180) % 360
                positions["South Node"] = {
                    "longitude": south_node_longitude,
                    "zodiac_sign": longitude_to_zodiac(
                        south_node_longitude, output
                    ).split()[0],
                    "retrograde": "R" if pos[3] < 0 else "",
                    "speed": pos[3],  # Same speed as North Node
                }
                positions["South Node"].update(
                    {
                        "decan_ruled_by": get_decan_ruler(
                            south_node_longitude,
                            positions[planet]["zodiac_sign"],
                            classic_rulers,
                        )
                    }
                )

            positions[planet].update(
                {
                    "decan_ruled_by": get_decan_ruler(
                        pos[0], positions[planet]["zodiac_sign"], classic_rulers
                    )
                }
            )

    # Calculate Ascendant and Midheaven, speed not exact but ok for now and only for approximately calculating aspect durations
    if mode == "planets" and center != "heliocentric":
        cusps, asc_mc = swe.houses(jd, latitude, longitude, h_sys.encode("utf-8"))
        positions["Ascendant"] = {
            "longitude": asc_mc[0],
            "zodiac_sign": longitude_to_zodiac(asc_mc[0], output).split()[0],
            "retrograde": "",
            "speed": 360,
        }
        positions["Midheaven"] = {
            "longitude": asc_mc[1],
            "zodiac_sign": longitude_to_zodiac(asc_mc[1], output).split()[0],
            "retrograde": "",
            "speed": 360,
        }
        positions["IC"] = {
            "longitude": cusps[3],
            "zodiac_sign": longitude_to_zodiac(cusps[3], output).split()[0],
            "retrograde": "",
            "speed": 360,
        }
        positions["DC"] = {
            "longitude": cusps[6],
            "zodiac_sign": longitude_to_zodiac(cusps[6], output).split()[0],
            "retrograde": "",
            "speed": 360,
        }

        # Fix south node
        PLANETS.update({"South Node": None})  # Add South Node to the list of planets
        positions["South Node"] = {
            "longitude": (positions["North Node"]["longitude"] + 180) % 360,
            "zodiac_sign": longitude_to_zodiac(
                (positions["North Node"]["longitude"] + 180) % 360, output
            ).split()[0],
            "retrograde": "",
            "speed": 0.05,
        }

        if arabic_parts:
            positions = add_arabic_parts(date, latitude, longitude, positions, output)

    house_positions, house_cusps = calculate_house_positions(
        date, latitude, longitude, altitude, positions, notime=False, h_sys=h_sys
    )

    for planet in positions:
        positions[planet]["house"] = house_positions.get(planet, {}).get("house", None)

    return positions


def calculate_sunrise_sunset(year, month, day, geopos):
    jd = swe.julday(year, month, day, 0)

    sunset_jd = swe.rise_trans(tjdut=jd, body=swe.SUN, geopos=geopos, rsmi=swe.CALC_SET)

    sunrise_jd = swe.rise_trans(
        tjdut=jd, body=swe.SUN, geopos=geopos, rsmi=swe.CALC_RISE
    )

    sunset_dt = swe.jdut1_to_utc(sunset_jd[1][0])
    sunset_dt = datetime(
        sunset_dt[0],
        sunset_dt[1],
        sunset_dt[2],
        sunset_dt[3],
        sunset_dt[4],
        int(sunset_dt[5]),
    )

    sunrise_dt = swe.jdut1_to_utc(sunrise_jd[1][0])
    sunrise_dt = datetime(
        sunrise_dt[0],
        sunrise_dt[1],
        sunrise_dt[2],
        sunrise_dt[3],
        sunrise_dt[4],
        int(sunrise_dt[5]),
    )

    return sunrise_dt, sunset_dt


def add_arabic_parts(date, latitude, longitude, positions, output):
    PLANETS.update(
        {
            "Fortune": None,
            "Spirit": None,
            "Love": None,
            "Marriage": None,
            "Friendship": None,
            "Death": None,
            "Commerce": None,
            "Passion": None,
        }
    )

    geopos = [longitude, latitude, 0]  # Elevation is set to 0 for now

    sunrise, sunset = calculate_sunrise_sunset(date.year, date.month, date.day, geopos)
    sunrise = sunrise.replace(tzinfo=date.tzinfo)
    sunset = sunset.replace(tzinfo=date.tzinfo)

    is_daytime = sunrise <= date < sunset

    fortune_pos = calculate_part_of_fortune(
        positions["Sun"]["longitude"],
        positions["Moon"]["longitude"],
        positions["Ascendant"]["longitude"],
        is_daytime,
    )
    spirit_pos = calculate_part_of_spirit(
        positions["Sun"]["longitude"],
        positions["Moon"]["longitude"],
        positions["Ascendant"]["longitude"],
        is_daytime,
    )
    love_pos = calculate_part_of_love(
        positions["Ascendant"]["longitude"],
        positions["Venus"]["longitude"],
        positions["Sun"]["longitude"],
    )
    marriage_pos = (
        positions["Venus"]["longitude"]
        + positions["Jupiter"]["longitude"]
        - positions["Saturn"]["longitude"]
    ) % 360
    friendship_pos = (
        positions["Moon"]["longitude"]
        + positions["Venus"]["longitude"]
        - positions["Sun"]["longitude"]
    ) % 360
    death_pos = (
        positions["Ascendant"]["longitude"]
        + positions["Saturn"]["longitude"]
        - positions["Moon"]["longitude"]
    ) % 360
    commerce_pos = (
        positions["Mercury"]["longitude"]
        + positions["Jupiter"]["longitude"]
        - positions["Sun"]["longitude"]
    ) % 360
    passion_pos = (
        positions["Ascendant"]["longitude"]
        + positions["Mars"]["longitude"]
        - positions["Venus"]["longitude"]
    ) % 360

    arabic_parts = {
        "Fortune": fortune_pos,
        "Spirit": spirit_pos,
        "Love": love_pos,
        "Marriage": marriage_pos,
        "Friendship": friendship_pos,
        "Death": death_pos,
        "Commerce": commerce_pos,
        "Passion": passion_pos,
    }

    for part, pos in arabic_parts.items():
        positions[part] = {
            "longitude": pos,
            "zodiac_sign": longitude_to_zodiac(pos, output).split()[0],
            "retrograde": "",
            "speed": 360,
        }

    return positions


def coord_in_minutes(longitude, output_type):
    """
    Convert a celestial longitude into degrees, minutes, and seconds format.

    This function is used to translate a decimal longitude (such as the position of a planet in the ecliptic coordinate system) into a format that is more commonly used in astrological and astronomical contexts, expressing the longitude in terms of degrees, minutes, and seconds.

    Parameters:
    - longitude (float): The ecliptic longitude to be converted, in decimal degrees.

    Returns:
    - str: The formatted string representing the longitude in degrees, minutes, and seconds (D°M'S'').
    """
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


def calculate_planetary_aspects(planet_positions, orbs, output_type, aspect_types):
    """
    Calculate astrological aspects between celestial bodies based on their positions,
    excluding predefined pairs such as Sun-Ascendant, and assuming minor aspects
    are included in aspect_types if necessary.

    Parameters:
    - planet_positions: A dictionary with celestial bodies as keys, each mapped to a
      dictionary containing 'longitude' and 'retrograde' status.
    - orb: The maximum orb (in degrees) to consider an aspect valid.
    - aspect_types: A dictionary of aspect names and their exact angles, possibly
      including minor aspects.

    Returns:
    - A list of tuples, each representing an aspect found between two celestial bodies.
      Each tuple includes the names of the bodies, the aspect name, and the exact angle.
    """
    # Pairs to exclude from the aspect calculations
    excluded_pairs = [
        {"Sun", "Ascendant"},
        {"Sun", "Midheaven"},
        {"DC", "Ascendant"},
        {"DC", "Midheaven"},
        {"DC", "IC"},
        {"Ascendant", "Midheaven"},
        {"South Node", "North Node"},
        {"Midheaven", "IC"},
        {"Ascendant", "IC"},
    ]

    aspects_found = {}
    planet_names = list(planet_positions.keys())

    for i, planet1 in enumerate(planet_names):
        for planet2 in planet_names[i + 1 :]:
            # Skip calculation if the pair is in the exclusion list or the same planet
            if ({planet1, planet2} in excluded_pairs) or (
                {planet2, planet1} in excluded_pairs
            ):
                continue

            long1 = planet_positions[planet1]["longitude"]
            long2 = planet_positions[planet2]["longitude"]
            angle_diff = (long1 - long2) % 360
            angle_diff = min(
                angle_diff, 360 - angle_diff
            )  # Normalize to <= 180 degrees

            for aspect_name, aspect_values in aspect_types.items():
                aspect_angle, aspect_score, aspect_comment = aspect_values.values()

                if aspect_name in MINOR_ASPECTS:
                    orb = orbs["Minor"]
                else:
                    orb = orbs["Major"]

                if abs(angle_diff - aspect_angle) <= orb:
                    # Check if the aspect is imprecise based on the movement per day of the planets involved
                    is_imprecise = any(
                        (planet in OFF_BY and OFF_BY[planet] > angle_diff)
                        or (planet in OFF_BY and OFF_BY[planet] < -angle_diff)
                        for planet in (planet1, planet2)
                    )

                    # Create a tuple for the planets involved in the aspect
                    planets_pair = (planet1, planet2)

                    # Update the aspects_found dictionary
                    angle_diff = angle_diff - aspect_angle  # Just show the difference

                    aspects_found[planets_pair] = {
                        "aspect_name": aspect_name,
                        "angle_diff": angle_diff,
                        "angle_diff_in_minutes": coord_in_minutes(
                            angle_diff, output_type
                        ),
                        "is_imprecise": is_imprecise,
                        "aspect_score": aspect_score,
                        "aspect_comment": aspect_comment,
                    }
    return aspects_found


def calculate_aspects_takes_two(
    natal_positions,
    second_positions,
    orbs,
    aspect_types,
    output_type,
    type,
    show_brief_aspects=False,
):
    """
    Calculate astrological aspects between natal and transit celestial bodies based on their positions,
    excluding predefined pairs such as Sun-Ascendant, and assuming minor aspects
    are included in aspect_types if necessary.

    Parameters:
    - natal_positions: A dictionary with natal celestial bodies as keys, each mapped to
      a dictionary containing 'longitude' and 'retrograde' status.
    - second_positions: A dictionary with another set of celestial bodies as keys, each mapped to
      a dictionary containing 'longitude' and 'retrograde' status.
    - orb: The maximum orb (in degrees) to consider an aspect valid.
    - aspect_types: A dictionary of aspect names and their exact angles, possibly
      including minor aspects.

    Returns:
    - A list of tuples, each representing an aspect found between a natal and a second celestial body.
      Each tuple includes the names of the bodies, the aspect name, and the exact angle.
    """
    excluded = ["Ascendant", "Midheaven", "IC", "DC"]

    aspects_found = {}
    natal_planet_names = list(natal_positions.keys())
    second_planet_names = list(second_positions.keys())

    for i, planet1 in enumerate(natal_planet_names):
        for planet2 in second_planet_names[i + 1 :]:
            if planet2 in excluded and type == "transits" and not show_brief_aspects:
                continue
            long1 = natal_positions[planet1]["longitude"]
            long2 = second_positions[planet2]["longitude"]
            angle_diff = (long1 - long2) % 360
            angle_diff = min(
                angle_diff, 360 - angle_diff
            )  # Normalize to <= 180 degrees

            for aspect_name, aspect_values in aspect_types.items():
                aspect_angle, aspect_score, aspect_comment = aspect_values.values()

                if type == "transits":
                    if OFF_BY[planet2] >= 0.5:  # 0.5 is the average speed of Mars
                        orb = orbs["Transit Fast"]
                    else:
                        orb = orbs["Transit Slow"]
                if type == "synastry":
                    if OFF_BY[planet2] >= 0.5:
                        orb = orbs["Synastry Fast"]
                    else:
                        orb = orbs["Synastry Slow"]
                if type == "asteroids":
                    orb = orbs["Asteroid"]
                if type == "stars":
                    orb = orbs["Fixed Star"]

                if abs(angle_diff - aspect_angle) <= orb:
                    # Check if the aspect is imprecise based on the movement per day of the planets involved
                    is_imprecise = any(
                        (planet in OFF_BY and OFF_BY[planet] > angle_diff)
                        or (planet in OFF_BY and OFF_BY[planet] < -angle_diff)
                        for planet in (planet1, planet2)
                    )

                    planets_pair = (planet1, planet2)

                    angle_diff = angle_diff - aspect_angle  # Just show the difference

                    aspects_found[planets_pair] = {
                        "aspect_name": aspect_name,
                        "angle_diff": angle_diff,
                        "angle_diff_in_minutes": coord_in_minutes(
                            angle_diff, output_type
                        ),
                        "is_imprecise": is_imprecise,
                        "aspect_score": aspect_score,
                        "aspect_comment": aspect_comment,
                    }
    return aspects_found


def julian_date_from_unix_time(t):
    # Not valid for dates before Oct 15, 1582
    return (t / 86400000) + 2440587.5


def unix_time_from_julian_date(jd):
    # Not valid for dates before Oct 15, 1582
    return (jd - 2440587.5) * 86400000


def constrain(d):
    t = d % 360
    if t < 0:
        t += 360
    return t


def get_illuminated_fraction_of_moon(jd: float):
    """
    Calculates the fraction of the moon's illumination based on the Julian Day.
    This method is based on Meeus' Astronomical Algorithms Second Edition, Chapter 48.

    Parameters:
    jd (float): The Julian Day for which the moon's illumination fraction is to be calculated.

    Returns:
    float: The fraction of the moon's disk that is illuminated, ranging from 0 (new moon) to 1 (full moon).
    """
    #  T is the number of Julian centuries since J2000: T=(jd−2451545)/36525.0
    #  k is the fraction (from 0.0 to 1.0) of the moon (approximated as a perfect sphere) which is illuminated as viewed from the Geocenter.

    #  D, M, M′are the Delaunay arguments. Respectively the Moon's mean elongation, the Sun's mean anomaly, and the Moon's mean anomaly.

    to_rad = pi / 180.0
    T = (jd - 2451545) / 36525.0

    D = (
        constrain(
            297.8501921
            + 445267.1114034 * T
            - 0.0018819 * T * T
            + 1.0 / 545868.0 * T * T * T
            - 1.0 / 113065000.0 * T * T * T * T
        )
        * to_rad
    )
    M = (
        constrain(
            357.5291092
            + 35999.0502909 * T
            - 0.0001536 * T * T
            + 1.0 / 24490000.0 * T * T * T
        )
        * to_rad
    )
    Mp = (
        constrain(
            134.9633964
            + 477198.8675055 * T
            + 0.0087414 * T * T
            + 1.0 / 69699.0 * T * T * T
            - 1.0 / 14712000.0 * T * T * T * T
        )
        * to_rad
    )

    i = (
        constrain(
            180
            - D * 180 / pi
            - 6.289 * sin(Mp)
            + 2.1 * sin(M)
            - 1.274 * sin(2 * D - Mp)
            - 0.658 * sin(2 * D)
            - 0.214 * sin(2 * Mp)
            - 0.11 * sin(D)
        )
        * to_rad
    )

    k = (1 + cos(i)) / 2
    return k


def moon_phase(date):
    """
    Calculates the moon phase and illumination for a given date. The function considers 8 distinct phases
    of the moon and returns the phase name and illumination percentage for the specified date.

    Parameters:
    - date (datetime): The date for which to calculate the moon phase and illumination.

    Returns:
    - a tuple (str: The name of the moon phase, float: the degree of moon illumination).

    The function considers 8 distinct phases of the moon and returns the phase name for the specified date.
    Doesn't take Earth's shadow into account.
    """
    jd = swe.julday(date.year, date.month, date.day)
    sun_pos = swe.calc_ut(jd, swe.SUN)[0][0]
    moon_pos = swe.calc_ut(jd, swe.MOON)[0][0]
    phase_angle = (moon_pos - sun_pos) % 360

    if date.tzinfo is None:
        date = date.replace(tzinfo=pytz.utc)

    # Use less precise method for dates before Oct 15, 1582 as precise method can't handle them.
    if date < datetime(1582, 10, 15, tzinfo=pytz.utc):
        illumination = 50 - 50 * cos(radians(phase_angle))
    else:
        illumination = get_illuminated_fraction_of_moon(jd) * 100

    if phase_angle < 45:
        return "New Moon", illumination
    elif phase_angle < 90:
        return "Waxing Crescent", illumination
    elif phase_angle < 135:
        return "First Quarter", illumination
    elif phase_angle < 180:
        return "Waxing Gibbous", illumination
    elif phase_angle < 225:
        return "Full Moon", illumination
    elif phase_angle < 270:
        return "Waning Gibbous", illumination
    elif phase_angle < 315:
        return "Last Quarter", illumination
    else:
        return "Waning Crescent", illumination


def house_count(house_counts, output, bold, nobold, br):
    house_count_string = f"{bold}House count{nobold}  "
    row = [house_count_string]

    sorted_star_house_counts = sorted(
        house_counts.items(), key=lambda item: item[1], reverse=True
    )

    for house, count in sorted_star_house_counts:
        if count > 0:
            if output == "text":
                house_count_string += (
                    f"{bold}{house}:{nobold} {Fore.GREEN}{count}{Style.RESET_ALL}, "
                )
            elif output in ("html", "return_html"):
                row.append(f"{bold}{house}:{nobold} {count}")
            else:
                house_count_string += f"{house}: {count}, "

    if output in ("html", "return_html"):
        table = tabulate([row], tablefmt="unsafehtml")
        house_count_string = table
    else:
        house_count_string = house_count_string[:-2]  # Remove the last comma and space
    return house_count_string


# Arabic Parts
def calculate_part_of_fortune(sun_pos, moon_pos, asc_pos, is_daytime):
    """Calculate the Part of Fortune"""
    if is_daytime:
        part_of_fortune = asc_pos + moon_pos - sun_pos
    else:
        part_of_fortune = asc_pos + sun_pos - moon_pos

    # Normalize to 0-360 degrees
    part_of_fortune = part_of_fortune % 360
    return part_of_fortune


def calculate_part_of_spirit(sun_pos, moon_pos, asc_pos, is_daytime):
    if is_daytime:
        part_of_spirit = asc_pos + sun_pos - moon_pos
    else:
        part_of_spirit = asc_pos + moon_pos - sun_pos

    part_of_spirit = part_of_spirit % 360
    return part_of_spirit


def calculate_part_of_love(asc_pos, venus_pos, sun_pos):
    """Calculate the Part of Love"""
    part_of_love = asc_pos + venus_pos - sun_pos
    part_of_love = part_of_love % 360
    return part_of_love


def get_sabian_symbol(planet_positions, planet: str):
    """
    Retrieve the Sabian symbol for a specific degree within a zodiac sign.

    Parameters:
    - degree (float): The degree within the zodiac sign for which to retrieve the Sabian symbol.
    - zodiac_sign (str): The zodiac sign in which the degree is located.

    Returns:
    - str: The Sabian symbol corresponding to the specified degree within the zodiac sign.
    """
    ephe = os.getenv("PRODUCTION_EPHE")
    if ephe:
        sabian_symbols = json.load(open(f"{ephe}/sabian.json"))
    else:
        if os.name == "nt":
            sabian_symbols = json.load(open(".\ephe\sabian.json"))
        else:
            sabian_symbols = json.load(open("./ephe/sabian.json"))
    zodiac_sign = planet_positions["Sun"]["zodiac_sign"]
    degree = int(planet_positions["Sun"]["longitude"]) - ZODIAC_DEGREES[zodiac_sign]

    return sabian_symbols[zodiac_sign][str(degree)]


def print_complex_aspects(
    complex_aspects,
    output,
    degree_in_minutes,
    degree_symbol,
    table_format,
    notime,
    bold,
    nobold,
    h4,
    h4_,
    p,
):
    to_return = ""
    if complex_aspects.get("T Squares", False):
        plur = "s" if len(complex_aspects["T Squares"]) > 1 else ""
        if output in ("text", "html"):
            print(f"{p}{bold}{h4}T-Square{plur}{h4_}{nobold}")
        else:
            to_return += f"{p}{bold}{h4}T-Square{plur}{h4_}{nobold}"
        headers = [
            "Planet 1",
            "Planet 2",
            f"{bold}Apex{nobold}",
            "Opposition",
            "Square 1",
            "Square 2",
        ]
        rows = []
        t_squares = complex_aspects.get("T Squares", False)
        for ts in t_squares:
            if degree_in_minutes:
                opp_deg = coord_in_minutes(ts[3], output)
                sq_deg1 = (
                    coord_in_minutes(ts[4], output) if degree_in_minutes else ts[4]
                )
                sq_deg2 = (
                    coord_in_minutes(ts[5], output) if degree_in_minutes else ts[5]
                )
            else:
                opp_deg = f"{ts[3]:.2f}{degree_symbol}"
                sq_deg1 = f"{ts[4]:.2f}{degree_symbol}"
                sq_deg2 = f"{ts[5]:.2f}{degree_symbol}"

            rows.append(
                [ts[0], ts[1], f"{bold}{ts[2]}{nobold}", opp_deg, sq_deg1, sq_deg2]
            )

        table = tabulate(rows, headers=headers, tablefmt=table_format, floatfmt=".2f")

        if output == "text":
            print(table + f"{p}")
        elif output == "html":
            print(table + f"{p}")
        elif output == "return_text":
            to_return += table + f"{p}"
        elif output == "return_html":
            to_return += table + f"{p}"

    if complex_aspects.get("Yods", False):
        plur = "s" if len(complex_aspects["Yods"]) > 1 else ""
        if output in ("text", "html"):
            print(f"{p}{bold}{h4}Yod{plur} (Finger{plur} of God){h4_}{nobold}")
        else:
            to_return += f"{p}{bold}{h4}Yod{plur} (Finger{plur} of God){h4_}{nobold}"
        headers = [
            "Planet 1",
            "Planet 2",
            f"{bold}Apex{nobold}",
            "Sextile",
            "Quincunx 1",
            "Quincunx 2",
        ]
        rows = []
        yods = complex_aspects["Yods"]

        for yod in yods:
            if degree_in_minutes:
                opp_deg = coord_in_minutes(yod[3], output)
                sq_deg1 = (
                    coord_in_minutes(yod[4], output) if degree_in_minutes else yod[4]
                )
                sq_deg2 = (
                    coord_in_minutes(yod[5], output) if degree_in_minutes else yod[5]
                )
            else:
                opp_deg = f"{yod[3]:.2f}{degree_symbol}"
                sq_deg1 = f"{yod[4]:.2f}{degree_symbol}"
                sq_deg2 = f"{yod[5]:.2f}{degree_symbol}"

            rows.append(
                [yod[0], yod[1], f"{bold}{yod[2]}{nobold}", opp_deg, sq_deg1, sq_deg2]
            )

        table = tabulate(rows, headers=headers, tablefmt=table_format, floatfmt=".2f")

        if output == "text":
            print(table + f"{p}")
        elif output == "html":
            print(table + f"{p}")
        elif output == "return_text":
            to_return += table + f"{p}"
        elif output == "return_html":
            to_return += table + f"{p}"

    if complex_aspects.get("Grand Crosses", False):
        plur = "es" if len(complex_aspects["Grand Crosses"]) > 1 else ""
        if output in ("text", "html"):
            print(f"{p}{bold}{h4}Grand Cross{plur}{h4_}{nobold}")
        else:
            to_return += f"{p}{bold}{h4}Grand Cross{plur}{h4_}{nobold}"

        headers = [
            "Planet 1",
            "Sq 1",
            "Planet 2",
            "Sq 2",
            "Planet 3",
            "Sq 3",
            "Planet 4",
            "Sq 4",
            "Opp 1",
            "Opp 2",
        ]
        rows = []
        grand_crosses = complex_aspects.get("Grand Crosses", False)

        for gc in grand_crosses:
            if degree_in_minutes:
                sq_deg1 = coord_in_minutes(gc[4], output)
                sq_deg2 = coord_in_minutes(gc[5], output)
                sq_deg3 = coord_in_minutes(gc[6], output)
                sq_deg4 = coord_in_minutes(gc[7], output)
                opp_deg1 = coord_in_minutes(gc[8], output)
                opp_deg2 = coord_in_minutes(gc[9], output)
            else:
                sq_deg1 = f"{gc[4]:.2f}{degree_symbol}"
                sq_deg2 = f"{gc[5]:.2f}{degree_symbol}"
                sq_deg3 = f"{gc[6]:.2f}{degree_symbol}"
                sq_deg4 = f"{gc[7]:.2f}{degree_symbol}"
                opp_deg1 = f"{gc[8]:.2f}{degree_symbol}"
                opp_deg2 = f"{gc[9]:.2f}{degree_symbol}"

            rows.append(
                [
                    gc[0],
                    sq_deg1,
                    gc[1],
                    sq_deg2,
                    gc[2],
                    sq_deg3,
                    gc[3],
                    sq_deg4,
                    opp_deg1,
                    opp_deg2,
                ]
            )

        table = tabulate(rows, headers=headers, tablefmt=table_format, floatfmt=".2f")

        if output == "text":
            print(table + f"{p}")
        elif output == "html":
            print(table + f"{p}")
        elif output == "return_text":
            to_return += table + f"{p}"
        elif output == "return_html":
            to_return += table + f"{p}"

    if complex_aspects.get("Grand Trines", False):
        plur = "s" if len(complex_aspects["Grand Trines"]) > 1 else ""
        if output in ("text", "html"):
            print(f"{p}{bold}{h4}Grand Trine{plur}{h4_}{nobold}")
        else:
            to_return += f"{p}{bold}{h4}Grand Trine{plur}{h4_}{nobold}"
        headers = [
            "Planet 1",
            "Sextile 1",
            "Planet 2",
            "Sextile 2",
            "Planet 3",
            "Sextile 3",
        ]
        rows = []
        grand_trines = complex_aspects["Grand Trines"]

        for trine in grand_trines:
            if degree_in_minutes:
                trine1_diff = coord_in_minutes(trine[3], output)
                trine2_diff = (
                    coord_in_minutes(trine[4], output)
                    if degree_in_minutes
                    else trine[4]
                )
                trine3_diff = (
                    coord_in_minutes(trine[5], output)
                    if degree_in_minutes
                    else trine[5]
                )
            else:
                trine1_diff = f"{trine[3]:.2f}{degree_symbol}"
                trine2_diff = f"{trine[4]:.2f}{degree_symbol}"
                trine3_diff = f"{trine[5]:.2f}{degree_symbol}"

            rows.append(
                [trine[0], trine1_diff, trine[1], trine2_diff, trine[2], trine3_diff]
            )

        table = tabulate(rows, headers=headers, tablefmt=table_format, floatfmt=".2f")

        if output == "text":
            print(table + f"{p}")
        elif output == "html":
            print(table + f"{p}")
        elif output == "return_text":
            to_return += table + f"{p}"
        elif output == "return_html":
            to_return += table + f"{p}"

    if complex_aspects.get("Kites", False):
        plur = "s" if len(complex_aspects["Kites"]) > 1 else ""
        if output in ("text", "html"):
            print(f"{p}{bold}{h4}Kite{plur}{h4_}{nobold}")
        else:
            to_return += f"{p}{bold}{h4}Kite{plur}{h4_}{nobold}"
        headers = [
            "Planet 1",
            "Sextile 1",
            "Planet 2",
            "Sextile 2",
            "Planet 3",
            "Sextile 3",
            "Opposition",
            "Degree",
        ]
        rows = []
        kites = complex_aspects["Kites"]

        for trine in kites:
            if degree_in_minutes:
                trine1_diff = coord_in_minutes(trine[4], output)
                trine2_diff = coord_in_minutes(trine[5], output)
                trine3_diff = coord_in_minutes(trine[6], output)
                oppo_diff = coord_in_minutes(trine[7], output)
            else:
                trine1_diff = f"{trine[4]:.2f}{degree_symbol}"
                trine2_diff = f"{trine[5]:.2f}{degree_symbol}"
                trine3_diff = f"{trine[6]:.2f}{degree_symbol}"
                oppo_diff = f"{trine[7]:.2f}{degree_symbol}"

            rows.append(
                [
                    trine[0],
                    trine1_diff,
                    trine[1],
                    trine2_diff,
                    trine[2],
                    trine3_diff,
                    trine[3],
                    oppo_diff,
                ]
            )

        table = tabulate(rows, headers=headers, tablefmt=table_format, floatfmt=".2f")

        if output == "text":
            print(table + f"{p}")
        elif output == "html":
            print(table + f"{p}")
        elif output == "return_text":
            to_return += table + f"{p}"
        elif output == "return_html":
            to_return += table + f"{p}"
    return to_return


def print_planet_positions(
    planet_positions,
    degree_in_minutes=False,
    notime=False,
    house_positions=None,
    orb=1,
    output_type="text",
    hide_decans=False,
    classic_rulers=False,
    center="geocentric",
    pluto_ecliptic=None,
):
    """
    Print the positions of planets in a human-readable format. This includes the zodiac sign,
    degree (optionally in minutes), whether the planet is retrograde, and its house position
    if available.

    Parameters:
    - planet_positions (dict): A dictionary with celestial bodies as keys and dictionaries as values,
      containing 'longitude', 'zodiac_sign', 'retrograde', and optionally 'house'.
    - degree_in_minutes (bool): If True, display the longitude in degrees, minutes, and seconds.
      Otherwise, display only in decimal degrees.
    - notime (bool): If True, house information is considered irrelevant or unavailable.
    - house_positions (dict, optional): Additional dictionary mapping planets to their house positions,
      if this information is available.
    - orb (float): The orb value to consider when determining the preciseness of the planet's position.
      This parameter might not be directly used in this function but is included for consistency with the
      overall structure of the astrological calculations.
    """

    sign_counts = {sign: {"count": 0, "planets": []} for sign in ZODIAC_ELEMENTS.keys()}
    modality_counts = {
        modality: {"count": 0, "planets": []} for modality in ZODIAC_MODALITIES.keys()
    }
    element_counts = {"Fire": 0, "Earth": 0, "Air": 0, "Water": 0}
    planet_house_counts = {house: 0 for house in range(1, 13)}

    zodiac_table_data = []

    if output_type in ("html", "return_html"):
        table_format = "html"
        bold = "<b>"
        nobold = "</b>"
        br = "\n<br>"
        p = "\n<p>"
    elif output_type == "text":
        table_format = "simple"
        bold = "\033[1m"
        nobold = "\033[0m"
        br = "\n"
        p = "\n"
    else:
        table_format = "simple"
        bold = ""
        nobold = ""
        br = "\n"
        p = "\n"

    degree_symbol = (
        "" if (os.name == "nt" and output_type == "html") else "°"
    )  # If running on Windows, don't use degree symbol for html output

    # Define headers based on whether house positions should be included
    if center == "heliocentric":
        headers = ["Planet", "Zodiac", "Degree"]
    else:
        headers = [
            "Planet",
            "Zodiac",
            "Degree",
            "Retrograde" if output_type in ("html", "return_html") else "R",
        ]

    if house_positions and (not notime and not center == "heliocentric"):
        headers.append("House")
    headers.append("Dignity")
    if notime:
        headers.insert(3, "Off by")
    if not hide_decans:
        headers.append(
            "Decan ruler" if output_type in ("html", "return_html") else "Decan"
        )

    planet_signs = {}

    for planet, info in planet_positions.items():
        if notime and (planet in ALWAYS_EXCLUDE_IF_NO_TIME):
            continue
        longitude = info["longitude"]
        degrees_within_sign = longitude % 30
        position = (
            coord_in_minutes(degrees_within_sign, output_type)
            if degree_in_minutes
            else f"{degrees_within_sign:.2f}{degree_symbol}"
        )
        retrograde = info["retrograde"]
        zodiac = info["zodiac_sign"]
        retrograde_status = retrograde  # "R" if retrograde else ""
        decan_ruler = info.get("decan_ruled_by", "")

        planet_signs[planet] = zodiac
        strength_check = assess_planet_strength(planet_signs, classic_rulers)
        elevation_check = is_planet_elevated(planet_positions)
        degree_check = check_degree(planet_signs, degrees_within_sign)

        if (
            not notime and not center == "heliocentric"
        ):  # assuming that we have the house positions if not notime
            house_num = house_positions.get(planet, {}).get("house", "Unknown")
            planet_positions[planet] = house_num
            if house_num:
                planet_house_counts[house_num] += 1

        if center == "heliocentric":
            row = [planet, zodiac, position]
        else:
            row = [planet, zodiac, position, retrograde_status]

        if notime and planet in OFF_BY.keys() and OFF_BY[planet] > orb:
            off_by = f"±{OFF_BY[planet]}{degree_symbol}"
            row.insert(3, off_by)
        elif notime:
            off_by = ""
            row.insert(3, off_by)
        if house_positions and not notime and not center == "heliocentric":
            house_num = house_positions.get(planet, {}).get("house", "Unknown")
            row.insert(4, house_num)
        row.append(
            elevation_check[planet]
            + strength_check[planet]
            + degree_check[planet]
            + (f" {pluto_ecliptic}" if planet == "Pluto" else "")
        )
        if not hide_decans:
            row.append(decan_ruler)

        if (planet == "Fortune" or planet == "Ascendant") and output_type in (
            "text",
            "return_text",
        ):
            zodiac_table_data.append(SEPARATING_LINE)
        zodiac_table_data.append(row)

        # Count zodiac signs, elements and modalities
        sign_counts[zodiac]["count"] += 1
        sign_counts[zodiac]["planets"].append(planet)
        modality = ZODIAC_SIGN_TO_MODALITY[zodiac]
        modality_counts[modality]["count"] += 1
        modality_counts[modality]["planets"].append(planet)
        element_counts[ZODIAC_ELEMENTS[zodiac]] += 1

    table_format = "html" if output_type in ("html", "return_html") else "simple"

    to_return = ""
    table = tabulate(
        zodiac_table_data, headers=headers, tablefmt=table_format, floatfmt=".2f"
    )

    if output_type in ("text", "html"):
        print(table)
    to_return += table

    sign_count_table_data = list()
    element_count_table_data = list()
    modality_count_table_data = list()

    ## House counts
    if not notime and not center == "heliocentric":
        if output_type in ("return_text", "return_html"):
            to_return += f"{p}" + house_count(
                planet_house_counts, output_type, bold, nobold, br
            )
        else:
            print(
                f"{p}" + house_count(planet_house_counts, output_type, bold, nobold, br)
            )

    # Print zodiac sign, element and modality counts
    if output_type in ("html"):
        print(f"{p}<div class='table-container'>")
    if output_type == "return_html":
        to_return += f"{p}<div class='table-container'>"

    for sign, data in sign_counts.items():
        if data["count"] > 0:
            row = [
                sign,
                data["count"],
                ", ".join(data["planets"])
                + (" (stellium)" if data["count"] >= 4 else ""),
            ]
            sign_count_table_data.append(row)

    table = tabulate(
        sign_count_table_data,
        headers=["Sign", "Nr", "Planets in Sign".title()],
        tablefmt=table_format,
        floatfmt=".2f",
    )
    to_return += f"{br}{br}{table}"
    if output_type in ("text", "html"):
        print(f"{p}{table}{br}")

    for element, count in element_counts.items():
        if count > 0:
            row = [element, count]
            element_count_table_data.append(row)

    # Check nr of day and night signs
    fire_count = next(
        (item[1] for item in element_count_table_data if item[0] == "Fire"), 0
    )
    air_count = next(
        (item[1] for item in element_count_table_data if item[0] == "Air"), 0
    )
    earth_count = next(
        (item[1] for item in element_count_table_data if item[0] == "Earth"), 0
    )
    water_count = next(
        (item[1] for item in element_count_table_data if item[0] == "Water"), 0
    )

    nr_day_signs = fire_count + air_count
    nr_night_signs = earth_count + water_count
    if output_type in ("text", "return_text"):
        element_count_table_data.append(SEPARATING_LINE)
    element_count_table_data.append(["Day signs", nr_day_signs])
    element_count_table_data.append(["Night signs", nr_night_signs])

    table = tabulate(
        element_count_table_data,
        headers=["Element", "Nr"],
        tablefmt=table_format,
        floatfmt=".2f",
    )
    to_return += f"{br}{br}{table}"
    if output_type in ("text", "html"):
        print(table + f"{br}")

    for modality, info in modality_counts.items():
        row = [modality, info["count"], ", ".join(info["planets"])]
        modality_count_table_data.append(row)
    table = tabulate(
        modality_count_table_data,
        headers=["Modality", "Nr", "Planets"],
        tablefmt=table_format,
    )
    to_return += f"{br}{br}{table}"
    if output_type in ("text", "html"):
        print(table + f"{br}")
        if output_type == "html":
            print("</div>")
    elif output_type == "return_html":
        to_return += "</div>"

    return to_return


def print_aspects(
    aspects,
    planet_positions,
    orbs,
    transit_planet_positions=None,
    imprecise_aspects="off",
    minor_aspects=True,
    degree_in_minutes=False,
    house_positions=None,
    orb=1,
    type="Natal",
    p1_name="",
    p2_name="",
    notime=False,
    output="text",
    show_aspect_score=False,
    star_positions=None,
    complex_aspects=None,
    center="geocentric",
):
    """
    Prints astrological aspects between celestial bodies, offering options for display and filtering.
    """
    if output in ("html", "return_html"):
        table_format = "unsafehtml"
        house_called = "House"
        bold = "<b>"
        nobold = "</b>"
        br = "\n<br>"
        p = "\n<p>"
        h3 = "<h3>"
        h3_ = "</h3>"
    elif output == "text":
        table_format = "simple"
        house_called = "H"
        bold = "\033[1m"
        nobold = "\033[0m"
        br = "\n"
        p = "\n"
        h3 = ""
        h3_ = ""
    else:
        table_format = "simple"
        house_called = "H"
        bold = ""
        nobold = ""
        br = "\n"
        p = "\n"
        h3 = ""
        h3_ = ""

    degree_symbol = "" if (os.name == "nt" and output == "html") else "°"
    orb_string_major_minor = (
        f"(major {orbs['Major']}{degree_symbol} minor {orbs['Minor']}{degree_symbol} orb)"
        if minor_aspects
        else f"({orbs['Major']}{degree_symbol} orb)"
    )
    orb_string_transits_fast_slow = f"(fast {orbs['Transit Fast']}{degree_symbol} slow {orbs['Transit Slow']}{degree_symbol} orb)"
    orb_string_synastry_fast_slow = f"(fast {orbs['Synastry Fast']}{degree_symbol} slow {orbs['Synastry Slow']}{degree_symbol} orb)"

    planetary_aspects_table_data = []
    if notime or center == "heliocentric":
        if type == "Transit":
            headers = [
                "Natal Planet",
                "Aspect",
                "Transit Planet",
                "Degree",
                "Exact",
                "Rem. Duration",
            ]
        if type == "Star Transit":
            headers = [
                "Natal Star",
                "Aspect",
                "Transit Planet",
                "Degree",
                "Exact",
                "Rem. Duration",
            ]
        if type == "Asteroids Transit":
            headers = [
                "Natal Asteroid",
                "Aspect",
                "Transit Planet",
                "Degree",
                "Exact",
                "Rem. Duration",
            ]
        elif type == "Synastry":
            headers = [p1_name, "Aspect", p2_name, "Degree", "Off by"]
        elif type == "Asteroids":
            headers = [
                "Natal Planet",
                house_called,
                "Aspect",
                "Natal Asteroid",
                house_called,
                "Degree",
            ]
        elif type == "Natal":
            headers = ["Planet", "Aspect", "Planet", "Degree", "Off by"]
    else:
        if type == "Transit":
            headers = [
                "Natal Planet",
                house_called,
                "Aspect",
                "Transit Planet",
                house_called,
                "Degree",
                "Exact",
                "Rem. Duration",
            ]
        if type == "Star Transit":
            headers = [
                "Natal Star",
                house_called,
                "Aspect",
                "Transit Planet",
                house_called,
                "Degree",
                "Exact",
                "Rem. Duration",
            ]
        if type == "Asteroids Transit":
            headers = [
                "Natal Asteroid",
                house_called,
                "Aspect",
                "Transit Planet",
                house_called,
                "Degree",
                "Exact",
                "Rem. Duration",
            ]
        elif type == "Synastry":
            headers = [
                p1_name,
                house_called,
                "Aspect",
                p2_name,
                house_called,
                "Degree",
                "Off by",
            ]
        elif type == "Asteroids":
            headers = [
                "Natal Planet",
                house_called,
                "Aspect",
                "Natal Asteroid",
                house_called,
                "Degree",
            ]
        elif type == "Natal":
            headers = [
                "Planet",
                house_called,
                "Aspect",
                "Planet",
                house_called,
                "Degree",
                "Off by",
            ]

    if show_aspect_score:
        headers.append("Score")
    to_return = ""

    if output in ("text", "html"):
        if type == "Asteroids":
            print(
                f"{p}{bold}{h3}Asteroid Aspects ({orbs['Asteroid']}{degree_symbol} orb){nobold}",
                end="",
            )
        elif type == "Transit":
            print(
                f"{p}{bold}{h3}Planetary Transit Aspects {orb_string_transits_fast_slow}{nobold}",
                end="",
            )
        elif type == "Star Transit":
            print(
                f"{p}{bold}{h3}Star Transit Aspects {orb_string_transits_fast_slow}{nobold}",
                end="",
            )
        elif type == "Asteroids Transit":
            print(
                f"{p}{bold}{h3}Asteroid Transit Aspects {orb_string_transits_fast_slow}{nobold}",
                end="",
            )
        elif type == "Synastry":
            print(
                f"{p}{bold}{h3}Planetary Synastry Aspects {orb_string_synastry_fast_slow}{nobold}",
                end="",
            )
        else:
            print(
                f"{p}{bold}{h3}Planetary Aspects {orb_string_major_minor}{nobold}",
                end="",
            )
        print(
            f"{bold} including minor aspects{nobold}" if minor_aspects else "", end=""
        )
        if notime:
            print(
                f"{bold} with imprecise aspects set to {imprecise_aspects}{nobold}",
                end="",
            )
        print(f"{h3_}")
    else:
        if type == "Asteroids":
            to_return = f"{p}{bold}{h3}Asteroid Aspects ({orbs['Asteroid']}{degree_symbol} orb{nobold})"
        elif type == "Transit":
            to_return += f"{p}{bold}{h3}Planetary Transit Aspects {orb_string_transits_fast_slow}{nobold}"
        elif type == "Star Transit":
            to_return += f"{p}{bold}{h3}Star Transit Aspects {orb_string_transits_fast_slow}{nobold}"
        elif type == "Asteroids Transit":
            to_return += f"{p}{bold}{h3}Asteroid Transit Aspects {orb_string_transits_fast_slow}{nobold}"
        elif type == "Synastry":
            to_return += f"{p}{bold}{h3}Planetary Synastry Aspects {orb_string_synastry_fast_slow}{nobold}"
        else:
            to_return = (
                f"{p}{bold}{h3}Planetary Aspects {orb_string_major_minor}{nobold}"
            )
        if minor_aspects:
            to_return += f"{bold} including minor aspects{nobold}"
        if notime:
            to_return += (
                f"{bold} with imprecise aspects set to {imprecise_aspects}{nobold}"
            )
        to_return += f"{h3_}"

    aspect_type_counts = {}
    hard_count = 0
    soft_count = 0
    hard_count_score = 0
    soft_count_score = 0
    house_counts = {house: 0 for house in range(1, 13)}

    all_aspects = {**SOFT_ASPECTS, **HARD_ASPECTS}

    off_by_column = False  # Check if any planets use the off by column

    for planets, aspect_details in aspects.items():
        if (
            planets[0] in ALWAYS_EXCLUDE_IF_NO_TIME
            or planets[1] in ALWAYS_EXCLUDE_IF_NO_TIME
        ) and notime:
            continue
        if (
            imprecise_aspects == "off"
            and ((planets[0] in OFF_BY.keys() or planets[1] in OFF_BY.keys()))
            and notime
        ):
            if round(OFF_BY.get(planets[0], 0) + OFF_BY.get(planets[1], 0), 2) > orb:
                continue
        if degree_in_minutes:
            angle_with_degree = f"{aspect_details['angle_diff_in_minutes']}".strip("-")
        else:
            if type in ("Transit", "Star Transit", "Asteroids Transit"):
                angle_with_degree = f"{aspect_details['angle_diff']:.2f}{degree_symbol}"
            else:
                angle_with_degree = (
                    f"{aspect_details['angle_diff']:.2f}{degree_symbol}".strip("-")
                )
        if imprecise_aspects == "off" and (
            aspect_details["is_imprecise"]
            or planets[0] in ALWAYS_EXCLUDE_IF_NO_TIME
            or planets[1] in ALWAYS_EXCLUDE_IF_NO_TIME
        ):
            continue
        else:
            if notime or center == "heliocentric":
                if type in ("Transit", "Star Transit", "Asteroids Transit"):
                    row = [
                        planets[0],
                        aspect_details["aspect_name"],
                        planets[1],
                        angle_with_degree,
                        ("In " if aspect_details["angle_diff"] < 0 else "")
                        + calculate_aspect_duration(
                            planet_positions,
                            planets[1],
                            0 - aspect_details["angle_diff"],
                        )
                        + (" ago" if aspect_details["angle_diff"] > 0 else ""),
                        calculate_aspect_duration(
                            planet_positions,
                            planets[1],
                            orb - aspect_details["angle_diff"],
                        ),
                    ]
                elif type == "Synastry" or type == "Asteroids":
                    row = [
                        planets[0],
                        aspect_details["aspect_name"],
                        planets[1],
                        angle_with_degree,
                    ]
                # elif type == "Star Transit":
                #     row = [planets[0], aspect_details['aspect_name'], planets[1], angle_with_degree,
                #         ("In " if aspect_details['angle_diff'] < 0 else "") + calculate_aspect_duration(planet_positions, planets[1], 0-aspect_details['angle_diff']) + (" ago" if aspect_details['angle_diff'] > 0 else ""),
                #         calculate_aspect_duration(planet_positions, planets[1], orb-aspect_details['angle_diff'])]
                # elif type == "Asteroids Transit":
                #     row = [planets[0], aspect_details['aspect_name'], planets[1], angle_with_degree,
                #         ("In " if aspect_details['angle_diff'] < 0 else "") + calculate_aspect_duration(planet_positions, planets[1], 0-aspect_details['angle_diff']) + (" ago" if aspect_details['angle_diff'] > 0 else ""),
                #         calculate_aspect_duration(planet_positions, planets[1], orb-aspect_details['angle_diff'])]
                else:
                    row = [
                        planets[0],
                        aspect_details["aspect_name"],
                        planets[1],
                        angle_with_degree,
                    ]
            else:
                if type == "Transit":
                    row = [
                        planets[0],
                        planet_positions[planets[0]]["house"],
                        aspect_details["aspect_name"],
                        planets[1],
                        transit_planet_positions[planets[1]]["house"],
                        angle_with_degree,
                        ("In " if aspect_details["angle_diff"] < 0 else "")
                        + calculate_aspect_duration(
                            planet_positions,
                            planets[1],
                            0 - aspect_details["angle_diff"],
                        )
                        + (" ago" if aspect_details["angle_diff"] > 0 else ""),
                        calculate_aspect_duration(
                            planet_positions,
                            planets[1],
                            orb - aspect_details["angle_diff"],
                        ),
                    ]
                elif type == "Synastry" or type == "Asteroids":
                    row = [
                        planets[0],
                        planet_positions[planets[0]]["house"],
                        aspect_details["aspect_name"],
                        planets[1],
                        transit_planet_positions[planets[1]]["house"],
                        angle_with_degree,
                    ]
                elif type == "Star Transit":
                    row = [
                        planets[0],
                        star_positions[planets[0]]["house"],
                        aspect_details["aspect_name"],
                        planets[1],
                        transit_planet_positions[planets[1]]["house"],
                        angle_with_degree,
                        ("In " if aspect_details["angle_diff"] < 0 else "")
                        + calculate_aspect_duration(
                            copy.deepcopy(planet_positions),
                            planets[1],
                            0 - aspect_details["angle_diff"],
                        )
                        + (" ago" if aspect_details["angle_diff"] > 0 else ""),
                        calculate_aspect_duration(
                            copy.deepcopy(planet_positions),
                            planets[1],
                            orb - aspect_details["angle_diff"],
                        ),
                    ]
                elif type == "Asteroids Transit":
                    row = [
                        planets[0],
                        star_positions[planets[0]]["house"],
                        aspect_details["aspect_name"],
                        planets[1],
                        transit_planet_positions[planets[1]]["house"],
                        angle_with_degree,
                        ("In " if aspect_details["angle_diff"] < 0 else "")
                        + calculate_aspect_duration(
                            planet_positions,
                            planets[1],
                            0 - aspect_details["angle_diff"],
                        )
                        + (" ago" if aspect_details["angle_diff"] > 0 else ""),
                        calculate_aspect_duration(
                            planet_positions,
                            planets[1],
                            orb - aspect_details["angle_diff"],
                        ),
                    ]
                else:
                    row = [
                        planets[0],
                        planet_positions[planets[0]]["house"],
                        aspect_details["aspect_name"],
                        planets[1],
                        planet_positions[planets[1]]["house"],
                        angle_with_degree,
                    ]
                if house_counts and not notime:
                    if star_positions:
                        house_counts[star_positions[planets[0]]["house"]] += 1
                    else:
                        if planet_positions[planets[0]].get("house", False):
                            house_counts[planet_positions[planets[0]]["house"]] += 1
                    if not type == "Natal":
                        if transit_planet_positions[planets[1]].get("house", False):
                            house_counts[
                                transit_planet_positions[planets[1]]["house"]
                            ] += 1

        if (
            imprecise_aspects == "warn"
            and ((planets[0] in OFF_BY.keys() or planets[1] in OFF_BY.keys()))
            and notime
        ):
            if float(OFF_BY[planets[0]]) > orb or float(OFF_BY[planets[1]]) > orb:
                off_by = str(
                    round(OFF_BY.get(planets[0], 0) + OFF_BY.get(planets[1], 0), 2)
                )
                row.append(" ± " + off_by)
                off_by_column = True
            else:
                row.append("")
        if show_aspect_score:
            row.append(
                calculate_aspect_score(
                    aspect_details["aspect_name"], aspect_details["angle_diff"]
                )
            )

        planetary_aspects_table_data.append(row)

        # Add or update the count of the aspect type
        aspect_name = aspect_details["aspect_name"]
        if aspect_name in aspect_type_counts:
            aspect_type_counts[aspect_name] += 1
        else:
            aspect_type_counts[aspect_name] = 1
        if aspect_name in HARD_ASPECTS:
            hard_count += 1
            hard_count_score += aspect_details["aspect_score"]
        elif aspect_name in SOFT_ASPECTS:
            soft_count += 1
            soft_count_score += aspect_details["aspect_score"]

    # If no aspects found
    if len(planetary_aspects_table_data) < 1:
        return ""

    # Sorting
    if notime or center == "heliocentric":
        planetary_aspects_table_data.sort(
            key=lambda x: x[3]
        )  # Sort by degree of aspect
    else:
        planetary_aspects_table_data.sort(key=lambda x: x[5])  # 2 more columns

    if not off_by_column:
        try:
            headers.remove("Off by")
        except:
            pass

    table = tabulate(
        planetary_aspects_table_data,
        headers=headers,
        tablefmt=table_format,
        floatfmt=".2f",
        colalign=(
            ("left", "left", "left", "right", "left", "left")
            if (type == "Transit" and center == "geocentric")
            else ""
        ),
    )

    if output in ("text", "html"):
        if output == "html":
            print('<div class="table-container">')
        print(f"{table}")
    if output == "return_html":
        to_return += '<div class="table-container">'
    if output in ("return_text", "return_html"):
        to_return += f"{br}" + table

    # Convert aspect type dictionary to a list of tuples
    aspect_data = list(aspect_type_counts.items())
    aspect_data.sort(key=lambda x: x[1], reverse=True)  # Sort by degree of aspect

    # Convert aspect_data to a list of lists
    aspect_data = [
        [aspect_data[i][0], aspect_data[i][1], list(all_aspects[aspect[0]].values())[2]]
        for i, aspect in enumerate(aspect_data)
    ]

    headers = ["Aspect Type", "Count", "Meaning"]
    table = tabulate(aspect_data, headers=headers, tablefmt=table_format)

    if output in ("html", "return_html"):
        div_string = '</div><div style="text-align: left; padding-bottom: 20px; padding-left: 20px;">'
    else:
        div_string = ""

    if hard_count + soft_count > 0:
        if output in ("html, return_html"):
            row = [
                f"{bold}Hard Aspects:{nobold}",
                hard_count,
                f"{bold}Soft Aspects:{nobold}",
                soft_count,
                f"{bold}Score:{nobold}",
                f"{(hard_count_score + soft_count_score)/(hard_count+soft_count):.1f}".rstrip(
                    "0"
                ).rstrip(
                    "."
                ),
            ]
            score_table = tabulate([row], tablefmt="unsafehtml")
            aspect_count_text = f"{div_string}{p}{score_table}"
        else:
            aspect_count_text = f"{div_string}{p}{bold}Hard Aspects:{nobold} {hard_count}, {bold}Soft Aspects:{nobold} {soft_count}, {bold}Score:{nobold} {(hard_count_score + soft_count_score)/(hard_count+soft_count):.1f}".rstrip(
                "0"
            ).rstrip(
                "."
            )
    else:
        aspect_count_text = f"{div_string}{p}No aspects found."
    to_return += f"{br}" + table + aspect_count_text

    # Print counts of each aspect type
    if output in ("text", "html"):
        print(f"{br}" + table + f"{p}" + aspect_count_text)

    # House counts only if time specified and more aspects than one, and not heliocentric
    if not notime and len(aspects) > 1 and not center == "heliocentric":
        if output in ("return_text", "return_html"):
            to_return += f"{p}" + house_count(house_counts, output, bold, nobold, br)
        else:
            if output == "html":
                print(p)
            print(house_count(house_counts, output, bold, nobold, br))

    if complex_aspects:
        to_return += print_complex_aspects(
            complex_aspects,
            output,
            degree_in_minutes,
            degree_symbol,
            table_format,
            notime,
            bold,
            nobold,
            h4,
            h4_,
            p,
        )

    if output == "html":
        print("</div>")
    if output == "return_html":
        to_return += "</div>"

    if output in ("text", "html"):
        if not house_positions:
            print(f"{p}* No time of day specified. Houses cannot be calculated. ")
            print("  Aspects to the Ascendant and Midheaven are not available.")
            print(
                "  The positions of the Sun, Moon, Mercury, Venus, and Mars are uncertain.\n"
            )
            print(f"{p}  Please specify the time of birth for a complete chart.\n")
    else:
        if not house_positions:
            to_return += f"{p}* No time of day specified. Houses cannot be calculated. "
            to_return += (
                f"{p}  Aspects to the Ascendant and Midheaven are not available."
            )
            to_return += f"{p}  The positions of the Sun, Moon, Mercury, Venus, and Mars are uncertain.\n"
            to_return += (
                f"{p}  Please specify the time of birth for a complete chart.\n"
            )

    return to_return


def print_fixed_star_aspects(
    aspects,
    orb=1,
    minor_aspects=False,
    imprecise_aspects="off",
    notime=True,
    degree_in_minutes=False,
    house_positions=None,
    stars=None,
    output="text",
    show_aspect_score=False,
    all_stars=False,
    center="topocentric",
) -> str:
    """
    Prints aspects between planets and fixed stars with options for minor aspects, precision warnings, and house positions.

    Parameters:
    - aspects (list): Aspects between planets and fixed stars.
    - orb (float): Orb for aspect significance.
    - minor_aspects (bool): Include minor aspects.
    - imprecise_aspects (str): Handle imprecise aspects ('off' or 'warn').
    - notime (bool): Exclude time-dependent data.
    - degree_in_minutes (bool): Show angles in degrees, minutes, and seconds.
    - house_positions (dict, optional): Mapping of fixed stars to house poitions.
    - all_stars (bool): Include aspects for all stars or significant ones only.

    Outputs a formatted list of aspects to the console based on the provided parameters.
    """
    to_return = ""
    if output in ("html", "return_html"):
        table_format = "html"
        bold = "<b>"
        nobold = "</b>"
        br = "\n<br>"
        p = "\n<p>"
        h3 = "<h3>"
        h3_ = "</h3>"
    elif output == "text":
        table_format = "simple"
        bold = "\033[1m"
        nobold = "\033[0m"
        br = "\n"
        p = "\n"
        h3 = ""
        h3_ = ""
    elif output == "return_text":
        table_format = "simple"
        bold = ""
        nobold = ""
        br = "\n"
        p = "\n"
        h3 = ""
        h3_ = ""
    degree_symbol = "" if (os.name == "nt" and output == "html") else "°"

    if output in ("text", "html"):
        print(
            f"{p}{bold}{h3}Fixed Star Aspects ({orb}{degree_symbol} orb){nobold}",
            end="",
        )
        print(
            f"{bold} including minor aspects{nobold}" if minor_aspects else "", end=""
        )
        if notime:
            print(
                f"{bold} with Imprecise Aspects set to {imprecise_aspects}{nobold}",
                end="",
            )
        print(f"{h3_}")
    else:
        to_return += f"{p}{bold}{h3}Fixed Star Aspects ({orb}° orb){nobold}"
        if minor_aspects:
            to_return += f"{bold} including minor aspects{nobold}"
        if notime:
            to_return += f"{bold} with Imprecise Aspects set to {imprecise_aspects}{nobold}{br}{br}"
        to_return += f"{h3_}{nobold}"
    star_aspects_table_data = []

    aspect_type_counts = {}
    hard_count = 0
    soft_count = 0
    hard_count_score = 0
    soft_count_score = 0
    all_aspects = {**SOFT_ASPECTS, **HARD_ASPECTS}
    house_counts = {house: 0 for house in range(1, 13)}

    for aspect in aspects:
        planet, star_name, aspect_name, angle, house, aspect_score, aspect_comment = (
            aspect
        )
        if planet in ALWAYS_EXCLUDE_IF_NO_TIME:
            continue
        if (
            imprecise_aspects == "off"
            and planet in OFF_BY.keys()
            and OFF_BY[planet] > orb
        ):
            continue
        if degree_in_minutes:
            angle = coord_in_minutes(angle, output)
        else:
            angle = f"{angle:.2f}{degree_symbol}".strip("-")
        row = [planet, aspect_name, star_name, angle]
        if house_positions and not notime and center in ("geocentric", "topocentric"):
            row.insert(
                1, house_positions[planet].get("house", "Unknown")
            )  # Planet house
            row.insert(4, house)  # Star house
            house_counts[house] += 1
            house_counts[house_positions[planet].get("house", "Unknown")] += 1
        if notime and planet in OFF_BY.keys() and OFF_BY[planet] > orb:
            row.append(f" ±{OFF_BY[planet]}{degree_symbol}")

        if show_aspect_score:
            row.append(calculate_aspect_score(aspect_name, aspect[3], stars[star_name]))
        star_aspects_table_data.append(row)

        if aspect_name in aspect_type_counts:
            aspect_type_counts[aspect_name] += 1
        else:
            aspect_type_counts[aspect_name] = 1
        if aspect_name in HARD_ASPECTS:
            hard_count += 1
            hard_count_score += calculate_aspect_score(
                aspect_name, aspect[3], stars[star_name]
            )
        elif aspect_name in SOFT_ASPECTS:
            soft_count += 1
            # soft_count_score += aspect_score # it was like this before magnitude was taken into account (keeping if adding switch)
            soft_count_score += calculate_aspect_score(
                aspect_name, aspect[3], stars[star_name]
            )

    headers = ["Planet", "Aspect", "Star", "Margin"]

    if house_positions and (not notime) and (center in ("geocentric", "topocentric")):
        if output in ("html", "return_html"):
            headers.insert(1, "House")
            headers.insert(4, "House")
        else:
            headers.insert(1, "H")
            headers.insert(4, "H")

    if planet in OFF_BY.keys() and OFF_BY[planet] > orb and notime:
        headers.append("Off by")
    if show_aspect_score:
        headers.append("Score")

    if notime or center not in ("geocentric", "topocentric"):
        star_aspects_table_data.sort(key=lambda x: x[3])  # Sort by degree of aspect
    else:
        star_aspects_table_data.sort(key=lambda x: x[5])  # Sort by degree of aspect

    table = tabulate(
        star_aspects_table_data, headers=headers, tablefmt=table_format, floatfmt=".2f"
    )
    if output in ("text", "html"):
        if output == "html":
            print('<div class="table-container">')
        print(table + f"{br}", end="")
    if output in ("return_html"):
        if all_stars:
            to_return += '<div id="allfixedstarsection">'
        to_return += '<div class="table-container">'
    to_return += f"{br}{br}" + table

    aspect_data = list(aspect_type_counts.items())
    aspect_data.sort(key=lambda x: x[1], reverse=True)
    aspect_data = [
        [aspect_data[i][0], aspect_data[i][1], list(all_aspects[aspect[0]].values())[2]]
        for i, aspect in enumerate(aspect_data)
    ]
    headers = ["Aspect Type", "Count", "Meaning"]
    table = tabulate(aspect_data, headers=headers, tablefmt=table_format)

    if output in ("html", "return_html"):
        div_string = '</div><div style="text-align: left";>'
    else:
        div_string = ""

    if hard_count + soft_count > 0:
        if output in ("html, return_html"):
            row = [
                f"{bold}Hard Aspects:{nobold}",
                hard_count,
                f"{bold}Soft Aspects:{nobold}",
                soft_count,
                f"{bold}Score:{nobold}",
                f"{(hard_count_score + soft_count_score)/(hard_count+soft_count):.1f}".rstrip(
                    "0"
                ).rstrip(
                    "."
                ),
            ]
            score_table = tabulate([row], tablefmt="unsafehtml")
            aspect_count_text = f"{div_string}{p}{score_table}"
        else:
            aspect_count_text = f"{div_string}{p}{bold}Hard Aspects:{nobold} {hard_count}, {bold}Soft Aspects:{nobold} {soft_count}, {bold}Score:{nobold} {(hard_count_score + soft_count_score)/(hard_count+soft_count):.1f}".rstrip(
                "0"
            ).rstrip(
                "."
            )
    else:
        aspect_count_text = f"{div_string}{p}No aspects found."

    # Print counts of each aspect type
    if output in ("text", "html"):
        print(f"{p}{table}{br}{aspect_count_text}")
    if output in ("return_text", "return_html"):
        to_return += f"{br}" + table + aspect_count_text

    # House counts
    if not notime:
        if output in ("return_text", "return_html"):
            if output == "return_html":
                to_return += f"{p}"
            to_return += house_count(house_counts, output, bold, nobold, br)
            if output == "return_html":
                to_return += "</div>"
        else:
            if output == "html":
                print(p)
            print(house_count(house_counts, output, bold, nobold, br))
            if output == "html":
                print("</div>")

    if output == "return_html":
        if all_stars:
            to_return += "</div>"
        to_return += "</div>"
    if output == "html":
        if all_stars:
            print("</div>")
        print("</div>")

    return to_return


# Function to check if there is an entry for a specified name in the JSON file
# def load_event(filename, name):
def load_event(name, guid=None):
    """
    Load event details from a SQL database file based on the given event name.

    Attempts to read from a specified file and retrieve event information for a named event.
    If successful, returns the event details; otherwise, provides an appropriate message.

    Parameters:
    - name (str): The name of the event to retrieve information for.

    Returns:
    - dict or bool: Event details as a dictionary if found, False otherwise.

    Raises:
    - FileNotFoundError: If the specified file does not exist.
    """

    event = db_manager.get_event(name, guid=guid)
    if event:
        return {
            "name": name,
            "location": event["location"],
            "datetime": event["datetime"],
            "timezone": event["timezone"],
            "latitude": event["latitude"],
            "longitude": event["longitude"],
            "altitude": event["altitude"],
            "notime": event["notime"],
        }
    else:
        print(f"No entry found for {name}.")
        return False


def parse_date(date_str):
    # Split the date string to separate the year from the rest of the date
    parts = date_str.split(" ")
    date_part = parts[0]
    time_part = parts[1] if len(parts) > 1 else "00:00"

    # Split the date part further to get the year, month, and day
    date_components = date_part.split("-")

    # Normalize the year to four digits
    year = date_components[0]
    if len(year) == 1:
        year = "000" + year
    elif len(year) == 2:
        year = "00" + year
    elif len(year) == 3:
        year = "0" + year

    try:
        normalized_date_str = (
            f"{year}-{date_components[1]}-{date_components[2]} {time_part}"
        )
        local_datetime = datetime.strptime(normalized_date_str, "%Y-%m-%d %H:%M")
    except ValueError:
        raise ValueError(f"Invalid date format: {date_str}")
    except IndexError:
        raise ValueError(f"Invalid date format: {date_str}")

    return local_datetime


def calculate_lmt_offset(longitude):
    # 4 minutes of time per degree of longitude
    delta = timedelta(minutes=(longitude * 4))
    return timedelta(seconds=int(delta.total_seconds()))


def convert_localtime_in_lmt_to_utc(local_dt, longitude):
    """
    Supposed to convert a local time in LMT to UTC.
    """
    # the logic is flaud behind this idea, as UT is all that's needed.
    lmt_offset = calculate_lmt_offset(longitude)
    if longitude < 0:
        lmt_offset = -lmt_offset

    if longitude < 0:
        utc_dt = local_dt + lmt_offset
    else:
        utc_dt = local_dt - lmt_offset
    return utc_dt


def set_orbs(args, def_orbs):
    # Set orbs to default if not specified
    orbs = {}

    # Blanket orb setting if "orb" is specified
    if args["Orb"]:
        orbs.update(
            {
                "Orb": args["Orb"],
                "Major": args["Orb"],
                "Minor": args["Orb"],
                "Fixed Star": args["Orb"],
                "Asteroid": args["Orb"],
                "Transit Fast": args["Orb"],
                "Transit Slow": args["Orb"],
                "Synastry Fast": args["Orb"],
                "Synastry Slow": args["Orb"],
            }
        )
        return orbs
    else:
        orbs.update(
            {
                "Major": (
                    args["Orb Major"] if args["Orb Major"] else def_orbs["Orb Major"]
                ),
                "Minor": (
                    args["Orb Minor"] if args["Orb Minor"] else def_orbs["Orb Minor"]
                ),
                "Fixed Star": (
                    args["Orb Fixed Star"]
                    if args["Orb Fixed Star"]
                    else def_orbs["Orb Fixed Star"]
                ),
                "Asteroid": (
                    args["Orb Asteroid"]
                    if args["Orb Asteroid"]
                    else def_orbs["Orb Asteroid"]
                ),
                "Transit Fast": (
                    args["Orb Transit Fast"]
                    if args["Orb Transit Fast"]
                    else def_orbs["Orb Transit Fast"]
                ),
                "Transit Slow": (
                    args["Orb Transit Slow"]
                    if args["Orb Transit Slow"]
                    else def_orbs["Orb Transit Slow"]
                ),
                "Synastry Fast": (
                    args["Orb Synastry Fast"]
                    if args["Orb Synastry Fast"]
                    else def_orbs["Orb Synastry Fast"]
                ),
                "Synastry Slow": (
                    args["Orb Synastry Slow"]
                    if args["Orb Synastry Slow"]
                    else def_orbs["Orb Synastry Slow"]
                ),
            }
        )

        return orbs


def called_by_gui(
    name,
    date,
    location,
    latitude,
    longitude,
    timezone,
    time_unknown,
    lmt,
    list_timezones,
    returns,
    save_as,
    davison,
    place,
    imprecise_aspects,
    minor_aspects,
    show_brief_aspects,
    show_score,
    show_arabic_parts,
    aspects_to_arabic_parts,
    classical,
    orb,
    orb_major,
    orb_minor,
    orb_fixed_star,
    orb_asteroid,
    orb_transit_fast,
    orb_transit_slow,
    orb_synastry_fast,
    orb_synastry_slow,
    degree_in_minutes,
    node,
    center,
    all_stars,
    house_system,
    house_cusps,
    hide_planetary_positions,
    hide_planetary_aspects,
    hide_fixed_star_aspects,
    hide_asteroid_aspects,
    hide_decans,
    transits,
    transits_timezone,
    transits_location,
    synastry,
    progressed,
    remove_saved_names,
    store_defaults,
    use_saved_settings,
    output_type,
    guid,
):

    if isinstance(date, datetime):
        date = date.strftime("%Y-%m-%d %H:%M")

    arguments = {
        "Name": name,
        "Date": date,
        "Location": location,
        "Latitude": latitude,
        "Longitude": longitude,
        "Timezone": timezone,
        "Time Unknown": time_unknown,
        "LMT": lmt,
        "List Timezones": list_timezones,
        "Return": returns,
        "Save As": save_as,
        "Davison": davison,
        "Place": place,
        "Imprecise Aspects": imprecise_aspects,
        "Minor Aspects": minor_aspects,
        "Show Brief Aspects": show_brief_aspects,
        "Show Score": show_score,
        "Arabic Parts": show_arabic_parts,
        "Aspects To Arabic Parts": aspects_to_arabic_parts,
        "Classical Rulership": classical,
        "Orb": orb,
        "Orb Major": orb_major,
        "Orb Minor": orb_minor,
        "Orb Fixed Star": orb_fixed_star,
        "Orb Asteroid": orb_asteroid,
        "Orb Transit Fast": orb_transit_fast,
        "Orb Transit Slow": orb_transit_slow,
        "Orb Synastry Fast": orb_synastry_fast,
        "Orb Synastry Slow": orb_synastry_slow,
        "Degree in Minutes": degree_in_minutes,
        "Node": node,
        "Center": center,
        "All Stars": all_stars,
        "House System": house_system,
        "House Cusps": house_cusps,
        "Hide Planetary Positions": hide_planetary_positions,
        "Hide Planetary Aspects": hide_planetary_aspects,
        "Hide Fixed Star Aspects": hide_fixed_star_aspects,
        "Hide Asteroid Aspects": hide_asteroid_aspects,
        "Hide Decans": hide_decans,
        "Transits": transits,
        "Transits Timezone": transits_timezone,
        "Transits Location": transits_location,
        "Synastry": synastry,
        "Progressed": progressed,
        "Saved Names": None,
        "Save Settings": store_defaults,
        "Use Saved Settings": use_saved_settings,
        "Output": output_type,
        "Remove Saved Names": remove_saved_names,
        "Guid": guid if guid else None,
    }

    print(arguments)
    text = main(arguments)
    return text


class ReturnAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        if (
            len(values) != 2
            or values[0] not in ["prev", "next"]
            or values[1]
            not in [
                "Sun",
                "Moon",
                "Mercury",
                "Venus",
                "Earth",
                "Mars",
                "Jupiter",
                "Saturn",
                "Uranus",
                "Neptune",
                "Pluto",
            ]
        ):
            parser.error(
                f"The {self.dest} argument must be followed by 'prev' or 'next' and then a valid planet name."
            )
        setattr(namespace, self.dest, values)


class ProgressedAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        if values == "now":
            setattr(namespace, self.dest, values)
        else:
            try:
                int_value = int(values)
                if int_value <= 1 or int_value >= 361:
                    raise ValueError
            except ValueError:
                parser.error(
                    f"The {self.dest} argument must be 'now' or an integer between 1 and 360."
                )

            setattr(namespace, self.dest, int_value)


def argparser():
    parser = argparse.ArgumentParser(
        description="""If no arguments are passed, values entered in the script will be used.
If a name is passed, the script will look up the record for that name in the JSON file and overwrite other passed values,
provided there are such values stored in the file (only the first 6 types are stored). 
If no record is found, default values will be used.""",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    parser.add_argument(
        "--name",
        help="Name to look up the record for. Will auto save event using this name, if not already saved.",
        required=False,
    )
    parser.add_argument(
        "--date",
        help="Date of the event (YYYY-MM-DD HH:MM local time). (Default: None)",
        required=False,
    )
    parser.add_argument(
        "--location",
        type=str,
        help='Name of location for lookup of coordinates, e.g. "Sahlgrenska, Göteborg, Sweden". (Default: "Sahlgrenska")',
        required=False,
    )
    parser.add_argument(
        "--latitude",
        type=float,
        help="Latitude of the location in degrees, e.g. 57.6828. (Default: 57.6828)",
        required=False,
    )
    parser.add_argument(
        "--longitude",
        type=float,
        help="Longitude of the location in degrees, e.g. 11.96. (Default: 11.9624)",
        required=False,
    )
    parser.add_argument(
        "--timezone",
        help='Timezone of the location (e.g. "Europe/Stockholm"). See README.md for all available tz. (Default: "Europe/Stockholm")',
        required=False,
    )
    parser.add_argument(
        "--time_unknown",
        action="store_true",
        help="Whether the exact time is unknown (affects e.g. house calculations).",
    )
    parser.add_argument(
        "--LMT",
        action="store_true",
        help="Indicates that the specified time is in Local Mean Time (pre standardized timezones). Still requires a timezone for the location, unless TimezoneFinder is installed.",
    )
    parser.add_argument(
        "--list_timezones",
        action="store_true",
        help="Prints all available timezones. Overrides all other arguments if specified.",
    )
    parser.add_argument(
        "--returns",
        nargs=2,
        action=ReturnAction,
        metavar=("DIRECTION", "PLANET"),
        help="Calculate the next or previous return of the named planet to a given datetime or saved named event. Format: prev/next PLANET",
    )
    parser.add_argument(
        "--save_as",
        help="Store event using the name specified here. Useful for returns, and e.g. being able to check for synastry with the natal chart.",
        required=False,
    )
    parser.add_argument(
        "--davison",
        type=str,
        nargs="+",
        metavar="EVENT",
        help="A Davison relationship chart requires at least two saved events (e.g. \"John, 'Jane Smith'\").",
        required=False,
    )
    parser.add_argument(
        "--place",
        help="Name of location without lookup of coordinates. (Default: None)",
        required=False,
    )
    parser.add_argument(
        "--imprecise_aspects",
        choices=["off", "warn"],
        help='Whether to not show imprecise aspects or just warn. (Default: "warn")',
        required=False,
    )
    parser.add_argument(
        "--minor_aspects", action="store_true", help="Show minor aspects."
    )
    parser.add_argument(
        "--brief_aspects",
        action="store_true",
        help="Show brief aspects for transits, i.e. Asc, MC, DC, Desc.",
    )
    parser.add_argument(
        "--score",
        action="store_true",
        help="Show ease of individual aspects (0 not easy, 50 neutral, 100 easy).",
    )
    parser.add_argument(
        "--arabic_parts", action="store_true", help="Show Arabic parts."
    )
    parser.add_argument(
        "--aspects_to_arabic_parts",
        action="store_true",
        help="Include aspects to Arabic parts. Requires --arabic_parts.",
    )
    parser.add_argument(
        "--classical",
        action="store_true",
        help="Use classical sign rulership, as before discovery of modern planets.",
    )
    parser.add_argument(
        "--orb",
        type=float,
        help="Orb size in degrees. Overrides all orb settings if specified. Use for blanket orb setting.",
        required=False,
    )
    parser.add_argument(
        "--orb_major",
        type=float,
        help="Orb size in degrees for major aspects. (Default: 6.0)",
        required=False,
    )
    parser.add_argument(
        "--orb_minor",
        type=float,
        help="Orb size in degrees for minor aspects. (Default: 3.0)",
        required=False,
    )
    parser.add_argument(
        "--orb_fixed_star",
        type=float,
        help="Orb size in degrees for fixed star aspects. (Default: 1.0)",
        required=False,
    )
    parser.add_argument(
        "--orb_asteroid",
        type=float,
        help="Orb size in degrees for asteroid aspects. (Default: 1.5)",
        required=False,
    )
    parser.add_argument(
        "--orb_transit_fast",
        type=float,
        help="Orb size in degrees for fast-moving planet transits. (Default: 1.5)",
        required=False,
    )
    parser.add_argument(
        "--orb_transit_slow",
        type=float,
        help="Orb size in degrees for slow-moving planet transits. (Default: 1.0)",
        required=False,
    )
    parser.add_argument(
        "--orb_synastry_fast",
        type=float,
        help="Orb size in degrees for fast-moving planet synastry. (Default: 1.5)",
        required=False,
    )
    parser.add_argument(
        "--orb_synastry_slow",
        type=float,
        help="Orb size in degrees for slow-moving planet synastry. (Default: 1.0)",
        required=False,
    )
    parser.add_argument(
        "--degree_in_minutes",
        action="store_true",
        help="Show degrees in arch minutes and seconds. (Default: false)",
    )
    parser.add_argument(
        "--node",
        choices=["mean", "true"],
        help='Whether to use the moon mean node or true node. (Default: "true")',
        required=False,
    )
    parser.add_argument(
        "--center",
        choices=["heliocentric", "geocentric", "topocentric"],
        help="Choose center of calculations (default: topocentric).",
    )
    parser.add_argument(
        "--all_stars",
        action="store_true",
        help="Show aspects for all fixed stars. (Default: false)",
    )
    parser.add_argument(
        "--house_system",
        choices=list(HOUSE_SYSTEMS.keys()),
        help='House system to use (Placidus, Koch etc). (Default: "Placidus")',
        required=False,
    )
    parser.add_argument(
        "--house_cusps",
        action="store_true",
        help="Whether to show house cusps or not. (Default: false)",
    )
    parser.add_argument(
        "--hide_planetary_positions",
        action="store_true",
        help="Output: hide what signs and houses (if time specified) planets are in. (Default: false)",
    )
    parser.add_argument(
        "--hide_planetary_aspects",
        action="store_true",
        help="Output: hide aspects planets are in. (Default: false)",
    )
    parser.add_argument(
        "--hide_fixed_star_aspects",
        action="store_true",
        help="Output: hide aspects planets are in to fixed stars. (Default: false)",
    )
    parser.add_argument(
        "--hide_asteroid_aspects",
        action="store_true",
        help="Output: hide aspects planets are in to asteroids. (Default: false)",
    )
    parser.add_argument(
        "--hide_decans",
        action="store_true",
        help="Hide the planet ruling the decan of the planet positions. (Default: false)",
    )
    parser.add_argument(
        "--transits",
        help="Date of the transit event ('YYYY-MM-DD HH:MM' local time, 'now' for current time). (Default: None)",
        required=False,
    )
    parser.add_argument(
        "--transits_timezone",
        help='Timezone of the transit location (e.g. "Europe/Stockholm"). See README.md for all available tz. (Default: "Europe/Stockholm")',
        required=False,
    )
    parser.add_argument(
        "--transits_location",
        type=str,
        help='Name of location for lookup of transit coordinates, e.g. "Göteborg, Sweden". (Default: "Göteborg")',
        required=False,
    )
    parser.add_argument(
        "--synastry",
        help="Name of the stored event (or person) with which to calculate synastry for the person specified under --name. (Default: None)",
        required=False,
    )
    parser.add_argument(
        "--progressed",
        help='Days to progress the natal chart, or "now" for the current year',
        action=ProgressedAction,
        required=False,
    )
    parser.add_argument(
        "--saved_names",
        action="store_true",
        help="List names previously saved using --name. If set, all other arguments are ignored. (Default: false)",
    )
    parser.add_argument(
        "--remove_saved_names",
        type=str,
        nargs="+",
        metavar="EVENT",
        help="Remove saved events (e.g. \"John, 'Jane Smith'\"). If set, all other arguments are ignored. (except --saved_names)",
        required=False,
    )
    parser.add_argument(
        "--save_settings",
        type=str,
        nargs="?",
        const="default",
        help='Store settings as defaults <name>. If no name passed will be stored as "default"',
        required=False,
    )
    parser.add_argument(
        "--use_saved_settings",
        nargs="?",
        const="default",
        type=str,
        help='Use settings specified by name <name>. If no name passed will use "default"',
        required=False,
    )
    parser.add_argument(
        "--output_type",
        choices=["text", "return_text", "html", "return_html"],
        help='Output: Print text or html to stdout, or return text or html. (Default: "text")',
        required=False,
    )

    args = parser.parse_args()

    if args.davison and len(args.davison) < 2:
        parser.error("--davison requires at least two named events.")

    arguments = {
        "Name": args.name,
        "Date": args.date,
        "Location": args.location,
        "Latitude": args.latitude,
        "Longitude": args.longitude,
        "Timezone": args.timezone,
        "Time Unknown": args.time_unknown,
        "LMT": args.LMT,
        "List Timezones": args.list_timezones,
        "Return": args.returns,
        "Save As": args.save_as,
        "Davison": args.davison,
        "Place": args.place,
        "Imprecise Aspects": args.imprecise_aspects,
        "Minor Aspects": args.minor_aspects,
        "Show Brief Aspects": args.brief_aspects,
        "Show Score": args.score,
        "Arabic Parts": args.arabic_parts,
        "Aspects To Arabic Parts": args.aspects_to_arabic_parts,
        "Classical Rulership": args.classical,
        "Orb": args.orb,
        "Orb Major": args.orb_major,
        "Orb Minor": args.orb_minor,
        "Orb Fixed Star": args.orb_fixed_star,
        "Orb Asteroid": args.orb_asteroid,
        "Orb Transit Fast": args.orb_transit_fast,
        "Orb Transit Slow": args.orb_transit_slow,
        "Orb Synastry Fast": args.orb_synastry_fast,
        "Orb Synastry Slow": args.orb_synastry_slow,
        "Degree in Minutes": args.degree_in_minutes,
        "Node": args.node,
        "Center": args.center,
        "All Stars": args.all_stars,
        "House System": args.house_system,
        "House Cusps": args.house_cusps,
        "Hide Planetary Positions": args.hide_planetary_positions,
        "Hide Planetary Aspects": args.hide_planetary_aspects,
        "Hide Fixed Star Aspects": args.hide_fixed_star_aspects,
        "Hide Asteroid Aspects": args.hide_asteroid_aspects,
        "Hide Decans": args.hide_decans,
        "Transits": args.transits,
        "Transits Timezone": args.transits_timezone,
        "Transits Location": args.transits_location,
        "Synastry": args.synastry,
        "Progressed": args.progressed,
        "Saved Names": args.saved_names,
        "Remove Saved Names": args.remove_saved_names,
        "Save Settings": args.save_settings,
        "Use Saved Settings": args.use_saved_settings,
        "Output": args.output_type,
        "Guid": None,
    }

    return arguments


def main(gui_arguments=None):
    if gui_arguments:
        args = gui_arguments
    else:
        args = argparser()

    local_datetime = datetime.now()  # Default date now

    # Check if name was provided as argument
    name = args["Name"] if args["Name"] else ""
    to_return = ""

    #################### Load event ####################
    if args["Guid"]:
        exists = load_event(name, args["Guid"]) if name else False
    else:
        exists = load_event(name) if name else False
    if exists:
        local_datetime = datetime.fromisoformat(exists["datetime"])
        latitude = exists["latitude"]
        longitude = exists["longitude"]
        altitude = exists["altitude"]
        local_timezone = pytz.timezone(exists["timezone"])
        notime = True if exists["notime"] in ("1", 1, "true") else False
        place = exists["location"]
    else:
        if args["Return"]:
            print("No valid event specified for return.")
            return "No valid event specified for return."
        notime = args["Time Unknown"]

    try:
        if args["Date"]:
            if args["Date"] == "now":
                if EPHE:
                    local_datetime = datetime.now()
                    local_timezone = pytz.timezone("UTC")
                else:
                    local_datetime = datetime.now()
            else:
                local_datetime = parse_date(args["Date"])
    except ValueError:
        print("Invalid date format. Please use YYYY-MM-DD HH:MM.")
        local_datetime = None
        return "Invalid date format. Please use YYYY-MM-DD HH:MM."

    try:
        if args["Progressed"]:
            local_datetime = get_progressed_datetime(local_datetime, args["Progressed"])
    except ValueError:
        pass

    if args["Center"]:
        center_of_calculations = args["Center"]
    else:
        center_of_calculations = "topocentric"

    if center_of_calculations == "heliocentric":
        PLANETS.pop("North Node", None)
        PLANETS.pop("South Node", None)
        PLANETS.pop("Lilith", None)
        PLANETS.pop("Sun", None)
        PLANETS.pop("Moon", None)
        PLANETS.update({"Earth": swe.EARTH})
        hide_fixed_star_aspects = True

    try:
        if args["Return"]:
            if not args["Name"]:
                print("No named event specified for return.")
                return "No named event specified for return."
            # convert to utc
            utc_datetime = convert_localtime_in_lmt_to_utc(local_datetime, longitude)
            nextprev = args["Return"][0]
            returning_planet = args["Return"][1]
            return_utc_datetime = find_next_same_degree(
                utc_datetime,
                returning_planet,
                longitude,
                latitude,
                altitude,
                nextprev,
                center_of_calculations,
            )
            if not return_utc_datetime:
                return "No return found for specified planet."
    except ValueError:
        print("Planet not found.")
        return "Planet not found."

    ######### Default settings if no arguments are passed #########
    def_tz = pytz.timezone("Europe/Stockholm")  # Default timezone
    def_transits_tz = pytz.timezone("Europe/Stockholm")  # Default timezone
    def_place_name = "Sahlgrenska"  # Default place
    def_transits_location = "Göteborg"  # Default transit location
    def_lat = 57.6828  # Default latitude
    def_long = 11.9624  # Default longitude
    def_alt = 0  # Default altitude
    def_imprecise_aspects = "warn"  # Default imprecise aspects ["off", "warn"]
    def_minor_aspects = False  # Default minor aspects
    def_show_brief_aspects = False  # Default brief aspects
    def_show_score = False  # Default minor aspects

    def_orbs = {
        "Orb": 1,  # General default orb size
        "Orb Major": 6.0,  # Default orb size for major aspects
        "Orb Minor": 1.5,  # Default orb size for minor aspects
        "Orb Fixed Star": 1.0,  # Default orb size for fixed star aspects
        "Orb Asteroid": 1.5,  # Default orb size for fixed star aspects
        "Orb Transit Fast": 1.5,  # Default orb size for fast-moving planet transits
        "Orb Transit Slow": 1.0,  # Default orb size for slow-moving planet transits
        "Orb Synastry Fast": 3.0,  # Default orb size for fast-moving planet synastry
        "Orb Synastry Slow": 2.0,  # Default orb size for slow-moving planet synastry
    }

    def_degree_in_minutes = False  # Default degree in minutes
    def_node = "true"  # Default node (true node is more accurate than mean node)
    def_all_stars = False  # Default only astrologically known stars
    def_house_cusps = False  # Default do not show house cusps
    def_output_type = "text"  # Default output type

    # Default Output settings
    hide_planetary_positions = False
    hide_planetary_aspects = False
    hide_fixed_star_aspects = False
    hide_asteroid_aspects = False
    show_transits = False
    show_synastry = False

    # Store defaults if requested
    if args["Save Settings"]:
        defaults_to_store = {
            "Name": args["Save Settings"],
            "GUID": args["Guid"] if args["Guid"] else None,
            "Location": args["Location"] if args["Location"] else None,
            "Timezone": args["Timezone"] if args["Timezone"] else None,
            "LMT": args["LMT"] if args["LMT"] else None,
            "Imprecise Aspects": (
                args["Imprecise Aspects"] if args["Imprecise Aspects"] else None
            ),
            "Minor Aspects": args["Minor Aspects"] if args["Minor Aspects"] else None,
            "Show Brief Aspects": (
                args["Show Brief Aspects"] if args["Show Brief Aspects"] else None
            ),
            "Show Score": args["Show Score"] if args["Show Score"] else None,
            "Orb": args["Orb"] if args["Orb"] else None,
            "Orb Major": args["Orb Major"] if args["Orb Major"] else None,
            "Orb Minor": args["Orb Minor"] if args["Orb Minor"] else None,
            "Orb Fixed Star": (
                args["Orb Fixed Star"] if args["Orb Fixed Star"] else None
            ),
            "Orb Asteroid": args["Orb Asteroid"] if args["Orb Asteroid"] else None,
            "Orb Transit Fast": (
                args["Orb Transit Fast"] if args["Orb Transit Fast"] else None
            ),
            "Orb Transit Slow": (
                args["Orb Transit Slow"] if args["Orb Transit Slow"] else None
            ),
            "Orb Synastry Fast": (
                args["Orb Synastry Fast"] if args["Orb Synastry Fast"] else None
            ),
            "Orb Synastry Slow": (
                args["Orb Synastry Slow"] if args["Orb Synastry Slow"] else None
            ),
            "Degree in Minutes": (
                args["Degree in Minutes"] if args["Degree in Minutes"] else None
            ),
            "Node": args["Node"] if args["Node"] else None,
            "Arabic Parts": args["Arabic Parts"] if args["Arabic Parts"] else None,
            "All Stars": args["All Stars"] if args["All Stars"] else None,
            "House System": args["House System"] if args["House System"] else None,
            "House Cusps": args["House Cusps"] if args["House Cusps"] else None,
            "Hide Planetary Positions": (
                args["Hide Planetary Positions"]
                if args["Hide Planetary Positions"]
                else None
            ),
            "Hide Planetary Aspects": (
                args["Hide Planetary Aspects"]
                if args["Hide Planetary Aspects"]
                else None
            ),
            "Hide Fixed Star Aspects": (
                args["Hide Fixed Star Aspects"]
                if args["Hide Fixed Star Aspects"]
                else None
            ),
            "Hide Asteroid Aspects": (
                args["Hide Asteroid Aspects"] if args["Hide Asteroid Aspects"] else None
            ),
            "Hide Decans": args["Hide Decans"] if args["Hide Decans"] else None,
            "Transits Timezone": (
                args["Transits Timezone"] if args["Transits Timezone"] else None
            ),
            "Transits Location": (
                args["Transits Location"] if args["Transits Location"] else None
            ),
            "Output": args["Output"] if args["Output"] else None,
        }

        db_manager.store_defaults(defaults_to_store)
        print(f"Settings stored with the name '{args['Save Settings']}'.")

        if EPHE:
            return f"Defaults saved."
        else:
            return f"Settings stored with the name '{args['Save Settings']}'."

    # Override using stored settings (default or specified name)
    stored_defaults = db_manager.read_defaults(
        args["Use Saved Settings"] if args["Use Saved Settings"] else "default",
        args["Guid"] if args["Guid"] else "",
    )

    if stored_defaults:
        keys = [
            "Location",
            "Timezone",
            "LMT",
            "Imprecise Aspects",
            "Minor Aspects",
            "Show Brief Aspects",
            "Show Score",
            "Orb",
            "Orb Major",
            "Orb Minor",
            "Orb Fixed Star",
            "Orb Asteroid",
            "Orb Transit Fast",
            "Orb Transit Slow",
            "Orb Synastry Fast",
            "Orb Synastry Slow",
            "Degree in Minutes",
            "Arabic Parts",
            "Node",
            "All Stars",
            "House System",
            "House Cusps",
            "Hide Planetary Positions",
            "Hide Planetary Aspects",
            "Hide Fixed Star Aspects",
            "Hide Asteroid Aspects",
            "Transits Timezone",
            "Transits Location",
            "Output",
        ]

        for key in keys:
            if stored_defaults.get(key):
                args[key] = stored_defaults.get(key)

    if args["Location"]:
        place = args["Location"]
        latitude, longitude, altitude = get_coordinates(args["Location"])
        if latitude is None or longitude is None:
            location_error_string = (
                f"Location not found, please check the spelling"
                + " and internet connection."
                if not EPHE
                else ""
            )
            les_html = f""" <!DOCTYPE html> <html> <head> <meta 
	charset="UTF-8"> <meta name="viewport" 
	content="width=device-width, initial-scale=1.0"> 
	</head> <body> 
	<div><p>{location_error_string}</p></div> </body> 
	</html>"""
            if args["Output"] == "html":
                print(les_html)
            elif args["Output"] == "return_html":
                return les_html
            elif args["Output"] == "return_text":
                return location_error_string
            else:
                print(location_error_string)
            return
        if args["Center"] == "heliocentric":
            altitude = None
        else:
            altitude = get_altitude(latitude, longitude, place)
    elif args["Place"]:
        place = args["Place"]
    elif not exists:
        place = def_place_name

    if not args["Location"] and not exists:
        latitude = args["Latitude"] if args["Latitude"] is not None else def_lat
        longitude = args["Longitude"] if args["Longitude"] is not None else def_long
        # longitude = args["Altitude"] if args["Altitude"] is not None else def_alt
        altitude = get_altitude(def_lat, def_long, def_place_name)

    if not exists:
        if args["Timezone"]:
            try:
                local_timezone = pytz.timezone(args["Timezone"])
            except:
                print("Invalid timezone")
                return "Invalid timezone"
        elif tz_finder_installed:

            tf = TimezoneFinder()
            timezone_name = tf.timezone_at(lng=longitude, lat=latitude)

            if timezone_name:
                local_timezone = pytz.timezone(timezone_name)
            else:
                print(
                    "Could not determine the timezone automatically. Please specify the timezone using --timezone."
                )
                local_timezone = def_tz
        else:
            local_timezone = def_tz

    def_house_system = (
        HOUSE_SYSTEMS["Placidus"]
        if abs(latitude) < 66
        else HOUSE_SYSTEMS["Equal (Ascendant cusp 1)"]
    )  # Default house system

    ephemeris_restriction_date = datetime(
        675, 1, 4, 12, 0
    )  # Ephemeris data for Chiron is available from 675 AD
    if local_datetime < ephemeris_restriction_date:
        PLANETS.pop("Chiron")

    # If "off", the script will not show such aspects, if "warn" print a warning for uncertain aspects
    imprecise_aspects = (
        args["Imprecise Aspects"]
        if args["Imprecise Aspects"]
        else def_imprecise_aspects
    )
    # If True, the script will include minor aspects
    minor_aspects = True if args["Minor Aspects"] else def_minor_aspects
    orbs = set_orbs(args, def_orbs)
    orb = float(args["Orb"]) if args["Orb"] else def_orbs["Orb"]
    # If True, the script will show the positions in degrees and minutes
    degree_in_minutes = True if args["Degree in Minutes"] else def_degree_in_minutes
    node = "mean" if args["Node"] and args["Node"].lower() in ["mean"] else def_node
    if node == "mean":
        PLANETS["North Node"] = swe.MEAN_NODE
    if node == "true":
        PLANETS["North Node"] = swe.TRUE_NODE

    # If True, the script will include all roughly 600 fixed stars
    all_stars = True if args["All Stars"] else def_all_stars
    h_sys = (
        HOUSE_SYSTEMS[args["House System"]]
        if args["House System"]
        else def_house_system
    )
    h_sys_changed = False
    if (
        h_sys not in ("A", "E", "V") and abs(latitude) >= 66
    ):  # The house systems safe for closer to the poles
        h_sys = def_house_system
        h_sys_changed = f"House system {args['House System']} not supported at latitudes above |66°|. Reverting to Equal house system."

    if args["House System"] and args["House System"] not in HOUSE_SYSTEMS:
        print(
            f"Invalid house system. Available house systems are: {', '.join(HOUSE_SYSTEMS.keys())}"
        )
        h_sys = def_house_system  # Reverting to default house system if invalid
    show_house_cusps = True if args["House Cusps"] else def_house_cusps

    show_brief_aspects = def_show_brief_aspects  # code follows
    if args["Show Brief Aspects"]:
        show_brief_aspects = True
    show_score = def_show_score
    if args["Show Score"]:
        show_score = True

    output_type = args["Output"] if args["Output"] else def_output_type

    if args["List Timezones"]:
        to_return = "Available timezones:\n"
        for tz in pytz.all_timezones:
            to_return += f"{tz}\n"
        if output_type in ("text", "html"):
            print(to_return)
            return
        else:
            return to_return

    if args["Remove Saved Names"]:
        to_return = db_manager.remove_saved_names(
            args["Remove Saved Names"],
            output_type,
            guid=args["Guid"] if args["Guid"] else None,
        )
        if output_type in ("text", "html"):
            print(to_return)
        if not args["Saved Names"]:
            return to_return

    if args["Saved Names"]:
        names = db_manager.read_saved_names()
        if output_type in ("text", "html"):
            print("Names stored in db:")
            for name in names:
                print(f"{name}")
        else:
            to_return += "Names stored in db:\n\n"
            for name in names:
                to_return += f"{name}"
        return to_return

    if output_type == "html":
        print(
            """
<!DOCTYPE html>
    <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>AstroScript Chart</title>\n
            <style>
                body {
                    font-family: Arial, sans-serif;
                    color: #333;
                    background-color: #f4f4f4;
                    margin: 0px;
                    padding-left: 8px;
                    padding-right: 8px;
                }

                h1, h2, h3 {
                    color: #35424a;
                    margin-bottom: 1em;
                    line-height: 1.3;
                }

                h1 {
                    font-size: 2.5rem; /* Responsive font size */
                }
                h2 {
                    font-size: 2.0rem;
                }
                h3 {
                    font-size: 1.75rem;
                }
                p {
                    font-size: 1.2rem;
                    line-height: 1.6;
                }

                th, td {
                    padding: 8px 10px;
                    text-align: left;
                    border-bottom: 1px solid #ddd;
                }

                th {
                    background-color: #35424a;
                    color: white;
                }

                img {
                    max-height: 90vh;   /* vh unit represents a percentage of the viewport height */
                    width: auto;        /* Maintains the aspect ratio of the image */
                    display: block;
                }
                .table-container {
                    display: flex;
                    flex-wrap: wrap;
                    justify-content: space-around; /* This will space out the tables evenly */
                    align-items: flex-start; /* Aligns tables to the top */
                }
                .content-block {
                    margin-bottom: 20px; /* Separation between different blocks */
                }
                table {
                    width: auto;
                    margin-top: 20px;
                    border-collapse: collapse;
                    display: block;
                    flex: 1 1 300px; /* Flex-grow, flex-shrink, and base width */
                    margin: 10px; /* Adds some space between tables */
                    max-width: 100%; /* Ensures table does not overflow its container */
                    // overflow-x: auto; /* Allows horizontal scrolling if needed */
                    display: block;
                }
                .stack-vertical {
                    flex: 0 0 100%; /* Forces the table to take up 100% width of the flex container */
                    margin: 10px 0; /* Vertical margin for spacing, no horizontal margins */
                }

                @media (max-width: 768px) {
                    .table-container {
                        flex-direction: column;
                    }
                }
            </style>
        </head>
        <body>"""
        )
    if output_type in ("html", "return_html"):
        bold = "<b>"
        nobold = "</b>"
        br = "\n<br>"
        p = "\n<p>"
        h1 = "<h1>"
        h2 = "<h2>"
        h3 = "<h3>"
        h1_ = "</h1>"
        h2_ = "</h2>"
        h3_ = "</h3>"
    elif output_type == "text":
        bold = "\033[1m"
        nobold = "\033[0m"
        br = "\n"
        p = "\n"
        h1 = ""
        h2 = ""
        h3 = ""
        h1_ = ""
        h2_ = ""
        h3_ = ""
    else:
        bold = ""
        nobold = ""
        br = "\n"
        p = "\n"
        h1 = ""
        h2 = ""
        h3 = ""
        h1_ = ""
        h2_ = ""
        h3_ = ""

    if args["Hide Planetary Positions"]:
        if args["Hide Planetary Positions"]:
            hide_planetary_positions = True
    if args["Hide Planetary Aspects"]:
        if args["Hide Planetary Aspects"]:
            hide_planetary_aspects = True
    if args["Hide Fixed Star Aspects"]:
        if args["Hide Fixed Star Aspects"]:
            hide_fixed_star_aspects = True
    if args["Hide Asteroid Aspects"]:
        if args["Hide Asteroid Aspects"]:
            hide_asteroid_aspects = True

    if args["Arabic Parts"]:
        show_arabic_parts = True
    else:
        show_arabic_parts = False

    if args["Davison"]:
        utc_datetime, longitude, latitude, altitude = get_davison_data(args["Davison"])
        place = "Davison chart"
        local_timezone = pytz.utc
        local_datetime = utc_datetime
    else:
        if place == "Davison chart":
            utc_datetime = local_datetime
        else:
            if args["LMT"]:  # If the time is Local Mean Time already
                utc_datetime = convert_localtime_in_lmt_to_utc(
                    local_datetime, longitude
                )
            elif args["Return"]:
                utc_datetime = return_utc_datetime
            else:
                utc_datetime = convert_to_utc(local_datetime, local_timezone)

    if args["Transits"]:
        if args["Transits Timezone"]:
            local_transits_timezone = pytz.timezone(args["Transits Timezone"])
        else:
            local_transits_timezone = def_transits_tz

        if args["Transits Location"]:
            transits_location = args["Transits Location"]
        else:
            transits_location = def_transits_location
        transits_latitude, transits_longitude, transits_altitude = get_coordinates(
            transits_location
        )

        if transits_latitude is None or transits_longitude is None:
            location_error_string = f"Transit location '{transits_location}' not found, please check the spelling and internet connection."
            print(location_error_string)
            return location_error_string

        transits_altitude = get_altitude(
            transits_latitude, transits_longitude, transits_location
        )

        if args["Transits"] == "now":
            transits_local_datetime = datetime.now()
            transits_utc_datetime = convert_to_utc(
                transits_local_datetime, local_transits_timezone
            )
            show_transits = True
        else:
            try:
                if EPHE:
                    transits_local_datetime = args["Transits"]
                else:
                    transits_local_datetime = datetime.strptime(
                        args["Transits"], "%Y-%m-%d %H:%M"
                    )
            except ValueError:
                print(
                    "Invalid transit date format. Please use YYYY-MM-DD HH:MM (00:00 for time if unknown).\nEnter 'now' for current time (UTC).",
                    file=sys.stderr,
                )
                return "Invalid transit date format. Please use YYYY-MM-DD HH:MM (00:00 for time if unknown).\nEnter 'now' for current time (UTC)."
            transits_utc_datetime = convert_to_utc(
                transits_local_datetime, local_transits_timezone
            )

            show_transits = True
        # only show transits, not the rest
        hide_asteroid_aspects = True
        hide_fixed_star_aspects = True
        hide_planetary_aspects = True
        hide_planetary_positions = True

        if args["Center"]:
            center_of_calculations = args["Center"]
        else:
            center_of_calculations = "geocentric"  # defaulting to geocentric calculations as swisseph does not report speed of planets in other modes

    if args["Synastry"]:
        try:
            exists = load_event(
                args["Synastry"], args["Guid"] if args["Guid"] else None
            )
            if exists:
                synastry_local_datetime = datetime.fromisoformat(exists["datetime"])
                synastry_latitude = exists["latitude"]
                synastry_longitude = exists["longitude"]
                synastry_altitude = exists["altitude"]

                if exists["timezone"] == "LMT":
                    synastry_local_timezone == "LMT"
                else:
                    synastry_local_timezone = pytz.timezone(exists["timezone"])
                synastry_place = exists["location"]
                synastry_utc_datetime = convert_to_utc(
                    synastry_local_datetime, synastry_local_timezone
                )
                synastry_notime = True if exists["notime"] else False
                show_synastry = True
                hide_planetary_positions = True
                hide_planetary_aspects = True
                hide_fixed_star_aspects = True
                hide_asteroid_aspects = True
        except:
            print("Invalid second event for synastry", file=sys.stderr)
            return "Invalid second event for synastry."

    # Save event if name given and not already stored
    if name and not exists:
        db_manager.update_event(
            name,
            place,
            local_datetime.isoformat(),
            str(local_timezone),
            latitude,
            longitude,
            altitude,
            notime,
            guid=args["Guid"] if args["Guid"] else None,
        )
    if args["Save As"]:
        db_manager.update_event(
            args["Save As"],
            place,
            (
                utc_datetime + utc_datetime.astimezone(local_timezone).utcoffset()
            ).isoformat(),
            str(local_timezone),
            latitude,
            longitude,
            altitude,
            notime,
            guid=args["Guid"] if args["Guid"] else None,
        )

    #################### Main Script ####################
    # Initialize Colorama, calculations for strings
    init()
    house_system_name = next(
        (name for name, code in HOUSE_SYSTEMS.items() if code == h_sys), None
    )
    planet_positions = calculate_planet_positions(
        utc_datetime,
        latitude,
        longitude,
        altitude,
        output_type,
        h_sys,
        "planets",
        center_of_calculations,
        show_arabic_parts,
        classic_rulers=args["Classical Rulership"],
    )
    house_positions, house_cusps = calculate_house_positions(
        utc_datetime,
        latitude,
        longitude,
        altitude,
        copy.deepcopy(planet_positions),
        notime,
        HOUSE_SYSTEMS[house_system_name],
    )

    complex_aspects = {}
    complex_aspects["T Squares"] = find_t_squares(
        copy.deepcopy(planet_positions), orb_opposition=6, orb_square=5
    )
    complex_aspects["Yods"] = find_yod(
        copy.deepcopy(planet_positions), orb_opposition=6, orb_square=5
    )
    complex_aspects["Grand Crosses"] = find_grand_crosses(
        copy.deepcopy(planet_positions), orb=5
    )
    complex_aspects["Grand Trines"] = find_grand_trines(
        copy.deepcopy(planet_positions), orb=5
    )
    complex_aspects["Kites"] = find_kites(copy.deepcopy(planet_positions), orb=5)

    moon_phase_name1, illumination1 = moon_phase(utc_datetime)
    moon_phase_name2, illumination2 = moon_phase(utc_datetime + timedelta(days=1))
    pluto_ecliptic = get_pluto_ecliptic(utc_datetime)

    if notime:
        illumination = f"{illumination1:.2f}-{illumination2:.2f}%"
    else:
        moon_phase_name, illumination = moon_phase(utc_datetime)
        illumination = f"{illumination:.2f}%"

    weekday, ruling_day, ruling_hour = datetime_ruled_by(local_datetime)
    if show_synastry:
        weekday_synastry, ruling_day_synastry, ruling_hour_synastry = datetime_ruled_by(
            synastry_utc_datetime
        )

    string_heading = (
        f"{p}{h1}{bold}AstroScript v.{version.__version__} Chart{nobold}{h1_}"
    )
    string_planets_heading = f"{p}{h3}{bold}Planetary Positions{nobold}{h3_}"
    string_name = f"{p}{bold}Name:{nobold} {name}".rstrip(", ")
    string_place = f"{br}{bold}Place:{nobold} {place}"
    string_latitude_in_minutes = (
        f"{br}{bold}Latitude:{nobold} {coord_in_minutes(latitude, output_type)}"
    )
    string_longitude_in_minutes = (
        f"{bold}Longitude:{nobold} {coord_in_minutes(longitude, output_type)}"
    )
    string_latitude = f"{br}{bold}Latitude:{nobold} {latitude}"
    string_longitude = f"{bold}Longitude:{nobold} {longitude}"
    string_altitude = f"{br}{bold}Altitude:{nobold} {altitude} m"
    string_davison_noname = "Davison chart"
    string_progressed = (
        f"{br}{bold}Progressed chart:{nobold} {args['Progressed']}"
        if args["Progressed"]
        else ""
    )

    if args["Name"] or exists:
        if len(args["Name"].split(",")) == 1:
            string_not_full_name = " (enter full name for correct destiny number)"
        else:
            string_not_full_name = ""

        string_numerology = (
            f"{br}{bold}Life path:{nobold} {life_path_number(utc_datetime)}, {bold}Destiny number:{nobold} {destiny_number(name)}"
            + string_not_full_name
        )
    else:
        string_numerology = (
            f"{br}{bold}Life path:{nobold} {life_path_number(utc_datetime)}"
        )

    if args["Name"] and args["Davison"]:
        string_davison = f"{br}{bold}Davison chart of:{nobold} {', '.join(args['Davison'])}. Stored as new event: {args['Name']}"
    elif args["Davison"]:
        string_davison = (
            f"{br}{bold}Davison chart of:{nobold} {', '.join(args['Davison'])}"
            + " (not stored, --name lacking)"
            if not EPHE
            else ""
        )
    string_local_time = (
        (f"{br}{bold}Local Time:{nobold} {str(local_datetime).lstrip('0')}" + " LMT")
        if args["LMT"]
        else (
            f"{br}{bold}Local Time:{nobold} {str(local_datetime).strip('0').strip(':')} {local_timezone}"
        )
    )
    string_UTC_Time_imprecise = f"{br}{bold}UTC Time:{nobold} {str(utc_datetime).lstrip('0')} UTC (imprecise due to exact time of day missing)"
    delta_symbol = "Delta" if (os.name == "nt" and output_type == "html") else "Δ"

    string_UTC_Time = f"{br}{bold}UTC Time:{nobold} {str(utc_datetime).lstrip('0')} UTC"  # ({delta_symbol}-T adjusted)"
    if args["Return"]:
        string_return = (
            f"{p}{bold}Return chart for "
            + ("the " if returning_planet in ("Moon", "Sun") else "")
            + returning_planet
            + f", {nextprev}{nobold}"
        )

    if notime:
        string_ruled_by = f"{br}{bold}Weekday:{nobold} {weekday} {bold}Day ruled by:{nobold} {ruling_day}"
    else:
        string_ruled_by = f"{br}{bold}Weekday:{nobold} {weekday} {bold}Day ruled by:{nobold} {ruling_day} {bold}Hour ruled by:{nobold} {ruling_hour}"
    if show_synastry:
        string_synastry_name = f"{p}{bold}Name:{nobold} {args['Synastry']}"
        string_synastry_place = f"{br}{bold}Place:{nobold} {synastry_place}"
        string_synastry_latitude_in_minutes = f"{br}{bold}Latitude:{nobold} {coord_in_minutes(synastry_latitude if show_synastry else 11.12, output_type)}"
        string_synastry_longitude_in_minutes = f"{bold}Longitude:{nobold} {coord_in_minutes(synastry_longitude if show_synastry else 22.33, output_type)}"
        string_synastry_latitude = f"{br}{bold}Latitude:{nobold} {synastry_latitude}"
        string_synastry_longitude = f"{bold}Longitude:{nobold} {synastry_longitude}"
        string_synastry_altitude = f"{br}{bold}Altitude:{nobold} {synastry_altitude} m"
        string_synastry_local_time = f"{br}{bold}Local Time:{nobold} {synastry_local_datetime} {synastry_local_timezone}"
        string_synastry_UTC_Time_imprecise = f"{br}{bold}UTC Time:{nobold} {synastry_utc_datetime} UTC (imprecise due to time of day missing)"
        string_synastry_UTC_Time = (
            f"{br}{bold}UTC Time:{nobold} {synastry_utc_datetime} UTC"
        )
        if notime:
            string_synastry_ruled_by = f"{br}{bold}Weekday:{nobold} {weekday_synastry} {bold}Day ruled by:{nobold} {ruling_day_synastry}"
        else:
            string_synastry_ruled_by = f"{br}{bold}Weekday:{nobold} {weekday_synastry} {bold}Day ruled by:{nobold} {ruling_day_synastry} {bold}Hour ruled by:{nobold} {ruling_hour_synastry}"

    string_house_system_moon_nodes = (
        f"{br}{bold}Center:{nobold} {center_of_calculations.title()}"
    )
    if center_of_calculations in ("geocentric", "topocentric"):
        string_house_system_moon_nodes += (
            f", {bold}House system:{nobold} {house_system_name}, {bold}Moon nodes:{nobold} {node}{br}"
            + (h_sys_changed + f"{br}" if h_sys_changed else "")
        )
    string_house_cusps = f"{p}{bold}House cusps:{nobold} {house_cusps}{br}"
    if output_type in ("return_text"):
        if moon_phase_name1 != moon_phase_name2:
            string_moon_phase_imprecise = f"\n\n{p}{bold}Moon Phase:{nobold} {moon_phase_name1} to {moon_phase_name2}{br}{bold}Moon Illumination:{nobold} {illumination}"
        else:
            string_moon_phase_imprecise = f"\n\n{p}{bold}Moon Phase:{nobold} {moon_phase_name1}{br}{bold}Moon Illumination:{nobold} {illumination}"
    else:
        string_moon_phase_imprecise = f"{p}{bold}Moon Phase:{nobold} {moon_phase_name1} to {moon_phase_name2}{br}{bold}Moon Illumination:{nobold} {illumination}"
    string_moon_phase = (
        f"{p}{bold}Moon Phase:{nobold} {moon_phase_name}{br}{bold}Moon Illumination:{nobold} {illumination}"
        if not notime
        else ""
    )
    string_transits = f"{p}{bold}{h2}Transits for"
    string_synastry = f"{p}{bold}{h2}Synastry chart for"
    string_no_transits_tz = f"{p}No timezone or location specified for transits (--transits_timezone, --transits_location).\nUsing default timezone ({def_transits_tz}) and location ({def_transits_location}) for transits."

    if output_type in ("text", "html"):
        print(f"{string_heading}", end="")
        if args["Return"]:
            print(f"{string_return}", end="")
        if args["Progressed"]:
            print(f"{string_progressed}", end="")
        if exists or name:
            print(f"{string_name}", end="")
        if place:
            print(f"{string_place}", end="")
        if degree_in_minutes:
            print(
                f"{string_latitude_in_minutes}, {string_longitude_in_minutes}", end=""
            )
        else:
            print(f"{string_latitude}, {string_longitude}", end="")
        print(f"{string_altitude}", end="")
        if args["Davison"]:
            print(f"{string_davison}", end="")

        if not args["Davison"] and place != "Davison chart":
            print(f"{string_local_time} ", end="")

        (
            print(f"{string_UTC_Time_imprecise}", end="")
            if notime
            else print(f"{string_UTC_Time}", end="")
        )

        print(f"{string_ruled_by}", end="")

        if not show_synastry and not center_of_calculations == "heliocentric":
            try:
                print(
                    f"{br}{bold}Sabian Symbol:{nobold} {get_sabian_symbol(planet_positions, 'Sun')}",
                    end="",
                )
            except:
                print(
                    f"{br}{bold}Sabian Symbol:{nobold} Cannot access sabian.json file",
                    end="",
                )

        print(f"{string_numerology}", end="")

        if show_synastry:
            print(f"{string_synastry_name}", end="")
            print(f"{string_synastry_place}", end="")
            if degree_in_minutes:
                print(
                    f"{string_synastry_latitude_in_minutes}, {string_synastry_longitude_in_minutes}, {string_synastry_altitude}",
                    end="",
                )
            else:
                print(
                    f"{string_synastry_latitude}, {string_synastry_longitude}, {string_synastry_altitude}",
                    end="",
                )
            print(f"{string_synastry_local_time} ", end="")
            (
                print(f"{string_synastry_UTC_Time_imprecise}", end="")
                if (notime or synastry_notime)
                else print(f"{string_synastry_UTC_Time}", end="")
            )
            print(f"{string_synastry_ruled_by}", end="")

    elif output_type in ("return_text", "return_html"):
        if args["Return"]:
            to_return += f"{string_return}"
        if args["Progressed"]:
            to_return += f"{string_progressed}"
        if exists or name:
            to_return += f"{string_name}"
        if place:
            to_return += f"{string_place}"
        if degree_in_minutes:
            to_return += f"{string_latitude_in_minutes}, {string_longitude_in_minutes}"
        else:
            to_return += f"{string_latitude}, {string_longitude}"
        to_return += f"{string_altitude}"
        if args["Davison"]:
            to_return += f"{string_davison}"

        if not args["Davison"] and place != "Davison chart":
            to_return += f"{string_local_time}"

        to_return += f"{br}{bold}Center:{nobold} {center_of_calculations.title()}"

        if notime:
            to_return += f"{string_UTC_Time_imprecise}"
        else:
            to_return += f"{string_UTC_Time}"

        to_return += f"{string_ruled_by}"

        if not show_synastry and not center_of_calculations == "heliocentric":
            try:
                to_return += f"{br}{bold}Sabian Symbol:{nobold} {get_sabian_symbol(planet_positions, 'Sun')}"
            except:
                to_return += (
                    f"{br}{bold}Sabian Symbol:{nobold} Cannot access sabian.json file"
                )

        to_return += f"{string_numerology}"

        if show_synastry:
            to_return += f"{string_synastry_name}"
            to_return += f"{string_synastry_place}"
            if degree_in_minutes:
                to_return += f"{string_synastry_latitude_in_minutes}, {string_synastry_longitude_in_minutes}, {string_synastry_altitude}"
            else:
                to_return += f"{string_synastry_latitude}, {string_synastry_longitude}, {string_synastry_altitude}"
            to_return += f"{string_synastry_local_time} "
            to_return += (
                f"{string_synastry_UTC_Time_imprecise}"
                if (notime or synastry_notime)
                else f"{string_synastry_UTC_Time}"
            )

    if output_type in ("text", "html"):
        print(f"{string_house_system_moon_nodes}", end="")
    else:
        to_return += f"{string_house_system_moon_nodes}"

    if minor_aspects:
        ASPECT_TYPES.update(MINOR_ASPECT_TYPES)
        MAJOR_ASPECTS.update(MINOR_ASPECTS)

    if show_house_cusps:
        if output_type in ("text", "html"):
            print(f"{string_house_cusps}", end="")
        else:
            to_return += f"{string_house_cusps}"

    if not hide_planetary_positions:
        if output_type in ("text", "html"):
            print(f"{string_planets_heading}{nobold}{h3_}{br}", end="")
        else:
            to_return += f"{string_planets_heading}"
        to_return += print_planet_positions(
            copy.deepcopy(planet_positions),
            degree_in_minutes,
            notime,
            house_positions,
            orb,
            output_type,
            args["Hide Decans"],
            args["Classical Rulership"],
            center_of_calculations,
            pluto_ecliptic,
        )

    if show_arabic_parts and not args["Aspects To Arabic Parts"]:
        ar_parts = [
            "Fortune",
            "Spirit",
            "Love",
            "Marriage",
            "Death",
            "Commerce",
            "Passion",
            "Friendship",
        ]
        for part in ar_parts:
            del planet_positions[part]

    aspects = calculate_planetary_aspects(
        copy.deepcopy(planet_positions), orbs, output_type, aspect_types=MAJOR_ASPECTS
    )  # Major aspects has been updated to include minor if
    fixstar_aspects = calculate_aspects_to_fixed_stars(
        utc_datetime,
        copy.deepcopy(planet_positions),
        house_cusps,
        orbs["Fixed Star"],
        MAJOR_ASPECTS,
        all_stars,
    )

    if not hide_planetary_aspects:
        to_return += f"{p}" + print_aspects(
            aspects=aspects,
            planet_positions=copy.deepcopy(planet_positions),
            orbs=orbs,
            imprecise_aspects=imprecise_aspects,
            minor_aspects=minor_aspects,
            degree_in_minutes=degree_in_minutes,
            house_positions=house_positions,
            orb=orb,
            type="Natal",
            p1_name="",
            p2_name="",
            notime=notime,
            output=output_type,
            show_aspect_score=show_score,
            complex_aspects=complex_aspects,
            center=center_of_calculations,
        )
    if not hide_fixed_star_aspects and fixstar_aspects:
        house_positions, house_cusps = calculate_house_positions(
            utc_datetime,
            latitude,
            longitude,
            altitude,
            copy.deepcopy(planet_positions),
            notime,
            HOUSE_SYSTEMS[house_system_name],
        )
        to_return += f"{p}" + print_fixed_star_aspects(
            fixstar_aspects,
            orb,
            minor_aspects,
            imprecise_aspects,
            notime,
            degree_in_minutes,
            copy.deepcopy(house_positions),
            read_fixed_stars(all_stars),
            output_type,
            all_stars,
            center=center_of_calculations,
        )
    if not hide_asteroid_aspects:
        asteroid_positions = calculate_planet_positions(
            utc_datetime,
            latitude,
            longitude,
            altitude,
            output_type,
            h_sys,
            "asteroids",
            center_of_calculations,
            classic_rulers=args["Classical Rulership"],
        )
        asteroid_aspects = calculate_aspects_takes_two(
            copy.deepcopy(planet_positions),
            copy.deepcopy(asteroid_positions),
            orbs,
            aspect_types=MAJOR_ASPECTS,
            output_type=output_type,
            type="asteroids",
            show_brief_aspects=show_brief_aspects,
        )
        if asteroid_aspects:
            to_return += f"{p}" + print_aspects(
                asteroid_aspects,
                copy.deepcopy(planet_positions),
                orbs,
                copy.deepcopy(asteroid_positions),
                imprecise_aspects,
                minor_aspects,
                degree_in_minutes,
                house_positions,
                orb,
                "Asteroids",
                "",
                "",
                notime,
                output_type,
                show_score,
                center=center_of_calculations,
            )
    if output_type == "html":
        print("</div>")
    elif output_type == "return_html":
        to_return += "</div>"

    if center_of_calculations != "heliocentric":
        if notime:
            if output_type in ("text", "html"):
                print(f"{string_moon_phase_imprecise}")
            else:
                if output_type == "return_text":
                    to_return += f"{br}{string_moon_phase_imprecise}"
                else:
                    to_return += f"{string_moon_phase_imprecise}"
        else:
            if output_type in ("text", "html"):
                print(f"{string_moon_phase}")
            else:
                to_return += f"{string_moon_phase}"

    name = f"{args['Name']} " if args["Name"] else ""

    if show_transits:
        planet_positions = calculate_planet_positions(
            utc_datetime,
            latitude,
            longitude,
            altitude,
            output_type,
            h_sys,
            "planets",
            center=center_of_calculations,
            classic_rulers=args["Classical Rulership"],
        )
        transits_planet_positions = calculate_planet_positions(
            transits_utc_datetime,
            transits_latitude,
            transits_longitude,
            transits_altitude,
            output_type,
            h_sys,
            "planets",
            center=center_of_calculations,
            classic_rulers=args["Classical Rulership"],
        )

        transit_aspects = calculate_aspects_takes_two(
            copy.deepcopy(planet_positions),
            copy.deepcopy(transits_planet_positions),
            orbs,
            aspect_types=MAJOR_ASPECTS,
            output_type=output_type,
            type="transits",
            show_brief_aspects=show_brief_aspects,
        )
        if output_type in ("text", "html"):
            print(
                f"{string_transits} {name}{transits_local_datetime.strftime('%Y-%m-%d %H:%M')} in {transits_location}{h2_}{nobold}"
            )
        else:
            to_return += f"{string_transits} {name} {transits_local_datetime.strftime('%Y-%m-%d %H:%M')} in {transits_location}{h2_}{nobold}"

        if not args["Transits Timezone"] or not args["Transits Location"]:
            if output_type in ("text", "html"):
                print(f"{string_no_transits_tz}")
            elif not EPHE:
                to_return += f"{string_no_transits_tz}"

        to_return += f"{p}" + print_aspects(
            transit_aspects,
            copy.deepcopy(planet_positions),
            orbs,
            copy.deepcopy(transits_planet_positions),
            imprecise_aspects,
            minor_aspects,
            degree_in_minutes,
            house_positions,
            orb,
            "Transit",
            "",
            "",
            notime,
            output_type,
            show_score,
            center=center_of_calculations,
        )

        star_positions = calculate_planet_positions(
            utc_datetime,
            latitude,
            longitude,
            altitude,
            output_type,
            h_sys,
            center=center_of_calculations,
            mode="stars",
            classic_rulers=args["Classical Rulership"],
        )
        transit_star_aspects = calculate_aspects_takes_two(
            copy.deepcopy(star_positions),
            copy.deepcopy(transits_planet_positions),
            orbs,
            aspect_types=MAJOR_ASPECTS,
            output_type=output_type,
            type="transits",
            show_brief_aspects=show_brief_aspects,
        )

        to_return += f"{p}" + print_aspects(
            transit_star_aspects,
            copy.deepcopy(planet_positions),
            orbs,
            copy.deepcopy(transits_planet_positions),
            imprecise_aspects,
            minor_aspects,
            degree_in_minutes,
            house_positions,
            orb,
            "Star Transit",
            "",
            "",
            notime,
            output_type,
            show_score,
            copy.deepcopy(star_positions),
            center=center_of_calculations,
        )

        asteroid_positions = calculate_planet_positions(
            utc_datetime,
            latitude,
            longitude,
            altitude,
            output_type,
            h_sys,
            "asteroids",
            center=center_of_calculations,
            classic_rulers=args["Classical Rulership"],
        )
        asteroid_transit_aspects = calculate_aspects_takes_two(
            copy.deepcopy(asteroid_positions),
            copy.deepcopy(transits_planet_positions),
            orbs,
            aspect_types=MAJOR_ASPECTS,
            output_type=output_type,
            type="asteroids",
            show_brief_aspects=show_brief_aspects,
        )
        if asteroid_transit_aspects:
            to_return += f"{p}" + print_aspects(
                asteroid_transit_aspects,
                copy.deepcopy(planet_positions),
                orbs,
                copy.deepcopy(transits_planet_positions),
                imprecise_aspects,
                minor_aspects,
                degree_in_minutes,
                house_positions,
                orb,
                "Asteroids Transit",
                "",
                "",
                notime,
                output_type,
                show_score,
                copy.deepcopy(asteroid_positions),
                center=center_of_calculations,
            )

    if show_synastry:
        planet_positions = calculate_planet_positions(
            utc_datetime,
            latitude,
            longitude,
            altitude,
            output_type,
            h_sys,
            center=center_of_calculations,
            classic_rulers=args["Classical Rulership"],
        )
        synastry_planet_positions = calculate_planet_positions(
            synastry_utc_datetime,
            synastry_latitude,
            synastry_longitude,
            synastry_altitude,
            output_type,
            h_sys,
            center=center_of_calculations,
            classic_rulers=args["Classical Rulership"],
        )

        synastry_aspects = calculate_aspects_takes_two(
            copy.deepcopy(planet_positions),
            copy.deepcopy(synastry_planet_positions),
            orbs,
            aspect_types=MAJOR_ASPECTS,
            output_type=output_type,
            type="synastry",
        )
        if output_type in ("text", "html"):
            print(f"{string_synastry} {name}and {args['Synastry']}{h2_}{nobold}")
        else:
            to_return += (
                f"{string_synastry} {name}and {args['Synastry']}{h2_}{nobold}{br}"
            )
        to_return += f"{p}" + print_aspects(
            synastry_aspects,
            copy.deepcopy(planet_positions),
            orbs,
            copy.deepcopy(synastry_planet_positions),
            imprecise_aspects,
            minor_aspects,
            degree_in_minutes,
            house_positions,
            orb,
            "Synastry",
            name,
            args["Synastry"],
            (notime or synastry_notime),
            output_type,
            show_score,
            center=center_of_calculations,
        )

    begin_date = utc_datetime - timedelta(days=10)
    end_date = utc_datetime + timedelta(days=10)
    # find_exact_aspects_in_timeframe(begin_date, end_date, latitude, longitude, altitude, orbs, center_of_calculations, step_days=1, output_type='text')

    # Make SVG chart if output is html
    if output_type in ("html", "return_html"):
        try:
            from . import chart_output
        except:
            import chart_output
        if show_transits:
            chart_type = "Transit"
        elif show_synastry:
            chart_type = "Synastry"
        else:
            chart_type = "Natal"

        if chart_type == "Natal":
            to_return += chart_output.chart_output(
                name,
                utc_datetime,
                longitude,
                latitude,
                local_timezone,
                place,
                chart_type,
                output_type,
                None,
                guid=args["Guid"] if args["Guid"] else None,
            )
        elif chart_type == "Transit":
            to_return += chart_output.chart_output(
                name,
                utc_datetime,
                longitude,
                latitude,
                local_timezone,
                place,
                chart_type,
                output_type,
                transits_utc_datetime,
                output_type,
                second_local_timezone=local_transits_timezone,
                second_place=transits_location,
                guid=args["Guid"] if args["Guid"] else None,
            )
        elif chart_type == "Synastry":
            to_return += chart_output.chart_output(
                name,
                utc_datetime,
                longitude,
                latitude,
                local_timezone,
                place,
                chart_type,
                output_type,
                synastry_utc_datetime,
                args["Synastry"],
                synastry_longitude,
                synastry_latitude,
                synastry_local_timezone,
                synastry_place,
                guid=args["Guid"] if args["Guid"] else None,
            )

        if output_type in ("html", "return_html"):
            print("</div></body>\n</html>")
        else:
            to_return += "\n    </div></body>\n</html>"
    return to_return


if __name__ == "__main__":
    main()
