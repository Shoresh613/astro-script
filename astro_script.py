import swisseph as swe
import datetime
import pytz
import json
import os
import argparse
from math import cos, radians

swe.set_ephe_path('./ephe/')

############### Constants ###############
aspect_types = {'Conjunction': 0, 'Opposition': 180, 'Trine': 120, 'Square': 90, 'Sextile': 60,}
minor_aspect_types = {
    'Quincunx': 150, 'Semi-Sextile': 30, 'Semi-Square': 45, 'Quintile': 72, 'Bi-Quintile': 144,
    'Sesqui-Square': 135, 'Septile': 51.4285714, 'Novile': 40, 'Decile': 36,
}
# notime_imprecise_planets = ['Moon', 'Mercury', 'Venus', 'Sun', 'Mars']  # Aspects that are uncertain without time of day
# Movement per day for each planet in degrees
off_by = { "Sun": 1, "Moon": 13.2, "Mercury": 1.2, "Venus": 1.2, "Mars": 0.5, "Jupiter": 0.2, "Saturn": 0.1,
          "Uranus": 0.04, "Neptune": 0.03, "Pluto": 0.01, "Chiron": 0.02, "North Node": 0.05,  "South Node": 0.05}

always_exclude_if_no_time = ['Ascendant', 'Midheaven']  # Aspects that are always excluded if no time of day is specified
filename = 'saved_events.json'  # Run save_event.py first to create this file and update with your preferred data
house_systems = {
    'Placidus': 'P',
    'Koch': 'K',
    'Porphyrius': 'O',
    'Regiomontanus': 'R',
    'Campanus': 'C',
    'Equal (Ascendant cusp 1)': 'A',
    'Equal (Aries cusp 1)': 'E',
    'Vehlow equal': 'V',
    'Axial rotation system/Meridian system/Zariel system': 'X',
    'Horizon/Azimuthal system': 'H',
    'Polich/Page/Topocentric': 'T',
    'Alcabitius': 'B',
    'Gauquelin sectors': 'G',
    'Sripati': 'S',
    'Morinus': 'M'
}

PLANETS = {
    'Sun': swe.SUN, 'Moon': swe.MOON, 'Mercury': swe.MERCURY, 'Venus': swe.VENUS,
    'Mars': swe.MARS, 'Jupiter': swe.JUPITER, 'Saturn': swe.SATURN,
    'Uranus': swe.URANUS, 'Neptune': swe.NEPTUNE, 'Pluto': swe.PLUTO,
    'Chiron': swe.CHIRON, 'North Node': swe.MEAN_NODE
}

############### Functions ###############
def convert_to_utc(local_datetime, local_timezone):
    """
    Convert a naive datetime object to UTC using a specified timezone.

    Parameters:
    - local_datetime (datetime.datetime): A naive datetime object representing local time.
    - local_timezone (pytz.timezone): A timezone object representing the local timezone.

    Returns:
    - datetime.datetime: A datetime object converted to UTC.
    """
    # Ensure local_datetime is naive before localization
    if local_datetime.tzinfo is not None:
        raise ValueError("local_datetime should be naive (no timezone info).")

    # Localize the naive datetime object to the specified timezone
    local_datetime = local_timezone.localize(local_datetime)
    
    # Convert the timezone-aware datetime object to UTC
    utc_datetime = local_datetime.astimezone(pytz.utc)
    
    return utc_datetime

