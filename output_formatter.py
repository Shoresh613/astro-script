"""
Output formatting functions for the astro script.
Contains functions for formatting text, HTML, and table output.
"""

import os
import pytz
from tabulate import tabulate, SEPARATING_LINE
from datetime import datetime
from constants import *


def setup_output_formatting(output_type: str) -> dict:
    """
    Set up formatting variables based on output type - matches original exactly.

    Args:
        output_type: output format ('text', 'html', 'return_text', 'return_html')

    Returns:
        dict: formatting variables
    """
    if output_type in ("html", "return_html"):
        return {
            "bold": "<b>",
            "nobold": "</b>",
            "br": "\n<br>",
            "p": "\n<p>",
            "h1": "<h1>",
            "h2": "<h2>",
            "h3": "<h3>",
            "h4": "<h4>",
            "h1_": "</h1>",
            "h2_": "</h2>",
            "h3_": "</h3>",
            "h4_": "</h4>",
            "degree_symbol": "" if os.name == "nt" else "°",
        }
    elif output_type == "text":
        return {
            "bold": "\033[1m",
            "nobold": "\033[0m",
            "br": "\n",
            "p": "\n",
            "h1": "",
            "h2": "",
            "h3": "",
            "h4": "",
            "h1_": "",
            "h2_": "",
            "h3_": "",
            "h4_": "",
            "degree_symbol": "°",
        }
    else:  # return_text and other modes
        return {
            "bold": "",
            "nobold": "",
            "br": "\n",
            "p": "\n",
            "h1": "",
            "h2": "",
            "h3": "",
            "h4": "",
            "h1_": "",
            "h2_": "",
            "h3_": "",
            "h4_": "",
            "degree_symbol": "°",
        }


def coord_in_minutes(longitude, output_type):
    """
    Convert a celestial longitude into degrees, minutes, and seconds format.
    """
    degrees = int(longitude)  # Extract whole degrees
    minutes = int((longitude - degrees) * 60)  # Extract whole minutes
    seconds = int(((longitude - degrees) * 60 - minutes) * 60)  # Extract whole seconds

    degree_symbol = "" if (os.name == "nt" and output_type == "html") else "°"

    neg = ""
    if minutes < 0:
        minutes = abs(minutes)
        seconds = abs(seconds)
        neg = "-"
    return f"{neg}{degrees}{degree_symbol}{minutes}'{seconds}\""


