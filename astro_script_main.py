#!/usr/bin/env python3
"""
AstroScript - Astrological Calculation Tool
Refactored version with modular components

This is the main entry point for the astrological calculation script.
The original monolithic file has been broken down into logical modules.
"""

import sys
import os
from datetime import datetime
import pytz

# Import our modular components
from cli_parser import argparser, validate_args, print_help
from astro_calculations import (
    calculate_planet_positions,
    calculate_house_positions,
    convert_to_utc,
    find_next_same_degree,
)
from aspect_analysis import (
    calculate_planetary_aspects,
    calculate_aspects_takes_two,
    find_exact_aspects_in_timeframe,
)
from chart_patterns import (
    find_t_squares,
    find_grand_trines,
    find_yod,
    find_grand_crosses,
    find_kites,
    assess_planet_strength,
)
from geo_time_utils import (
    get_coordinates,
    get_location_info,
    parse_date,
    list_common_timezones,
)
from data_manager import (
    load_event,
    save_event,
    create_event_data,
    list_saved_events,
    delete_event,
)
from numerology import calculate_all_numerology
from fixed_stars_arabic_parts import (
    calculate_aspects_to_fixed_stars,
    add_arabic_parts,
    moon_phase,
    datetime_ruled_by,
)
from output_formatter import (
    setup_output_formatting,
    format_planet_position,
    format_aspect_table,
    format_house_positions,
    format_chart_patterns,
    format_numerology,
    format_fixed_star_aspects,
    format_arabic_parts,
    format_moon_phase,
    create_html_document,
    format_event_info,
)

# Import constants
from constants import *

# Try to import version and db_manager
try:
    from . import version
    from . import db_manager
except ImportError:
    import version
    import db_manager

# Initialize database
db_manager.initialize_db()

# Default settings
DEFAULT_SETTINGS = {
    "timezone": "Europe/Stockholm",
    "latitude": 57.6828,
    "longitude": 11.9624,
    "altitude": 0,
    "location": "Göteborg, Sweden",
    "house_system": "P",
    "output_type": "text",
}

DEFAULT_ORBS = {"Major": 8, "Minor": 4, "Fixed": 2, "Asteroid": 2}


def get_progressed_datetime(input_date: datetime, input_value: str) -> datetime:
    """
    Calculate progressed datetime based on input value.

    Args:
        input_date: base datetime
        input_value: progression value (age, years, or date)

    Returns:
        datetime: progressed datetime
    """
    # This is a simplified version - implement full progression logic as needed
    try:
        # If it's a number, treat as years
        years = float(input_value)
        from datetime import timedelta

        return input_date + timedelta(days=years * 365.25)
    except ValueError:
        # Try to parse as date
        return parse_date(input_value)


def handle_utility_commands(args: dict) -> bool:
    """
    Handle utility commands that should exit immediately.

    Args:
        args: parsed arguments

    Returns:
        bool: True if a utility command was handled (should exit)
    """
    if args.get("List Timezones"):
        print("Available Timezones:")
        for tz in list_common_timezones():
            print(f"  {tz}")
        return True

    if args.get("List Events"):
        events = list_saved_events()
        if events:
            print("Saved Events:")
            for event in events:
                print(f"  {event}")
        else:
            print("No saved events found.")
        return True

    if args.get("Delete Event"):
        event_name = args["Delete Event"]
        if delete_event(event_name):
            print(f"Event '{event_name}' deleted successfully.")
        else:
            print(f"Failed to delete event '{event_name}'.")
        return True

    if args.get("Validate Location"):
        location = args["Validate Location"]
        info = get_location_info(location)
        if info:
            print(f"Location: {info['name']}")
            print(f"Coordinates: {info['latitude']:.4f}, {info['longitude']:.4f}")
            print(f"Altitude: {info['altitude']} meters")
            print(f"Timezone: {info['timezone']}")
        else:
            print(f"Could not find location: {location}")
        return True

    return False


