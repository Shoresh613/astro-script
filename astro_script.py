import swisseph as swe
import datetime
import pytz

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

def list_aspects_to_fixed_stars_and_houses(date, planet_positions, houses, orb=1.0, aspect_types=None, all_stars=False):
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
        positions[planet] = {
            'longitude': pos[0],
            'retrograde': 'R' if pos[3] < 0 else ''  # pos[3] is the daily motion. If negative, the planet is retrograde.
        }

    # Special calculations for South Node, Midheaven (MC), and Ascendant
    _, ascmc = swe.houses(jd, latitude, longitude, 'P'.encode('utf-8'))  # Placidus system
    positions['Ascendant'] = {'longitude': ascmc[0], 'retrograde': ''}
    positions['Midheaven'] = {'longitude': ascmc[1], 'retrograde': ''}

    # Calculate South Node as opposite of North Node
    positions['South Node'] = {
        'longitude': (positions['North Node']['longitude'] + 180) % 360,
        'retrograde': ''
    }

    return positions




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
        {"Sun", "Ascendant"}, {"Sun", "Midheaven"}, 
        {"Moon", "Ascendant"}, {"Moon", "Midheaven"},
        {"Ascendant", "Midheaven"}, {"South Node", "North Node"}
    ]

    aspects_found = []
    planet_names = list(planet_positions.keys())

    for i, planet1 in enumerate(planet_names):
        for planet2 in planet_names[i+1:]:
            # Skip calculation if the pair is in the exclusion list
            if {planet1, planet2} in excluded_pairs:
                continue

            long1 = planet_positions[planet1]['longitude']
            long2 = planet_positions[planet2]['longitude']
            angle_diff = abs(long1 - long2) % 360
            angle_diff = min(angle_diff, 360 - angle_diff)  # Normalize to <= 180 degrees

            for aspect_name, aspect_angle in aspect_types.items():
                if abs(angle_diff - aspect_angle) <= orb:
                    aspects_found.append((planet1, planet2, aspect_name, angle_diff))

    return aspects_found

def print_planet_positions(planet_positions):
    off_by = {"Sun": 1, "Moon": 12, "Mercury": 1.2, "Venus": 1.2, "Mars": 0.5}  # Movement per day in degrees
    print(f"\n{'Planet':<10} | {'Zodiac':<11} | {'Position':<10} | {'Retrograde':<10}", end='')
    if house_positions:  # Checks if house_positions is not empty
        print(f" | {'House':<5}", end='')
    print("\n" + ("-" * 58 if house_positions else "-" * 50))  

    for planet, info in planet_positions.items():
        if notime and (planet in always_exclude_if_no_time):
            continue
        longitude = info['longitude']
        retrograde = info['retrograde']
        # house = house_positions.get(planet, "Unknown")  # Fallback to "Unknown" if not found
        zodiac_position = longitude_to_zodiac(longitude)
        zodiac, position = zodiac_position.split()
        retrograde_status = "R" if retrograde else ""
        print(f"{planet:<10} | {zodiac:<11} | {position:>10} | {retrograde_status:<10}", end='')
        if house_positions:
            house_num = house_positions.get(planet, {}).get('house', 'Unknown')  
            print(f" | {house_num:<5}", end='')
        elif planet in notime_imprecise_planets:
            print(f"±{off_by[planet]}°", end='')
        print()

