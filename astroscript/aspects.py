from datetime import datetime, timedelta
from math import sin, cos, radians, exp, pi

from .constants import *
from .coords import coord_in_minutes
from .positions import calculate_planet_positions

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
