import swisseph as swe
from datetime import datetime, timedelta
import pytz
import json
import os
import argparse
from math import cos, radians
from geopy.geocoders import Nominatim
from tabulate import tabulate
import save_event
from version import __version__
import csv
from colorama import init, Fore, Style

swe.set_ephe_path('./ephe/')
saved_locations_file = 'saved_locations.json'  # File to save locations to
saved_events_file = 'saved_events.json'

############### Constants ###############
ASPECT_TYPES = {'Conjunction': 0, 'Opposition': 180, 'Trine': 120, 'Square': 90, 'Sextile': 60,}
MINOR_ASPECT_TYPES = {
    'Quincunx': 150, 'Semi-Sextile': 30, 'Semi-Square': 45, 'Quintile': 72, 'Bi-Quintile': 144,
    'Sesqui-Square': 135, 'Septile': 51.4285714, 'Novile': 40, 'Decile': 36,
}
MAJOR_ASPECTS = {
    'Conjunction': {'Degrees': 0, 'Score': 40, 'Comment': 'Impactful, varies by planets involved.'},
    'Opposition': {'Degrees': 180, 'Score': 10, 'Comment': 'Polarities needing integration.'},
    'Square': {'Degrees': 90, 'Score': 15, 'Comment': 'Tension and obstacles.'},
    'Trine': {'Degrees': 120, 'Score': 90, 'Comment': 'Promotes ease and talents.'},
    'Sextile': {'Degrees': 60, 'Score': 80, 'Comment': 'Opportunities and support.'},
}

MINOR_ASPECTS = {
    'Semi-Square': {'Degrees': 45, 'Score': 25, 'Comment': 'Friction and minor challenges.'},
    'Sesqui-Square': {'Degrees': 135, 'Score': 20, 'Comment': 'Less intense square, irritation.'},
    'Semi-Sextile': {'Degrees': 30, 'Score': 70, 'Comment': 'Slightly beneficial, subtle.'},
    'Quincunx': {'Degrees': 150, 'Score': 30, 'Comment': 'Adjustment and misunderstandings.'},
    'Quintile': {'Degrees': 72, 'Score': 75, 'Comment': 'Creativity and talent.'},
    'Bi-Quintile': {'Degrees': 144, 'Score': 75, 'Comment': 'Creative expression, like quintile.'},
    'Septile': {'Degrees': 51.4285714, 'Score': 60, 'Comment': 'Spiritual insights, less tangible.'},
    'Novile': {'Degrees': 40, 'Score': 65, 'Comment': 'Spiritual insights, harmonious.'},
    'Decile': {'Degrees': 36, 'Score': 50, 'Comment': 'Growth opportunities, mild challenges.'},
}

ALL_ASPECTS = {**MAJOR_ASPECTS.copy(), **MINOR_ASPECTS}

# Dictionaries for hard and soft aspects based on the scores
HARD_ASPECTS = {name: info for name, info in ALL_ASPECTS.items() if info['Score'] < 50}
SOFT_ASPECTS = {name: info for name, info in ALL_ASPECTS.items() if info['Score'] >= 50}

# Movement per day for each planet in degrees
OFF_BY = { "Sun": 1, "Moon": 13.2, "Mercury": 1.2, "Venus": 1.2, "Mars": 0.5, "Jupiter": 0.2, "Saturn": 0.1,
          "Uranus": 0.04, "Neptune": 0.03, "Pluto": 0.01, "Chiron": 0.02, "North Node": 0.05,  "South Node": 0.05, "True Node": 0.05,
          "Ascendant": 360, "Midheaven": 360}

ALWAYS_EXCLUDE_IF_NO_TIME = ['Ascendant', 'Midheaven']  # Aspects that are always excluded if no time of day is specified
FILENAME = 'saved_events.json' 
HOUSE_SYSTEMS = {
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
    'Chiron': swe.CHIRON, 'North Node': swe.TRUE_NODE, 
}

ZODIAC_ELEMENTS = {
    'Aries': 'Fire', 'Taurus': 'Earth', 'Gemini': 'Air', 'Cancer': 'Water',
    'Leo': 'Fire', 'Virgo': 'Earth', 'Libra': 'Air', 'Scorpio': 'Water',
    'Sagittarius': 'Fire', 'Capricorn': 'Earth', 'Aquarius': 'Air', 'Pisces': 'Water'
}

ZODIAC_MODALITIES = {
    'Cardinal': ['Aries', 'Cancer', 'Libra', 'Capricorn'],
    'Fixed': ['Taurus', 'Leo', 'Scorpio', 'Aquarius'],
    'Mutable': ['Gemini', 'Virgo', 'Sagittarius', 'Pisces'],
}

ZODIAC_SIGN_TO_MODALITY = {
    'Aries': 'Cardinal', 'Taurus': 'Fixed', 'Gemini': 'Mutable',
    'Cancer': 'Cardinal', 'Leo': 'Fixed', 'Virgo': 'Mutable',
    'Libra': 'Cardinal', 'Scorpio': 'Fixed', 'Sagittarius': 'Mutable',
    'Capricorn': 'Cardinal', 'Aquarius': 'Fixed', 'Pisces': 'Mutable',
}

# Dictionary definitions for planet dignity
exaltation = {
    'Sun': 'Aries', 'Moon': 'Taurus', 'Mercury': 'Virgo', 'Venus': 'Pisces',
    'Mars': 'Capricorn', 'Jupiter': 'Cancer', 'Saturn': 'Libra'
}
detriment = {
    'Sun': 'Libra', 'Moon': 'Scorpio', 'Mercury': 'Pisces', 'Venus': 'Virgo',
    'Mars': 'Cancer', 'Jupiter': 'Capricorn', 'Saturn': 'Aries'
}
fall = {
    'Sun': 'Libra', 'Moon': 'Scorpio', 'Mercury': 'Pisces', 'Venus': 'Virgo',
    'Mars': 'Cancer', 'Jupiter': 'Capricorn', 'Saturn': 'Aries'
}

bold = "\033[1m"
nobold = "\033[0m"
newline_end = "\n"  # Changed to <br> for HTML output
newline_begin = "\n"  # Changed to <p> for HTML output

############### Functions ###############

# Assesses the score in terms of ease (100) or difficulty (0) of aspects based on magnitude of stars
def calculate_aspect_score(aspect, magnitude):
    if aspect in MAJOR_ASPECTS:
        base_score = MAJOR_ASPECTS[aspect]['Score']
    elif aspect in MINOR_ASPECTS:
        base_score = MINOR_ASPECTS[aspect]['Score']
    else:
        return None  # Aspect not found

    # Adjust score based on magnitude
    adjustment_factor = 1 + (10 - float(magnitude)) / 10
    adjusted_score = base_score * adjustment_factor

    # Normalize to 0-100 scale
    final_score = min(max(0, adjusted_score), 100)

    return final_score