def calculate_house_positions(date, latitude, longitude, planets_positions, notime=False):
    """
    Calculate the house positions for a given datetime, latitude, and longitude, considering the positions of planets.

    Parameters:
    - date (datetime.datetime): The date and time for the calculation. Must include a time component; calculations at midnight may be less accurate.
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
    # Validate input date has a time component (convention to use 00:00:00 for unknown time )
    if date.hour == 0 and date.minute == 0 and date.second == 0:
        print("Warning: Time is not set. Calculations may be less accurate.")

    jd = swe.julday(date.year, date.month, date.day, date.hour + date.minute / 60.0 + date.second / 3600)
    h_sys = 'P'  # Placidus house system; consider making this a parameter if flexibility is needed
    houses, ascmc = swe.houses(jd, latitude, longitude, h_sys.encode('utf-8'))

    ascendant_long = ascmc[0]  # Ascendant is the first item in ascmc list
    midheaven_long = ascmc[1]  # Midheaven is the second item in ascmc list
   
    # Initialize dictionary with Ascendant and Midheaven
    house_positions = {
        'Ascendant': {'longitude': ascendant_long, 'house': 1},
        'Midheaven': {'longitude': midheaven_long, 'house': 10}  # Midheaven is traditionally associated with the 10th house
    }

    # Assign planets to houses
    for planet, planet_info in planets_positions.items():
        planet_longitude = planet_info['longitude']
        house_num = 1
        for i, cusp in enumerate(houses[1:], start=1):  # Skip the 0th cusp as it represents the Ascendant
            if planet_longitude < cusp:
                break
            house_num = i + 1
        house_positions[planet] = {'longitude': planet_longitude, 'house': house_num}

    return house_positions, houses[:13]  # Return house positions and cusps (including Ascendant)

def longitude_to_zodiac(longitude):
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
    zodiac_signs = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 
                    'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']
    sign_index = int(longitude // 30)
    degree = int(longitude % 30)
    minutes = int((longitude % 1) * 60)
    seconds = int((((longitude % 1) * 60) % 1) * 60)
    
    return f"{zodiac_signs[sign_index]} {degree}°{minutes}'{seconds}''"

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
    except swe.SwissephException as e:
        raise ValueError(f"Fixed star '{star_name}' not recognized: {e}")

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
    angular_difference = abs(planet_long - star_long) % 360
    # Normalize the angle to <= 180 degrees for comparison
    if angular_difference > 180:
        angular_difference = 360 - angular_difference
    
    angle_off = abs(angular_difference - aspect_angle)
    return angle_off <= orb, angle_off

def calculate_aspects_to_fixed_stars(date, planet_positions, houses, orb=1.0, aspect_types=None, all_stars=False):
    """
    List aspects between planets and fixed stars, considering the house placement of each fixed star
    and the angle difference from the exact aspect angle. This function enriches astrological analysis
    by providing detailed insights into the relationships between planets and stars, including how closely
    each aspect aligns with its ideal angular relationship.

    Parameters:
    - date (datetime.datetime): The date and time for the calculation.
    - planet_positions (dict): A dictionary of planets and their positions.
    - houses (list): A list of house cusp positions.
    - orb (float): Orb value for aspect consideration. Default is 1.0 degree.
    - aspect_types (dict, optional): A dictionary of aspect names and their angular distances.
                                     Defaults to common aspects if None.
    - all_stars (bool): Whether to include all stars or a predefined list of astrologically significant stars.

    Returns:
    - list: A list of tuples, each representing an aspect between a planet and a fixed star. Each tuple includes
            the planet name, star name, aspect name, the angle difference from the aspect angle, and the house of the fixed star.
    """
    if aspect_types is None:
        aspect_types = {'Conjunction': 0, 'Opposition': 180, 'Trine': 120, 'Square': 90, 'Sextile': 60}

    fixed_stars = read_fixed_stars(all_stars)
    jd = swe.julday(date.year, date.month, date.day, date.hour)  # Assumes date includes time information
    aspects = []

    for star_name in fixed_stars:
        try:
            star_long = get_fixed_star_position(star_name, jd)
            star_house = next((i + 1 for i, cusp in enumerate(houses) if star_long < cusp), 12)

            for planet, data in planet_positions.items():
                planet_long = data['longitude']
                for aspect_name, aspect_angle in aspect_types.items():
                    valid_aspect, angle_off = check_aspect(planet_long, star_long, aspect_angle, orb)
                    if valid_aspect:
                        aspects.append((planet, star_name, aspect_name, angle_off, star_house))
        except ValueError as e:
            print(f"Error processing star {star_name}: {e}")

    return aspects

def read_fixed_stars(all_stars=False):
    """
    Read and return a list of fixed star names from a predefined file. This function can select
    between a comprehensive list of all fixed stars or a curated list of those known for their
    astrological significance based on the input parameter.

    Parameters:
    - all_stars (bool): Determines which list of fixed stars to read:
                        if True, reads a comprehensive list;
                        if False, reads a list of astrologically significant stars.

    Returns:
    - list: A list containing the names of fixed stars.

    Raises:
    - FileNotFoundError: If the specified file cannot be found.
    - IOError: If there is an issue reading from the file.
    """
    filename = './ephe/fixed_stars_all.txt' if all_stars else './ephe/astrologically_known_fixed_stars.txt'
    
    try:
        with open(filename, 'r') as file:
            fixed_stars = file.read().splitlines()
    except FileNotFoundError:
        raise FileNotFoundError(f"The file '{filename}' was not found.")
    except IOError as e:
        raise IOError(f"An error occurred while reading from '{filename}': {e}")
    
    return fixed_stars

def get_max_star_name_length(all_stars=False):
    """
    Determine the length of the longest fixed star name from a predefined list. This function can
    operate on either a comprehensive list of all fixed stars or a curated list of those known for
    their astrological significance, depending on the input parameter.

    Parameters:
    - all_stars (bool): Determines which list of fixed stars to evaluate:
                        if True, uses a comprehensive list;
                        if False, uses a list of astrologically significant stars.

    Returns:
    - int: The length of the longest fixed star name in the selected list.

    Raises:
    - FileNotFoundError: If the specified file cannot be found. This is propagated from the
                         `read_fixed_stars` function.
    - IOError: If there is an issue reading from the file. This is also propagated from the
               `read_fixed_stars` function.
    """
    fixed_stars = read_fixed_stars(all_stars)
    max_length = max(len(star_name) for star_name in fixed_stars)
    return max_length

def calculate_planet_positions(date, latitude, longitude, h_sys='P'):
    """
    Calculate the ecliptic longitudes, signs, and retrograde status of celestial bodies
    at a given datetime, for a specified location. This includes the Sun, Moon, planets,
    Chiron, and the lunar nodes, along with the Ascendant (ASC) and Midheaven (MC).

    Parameters:
    - date (datetime.datetime): The datetime for which positions are calculated.
    - latitude (float): Latitude of the location in degrees.
    - longitude (float): Longitude of the location in degrees.

    Returns:
    - dict: A dictionary with each celestial body as keys, and dictionaries containing
      their ecliptic longitude, zodiac sign, and retrograde status ('R' if retrograde) as values.
    """
    jd = swe.julday(date.year, date.month, date.day, date.hour + date.minute / 60.0 + date.second / 3600.0)
    positions = {}

    for planet, id in PLANETS.items():
        pos, ret = swe.calc_ut(jd, id)
        positions[planet] = {
            'longitude': pos[0],
            'zodiac_sign': longitude_to_zodiac(pos[0]).split()[0],
            'retrograde': 'R' if pos[3] < 0 else ''
        }

    # Calculate Ascendant and Midheaven
    asc_mc = swe.houses(jd, latitude, longitude, h_sys.encode('utf-8'))[1]
    positions['Ascendant'] = {'longitude': asc_mc[0], 'zodiac_sign': longitude_to_zodiac(asc_mc[0]).split()[0], 'retrograde': ''}
    positions['Midheaven'] = {'longitude': asc_mc[1], 'zodiac_sign': longitude_to_zodiac(asc_mc[1]).split()[0], 'retrograde': ''}

    return positions

def coord_in_minutes(longitude):
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

    return f"{degrees}°{minutes}'{seconds}''"  

def calculate_aspects(planet_positions, orb, aspect_types):
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
        {"Sun", "Ascendant"}, {"Sun", "Midheaven"}, {"Moon", "Ascendant"}, {"Moon", "Midheaven"},
        {"Ascendant", "Midheaven"}, {"South Node", "North Node"}
    ]

    aspects_found = {}
    planet_names = list(planet_positions.keys())

    for i, planet1 in enumerate(planet_names):
        for planet2 in planet_names[i+1:]:
            # Skip calculation if the pair is in the exclusion list or the same planet
            if {planet1, planet2} in (excluded_pairs or planet1 == planet2):
                continue

            long1 = planet_positions[planet1]['longitude']
            long2 = planet_positions[planet2]['longitude']
            angle_diff = abs(long1 - long2) % 360
            angle_diff = min(angle_diff, 360 - angle_diff)  # Normalize to <= 180 degrees

            for aspect_name, aspect_angle in aspect_types.items():
                if abs(angle_diff - aspect_angle) <= orb:
                    # Check if the aspect is imprecise based on the movement per day of the planets involved
                    is_imprecise = any(
                        planet in off_by and off_by[planet] > angle_diff
                        for planet in (planet1, planet2)
                    )
                    
                    # Create a tuple for the planets involved in the aspect
                    planets_pair = (planet1, planet2)
                    
                    # Update the aspects_found dictionary
                    angle_diff = angle_diff - aspect_angle # Just show the difference


                    aspects_found[planets_pair] = {
                        'aspect_name': aspect_name,
                        'angle_diff': angle_diff,
                        'angle_diff_in_minutes': coord_in_minutes(angle_diff),
                        'is_imprecise': is_imprecise
                    }
    return aspects_found

def moon_phase(date):
    """
    Calculates the moon phase and illumination for a given date. The function considers 8 distinct phases 
    of the moon and returns the phase name and illumination percentage for the specified date.

    Parameters:
    - date (datetime.datetime): The date for which to calculate the moon phase and illumination.

    Returns:
    - a tuple (str: The name of the moon phase, float: the degree of moon illumination).

    The function considers 8 distinct phases of the moon and returns the phase name for the specified date.
    """
    jd = swe.julday(date.year, date.month, date.day)
    sun_pos = swe.calc_ut(jd, swe.SUN)[0][0]
    moon_pos = swe.calc_ut(jd, swe.MOON)[0][0]
    phase_angle = (moon_pos - sun_pos) % 360

    illumination = 50 - 50 * cos(radians(phase_angle))

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
        return "Waning Crescent"

def print_planet_positions(planet_positions, degree_in_minutes=False, notime=False, house_positions=None, orb=1):
    """
    Print the positions of planets in a human-readable format. This includes the zodiac sign, 
    degree (optionally in minutes), whether the planet is retrograde, and its house position 
    if available and relevant.

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
    print(f"\n{'Planet':<10} | {'Zodiac':<11} | {'Position':<10} | {'Retrograde':<10}", end='')
    if house_positions and not notime:  # Checks if house_positions is not empty
        print(f" | {'House':<5}", end='')
    print("\n" + ("-" * 58 if house_positions else "-" * 50))  

    for planet, info in planet_positions.items():
        if notime and (planet in always_exclude_if_no_time):
            continue
        longitude = info['longitude']
        # zodiac_index = int(longitude // 30)
        degrees_within_sign = longitude % 30
        position = coord_in_minutes(degrees_within_sign) if degree_in_minutes else f"{degrees_within_sign:.2f}°"
        retrograde = info['retrograde']
        zodiac = info['zodiac_sign']
        retrograde_status = "R" if retrograde else ""
        print(f"{planet:<10} | {zodiac:<11} | {position:>10} | {retrograde_status:<10}", end='')
        if house_positions and not notime:
            house_num = house_positions.get(planet, {}).get('house', 'Unknown')  
            print(f" | {house_num:<5}", end='')
        elif planet in off_by.keys() and off_by[planet] > orb:
            print(f"±{off_by[planet]}°", end='')
        print()

