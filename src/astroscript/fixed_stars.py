import csv

import swisseph as swe

from .config import EPHE

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