def get_davison_data(names):
    if not os.path.exists(saved_events_file):
        print(f"No file named {saved_events_file} found.")
        return False
    try:
        with open(saved_events_file, 'r') as file:
            data_dict = json.load(file)
    except json.JSONDecodeError:
        print(f"Error reading JSON data from {saved_events_file}.")
        return False

    datetimes = []
    longitudes = []
    latitudes = []
    
    # Collect the data for each name in the list
    names = names.split(',')    
    for name in names:
        name = name.strip()
        if name in data_dict:
            datetime_str = data_dict[name]['datetime']
            timezone_str = data_dict[name]['timezone']
            timezone = pytz.timezone(timezone_str)
            dt = datetime.strptime(datetime_str, '%Y-%m-%dT%H:%M:%S')
            dt_with_tz = timezone.localize(dt)
            datetimes.append(dt_with_tz)
            longitudes.append(data_dict[name]['longitude'])
            latitudes.append(data_dict[name]['latitude'])
    
    # Calculate the average datetime
    if datetimes:
        # Convert all datetimes to UTC for averaging
        total_seconds = sum((dt.astimezone(pytz.utc) - datetime(1970, 1, 1, tzinfo=pytz.utc)).total_seconds() for dt in datetimes)
        avg_seconds = total_seconds / len(datetimes)
        avg_datetime_utc = datetime(1970, 1, 1, tzinfo=pytz.utc) + timedelta(seconds=avg_seconds)
        # avg_datetime_str = avg_datetime_utc.strftime('%Y-%m-%d %H:%M:%S %Z')
    else:
        avg_datetime_str = 'No datetimes to average'
    
    # Calculate the average longitude and latitude
    if longitudes:
        avg_longitude = sum(longitudes) / len(longitudes)
    else:
        avg_longitude = 'No longitudes to average'
    
    if latitudes:
        avg_latitude = sum(latitudes) / len(latitudes)
    else:
        avg_latitude = 'No latitudes to average'
    
    return avg_datetime_utc, avg_longitude, avg_latitude

def assess_planet_strength(planet_signs):
    strength_status = {}
    for planet, sign in planet_signs.items():
        if planet in exaltation and sign == exaltation[planet]:
            strength_status[planet] = 'Exalted (Strong)'
        elif planet in detriment and sign == detriment[planet]:
            strength_status[planet] = 'In Detriment (Weak)'
        elif planet in fall and sign == fall[planet]:
            strength_status[planet] = 'In Fall (Very Weak)'
        else:
            strength_status[planet] = ''
    
    return strength_status

# Function to check elevation based on house
def is_planet_elevated(planet_positions):
    elevated_status = {}
    for planet, house in planet_positions.items():
        if planet not in ['Ascendant', 'Midheaven']:
            if house == 10:
                elevated_status[planet] = 'Angular, Elevated'
            elif house in [1, 4, 7]:
                elevated_status[planet] = 'Angular'
            else:
                elevated_status[planet] = ''
        else:
            elevated_status[planet] = ''
    return elevated_status

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
    
    return utc_datetime