def load_or_create_event_data(args: dict) -> dict:
    """
    Load existing event or create new event data from arguments.

    Args:
        args: parsed arguments

    Returns:
        dict: event data
    """
    name = args.get("Name", "")

    # Try to load existing event
    if name:
        guid = args.get("Guid")
        existing_event = load_event(name, guid)
        if existing_event:
            return existing_event

    # Create new event data from arguments
    event_data = {}

    # Handle date
    if args.get("Date"):
        if args["Date"] == "now":
            event_data["datetime"] = datetime.now()
        else:
            event_data["datetime"] = parse_date(args["Date"])
    else:
        event_data["datetime"] = datetime.now()  # Handle location
    if args.get("Location"):
        location_info = get_location_info(args["Location"])
        if location_info:
            event_data.update(location_info)
            # Copy name to location for display
            event_data["location"] = location_info["name"]
        else:
            raise ValueError(f"Could not find location: {args['Location']}")
    else:
        # Use provided coordinates or defaults
        event_data["latitude"] = args.get("Latitude", DEFAULT_SETTINGS["latitude"])
        event_data["longitude"] = args.get("Longitude", DEFAULT_SETTINGS["longitude"])
        event_data["altitude"] = args.get("Altitude", DEFAULT_SETTINGS["altitude"])
        event_data["location"] = args.get(
            "Location", DEFAULT_SETTINGS["location"]
        )  # Handle timezone - use location timezone if available, otherwise use argument or default
    if not event_data.get("timezone") or args.get("Timezone"):
        event_data["timezone"] = args.get("Timezone", DEFAULT_SETTINGS["timezone"])
    event_data["notime"] = args.get("Time Unknown", False)
    event_data["name"] = name or "Unnamed Event"

    return event_data


def calculate_chart_data(event_data: dict, args: dict) -> dict:
    """
    Calculate all chart data for an event.

    Args:
        event_data: event information
        args: calculation arguments

    Returns:
        dict: calculated chart data
    """
    # Get calculation parameters
    center = args.get("Center", "geocentric")
    house_system = args.get("House System", DEFAULT_SETTINGS["house_system"])

    # Convert to UTC
    local_datetime = event_data["datetime"]
    if isinstance(local_datetime, str):
        local_datetime = datetime.fromisoformat(local_datetime)

    local_timezone = pytz.timezone(event_data["timezone"])
    utc_datetime = convert_to_utc(local_datetime, local_timezone)

    # Calculate planet positions
    planet_positions = calculate_planet_positions(
        utc_datetime,
        event_data["latitude"],
        event_data["longitude"],
        event_data["altitude"],
        center,
    )

    # Calculate house positions
    house_cusps, ascendant, midheaven = calculate_house_positions(
        utc_datetime,
        event_data["latitude"],
        event_data["longitude"],
        event_data["altitude"],
        house_system,
        center,
    )

    # Calculate house positions for planets
    from astro_calculations import calculate_individual_house_position

    house_positions = {}
    for planet, position in planet_positions.items():
        if planet not in ["house_cusps"]:
            house_positions[planet] = calculate_individual_house_position(
                position["longitude"], house_cusps, house_system
            )

    # Calculate aspects
    orbs = {
        "Major": args.get("Orb Major", DEFAULT_ORBS["Major"]),
        "Minor": args.get("Orb Minor", DEFAULT_ORBS["Minor"]),
    }

    aspect_types = ["major"]
    if args.get("Minor Aspects"):
        aspect_types.append("minor")

    aspects = calculate_planetary_aspects(
        planet_positions, orbs, args.get("Output", "text"), aspect_types
    )
    # Detect chart patterns if requested
    patterns = []
    if args.get("Chart Patterns"):
        patterns.extend(find_t_squares(planet_positions))
        patterns.extend(find_grand_trines(planet_positions))
        patterns.extend(find_yod(planet_positions))
        patterns.extend(find_grand_crosses(planet_positions))
        patterns.extend(find_kites(planet_positions))

    # Calculate fixed star aspects if requested
    star_aspects = []
    if args.get("Fixed Stars"):
        import time

        jd = time.mktime(utc_datetime.timetuple()) / 86400.0 + 2440587.5
        star_aspects = calculate_aspects_to_fixed_stars(
            planet_positions, jd, orbs.get("Fixed", 2)
        )

    # Calculate Arabic parts if requested
    arabic_parts = {}
    if args.get("Arabic Parts"):
        arabic_parts = add_arabic_parts(
            utc_datetime,
            event_data["latitude"],
            event_data["longitude"],
            planet_positions,
            args.get("Output", "text"),
        )

    # Calculate moon phase
    moon_phase_data = moon_phase(utc_datetime)

    return {
        "planet_positions": planet_positions,
        "house_positions": house_positions,
        "house_cusps": house_cusps,
        "aspects": aspects,
        "patterns": patterns,
        "star_aspects": star_aspects,
        "arabic_parts": arabic_parts,
        "moon_phase": moon_phase_data,
        "utc_datetime": utc_datetime,
        "local_datetime": local_datetime,
        "local_timezone": local_timezone,
    }


