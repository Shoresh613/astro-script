import swisseph as swe
import datetime

swe.set_ephe_path('./ephe/')

def calculate_house_positions(date, latitude, longitude, planets_positions):
    if date.hour == 0 and date.minute == 0: # Doesn't work for people born at midnight
        return {}  #Return an empty dictionary if the time is not specified
    
    # Convert date and time to Julian Day
    jd = swe.julday(date.year, date.month, date.day, date.hour + date.minute / 60.0)
    
    # Calculate houses
    h_sys = 'P'  # Placidus house system
    houses, _ = swe.houses(jd, latitude, longitude, h_sys.encode('utf-8'))
    house_cusps = houses[:13]  # The cusps of the houses are the first 12 elements of the houses list

    # Determine the house for each planet
    house_positions = {}
    for planet, longitude in planets_positions.items():
        longitude = longitude['longitude']  # Correctly extract the longitude
        house_num = 1
        for i in range(1, len(houses)):
            if longitude < houses[i]:
                break
            house_num = i + 1
        house_positions[planet] = house_num
    
    return house_positions, house_cusps

def longitude_to_zodiac(longitude):
    zodiac_signs = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']
    sign_index = int(longitude / 30)
    degree = longitude % 30
    return f"{zodiac_signs[sign_index]} {degree:.2f}°"

def is_planet_retrograde(planet, jd):
    # Calculate the planet's position 10 minutes before the given Julian Day
    pos_before, _ = swe.calc_ut(jd - (10 / 1440), planet)[:2]  # 10 minutes as a fraction of a day
    longitude_before = pos_before[0]

    # Calculate the planet's position 10 minutes after the given Julian Day
    pos_after, _ = swe.calc_ut(jd + (10 / 1440), planet)[:2]  # 10 minutes as a fraction of a day
    longitude_after = pos_after[0]

    # If the later longitude is less than the earlier longitude, the planet is moving "backwards" - indicating retrograde motion
    return longitude_after < longitude_before

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

def list_aspects_to_fixed_stars_and_houses(date, planet_positions, houses, orb=1.0, aspect_types={'Conjunction': 0, 'Opposition': 180, 'Trine': 120, 'Square': 90, 'Sextile': 60}):
    """
    List aspects between planets and fixed stars, including the house of each fixed star.
    
    Parameters:
    - date: datetime object specifying the date and time for the calculation.
    - planet_positions: A dictionary of planets and their positions.
    - houses: A list of house cusp positions.
    - orb: Orb value for aspect consideration.
    - aspect_types: A dictionary of aspect names and their angular distances.
    """
    fixed_stars = read_fixed_stars()
    jd = swe.julday(date.year, date.month, date.day, date.hour)  # Assumes date includes time information
    aspects = []
    
    for star_name in fixed_stars:
        star_long = get_fixed_star_position(star_name, jd)
        # Find the house of the fixed star
        star_house = 1
        for i, cusp in enumerate(houses[1:], start=1):
            if star_long < cusp:
                break
            star_house = i + 1
        
        # Check aspects with planets
        for planet, data in planet_positions.items():
            planet_long = data['longitude']
            for aspect_name, aspect_angle in aspect_types.items():
                angular_difference = abs(planet_long - star_long) % 360
                if angular_difference > 180:  # Normalize the angle
                    angular_difference = 360 - angular_difference
                if abs(angular_difference - aspect_angle) <= orb:
                    aspects.append((planet, star_name, aspect_name, star_house))
    
    return aspects


def read_fixed_stars():
    with open('./ephe/fixed_stars.txt', 'r') as file:
        fixed_stars = file.read().splitlines()
    return fixed_stars

def calculate_planet_positions(date, latitude, longitude):
    jd = swe.julday(date.year, date.month, date.day)
    planets = {
        'Sun': swe.SUN,
        'Moon': swe.MOON,
        'Mercury': swe.MERCURY,
        'Venus': swe.VENUS,
        'Mars': swe.MARS,
        'Jupiter': swe.JUPITER,
        'Saturn': swe.SATURN,
        'Uranus': swe.URANUS,
        'Neptune': swe.NEPTUNE,
        'Pluto': swe.PLUTO,
        'Chiron': swe.CHIRON,
        'North Node': swe.MEAN_NODE,  # Using the Mean Node; for True Node, use swe.TRUE_NODE
        'Ascendant': swe.ASC,
        # South Node and Midheaven aren't directly available but can be calculated from the North Node's ans Ascendants positions (opposite point)
    }

    positions = {}
    for planet, id in planets.items():
        if planet == 'Chiron':
            pos, ret = swe.calc(jd, id)  # For asteroids, use swe.calc instead of swe.calc_ut
        else:
            pos, ret = swe.calc_ut(jd, id)
        longitude = pos[0]
        # Check for retrograde movement
        retrograde = 'R' if is_planet_retrograde(id, jd) else ''
        positions[planet] = {'longitude': longitude, 'retrograde': retrograde}

    # Calculate South Node as opposite of North Node
    north_node_long = positions['North Node']['longitude']
    south_node_long = (north_node_long + 180) % 360
    positions['South Node'] = {'longitude': south_node_long, 'retrograde': ''}

    # Calculate Midheaven as opposite of Ascendant
    ascendant_long = positions['Ascendant']['longitude']
    midheaven_long = (ascendant_long + 180) % 360
    positions['Midheaven'] = {'longitude': midheaven_long, 'retrograde': ''}

    return positions