def get_coordinates(location_name:str):
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
    - tuple: A tuple containing the latitude and longitude of the specified location.

    Note:
    - The accuracy of the coordinates returned depends on the specificity of the location name provided.
    - Ensure compliance with Nominatim's usage policy when using this function.
    """
    
    location_details = load_location('locations.json', location_name)
    if location_details:
        return location_details.latutude, location_details.longitude 
    else:
        # Initialize Nominatim API
        try:
            geolocator = Nominatim(user_agent="AstroScript")
        except Exception as e:
            print(f"Error initializing geolocator: {e}")
            return None, None

        # Get location
        try:
            location = geolocator.geocode(location_name)
        except Exception as e:
            print(f"Error getting location, check internet connection: {e}")
            return None, None
        save_location(saved_locations_file, location_name, location.latitude, location.longitude)

        return location.latitude, location.longitude

def save_location(filename, location_name, latitude, longitude):
    """
    Save a location with its latitude and longitude to a JSON file.
    
    Parameters:
    - filename (str): The name of the file where the data will be saved.
    - location_name (str): The name of the location.
    - latitude (float): The latitude of the location.
    - longitude (float): The longitude of the location.
    """
    # Check if the file exists and read its content if it does
    if os.path.exists(filename):
        with open(filename, 'r') as file:
            try:
                data = json.load(file)
            except json.JSONDecodeError:
                # If the file is empty or corrupted, start with an empty dictionary
                data = {}
    else:
        data = {}

    # Add or update the location in the data
    data[location_name] = {
        'latitude': latitude,
        'longitude': longitude
    }

    # Write the updated data back to the file
    with open(filename, 'w') as file:
        json.dump(data, file, indent=4)

def load_location(filename, location_name):
    """
    Load and return the details of a specified location from a JSON file.
    
    Parameters:
    - filename (str): The name of the JSON file to read from.
    - location_name (str): The name of the location to retrieve details for.
    
    Returns:
    - dict or None: The dictionary containing the latitude and longitude of the location if found, 
                     None otherwise.
    """
    try:
        with open(filename, 'r') as file:
            data = json.load(file)
            
        # Check if the location exists in the data and return its details
        if location_name in data:
            return data[location_name]
        else:
            return None
    except (FileNotFoundError, json.JSONDecodeError):
        # If the file doesn't exist or there's an error reading it, return None
        return None

def calculate_house_positions(date, latitude, longitude, planets_positions, notime=False, h_sys='P'):
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
    # Validate input date has a time component (convention to use 00:00:00 for unknown time )
    if date.hour == 0 and date.minute == 0:
        print("Warning: Time is not set. Calculations may be less accurate.")

    jd = swe.julday(date.year, date.month, date.day, date.hour + date.minute / 60.0)
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
        planet_longitude = planet_info['longitude'] % 360
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
    - date (datetime): The date and time for the calculation.
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

    for star_name in fixed_stars.keys():
        try:
            star_long = get_fixed_star_position(star_name, jd) % 360
            # star_house = next((i + 1 for i, cusp in enumerate(houses) if star_long < cusp), 12)

            # Assign star to house
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
                planet_long = data['longitude']
                for aspect_name, aspect_details in aspect_types.items():
                    aspect_angle, aspect_score, aspect_comment = aspect_details.values()
                    valid_aspect, angle_off = check_aspect(planet_long, star_long, aspect_angle, orb)
                    if valid_aspect:
                        aspects.append((planet, star_name, aspect_name, angle_off, house_num, aspect_score, aspect_comment))
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
    filename = './ephe/fixed_stars_all.csv' if all_stars else './ephe/astrologically_known_fixed_stars.csv'
    
    try:
        with open(filename, mode='r', newline='') as file:
            reader = csv.DictReader(file)
            fixed_stars = {row['Name']: row['Magnitude'] for row in reader}
    except FileNotFoundError:
        raise FileNotFoundError(f"The file '{filename}' was not found.")
    except IOError as e:
        raise IOError(f"An error occurred while reading from '{filename}': {e}")
    
    return fixed_stars

def calculate_aspect_duration(planet_positions, planet1, planet2, degrees_to_travel):
    """
    Calculate the exact duration for which two planets are within a specified number of degrees of each other.
    
    Parameters:
    - planet_positions (dict): Dictionary with each celestial body as keys, containing their
      ecliptic longitude, zodiac sign, retrograde status, and speed.
    - planet1 (str): The first planet involved in the transit.
    - planet2 (str): The second planet involved in the transit.
    - degrees_to_travel (float): The number of degrees representing the orb of the aspect.
    
    Returns:
    - str: Duration of the aspect in days, hours, and minutes.
    """
    # Extract the speeds and consider retrograde status
    speed1 = abs(planet_positions[planet1]['speed'])
    speed2 = abs(planet_positions[planet2]['speed'])

    # Determine relative speed based on their retrograde status and absolute speed
    if planet_positions[planet1]['retrograde'] == planet_positions[planet2]['retrograde']:
        relative_speed = abs(speed1 - speed2)
    else:
        relative_speed = speed1 + speed2

    # Calculate the duration based on the relative speed
    days = degrees_to_travel / relative_speed

    # Return formatted duration
    return f"{int(days)} days, {int((days % 1) * 24)} hours, {int(((days % 1) * 24 % 1) * 60)} minutes"

# Example usage assuming planet_positions dictionary is populated accordingly
example_planet_positions = {
    'Mars': {'longitude': 120, 'zodiac_sign': 'Leo', 'retrograde': '', 'speed': 0.8},
    'Venus': {'longitude': 125, 'zodiac_sign': 'Leo', 'retrograde': '', 'speed': 1.1}
}

# Calculate duration of a transit with a 3-degree separation
# aspect_duration = calculate_aspect_duration(example_planet_positions, 'Mars', 'Venus', 3)
# print(aspect_duration)  # Outputs the calculated duration


def calculate_planet_positions(date, latitude, longitude, h_sys='P'):
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
    jd = swe.julday(date.year, date.month, date.day, date.hour + date.minute / 60.0 + date.second / 3600.0)
    positions = {}
    PLANETS.pop('South Node', None)  # None is the default value if the key doesn't exist

    for planet, id in PLANETS.items():
        pos, ret = swe.calc_ut(jd, id)
        positions[planet] = {
            'longitude': pos[0],
            'zodiac_sign': longitude_to_zodiac(pos[0]).split()[0],
            'retrograde': 'R' if pos[3] < 0 else ''
        }
        if planet == "North Node":
            # Calculate the South Node
            south_node_longitude = (pos[0] + 180) % 360
            positions["South Node"] = {
                'longitude': south_node_longitude,
                'zodiac_sign': longitude_to_zodiac(south_node_longitude).split()[0],
                'retrograde': ''  # South Node does not have retrograde motion
            }

    # Calculate Ascendant and Midheaven
    asc_mc = swe.houses(jd, latitude, longitude, h_sys.encode('utf-8'))[1]
    positions['Ascendant'] = {'longitude': asc_mc[0], 'zodiac_sign': longitude_to_zodiac(asc_mc[0]).split()[0], 'retrograde': ''}
    positions['Midheaven'] = {'longitude': asc_mc[1], 'zodiac_sign': longitude_to_zodiac(asc_mc[1]).split()[0], 'retrograde': ''}

    # Fix south node
    PLANETS.update({"South Node": None})  # Add South Node to the list of planets
    positions["South Node"] = {
        'longitude': (positions["North Node"]['longitude'] + 180) % 360,
        'zodiac_sign': longitude_to_zodiac((positions["North Node"]['longitude'] + 180) % 360).split()[0],
        'retrograde': ''
    }

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

    return f"{degrees}°{minutes}'{seconds}\""  

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

            for aspect_name, aspect_values in aspect_types.items():
                aspect_angle, aspect_score, aspect_comment = aspect_values.values()
                
                if abs(angle_diff - aspect_angle) <= orb:
                    # Check if the aspect is imprecise based on the movement per day of the planets involved
                    is_imprecise = any(
                        planet in OFF_BY and OFF_BY[planet] > angle_diff
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
                        'is_imprecise': is_imprecise,
                        'aspect_score': aspect_score,
                        'aspect_comment': aspect_comment
                    }
    return aspects_found

def calculate_transits(natal_positions, transit_positions, orb, aspect_types):
    """
    Calculate astrological aspects between natal and transit celestial bodies based on their positions,
    excluding predefined pairs such as Sun-Ascendant, and assuming minor aspects
    are included in aspect_types if necessary.

    Parameters:
    - natal_positions: A dictionary with natal celestial bodies as keys, each mapped to 
      a dictionary containing 'longitude' and 'retrograde' status.
    - transit_positions: A dictionary with transit celestial bodies as keys, each mapped to 
      a dictionary containing 'longitude' and 'retrograde' status.
    - orb: The maximum orb (in degrees) to consider an aspect valid.
    - aspect_types: A dictionary of aspect names and their exact angles, possibly 
      including minor aspects.

    Returns:
    - A list of tuples, each representing an aspect found between a natal and a transit celestial body.
      Each tuple includes the names of the bodies, the aspect name, and the exact angle.
    """
    aspects_found = {}
    natal_planet_names = list(natal_positions.keys())
    transit_planet_names = list(transit_positions.keys())

    for i, planet1 in enumerate(natal_planet_names):
        for planet2 in transit_planet_names[i+1:]:
            long1 = natal_positions[planet1]['longitude']
            long2 = transit_positions[planet2]['longitude']
            angle_diff = abs(long1 - long2) % 360
            angle_diff = min(angle_diff, 360 - angle_diff)  # Normalize to <= 180 degrees

            for aspect_name, aspect_values in aspect_types.items():
                aspect_angle, aspect_score, aspect_comment = aspect_values.values()
                
                if abs(angle_diff - aspect_angle) <= orb:
                    # Check if the aspect is imprecise based on the movement per day of the planets involved
                    is_imprecise = any(
                        planet in OFF_BY and OFF_BY[planet] > angle_diff
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
                        'is_imprecise': is_imprecise,
                        'aspect_score': aspect_score,
                        'aspect_comment': aspect_comment
                    }
    return aspects_found


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
        return "Waning Crescent", illumination

def print_planet_positions(planet_positions, degree_in_minutes=False, notime=False, house_positions=None, orb=1, output="text"):
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
    
    sign_counts = {sign: {'count': 0, 'planets':[]} for sign in ZODIAC_ELEMENTS.keys()}
    modality_counts = {modality: {'count': 0, 'planets':[]} for modality in ZODIAC_MODALITIES.keys()}
    element_counts = {'Fire': 0, 'Earth': 0, 'Air': 0, 'Water': 0}
    planet_house_counts = {house: 0 for house in range(1, 13)}

    zodiac_table_data = []

    # Define headers based on whether house positions should be included
    headers = ["Planet", "Zodiac", "Position", "R"]
    if house_positions:
        headers.append("House")
    if not notime:
        headers.append("Dignity")
    if notime:
        headers.insert(3, "Off by")

    planet_signs = {}
    
    for planet, info in planet_positions.items():
        if notime and (planet in ALWAYS_EXCLUDE_IF_NO_TIME):
            continue
        longitude = info['longitude']
        degrees_within_sign = longitude % 30
        position = coord_in_minutes(degrees_within_sign) if degree_in_minutes else f"{degrees_within_sign:.2f}°"
        retrograde = info['retrograde']
        zodiac = info['zodiac_sign']
        retrograde_status = "R" if retrograde else ""

        planet_signs[planet] = zodiac
        if not notime:  # assuming that we have the house positions if not notime
            house_num = house_positions.get(planet, {}).get('house', 'Unknown')
            planet_positions[planet] = house_num
            planet_house_counts[house_num] += 1
            strength_check = assess_planet_strength(planet_signs)
            elevation_check = is_planet_elevated(planet_positions)

        if notime and planet in OFF_BY.keys() and OFF_BY[planet] > orb:
            off_by = f"±{OFF_BY[planet]}°"
            row = [planet, zodiac, position, off_by, retrograde_status]
        else:
            if notime:
                row = [planet, zodiac, position, "", retrograde_status]
            else:
                row = [planet, zodiac, position, retrograde_status, (elevation_check[planet] + " " + strength_check[planet]) ]

        if house_positions and not notime:
            house_num = house_positions.get(planet, {}).get('house', 'Unknown')
            row.insert(4, house_num)
            pass
        zodiac_table_data.append(row)

        # Count zodiac signs, elements and modalities
        sign_counts[zodiac]['count'] += 1
        sign_counts[zodiac]['planets'].append(planet)
        modality = ZODIAC_SIGN_TO_MODALITY[zodiac]
        modality_counts[modality]['count'] += 1
        modality_counts[modality]['planets'].append(planet)
        element_counts[ZODIAC_ELEMENTS[zodiac]] += 1

    to_return = ''
    if output=='text' or 'return_text':
        table = tabulate(zodiac_table_data, headers=headers, tablefmt="simple", floatfmt=".2f")
    if output=='html':
        table = tabulate(zodiac_table_data, headers=headers, tablefmt="html", floatfmt=".2f")
    if output == 'text' or output =='html':
        print(table)
    to_return += table

    sign_count_table_data = list()
    element_count_table_data = list()
    modality_count_table_data = list()
    house_count_string = '\nHouse count  '

    ## House counts
    sorted_planet_house_counts = sorted(planet_house_counts.items(), key=lambda item: item[1], reverse=True)
    
    for house, count in sorted_planet_house_counts:
        if count > 0:
            if output == 'text':
                house_count_string += f"{house}: {Fore.GREEN}{count}{Style.RESET_ALL}, "
            else:
                house_count_string += f"{house}: {count}, "
    house_count_string = house_count_string[:-2] # Remove the last comma and space
    to_return += "\n" + house_count_string
    if output == 'text' or output == 'html':
        print(house_count_string)

    # Print zodiac sign, element and modality counts
    if output == 'text':
        print("\n")
    for sign, data in sign_counts.items():
        if data['count'] > 0:
            row = [sign, data['count'], ', '.join(data['planets'])]
            sign_count_table_data.append(row)

    table = tabulate(sign_count_table_data, headers=["Sign","Nr","Planets in Sign".title()], tablefmt="simple", floatfmt=".2f")
    to_return += "\n\n" + table
    if output == 'text':
        print(table + "\n")

    for element, count in element_counts.items():
        if count > 0:
            row = [element, count]
            element_count_table_data.append(row)

    table = tabulate(element_count_table_data, headers=["Element","Nr"], tablefmt="simple", floatfmt=".2f")
    to_return += "\n\n" + table
    if output == 'text':
        print(table + "\n")

    for modality, info in modality_counts.items():
        row = [modality, info['count'], ', '.join(info['planets'])]
        modality_count_table_data.append(row)
    table = tabulate(modality_count_table_data, headers=["Modality","Nr", "Planets"], tablefmt="simple")
    to_return += "\n\n" + table
    if output == 'text':
        print(table + "\n")

    return to_return

def print_aspects(aspects, imprecise_aspects="off", minor_aspects=True, degree_in_minutes=False, house_positions=None, orb=1, transits=False, notime=False, output="text"):
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

    planetary_aspects_table_data = []
    if transits:
        headers = ["Natal Planet", "Aspect", "Transit Planet", "Degree", "Off by"]
    else:
        headers = ["Planet", "Aspect", "Planet", "Degree", "Off by"]
    to_return = ""

    if output=='text':
        print(f"{bold}Planetary Aspects ({orb}° orb){nobold}", end="")
        print(f"{bold} and minor aspects{nobold}" if minor_aspects else "", end="")
        if notime:
            print(f"{bold} with imprecise aspects set to {imprecise_aspects}{nobold}", end="")
        print(":\n")
    else:
        to_return = f"\nPlanetary Aspects ({orb}° orb)"
        if minor_aspects:
            to_return += " and minor aspects" 
        if notime:
            to_return += f" with imprecise aspects set to {imprecise_aspects}"

    aspect_type_counts = {}
    hard_count = 0 
    soft_count = 0
    hard_count_score = 0
    soft_count_score = 0

    all_aspects = {**SOFT_ASPECTS, **HARD_ASPECTS}

    for planets, aspect_details in aspects.items():
        if planets[0] in ALWAYS_EXCLUDE_IF_NO_TIME or planets[1] in ALWAYS_EXCLUDE_IF_NO_TIME:
            continue
        if degree_in_minutes:
            angle_with_degree = f"{aspect_details['angle_diff_in_minutes']}".strip("-")
        else:
            angle_with_degree = f"{aspect_details['angle_diff']:.2f}°".strip("-")
        if imprecise_aspects == "off" and (aspect_details['is_imprecise'] or planets[0] in ALWAYS_EXCLUDE_IF_NO_TIME or planets[1] in ALWAYS_EXCLUDE_IF_NO_TIME):
            continue
        else:
            row = [planets[0], aspect_details['aspect_name'], planets[1], angle_with_degree]

        if imprecise_aspects == "warn" and ((planets[0] in OFF_BY.keys() or planets[1] in OFF_BY.keys())) and notime:
            if float(OFF_BY[planets[0]]) > orb or float(OFF_BY[planets[1]]) > orb:
                off_by = str(OFF_BY.get(planets[0], 0) + OFF_BY.get(planets[1], 0))
                row.append(" ± " + off_by)
        planetary_aspects_table_data.append(row)
        # Add or update the count of the aspect type
        aspect_name = aspect_details['aspect_name']
        if aspect_name in aspect_type_counts:
            aspect_type_counts[aspect_name] += 1
        else:
            aspect_type_counts[aspect_name] = 1
        if aspect_name in HARD_ASPECTS:
            hard_count += 1
            hard_count_score += aspect_details['aspect_score']
        elif aspect_name in SOFT_ASPECTS:
            soft_count += 1
            soft_count_score += aspect_details['aspect_score']

    table = tabulate(planetary_aspects_table_data, headers=headers, tablefmt="simple", floatfmt=".2f")
    to_return += "\n" + table

    if output == 'text':
        print(table)

    # Convert aspect type dictionary to a list of tuples
    aspect_data = list(aspect_type_counts.items())
    aspect_data.sort(key=lambda x: x[1], reverse=True)
    
    # Convert aspect_data to a list of lists
    aspect_data = [[aspect_data[i][0], aspect_data[i][1], list(all_aspects[aspect[0]].values())[2]] for i, aspect in enumerate(aspect_data)]

    headers = ["Aspect Type", "Count", "Meaning"]
    table = tabulate(aspect_data, headers=headers, tablefmt="simple")
    if hard_count+soft_count > 0:
        aspect_count_text = f"\nHard Aspects: {hard_count}, Soft Aspects: {soft_count}, Score: {(hard_count_score + soft_count_score)/(hard_count+soft_count):.1f}".rstrip('0').rstrip('.')+'\n'
    else:
        aspect_count_text = "\nNo aspects found.\n"
    to_return += "\n" + table + aspect_count_text

    # Print counts of each aspect type
    if output == 'text':
        print('\n'+table + '\n' + aspect_count_text)

    if output == 'text':
        if not house_positions:
            print("* No time of day specified. Houses cannot be calculated. ")
            print("  Aspects to the Ascendant and Midheaven are not available.")
            print("  The positions of the Sun, Moon, Mercury, Venus, and Mars are uncertain.\n")
            print("\n  Please specify the time of birth for a complete chart.\n")
    else:
        if not house_positions:
            to_return += "\n* No time of day specified. Houses cannot be calculated. "
            to_return += "  Aspects to the Ascendant and Midheaven are not available."
            to_return += "  The positions of the Sun, Moon, Mercury, Venus, and Mars are uncertain.\n"
            to_return += "\n  Please specify the time of birth for a complete chart.\n"

    return to_return

def print_fixed_star_aspects(aspects, orb=1, minor_aspects=False, imprecise_aspects="off", notime=True, degree_in_minutes=False, house_positions=None, stars=None, output="text"):
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
    to_return = ""

    if output == 'text':
        print(f"\n{bold}Fixed Star Aspects ({orb}° orb){nobold}", end="")
        print(f"{bold} including Minor Aspects{nobold}" if minor_aspects else "", end="")
        if notime:
            print(f"{bold} with Imprecise Aspects set to {imprecise_aspects}{nobold}", end="")
        print()
    else:
        to_return += f"Fixed Star Aspects ({orb}° orb)"
        if minor_aspects:
            to_return += " including Minor Aspects"
        if notime:
            to_return += f" with Imprecise Aspects set to {imprecise_aspects}\n\n"

    star_aspects_table_data = []

    aspect_type_counts = {}
    hard_count = 0 
    soft_count = 0
    hard_count_score = 0
    soft_count_score = 0
    all_aspects = {**SOFT_ASPECTS, **HARD_ASPECTS}
    star_house_counts = {house: 0 for house in range(1, 13)}


    for aspect in aspects:
        planet, star_name, aspect_name, angle, house, aspect_score, aspect_comment = aspect
        if planet in ALWAYS_EXCLUDE_IF_NO_TIME:
            continue
        if degree_in_minutes:
            angle = coord_in_minutes(angle)
        else:
            angle = f"{angle:.2f}°".strip("-")
        row = [planet, aspect_name, star_name, angle]

        if house_positions and not notime:
            row.append(house)
            star_house_counts[house] += 1
        elif planet in OFF_BY.keys() and OFF_BY[planet] > orb:
            row.append(f" ±{OFF_BY[planet]}°")
        star_aspects_table_data.append(row)
        # Add or update the count of the aspect type
        if aspect_name in aspect_type_counts:
            aspect_type_counts[aspect_name] += 1
        else:
            aspect_type_counts[aspect_name] = 1
        if aspect_name in HARD_ASPECTS:
            hard_count += 1
            hard_count_score +=  calculate_aspect_score(aspect_name, stars[star_name])
        elif aspect_name in SOFT_ASPECTS:
            soft_count += 1
            # soft_count_score += aspect_score # it was like this before magnitude was taken into account (keeping if adding switch)
            soft_count_score += calculate_aspect_score(aspect_name, stars[star_name])

    headers = ["Planet", "Aspect", "Star", "Margin"]

    if house_positions and not notime:
        headers.append("Star in House")
    if planet in OFF_BY.keys() and OFF_BY[planet] > orb and notime:
        headers.append("Off by")

    table = tabulate(star_aspects_table_data, headers=headers, tablefmt="simple", floatfmt=".2f")
    to_return += "\n\n" + table
    if output == 'text':
        print(table + "\n")

    ## House counts
    house_count_string = ''
    sorted_star_house_counts = sorted(star_house_counts.items(), key=lambda item: item[1], reverse=True)

    for house, count in sorted_star_house_counts:
        if count > 0:
            if output == 'text':
                house_count_string += f"{house}: {Fore.GREEN}{count}{Style.RESET_ALL}, "
            else:
                house_count_string += f"{house}: {count}, "
    house_count_string = house_count_string[:-2]+"\n" # Remove the last comma and space
    to_return += "\n" + house_count_string
    if output == 'text':
        print(house_count_string)

    aspect_data = list(aspect_type_counts.items())
    aspect_data.sort(key=lambda x: x[1], reverse=True)
    aspect_data = [[aspect_data[i][0], aspect_data[i][1], list(all_aspects[aspect[0]].values())[2]] for i, aspect in enumerate(aspect_data)]
    headers = ["Aspect Type", "Count", "Meaning"]
    table = tabulate(aspect_data, headers=headers, tablefmt="simple")
    aspect_count_text = f"\nHard Aspects: {hard_count}, Soft Aspects: {soft_count}, Score: {(hard_count_score + soft_count_score)/(hard_count+soft_count):.1f}".rstrip('0').rstrip('.')+'\n' 
    to_return += "\n" + table + '\n' + aspect_count_text

    # Update scoring based on the magnitude and the new function for scoring.

    #Print counts of each aspect type
    if output == 'text':
        print(table + '\n' + aspect_count_text)

    return to_return

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

def called_by_gui(name, date, location, latitude, longitude, timezone, davison, place, imprecise_aspects,
                  minor_aspects, orb, degree_in_minutes, node, all_stars, house_system, house_cusps, hide_planetary_positions,
                  hide_planetary_aspects, hide_fixed_star_aspects, transits):
    arguments = {
        "Name": name,
        "Date": date,
        "Location": location,
        "Latitude": latitude,
        "Longitude": longitude,
        "Timezone": timezone,
        "Davison": davison,
        "Place": place,
        "Imprecise Aspects": imprecise_aspects,
        "Minor Aspects": minor_aspects,
        "Orb": orb,
        "Degree in Minutes": degree_in_minutes,
        "Node": node,
        "All Stars": all_stars,
        "House System": house_system,
        "House Cusps": house_cusps,
        "Hide Planetary Positions": hide_planetary_positions,
        "Hide Planetary Aspects": hide_planetary_aspects,
        "Hide Fixed Star Aspects": hide_fixed_star_aspects,
        "Transits": transits,
        "Output": "return text"
    }

    print(arguments) 
    text = main(arguments)
    return text

def argparser():
    parser = argparse.ArgumentParser(description='''If no arguments are passed, values entered in the script will be used.
If a name is passed, the script will look up the record for that name in the JSON file and overwrite other passed values,
provided there are such values stored in the file (only the first 6 types are stored). 
If no record is found, default values will be used.''')

    # Add arguments
    parser.add_argument('--name', help='Name to look up the record for.', required=False)
    parser.add_argument('--date', help='Date of the event (YYYY-MM-DD HH:MM local time).', required=False)
    parser.add_argument('--location', type=str, help='Name of location for lookup of coordinates, e.g. "Sahlgrenska, Göteborg, Sweden".', required=False)
    parser.add_argument('--latitude', type=float, help='Latitude of the location in degrees, e.g. 57.6828.', required=False)
    parser.add_argument('--longitude', type=float, help='Longitude of the location in degrees, e.g. 11.96.', required=False)
    parser.add_argument('--timezone', help='Timezone of the location (e.g. "Europe/Stockholm").', required=False)
    parser.add_argument('--davison', help='Create a Davison chart out of many stored events (e.g. "John, Jane").', required=False)
    parser.add_argument('--place', help='Name of location without lookup of coordinates.', required=False)
    parser.add_argument('--imprecise_aspects', choices=['off', 'warn'], help='Whether to not show imprecise aspects or just warn.', required=False)
    parser.add_argument('--minor_aspects', choices=['true','false'], help='Whether to show minor aspects.', required=False)
    parser.add_argument('--orb', type=float, help='Orb size in degrees.', required=False)
    parser.add_argument('--degree_in_minutes',choices=['true','false'], help='Show degrees in arch minutes and seconds', required=False)
    parser.add_argument('--node',choices=['mean','true'], help='Whether to use the moon mean node or true node', required=False)
    parser.add_argument('--all_stars', choices=['true','false'], help='Show aspects for all fixed stars.', required=False)
    parser.add_argument('--house_system', choices=list(HOUSE_SYSTEMS.keys()), help='House system to use (Placidus, Koch etc).', required=False)
    parser.add_argument('--house_cusps', choices=['true','false'], help='Whether to show house cusps or not', required=False)
    parser.add_argument('--hide_planetary_positions', choices=['true','false'], help='Output: hide what signs and houses (if time specified) planets are in.', required=False)
    parser.add_argument('--hide_planetary_aspects', choices=['true','false'], help='Output: hide aspects planets are in.', required=False)
    parser.add_argument('--hide_fixed_star_aspects', choices=['true','false'], help='Output: hide aspects planets are in to fixed stars.', required=False)
    parser.add_argument('--transits', help="Date of the transit event ('YYYY-MM-DD HH:MM' local time, 'now' for current time)", required=False)
    parser.add_argument('--output_type', choices=['text','return_text', 'html'], help='Output: Print to stdout, return text or return html.', required=False)

    args = parser.parse_args()

    arguments = {
    "Name": args.name,
    "Date": args.date,
    "Location": args.location,
    "Latitude": args.latitude,
    "Longitude": args.longitude,
    "Timezone": args.timezone,
    "Davison": args.davison,
    "Place": args.place,
    "Imprecise Aspects": args.imprecise_aspects,
    "Minor Aspects": args.minor_aspects,
    "Orb": args.orb,
    "Degree in Minutes": args.degree_in_minutes,
    "Node": args.node,
    "All Stars": args.all_stars,
    "House System": args.house_system,
    "House Cusps": args.house_cusps,
    "Hide Planetary Positions": args.hide_planetary_positions,
    "Hide Planetary Aspects": args.hide_planetary_aspects,
    "Hide Fixed Star Aspects": args.hide_fixed_star_aspects,
    "Transits": args.transits,
    "Output": args.output_type}

    return arguments

def main(gui_arguments=None):    
    if gui_arguments:
        args = gui_arguments
    else:
        args = argparser()

    local_datetime = datetime.now()  # Default date now

    # Check if name was provided as argument
    name = args["Name"] if args["Name"] else None
    to_return = ""

    #################### Load event ####################
    exists = load_event(FILENAME, name) if name else None
    if exists:
        if not args["Date"]:
            local_datetime = datetime.fromisoformat(exists[0]['datetime'])
        if not args["Latitude"]:
            latitude = exists[0]['latitude']
        if not args["Longitude"]:
            longitude = exists[0]['longitude']
        if not args["Timezone"]:
            local_timezone = pytz.timezone(exists[0]['timezone'])
        if not args["Place"]:
            place = exists[0]['location']
    else:
        try:
            if args["Date"]:
                local_datetime = datetime.strptime(args["Date"], "%Y-%m-%d %H:%M")
        except ValueError:
            print("Invalid date format. Please use YYYY-MM-DD HH:MM.")
            local_datetime = None
            return "Invalid date format. Please use YYYY-MM-DD HH:MM."
    if args["Date"]:
        local_datetime = datetime.strptime(args["Date"], "%Y-%m-%d %H:%M")

    ######### Default settings if no arguments are passed #########
    def_tz = pytz.timezone('Europe/Stockholm')  # Default timezone
    def_place_name = "Sahlgrenska"  # Default place
    def_lat = 57.6828  # Default latitude
    def_long = 11.9624  # Default longitude
    def_imprecise_aspects = "warn"  # Default imprecise aspects ["off", "warn"]
    def_minor_aspects = False  # Default minor aspects
    def_orb = 1  # Default orb size
    def_degree_in_minutes = False  # Default degree in minutes
    def_node = "true"  # Default mean node (true node is more accurate)
    def_all_stars = False  # Default all stars
    def_house_system = HOUSE_SYSTEMS["Placidus"]  # Default house system
    def_house_cusps = False  # Default do not show house cusps
    def_output_type = "text"  # Default output type

    # Default Output settings
    hide_planetary_positions = False  # Default hide planetary positions
    hide_planetary_aspects = False  # Default hide planetary aspects
    hide_fixed_star_aspects = False  # Default hide fixed star aspects
    show_transits = False

    if args["Location"]: 
        place = args["Location"]
        latitude, longitude = get_coordinates(args["Location"])
        if latitude is None or longitude is None:
            print("Location not found. Please check the spelling and internet connection.")
            return "Location not found. Please check the spelling and internet connection."
    elif args["Place"]:
        place = args["Place"]
    elif not exists:
        place = def_place_name

    if not args["Location"]:
        latitude = args["Latitude"] if args["Latitude"] is not None else def_lat
        longitude = args["Longitude"] if args["Longitude"] is not None else def_long
    local_timezone = pytz.timezone(args["Timezone"]) if args["Timezone"] else def_tz
    # If "off", the script will not show such aspects, if "warn" print a warning for uncertain aspects
    imprecise_aspects = args["Imprecise Aspects"] if args["Imprecise Aspects"] else def_imprecise_aspects
    # If True, the script will include minor aspects
    minor_aspects = True if args["Minor Aspects"] and args["Minor Aspects"].lower() in ["true", "yes", "1"] else def_minor_aspects
    orb = float(args["Orb"]) if args["Orb"] else def_orb
    # If True, the script will show the positions in degrees and minutes
    degree_in_minutes = True if args["Degree in Minutes"] and args["Degree in Minutes"].lower() in ["true", "yes", "1"] else def_degree_in_minutes
    node = "mean" if args["Node"] and args["Node"].lower() in ["mean"] else def_node
    if node == "mean":
        PLANETS["North Node"] = swe.MEAN_NODE
    if node == "true":
        PLANETS["North Node"] = swe.TRUE_NODE
    # If True, the script will include all roughly 700 fixed stars
    all_stars = True if args["All Stars"] and args["All Stars"].lower() in ["true", "yes", "1"] else def_all_stars
    h_sys = HOUSE_SYSTEMS[args["House System"]] if args["House System"] else def_house_system
    if args["House System"] and args["House System"] not in HOUSE_SYSTEMS:
        print(f"Invalid house system. Available house systems are: {', '.join(HOUSE_SYSTEMS.keys())}")
        h_sys = HOUSE_SYSTEMS["Placidus"]  # Reverting to default house system
    show_house_cusps = True if args["House Cusps"] == 'true' else def_house_cusps
    
    output_type = args["Output"] if args["Output"] else def_output_type
    if output_type == 'html':
        print(f"<!DOCTYPE html>\n<html>\n<head>\n<title>AstroScript Chart</title>\n</head>\n<body>")
        newline_end = "\n<br>"
        newline_begin = "\n<p>"

    if args["Hide Planetary Positions"]:
        if args["Hide Planetary Positions"].lower() in ["true", "yes", "1"]: hide_planetary_positions = True 
    if args["Hide Planetary Aspects"]:
        if args["Hide Planetary Aspects"].lower() in ["true", "yes", "1"]: hide_planetary_aspects = True
    if args["Hide Fixed Star Aspects"]:
        if args["Hide Fixed Star Aspects"].lower() in ["true", "yes", "1"]: hide_fixed_star_aspects = True 

    if args["Davison"]:
        utc_datetime, longitude, latitude = get_davison_data(args["Davison"])
        place = "Davison chart"
        local_timezone = pytz.utc
        local_datetime = utc_datetime
    else:
        if place == "Davison chart":
            utc_datetime = local_datetime
        else:
            utc_datetime = convert_to_utc(local_datetime, local_timezone)

    if args["Transits"]:
        if args["Transits"] == "now":
            transits_local_datetime = datetime.now() # Defaulting to now
            # transits_local_timezone = pytz.timezone(args["Timezone"]) if args["Timezone"] else def_tz # Also add argument for transits timezone if different
            transits_utc_datetime = convert_to_utc(transits_local_datetime, local_timezone)
            show_transits = True
        else:
            try:
                transits_local_datetime = datetime.strptime(args["Transits"], "%Y-%m-%d %H:%M")
            except ValueError:
                print("Invalid transit date format. Please use YYYY-MM-DD HH:MM (00:00 for time if unknown).\nLeave blank for current time (UTC")
                return "Invalid transit date format. Please use YYYY-MM-DD HH:MM (00:00 for time if unknown).\nLeave blank for current time (UTC)"
            transits_utc_datetime = convert_to_utc(transits_local_datetime, local_timezone)
            show_transits = True 

    # Check if the time is set, or only the date, this is not compatible with people born at midnight (but can set second to 1)
    notime = (local_datetime.hour == 0 and local_datetime.minute == 0)

    # Save event if name given and not already given
    if name and not exists:
        new_data = {name: {"location": place,
                           "datetime": local_datetime.isoformat(),
                           'timezone': str(local_timezone),
                           "latitude": latitude,
                           "longitude": longitude}}
        save_event.update_json_file(saved_events_file,new_data)

    #################### Main Script ####################    
    # Initialize Colorama, calculations for strings
    init()
    house_system_name = next((name for name, code in HOUSE_SYSTEMS.items() if code == h_sys), None)
    planet_positions = calculate_planet_positions(utc_datetime, latitude, longitude)
    house_positions, house_cusps = calculate_house_positions(utc_datetime, latitude, longitude, planet_positions, notime, HOUSE_SYSTEMS[house_system_name])
    moon_phase_name1, illumination1 = moon_phase(utc_datetime)
    moon_phase_name2, illumination2 = moon_phase(utc_datetime + timedelta(days=1))
    if notime:
        illumination = f"{illumination1:.2f}-{illumination2:.2f}%"
    else:
        moon_phase_name, illumination = moon_phase(utc_datetime)
        illumination = f"{illumination:.2f}%"

    string_heading = f"AstroScript v.{__version__} Chart\n--------------------------"
    string_name = f"Name: {name}"
    string_place = f"Place: {place}"
    string_latitude_in_minutes = f"Latitude: {coord_in_minutes(latitude)}"
    string_longitude_in_minutes = f"Longitude: {coord_in_minutes(longitude)}"
    string_latitude = f"Latitude: {latitude}"
    string_longitude = f"Longitude: {longitude}"
    string_davison_noname = "Davison chart"
    string_davison = f"Davison chart of: {args['Davison']}"
    string_local_time = f"Local Time: {local_datetime} {local_timezone}"
    string_UTC_Time_imprecise = f"UTC Time: {utc_datetime} UTC (imprecise due to time of day missing)"
    string_UTC_Time = f"UTC Time: {utc_datetime} UTC"
    string_house_system_moon_nodes = f"House system: {house_system_name}, Moon nodes: {node}"
    string_house_cusps = f"House cusps: {house_cusps}"
    string_moon_phase_imprecise = f"Moon Phase: {moon_phase_name1} to {moon_phase_name2}\nMoon Illumination: {illumination}"
    string_moon_phase = f"Moon Phase: {moon_phase_name}{newline_end}Moon Illumination: {illumination}"
    string_transits = f"Transits for"

    if output_type == "text" or output_type == "html":
        print(f"\n{string_heading}")
        if exists or name:
            print(f"\n{string_name}")
        if place:
            print(f"{string_place}")
        if degree_in_minutes:
            print(f"{string_latitude_in_minutes}, {string_longitude_in_minutes}")
        else:
            print(f"{string_latitude}, {string_longitude}")
        
        if place == "Davison chart" and not args["Davison"]:
                print(f"\{string_davison_noname}")
        elif args["Davison"]:
            print(f"\n{string_davison}")

        if not args['Davison'] or place != "Davison chart":
            print(f"\n{string_local_time}")
        print(f"\n{string_UTC_Time_imprecise}") if notime else print(f"{string_UTC_Time}")
    else:
        to_return = f"{string_heading}"
        if exists or name:
            to_return += f"\n{string_name}"
        if place:
            to_return += f", {string_place}"
        if degree_in_minutes:
            to_return += f"\n{string_latitude_in_minutes}, {string_longitude_in_minutes}"
        else:
            to_return += f"\n{string_latitude}, {string_longitude}"
        if place == "Davison chart" and not args["Davison"]:
            to_return += f"\n{string_davison_noname}"
        if args["Davison"]:
            to_return += f"\n{string_davison}"

        to_return += f"\n{string_local_time}"
        if notime: to_return += f"\n{string_UTC_Time_imprecise}"
        else: to_return += f", {string_UTC_Time}"


    if output_type == "text or html":
        print(f"{string_house_system_moon_nodes}\n")
    else: to_return += f"\n{string_house_system_moon_nodes}\n"

    if minor_aspects:
        ASPECT_TYPES.update(MINOR_ASPECT_TYPES)
        MAJOR_ASPECTS.update(MINOR_ASPECTS)

    if show_house_cusps:
        if output_type == 'text':
            print(f"\n{string_house_cusps}\n")
        else:
            to_return += f"\{string_house_cusps}\n"

    aspects = calculate_aspects(planet_positions, orb, aspect_types=MAJOR_ASPECTS) # Major aspects has been updated to include minor if 
    fixstar_aspects = calculate_aspects_to_fixed_stars(utc_datetime, planet_positions, house_cusps, orb, MAJOR_ASPECTS, all_stars)

    if not hide_planetary_positions:
        to_return += "\n" + print_planet_positions(planet_positions, degree_in_minutes, notime, house_positions, orb, output_type)
    if not hide_planetary_aspects:
        to_return += "\n" + print_aspects(aspects, imprecise_aspects, minor_aspects, degree_in_minutes, house_positions, orb, False, notime, output_type) # False = these are not transits
    if not hide_fixed_star_aspects:
        to_return += "\n\n" + print_fixed_star_aspects(fixstar_aspects, orb, minor_aspects, imprecise_aspects, notime, degree_in_minutes, house_positions, read_fixed_stars(all_stars), output_type)
    
    if notime:
        if moon_phase_name1 != moon_phase_name2:
            if (output_type == "text"):
                print(f"{string_moon_phase_imprecise}")
            else:
                to_return += f"\n\n{string_moon_phase_imprecise}"
    else:
        if output_type == "text":
            print(f"{string_moon_phase}")
        else:
            to_return += f"\n\n{string_moon_phase_imprecise}"

    if show_transits:           
        planet_positions = calculate_planet_positions(utc_datetime, latitude, longitude)
        transits_planet_positions = calculate_planet_positions(transits_utc_datetime, latitude, longitude) # Also add argument for transits location if different

        transit_aspects = calculate_transits(planet_positions, transits_planet_positions, orb, aspect_types=MAJOR_ASPECTS)
        if output_type == "text":
            print(f"\n{bold}{string_transits} {transits_local_datetime}{nobold}")
        else:
            to_return += f"\n{string_transits} {transits_local_datetime}\n===================================" 
        to_return += "\n" + print_aspects(transit_aspects, imprecise_aspects, minor_aspects, degree_in_minutes, house_positions, orb, True, notime, output_type) # Transit True

    return to_return

if __name__ == "__main__":
    main()