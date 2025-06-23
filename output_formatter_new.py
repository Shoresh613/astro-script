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
    Print the positions of planets in a human-readable format.
    Simplified version that focuses on HTML output compatibility with original.
    """
    from astro_calculations import longitude_to_zodiac

    fmt = setup_output_formatting(output_type)
    table_format = "unsafehtml" if output_type in ("html", "return_html") else "simple"

    # Build table data exactly like original
    table_data = []
    headers = ["Planet", "Zodiac", "Degree"]
    if not center == "heliocentric":
        headers.append("Retrograde" if output_type in ("html", "return_html") else "R")
    if house_positions and not notime and not center == "heliocentric":
        headers.append("House")

    for planet, info in planet_positions.items():
        if notime and planet in ["Ascendant", "Midheaven", "Descendant", "IC"]:
            continue

        longitude = info["longitude"]
        zodiac = longitude_to_zodiac(longitude).split()[0]  # Get sign name only
        degrees_within_sign = longitude % 30

        position = (
            coord_in_minutes(degrees_within_sign, output_type)
            if degree_in_minutes
            else f"{degrees_within_sign:.2f}{'' if (os.name == 'nt' and output_type == 'html') else '°'}"
        )

        if center == "heliocentric":
            row = [planet, zodiac, position]
        else:
            retrograde = info.get("retrograde", False)
            row = [planet, zodiac, position, retrograde]

        if house_positions and not notime and not center == "heliocentric":
            house_num = house_positions.get(planet, {}).get("house", "")
            row.append(house_num)

        table_data.append(row)

    # Generate table
    table = tabulate(table_data, headers=headers, tablefmt=table_format)

    if output_type in ("text", "html"):
        print(table)
        return ""
    else:
        return table


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


def format_event_info(event_data: dict, output_type: str = "text") -> str:
    """
    Format event information header.

    Args:
        event_data: event data dictionary
        output_type: output format

    Returns:
        str: formatted event information
    """
    fmt = setup_output_formatting(output_type)

    name = event_data.get("name", "Unknown")
    date_str = event_data.get("datetime", "")
    location = event_data.get("location", "Unknown")

    result = f"{fmt['h1']}{name}{fmt['h1_']}{fmt['br']}"
    result += f"Date: {date_str}{fmt['br']}"
    result += f"Location: {location}{fmt['br']}{fmt['br']}"

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