def print_aspects(aspects, imprecise_aspects="off", minor_aspects=True, degree_in_minutes=False, house_positions=None, orb=1, notime=False):
    """
    Prints astrological aspects between celestial bodies, offering options for display and filtering.

    Parameters:
    - aspects (dict): Dictionary containing aspect data between celestial bodies.
    - imprecise_aspects (str): Controls display of imprecise aspects ('off' or 'warn').
    - minor_aspects (bool): Whether to include minor aspects in the output.
    - degree_in_minutes (bool): Display angles in degrees, minutes, and seconds format.
    - house_positions (dict, optional): House positions for additional context, ignored if notime is True.
    - orb (float): Orb value used for aspect consideration.
    - notime (bool): If True, time-dependent aspects and house positions are not displayed.

    Directly prints formatted aspect information based on specified parameters.
    """

    print(f"\nPlanetary Aspects ({orb}° orb)", end="")
    print(" and minor aspects" if minor_aspects else "", end="")
    if notime:
        print(f" with imprecise aspects set to {imprecise_aspects}", end="")
    print(":\n" + "-" * 49)

    for planets, aspect_details in aspects.items():
        if degree_in_minutes:
            angle_with_degree = f"{aspect_details['angle_diff_in_minutes']}"
        else:
            angle_with_degree = f"{aspect_details['angle_diff']:.2f}°"
        if imprecise_aspects == "off" and (aspect_details['is_imprecise'] or planets[0] in always_exclude_if_no_time or planets[1] in always_exclude_if_no_time):
            continue
        else:
            print(f"{planets[0]:<10} | {aspect_details['aspect_name']:<14} | {planets[1]:<10} | {angle_with_degree:<7}", end='')
        if imprecise_aspects == "warning" and ((planets[0] in off_by.keys() or planets[1] in off_by.keys())):
            print(" (uncertain)", end='')
        print()
    print("\n")
    if not house_positions:
        print("* No time of day specified. Houses cannot be calculated. ")
        print("  Aspects to the Ascendant and Midheaven are not available.")
        print("  The positions of the Sun, Moon, Mercury, Venus, and Mars are uncertain.\n")
        print("\n  Please specify the time of birth for a complete chart.\n")