def calculate_aspects(planet_positions, orb, aspect_types, minor_aspects=True):
    aspects = []

    planets = list(planet_positions.keys())
    for i, planet1 in enumerate(planets):
        for planet2 in planets[i+1:]:
            longitude1 = planet_positions[planet1]['longitude']
            longitude2 = planet_positions[planet2]['longitude']
            
            angle = abs(longitude1 - longitude2)
            angle = min(angle, 360 - angle)  # Correct for angles > 180

            for aspect, aspect_angle in aspect_types.items():
                if abs(angle - aspect_angle) <= orb:  # Within the specified orb
                    aspects.append((planet1, planet2, aspect, angle))
            
            if minor_aspects:
                for aspect, aspect_angle in minor_aspect_types.items():
                    if abs(angle - aspect_angle) <= orb:
                        aspects.append((planet1, planet2, aspect, angle))
    return aspects

def print_planet_positions(planet_positions):
    off_by = {"Sun": 1, "Moon": 12, "Mercury": 1.2, "Venus": 1.2, "Mars": 0.5}  # Movement per day in degrees
    print(f"\n{'Planet':<10} | {'Zodiac':<11} | {'Position':<8} | {'Retrograde':<10}", end='')
    if house_positions:  # Checks if house_positions is not empty
        print(f" | {'House':<5}", end='')
    print("\n" + ("-" * 54 if house_positions else "-" * 46))  

    for planet in planet_positions:
        if notime and (planet in always_exclude_if_no_time):
            continue
        data = planet_positions[planet]
        longitude = data['longitude']
        retrograde = data['retrograde']
        house = house_positions.get(planet, "Unknown")  # Fallback to "Unknown" if not found
        zodiac_position = longitude_to_zodiac(longitude)
        zodiac, position = zodiac_position.split()
        retrograde_status = "R" if retrograde else ""
        print(f"{planet:<10} | {zodiac:<11} | {position:>8} | {retrograde_status:<10}", end='')
        if house_positions:
            print(f" | {house:<5}", end='')
        elif planet in notime_imprecise_planets:
            print(f"±{off_by[planet]}°", end='')
        print()

def print_aspects(aspects, imprecise_aspects="off"):
    print(f"\nAspects ({orb}° orb) with imprecise aspects {imprecise_aspects}:")
    print("-" * 49)
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

def print_fixed_star_aspects(aspects):
    print("\nAspects to fixed stars:")
    print("-" * 49)
    for aspect in aspects:
        print(f"{aspect[0]:<10} | {aspect[2]:<14} | {aspect[1]:<10} | {aspect[3]:<7}")
    print("\n")

# Example usage
date = datetime.datetime(1979, 1, 9, 12, 38)  # Time of day needed for house calculation, ascendant and midheaven
notime = (date.hour == 0 and date.minute == 0)

latitude = 57.7089  # Göteborg, Sweden
longitude = 11.9746
orb = 0.5 # 1 degree orb
aspect_types = {'Conjunction': 0, 'Opposition': 180, 'Trine': 120, 'Square': 90, 'Sextile': 60,}
minor_aspect_types = {
    'Quincunx': 150, 'Semi-Sextile': 30, 'Semi-Square': 45, 'Quintile': 72, 'Bi-Quintile': 144,
    'Sesqui-Square': 135, 'Septile': 51.4285714, 'Novile': 40, 'Decile': 36,
}

notime_imprecise_planets = ['Moon', 'Mercury', 'Venus', 'Sun', 'Mars']  # Aspects that are uncertain without time of day
imprecise_aspects = "off"  # If True, the script will not show, if "Warn" print a warning for uncertain aspects
always_exclude_if_no_time = ['Ascendant', 'Midheaven']  # Aspects that are always excluded if no time of day is specified
minor_aspects = True  # If True, the script will include minor aspects
if minor_aspects:
    aspect_types.update(minor_aspect_types)

planet_positions = calculate_planet_positions(date, latitude, longitude)
house_positions, house_cusps = calculate_house_positions(date, latitude, longitude, planet_positions)
aspects = calculate_aspects(planet_positions, orb, aspect_types=aspect_types)

fixstar_aspects = list_aspects_to_fixed_stars_and_houses(date, planet_positions, house_cusps, orb, aspect_types=aspect_types)


print_planet_positions(planet_positions)
print_aspects(aspects)
print_fixed_star_aspects(fixstar_aspects)