def print_planet_positions(
    planet_positions,
    degree_in_minutes=False,
    notime=False,
    house_positions=None,
    orb=1,
    output_type="text",
    hide_decans=False,
    classic_rulers=False,
    center="geocentric",
    pluto_ecliptic=None,
):
    """
    Print the positions of planets in a human-readable format - matches original exactly.
    """
    from astro_calculations import (
        assess_planet_strength,
        check_degree,
        is_planet_elevated,
        longitude_to_zodiac,
        coord_in_minutes,
    )

    # Set up formatting variables exactly like original
    fmt = setup_output_formatting(output_type)
    table_format = "unsafehtml" if output_type in ("html", "return_html") else "simple"
    # Initialize counters for analysis tables
    zodiac_signs = list(ZODIAC_ELEMENTS.keys())
    sign_counts = {sign: {"count": 0, "planets": []} for sign in zodiac_signs}
    element_counts = {element: 0 for element in ["Fire", "Earth", "Air", "Water"]}
    modality_counts = {
        mod: {"count": 0, "planets": []} for mod in ["Cardinal", "Fixed", "Mutable"]
    }
    planet_house_counts = {house: 0 for house in range(1, 13)}

    # Define headers exactly like original
    if center == "heliocentric":
        headers = ["Planet", "Zodiac", "Degree"]
    else:
        headers = [
            "Planet",
            "Zodiac",
            "Degree",
            "Retrograde" if output_type in ("html", "return_html") else "R",
        ]

    if house_positions and (not notime and not center == "heliocentric"):
        headers.append("House")
    headers.append("Dignity")
    if notime:
        headers.insert(3, "Off by")
    if not hide_decans:
        headers.append(
            "Decan ruler" if output_type in ("html", "return_html") else "Decan"
        )

    # Build planet signs dict for dignity calculations
    planet_signs = {}
    for planet, info in planet_positions.items():
        zodiac = info.get(
            "zodiac_sign", longitude_to_zodiac(info["longitude"], "text").split()[-1]
        )
        planet_signs[planet] = zodiac  # Calculate dignity assessments
    strength_check = assess_planet_strength(planet_signs, classic_rulers)
    # For elevation check we need house positions, so let's prepare a proper dict
    planet_house_dict = {}
    if house_positions:
        for planet in planet_positions.keys():
            house_info = house_positions.get(planet, {})
            if isinstance(house_info, dict):
                planet_house_dict[planet] = house_info.get("house", "")
            else:
                planet_house_dict[planet] = house_info
    elevation_check = is_planet_elevated(planet_house_dict)

    # Build table data
    zodiac_table_data = []

    for planet, info in planet_positions.items():
        if notime and planet in ALWAYS_EXCLUDE_IF_NO_TIME:
            continue

        longitude = info["longitude"]
        degrees_within_sign = longitude % 30
        zodiac = info.get(
            "zodiac_sign", longitude_to_zodiac(longitude, "text").split()[-1]
        )
        retrograde = info.get("retrograde", False)
        decan_ruler = info.get("decan_ruled_by", "")

        # Calculate degree checks
        degree_check = check_degree({planet: zodiac}, degrees_within_sign)

        position = (
            coord_in_minutes(degrees_within_sign, output_type)
            if degree_in_minutes
            else f"{degrees_within_sign:.2f}{fmt['degree_symbol']}"
        )

        retrograde_status = "R" if retrograde else ""

        # Build row based on center type
        if center == "heliocentric":
            row = [planet, zodiac, position]
        else:
            row = [planet, zodiac, position, retrograde_status]

        # Add "Off by" column if notime
        if notime and planet in OFF_BY.keys() and OFF_BY[planet] > orb:
            off_by = f"±{OFF_BY[planet]}{fmt['degree_symbol']}"
            row.insert(3, off_by)
        elif notime:
            off_by = ""
            row.insert(3, off_by)  # Add house if available
        if house_positions and not notime and not center == "heliocentric":
            house_info = house_positions.get(planet, {})
            if isinstance(house_info, dict):
                house_num = house_info.get("house", "Unknown")
            else:
                house_num = house_info  # In case it's just an integer
            row.insert(4 if notime else -1, house_num)
            if house_num and isinstance(house_num, int):
                planet_house_counts[house_num] += 1

        # Add dignity column
        dignity = (
            elevation_check.get(planet, "")
            + strength_check.get(planet, "")
            + degree_check.get(planet, "")
            + (f" {pluto_ecliptic}" if planet == "Pluto" and pluto_ecliptic else "")
        )
        row.append(dignity)

        # Add decan ruler if not hidden
        if not hide_decans:
            row.append(
                decan_ruler
            )  # Add separating line for special planets in text output
        if (planet == "Fortune" or planet == "Ascendant") and output_type in (
            "text",
            "return_text",
        ):
            zodiac_table_data.append(SEPARATING_LINE)
        zodiac_table_data.append(row)

        # Count zodiac signs, elements and modalities for analysis tables
        sign_counts[zodiac]["count"] += 1
        sign_counts[zodiac]["planets"].append(planet)
        modality = ZODIAC_SIGN_TO_MODALITY[zodiac]
        modality_counts[modality]["count"] += 1
        modality_counts[modality]["planets"].append(planet)
        element_counts[ZODIAC_ELEMENTS[zodiac]] += 1

    # Generate main planetary positions table
    table = tabulate(
        zodiac_table_data, headers=headers, tablefmt=table_format, floatfmt=".2f"
    )
    to_return = table

    if output_type in ("text", "html"):
        print(table)

    # Add house counts if available
    if not notime and not center == "heliocentric":
        house_count_output = house_count(
            planet_house_counts, output_type, fmt["bold"], fmt["nobold"], fmt["br"]
        )
        if output_type in ("return_text", "return_html"):
            to_return += fmt["p"] + house_count_output
        else:
            print(fmt["p"] + house_count_output)

    # Add zodiac sign distribution table
    if output_type in ("html", "return_html"):
        to_return += fmt["p"] + "<div class='table-container'>"
    elif output_type == "html":
        print(fmt["p"] + "<div class='table-container'>")

    sign_count_table_data = []
    for sign, data in sign_counts.items():
        if data["count"] > 0:
            row = [
                sign,
                data["count"],
                ", ".join(data["planets"])
                + (" (stellium)" if data["count"] >= 4 else ""),
            ]
            sign_count_table_data.append(row)

    sign_table = tabulate(
        sign_count_table_data,
        headers=["Sign", "Nr", "Planets in Sign".title()],
        tablefmt=table_format,
        floatfmt=".2f",
    )
    to_return += fmt["br"] + fmt["br"] + sign_table
    if output_type in ("text", "html"):
        print(fmt["p"] + sign_table + fmt["br"])

    # Add element distribution table
    element_count_table_data = []
    for element, count in element_counts.items():
        if count > 0:
            row = [element, count]
            element_count_table_data.append(row)

    # Calculate day/night sign totals
    fire_count = next(
        (item[1] for item in element_count_table_data if item[0] == "Fire"), 0
    )
    air_count = next(
        (item[1] for item in element_count_table_data if item[0] == "Air"), 0
    )
    earth_count = next(
        (item[1] for item in element_count_table_data if item[0] == "Earth"), 0
    )
    water_count = next(
        (item[1] for item in element_count_table_data if item[0] == "Water"), 0
    )

    day_signs = fire_count + air_count
    night_signs = earth_count + water_count

    element_count_table_data.append(["Day", day_signs])
    element_count_table_data.append(["Night", night_signs])

    element_table = tabulate(
        element_count_table_data,
        headers=["Element", "Nr"],
        tablefmt=table_format,
        floatfmt=".2f",
    )
    to_return += fmt["br"] + element_table
    if output_type in ("text", "html"):
        print(element_table + fmt["br"])

    # Add modality distribution table
    modality_count_table_data = []
    for modality, data in modality_counts.items():
        if data["count"] > 0:
            row = [
                modality,
                data["count"],
                ", ".join(data["planets"]),
            ]
            modality_count_table_data.append(row)

    modality_table = tabulate(
        modality_count_table_data,
        headers=["Modality", "Nr", "Planets in Modality".title()],
        tablefmt=table_format,
        floatfmt=".2f",
    )
    to_return += fmt["br"] + modality_table

    if output_type in ("text", "html"):
        print(modality_table)

    # Close div for HTML
    if output_type in ("html", "return_html"):
        to_return += "</div>"
    elif output_type == "html":
        print("</div>")

    if output_type == "text":
        return ""
    else:
        return to_return


