import swisseph as swe
import datetime
import pytz
import json
import os

swe.set_ephe_path('./ephe/')

def convert_to_utc(local_datetime, local_timezone):
    # Make the datetime object timezone-aware
    local_datetime = local_timezone.localize(local_datetime)
    
    # Convert to UTC
    utc_datetime = local_datetime.astimezone(pytz.utc)
    
    return utc_datetime

def calculate_house_positions(date, latitude, longitude, planets_positions):
    """
    Calculate the house positions for a given date, time, latitude, and longitude.
    
    Parameters:
    - date: datetime object specifying the date and time for the calculation.
    - latitude: Latitude of the place for the chart.
    - longitude: Longitude of the place for the chart.
    - planets_positions: A dictionary containing planets and their ecliptic longitudes.
    
    Returns:
    - house_positions: A dictionary mapping each planet, including the Ascendant ('Ascendant')
      and Midheaven ('Midheaven'), to their house numbers.
    - house_cusps: A list of the zodiac positions of the beginnings of each house.
    """
    if date.hour == 0 and date.minute == 0 and date.second == 0:
        raise ValueError("Time must be specified for accurate house calculations.")

    jd = swe.julday(date.year, date.month, date.day, date.hour + date.minute / 60.0 + date.second / 3600)
    h_sys = 'P'
    houses, ascmc = swe.houses(jd, latitude, longitude, h_sys.encode('utf-8'))

    ascendant_long = ascmc[5]
    midheaven_long = ascmc[7]
   
    # Determine the house number for Midheaven
    midheaven_house = 10  # Default to 10th house
    for i, cusp in enumerate(houses[1:], start=1):
        if midheaven_long < cusp:
            midheaven_house = i
            break

    house_positions = {
        'Ascendant': {'longitude': ascendant_long, 'house': 1},
        'Midheaven': {'longitude': midheaven_long, 'house': midheaven_house}
    }

    for planet, planet_info in planets_positions.items():
        planet_longitude = planet_info['longitude']
        house_num = 1
        for i in range(1, len(houses)):
            if planet_longitude < houses[i]:
                break
            house_num = i + 1
        house_positions[planet] = {'longitude': planet_longitude, 'house': house_num}

    return house_positions, houses[:13]  # Return the house positions and the house cusps

