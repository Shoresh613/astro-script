import argparse
import copy
import json
import os
import sys
from datetime import datetime, timedelta

import pytz
import swisseph as swe
from colorama import Fore, Style, init
from geopy.geocoders import Nominatim
from tabulate import SEPARATING_LINE, tabulate

import db_manager
import version

from .config import EPHE, TimezoneFinder, tz_finder_installed
from .constants import *
from .coords import *
from .numerology import *
from .time_utils import *
from .geo import *
from .houses import *
from .dignity import *
from .positions import *
from .fixed_stars import *
from .arabic_parts import *
from .aspects import *
from .output import *
from .events import *
from .returns import *

def set_orbs(args, def_orbs):
    # Set orbs to default if not specified
    orbs = {}

    # Blanket orb setting if "orb" is specified
    if args["Orb"]:
        orbs.update(
            {
                "Orb": args["Orb"],
                "Major": args["Orb"],
                "Minor": args["Orb"],
                "Fixed Star": args["Orb"],
                "Asteroid": args["Orb"],
                "Transit Fast": args["Orb"],
                "Transit Slow": args["Orb"],
                "Synastry Fast": args["Orb"],
                "Synastry Slow": args["Orb"],
            }
        )
        return orbs
    else:
        orbs.update(
            {
                "Major": (
                    args["Orb Major"] if args["Orb Major"] else def_orbs["Orb Major"]
                ),
                "Minor": (
                    args["Orb Minor"] if args["Orb Minor"] else def_orbs["Orb Minor"]
                ),
                "Fixed Star": (
                    args["Orb Fixed Star"]
                    if args["Orb Fixed Star"]
                    else def_orbs["Orb Fixed Star"]
                ),
                "Asteroid": (
                    args["Orb Asteroid"]
                    if args["Orb Asteroid"]
                    else def_orbs["Orb Asteroid"]
                ),
                "Transit Fast": (
                    args["Orb Transit Fast"]
                    if args["Orb Transit Fast"]
                    else def_orbs["Orb Transit Fast"]
                ),
                "Transit Slow": (
                    args["Orb Transit Slow"]
                    if args["Orb Transit Slow"]
                    else def_orbs["Orb Transit Slow"]
                ),
                "Synastry Fast": (
                    args["Orb Synastry Fast"]
                    if args["Orb Synastry Fast"]
                    else def_orbs["Orb Synastry Fast"]
                ),
                "Synastry Slow": (
                    args["Orb Synastry Slow"]
                    if args["Orb Synastry Slow"]
                    else def_orbs["Orb Synastry Slow"]
                ),
            }
        )

        return orbs


def called_by_gui(
    name,
    date,
    location,
    latitude,
    longitude,
    timezone,
    time_unknown,
    lmt,
    list_timezones,
    returns,
    save_as,
    davison,
    place,
    imprecise_aspects,
    minor_aspects,
    show_brief_aspects,
    show_score,
    show_arabic_parts,
    aspects_to_arabic_parts,
    classical,
    orb,
    orb_major,
    orb_minor,
    orb_fixed_star,
    orb_asteroid,
    orb_transit_fast,
    orb_transit_slow,
    orb_synastry_fast,
    orb_synastry_slow,
    degree_in_minutes,
    node,
    center,
    all_stars,
    house_system,
    house_cusps,
    hide_planetary_positions,
    hide_planetary_aspects,
    hide_fixed_star_aspects,
    hide_asteroid_aspects,
    hide_decans,
    transits,
    transits_timezone,
    transits_location,
    synastry,
    progressed,
    remove_saved_names,
    store_defaults,
    use_saved_settings,
    output_type,
    guid,
):

    if isinstance(date, datetime):
        date = date.strftime("%Y-%m-%d %H:%M")

    arguments = {
        "Name": name,
        "Date": date,
        "Location": location,
        "Latitude": latitude,
        "Longitude": longitude,
        "Timezone": timezone,
        "Time Unknown": time_unknown,
        "LMT": lmt,
        "List Timezones": list_timezones,
        "Return": returns,
        "Save As": save_as,
        "Davison": davison,
        "Place": place,
        "Imprecise Aspects": imprecise_aspects,
        "Minor Aspects": minor_aspects,
        "Show Brief Aspects": show_brief_aspects,
        "Show Score": show_score,
        "Arabic Parts": show_arabic_parts,
        "Aspects To Arabic Parts": aspects_to_arabic_parts,
        "Classical Rulership": classical,
        "Orb": orb,
        "Orb Major": orb_major,
        "Orb Minor": orb_minor,
        "Orb Fixed Star": orb_fixed_star,
        "Orb Asteroid": orb_asteroid,
        "Orb Transit Fast": orb_transit_fast,
        "Orb Transit Slow": orb_transit_slow,
        "Orb Synastry Fast": orb_synastry_fast,
        "Orb Synastry Slow": orb_synastry_slow,
        "Degree in Minutes": degree_in_minutes,
        "Node": node,
        "Center": center,
        "All Stars": all_stars,
        "House System": house_system,
        "House Cusps": house_cusps,
        "Hide Planetary Positions": hide_planetary_positions,
        "Hide Planetary Aspects": hide_planetary_aspects,
        "Hide Fixed Star Aspects": hide_fixed_star_aspects,
        "Hide Asteroid Aspects": hide_asteroid_aspects,
        "Hide Decans": hide_decans,
        "Transits": transits,
        "Transits Timezone": transits_timezone,
        "Transits Location": transits_location,
        "Synastry": synastry,
        "Progressed": progressed,
        "Saved Names": None,
        "Save Settings": store_defaults,
        "Use Saved Settings": use_saved_settings,
        "Output": output_type,
        "Remove Saved Names": remove_saved_names,
        "Guid": guid if guid else None,
    }

    print(arguments)
    text = main(arguments)
    return text


class ReturnAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        if (
            len(values) != 2
            or values[0] not in ["prev", "next"]
            or values[1]
            not in [
                "Sun",
                "Moon",
                "Mercury",
                "Venus",
                "Earth",
                "Mars",
                "Jupiter",
                "Saturn",
                "Uranus",
                "Neptune",
                "Pluto",
            ]
        ):
            parser.error(
                f"The {self.dest} argument must be followed by 'prev' or 'next' and then a valid planet name."
            )
        setattr(namespace, self.dest, values)


class ProgressedAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        if values == "now":
            setattr(namespace, self.dest, values)
        else:
            try:
                int_value = int(values)
                if int_value <= 1 or int_value >= 361:
                    raise ValueError
            except ValueError:
                parser.error(
                    f"The {self.dest} argument must be 'now' or an integer between 1 and 360."
                )

            setattr(namespace, self.dest, int_value)