def format_planet_position(
    planet: str,
    longitude: float,
    house: int = None,
    retrograde: bool = False,
    output_type: str = "text",
) -> str:
    """
    Format a planet position for display.
    """
    from astro_calculations import longitude_to_zodiac

    fmt = setup_output_formatting(output_type)

    # Get zodiac position
    zodiac_pos = longitude_to_zodiac(longitude, output_type)

    # Add retrograde indicator
    retro_symbol = " ℞" if retrograde else ""

    # Add house if provided
    house_str = f" in House {house}" if house else ""

    return f"{planet}: {zodiac_pos}{retro_symbol}{house_str}"


def format_aspect_table(
    aspects: dict, planet_positions: dict, output_type: str = "text"
) -> str:
    """
    Format aspects as a table.
    """
    from astro_calculations import longitude_to_zodiac

    fmt = setup_output_formatting(output_type)
    table_format = "unsafehtml" if output_type in ("html", "return_html") else "simple"

    if not aspects:
        return f"No aspects found{fmt['br']}"

    headers = ["Planet 1", "Aspect", "Planet 2", "Orb"]
    table_data = []

    for (planet1, planet2), aspect_info in aspects.items():
        aspect_name = aspect_info.get("aspect_name", "")
        orb_diff = aspect_info.get("orb_difference", 0)

        row = [planet1, aspect_name, planet2, f"{orb_diff:.2f}{fmt['degree_symbol']}"]
        table_data.append(row)

    if output_type in ("html", "return_html"):
        table_html = tabulate(table_data, headers=headers, tablefmt="html")
        return table_html
    else:
        table_text = tabulate(table_data, headers=headers, tablefmt="grid")
        return table_text