def print_aspects(aspects, imprecise_aspects="off", minor_aspects=True):
    print(f"\nPlanetary Aspects ({orb}° orb)", end="")
    print(" and minor aspects" if minor_aspects else "", end="")
    if notime:
        print(f" with imprecise aspects {imprecise_aspects}", end="")
    print(":\n" + "-" * 49)
    for aspect in aspects:
        angle_with_degree = f"{aspect[3]:.2f}°" # Format the angle with the degree sign included
        if imprecise_aspects == "off" and (aspect[0] in notime_imprecise_planets or aspect[1] in notime_imprecise_planets):
            continue
        elif notime and (aspect[0] in always_exclude_if_no_time or aspect[1] in always_exclude_if_no_time):
            continue
        else:
            print(f"{aspect[0]:<10} | {aspect[2]:<14} | {aspect[1]:<10} | {angle_with_degree:<7}", end='')
        if imprecise_aspects == "warning" and (aspect[0] in notime_imprecise_planets or aspect[1] in notime_imprecise_planets):
            print(" (uncertain)", end='')
        print()
    print("\n")
    if not house_positions:
        print("* No time of day specified. Houses cannot be calculated. ")
        print("  Aspects to the Ascendant and Midheaven are not available.")
        print("  The positions of the Sun, Moon, Mercury, Venus, and Mars are uncertain.\n")
        print("\n  Please specify the time of birth for a complete chart.\n")

def print_fixed_star_aspects(aspects, orb=1, minor_aspects=False, imprecise_aspects="off", notime=False):
    print(f"\nFixed Star Aspects ({orb}° orb)", end="")
    print(" including Minor Aspects" if minor_aspects else "", end="")
    if notime:
        print(f" with Imprecise Aspects set to {imprecise_aspects}", end="")
    print()
    
    # When you print the table
    max_star_name_length = get_max_star_name_length(all_stars)

    print(f"{'Planet':<10} | {'Aspect':<14} | {'Star':<{max_star_name_length}} | {'House':<5} | {'Angle':<6}")
    print("-" * (46+max_star_name_length))  # Adjust the separator length accordingly
    for aspect in aspects:
        # Unpack the aspect tuple to include the angle
        planet, star_name, aspect_name, angle, house = aspect
        print(f"{planet:<10} | {aspect_name:<14} | {star_name:<{max_star_name_length}} | {house:<5} | {angle:.2f}°")
    print("\n")


aspect_types = {'Conjunction': 0, 'Opposition': 180, 'Trine': 120, 'Square': 90, 'Sextile': 60,}
minor_aspect_types = {
    'Quincunx': 150, 'Semi-Sextile': 30, 'Semi-Square': 45, 'Quintile': 72, 'Bi-Quintile': 144,
    'Sesqui-Square': 135, 'Septile': 51.4285714, 'Novile': 40, 'Decile': 36,
}
notime_imprecise_planets = ['Moon', 'Mercury', 'Venus', 'Sun', 'Mars']  # Aspects that are uncertain without time of day
imprecise_aspects = "warn"  # If True, the script will not show, if "Warn" print a warning for uncertain aspects
always_exclude_if_no_time = ['Ascendant', 'Midheaven']  # Aspects that are always excluded if no time of day is specified

# Example usage
date = datetime.datetime(1979, 1, 9, 12, 38)  # Time of day needed for house calculation, ascendant and midheaven
notime = (date.hour == 0 and date.minute == 0)

latitude = 57.7089  # Göteborg, Sweden
longitude = 11.9746

# Settings
orb = 0.1 # 1 degree orb
minor_aspects = False  # If True, the script will include minor aspects
all_stars = False  # If True, the script will include all fixed stars

local_timezone = pytz.timezone('Europe/Stockholm')  # For Göteborg, Sweden
local_datetime = date

utc_datetime = convert_to_utc(local_datetime, local_timezone)
print(f"\nLocal Time: {local_datetime} {local_timezone}")
print(f"UTC Time: {utc_datetime} UTC")

if minor_aspects:
    aspect_types.update(minor_aspect_types)

planet_positions = calculate_planet_positions(utc_datetime, latitude, longitude)
house_positions, house_cusps = calculate_house_positions(utc_datetime, latitude, longitude, planet_positions)
aspects = calculate_aspects(planet_positions, orb, aspect_types=aspect_types)
fixstar_aspects = list_aspects_to_fixed_stars_and_houses(utc_datetime, planet_positions, house_cusps, orb, aspect_types, all_stars)

print_planet_positions(planet_positions)
print_aspects(aspects, imprecise_aspects, minor_aspects)
print_fixed_star_aspects(fixstar_aspects)