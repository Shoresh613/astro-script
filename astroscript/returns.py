from datetime import datetime, timedelta

import swisseph as swe

from .constants import PLANET_RETURN_DICT

def find_next_same_degree(
    dt,
    planet_name,
    longitude,
    latitude,
    altitude,
    nextprev="next",
    center="topocentric",
):
    if planet_name.title() not in PLANET_RETURN_DICT:
        raise ValueError("Invalid planet name provided.")

    planet_info = PLANET_RETURN_DICT[planet_name.title()]
    planet = planet_info["constant"]
    orbital_period = planet_info["orbital_period_days"]

    julian_day = swe.julday(dt.year, dt.month, dt.day, dt.hour + dt.minute / 60.0)

    # Handle None altitude by defaulting to sea level (0.0)
    if altitude is None:
        altitude = 0.0

    if center == "topocentric":
        swe.set_topo(float(longitude), float(latitude), float(altitude))
        current_pos, _ = swe.calc(julian_day, planet, swe.FLG_TOPOCTR)
    elif center == "heliocentric":
        current_pos, _ = swe.calc_ut(julian_day, planet, swe.FLG_HELCTR)
    else:
        current_pos, _ = swe.calc_ut(julian_day, planet)

    current_degree = current_pos[0] % 360  # Normalize to 0-360 degrees

    if nextprev == "next":
        start_dt = datetime.now()
    else:
        start_dt = datetime.now() - timedelta(days=orbital_period)

    # Define the search interval (orbital period)
    end_dt = start_dt + timedelta(days=orbital_period)

    def get_next_degree(next_dt, longitude, latitude, altitude, center):
        julian_day_next = swe.julday(
            next_dt.year,
            next_dt.month,
            next_dt.day,
            next_dt.hour + next_dt.minute / 60.0,
        )

        if center == "topocentric":
            swe.set_topo(float(longitude), float(latitude), float(altitude))
            next_pos, _ = swe.calc(julian_day_next, planet, swe.FLG_TOPOCTR)
        elif center == "heliocentric":
            next_pos, _ = swe.calc_ut(julian_day_next, planet, swe.FLG_HELCTR)
        else:
            next_pos, _ = swe.calc_ut(julian_day_next, planet)

        return next_pos[0] % 360

    # Binary search-like approach to find the date with the same degree
    while (
        end_dt - start_dt
    ).total_seconds() > 30:  # While the interval is larger than 1/2 minute
        mid_dt = start_dt + (end_dt - start_dt) / 2
        next_degree = get_next_degree(mid_dt, longitude, latitude, altitude, center)

        if (
            abs(next_degree - current_degree) < 0.005
        ):  # Allow small tolerance due to precision
            return mid_dt

        if next_degree < current_degree:
            start_dt = mid_dt
        else:
            end_dt = mid_dt

    # If not found within the loop, return the closest approximation
    print("Exact return not found")
    return start_dt