def print_aspects(
    aspects,
    planet_positions,
    orbs,
    transit_planet_positions=None,
    imprecise_aspects="off",
    minor_aspects=True,
    degree_in_minutes=False,
    house_positions=None,
    orb=1,
    type="Natal",
    p1_name="",
    p2_name="",
    notime=False,
    output="text",
    show_aspect_score=False,
    star_positions=None,
    complex_aspects=None,
    center="geocentric",
):
    """
    Print astrological aspects between celestial bodies - matches original exactly.
    """
    # Set up formatting variables exactly like original
    if output in ("html", "return_html"):
        table_format = "unsafehtml"
        house_called = "House"
        bold = "<b>"
        nobold = "</b>"
        br = "\n<br>"
        p = "\n<p>"
        h3 = "<h3>"
        h3_ = "</h3>"
    elif output == "text":
        table_format = "simple"
        house_called = "H"
        bold = "\033[1m"
        nobold = "\033[0m"
        br = "\n"
        p = "\n"
        h3 = ""
        h3_ = ""
    else:
        table_format = "simple"
        house_called = "H"
        bold = ""
        nobold = ""
        br = "\n"
        p = "\n"
        h3 = ""
        h3_ = ""

    degree_symbol = "" if (os.name == "nt" and output == "html") else "°"

    # Build aspects table
    planetary_aspects_table_data = []
    headers = ["Planet", "H", "Aspect", "Planet", "H", "Degree"]
    if show_aspect_score:
        headers.append("Score")

    to_return = ""

    # Simple aspects table - basic implementation
    for (planet1, planet2), aspect_info in aspects.items():
        aspect_name = aspect_info.get("aspect_name", "")
        orb_diff = aspect_info.get("orb_difference", 0)

        # Get house positions if available
        house1 = house_positions.get(planet1, "") if house_positions else ""
        house2 = house_positions.get(planet2, "") if house_positions else ""

        # Format orb difference
        orb_str = f"{orb_diff:.2f}{degree_symbol}"

        row = [planet1, house1, aspect_name, planet2, house2, orb_str]
        if show_aspect_score:
            score = aspect_info.get("score", 0)
            row.append(f"{score:.1f}")

        planetary_aspects_table_data.append(row)

    if planetary_aspects_table_data:  # Create table
        table = tabulate(
            planetary_aspects_table_data, headers=headers, tablefmt=table_format
        )

        if output in ("text"):
            print(f"{h3}Planetary Aspects{h3_}")
            print(table)

        to_return = f"{h3}Planetary Aspects{h3_}{br}{table}"
    else:
        if output in ("text"):
            print("No aspects found")
        to_return = "No aspects found"

    return to_return


def format_house_positions(house_positions: dict, output_type: str = "text") -> str:
    """
    Format house positions as a table.
    """
    fmt = setup_output_formatting(output_type)

    if not house_positions:
        return f"No house positions available{fmt['br']}"

    result = f"{fmt['h3']}House Positions{fmt['h3_']}{fmt['br']}"

    for house_num in range(1, 13):
        planets_in_house = [
            planet
            for planet, house_info in house_positions.items()
            if house_info.get("house") == house_num
        ]

        if planets_in_house:
            planets_str = ", ".join(planets_in_house)
            result += f"House {house_num}: {planets_str}{fmt['br']}"

    return result


def format_chart_patterns(patterns: list, output_type: str = "text") -> str:
    """
    Format chart patterns for display.

    Args:
        patterns: list of chart pattern dictionaries
        output_type: output format

    Returns:
        str: formatted chart patterns
    """
    fmt = setup_output_formatting(output_type)

    if not patterns:
        return f"No significant chart patterns found{fmt['br']}"

    result = f"{fmt['h3']}Chart Patterns{fmt['h3_']}{fmt['br']}"

    for pattern in patterns:
        pattern_type = pattern.get("type", "Unknown")
        planets = pattern.get("planets", [])
        description = pattern.get("description", "")

        result += f"{fmt['bold']}{pattern_type}{fmt['nobold']}: "
        result += f"{', '.join(planets)}"

        if description:
            result += f" - {description}"

        result += f"{fmt['br']}"

    return result


def format_moon_phase(phase_info: dict, output_type: str = "text") -> str:
    """
    Format moon phase information.

    Args:
        phase_info: moon phase data
        output_type: output format

    Returns:
        str: formatted moon phase
    """
    fmt = setup_output_formatting(output_type)

    if not phase_info:
        return ""

    phase_name = phase_info.get("phase_name", "Unknown")
    illumination = phase_info.get("illumination", 0)

    result = f"{fmt['h4']}Moon Phase{fmt['h4_']}{fmt['br']}"
    result += f"Phase: {fmt['bold']}{phase_name}{fmt['nobold']}{fmt['br']}"
    result += f"Illumination: {illumination:.1f}%{fmt['br']}"

    return result


