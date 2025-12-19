from .constants import (
    CLASSICAL_RULERSHIP,
    DETRIMENT,
    EXALTATION,
    FALL,
    FORMER_RULERS,
    RULERSHIP,
    ZODIAC_MODALITIES,
)

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