def argparser():
    parser = argparse.ArgumentParser(
        description="""If no arguments are passed, values entered in the script will be used.
If a name is passed, the script will look up the record for that name in the JSON file and overwrite other passed values,
provided there are such values stored in the file (only the first 6 types are stored). 
If no record is found, default values will be used.""",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    parser.add_argument(
        "--name",
        help="Name to look up the record for. Will auto save event using this name, if not already saved.",
        required=False,
    )
    parser.add_argument(
        "--date",
        help="Date of the event (YYYY-MM-DD HH:MM local time). (Default: None)",
        required=False,
    )
    parser.add_argument(
        "--location",
        type=str,
        help='Name of location for lookup of coordinates, e.g. "Sahlgrenska, Göteborg, Sweden". (Default: "Sahlgrenska")',
        required=False,
    )
    parser.add_argument(
        "--latitude",
        type=float,
        help="Latitude of the location in degrees, e.g. 57.6828. (Default: 57.6828)",
        required=False,
    )
    parser.add_argument(
        "--longitude",
        type=float,
        help="Longitude of the location in degrees, e.g. 11.96. (Default: 11.9624)",
        required=False,
    )
    parser.add_argument(
        "--timezone",
        help='Timezone of the location (e.g. "Europe/Stockholm"). See README.md for all available tz. (Default: "Europe/Stockholm")',
        required=False,
    )
    parser.add_argument(
        "--time_unknown",
        action="store_true",
        help="Whether the exact time is unknown (affects e.g. house calculations).",
    )
    parser.add_argument(
        "--LMT",
        action="store_true",
        help="Indicates that the specified time is in Local Mean Time (pre standardized timezones). Still requires a timezone for the location, unless TimezoneFinder is installed.",
    )
    parser.add_argument(
        "--list_timezones",
        action="store_true",
        help="Prints all available timezones. Overrides all other arguments if specified.",
    )
    parser.add_argument(
        "--returns",
        nargs=2,
        action=ReturnAction,
        metavar=("DIRECTION", "PLANET"),
        help="Calculate the next or previous return of the named planet to a given datetime or saved named event. Format: prev/next PLANET",
    )
    parser.add_argument(
        "--save_as",
        help="Store event using the name specified here. Useful for returns, and e.g. being able to check for synastry with the natal chart.",
        required=False,
    )
    parser.add_argument(
        "--davison",
        type=str,
        nargs="+",
        metavar="EVENT",
        help="A Davison relationship chart requires at least two saved events (e.g. \"John, 'Jane Smith'\").",
        required=False,
    )
    parser.add_argument(
        "--place",
        help="Name of location without lookup of coordinates. (Default: None)",
        required=False,
    )
    parser.add_argument(
        "--imprecise_aspects",
        choices=["off", "warn"],
        help='Whether to not show imprecise aspects or just warn. (Default: "warn")',
        required=False,
    )
    parser.add_argument(
        "--minor_aspects", action="store_true", help="Show minor aspects."
    )
    parser.add_argument(
        "--brief_aspects",
        action="store_true",
        help="Show brief aspects for transits, i.e. Asc, MC, DC, Desc.",
    )
    parser.add_argument(
        "--score",
        action="store_true",
        help="Show ease of individual aspects (0 not easy, 50 neutral, 100 easy).",
    )
    parser.add_argument(
        "--arabic_parts", action="store_true", help="Show Arabic parts."
    )
    parser.add_argument(
        "--aspects_to_arabic_parts",
        action="store_true",
        help="Include aspects to Arabic parts. Requires --arabic_parts.",
    )
    parser.add_argument(
        "--classical",
        action="store_true",
        help="Use classical sign rulership, as before discovery of modern planets.",
    )
    parser.add_argument(
        "--orb",
        type=float,
        help="Orb size in degrees. Overrides all orb settings if specified. Use for blanket orb setting.",
        required=False,
    )
    parser.add_argument(
        "--orb_major",
        type=float,
        help="Orb size in degrees for major aspects. (Default: 6.0)",
        required=False,
    )
    parser.add_argument(
        "--orb_minor",
        type=float,
        help="Orb size in degrees for minor aspects. (Default: 3.0)",
        required=False,
    )
    parser.add_argument(
        "--orb_fixed_star",
        type=float,
        help="Orb size in degrees for fixed star aspects. (Default: 1.0)",
        required=False,
    )
    parser.add_argument(
        "--orb_asteroid",
        type=float,
        help="Orb size in degrees for asteroid aspects. (Default: 1.5)",
        required=False,
    )
    parser.add_argument(
        "--orb_transit_fast",
        type=float,
        help="Orb size in degrees for fast-moving planet transits. (Default: 1.5)",
        required=False,
    )
    parser.add_argument(
        "--orb_transit_slow",
        type=float,
        help="Orb size in degrees for slow-moving planet transits. (Default: 1.0)",
        required=False,
    )
    parser.add_argument(
        "--orb_synastry_fast",
        type=float,
        help="Orb size in degrees for fast-moving planet synastry. (Default: 1.5)",
        required=False,
    )
    parser.add_argument(
        "--orb_synastry_slow",
        type=float,
        help="Orb size in degrees for slow-moving planet synastry. (Default: 1.0)",
        required=False,
    )
    parser.add_argument(
        "--degree_in_minutes",
        action="store_true",
        help="Show degrees in arch minutes and seconds. (Default: false)",
    )
    parser.add_argument(
        "--node",
        choices=["mean", "true"],
        help='Whether to use the moon mean node or true node. (Default: "true")',
        required=False,
    )
    parser.add_argument(
        "--center",
        choices=["heliocentric", "geocentric", "topocentric"],
        help="Choose center of calculations (default: topocentric).",
    )
    parser.add_argument(
        "--all_stars",
        action="store_true",
        help="Show aspects for all fixed stars. (Default: false)",
    )
    parser.add_argument(
        "--house_system",
        choices=list(HOUSE_SYSTEMS.keys()),
        help='House system to use (Placidus, Koch etc). (Default: "Placidus")',
        required=False,
    )
    parser.add_argument(
        "--house_cusps",
        action="store_true",
        help="Whether to show house cusps or not. (Default: false)",
    )
    parser.add_argument(
        "--hide_planetary_positions",
        action="store_true",
        help="Output: hide what signs and houses (if time specified) planets are in. (Default: false)",
    )
    parser.add_argument(
        "--hide_planetary_aspects",
        action="store_true",
        help="Output: hide aspects planets are in. (Default: false)",
    )
    parser.add_argument(
        "--hide_fixed_star_aspects",
        action="store_true",
        help="Output: hide aspects planets are in to fixed stars. (Default: false)",
    )
    parser.add_argument(
        "--hide_asteroid_aspects",
        action="store_true",
        help="Output: hide aspects planets are in to asteroids. (Default: false)",
    )
    parser.add_argument(
        "--hide_decans",
        action="store_true",
        help="Hide the planet ruling the decan of the planet positions. (Default: false)",
    )
    parser.add_argument(
        "--transits",
        help="Date of the transit event ('YYYY-MM-DD HH:MM' local time, 'now' for current time). (Default: None)",
        required=False,
    )
    parser.add_argument(
        "--transits_timezone",
        help='Timezone of the transit location (e.g. "Europe/Stockholm"). See README.md for all available tz. (Default: "Europe/Stockholm")',
        required=False,
    )
    parser.add_argument(
        "--transits_location",
        type=str,
        help='Name of location for lookup of transit coordinates, e.g. "Göteborg, Sweden". (Default: "Göteborg")',
        required=False,
    )
    parser.add_argument(
        "--synastry",
        help="Name of the stored event (or person) with which to calculate synastry for the person specified under --name. (Default: None)",
        required=False,
    )
    parser.add_argument(
        "--progressed",
        help='Days to progress the natal chart, or "now" for the current year',
        action=ProgressedAction,
        required=False,
    )
    parser.add_argument(
        "--saved_names",
        action="store_true",
        help="List names previously saved using --name. If set, all other arguments are ignored. (Default: false)",
    )
    parser.add_argument(
        "--remove_saved_names",
        type=str,
        nargs="+",
        metavar="EVENT",
        help="Remove saved events (e.g. \"John, 'Jane Smith'\"). If set, all other arguments are ignored. (except --saved_names)",
        required=False,
    )
    parser.add_argument(
        "--save_settings",
        type=str,
        nargs="?",
        const="default",
        help='Store settings as defaults <name>. If no name passed will be stored as "default"',
        required=False,
    )
    parser.add_argument(
        "--use_saved_settings",
        nargs="?",
        const="default",
        type=str,
        help='Use settings specified by name <name>. If no name passed will use "default"',
        required=False,
    )
    parser.add_argument(
        "--output_type",
        choices=["text", "return_text", "html", "return_html"],
        help='Output: Print text or html to stdout, or return text or html. (Default: "text")',
        required=False,
    )

    args = parser.parse_args()

    if args.davison and len(args.davison) < 2:
        parser.error("--davison requires at least two named events.")

    arguments = {
        "Name": args.name,
        "Date": args.date,
        "Location": args.location,
        "Latitude": args.latitude,
        "Longitude": args.longitude,
        "Timezone": args.timezone,
        "Time Unknown": args.time_unknown,
        "LMT": args.LMT,
        "List Timezones": args.list_timezones,
        "Return": args.returns,
        "Save As": args.save_as,
        "Davison": args.davison,
        "Place": args.place,
        "Imprecise Aspects": args.imprecise_aspects,
        "Minor Aspects": args.minor_aspects,
        "Show Brief Aspects": args.brief_aspects,
        "Show Score": args.score,
        "Arabic Parts": args.arabic_parts,
        "Aspects To Arabic Parts": args.aspects_to_arabic_parts,
        "Classical Rulership": args.classical,
        "Orb": args.orb,
        "Orb Major": args.orb_major,
        "Orb Minor": args.orb_minor,
        "Orb Fixed Star": args.orb_fixed_star,
        "Orb Asteroid": args.orb_asteroid,
        "Orb Transit Fast": args.orb_transit_fast,
        "Orb Transit Slow": args.orb_transit_slow,
        "Orb Synastry Fast": args.orb_synastry_fast,
        "Orb Synastry Slow": args.orb_synastry_slow,
        "Degree in Minutes": args.degree_in_minutes,
        "Node": args.node,
        "Center": args.center,
        "All Stars": args.all_stars,
        "House System": args.house_system,
        "House Cusps": args.house_cusps,
        "Hide Planetary Positions": args.hide_planetary_positions,
        "Hide Planetary Aspects": args.hide_planetary_aspects,
        "Hide Fixed Star Aspects": args.hide_fixed_star_aspects,
        "Hide Asteroid Aspects": args.hide_asteroid_aspects,
        "Hide Decans": args.hide_decans,
        "Transits": args.transits,
        "Transits Timezone": args.transits_timezone,
        "Transits Location": args.transits_location,
        "Synastry": args.synastry,
        "Progressed": args.progressed,
        "Saved Names": args.saved_names,
        "Remove Saved Names": args.remove_saved_names,
        "Save Settings": args.save_settings,
        "Use Saved Settings": args.use_saved_settings,
        "Output": args.output_type,
        "Guid": None,
    }

    return arguments


def main(gui_arguments=None):
    if gui_arguments:
        args = gui_arguments
    else:
        args = argparser()

    local_datetime = datetime.now()  # Default date now

    # Check if name was provided as argument
    name = args["Name"] if args["Name"] else ""
    to_return = ""

    #################### Load event ####################
    if args["Guid"]:
        exists = load_event(name, args["Guid"]) if name else False
    else:
        exists = load_event(name) if name else False
    if exists:
        local_datetime = datetime.fromisoformat(exists["datetime"])
        latitude = exists["latitude"]
        longitude = exists["longitude"]
        altitude = exists["altitude"]
        local_timezone = pytz.timezone(exists["timezone"])
        notime = True if exists["notime"] in ("1", 1, "true") else False
        place = exists["location"]
    else:
        if args["Return"]:
            print("No valid event specified for return.")
            return "No valid event specified for return."
        notime = args["Time Unknown"]

    try:
        if args["Date"]:
            if args["Date"] == "now":
                if EPHE:
                    local_datetime = datetime.now()
                    local_timezone = pytz.timezone("UTC")
                else:
                    local_datetime = datetime.now()
            else:
                local_datetime = parse_date(args["Date"])
    except ValueError:
        print("Invalid date format. Please use YYYY-MM-DD HH:MM.")
        local_datetime = None
        return "Invalid date format. Please use YYYY-MM-DD HH:MM."

    try:
        if args["Progressed"]:
            local_datetime = get_progressed_datetime(local_datetime, args["Progressed"])
    except ValueError:
        pass

    if args["Center"]:
        center_of_calculations = args["Center"]
    else:
        center_of_calculations = "topocentric"

    if center_of_calculations == "heliocentric":
        PLANETS.pop("North Node", None)
        PLANETS.pop("South Node", None)
        PLANETS.pop("Lilith", None)
        PLANETS.pop("Sun", None)
        PLANETS.pop("Moon", None)
        PLANETS.update({"Earth": swe.EARTH})
        hide_fixed_star_aspects = True

    try:
        if args["Return"]:
            if not args["Name"]:
                print("No named event specified for return.")
                return "No named event specified for return."
            # convert to utc
            utc_datetime = convert_localtime_in_lmt_to_utc(local_datetime, longitude)
            nextprev = args["Return"][0]
            returning_planet = args["Return"][1]
            return_utc_datetime = find_next_same_degree(
                utc_datetime,
                returning_planet,
                longitude,
                latitude,
                altitude,
                nextprev,
                center_of_calculations,
            )
            if not return_utc_datetime:
                return "No return found for specified planet."
    except ValueError:
        print("Planet not found.")
        return "Planet not found."

    ######### Default settings if no arguments are passed #########
    def_tz = pytz.timezone("Europe/Stockholm")  # Default timezone
    def_transits_tz = pytz.timezone("Europe/Stockholm")  # Default timezone
    def_place_name = "Sahlgrenska"  # Default place
    def_transits_location = "Göteborg"  # Default transit location
    def_lat = 57.6828  # Default latitude
    def_long = 11.9624  # Default longitude
    def_alt = 0  # Default altitude
    def_imprecise_aspects = "warn"  # Default imprecise aspects ["off", "warn"]
    def_minor_aspects = False  # Default minor aspects
    def_show_brief_aspects = False  # Default brief aspects
    def_show_score = False  # Default minor aspects

    def_orbs = {
        "Orb": 1,  # General default orb size
        "Orb Major": 6.0,  # Default orb size for major aspects
        "Orb Minor": 1.5,  # Default orb size for minor aspects
        "Orb Fixed Star": 1.0,  # Default orb size for fixed star aspects
        "Orb Asteroid": 1.5,  # Default orb size for fixed star aspects
        "Orb Transit Fast": 1.5,  # Default orb size for fast-moving planet transits
        "Orb Transit Slow": 1.0,  # Default orb size for slow-moving planet transits
        "Orb Synastry Fast": 3.0,  # Default orb size for fast-moving planet synastry
        "Orb Synastry Slow": 2.0,  # Default orb size for slow-moving planet synastry
    }

    def_degree_in_minutes = False  # Default degree in minutes
    def_node = "true"  # Default node (true node is more accurate than mean node)
    def_all_stars = False  # Default only astrologically known stars
    def_house_cusps = False  # Default do not show house cusps
    def_output_type = "text"  # Default output type

    # Default Output settings
    hide_planetary_positions = False
    hide_planetary_aspects = False
    hide_fixed_star_aspects = False
    hide_asteroid_aspects = False
    show_transits = False
    show_synastry = False

    # Store defaults if requested
    if args["Save Settings"]:
        defaults_to_store = {
            "Name": args["Save Settings"],
            "GUID": args["Guid"] if args["Guid"] else None,
            "Location": args["Location"] if args["Location"] else None,
            "Timezone": args["Timezone"] if args["Timezone"] else None,
            "LMT": args["LMT"] if args["LMT"] else None,
            "Imprecise Aspects": (
                args["Imprecise Aspects"] if args["Imprecise Aspects"] else None
            ),
            "Minor Aspects": args["Minor Aspects"] if args["Minor Aspects"] else None,
            "Show Brief Aspects": (
                args["Show Brief Aspects"] if args["Show Brief Aspects"] else None
            ),
            "Show Score": args["Show Score"] if args["Show Score"] else None,
            "Orb": args["Orb"] if args["Orb"] else None,
            "Orb Major": args["Orb Major"] if args["Orb Major"] else None,
            "Orb Minor": args["Orb Minor"] if args["Orb Minor"] else None,
            "Orb Fixed Star": (
                args["Orb Fixed Star"] if args["Orb Fixed Star"] else None
            ),
            "Orb Asteroid": args["Orb Asteroid"] if args["Orb Asteroid"] else None,
            "Orb Transit Fast": (
                args["Orb Transit Fast"] if args["Orb Transit Fast"] else None
            ),
            "Orb Transit Slow": (
                args["Orb Transit Slow"] if args["Orb Transit Slow"] else None
            ),
            "Orb Synastry Fast": (
                args["Orb Synastry Fast"] if args["Orb Synastry Fast"] else None
            ),
            "Orb Synastry Slow": (
                args["Orb Synastry Slow"] if args["Orb Synastry Slow"] else None
            ),
            "Degree in Minutes": (
                args["Degree in Minutes"] if args["Degree in Minutes"] else None
            ),
            "Node": args["Node"] if args["Node"] else None,
            "Arabic Parts": args["Arabic Parts"] if args["Arabic Parts"] else None,
            "All Stars": args["All Stars"] if args["All Stars"] else None,
            "House System": args["House System"] if args["House System"] else None,
            "House Cusps": args["House Cusps"] if args["House Cusps"] else None,
            "Hide Planetary Positions": (
                args["Hide Planetary Positions"]
                if args["Hide Planetary Positions"]
                else None
            ),
            "Hide Planetary Aspects": (
                args["Hide Planetary Aspects"]
                if args["Hide Planetary Aspects"]
                else None
            ),
            "Hide Fixed Star Aspects": (
                args["Hide Fixed Star Aspects"]
                if args["Hide Fixed Star Aspects"]
                else None
            ),
            "Hide Asteroid Aspects": (
                args["Hide Asteroid Aspects"] if args["Hide Asteroid Aspects"] else None
            ),
            "Hide Decans": args["Hide Decans"] if args["Hide Decans"] else None,
            "Transits Timezone": (
                args["Transits Timezone"] if args["Transits Timezone"] else None
            ),
            "Transits Location": (
                args["Transits Location"] if args["Transits Location"] else None
            ),
            "Output": args["Output"] if args["Output"] else None,
        }

        db_manager.store_defaults(defaults_to_store)
        print(f"Settings stored with the name '{args['Save Settings']}'.")

        if EPHE:
            return f"Defaults saved."
        else:
            return f"Settings stored with the name '{args['Save Settings']}'."

    # Override using stored settings (default or specified name)
    stored_defaults = db_manager.read_defaults(
        args["Use Saved Settings"] if args["Use Saved Settings"] else "default",
        args["Guid"] if args["Guid"] else "",
    )

    if stored_defaults:
        keys = [
            "Location",
            "Timezone",
            "LMT",
            "Imprecise Aspects",
            "Minor Aspects",
            "Show Brief Aspects",
            "Show Score",
            "Orb",
            "Orb Major",
            "Orb Minor",
            "Orb Fixed Star",
            "Orb Asteroid",
            "Orb Transit Fast",
            "Orb Transit Slow",
            "Orb Synastry Fast",
            "Orb Synastry Slow",
            "Degree in Minutes",
            "Arabic Parts",
            "Node",
            "All Stars",
            "House System",
            "House Cusps",
            "Hide Planetary Positions",
            "Hide Planetary Aspects",
            "Hide Fixed Star Aspects",
            "Hide Asteroid Aspects",
            "Transits Timezone",
            "Transits Location",
            "Output",
        ]

        for key in keys:
            if stored_defaults.get(key):
                args[key] = stored_defaults.get(key)

    if args["Location"]:
        place = args["Location"]
        latitude, longitude, altitude = get_coordinates(args["Location"])
        if latitude is None or longitude is None:
            location_error_string = (
                f"Location not found, please check the spelling"
                + " and internet connection."
                if not EPHE
                else ""
            )
            les_html = f""" <!DOCTYPE html> <html> <head> <meta 
	charset="UTF-8"> <meta name="viewport" 
	content="width=device-width, initial-scale=1.0"> 
	</head> <body> 
	<div><p>{location_error_string}</p></div> </body> 
	</html>"""
            if args["Output"] == "html":
                print(les_html)
            elif args["Output"] == "return_html":
                return les_html
            elif args["Output"] == "return_text":
                return location_error_string
            else:
                print(location_error_string)
            return
        if args["Center"] == "heliocentric":
            altitude = None
        else:
            altitude = get_altitude(latitude, longitude, place)
    elif args["Place"]:
        place = args["Place"]
    elif not exists:
        place = def_place_name

    if not args["Location"] and not exists:
        latitude = args["Latitude"] if args["Latitude"] is not None else def_lat
        longitude = args["Longitude"] if args["Longitude"] is not None else def_long
        # longitude = args["Altitude"] if args["Altitude"] is not None else def_alt
        altitude = get_altitude(def_lat, def_long, def_place_name)

    if not exists:
        if args["Timezone"]:
            try:
                local_timezone = pytz.timezone(args["Timezone"])
            except:
                print("Invalid timezone")
                return "Invalid timezone"
        elif tz_finder_installed:

            tf = TimezoneFinder()
            timezone_name = tf.timezone_at(lng=longitude, lat=latitude)

            if timezone_name:
                local_timezone = pytz.timezone(timezone_name)
            else:
                print(
                    "Could not determine the timezone automatically. Please specify the timezone using --timezone."
                )
                local_timezone = def_tz
        else:
            local_timezone = def_tz

    def_house_system = (
        HOUSE_SYSTEMS["Placidus"]
        if abs(latitude) < 66
        else HOUSE_SYSTEMS["Equal (Ascendant cusp 1)"]
    )  # Default house system

    ephemeris_restriction_date = datetime(
        675, 1, 4, 12, 0
    )  # Ephemeris data for Chiron is available from 675 AD
    if local_datetime < ephemeris_restriction_date:
        PLANETS.pop("Chiron")

    # If "off", the script will not show such aspects, if "warn" print a warning for uncertain aspects
    imprecise_aspects = (
        args["Imprecise Aspects"]
        if args["Imprecise Aspects"]
        else def_imprecise_aspects
    )
    # If True, the script will include minor aspects
    minor_aspects = True if args["Minor Aspects"] else def_minor_aspects
    orbs = set_orbs(args, def_orbs)
    orb = float(args["Orb"]) if args["Orb"] else def_orbs["Orb"]
    # If True, the script will show the positions in degrees and minutes
    degree_in_minutes = True if args["Degree in Minutes"] else def_degree_in_minutes
    node = "mean" if args["Node"] and args["Node"].lower() in ["mean"] else def_node
    if node == "mean":
        PLANETS["North Node"] = swe.MEAN_NODE
    if node == "true":
        PLANETS["North Node"] = swe.TRUE_NODE

    # If True, the script will include all roughly 600 fixed stars
    all_stars = True if args["All Stars"] else def_all_stars
    h_sys = (
        HOUSE_SYSTEMS[args["House System"]]
        if args["House System"]
        else def_house_system
    )
    h_sys_changed = False
    if (
        h_sys not in ("A", "E", "V") and abs(latitude) >= 66
    ):  # The house systems safe for closer to the poles
        h_sys = def_house_system
        h_sys_changed = f"House system {args['House System']} not supported at latitudes above |66°|. Reverting to Equal house system."

    if args["House System"] and args["House System"] not in HOUSE_SYSTEMS:
        print(
            f"Invalid house system. Available house systems are: {', '.join(HOUSE_SYSTEMS.keys())}"
        )
        h_sys = def_house_system  # Reverting to default house system if invalid
    show_house_cusps = True if args["House Cusps"] else def_house_cusps

    show_brief_aspects = def_show_brief_aspects  # code follows
    if args["Show Brief Aspects"]:
        show_brief_aspects = True
    show_score = def_show_score
    if args["Show Score"]:
        show_score = True

    output_type = args["Output"] if args["Output"] else def_output_type

    if args["List Timezones"]:
        to_return = "Available timezones:\n"
        for tz in pytz.all_timezones:
            to_return += f"{tz}\n"
        if output_type in ("text", "html"):
            print(to_return)
            return
        else:
            return to_return

    if args["Remove Saved Names"]:
        to_return = db_manager.remove_saved_names(
            args["Remove Saved Names"],
            output_type,
            guid=args["Guid"] if args["Guid"] else None,
        )
        if output_type in ("text", "html"):
            print(to_return)
        if not args["Saved Names"]:
            return to_return

    if args["Saved Names"]:
        names = db_manager.read_saved_names()
        if output_type in ("text", "html"):
            print("Names stored in db:")
            for name in names:
                print(f"{name}")
        else:
            to_return += "Names stored in db:\n\n"
            for name in names:
                to_return += f"{name}"
        return to_return

    if output_type == "html":
        print(
            """
<!DOCTYPE html>
    <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>AstroScript Chart</title>\n
            <style>
                body {
                    font-family: Arial, sans-serif;
                    color: #333;
                    background-color: #f4f4f4;
                    margin: 0px;
                    padding-left: 8px;
                    padding-right: 8px;
                }

                h1, h2, h3 {
                    color: #35424a;
                    margin-bottom: 1em;
                    line-height: 1.3;
                }

                h1 {
                    font-size: 2.5rem; /* Responsive font size */
                }
                h2 {
                    font-size: 2.0rem;
                }
                h3 {
                    font-size: 1.75rem;
                }
                p {
                    font-size: 1.2rem;
                    line-height: 1.6;
                }

                th, td {
                    padding: 8px 10px;
                    text-align: left;
                    border-bottom: 1px solid #ddd;
                }

                th {
                    background-color: #35424a;
                    color: white;
                }

                img {
                    max-height: 90vh;   /* vh unit represents a percentage of the viewport height */
                    width: auto;        /* Maintains the aspect ratio of the image */
                    display: block;
                }
                .table-container {
                    display: flex;
                    flex-wrap: wrap;
                    justify-content: space-around; /* This will space out the tables evenly */
                    align-items: flex-start; /* Aligns tables to the top */
                }
                .content-block {
                    margin-bottom: 20px; /* Separation between different blocks */
                }
                table {
                    width: auto;
                    margin-top: 20px;
                    border-collapse: collapse;
                    display: block;
                    flex: 1 1 300px; /* Flex-grow, flex-shrink, and base width */
                    margin: 10px; /* Adds some space between tables */
                    max-width: 100%; /* Ensures table does not overflow its container */
                    // overflow-x: auto; /* Allows horizontal scrolling if needed */
                    display: block;
                }
                .stack-vertical {
                    flex: 0 0 100%; /* Forces the table to take up 100% width of the flex container */
                    margin: 10px 0; /* Vertical margin for spacing, no horizontal margins */
                }

                @media (max-width: 768px) {
                    .table-container {
                        flex-direction: column;
                    }
                }
            </style>
        </head>
        <body>"""
        )
    if output_type in ("html", "return_html"):
        bold = "<b>"
        nobold = "</b>"
        br = "\n<br>"
        p = "\n<p>"
        h1 = "<h1>"
        h2 = "<h2>"
        h3 = "<h3>"
        h1_ = "</h1>"
        h2_ = "</h2>"
        h3_ = "</h3>"
    elif output_type == "text":
        bold = "\033[1m"
        nobold = "\033[0m"
        br = "\n"
        p = "\n"
        h1 = ""
        h2 = ""
        h3 = ""
        h1_ = ""
        h2_ = ""
        h3_ = ""
    else:
        bold = ""
        nobold = ""
        br = "\n"
        p = "\n"
        h1 = ""
        h2 = ""
        h3 = ""
        h1_ = ""
        h2_ = ""
        h3_ = ""

    if args["Hide Planetary Positions"]:
        if args["Hide Planetary Positions"]:
            hide_planetary_positions = True
    if args["Hide Planetary Aspects"]:
        if args["Hide Planetary Aspects"]:
            hide_planetary_aspects = True
    if args["Hide Fixed Star Aspects"]:
        if args["Hide Fixed Star Aspects"]:
            hide_fixed_star_aspects = True
    if args["Hide Asteroid Aspects"]:
        if args["Hide Asteroid Aspects"]:
            hide_asteroid_aspects = True

    if args["Arabic Parts"]:
        show_arabic_parts = True
    else:
        show_arabic_parts = False

    if args["Davison"]:
        utc_datetime, longitude, latitude, altitude = get_davison_data(args["Davison"])
        place = "Davison chart"
        local_timezone = pytz.utc
        local_datetime = utc_datetime
    else:
        if place == "Davison chart":
            utc_datetime = local_datetime
        else:
            if args["LMT"]:  # If the time is Local Mean Time already
                utc_datetime = convert_localtime_in_lmt_to_utc(
                    local_datetime, longitude
                )
            elif args["Return"]:
                utc_datetime = return_utc_datetime
            else:
                utc_datetime = convert_to_utc(local_datetime, local_timezone)

    if args["Transits"]:
        if args["Transits Timezone"]:
            local_transits_timezone = pytz.timezone(args["Transits Timezone"])
        else:
            local_transits_timezone = def_transits_tz

        if args["Transits Location"]:
            transits_location = args["Transits Location"]
        else:
            transits_location = def_transits_location
        transits_latitude, transits_longitude, transits_altitude = get_coordinates(
            transits_location
        )

        if transits_latitude is None or transits_longitude is None:
            location_error_string = f"Transit location '{transits_location}' not found, please check the spelling and internet connection."
            print(location_error_string)
            return location_error_string

        transits_altitude = get_altitude(
            transits_latitude, transits_longitude, transits_location
        )

        if args["Transits"] == "now":
            transits_local_datetime = datetime.now()
            transits_utc_datetime = convert_to_utc(
                transits_local_datetime, local_transits_timezone
            )
            show_transits = True
        else:
            try:
                if EPHE:
                    transits_local_datetime = args["Transits"]
                else:
                    transits_local_datetime = datetime.strptime(
                        args["Transits"], "%Y-%m-%d %H:%M"
                    )
            except ValueError:
                print(
                    "Invalid transit date format. Please use YYYY-MM-DD HH:MM (00:00 for time if unknown).\nEnter 'now' for current time (UTC).",
                    file=sys.stderr,
                )
                return "Invalid transit date format. Please use YYYY-MM-DD HH:MM (00:00 for time if unknown).\nEnter 'now' for current time (UTC)."
            transits_utc_datetime = convert_to_utc(
                transits_local_datetime, local_transits_timezone
            )

            show_transits = True
        # only show transits, not the rest
        hide_asteroid_aspects = True
        hide_fixed_star_aspects = True
        hide_planetary_aspects = True
        hide_planetary_positions = True

        if args["Center"]:
            center_of_calculations = args["Center"]
        else:
            center_of_calculations = "geocentric"  # defaulting to geocentric calculations as swisseph does not report speed of planets in other modes

    if args["Synastry"]:
        try:
            exists = load_event(
                args["Synastry"], args["Guid"] if args["Guid"] else None
            )
            if exists:
                synastry_local_datetime = datetime.fromisoformat(exists["datetime"])
                synastry_latitude = exists["latitude"]
                synastry_longitude = exists["longitude"]
                synastry_altitude = exists["altitude"]

                if exists["timezone"] == "LMT":
                    synastry_local_timezone == "LMT"
                else:
                    synastry_local_timezone = pytz.timezone(exists["timezone"])
                synastry_place = exists["location"]
                synastry_utc_datetime = convert_to_utc(
                    synastry_local_datetime, synastry_local_timezone
                )
                synastry_notime = True if exists["notime"] else False
                show_synastry = True
                hide_planetary_positions = True
                hide_planetary_aspects = True
                hide_fixed_star_aspects = True
                hide_asteroid_aspects = True
        except:
            print("Invalid second event for synastry", file=sys.stderr)
            return "Invalid second event for synastry."

    # Save event if name given and not already stored
    if name and not exists:
        db_manager.update_event(
            name,
            place,
            local_datetime.isoformat(),
            str(local_timezone),
            latitude,
            longitude,
            altitude,
            notime,
            guid=args["Guid"] if args["Guid"] else None,
        )
    if args["Save As"]:
        db_manager.update_event(
            args["Save As"],
            place,
            (
                utc_datetime + utc_datetime.astimezone(local_timezone).utcoffset()
            ).isoformat(),
            str(local_timezone),
            latitude,
            longitude,
            altitude,
            notime,
            guid=args["Guid"] if args["Guid"] else None,
        )

    #################### Main Script ####################
    # Initialize Colorama, calculations for strings
    init()
    house_system_name = next(
        (name for name, code in HOUSE_SYSTEMS.items() if code == h_sys), None
    )
    planet_positions = calculate_planet_positions(
        utc_datetime,
        latitude,
        longitude,
        altitude,
        output_type,
        h_sys,
        "planets",
        center_of_calculations,
        show_arabic_parts,
        classic_rulers=args["Classical Rulership"],
    )
    house_positions, house_cusps = calculate_house_positions(
        utc_datetime,
        latitude,
        longitude,
        altitude,
        copy.deepcopy(planet_positions),
        notime,
        HOUSE_SYSTEMS[house_system_name],
    )

    complex_aspects = {}
    complex_aspects["T Squares"] = find_t_squares(
        copy.deepcopy(planet_positions), orb_opposition=6, orb_square=5
    )
    complex_aspects["Yods"] = find_yod(
        copy.deepcopy(planet_positions), orb_opposition=6, orb_square=5
    )
    complex_aspects["Grand Crosses"] = find_grand_crosses(
        copy.deepcopy(planet_positions), orb=5
    )
    complex_aspects["Grand Trines"] = find_grand_trines(
        copy.deepcopy(planet_positions), orb=5
    )
    complex_aspects["Kites"] = find_kites(copy.deepcopy(planet_positions), orb=5)

    moon_phase_name1, illumination1 = moon_phase(utc_datetime)
    moon_phase_name2, illumination2 = moon_phase(utc_datetime + timedelta(days=1))
    pluto_ecliptic = get_pluto_ecliptic(utc_datetime)

    if notime:
        illumination = f"{illumination1:.2f}-{illumination2:.2f}%"
    else:
        moon_phase_name, illumination = moon_phase(utc_datetime)
        illumination = f"{illumination:.2f}%"

    weekday, ruling_day, ruling_hour = datetime_ruled_by(local_datetime)
    if show_synastry:
        weekday_synastry, ruling_day_synastry, ruling_hour_synastry = datetime_ruled_by(
            synastry_utc_datetime
        )

    string_heading = (
        f"{p}{h1}{bold}AstroScript v.{version.__version__} Chart{nobold}{h1_}"
    )
    string_planets_heading = f"{p}{h3}{bold}Planetary Positions{nobold}{h3_}"
    string_name = f"{p}{bold}Name:{nobold} {name}".rstrip(", ")
    string_place = f"{br}{bold}Place:{nobold} {place}"
    string_latitude_in_minutes = (
        f"{br}{bold}Latitude:{nobold} {coord_in_minutes(latitude, output_type)}"
    )
    string_longitude_in_minutes = (
        f"{bold}Longitude:{nobold} {coord_in_minutes(longitude, output_type)}"
    )
    string_latitude = f"{br}{bold}Latitude:{nobold} {latitude}"
    string_longitude = f"{bold}Longitude:{nobold} {longitude}"
    string_altitude = f"{br}{bold}Altitude:{nobold} {altitude} m"
    string_davison_noname = "Davison chart"
    string_progressed = (
        f"{br}{bold}Progressed chart:{nobold} {args['Progressed']}"
        if args["Progressed"]
        else ""
    )

    if args["Name"] or exists:
        if len(args["Name"].split(",")) == 1:
            string_not_full_name = " (enter full name for correct destiny number)"
        else:
            string_not_full_name = ""

        string_numerology = (
            f"{br}{bold}Life path:{nobold} {life_path_number(utc_datetime)}, {bold}Destiny number:{nobold} {destiny_number(name)}"
            + string_not_full_name
        )
    else:
        string_numerology = (
            f"{br}{bold}Life path:{nobold} {life_path_number(utc_datetime)}"
        )

    if args["Name"] and args["Davison"]:
        string_davison = f"{br}{bold}Davison chart of:{nobold} {', '.join(args['Davison'])}. Stored as new event: {args['Name']}"
    elif args["Davison"]:
        string_davison = (
            f"{br}{bold}Davison chart of:{nobold} {', '.join(args['Davison'])}"
            + " (not stored, --name lacking)"
            if not EPHE
            else ""
        )
    string_local_time = (
        (f"{br}{bold}Local Time:{nobold} {str(local_datetime).lstrip('0')}" + " LMT")
        if args["LMT"]
        else (
            f"{br}{bold}Local Time:{nobold} {str(local_datetime).strip('0').strip(':')} {local_timezone}"
        )
    )
    string_UTC_Time_imprecise = f"{br}{bold}UTC Time:{nobold} {str(utc_datetime).lstrip('0')} UTC (imprecise due to exact time of day missing)"
    delta_symbol = "Delta" if (os.name == "nt" and output_type == "html") else "Δ"

    string_UTC_Time = f"{br}{bold}UTC Time:{nobold} {str(utc_datetime).lstrip('0')} UTC"  # ({delta_symbol}-T adjusted)"
    if args["Return"]:
        string_return = (
            f"{p}{bold}Return chart for "
            + ("the " if returning_planet in ("Moon", "Sun") else "")
            + returning_planet
            + f", {nextprev}{nobold}"
        )

    if notime:
        string_ruled_by = f"{br}{bold}Weekday:{nobold} {weekday} {bold}Day ruled by:{nobold} {ruling_day}"
    else:
        string_ruled_by = f"{br}{bold}Weekday:{nobold} {weekday} {bold}Day ruled by:{nobold} {ruling_day} {bold}Hour ruled by:{nobold} {ruling_hour}"
    if show_synastry:
        string_synastry_name = f"{p}{bold}Name:{nobold} {args['Synastry']}"
        string_synastry_place = f"{br}{bold}Place:{nobold} {synastry_place}"
        string_synastry_latitude_in_minutes = f"{br}{bold}Latitude:{nobold} {coord_in_minutes(synastry_latitude if show_synastry else 11.12, output_type)}"
        string_synastry_longitude_in_minutes = f"{bold}Longitude:{nobold} {coord_in_minutes(synastry_longitude if show_synastry else 22.33, output_type)}"
        string_synastry_latitude = f"{br}{bold}Latitude:{nobold} {synastry_latitude}"
        string_synastry_longitude = f"{bold}Longitude:{nobold} {synastry_longitude}"
        string_synastry_altitude = f"{br}{bold}Altitude:{nobold} {synastry_altitude} m"
        string_synastry_local_time = f"{br}{bold}Local Time:{nobold} {synastry_local_datetime} {synastry_local_timezone}"
        string_synastry_UTC_Time_imprecise = f"{br}{bold}UTC Time:{nobold} {synastry_utc_datetime} UTC (imprecise due to time of day missing)"
        string_synastry_UTC_Time = (
            f"{br}{bold}UTC Time:{nobold} {synastry_utc_datetime} UTC"
        )
        if notime:
            string_synastry_ruled_by = f"{br}{bold}Weekday:{nobold} {weekday_synastry} {bold}Day ruled by:{nobold} {ruling_day_synastry}"
        else:
            string_synastry_ruled_by = f"{br}{bold}Weekday:{nobold} {weekday_synastry} {bold}Day ruled by:{nobold} {ruling_day_synastry} {bold}Hour ruled by:{nobold} {ruling_hour_synastry}"

    string_house_system_moon_nodes = (
        f"{br}{bold}Center:{nobold} {center_of_calculations.title()}"
    )
    if center_of_calculations in ("geocentric", "topocentric"):
        string_house_system_moon_nodes += (
            f", {bold}House system:{nobold} {house_system_name}, {bold}Moon nodes:{nobold} {node}{br}"
            + (h_sys_changed + f"{br}" if h_sys_changed else "")
        )
    string_house_cusps = f"{p}{bold}House cusps:{nobold} {house_cusps}{br}"
    if output_type in ("return_text"):
        if moon_phase_name1 != moon_phase_name2:
            string_moon_phase_imprecise = f"\n\n{p}{bold}Moon Phase:{nobold} {moon_phase_name1} to {moon_phase_name2}{br}{bold}Moon Illumination:{nobold} {illumination}"
        else:
            string_moon_phase_imprecise = f"\n\n{p}{bold}Moon Phase:{nobold} {moon_phase_name1}{br}{bold}Moon Illumination:{nobold} {illumination}"
    else:
        string_moon_phase_imprecise = f"{p}{bold}Moon Phase:{nobold} {moon_phase_name1} to {moon_phase_name2}{br}{bold}Moon Illumination:{nobold} {illumination}"
    string_moon_phase = (
        f"{p}{bold}Moon Phase:{nobold} {moon_phase_name}{br}{bold}Moon Illumination:{nobold} {illumination}"
        if not notime
        else ""
    )
    string_transits = f"{p}{bold}{h2}Transits for"
    string_synastry = f"{p}{bold}{h2}Synastry chart for"
    string_no_transits_tz = f"{p}No timezone or location specified for transits (--transits_timezone, --transits_location).\nUsing default timezone ({def_transits_tz}) and location ({def_transits_location}) for transits."

    if output_type in ("text", "html"):
        print(f"{string_heading}", end="")
        if args["Return"]:
            print(f"{string_return}", end="")
        if args["Progressed"]:
            print(f"{string_progressed}", end="")
        if exists or name:
            print(f"{string_name}", end="")
        if place:
            print(f"{string_place}", end="")
        if degree_in_minutes:
            print(
                f"{string_latitude_in_minutes}, {string_longitude_in_minutes}", end=""
            )
        else:
            print(f"{string_latitude}, {string_longitude}", end="")
        print(f"{string_altitude}", end="")
        if args["Davison"]:
            print(f"{string_davison}", end="")

        if not args["Davison"] and place != "Davison chart":
            print(f"{string_local_time} ", end="")

        (
            print(f"{string_UTC_Time_imprecise}", end="")
            if notime
            else print(f"{string_UTC_Time}", end="")
        )

        print(f"{string_ruled_by}", end="")

        if not show_synastry and not center_of_calculations == "heliocentric":
            try:
                print(
                    f"{br}{bold}Sabian Symbol:{nobold} {get_sabian_symbol(planet_positions, 'Sun')}",
                    end="",
                )
            except:
                print(
                    f"{br}{bold}Sabian Symbol:{nobold} Cannot access sabian.json file",
                    end="",
                )

        print(f"{string_numerology}", end="")

        if show_synastry:
            print(f"{string_synastry_name}", end="")
            print(f"{string_synastry_place}", end="")
            if degree_in_minutes:
                print(
                    f"{string_synastry_latitude_in_minutes}, {string_synastry_longitude_in_minutes}, {string_synastry_altitude}",
                    end="",
                )
            else:
                print(
                    f"{string_synastry_latitude}, {string_synastry_longitude}, {string_synastry_altitude}",
                    end="",
                )
            print(f"{string_synastry_local_time} ", end="")
            (
                print(f"{string_synastry_UTC_Time_imprecise}", end="")
                if (notime or synastry_notime)
                else print(f"{string_synastry_UTC_Time}", end="")
            )
            print(f"{string_synastry_ruled_by}", end="")

    elif output_type in ("return_text", "return_html"):
        if args["Return"]:
            to_return += f"{string_return}"
        if args["Progressed"]:
            to_return += f"{string_progressed}"
        if exists or name:
            to_return += f"{string_name}"
        if place:
            to_return += f"{string_place}"
        if degree_in_minutes:
            to_return += f"{string_latitude_in_minutes}, {string_longitude_in_minutes}"
        else:
            to_return += f"{string_latitude}, {string_longitude}"
        to_return += f"{string_altitude}"
        if args["Davison"]:
            to_return += f"{string_davison}"

        if not args["Davison"] and place != "Davison chart":
            to_return += f"{string_local_time}"

        to_return += f"{br}{bold}Center:{nobold} {center_of_calculations.title()}"

        if notime:
            to_return += f"{string_UTC_Time_imprecise}"
        else:
            to_return += f"{string_UTC_Time}"

        to_return += f"{string_ruled_by}"

        if not show_synastry and not center_of_calculations == "heliocentric":
            try:
                to_return += f"{br}{bold}Sabian Symbol:{nobold} {get_sabian_symbol(planet_positions, 'Sun')}"
            except:
                to_return += (
                    f"{br}{bold}Sabian Symbol:{nobold} Cannot access sabian.json file"
                )

        to_return += f"{string_numerology}"

        if show_synastry:
            to_return += f"{string_synastry_name}"
            to_return += f"{string_synastry_place}"
            if degree_in_minutes:
                to_return += f"{string_synastry_latitude_in_minutes}, {string_synastry_longitude_in_minutes}, {string_synastry_altitude}"
            else:
                to_return += f"{string_synastry_latitude}, {string_synastry_longitude}, {string_synastry_altitude}"
            to_return += f"{string_synastry_local_time} "
            to_return += (
                f"{string_synastry_UTC_Time_imprecise}"
                if (notime or synastry_notime)
                else f"{string_synastry_UTC_Time}"
            )

    if output_type in ("text", "html"):
        print(f"{string_house_system_moon_nodes}", end="")
    else:
        to_return += f"{string_house_system_moon_nodes}"

    if minor_aspects:
        ASPECT_TYPES.update(MINOR_ASPECT_TYPES)
        MAJOR_ASPECTS.update(MINOR_ASPECTS)

    if show_house_cusps:
        if output_type in ("text", "html"):
            print(f"{string_house_cusps}", end="")
        else:
            to_return += f"{string_house_cusps}"

    if not hide_planetary_positions:
        if output_type in ("text", "html"):
            print(f"{string_planets_heading}{nobold}{h3_}{br}", end="")
        else:
            to_return += f"{string_planets_heading}"
        to_return += print_planet_positions(
            copy.deepcopy(planet_positions),
            degree_in_minutes,
            notime,
            house_positions,
            orb,
            output_type,
            args["Hide Decans"],
            args["Classical Rulership"],
            center_of_calculations,
            pluto_ecliptic,
        )

    if show_arabic_parts and not args["Aspects To Arabic Parts"]:
        ar_parts = [
            "Fortune",
            "Spirit",
            "Love",
            "Marriage",
            "Death",
            "Commerce",
            "Passion",
            "Friendship",
        ]
        for part in ar_parts:
            del planet_positions[part]

    aspects = calculate_planetary_aspects(
        copy.deepcopy(planet_positions), orbs, output_type, aspect_types=MAJOR_ASPECTS
    )  # Major aspects has been updated to include minor if
    fixstar_aspects = calculate_aspects_to_fixed_stars(
        utc_datetime,
        copy.deepcopy(planet_positions),
        house_cusps,
        orbs["Fixed Star"],
        MAJOR_ASPECTS,
        all_stars,
    )

    if not hide_planetary_aspects:
        to_return += f"{p}" + print_aspects(
            aspects=aspects,
            planet_positions=copy.deepcopy(planet_positions),
            orbs=orbs,
            imprecise_aspects=imprecise_aspects,
            minor_aspects=minor_aspects,
            degree_in_minutes=degree_in_minutes,
            house_positions=house_positions,
            orb=orb,
            type="Natal",
            p1_name="",
            p2_name="",
            notime=notime,
            output=output_type,
            show_aspect_score=show_score,
            complex_aspects=complex_aspects,
            center=center_of_calculations,
        )
    if not hide_fixed_star_aspects and fixstar_aspects:
        house_positions, house_cusps = calculate_house_positions(
            utc_datetime,
            latitude,
            longitude,
            altitude,
            copy.deepcopy(planet_positions),
            notime,
            HOUSE_SYSTEMS[house_system_name],
        )
        to_return += f"{p}" + print_fixed_star_aspects(
            fixstar_aspects,
            orb,
            minor_aspects,
            imprecise_aspects,
            notime,
            degree_in_minutes,
            copy.deepcopy(house_positions),
            read_fixed_stars(all_stars),
            output_type,
            all_stars,
            center=center_of_calculations,
        )
    if not hide_asteroid_aspects:
        asteroid_positions = calculate_planet_positions(
            utc_datetime,
            latitude,
            longitude,
            altitude,
            output_type,
            h_sys,
            "asteroids",
            center_of_calculations,
            classic_rulers=args["Classical Rulership"],
        )
        asteroid_aspects = calculate_aspects_takes_two(
            copy.deepcopy(planet_positions),
            copy.deepcopy(asteroid_positions),
            orbs,
            aspect_types=MAJOR_ASPECTS,
            output_type=output_type,
            type="asteroids",
            show_brief_aspects=show_brief_aspects,
        )
        if asteroid_aspects:
            to_return += f"{p}" + print_aspects(
                asteroid_aspects,
                copy.deepcopy(planet_positions),
                orbs,
                copy.deepcopy(asteroid_positions),
                imprecise_aspects,
                minor_aspects,
                degree_in_minutes,
                house_positions,
                orb,
                "Asteroids",
                "",
                "",
                notime,
                output_type,
                show_score,
                center=center_of_calculations,
            )
    if output_type == "html":
        print("</div>")
    elif output_type == "return_html":
        to_return += "</div>"

    if center_of_calculations != "heliocentric":
        if notime:
            if output_type in ("text", "html"):
                print(f"{string_moon_phase_imprecise}")
            else:
                if output_type == "return_text":
                    to_return += f"{br}{string_moon_phase_imprecise}"
                else:
                    to_return += f"{string_moon_phase_imprecise}"
        else:
            if output_type in ("text", "html"):
                print(f"{string_moon_phase}")
            else:
                to_return += f"{string_moon_phase}"

    name = f"{args['Name']} " if args["Name"] else ""

    if show_transits:
        planet_positions = calculate_planet_positions(
            utc_datetime,
            latitude,
            longitude,
            altitude,
            output_type,
            h_sys,
            "planets",
            center=center_of_calculations,
            classic_rulers=args["Classical Rulership"],
        )
        transits_planet_positions = calculate_planet_positions(
            transits_utc_datetime,
            transits_latitude,
            transits_longitude,
            transits_altitude,
            output_type,
            h_sys,
            "planets",
            center=center_of_calculations,
            classic_rulers=args["Classical Rulership"],
        )

        transit_aspects = calculate_aspects_takes_two(
            copy.deepcopy(planet_positions),
            copy.deepcopy(transits_planet_positions),
            orbs,
            aspect_types=MAJOR_ASPECTS,
            output_type=output_type,
            type="transits",
            show_brief_aspects=show_brief_aspects,
        )
        if output_type in ("text", "html"):
            print(
                f"{string_transits} {name}{transits_local_datetime.strftime('%Y-%m-%d %H:%M')} in {transits_location}{h2_}{nobold}"
            )
        else:
            to_return += f"{string_transits} {name} {transits_local_datetime.strftime('%Y-%m-%d %H:%M')} in {transits_location}{h2_}{nobold}"

        if not args["Transits Timezone"] or not args["Transits Location"]:
            if output_type in ("text", "html"):
                print(f"{string_no_transits_tz}")
            elif not EPHE:
                to_return += f"{string_no_transits_tz}"

        to_return += f"{p}" + print_aspects(
            transit_aspects,
            copy.deepcopy(planet_positions),
            orbs,
            copy.deepcopy(transits_planet_positions),
            imprecise_aspects,
            minor_aspects,
            degree_in_minutes,
            house_positions,
            orb,
            "Transit",
            "",
            "",
            notime,
            output_type,
            show_score,
            center=center_of_calculations,
        )

        star_positions = calculate_planet_positions(
            utc_datetime,
            latitude,
            longitude,
            altitude,
            output_type,
            h_sys,
            center=center_of_calculations,
            mode="stars",
            classic_rulers=args["Classical Rulership"],
        )
        transit_star_aspects = calculate_aspects_takes_two(
            copy.deepcopy(star_positions),
            copy.deepcopy(transits_planet_positions),
            orbs,
            aspect_types=MAJOR_ASPECTS,
            output_type=output_type,
            type="transits",
            show_brief_aspects=show_brief_aspects,
        )

        to_return += f"{p}" + print_aspects(
            transit_star_aspects,
            copy.deepcopy(planet_positions),
            orbs,
            copy.deepcopy(transits_planet_positions),
            imprecise_aspects,
            minor_aspects,
            degree_in_minutes,
            house_positions,
            orb,
            "Star Transit",
            "",
            "",
            notime,
            output_type,
            show_score,
            copy.deepcopy(star_positions),
            center=center_of_calculations,
        )

        asteroid_positions = calculate_planet_positions(
            utc_datetime,
            latitude,
            longitude,
            altitude,
            output_type,
            h_sys,
            "asteroids",
            center=center_of_calculations,
            classic_rulers=args["Classical Rulership"],
        )
        asteroid_transit_aspects = calculate_aspects_takes_two(
            copy.deepcopy(asteroid_positions),
            copy.deepcopy(transits_planet_positions),
            orbs,
            aspect_types=MAJOR_ASPECTS,
            output_type=output_type,
            type="asteroids",
            show_brief_aspects=show_brief_aspects,
        )
        if asteroid_transit_aspects:
            to_return += f"{p}" + print_aspects(
                asteroid_transit_aspects,
                copy.deepcopy(planet_positions),
                orbs,
                copy.deepcopy(transits_planet_positions),
                imprecise_aspects,
                minor_aspects,
                degree_in_minutes,
                house_positions,
                orb,
                "Asteroids Transit",
                "",
                "",
                notime,
                output_type,
                show_score,
                copy.deepcopy(asteroid_positions),
                center=center_of_calculations,
            )

    if show_synastry:
        planet_positions = calculate_planet_positions(
            utc_datetime,
            latitude,
            longitude,
            altitude,
            output_type,
            h_sys,
            center=center_of_calculations,
            classic_rulers=args["Classical Rulership"],
        )
        synastry_planet_positions = calculate_planet_positions(
            synastry_utc_datetime,
            synastry_latitude,
            synastry_longitude,
            synastry_altitude,
            output_type,
            h_sys,
            center=center_of_calculations,
            classic_rulers=args["Classical Rulership"],
        )

        synastry_aspects = calculate_aspects_takes_two(
            copy.deepcopy(planet_positions),
            copy.deepcopy(synastry_planet_positions),
            orbs,
            aspect_types=MAJOR_ASPECTS,
            output_type=output_type,
            type="synastry",
        )
        if output_type in ("text", "html"):
            print(f"{string_synastry} {name}and {args['Synastry']}{h2_}{nobold}")
        else:
            to_return += (
                f"{string_synastry} {name}and {args['Synastry']}{h2_}{nobold}{br}"
            )
        to_return += f"{p}" + print_aspects(
            synastry_aspects,
            copy.deepcopy(planet_positions),
            orbs,
            copy.deepcopy(synastry_planet_positions),
            imprecise_aspects,
            minor_aspects,
            degree_in_minutes,
            house_positions,
            orb,
            "Synastry",
            name,
            args["Synastry"],
            (notime or synastry_notime),
            output_type,
            show_score,
            center=center_of_calculations,
        )

    begin_date = utc_datetime - timedelta(days=10)
    end_date = utc_datetime + timedelta(days=10)
    # find_exact_aspects_in_timeframe(begin_date, end_date, latitude, longitude, altitude, orbs, center_of_calculations, step_days=1, output_type='text')

    # Make SVG chart if output is html
    if output_type in ("html", "return_html"):
        try:
            from . import chart_output
        except:
            import chart_output
        if show_transits:
            chart_type = "Transit"
        elif show_synastry:
            chart_type = "Synastry"
        else:
            chart_type = "Natal"

        if chart_type == "Natal":
            to_return += chart_output.chart_output(
                name,
                utc_datetime,
                longitude,
                latitude,
                local_timezone,
                place,
                chart_type,
                output_type,
                None,
                guid=args["Guid"] if args["Guid"] else None,
            )
        elif chart_type == "Transit":
            to_return += chart_output.chart_output(
                name,
                utc_datetime,
                longitude,
                latitude,
                local_timezone,
                place,
                chart_type,
                output_type,
                transits_utc_datetime,
                output_type,
                second_local_timezone=local_transits_timezone,
                second_place=transits_location,
                guid=args["Guid"] if args["Guid"] else None,
            )
        elif chart_type == "Synastry":
            to_return += chart_output.chart_output(
                name,
                utc_datetime,
                longitude,
                latitude,
                local_timezone,
                place,
                chart_type,
                output_type,
                synastry_utc_datetime,
                args["Synastry"],
                synastry_longitude,
                synastry_latitude,
                synastry_local_timezone,
                synastry_place,
                guid=args["Guid"] if args["Guid"] else None,
            )

        if output_type in ("html", "return_html"):
            print("</div></body>\n</html>")
        else:
            to_return += "\n    </div></body>\n</html>"
    return to_return