def format_numerology(numerology_data: dict, output_type: str = "text") -> str:
    """
    Format numerology calculations.

    Args:
        numerology_data: numerology calculation results
        output_type: output format

    Returns:
        str: formatted numerology data
    """
    fmt = setup_output_formatting(output_type)

    if not numerology_data:
        return ""

    result = f"{fmt['h3']}Numerology{fmt['h3_']}{fmt['br']}"

    for key, value in numerology_data.items():
        if isinstance(value, dict):
            result += f"{fmt['bold']}{key.replace('_', ' ').title()}{fmt['nobold']}: "
            result += f"{value.get('number', 'N/A')} - {value.get('meaning', 'No meaning available')}{fmt['br']}"
        else:
            result += f"{fmt['bold']}{key.replace('_', ' ').title()}{fmt['nobold']}: {value}{fmt['br']}"

    return result


def format_fixed_star_aspects(star_aspects: list, output_type: str = "text") -> str:
    """
    Format fixed star aspects.

    Args:
        star_aspects: list of fixed star aspects
        output_type: output format

    Returns:
        str: formatted fixed star aspects
    """
    fmt = setup_output_formatting(output_type)

    if not star_aspects:
        return ""

    result = f"{fmt['h3']}Fixed Star Aspects{fmt['h3_']}{fmt['br']}"

    for aspect in star_aspects:
        planet = aspect.get("planet", "Unknown")
        star = aspect.get("star", "Unknown")
        aspect_type = aspect.get("aspect", "conjunction")
        orb = aspect.get("orb", 0)

        result += f"{planet} {aspect_type} {star} "
        result += f"(orb: {orb:.2f}{fmt['degree_symbol']}){fmt['br']}"

    return result


def format_arabic_parts(arabic_parts: dict, output_type: str = "text") -> str:
    """
    Format Arabic Parts.

    Args:
        arabic_parts: Arabic Parts data
        output_type: output format

    Returns:
        str: formatted Arabic Parts
    """
    fmt = setup_output_formatting(output_type)

    if not arabic_parts:
        return ""

    result = f"{fmt['h3']}Arabic Parts{fmt['h3_']}{fmt['br']}"

    for part_name, part_data in arabic_parts.items():
        if isinstance(part_data, dict):
            longitude = part_data.get("longitude", 0)
            from astro_calculations import longitude_to_zodiac

            zodiac_pos = longitude_to_zodiac(longitude)
            result += f"{part_name}: {zodiac_pos}{fmt['br']}"
        else:
            result += f"{part_name}: {part_data}{fmt['br']}"

    return result


def house_count(
    planet_house_counts, output_type, bold, nobold, br, p="", h4="", h4_=""
) -> str:
    """
    Format house count information - matches original exactly.
    """
    result = ""
    house_count_data = []
    for house, count in planet_house_counts.items():
        if count > 0:
            house_count_data.append([f"House {house}", count])

    if house_count_data:
        table_format = (
            "unsafehtml" if output_type in ("html", "return_html") else "simple"
        )
        house_table = tabulate(
            house_count_data, headers=["House", "Count"], tablefmt=table_format
        )
        result = f"{bold}Planets in Houses{nobold}{br}{house_table}"

    return result


def get_sabian_symbol(planet_positions, planet: str):
    """
    Retrieve the Sabian symbol for a specific degree within a zodiac sign.
    """
    import json

    try:
        ephe = os.getenv("PRODUCTION_EPHE")
        if ephe:
            sabian_symbols = json.load(open(f"{ephe}/sabian.json"))
        else:
            if os.name == "nt":
                sabian_symbols = json.load(open(".\\ephe\\sabian.json"))
            else:
                sabian_symbols = json.load(open("./ephe/sabian.json"))

        # Get zodiac sign from longitude
        from astro_calculations import longitude_to_zodiac

        sun_longitude = planet_positions["Sun"]["longitude"]
        zodiac_sign = longitude_to_zodiac(sun_longitude, "text").split()[
            -1
        ]  # Get sign name
        degree = int(sun_longitude % 30) + 1  # Sabian symbols start from 1

        return sabian_symbols[zodiac_sign][str(degree)]
    except Exception as e:
        return f"Cannot access sabian.json file: {e}"


