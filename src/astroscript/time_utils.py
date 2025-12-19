from datetime import datetime, timedelta
from math import sin, cos, radians, pi

import pytz
import swisseph as swe

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