def format_output(event_data: dict, chart_data: dict, args: dict) -> str:
    """
    Format all output exactly like original astro_script.py.

    Args:
        event_data: event information
        chart_data: calculated chart data
        args: formatting arguments

    Returns:
        str: formatted output matching original exactly
    """
    output_type = args.get("Output", "text")
    fmt = setup_output_formatting(output_type)

    result = ""  # Event information header (exactly like original)
    result += format_event_info(
        event_data, output_type, chart_data["planet_positions"], args
    )

    # Center, House system, Moon nodes line
    center = args.get("Center", "geocentric")
    house_system = args.get("House System", "Placidus")
    node_type = args.get("Node", "true")

    if center in ("geocentric", "topocentric"):
        result += f"{fmt['br']}{fmt['bold']}Center:{fmt['nobold']} {center.title()}, {fmt['bold']}House system:{fmt['nobold']} {house_system}, {fmt['bold']}Moon nodes:{fmt['nobold']} {node_type}{fmt['br']}"
    else:
        result += f"{fmt['br']}{fmt['bold']}Center:{fmt['nobold']} {center.title()}{fmt['br']}"

    # House cusps (if requested)
    if args.get("House Cusps"):
        house_cusps_str = ", ".join(
            [f"{cusp:.2f}°" for cusp in chart_data["house_cusps"]]
        )
        result += f"{fmt['p']}{fmt['bold']}House cusps:{fmt['nobold']} {house_cusps_str}{fmt['br']}"

    # Planetary Positions (comprehensive table with all analysis)
    if not args.get("Hide Planetary Positions"):
        result += f"{fmt['p']}{fmt['h3']}{fmt['bold']}Planetary Positions{fmt['nobold']}{fmt['h3_']}{fmt['br']}"

        # Use the comprehensive print_planet_positions function
        from output_formatter import print_planet_positions

        planet_positions_result = print_planet_positions(
            chart_data["planet_positions"],
            degree_in_minutes=args.get("Degree in Minutes", False),
            notime=event_data.get("notime", False),
            house_positions=chart_data["house_positions"],
            orb=args.get("Orb", 1),
            output_type=output_type,
            hide_decans=args.get("Hide Decans", False),
            classic_rulers=args.get("Classical Rulership", False),
            center=center,
            pluto_ecliptic=None,  # Would need to calculate this
        )
        result += planet_positions_result

    # Aspects (comprehensive with scoring and statistics)
    if not args.get("Hide Planetary Aspects") and chart_data["aspects"]:
        from output_formatter import print_aspects

        aspects_result = print_aspects(
            chart_data["aspects"],
            chart_data["planet_positions"],
            {"Major": args.get("Orb Major", 8), "Minor": args.get("Orb Minor", 4)},
            imprecise_aspects=args.get("Imprecise Aspects", "off"),
            minor_aspects=args.get("Minor Aspects", False),
            degree_in_minutes=args.get("Degree in Minutes", False),
            house_positions=chart_data["house_positions"],
            orb=args.get("Orb", 6),
            type="Natal",
            notime=event_data.get("notime", False),
            output=output_type,
            show_aspect_score=args.get("Show Score", False),
            complex_aspects=chart_data.get("patterns", {}),
            center=center,
        )
        result += aspects_result

    # Fixed star aspects (if enabled and available)
    if not args.get("Hide Fixed Star Aspects") and chart_data.get("star_aspects"):
        from output_formatter import print_fixed_star_aspects

        star_aspects_result = print_fixed_star_aspects(
            chart_data["star_aspects"],
            orb=args.get("Orb Fixed Star", 1),
            minor_aspects=args.get("Minor Aspects", False),
            imprecise_aspects=args.get("Imprecise Aspects", "off"),
            notime=event_data.get("notime", False),
            degree_in_minutes=args.get("Degree in Minutes", False),
            house_positions=chart_data["house_positions"],
            fixed_stars_data={},  # Would need to load this
            output_type=output_type,
            all_stars=args.get("All Stars", False),
            center=center,
        )
        result += star_aspects_result

    # Chart patterns (T-Squares, Grand Trines, etc.)
    if chart_data.get("patterns"):
        result += format_chart_patterns(chart_data["patterns"], output_type)

    # Arabic parts (if enabled)
    if chart_data.get("arabic_parts"):
        result += format_arabic_parts(chart_data["arabic_parts"], output_type)

    # Moon phase (if not heliocentric)
    if center != "heliocentric" and chart_data.get("moon_phase"):
        result += format_moon_phase(chart_data["moon_phase"], output_type)

    # Wrap in HTML document if needed
    if output_type == "html":
        result = create_html_document(result, f"Chart for {event_data['name']}")
    elif output_type == "return_html":
        result += "</div>"

    return result


