"""
Chart pattern detection functions for the astro script.
Contains functions for detecting T-squares, Yods, Grand Crosses, Grand Trines, and Kites.
"""

from constants import *


def aspect_diff(angle1: float, angle2: float) -> float:
    """
    Calculate the smallest angular difference between two angles.

    Args:
        angle1: first angle in degrees
        angle2: second angle in degrees

    Returns:
        float: smallest angular difference
    """
    diff = abs(angle1 - angle2)
    return min(diff, 360 - diff)


def find_t_squares(
    planet_positions: dict, orb_opposition: float = 8, orb_square: float = 6
) -> list:
    """
    Find T-square patterns in the chart.

    Args:
        planet_positions: dictionary of planet positions
        orb_opposition: orb for opposition aspects
        orb_square: orb for square aspects

    Returns:
        list: list of T-square patterns found
    """
    t_squares = []
    planets = list(planet_positions.keys())

    for i, planet1 in enumerate(planets):
        for j, planet2 in enumerate(planets[i + 1 :], i + 1):
            # Check for opposition between planet1 and planet2
            diff = aspect_diff(
                planet_positions[planet1]["longitude"],
                planet_positions[planet2]["longitude"],
            )

            if abs(diff - 180) <= orb_opposition:
                # Found opposition, now look for the apex planet
                for k, planet3 in enumerate(planets):
                    if planet3 != planet1 and planet3 != planet2:
                        # Check if planet3 squares both planet1 and planet2
                        diff1 = aspect_diff(
                            planet_positions[planet1]["longitude"],
                            planet_positions[planet3]["longitude"],
                        )
                        diff2 = aspect_diff(
                            planet_positions[planet2]["longitude"],
                            planet_positions[planet3]["longitude"],
                        )

                        if (
                            abs(diff1 - 90) <= orb_square
                            and abs(diff2 - 90) <= orb_square
                        ):
                            t_squares.append(
                                {
                                    "type": "T-Square",
                                    "opposition": [planet1, planet2],
                                    "apex": planet3,
                                    "orb_opposition": abs(diff - 180),
                                    "orb_square1": abs(diff1 - 90),
                                    "orb_square2": abs(diff2 - 90),
                                }
                            )

    return t_squares


def find_yod(
    planet_positions: dict, orb_opposition: float = 8, orb_square: float = 6
) -> list:
    """
    Find Yod patterns (Finger of God) in the chart.

    Args:
        planet_positions: dictionary of planet positions
        orb_opposition: orb for quincunx aspects (150°)
        orb_square: orb for sextile aspects (60°)

    Returns:
        list: list of Yod patterns found
    """
    yods = []
    planets = list(planet_positions.keys())

    for i, planet1 in enumerate(planets):
        for j, planet2 in enumerate(planets[i + 1 :], i + 1):
            # Check for sextile between planet1 and planet2
            diff = aspect_diff(
                planet_positions[planet1]["longitude"],
                planet_positions[planet2]["longitude"],
            )

            if abs(diff - 60) <= orb_square:
                # Found sextile, now look for the apex planet
                for k, planet3 in enumerate(planets):
                    if planet3 != planet1 and planet3 != planet2:
                        # Check if planet3 forms quincunx with both planet1 and planet2
                        diff1 = aspect_diff(
                            planet_positions[planet1]["longitude"],
                            planet_positions[planet3]["longitude"],
                        )
                        diff2 = aspect_diff(
                            planet_positions[planet2]["longitude"],
                            planet_positions[planet3]["longitude"],
                        )

                        if (
                            abs(diff1 - 150) <= orb_opposition
                            and abs(diff2 - 150) <= orb_opposition
                        ):
                            yods.append(
                                {
                                    "type": "Yod",
                                    "sextile": [planet1, planet2],
                                    "apex": planet3,
                                    "orb_sextile": abs(diff - 60),
                                    "orb_quincunx1": abs(diff1 - 150),
                                    "orb_quincunx2": abs(diff2 - 150),
                                }
                            )

    return yods


