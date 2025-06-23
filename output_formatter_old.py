"""
Output formatting functions for the astro script.
Contains functions for formatting text, HTML, and table output.
"""

import os
from tabulate import tabulate, SEPARATING_LINE
from datetime import datetime
from constants import *


def setup_output_formatting(output_type: str) -> dict:
    """
    Set up formatting variables based on output type.

    Args:
        output_type: output format ('text', 'html', 'json')

    Returns:
        dict: formatting variables
    """
    if output_type == "html":
        return {
            "bold": "<strong>",
            "nobold": "</strong>",
            "br": "<br>",
            "p": "<p>",
            "h1": "<h1>",
            "h2": "<h2>",
            "h3": "<h3>",
            "h4": "<h4>",
            "h1_": "</h1>",
            "h2_": "</h2>",
            "h3_": "</h3>",
            "h4_": "</h4>",
            "degree_symbol": "&deg;",
        }
    else:
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


def format_planet_position(
    planet: str,
    longitude: float,
    house: int = None,
    retrograde: bool = False,
    output_type: str = "text",
) -> str:
    """
    Format a planet position for display.

    Args:
        planet: planet name
        longitude: ecliptic longitude
        house: house number
        retrograde: whether planet is retrograde
        output_type: output format

    Returns:
        str: formatted planet position
    """
    from astro_calculations import longitude_to_zodiac

    fmt = setup_output_formatting(output_type)

    # Get zodiac position
    zodiac_pos = longitude_to_zodiac(longitude, output_type)

    # Add retrograde indicator
    retro_symbol = " ℞" if retrograde else ""

    # Add house if provided
    house_info = f" in {house}H" if house else ""

    return f"{planet}: {zodiac_pos}{retro_symbol}{house_info}"


def format_aspect_table(
    aspects: dict,
    planet_positions: dict,
    output_type: str = "text",
    include_scores: bool = False,
    type_label: str = "Natal",
) -> str:
    """
    Format aspects as a table.

    Args:
        aspects: aspect data
        planet_positions: planet position data
        output_type: output format
        include_scores: whether to include aspect scores
        type_label: type of aspects (Natal, Transit, etc.)

    Returns:
        str: formatted aspect table
    """
    if not aspects:
        return "No aspects found."

    fmt = setup_output_formatting(output_type)

    # Prepare table headers
    headers = ["Planet 1", "Aspect", "Planet 2", "Orb"]
    if include_scores:
        headers.append("Score")

    # Prepare table data
    table_data = []
    for (planet1, planet2), aspect_info in aspects.items():
        row = [
            planet1,
            aspect_info["aspect_name"],
            planet2,
            f"{aspect_info['angle_diff']:.2f}{fmt['degree_symbol']}",
        ]

        if include_scores:
            row.append(f"{aspect_info.get('score', 0):.1f}")

        table_data.append(row)

    # Sort by aspect strength/score if available
    if include_scores:
        table_data.sort(key=lambda x: float(x[-1]), reverse=True)

    # Format table
    if output_type == "html":
        table_html = tabulate(table_data, headers=headers, tablefmt="html")
        return f"{fmt['h3']}{type_label} Aspects{fmt['h3_']}\n{table_html}"
    else:
        table_text = tabulate(table_data, headers=headers, tablefmt="grid")
        return f"{fmt['bold']}{type_label} Aspects{fmt['nobold']}\n{table_text}"


def format_house_positions(
    planet_positions: dict, house_positions: dict, output_type: str = "text"
) -> str:
    """
    Format house positions for display.

    Args:
        planet_positions: planet position data
        house_positions: house position data
        output_type: output format

    Returns:
        str: formatted house positions
    """
    fmt = setup_output_formatting(output_type)

    # Group planets by house
    houses = {}
    for planet, position in planet_positions.items():
        if planet in ["house_cusps"]:
            continue

        house = house_positions.get(planet)
        if house:
            if house not in houses:
                houses[house] = []
            houses[house].append(planet)

    # Format output
    result = f"{fmt['h3']}Houses{fmt['h3_']}\n"

    for house_num in range(1, 13):
        if house_num in houses:
            planets = ", ".join(houses[house_num])
            result += f"{fmt['bold']}House {house_num}:{fmt['nobold']} {planets}\n"
        else:
            result += f"{fmt['bold']}House {house_num}:{fmt['nobold']} (empty)\n"

    return result