def print_fixed_star_aspects(aspects, orb=1, minor_aspects=False, imprecise_aspects="off", notime=True, degree_in_minutes=False, house_positions=None, all_stars=False):
    """
    Prints aspects between planets and fixed stars with options for minor aspects, precision warnings, and house positions.

    Parameters:
    - aspects (list): Aspects between planets and fixed stars.
    - orb (float): Orb for aspect significance.
    - minor_aspects (bool): Include minor aspects.
    - imprecise_aspects (str): Handle imprecise aspects ('off' or 'warn').
    - notime (bool): Exclude time-dependent data.
    - degree_in_minutes (bool): Show angles in degrees, minutes, and seconds.
    - house_positions (dict, optional): Mapping of fixed stars to house positions.
    - all_stars (bool): Include aspects for all stars or significant ones only.

    Outputs a formatted list of aspects to the console based on the provided parameters.
    """

    print(f"Fixed Star Aspects ({orb}° orb)", end="")
    print(" including Minor Aspects" if minor_aspects else "", end="")
    if notime:
        print(f" with Imprecise Aspects set to {imprecise_aspects}", end="")
    print()
    
    # For formatting the table
    max_star_name_length = get_max_star_name_length(all_stars)

    print(f"{'Planet':<10} | {'Aspect':<14} | {'Star':<{max_star_name_length}} | {'Margin':<9}", end="")
    if house_positions and not notime:
        print(f" | {'Star in House':<5}", end='')
    print("\n" + "-" * (47+max_star_name_length)) 
    for aspect in aspects:
        planet, star_name, aspect_name, angle, house = aspect
        if degree_in_minutes:
            angle = coord_in_minutes(angle)
        else:
            angle = f"{angle:.2f}°"
        print(f"{planet:<10} | {aspect_name:<14} | {star_name:<{max_star_name_length}} | {angle:<9}", end='')

        if house_positions and not notime:
            print(f" | {house:<5}", end='')
        elif planet in off_by.keys() and off_by[planet] > orb:
            print(f" ±{off_by[planet]}°", end='')
        print()

    print()