def find_grand_crosses(planet_positions: dict, orb: float = 8) -> list:
    """
    Find Grand Cross patterns in the chart.

    Args:
        planet_positions: dictionary of planet positions
        orb: orb for aspects

    Returns:
        list: list of Grand Cross patterns found
    """
    grand_crosses = []
    planets = list(planet_positions.keys())

    for i, planet1 in enumerate(planets):
        for j, planet2 in enumerate(planets[i + 1 :], i + 1):
            for k, planet3 in enumerate(planets[j + 1 :], j + 1):
                for l, planet4 in enumerate(planets[k + 1 :], k + 1):
                    # Check if we have two oppositions and four squares
                    positions = [
                        planet_positions[planet1]["longitude"],
                        planet_positions[planet2]["longitude"],
                        planet_positions[planet3]["longitude"],
                        planet_positions[planet4]["longitude"],
                    ]

                    # Sort by longitude
                    planet_order = sorted(
                        zip(positions, [planet1, planet2, planet3, planet4])
                    )
                    sorted_positions = [pos for pos, _ in planet_order]
                    sorted_planets = [planet for _, planet in planet_order]

                    # Check for Grand Cross pattern
                    oppositions = []
                    squares = []

                    for idx in range(4):
                        # Check opposition with planet 2 positions away
                        opp_idx = (idx + 2) % 4
                        diff_opp = aspect_diff(
                            sorted_positions[idx], sorted_positions[opp_idx]
                        )

                        if abs(diff_opp - 180) <= orb:
                            oppositions.append(
                                (sorted_planets[idx], sorted_planets[opp_idx])
                            )

                        # Check square with adjacent planets
                        sq_idx = (idx + 1) % 4
                        diff_sq = aspect_diff(
                            sorted_positions[idx], sorted_positions[sq_idx]
                        )

                        if abs(diff_sq - 90) <= orb:
                            squares.append(
                                (sorted_planets[idx], sorted_planets[sq_idx])
                            )

                    if len(oppositions) >= 2 and len(squares) >= 4:
                        grand_crosses.append(
                            {
                                "type": "Grand Cross",
                                "planets": sorted_planets,
                                "oppositions": oppositions,
                                "squares": squares,
                            }
                        )

    return grand_crosses


def find_grand_trines(planet_positions: dict, orb: float = 8) -> list:
    """
    Find Grand Trine patterns in the chart.

    Args:
        planet_positions: dictionary of planet positions
        orb: orb for trine aspects

    Returns:
        list: list of Grand Trine patterns found
    """
    grand_trines = []
    planets = list(planet_positions.keys())

    for i, planet1 in enumerate(planets):
        for j, planet2 in enumerate(planets[i + 1 :], i + 1):
            for k, planet3 in enumerate(planets[j + 1 :], j + 1):
                # Check if all three planets form trines with each other
                diff12 = aspect_diff(
                    planet_positions[planet1]["longitude"],
                    planet_positions[planet2]["longitude"],
                )
                diff13 = aspect_diff(
                    planet_positions[planet1]["longitude"],
                    planet_positions[planet3]["longitude"],
                )
                diff23 = aspect_diff(
                    planet_positions[planet2]["longitude"],
                    planet_positions[planet3]["longitude"],
                )

                if (
                    abs(diff12 - 120) <= orb
                    and abs(diff13 - 120) <= orb
                    and abs(diff23 - 120) <= orb
                ):
                    grand_trines.append(
                        {
                            "type": "Grand Trine",
                            "planets": [planet1, planet2, planet3],
                            "orb12": abs(diff12 - 120),
                            "orb13": abs(diff13 - 120),
                            "orb23": abs(diff23 - 120),
                        }
                    )

    return grand_trines


def find_kites(planet_positions: dict, orb: float = 8) -> list:
    """
    Find Kite patterns in the chart (Grand Trine + opposition).

    Args:
        planet_positions: dictionary of planet positions
        orb: orb for aspects

    Returns:
        list: list of Kite patterns found
    """
    kites = []
    planets = list(planet_positions.keys())

    # First find all Grand Trines
    grand_trines = find_grand_trines(planet_positions, orb)

    # For each Grand Trine, look for a fourth planet that opposes one of the trine planets
    for trine in grand_trines:
        trine_planets = trine["planets"]

        for planet4 in planets:
            if planet4 not in trine_planets:
                # Check if planet4 opposes any of the trine planets
                for trine_planet in trine_planets:
                    diff = aspect_diff(
                        planet_positions[trine_planet]["longitude"],
                        planet_positions[planet4]["longitude"],
                    )

                    if abs(diff - 180) <= orb:
                        # Found a kite - planet4 opposes trine_planet
                        # Now check if planet4 sextiles the other two trine planets
                        other_planets = [p for p in trine_planets if p != trine_planet]

                        sextiles = []
                        for other_planet in other_planets:
                            diff_sext = aspect_diff(
                                planet_positions[other_planet]["longitude"],
                                planet_positions[planet4]["longitude"],
                            )
                            if abs(diff_sext - 60) <= orb:
                                sextiles.append((other_planet, planet4))

                        if len(sextiles) == 2:  # Both sextiles present
                            kites.append(
                                {
                                    "type": "Kite",
                                    "grand_trine": trine_planets,
                                    "opposition": (trine_planet, planet4),
                                    "sextiles": sextiles,
                                    "focal_planet": planet4,
                                }
                            )

    return kites