def longitude_to_zodiac(longitude):
    """
    Convert ecliptic longitude to its zodiac sign and degree.

    Parameters:
    - longitude: The ecliptic longitude to convert.
    
    Returns:
    - A string representation of the zodiac sign and degree.
    """
    zodiac_signs = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']
    sign_index = int(longitude // 30)
    degree = int(longitude % 30)
    minutes = int((longitude % 1) * 60)
    seconds = int((((longitude % 1) * 60) % 1) * 60)
    return f"{zodiac_signs[sign_index]} {degree}°{minutes}'{seconds}''"


def is_planet_retrograde(planet, jd):
    """
    Determine if a planet is retrograde on a given Julian Day.

    Parameters:
    - planet: The planet's identifier for swisseph.
    - jd: Julian Day.
    
    Returns:
    - True if the planet is retrograde, False otherwise.
    """
    pos_before = swe.calc_ut(jd - (10 / 1440), planet)[0]
    pos_after = swe.calc_ut(jd + (10 / 1440), planet)[0]
    return pos_after[0] < pos_before[0]


def get_fixed_star_position(star_name, jd):
    """
    Get the longitudinal position of a fixed star on a given Julian Day.
    
    Parameters:
    - star_name: The name of the fixed star.
    - jd: Julian Day.

    Returns:
    - The longitude of the fixed star.
    """
    star_info = swe.fixstar(star_name, jd)
    return star_info[0][0]  # Returning the longitude part of the position

def calculate_aspects_to_fixed_stars(date, planet_positions, houses, orb=1.0, aspect_types=None, all_stars=False):
    """
    List aspects between planets and fixed stars, including the house of each fixed star.

    Parameters:
    - date: datetime object specifying the date and time for the calculation.
    - planet_positions: A dictionary of planets and their positions.
    - houses: A list of house cusp positions.
    - orb: Orb value for aspect consideration. Default is 1.0 degree.
    - aspect_types: A dictionary of aspect names and their angular distances. Defaults to common aspects if None.

    Returns:
    - A list of tuples, each representing an aspect between a planet and a fixed star, including the aspect name and the house of the fixed star.
    """
    fixed_stars = read_fixed_stars(all_stars)
    jd = swe.julday(date.year, date.month, date.day, date.hour)  # Assumes date includes time information
    aspects = []

    for star_name in fixed_stars:
        star_long = get_fixed_star_position(star_name, jd)
        
        # Determine the house for the fixed star
        star_house = next((i + 1 for i, cusp in enumerate(houses) if star_long < cusp), 12)

        # Check aspects with planets
        for planet, data in planet_positions.items():
            planet_long = data['longitude']
            for aspect_name, aspect_angle in aspect_types.items():
                angular_difference = abs(planet_long - star_long) % 360
                # Normalize the angle to <= 180 degrees for comparison
                if angular_difference > 180:
                    angular_difference = 360 - angular_difference
                if abs(angular_difference - aspect_angle) <= orb:
                    angular_difference = angular_difference - aspect_angle # Just show the difference
                    aspects.append((planet, star_name, aspect_name, angular_difference, star_house))
    
    return aspects

def read_fixed_stars(all_stars=False):
    """
    Read a list of fixed star names from a file.

    Returns:
    - A list of fixed star names.
    """
    if all_stars:
        with open('./ephe/fixed_stars_all.txt', 'r') as file:
            fixed_stars = file.read().splitlines()
    else:   
        with open('./ephe/astrologically_known_fixed_stars.txt', 'r') as file:
            fixed_stars = file.read().splitlines()
    return fixed_stars

def get_max_star_name_length(all_stars=False):
    fixed_stars = read_fixed_stars(all_stars)
    max_length = max(len(star_name) for star_name in fixed_stars)
    return max_length

def calculate_planet_positions(date, latitude, longitude):
    """
    Calculate the ecliptic longitudes and retrograde status of celestial bodies 
    at a given date and time, including special points like the Ascendant, Midheaven,
    and the South Node.

    Parameters:
    - date: A datetime object specifying the exact date and time.
    - latitude: The latitude of the observation point.
    - longitude: The longitude of the observation point.

    Returns:
    - A dictionary with each celestial body or point as keys, and their ecliptic longitude 
      and retrograde status as values.
    """
    jd = swe.julday(date.year, date.month, date.day, date.hour + date.minute / 60.0 + date.second / 3600.0)

    planets = {
        'Sun': swe.SUN, 'Moon': swe.MOON, 'Mercury': swe.MERCURY, 'Venus': swe.VENUS,
        'Mars': swe.MARS, 'Jupiter': swe.JUPITER, 'Saturn': swe.SATURN,
        'Uranus': swe.URANUS, 'Neptune': swe.NEPTUNE, 'Pluto': swe.PLUTO,
        'Chiron': swe.CHIRON, 'North Node': swe.MEAN_NODE  # Using the Mean Node
    }

    positions = {}

    for planet, id in planets.items():
        pos, ret = swe.calc_ut(jd, id) if planet != 'Chiron' else swe.calc(jd, id)
        zodiac, position = longitude_to_zodiac(pos[0]).split()
        positions[planet] = {
            'longitude': pos[0],
            'long_minutes': position,
            'zodiac_sign': zodiac,
            'retrograde': 'R' if pos[3] < 0 else ''  # pos[3] is the daily motion. If negative, the planet is retrograde.
        }

    # Calculate South Node as opposite of North Node
    positions['South Node'] = {
        'longitude': (positions['North Node']['longitude'] + 180) % 360,
        'long_minutes': coord_in_minutes((positions['North Node']['longitude'] + 180) % 360),
        'retrograde': 'R' if positions['North Node']['retrograde'] else '',
        'zodiac_sign': longitude_to_zodiac((positions['North Node']['longitude'] + 180) % 360).split()[0]
    }

    # Special calculations for Midheaven (MC), and Ascendant
    _, ascmc = swe.houses(jd, latitude, longitude, 'P'.encode('utf-8'))  # Placidus system
    positions['Ascendant'] = {'longitude': ascmc[0], 'long_minutes': coord_in_minutes(ascmc[0]),
                               'retrograde': '', 'zodiac_sign': longitude_to_zodiac(ascmc[0]).split()[0]}
    positions['Midheaven'] = {'longitude': ascmc[1], 'long_minutes': coord_in_minutes(ascmc[1]),
                               'retrograde': '', 'zodiac_sign': longitude_to_zodiac(ascmc[1]).split()[0]}


    return positions

def coord_in_minutes(longitude):
    degree = int(longitude % 30)
    minutes = int((longitude % 1) * 60)
    seconds = int((((longitude % 1) * 60) % 1) * 60)
    return f"{degree}°{minutes}'{seconds}''"    

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

def print_planet_positions(planet_positions, degree_in_minutes=False, notime=False):
    print(f"\n{'Planet':<10} | {'Zodiac':<11} | {'Position':<10} | {'Retrograde':<10}", end='')
    if house_positions and not notime:  # Checks if house_positions is not empty
        print(f" | {'House':<5}", end='')
    print("\n" + ("-" * 58 if house_positions else "-" * 50))  

    for planet, info in planet_positions.items():
        if notime and (planet in always_exclude_if_no_time):
            continue
        if degree_in_minutes:
            position = f"{info['long_minutes']}"
        else:
            position = f"{info['longitude']:.2f}°"
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

def print_aspects(aspects, imprecise_aspects="off", minor_aspects=True, degree_in_minutes=False):
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

def print_fixed_star_aspects(aspects, orb=1, minor_aspects=False, imprecise_aspects="off", notime=True, degree_in_minutes=False):
    print(f"Fixed Star Aspects ({orb}° orb)", end="")
    print(" including Minor Aspects" if minor_aspects else "", end="")
    if notime:
        print(f" with Imprecise Aspects set to {imprecise_aspects}", end="")
    print()
    
    # For formatting the table
    max_star_name_length = get_max_star_name_length(all_stars)

    print(f"{'Planet':<10} | {'Aspect':<14} | {'Star':<{max_star_name_length}} | {'Margin':<6}", end="")
    if house_positions and not notime:
        print(f" | {'Star in House':<5}", end='')
    print("\n" + "-" * (47+max_star_name_length)) 
    for aspect in aspects:
        planet, star_name, aspect_name, angle, house = aspect
        print(f"{planet:<10} | {aspect_name:<14} | {star_name:<{max_star_name_length}} | {angle:>5.2f}°", end='')

        if house_positions and not notime:
            print(f" | {house:<5}", end='')
        elif planet in off_by.keys() and off_by[planet] > orb:
            print(f" ±{off_by[planet]}°", end='')
        print()

    print()

# Function to check if there is an entry for a specified name in the JSON file
def load_event(filename, name):
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

# Constants
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

# Load event and Settings
name = "Mikael"  # Specify the name you want to check
exists = load_event(filename, name)
if exists:
    local_datetime = datetime.datetime.fromisoformat(exists[0]['datetime'])
    latitude = exists[0]['latitude']
    longitude = exists[0]['longitude']
    local_timezone = pytz.timezone(exists[0]['timezone'])
else: # If the name does not exist, use the following default settings
    local_datetime = datetime.datetime(1937, 11, 9, 2, 55)  # Time of day needed for house calculation, ascendant and midheaven
    latitude = 57.6828  # Sahlgrenska, Göteborg, Sweden
    longitude = 11.9624  # 11°57'44'' E 57°40'58'' N
    local_timezone = pytz.timezone('Europe/Stockholm')  # For Göteborg, Sweden
utc_datetime = convert_to_utc(local_datetime, local_timezone)
# Check if the time is set, or only the date, this is not compatible with people born at midnight (but can set second to 1)
notime = (local_datetime.hour == 0 and local_datetime.minute == 0 and local_datetime.second == 0)

imprecise_aspects = "off"  # If "off", the script will not show, if "warn" print a warning for uncertain aspects
orb = 1 # 1 degree orb
minor_aspects = False  # If True, the script will include minor aspects
all_stars = False  # If True, the script will include all fixed stars
degree_in_minutes = False  # If True, the script will show the positions in degrees and minutes

print(f"\nLocal Time: {local_datetime} {local_timezone}")
print(f"UTC Time: {utc_datetime} UTC")
print(f"Latitude: {latitude}, Longitude: {longitude}")
print("Placidus Houses")

if minor_aspects:
    aspect_types.update(minor_aspect_types)

planet_positions = calculate_planet_positions(utc_datetime, latitude, longitude)
house_positions, house_cusps = calculate_house_positions(utc_datetime, latitude, longitude, planet_positions)
aspects = calculate_aspects(planet_positions, orb, aspect_types=aspect_types)
fixstar_aspects = calculate_aspects_to_fixed_stars(utc_datetime, planet_positions, house_cusps, orb, aspect_types, all_stars)

print_planet_positions(planet_positions, degree_in_minutes, notime)
print_aspects(aspects, imprecise_aspects, minor_aspects, degree_in_minutes)
print_fixed_star_aspects(fixstar_aspects, orb, minor_aspects, imprecise_aspects, notime, degree_in_minutes)