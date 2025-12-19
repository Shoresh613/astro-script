from datetime import datetime
import os

import swisseph as swe

from .config import EPHE
from .constants import ASTEROIDS, PLANETS
from .coords import longitude_to_zodiac
from .dignity import get_decan_ruler
from .fixed_stars import get_fixed_star_position, read_fixed_stars
from .houses import calculate_house_positions, calculate_individual_house_position
from .arabic_parts import add_arabic_parts

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