def assess_planet_strength(planet_signs: dict, classic_rulership: bool = False) -> dict:
    """
    Assess the strength of planets based on their signs.

    Args:
        planet_signs: dictionary mapping planets to their signs
        classic_rulership: whether to use classical rulerships

    Returns:
        dict: planet strength assessments
    """
    strength_scores = {}
    # Define rulerships (modern vs classical)
    if classic_rulership:
        rulerships = CLASSICAL_RULERSHIP
    else:
        rulerships = RULERSHIP

    exaltations = EXALTATION
    detriments = DETRIMENT
    falls = FALL

    for planet, sign in planet_signs.items():
        score = 0
        status = "neutral"

        # Check for rulership
        if sign in rulerships.get(planet, []):
            score += 5
            status = "dignified (ruler)"

        # Check for exaltation
        elif sign == exaltations.get(planet):
            score += 4
            status = "exalted"

        # Check for detriment
        elif sign in detriments.get(planet, []):
            score -= 4
            status = "detriment"

        # Check for fall
        elif sign == falls.get(planet):
            score -= 5
            status = "fall"

        strength_scores[planet] = {"score": score, "status": status, "sign": sign}

    return strength_scores


def check_degree(planet_signs: dict, degrees_within_sign: dict) -> dict:
    """
    Check for critical degrees and special degree positions.

    Args:
        planet_signs: dictionary mapping planets to their signs
        degrees_within_sign: dictionary mapping planets to their degrees within sign

    Returns:
        dict: degree analysis for each planet
    """
    degree_analysis = {}

    # Critical degrees for each sign
    critical_degrees = {
        "cardinal": [0, 13, 26],  # Aries, Cancer, Libra, Capricorn
        "fixed": [8, 9, 21, 22],  # Taurus, Leo, Scorpio, Aquarius
        "mutable": [4, 17],  # Gemini, Virgo, Sagittarius, Pisces
    }

    cardinal_signs = ["Aries", "Cancer", "Libra", "Capricorn"]
    fixed_signs = ["Taurus", "Leo", "Scorpio", "Aquarius"]
    mutable_signs = ["Gemini", "Virgo", "Sagittarius", "Pisces"]

    for planet, sign in planet_signs.items():
        degree = degrees_within_sign.get(planet, 0)
        analysis = {
            "degree": degree,
            "is_critical": False,
            "is_anaretic": False,
            "quality": "neutral",
        }

        # Check for critical degrees
        if sign in cardinal_signs:
            if int(degree) in critical_degrees["cardinal"]:
                analysis["is_critical"] = True
        elif sign in fixed_signs:
            if int(degree) in critical_degrees["fixed"]:
                analysis["is_critical"] = True
        elif sign in mutable_signs:
            if int(degree) in critical_degrees["mutable"]:
                analysis["is_critical"] = True

        # Check for anaretic degree (29°)
        if 29 <= degree < 30:
            analysis["is_anaretic"] = True
            analysis["quality"] = "urgent"

        # Check for early degrees (0-1°)
        elif 0 <= degree < 1:
            analysis["quality"] = "new/raw"

        degree_analysis[planet] = analysis

    return degree_analysis


def is_planet_elevated(planet_positions: dict) -> dict:
    """
    Check which planets are elevated (close to Midheaven).

    Args:
        planet_positions: dictionary of planet positions

    Returns:
        dict: elevation status for each planet
    """
    elevation_status = {}

    if "Midheaven" not in planet_positions:
        return elevation_status

    mc_longitude = planet_positions["Midheaven"]["longitude"]

    for planet, position in planet_positions.items():
        if planet in ["Midheaven", "IC", "Ascendant", "Descendant", "house_cusps"]:
            continue

        # Calculate angular distance from MC
        diff = aspect_diff(position["longitude"], mc_longitude)

        elevation_status[planet] = {
            "distance_from_mc": diff,
            "is_elevated": diff <= 10,  # Within 10 degrees of MC
            "is_very_elevated": diff <= 5,  # Within 5 degrees of MC
        }

    return elevation_status
