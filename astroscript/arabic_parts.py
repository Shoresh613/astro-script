from datetime import datetime

import swisseph as swe

from .constants import PLANETS
from .coords import longitude_to_zodiac

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
