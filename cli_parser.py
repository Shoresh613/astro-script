"""
Command line interface parser for the astro script.
Contains argument parsing functionality and CLI-specific classes.
"""

import argparse
from datetime import datetime


class ReturnAction(argparse.Action):
    """Custom action for handling return calculations."""

    def __call__(self, parser, namespace, values, option_string=None):
        if len(values) != 2:
            raise argparse.ArgumentTypeError(
                "Returns requires exactly 2 arguments: DIRECTION PLANET"
            )

        direction, planet = values
        direction = direction.lower()

        if direction not in ["prev", "previous", "next"]:
            raise argparse.ArgumentTypeError(
                "Direction must be 'prev', 'previous', or 'next'"
            )

        # Convert direction to standard format
        if direction in ["prev", "previous"]:
            direction = "previous"

        setattr(namespace, self.dest, {"direction": direction, "planet": planet})


class ProgressedAction(argparse.Action):
    """Custom action for handling progressed chart calculations."""

    def __call__(self, parser, namespace, values, option_string=None):
        if not values:
            raise argparse.ArgumentTypeError("Progressed requires a value")

        # Parse progressed value (could be age, date, or years)
        progressed_value = values[0] if isinstance(values, list) else values

        setattr(namespace, self.dest, progressed_value)


def argparser():
    """
    Create and configure the argument parser for the astro script.

    Returns:
        dict: parsed arguments as dictionary
    """
    parser = argparse.ArgumentParser(
        description="""Astrological calculation script.
        
If no arguments are passed, values entered in the script will be used.
If a name is passed, the script will look up the record for that name in the database/JSON file 
and overwrite other passed values, provided there are such values stored.
If no record is found, default values will be used.""",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    # Basic information
    parser.add_argument(
        "--name",
        help="Name to look up the record for. Will auto save event using this name, if not already saved.",
        required=False,
    )

    parser.add_argument(
        "--date",
        help="Date of the event (YYYY-MM-DD HH:MM local time). Use 'now' for current time.",
        required=False,
    )

    parser.add_argument(
        "--location",
        type=str,
        help='Name of location for coordinate lookup, e.g. "Stockholm, Sweden".',
        required=False,
    )

    parser.add_argument(
        "--latitude",
        type=float,
        help="Latitude of the location in degrees, e.g. 57.6828.",
        required=False,
    )

    parser.add_argument(
        "--longitude",
        type=float,
        help="Longitude of the location in degrees, e.g. 11.96.",
        required=False,
    )

    parser.add_argument(
        "--altitude",
        type=float,
        help="Altitude of the location in meters.",
        required=False,
        default=0,
    )

    parser.add_argument(
        "--timezone",
        help='Timezone of the location (e.g. "Europe/Stockholm"). See --list_timezones for options.',
        required=False,
    )

    # Time and calculation options
    parser.add_argument(
        "--time_unknown",
        action="store_true",
        help="Whether the exact time is unknown (affects house calculations and aspects).",
    )

    parser.add_argument(
        "--LMT",
        action="store_true",
        help="Indicates that the specified time is in Local Mean Time (pre-standardized timezones).",
    )

    parser.add_argument(
        "--center",
        choices=["geocentric", "heliocentric"],
        default="geocentric",
        help="Center of calculations (default: geocentric).",
    )

    parser.add_argument(
        "--house_system",
        choices=["P", "K", "O", "R", "C", "A", "V", "W", "X", "H", "T", "B", "M"],
        default="P",
        help="House system to use (P=Placidus, K=Koch, etc.). Default: Placidus.",
    )

    # Output options
    parser.add_argument(
        "--output",
        choices=["text", "html", "json"],
        default="text",
        help="Output format (default: text).",
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output with additional details.",
    )

    parser.add_argument(
        "--degree_in_minutes",
        action="store_true",
        help="Display coordinates in degrees and minutes format.",
    )

    # Aspect options
    parser.add_argument(
        "--major_aspects_only",
        action="store_true",
        help="Show only major aspects (conjunction, opposition, trine, square, sextile).",
    )

    parser.add_argument(
        "--minor_aspects",
        action="store_true",
        help="Include minor aspects in calculations.",
    )

    parser.add_argument(
        "--aspect_scores",
        action="store_true",
        help="Show aspect scores in output.",
    )

    parser.add_argument(
        "--orb_major",
        type=float,
        default=8.0,
        help="Orb for major aspects in degrees (default: 8.0).",
    )

    parser.add_argument(
        "--orb_minor",
        type=float,
        default=4.0,
        help="Orb for minor aspects in degrees (default: 4.0).",
    )

    # Advanced calculations
    parser.add_argument(
        "--transits",
        help="Calculate transits for the specified date. Format: YYYY-MM-DD HH:MM",
        required=False,
    )

    parser.add_argument(
        "--transits_location",
        help="Location for transit calculations (if different from natal).",
        required=False,
    )

    parser.add_argument(
        "--synastry",
        help="Calculate synastry with another saved event (specify name).",
        required=False,
    )

    parser.add_argument(
        "--returns",
        nargs=2,
        action=ReturnAction,
        metavar=("DIRECTION", "PLANET"),
        help="Calculate the next or previous return of the named planet. Format: next/prev PLANET",
    )

    parser.add_argument(
        "--progressed",
        nargs=1,
        action=ProgressedAction,
        metavar="VALUE",
        help="Calculate progressed chart. Value can be age, date, or years from birth.",
    )

    # Special features
    parser.add_argument(
        "--fixed_stars",
        action="store_true",
        help="Include fixed star aspects in calculations.",
    )

    parser.add_argument(
        "--asteroids",
        action="store_true",
        help="Include asteroid calculations.",
    )

    parser.add_argument(
        "--arabic_parts",
        action="store_true",
        help="Calculate Arabic parts (Lot of Fortune, Spirit, etc.).",
    )

    parser.add_argument(
        "--chart_patterns",
        action="store_true",
        help="Detect chart patterns (T-squares, Grand Trines, etc.).",
    )

    parser.add_argument(
        "--numerology",
        action="store_true",
        help="Include numerology calculations (Life Path, Destiny numbers, etc.).",
    )

    # Data management
    parser.add_argument(
        "--save_as",
        help="Store event using the specified name.",
        required=False,
    )

    parser.add_argument(
        "--guid",
        help="GUID for specific event lookup/storage.",
        required=False,
    )

    parser.add_argument(
        "--list_events",
        action="store_true",
        help="List all saved events and exit.",
    )

    parser.add_argument(
        "--delete_event",
        help="Delete the specified saved event.",
        required=False,
    )

    # Utility options
    parser.add_argument(
        "--list_timezones",
        action="store_true",
        help="List all available timezones and exit.",
    )

    parser.add_argument(
        "--validate_location",
        help="Validate and show information for the specified location.",
        required=False,
    )

    # Davison relationship chart
    parser.add_argument(
        "--davison",
        type=str,
        nargs="+",
        metavar="EVENT",
        help="Create a Davison relationship chart from two or more saved events.",
        required=False,
    )

    # Parse arguments and convert to dictionary
    args = parser.parse_args()

    # Convert Namespace to dictionary for easier handling
    args_dict = {}
    for key, value in vars(args).items():
        # Convert argument names to match existing code expectations
        if key == "time_unknown":
            args_dict["Time Unknown"] = value
        elif key == "major_aspects_only":
            args_dict["Major Aspects Only"] = value
        elif key == "minor_aspects":
            args_dict["Minor Aspects"] = value
        elif key == "aspect_scores":
            args_dict["Aspect Scores"] = value
        elif key == "fixed_stars":
            args_dict["Fixed Stars"] = value
        elif key == "arabic_parts":
            args_dict["Arabic Parts"] = value
        elif key == "chart_patterns":
            args_dict["Chart Patterns"] = value
        elif key == "degree_in_minutes":
            args_dict["Degree in Minutes"] = value
        elif key == "list_timezones":
            args_dict["List Timezones"] = value
        elif key == "list_events":
            args_dict["List Events"] = value
        elif key == "delete_event":
            args_dict["Delete Event"] = value
        elif key == "validate_location":
            args_dict["Validate Location"] = value
        elif key == "save_as":
            args_dict["Save As"] = value
        elif key == "house_system":
            args_dict["House System"] = value
        elif key == "orb_major":
            args_dict["Orb Major"] = value
        elif key == "orb_minor":
            args_dict["Orb Minor"] = value
        elif key == "transits_location":
            args_dict["Transits Location"] = value
        else:
            # Capitalize first letter for other arguments
            args_dict[key.capitalize()] = value

    return args_dict


def print_help():
    """Print help information for the script."""
    parser = argparse.ArgumentParser()
    argparser()  # This will set up the parser
    parser.print_help()


def validate_args(args_dict: dict) -> list:
    """
    Validate command line arguments.

    Args:
        args_dict: parsed arguments dictionary

    Returns:
        list: list of validation errors (empty if valid)
    """
    errors = []

    # Validate coordinate ranges
    if args_dict.get("Latitude") is not None:
        lat = args_dict["Latitude"]
        if not (-90 <= lat <= 90):
            errors.append("Latitude must be between -90 and 90 degrees")

    if args_dict.get("Longitude") is not None:
        lon = args_dict["Longitude"]
        if not (-180 <= lon <= 180):
            errors.append("Longitude must be between -180 and 180 degrees")

    # Validate orb values
    if args_dict.get("Orb Major", 0) < 0:
        errors.append("Major aspect orb must be positive")

    if args_dict.get("Orb Minor", 0) < 0:
        errors.append("Minor aspect orb must be positive")

    # Validate date format if provided
    if args_dict.get("Date") and args_dict["Date"] != "now":
        try:
            from geo_time_utils import parse_date

            parse_date(args_dict["Date"])
        except ValueError as e:
            errors.append(f"Invalid date format: {e}")

    return errors