# Function to check if there is an entry for a specified name in the JSON file
def load_event(filename, name):
    """
    Load event details from a JSON file based on the given event name.

    Attempts to read from a specified file and retrieve event information for a named event. 
    If successful, returns the event details; otherwise, provides an appropriate message.

    Parameters:
    - filename (str): Path to the JSON file containing event data.
    - name (str): The name of the event to retrieve information for.

    Returns:
    - dict or bool: Event details as a dictionary if found, False otherwise.

    Raises:
    - FileNotFoundError: If the specified file does not exist.
    - json.JSONDecodeError: If there's an error parsing the JSON file.
    """
    # Check if the file exists
    if not os.path.exists(filename):
        print(f"No file named {filename} found.")
        return False

    # Read the current data from the file
    try:
        with open(filename, 'r') as file:
            data = json.load(file)
    except json.JSONDecodeError:
        print(f"Error reading JSON data from {filename}.")
        return False

    # Check if the name exists in the data
    if name in data:
        return data[name],
    else:
        print(f"No entry found for {name}.")
        return False

def main():
    parser = argparse.ArgumentParser(description='''If no arguments are passed, values entered in the script will be used.
If a name is passed, the script will look up the record for that name in the JSON file and overwrite other passed values,
provided there are such values stored in the file (only the first 6 types are stored). 
If no record is found, default values will be used.''')

    # Add arguments
    parser.add_argument('--name', help='Name to look up the record for.', required=False)
    parser.add_argument('--date', help='Date of the event (YYYY-MM-DD HH:MM:SS local time).', required=False)
    parser.add_argument('--latitude', type=float, help='Latitude of the location in degrees, e.g. 57.6828.', required=False)
    parser.add_argument('--longitude', type=float, help='Longitude of the location in degrees, e.g. 11.96.', required=False)
    parser.add_argument('--timezone', help='Timezone of the location (e.g. "Europe/Stockholm").', required=False)
    parser.add_argument('--place', help='Name of location.', required=False)
    parser.add_argument('--imprecise_aspects', choices=['off', 'warn'], help='Whether to not show imprecise aspects or just warn.', required=False)
    parser.add_argument('--minor_aspects', choices=['true','false'], help='Whether to show minor aspects.', required=False)
    parser.add_argument('--orb', type=float, help='Orb size in degrees.', required=False)
    parser.add_argument('--degree_in_minutes',choices=['true','false'], help='Show degrees in arch minutes and seconds', required=False)
    parser.add_argument('--all_stars', choices=['true','false'], help='Show aspects for all fixed stars.', required=False)
    parser.add_argument('--house_system', choices=list(house_systems.keys()), help='House system to use (Placidus, Koch etc).', required=False)
    parser.add_argument('--hide_planetary_positions', choices=['true','false'], help='Output: hide what signs and houses (if time specified) planets are in.', required=False)
    parser.add_argument('--hide_planetary_aspects', choices=['true','false'], help='Output: hide aspects planets are in.', required=False)
    parser.add_argument('--hide_fixed_star_aspects', choices=['true','false'], help='Output: hide aspects planets are in to fixed stars.', required=False)

    # Parse the arguments
    args = parser.parse_args()

    # Check if any arguments were provided
    name = args.name if args.name else None

    try:
        local_datetime = datetime.datetime.strptime(args.date, "%Y-%m-%d %H:%M:%S") if args.date else datetime.datetime.now()
    except ValueError:
        print("Invalid date format. Please use YYYY-MM-DD HH:MM:SS.")
        local_datetime = None

    ######### Default settings if no arguments are passed. Change default by entering other option after 'else #########
    latitude = args.latitude if args.latitude is not None else 57.6828
    longitude = args.longitude if args.longitude is not None else 11.9624
    local_timezone = args.timezone if args.timezone else pytz.timezone('Europe/Stockholm')
    # If "off", the script will not show such aspects, if "warn" print a warning for uncertain aspects
    imprecise_aspects = args.imprecise_aspects if args.imprecise_aspects else "off"
    # If True, the script will include minor aspects
    minor_aspects = True if args.minor_aspects and args.minor_aspects.lower() in ["true", "yes", "1"] else False
    orb = float(args.orb) if args.orb else 1  # Default orb size set to 1
    # If True, the script will show the positions in degrees and minutes
    degree_in_minutes = True if args.degree_in_minutes and args.degree_in_minutes.lower() in ["true", "yes", "1"] else False
    # If True, the script will include all roughly 700 fixed stars
    all_stars = True if args.all_stars and args.all_stars.lower() in ["true", "yes", "1"] else False
    if args.house_system and args.house_system not in house_systems:
        print(f"Invalid house system. Available house systems are: {', '.join(house_systems.keys())}")
        h_sys = house_systems["Placidus"]  # Default house system
    h_sys = house_systems[args.house_system] if args.house_system else house_systems["Placidus"]  # Default house system


    #################### Load event ####################
    if not name: name = "Mikael"  # Specify the name you want to load from file unless passed as argument
    exists = load_event(filename, name)
    if exists:
        local_datetime = datetime.datetime.fromisoformat(exists[0]['datetime'])
        latitude = exists[0]['latitude']
        longitude = exists[0]['longitude']
        local_timezone = pytz.timezone(exists[0]['timezone'])
        place = exists[0]['location']
    
    utc_datetime = convert_to_utc(local_datetime, local_timezone)
    # Check if the time is set, or only the date, this is not compatible with people born at midnight (but can set second to 1)
    notime = (local_datetime.hour == 0 and local_datetime.minute == 0 and local_datetime.second == 0)

    #################### Main Script ####################    
    if exists:
        print(f"\nName: {name}")
    if place:
        print(f"Place: {place}")
    print(f"\nLocal Time: {local_datetime} {local_timezone}")
    print(f"UTC Time: {utc_datetime} UTC")
    if degree_in_minutes:
        print(f"Latitude: {coord_in_minutes(latitude)}, Longitude: {coord_in_minutes(longitude)}")
    else:
        print(f"Latitude: {latitude}, Longitude: {longitude}")
    house_system_name = next((name for name, code in house_systems.items() if code == h_sys), None)
    print(f"House system: {house_system_name}\n")

    if minor_aspects:
        aspect_types.update(minor_aspect_types)

    planet_positions = calculate_planet_positions(utc_datetime, latitude, longitude)
    house_positions, house_cusps = calculate_house_positions(utc_datetime, latitude, longitude, planet_positions, notime)
    aspects = calculate_aspects(planet_positions, orb, aspect_types=aspect_types)
    fixstar_aspects = calculate_aspects_to_fixed_stars(utc_datetime, planet_positions, house_cusps, orb, aspect_types, all_stars)
    moon_phase_name, illumination = moon_phase(utc_datetime)

    if not args.hide_planetary_positions:
        print_planet_positions(planet_positions, degree_in_minutes, notime, house_positions, orb)
    if not args.hide_planetary_aspects:
        print_aspects(aspects, imprecise_aspects, minor_aspects, degree_in_minutes, house_positions, orb, notime)
    if not args.hide_fixed_star_aspects:
        print_fixed_star_aspects(fixstar_aspects, orb, minor_aspects, imprecise_aspects, notime, degree_in_minutes, house_positions, all_stars=all_stars)
    
    print(f"Moon Phase: {moon_phase_name}\nMoon Illumination: approximately {illumination:.1f}%\n")

if __name__ == "__main__":
    main()