def main(gui_arguments=None):
    """
    Main function for the astrological script.

    Args:
        gui_arguments: arguments from GUI (optional)

    Returns:
        str: formatted output
    """
    try:
        # Parse arguments
        if gui_arguments:
            args = gui_arguments
        else:
            args = argparser()

        # Validate arguments
        validation_errors = validate_args(args)
        if validation_errors:
            for error in validation_errors:
                print(f"Error: {error}")
            return "Invalid arguments provided."

        # Handle utility commands
        if handle_utility_commands(args):
            return ""

        # Load or create event data
        try:
            event_data = load_or_create_event_data(args)
        except Exception as e:
            print(f"Error loading event data: {e}")
            return f"Error loading event data: {e}"

        # Handle progressed charts
        if args.get("Progressed"):
            try:
                event_data["datetime"] = get_progressed_datetime(
                    event_data["datetime"], args["Progressed"]
                )
            except Exception as e:
                print(f"Error calculating progressed date: {e}")

        # Calculate chart data
        try:
            chart_data = calculate_chart_data(event_data, args)
        except Exception as e:
            print(f"Error calculating chart: {e}")
            return f"Error calculating chart: {e}"

        # Save event if requested
        save_name = args.get("Save As") or event_data.get("name")
        if save_name and save_name != "Unnamed Event":
            event_to_save = create_event_data(
                save_name,
                event_data["datetime"],
                event_data["latitude"],
                event_data["longitude"],
                event_data.get("altitude", 0),
                event_data["timezone"],
                event_data.get("location", ""),
                event_data.get("notime", False),
                args.get("Guid"),
            )
            save_event(event_to_save)

        # Format and return output
        output = format_output(event_data, chart_data, args)  # Print to console
        print(output)

        return output

    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        return "Operation cancelled."
    except Exception as e:
        print(f"Unexpected error: {e}")
        import traceback

        traceback.print_exc()
        return f"Unexpected error: {e}"


if __name__ == "__main__":
    main()
