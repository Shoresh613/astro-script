import os

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