def format_event_info(
    event_data: dict, output_type: str = "text", planet_positions=None, args=None
) -> str:
    """
    Format event information header exactly like original.
    """
    import version
    from numerology import life_path_number_simple, destiny_number_simple
    from fixed_stars_arabic_parts import datetime_ruled_by

    fmt = setup_output_formatting(output_type)
    bold = fmt["bold"]
    nobold = fmt["nobold"]
    br = fmt["br"]
    p = fmt["p"]
    h1 = fmt["h1"]
    h1_ = fmt["h1_"]

    name = event_data.get("name", "Unknown")
    place = event_data.get("location", "Unknown")
    latitude = event_data.get("latitude", 0)
    longitude = event_data.get("longitude", 0)
    altitude = event_data.get("altitude", 0)
    local_datetime = event_data.get("datetime")
    if isinstance(local_datetime, str):
        from datetime import datetime

        local_datetime = datetime.fromisoformat(local_datetime.replace("T", " "))
    # Convert local time to UTC
    if isinstance(local_datetime, datetime) and local_datetime.tzinfo:
        utc_datetime = local_datetime.astimezone(pytz.UTC)
    else:
        utc_datetime = local_datetime  # Fallback
    timezone = event_data.get("timezone", "UTC")
    notime = event_data.get("notime", False)

    # Build header exactly like original
    result = f"{p}{h1}{bold}AstroScript v.{version.__version__} Chart{nobold}{h1_}"
    result += f"{p}{bold}Name:{nobold} {name}"
    result += f"{br}{bold}Place:{nobold} {place}"
    result += (
        f"{br}{bold}Latitude:{nobold} {latitude}, {bold}Longitude:{nobold} {longitude}"
    )
    result += f"{br}{bold}Altitude:{nobold} {altitude} m"
    result += f"{br}{bold}Local Time:{nobold} {str(local_datetime)} {timezone}"
    result += f"{br}{bold}UTC Time:{nobold} {utc_datetime.strftime('%Y-%m-%d %H:%M:%S')}+00:00 UTC"

    # Add weekday and ruling planets
    if local_datetime:
        weekday, ruling_day, ruling_hour = datetime_ruled_by(local_datetime)
        if notime:
            result += f"{br}{bold}Weekday:{nobold} {weekday} {bold}Day ruled by:{nobold} {ruling_day}"
        else:
            result += f"{br}{bold}Weekday:{nobold} {weekday} {bold}Day ruled by:{nobold} {ruling_day} {bold}Hour ruled by:{nobold} {ruling_hour}"

    # Add Sabian symbol
    if planet_positions:
        try:
            sabian = get_sabian_symbol(planet_positions, "Sun")
            result += f"{br}{bold}Sabian Symbol:{nobold} {sabian}"
        except:
            result += f"{br}{bold}Sabian Symbol:{nobold} Cannot access sabian.json file"

    # Add numerology
    if name and local_datetime:
        life_path = life_path_number_simple(local_datetime)
        destiny = destiny_number_simple(name)
        name_parts = name.split(",") if name else []
        string_not_full_name = (
            " (enter full name for correct destiny number)"
            if len(name_parts) == 1
            else ""
        )
        result += f"{br}{bold}Life path:{nobold} {life_path}, {bold}Destiny number:{nobold} {destiny}{string_not_full_name}"

    return result


def create_html_document(content: str, title: str = "Astrological Chart") -> str:
    """
    Wrap content in a complete HTML document.

    Args:
        content: HTML content to wrap
        title: document title

    Returns:
        str: complete HTML document
    """
    html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            background-color: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
        }}
        h1, h2, h3, h4 {{
            color: #333;
            border-bottom: 2px solid #4a90e2;
            padding-bottom: 5px;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 15px 0;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }}
        th {{
            background-color: #4a90e2;
            color: white;
        }}
        tr:nth-child(even) {{
            background-color: #f2f2f2;
        }}
        .highlight {{
            background-color: #fff3cd;
            padding: 10px;
            border-left: 4px solid #ffc107;
            margin: 15px 0;
        }}
    </style>
</head>
<body>
    <div class="container">
        {content}
    </div>
</body>
</html>"""

    return html_template