def format_chart_patterns(patterns: list, output_type: str = "text") -> str:
    """
    Format chart patterns for display.

    Args:
        patterns: list of detected patterns
        output_type: output format

    Returns:
        str: formatted patterns
    """
    if not patterns:
        return "No significant chart patterns detected."

    fmt = setup_output_formatting(output_type)
    result = f"{fmt['h3']}Chart Patterns{fmt['h3_']}\n"

    for pattern in patterns:
        pattern_type = pattern.get("type", "Unknown")
        result += f"{fmt['bold']}{pattern_type}{fmt['nobold']}\n"

        if pattern_type == "T-Square":
            opp = " - ".join(pattern["opposition"])
            apex = pattern["apex"]
            result += f"  Opposition: {opp}\n"
            result += f"  Apex: {apex}\n"

        elif pattern_type == "Grand Trine":
            planets = " - ".join(pattern["planets"])
            result += f"  Planets: {planets}\n"

        elif pattern_type == "Yod":
            sextile = " - ".join(pattern["sextile"])
            apex = pattern["apex"]
            result += f"  Sextile: {sextile}\n"
            result += f"  Apex: {apex}\n"

        elif pattern_type == "Kite":
            trine = " - ".join(pattern["grand_trine"])
            focal = pattern["focal_planet"]
            result += f"  Grand Trine: {trine}\n"
            result += f"  Focal Planet: {focal}\n"

        result += "\n"

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

    phase_name = phase_info.get("phase", "Unknown")
    illumination = phase_info.get("illumination", 0)

    result = f"{fmt['h4']}Moon Phase{fmt['h4_']}\n"
    result += f"Phase: {fmt['bold']}{phase_name}{fmt['nobold']}\n"
    result += f"Illumination: {fmt['bold']}{illumination:.1f}%{fmt['nobold']}\n"

    return result


def format_numerology(numerology_data: dict, output_type: str = "text") -> str:
    """
    Format numerology information.

    Args:
        numerology_data: numerology calculation results
        output_type: output format

    Returns:
        str: formatted numerology
    """
    fmt = setup_output_formatting(output_type)

    result = f"{fmt['h3']}Numerology{fmt['h3_']}\n"

    for category, data in numerology_data.items():
        if isinstance(data, dict):
            number = data.get("number", 0)
            interpretation = data.get("interpretation", "")

            category_title = category.replace("_", " ").title()
            result += f"{fmt['bold']}{category_title}: {number}{fmt['nobold']}\n"
            result += f"  {interpretation}\n\n"

    return result


def format_fixed_star_aspects(star_aspects: list, output_type: str = "text") -> str:
    """
    Format fixed star aspects.

    Args:
        star_aspects: list of star aspect data
        output_type: output format

    Returns:
        str: formatted star aspects
    """
    if not star_aspects:
        return "No significant fixed star aspects found."

    fmt = setup_output_formatting(output_type)

    headers = ["Planet", "Aspect", "Fixed Star", "Orb"]
    table_data = []

    for aspect in star_aspects:
        row = [
            aspect.get("planet", ""),
            aspect.get("aspect", ""),
            aspect.get("star", ""),
            f"{aspect.get('orb', 0):.2f}{fmt['degree_symbol']}",
        ]
        table_data.append(row)

    if output_type == "html":
        table_html = tabulate(table_data, headers=headers, tablefmt="html")
        return f"{fmt['h3']}Fixed Star Aspects{fmt['h3_']}\n{table_html}"
    else:
        table_text = tabulate(table_data, headers=headers, tablefmt="grid")
        return f"{fmt['bold']}Fixed Star Aspects{fmt['nobold']}\n{table_text}"


def format_arabic_parts(arabic_parts: dict, output_type: str = "text") -> str:
    """
    Format Arabic parts information.

    Args:
        arabic_parts: Arabic parts data
        output_type: output format

    Returns:
        str: formatted Arabic parts
    """
    if not arabic_parts:
        return "No Arabic parts calculated."

    fmt = setup_output_formatting(output_type)
    from astro_calculations import longitude_to_zodiac

    result = f"{fmt['h3']}Arabic Parts{fmt['h3_']}\n"

    for part_name, longitude in arabic_parts.items():
        zodiac_pos = longitude_to_zodiac(longitude, output_type)
        result += f"{fmt['bold']}{part_name}:{fmt['nobold']} {zodiac_pos}\n"

    return result


def house_count(
    house_counts: dict, output_type: str, bold: str, nobold: str, br: str
) -> str:
    """
    Format house count statistics.

    Args:
        house_counts: dictionary of house counts
        output_type: output format
        bold, nobold, br: formatting strings

    Returns:
        str: formatted house count
    """
    if not house_counts or all(count == 0 for count in house_counts.values()):
        return ""

    result = f"{br}{bold}Planetary Distribution by House:{nobold}{br}"

    for house in range(1, 13):
        count = house_counts.get(house, 0)
        if count > 0:
            result += f"House {house}: {count} planet{'s' if count > 1 else ''}{br}"

    return result


def format_event_info(event_data: dict, output_type: str = "text") -> str:
    """
    Format event information header.

    Args:
        event_data: event data dictionary
        output_type: output format

    Returns:
        str: formatted event info
    """
    fmt = setup_output_formatting(output_type)

    name = event_data.get("name", "Unknown")
    date = event_data.get("datetime", "")
    location = event_data.get("location", "")
    timezone = event_data.get("timezone", "")

    result = f"{fmt['h1']}Astrological Chart for {name}{fmt['h1_']}\n"
    result += f"{fmt['bold']}Date:{fmt['nobold']} {date}\n"
    result += f"{fmt['bold']}Location:{fmt['nobold']} {location}\n"
    result += f"{fmt['bold']}Timezone:{fmt['nobold']} {timezone}\n\n"

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


