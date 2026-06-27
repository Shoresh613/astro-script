import swisseph as swe

from .zodiac import calculation_flags


def calculate_house_cusps(date, latitude, longitude, h_sys="P", zodiac="tropical"):
    jd = swe.julday(
        date.year,
        date.month,
        date.day,
        date.hour + date.minute / 60.0 + date.second / 3600.0,
    )
    flags = calculation_flags(zodiac)
    if flags:
        return swe.houses_ex(
            jd, latitude, longitude, h_sys.encode("utf-8"), flags
        )
    return swe.houses(jd, latitude, longitude, h_sys.encode("utf-8"))


def find_house_number(longitude, houses):
    """Return the house containing longitude, including 0/360 wraparound."""
    longitude %= 360
    house_cusps = houses[:12]

    for index, cusp in enumerate(house_cusps):
        cusp %= 360
        next_cusp = house_cusps[(index + 1) % 12] % 360
        adjusted_longitude = longitude

        if next_cusp < cusp:
            next_cusp += 360
            if adjusted_longitude < cusp:
                adjusted_longitude += 360

        if cusp <= adjusted_longitude < next_cusp:
            return index + 1

    return 1


def calculate_individual_house_position(
    date, latitude, longitude, planet_longitude, h_sys="P", zodiac="tropical"
):
    houses, _ = calculate_house_cusps(
        date, latitude, longitude, h_sys=h_sys, zodiac=zodiac
    )
    return find_house_number(planet_longitude, houses)


def calculate_house_positions(
    date,
    latitude,
    longitude,
    altitude,
    planets_positions,
    notime=False,
    h_sys="P",
    zodiac="tropical",
):
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
    try:
        swe.set_topo(longitude, latitude, altitude or 0.0)
    except Exception as e:
        print(f"Error setting topocentric coordinates: {e}")

    # Validate input date has a time component (convention to use 00:00:00 for unknown time )
    if notime:
        print("Warning: Time is not set. Houses cannot be reliably calculated.")

    houses, ascmc = calculate_house_cusps(
        date, latitude, longitude, h_sys=h_sys, zodiac=zodiac
    )

    ascendant_long = ascmc[0]  # Ascendant is the first item in ascmc list
    midheaven_long = ascmc[1]  # Midheaven is the second item in ascmc list

    # Initialize dictionary with Ascendant and Midheaven
    house_positions = {
        "Ascendant": {"longitude": ascendant_long, "house": 1},
        "Midheaven": {
            "longitude": midheaven_long,
            "house": 10,
        },  # Midheaven is traditionally associated with the 10th house
    }

    # Assign planets to houses
    for planet, planet_info in planets_positions.items():
        planet_longitude = planet_info["longitude"] % 360
        house_num = find_house_number(planet_longitude, houses)

        house_positions[planet] = {"longitude": planet_longitude, "house": house_num}

    # Always in same houses, so as not to inflate house counts
    keys_to_update = ["Ascendant", "Midheaven", "IC", "DC"]
    for key in keys_to_update:
        if key in house_positions:
            house_positions[key]["house"] = ""

    return (
        house_positions,
        houses[:13],
    )  # Return house positions and cusps (including Ascendant)