def coord_in_minutes(longitude, output_type):
    """
    Convert a celestial longitude into degrees, minutes, and seconds format.
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
    Print the positions of planets in a human-readable format exactly like the original.
    """
    # Import required functions
    from chart_patterns import assess_planet_strength, is_planet_elevated, check_degree

    sign_counts = {sign: {"count": 0, "planets": []} for sign in ZODIAC_ELEMENTS.keys()}
    modality_counts = {
        modality: {"count": 0, "planets": []} for modality in ZODIAC_MODALITIES.keys()
    }
    element_counts = {"Fire": 0, "Earth": 0, "Air": 0, "Water": 0}
    planet_house_counts = {house: 0 for house in range(1, 13)}

    zodiac_table_data = []

    if output_type in ("html", "return_html"):
        table_format = "unsafehtml"
        bold = "<b>"
        nobold = "</b>"
        br = "\n<br>"
        p = "\n<p>"
    elif output_type == "text":
        table_format = "simple"
        bold = "\033[1m"
        nobold = "\033[0m"
        br = "\n"
        p = "\n"
    else:
        table_format = "simple"
        bold = ""
        nobold = ""
        br = "\n"
        p = "\n"

    degree_symbol = (
        "" if (os.name == "nt" and output_type == "html") else "°"
    )  # If running on Windows, don't use degree symbol for html output

    # Define headers based on whether house positions should be included
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
        headers.insert(3, "Off by")    if not hide_decans:
        headers.append(
            "Decan ruler" if output_type in ("html", "return_html") else "Decan"
        )

    planet_signs = {}
    planet_degrees = {}

    for planet, info in planet_positions.items():
        if notime and (planet in ALWAYS_EXCLUDE_IF_NO_TIME):
            continue
        longitude = info["longitude"]
        
        # Import longitude_to_zodiac function
        from astro_calculations import longitude_to_zodiac
        zodiac = longitude_to_zodiac(longitude).split()[0]  # Get just the sign name
        
        degrees_within_sign = longitude % 30
        position = (
            coord_in_minutes(degrees_within_sign, output_type)
            if degree_in_minutes
            else f"{degrees_within_sign:.2f}{degree_symbol}"
        )
        retrograde = info["retrograde"]
        retrograde_status = retrograde  # "R" if retrograde else ""
        decan_ruler = info.get("decan_ruled_by", "")

        planet_signs[planet] = zodiac
        planet_degrees[planet] = degrees_within_sign
        
        strength_check = assess_planet_strength(planet_signs, classic_rulers)
        elevation_check = is_planet_elevated(planet_positions)
        degree_check = check_degree(planet_signs, planet_degrees)

        if (
            not notime and not center == "heliocentric"
        ):  # assuming that we have the house positions if not notime
            house_num = house_positions.get(planet, {}).get("house", "Unknown")
            planet_positions[planet] = house_num
            if house_num:
                planet_house_counts[house_num] += 1

        if center == "heliocentric":
            row = [planet, zodiac, position]
        else:
            row = [planet, zodiac, position, retrograde_status]

        if notime and planet in OFF_BY.keys() and OFF_BY[planet] > orb:
            off_by = f"±{OFF_BY[planet]}{degree_symbol}"
            row.insert(3, off_by)
        elif notime:
            off_by = ""
            row.insert(3, off_by)
        if house_positions and not notime and not center == "heliocentric":
            house_num = house_positions.get(planet, {}).get("house", "Unknown")
            row.insert(4, house_num)
        row.append(
            elevation_check[planet]
            + strength_check[planet]
            + degree_check[planet]
            + (f" {pluto_ecliptic}" if planet == "Pluto" else "")
        )
        if not hide_decans:
            row.append(decan_ruler)

        if (planet == "Fortune" or planet == "Ascendant") and output_type in (
            "text",
            "return_text",
        ):
            zodiac_table_data.append(SEPARATING_LINE)
        zodiac_table_data.append(row)

        # Count zodiac signs, elements and modalities
        sign_counts[zodiac]["count"] += 1
        sign_counts[zodiac]["planets"].append(planet)
        modality = ZODIAC_SIGN_TO_MODALITY[zodiac]
        modality_counts[modality]["count"] += 1
        modality_counts[modality]["planets"].append(planet)
        element_counts[ZODIAC_ELEMENTS[zodiac]] += 1

    table_format = "unsafehtml" if output_type in ("html", "return_html") else "simple"

    to_return = ""
    table = tabulate(
        zodiac_table_data, headers=headers, tablefmt=table_format, floatfmt=".2f"
    )

    if output_type in ("text", "html"):
        print(table)
    to_return += table

    sign_count_table_data = list()
    element_count_table_data = list()
    modality_count_table_data = list()    ## House counts
    if not notime and not center == "heliocentric":
        if output_type in ("return_text", "return_html"):
            to_return += f"{p}" + house_count(
                planet_house_counts, output_type, bold, nobold, br
            )
        else:
            print(
                f"{p}" + house_count(planet_house_counts, output_type, bold, nobold, br)
            )
