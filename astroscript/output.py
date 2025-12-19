import json
import os

from colorama import Fore, Style
from tabulate import tabulate, SEPARATING_LINE

from .constants import *
from .coords import coord_in_minutes
from .dignity import assess_planet_strength, check_degree, is_planet_elevated
from .aspects import calculate_aspect_duration, calculate_aspect_score

def house_count(house_counts, output, bold, nobold, br):
    house_count_string = f"{bold}House count{nobold}  "
    row = [house_count_string]

    sorted_star_house_counts = sorted(
        house_counts.items(), key=lambda item: item[1], reverse=True
    )

    for house, count in sorted_star_house_counts:
        if count > 0:
            if output == "text":
                house_count_string += (
                    f"{bold}{house}:{nobold} {Fore.GREEN}{count}{Style.RESET_ALL}, "
                )
            elif output in ("html", "return_html"):
                row.append(f"{bold}{house}:{nobold} {count}")
            else:
                house_count_string += f"{house}: {count}, "

    if output in ("html", "return_html"):
        table = tabulate([row], tablefmt="unsafehtml")
        house_count_string = table
    else:
        house_count_string = house_count_string[:-2]  # Remove the last comma and space
    return house_count_string


def get_sabian_symbol(planet_positions, planet: str):
    """
    Retrieve the Sabian symbol for a specific degree within a zodiac sign.

    Parameters:
    - degree (float): The degree within the zodiac sign for which to retrieve the Sabian symbol.
    - zodiac_sign (str): The zodiac sign in which the degree is located.

    Returns:
    - str: The Sabian symbol corresponding to the specified degree within the zodiac sign.
    """
    ephe = os.getenv("PRODUCTION_EPHE")
    if ephe:
        sabian_symbols = json.load(open(f"{ephe}/sabian.json"))
    else:
        if os.name == "nt":
            sabian_symbols = json.load(open(".\ephe\sabian.json"))
        else:
            sabian_symbols = json.load(open("./ephe/sabian.json"))
    zodiac_sign = planet_positions["Sun"]["zodiac_sign"]
    degree = int(planet_positions["Sun"]["longitude"]) - ZODIAC_DEGREES[zodiac_sign]

    return sabian_symbols[zodiac_sign][str(degree)]


def print_complex_aspects(
    complex_aspects,
    output,
    degree_in_minutes,
    degree_symbol,
    table_format,
    notime,
    bold,
    nobold,
    h4,
    h4_,
    p,
):
    to_return = ""
    if complex_aspects.get("T Squares", False):
        plur = "s" if len(complex_aspects["T Squares"]) > 1 else ""
        if output in ("text", "html"):
            print(f"{p}{bold}{h4}T-Square{plur}{h4_}{nobold}")
        else:
            to_return += f"{p}{bold}{h4}T-Square{plur}{h4_}{nobold}"
        headers = [
            "Planet 1",
            "Planet 2",
            f"{bold}Apex{nobold}",
            "Opposition",
            "Square 1",
            "Square 2",
        ]
        rows = []
        t_squares = complex_aspects.get("T Squares", False)
        for ts in t_squares:
            if degree_in_minutes:
                opp_deg = coord_in_minutes(ts[3], output)
                sq_deg1 = (
                    coord_in_minutes(ts[4], output) if degree_in_minutes else ts[4]
                )
                sq_deg2 = (
                    coord_in_minutes(ts[5], output) if degree_in_minutes else ts[5]
                )
            else:
                opp_deg = f"{ts[3]:.2f}{degree_symbol}"
                sq_deg1 = f"{ts[4]:.2f}{degree_symbol}"
                sq_deg2 = f"{ts[5]:.2f}{degree_symbol}"

            rows.append(
                [ts[0], ts[1], f"{bold}{ts[2]}{nobold}", opp_deg, sq_deg1, sq_deg2]
            )

        table = tabulate(rows, headers=headers, tablefmt=table_format, floatfmt=".2f")

        if output == "text":
            print(table + f"{p}")
        elif output == "html":
            print(table + f"{p}")
        elif output == "return_text":
            to_return += table + f"{p}"
        elif output == "return_html":
            to_return += table + f"{p}"

    if complex_aspects.get("Yods", False):
        plur = "s" if len(complex_aspects["Yods"]) > 1 else ""
        if output in ("text", "html"):
            print(f"{p}{bold}{h4}Yod{plur} (Finger{plur} of God){h4_}{nobold}")
        else:
            to_return += f"{p}{bold}{h4}Yod{plur} (Finger{plur} of God){h4_}{nobold}"
        headers = [
            "Planet 1",
            "Planet 2",
            f"{bold}Apex{nobold}",
            "Sextile",
            "Quincunx 1",
            "Quincunx 2",
        ]
        rows = []
        yods = complex_aspects["Yods"]

        for yod in yods:
            if degree_in_minutes:
                opp_deg = coord_in_minutes(yod[3], output)
                sq_deg1 = (
                    coord_in_minutes(yod[4], output) if degree_in_minutes else yod[4]
                )
                sq_deg2 = (
                    coord_in_minutes(yod[5], output) if degree_in_minutes else yod[5]
                )
            else:
                opp_deg = f"{yod[3]:.2f}{degree_symbol}"
                sq_deg1 = f"{yod[4]:.2f}{degree_symbol}"
                sq_deg2 = f"{yod[5]:.2f}{degree_symbol}"

            rows.append(
                [yod[0], yod[1], f"{bold}{yod[2]}{nobold}", opp_deg, sq_deg1, sq_deg2]
            )

        table = tabulate(rows, headers=headers, tablefmt=table_format, floatfmt=".2f")

        if output == "text":
            print(table + f"{p}")
        elif output == "html":
            print(table + f"{p}")
        elif output == "return_text":
            to_return += table + f"{p}"
        elif output == "return_html":
            to_return += table + f"{p}"

    if complex_aspects.get("Grand Crosses", False):
        plur = "es" if len(complex_aspects["Grand Crosses"]) > 1 else ""
        if output in ("text", "html"):
            print(f"{p}{bold}{h4}Grand Cross{plur}{h4_}{nobold}")
        else:
            to_return += f"{p}{bold}{h4}Grand Cross{plur}{h4_}{nobold}"

        headers = [
            "Planet 1",
            "Sq 1",
            "Planet 2",
            "Sq 2",
            "Planet 3",
            "Sq 3",
            "Planet 4",
            "Sq 4",
            "Opp 1",
            "Opp 2",
        ]
        rows = []
        grand_crosses = complex_aspects.get("Grand Crosses", False)

        for gc in grand_crosses:
            if degree_in_minutes:
                sq_deg1 = coord_in_minutes(gc[4], output)
                sq_deg2 = coord_in_minutes(gc[5], output)
                sq_deg3 = coord_in_minutes(gc[6], output)
                sq_deg4 = coord_in_minutes(gc[7], output)
                opp_deg1 = coord_in_minutes(gc[8], output)
                opp_deg2 = coord_in_minutes(gc[9], output)
            else:
                sq_deg1 = f"{gc[4]:.2f}{degree_symbol}"
                sq_deg2 = f"{gc[5]:.2f}{degree_symbol}"
                sq_deg3 = f"{gc[6]:.2f}{degree_symbol}"
                sq_deg4 = f"{gc[7]:.2f}{degree_symbol}"
                opp_deg1 = f"{gc[8]:.2f}{degree_symbol}"
                opp_deg2 = f"{gc[9]:.2f}{degree_symbol}"

            rows.append(
                [
                    gc[0],
                    sq_deg1,
                    gc[1],
                    sq_deg2,
                    gc[2],
                    sq_deg3,
                    gc[3],
                    sq_deg4,
                    opp_deg1,
                    opp_deg2,
                ]
            )

        table = tabulate(rows, headers=headers, tablefmt=table_format, floatfmt=".2f")

        if output == "text":
            print(table + f"{p}")
        elif output == "html":
            print(table + f"{p}")
        elif output == "return_text":
            to_return += table + f"{p}"
        elif output == "return_html":
            to_return += table + f"{p}"

    if complex_aspects.get("Grand Trines", False):
        plur = "s" if len(complex_aspects["Grand Trines"]) > 1 else ""
        if output in ("text", "html"):
            print(f"{p}{bold}{h4}Grand Trine{plur}{h4_}{nobold}")
        else:
            to_return += f"{p}{bold}{h4}Grand Trine{plur}{h4_}{nobold}"
        headers = [
            "Planet 1",
            "Sextile 1",
            "Planet 2",
            "Sextile 2",
            "Planet 3",
            "Sextile 3",
        ]
        rows = []
        grand_trines = complex_aspects["Grand Trines"]

        for trine in grand_trines:
            if degree_in_minutes:
                trine1_diff = coord_in_minutes(trine[3], output)
                trine2_diff = (
                    coord_in_minutes(trine[4], output)
                    if degree_in_minutes
                    else trine[4]
                )
                trine3_diff = (
                    coord_in_minutes(trine[5], output)
                    if degree_in_minutes
                    else trine[5]
                )
            else:
                trine1_diff = f"{trine[3]:.2f}{degree_symbol}"
                trine2_diff = f"{trine[4]:.2f}{degree_symbol}"
                trine3_diff = f"{trine[5]:.2f}{degree_symbol}"

            rows.append(
                [trine[0], trine1_diff, trine[1], trine2_diff, trine[2], trine3_diff]
            )

        table = tabulate(rows, headers=headers, tablefmt=table_format, floatfmt=".2f")

        if output == "text":
            print(table + f"{p}")
        elif output == "html":
            print(table + f"{p}")
        elif output == "return_text":
            to_return += table + f"{p}"
        elif output == "return_html":
            to_return += table + f"{p}"

    if complex_aspects.get("Kites", False):
        plur = "s" if len(complex_aspects["Kites"]) > 1 else ""
        if output in ("text", "html"):
            print(f"{p}{bold}{h4}Kite{plur}{h4_}{nobold}")
        else:
            to_return += f"{p}{bold}{h4}Kite{plur}{h4_}{nobold}"
        headers = [
            "Planet 1",
            "Sextile 1",
            "Planet 2",
            "Sextile 2",
            "Planet 3",
            "Sextile 3",
            "Opposition",
            "Degree",
        ]
        rows = []
        kites = complex_aspects["Kites"]

        for trine in kites:
            if degree_in_minutes:
                trine1_diff = coord_in_minutes(trine[4], output)
                trine2_diff = coord_in_minutes(trine[5], output)
                trine3_diff = coord_in_minutes(trine[6], output)
                oppo_diff = coord_in_minutes(trine[7], output)
            else:
                trine1_diff = f"{trine[4]:.2f}{degree_symbol}"
                trine2_diff = f"{trine[5]:.2f}{degree_symbol}"
                trine3_diff = f"{trine[6]:.2f}{degree_symbol}"
                oppo_diff = f"{trine[7]:.2f}{degree_symbol}"

            rows.append(
                [
                    trine[0],
                    trine1_diff,
                    trine[1],
                    trine2_diff,
                    trine[2],
                    trine3_diff,
                    trine[3],
                    oppo_diff,
                ]
            )

        table = tabulate(rows, headers=headers, tablefmt=table_format, floatfmt=".2f")

        if output == "text":
            print(table + f"{p}")
        elif output == "html":
            print(table + f"{p}")
        elif output == "return_text":
            to_return += table + f"{p}"
        elif output == "return_html":
            to_return += table + f"{p}"
    return to_return


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
    Print the positions of planets in a human-readable format. This includes the zodiac sign,
    degree (optionally in minutes), whether the planet is retrograde, and its house position
    if available.

    Parameters:
    - planet_positions (dict): A dictionary with celestial bodies as keys and dictionaries as values,
      containing 'longitude', 'zodiac_sign', 'retrograde', and optionally 'house'.
    - degree_in_minutes (bool): If True, display the longitude in degrees, minutes, and seconds.
      Otherwise, display only in decimal degrees.
    - notime (bool): If True, house information is considered irrelevant or unavailable.
    - house_positions (dict, optional): Additional dictionary mapping planets to their house positions,
      if this information is available.
    - orb (float): The orb value to consider when determining the preciseness of the planet's position.
      This parameter might not be directly used in this function but is included for consistency with the
      overall structure of the astrological calculations.
    """

    sign_counts = {sign: {"count": 0, "planets": []} for sign in ZODIAC_ELEMENTS.keys()}
    modality_counts = {
        modality: {"count": 0, "planets": []} for modality in ZODIAC_MODALITIES.keys()
    }
    element_counts = {"Fire": 0, "Earth": 0, "Air": 0, "Water": 0}
    planet_house_counts = {house: 0 for house in range(1, 13)}

    zodiac_table_data = []

    if output_type in ("html", "return_html"):
        table_format = "html"
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
        headers.insert(3, "Off by")
    if not hide_decans:
        headers.append(
            "Decan ruler" if output_type in ("html", "return_html") else "Decan"
        )

    planet_signs = {}

    for planet, info in planet_positions.items():
        if notime and (planet in ALWAYS_EXCLUDE_IF_NO_TIME):
            continue
        longitude = info["longitude"]
        degrees_within_sign = longitude % 30
        position = (
            coord_in_minutes(degrees_within_sign, output_type)
            if degree_in_minutes
            else f"{degrees_within_sign:.2f}{degree_symbol}"
        )
        retrograde = info["retrograde"]
        zodiac = info["zodiac_sign"]
        retrograde_status = retrograde  # "R" if retrograde else ""
        decan_ruler = info.get("decan_ruled_by", "")

        planet_signs[planet] = zodiac
        strength_check = assess_planet_strength(planet_signs, classic_rulers)
        elevation_check = is_planet_elevated(planet_positions)
        degree_check = check_degree(planet_signs, degrees_within_sign)

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

    table_format = "html" if output_type in ("html", "return_html") else "simple"

    to_return = ""
    table = tabulate(
        zodiac_table_data, headers=headers, tablefmt=table_format, floatfmt=".2f"
    )

    if output_type in ("text", "html"):
        print(table)
    to_return += table

    sign_count_table_data = list()
    element_count_table_data = list()
    modality_count_table_data = list()

    ## House counts
    if not notime and not center == "heliocentric":
        if output_type in ("return_text", "return_html"):
            to_return += f"{p}" + house_count(
                planet_house_counts, output_type, bold, nobold, br
            )
        else:
            print(
                f"{p}" + house_count(planet_house_counts, output_type, bold, nobold, br)
            )

    # Print zodiac sign, element and modality counts
    if output_type in ("html"):
        print(f"{p}<div class='table-container'>")
    if output_type == "return_html":
        to_return += f"{p}<div class='table-container'>"

    for sign, data in sign_counts.items():
        if data["count"] > 0:
            row = [
                sign,
                data["count"],
                ", ".join(data["planets"])
                + (" (stellium)" if data["count"] >= 4 else ""),
            ]
            sign_count_table_data.append(row)

    table = tabulate(
        sign_count_table_data,
        headers=["Sign", "Nr", "Planets in Sign".title()],
        tablefmt=table_format,
        floatfmt=".2f",
    )
    to_return += f"{br}{br}{table}"
    if output_type in ("text", "html"):
        print(f"{p}{table}{br}")

    for element, count in element_counts.items():
        if count > 0:
            row = [element, count]
            element_count_table_data.append(row)

    # Check nr of day and night signs
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

    nr_day_signs = fire_count + air_count
    nr_night_signs = earth_count + water_count
    if output_type in ("text", "return_text"):
        element_count_table_data.append(SEPARATING_LINE)
    element_count_table_data.append(["Day signs", nr_day_signs])
    element_count_table_data.append(["Night signs", nr_night_signs])

    table = tabulate(
        element_count_table_data,
        headers=["Element", "Nr"],
        tablefmt=table_format,
        floatfmt=".2f",
    )
    to_return += f"{br}{br}{table}"
    if output_type in ("text", "html"):
        print(table + f"{br}")

    for modality, info in modality_counts.items():
        row = [modality, info["count"], ", ".join(info["planets"])]
        modality_count_table_data.append(row)
    table = tabulate(
        modality_count_table_data,
        headers=["Modality", "Nr", "Planets"],
        tablefmt=table_format,
    )
    to_return += f"{br}{br}{table}"
    if output_type in ("text", "html"):
        print(table + f"{br}")
        if output_type == "html":
            print("</div>")
    elif output_type == "return_html":
        to_return += "</div>"

    return to_return


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
    Prints astrological aspects between celestial bodies, offering options for display and filtering.
    """
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
    orb_string_major_minor = (
        f"(major {orbs['Major']}{degree_symbol} minor {orbs['Minor']}{degree_symbol} orb)"
        if minor_aspects
        else f"({orbs['Major']}{degree_symbol} orb)"
    )
    orb_string_transits_fast_slow = f"(fast {orbs['Transit Fast']}{degree_symbol} slow {orbs['Transit Slow']}{degree_symbol} orb)"
    orb_string_synastry_fast_slow = f"(fast {orbs['Synastry Fast']}{degree_symbol} slow {orbs['Synastry Slow']}{degree_symbol} orb)"

    planetary_aspects_table_data = []
    if notime or center == "heliocentric":
        if type == "Transit":
            headers = [
                "Natal Planet",
                "Aspect",
                "Transit Planet",
                "Degree",
                "Exact",
                "Rem. Duration",
            ]
        if type == "Star Transit":
            headers = [
                "Natal Star",
                "Aspect",
                "Transit Planet",
                "Degree",
                "Exact",
                "Rem. Duration",
            ]
        if type == "Asteroids Transit":
            headers = [
                "Natal Asteroid",
                "Aspect",
                "Transit Planet",
                "Degree",
                "Exact",
                "Rem. Duration",
            ]
        elif type == "Synastry":
            headers = [p1_name, "Aspect", p2_name, "Degree", "Off by"]
        elif type == "Asteroids":
            headers = [
                "Natal Planet",
                house_called,
                "Aspect",
                "Natal Asteroid",
                house_called,
                "Degree",
            ]
        elif type == "Natal":
            headers = ["Planet", "Aspect", "Planet", "Degree", "Off by"]
    else:
        if type == "Transit":
            headers = [
                "Natal Planet",
                house_called,
                "Aspect",
                "Transit Planet",
                house_called,
                "Degree",
                "Exact",
                "Rem. Duration",
            ]
        if type == "Star Transit":
            headers = [
                "Natal Star",
                house_called,
                "Aspect",
                "Transit Planet",
                house_called,
                "Degree",
                "Exact",
                "Rem. Duration",
            ]
        if type == "Asteroids Transit":
            headers = [
                "Natal Asteroid",
                house_called,
                "Aspect",
                "Transit Planet",
                house_called,
                "Degree",
                "Exact",
                "Rem. Duration",
            ]
        elif type == "Synastry":
            headers = [
                p1_name,
                house_called,
                "Aspect",
                p2_name,
                house_called,
                "Degree",
                "Off by",
            ]
        elif type == "Asteroids":
            headers = [
                "Natal Planet",
                house_called,
                "Aspect",
                "Natal Asteroid",
                house_called,
                "Degree",
            ]
        elif type == "Natal":
            headers = [
                "Planet",
                house_called,
                "Aspect",
                "Planet",
                house_called,
                "Degree",
                "Off by",
            ]

    if show_aspect_score:
        headers.append("Score")
    to_return = ""

    if output in ("text", "html"):
        if type == "Asteroids":
            print(
                f"{p}{bold}{h3}Asteroid Aspects ({orbs['Asteroid']}{degree_symbol} orb){nobold}",
                end="",
            )
        elif type == "Transit":
            print(
                f"{p}{bold}{h3}Planetary Transit Aspects {orb_string_transits_fast_slow}{nobold}",
                end="",
            )
        elif type == "Star Transit":
            print(
                f"{p}{bold}{h3}Star Transit Aspects {orb_string_transits_fast_slow}{nobold}",
                end="",
            )
        elif type == "Asteroids Transit":
            print(
                f"{p}{bold}{h3}Asteroid Transit Aspects {orb_string_transits_fast_slow}{nobold}",
                end="",
            )
        elif type == "Synastry":
            print(
                f"{p}{bold}{h3}Planetary Synastry Aspects {orb_string_synastry_fast_slow}{nobold}",
                end="",
            )
        else:
            print(
                f"{p}{bold}{h3}Planetary Aspects {orb_string_major_minor}{nobold}",
                end="",
            )
        print(
            f"{bold} including minor aspects{nobold}" if minor_aspects else "", end=""
        )
        if notime:
            print(
                f"{bold} with imprecise aspects set to {imprecise_aspects}{nobold}",
                end="",
            )
        print(f"{h3_}")
    else:
        if type == "Asteroids":
            to_return = f"{p}{bold}{h3}Asteroid Aspects ({orbs['Asteroid']}{degree_symbol} orb{nobold})"
        elif type == "Transit":
            to_return += f"{p}{bold}{h3}Planetary Transit Aspects {orb_string_transits_fast_slow}{nobold}"
        elif type == "Star Transit":
            to_return += f"{p}{bold}{h3}Star Transit Aspects {orb_string_transits_fast_slow}{nobold}"
        elif type == "Asteroids Transit":
            to_return += f"{p}{bold}{h3}Asteroid Transit Aspects {orb_string_transits_fast_slow}{nobold}"
        elif type == "Synastry":
            to_return += f"{p}{bold}{h3}Planetary Synastry Aspects {orb_string_synastry_fast_slow}{nobold}"
        else:
            to_return = (
                f"{p}{bold}{h3}Planetary Aspects {orb_string_major_minor}{nobold}"
            )
        if minor_aspects:
            to_return += f"{bold} including minor aspects{nobold}"
        if notime:
            to_return += (
                f"{bold} with imprecise aspects set to {imprecise_aspects}{nobold}"
            )
        to_return += f"{h3_}"

    aspect_type_counts = {}
    hard_count = 0
    soft_count = 0
    hard_count_score = 0
    soft_count_score = 0
    house_counts = {house: 0 for house in range(1, 13)}

    all_aspects = {**SOFT_ASPECTS, **HARD_ASPECTS}

    off_by_column = False  # Check if any planets use the off by column

    for planets, aspect_details in aspects.items():
        if (
            planets[0] in ALWAYS_EXCLUDE_IF_NO_TIME
            or planets[1] in ALWAYS_EXCLUDE_IF_NO_TIME
        ) and notime:
            continue
        if (
            imprecise_aspects == "off"
            and ((planets[0] in OFF_BY.keys() or planets[1] in OFF_BY.keys()))
            and notime
        ):
            if round(OFF_BY.get(planets[0], 0) + OFF_BY.get(planets[1], 0), 2) > orb:
                continue
        if degree_in_minutes:
            angle_with_degree = f"{aspect_details['angle_diff_in_minutes']}".strip("-")
        else:
            if type in ("Transit", "Star Transit", "Asteroids Transit"):
                angle_with_degree = f"{aspect_details['angle_diff']:.2f}{degree_symbol}"
            else:
                angle_with_degree = (
                    f"{aspect_details['angle_diff']:.2f}{degree_symbol}".strip("-")
                )
        if imprecise_aspects == "off" and (
            aspect_details["is_imprecise"]
            or planets[0] in ALWAYS_EXCLUDE_IF_NO_TIME
            or planets[1] in ALWAYS_EXCLUDE_IF_NO_TIME
        ):
            continue
        else:
            if notime or center == "heliocentric":
                if type in ("Transit", "Star Transit", "Asteroids Transit"):
                    row = [
                        planets[0],
                        aspect_details["aspect_name"],
                        planets[1],
                        angle_with_degree,
                        ("In " if aspect_details["angle_diff"] < 0 else "")
                        + calculate_aspect_duration(
                            planet_positions,
                            planets[1],
                            0 - aspect_details["angle_diff"],
                        )
                        + (" ago" if aspect_details["angle_diff"] > 0 else ""),
                        calculate_aspect_duration(
                            planet_positions,
                            planets[1],
                            orb - aspect_details["angle_diff"],
                        ),
                    ]
                elif type == "Synastry" or type == "Asteroids":
                    row = [
                        planets[0],
                        aspect_details["aspect_name"],
                        planets[1],
                        angle_with_degree,
                    ]
                # elif type == "Star Transit":
                #     row = [planets[0], aspect_details['aspect_name'], planets[1], angle_with_degree,
                #         ("In " if aspect_details['angle_diff'] < 0 else "") + calculate_aspect_duration(planet_positions, planets[1], 0-aspect_details['angle_diff']) + (" ago" if aspect_details['angle_diff'] > 0 else ""),
                #         calculate_aspect_duration(planet_positions, planets[1], orb-aspect_details['angle_diff'])]
                # elif type == "Asteroids Transit":
                #     row = [planets[0], aspect_details['aspect_name'], planets[1], angle_with_degree,
                #         ("In " if aspect_details['angle_diff'] < 0 else "") + calculate_aspect_duration(planet_positions, planets[1], 0-aspect_details['angle_diff']) + (" ago" if aspect_details['angle_diff'] > 0 else ""),
                #         calculate_aspect_duration(planet_positions, planets[1], orb-aspect_details['angle_diff'])]
                else:
                    row = [
                        planets[0],
                        aspect_details["aspect_name"],
                        planets[1],
                        angle_with_degree,
                    ]
            else:
                if type == "Transit":
                    row = [
                        planets[0],
                        planet_positions[planets[0]]["house"],
                        aspect_details["aspect_name"],
                        planets[1],
                        transit_planet_positions[planets[1]]["house"],
                        angle_with_degree,
                        ("In " if aspect_details["angle_diff"] < 0 else "")
                        + calculate_aspect_duration(
                            planet_positions,
                            planets[1],
                            0 - aspect_details["angle_diff"],
                        )
                        + (" ago" if aspect_details["angle_diff"] > 0 else ""),
                        calculate_aspect_duration(
                            planet_positions,
                            planets[1],
                            orb - aspect_details["angle_diff"],
                        ),
                    ]
                elif type == "Synastry" or type == "Asteroids":
                    row = [
                        planets[0],
                        planet_positions[planets[0]]["house"],
                        aspect_details["aspect_name"],
                        planets[1],
                        transit_planet_positions[planets[1]]["house"],
                        angle_with_degree,
                    ]
                elif type == "Star Transit":
                    row = [
                        planets[0],
                        star_positions[planets[0]]["house"],
                        aspect_details["aspect_name"],
                        planets[1],
                        transit_planet_positions[planets[1]]["house"],
                        angle_with_degree,
                        ("In " if aspect_details["angle_diff"] < 0 else "")
                        + calculate_aspect_duration(
                            copy.deepcopy(planet_positions),
                            planets[1],
                            0 - aspect_details["angle_diff"],
                        )
                        + (" ago" if aspect_details["angle_diff"] > 0 else ""),
                        calculate_aspect_duration(
                            copy.deepcopy(planet_positions),
                            planets[1],
                            orb - aspect_details["angle_diff"],
                        ),
                    ]
                elif type == "Asteroids Transit":
                    row = [
                        planets[0],
                        star_positions[planets[0]]["house"],
                        aspect_details["aspect_name"],
                        planets[1],
                        transit_planet_positions[planets[1]]["house"],
                        angle_with_degree,
                        ("In " if aspect_details["angle_diff"] < 0 else "")
                        + calculate_aspect_duration(
                            planet_positions,
                            planets[1],
                            0 - aspect_details["angle_diff"],
                        )
                        + (" ago" if aspect_details["angle_diff"] > 0 else ""),
                        calculate_aspect_duration(
                            planet_positions,
                            planets[1],
                            orb - aspect_details["angle_diff"],
                        ),
                    ]
                else:
                    row = [
                        planets[0],
                        planet_positions[planets[0]]["house"],
                        aspect_details["aspect_name"],
                        planets[1],
                        planet_positions[planets[1]]["house"],
                        angle_with_degree,
                    ]
                if house_counts and not notime:
                    if star_positions:
                        house_counts[star_positions[planets[0]]["house"]] += 1
                    else:
                        if planet_positions[planets[0]].get("house", False):
                            house_counts[planet_positions[planets[0]]["house"]] += 1
                    if not type == "Natal":
                        if transit_planet_positions[planets[1]].get("house", False):
                            house_counts[
                                transit_planet_positions[planets[1]]["house"]
                            ] += 1

        if (
            imprecise_aspects == "warn"
            and ((planets[0] in OFF_BY.keys() or planets[1] in OFF_BY.keys()))
            and notime
        ):
            if float(OFF_BY[planets[0]]) > orb or float(OFF_BY[planets[1]]) > orb:
                off_by = str(
                    round(OFF_BY.get(planets[0], 0) + OFF_BY.get(planets[1], 0), 2)
                )
                row.append(" ± " + off_by)
                off_by_column = True
            else:
                row.append("")
        if show_aspect_score:
            row.append(
                calculate_aspect_score(
                    aspect_details["aspect_name"], aspect_details["angle_diff"]
                )
            )

        planetary_aspects_table_data.append(row)

        # Add or update the count of the aspect type
        aspect_name = aspect_details["aspect_name"]
        if aspect_name in aspect_type_counts:
            aspect_type_counts[aspect_name] += 1
        else:
            aspect_type_counts[aspect_name] = 1
        if aspect_name in HARD_ASPECTS:
            hard_count += 1
            hard_count_score += aspect_details["aspect_score"]
        elif aspect_name in SOFT_ASPECTS:
            soft_count += 1
            soft_count_score += aspect_details["aspect_score"]

    # If no aspects found
    if len(planetary_aspects_table_data) < 1:
        return ""

    # Sorting
    if notime or center == "heliocentric":
        planetary_aspects_table_data.sort(
            key=lambda x: x[3]
        )  # Sort by degree of aspect
    else:
        planetary_aspects_table_data.sort(key=lambda x: x[5])  # 2 more columns

    if not off_by_column:
        try:
            headers.remove("Off by")
        except:
            pass

    table = tabulate(
        planetary_aspects_table_data,
        headers=headers,
        tablefmt=table_format,
        floatfmt=".2f",
        colalign=(
            ("left", "left", "left", "right", "left", "left")
            if (type == "Transit" and center == "geocentric")
            else ""
        ),
    )

    if output in ("text", "html"):
        if output == "html":
            print('<div class="table-container">')
        print(f"{table}")
    if output == "return_html":
        to_return += '<div class="table-container">'
    if output in ("return_text", "return_html"):
        to_return += f"{br}" + table

    # Convert aspect type dictionary to a list of tuples
    aspect_data = list(aspect_type_counts.items())
    aspect_data.sort(key=lambda x: x[1], reverse=True)  # Sort by degree of aspect

    # Convert aspect_data to a list of lists
    aspect_data = [
        [aspect_data[i][0], aspect_data[i][1], list(all_aspects[aspect[0]].values())[2]]
        for i, aspect in enumerate(aspect_data)
    ]

    headers = ["Aspect Type", "Count", "Meaning"]
    table = tabulate(aspect_data, headers=headers, tablefmt=table_format)

    if output in ("html", "return_html"):
        div_string = '</div><div style="text-align: left; padding-bottom: 20px; padding-left: 20px;">'
    else:
        div_string = ""

    if hard_count + soft_count > 0:
        if output in ("html, return_html"):
            row = [
                f"{bold}Hard Aspects:{nobold}",
                hard_count,
                f"{bold}Soft Aspects:{nobold}",
                soft_count,
                f"{bold}Score:{nobold}",
                f"{(hard_count_score + soft_count_score)/(hard_count+soft_count):.1f}".rstrip(
                    "0"
                ).rstrip(
                    "."
                ),
            ]
            score_table = tabulate([row], tablefmt="unsafehtml")
            aspect_count_text = f"{div_string}{p}{score_table}"
        else:
            aspect_count_text = f"{div_string}{p}{bold}Hard Aspects:{nobold} {hard_count}, {bold}Soft Aspects:{nobold} {soft_count}, {bold}Score:{nobold} {(hard_count_score + soft_count_score)/(hard_count+soft_count):.1f}".rstrip(
                "0"
            ).rstrip(
                "."
            )
    else:
        aspect_count_text = f"{div_string}{p}No aspects found."
    to_return += f"{br}" + table + aspect_count_text

    # Print counts of each aspect type
    if output in ("text", "html"):
        print(f"{br}" + table + f"{p}" + aspect_count_text)

    # House counts only if time specified and more aspects than one, and not heliocentric
    if not notime and len(aspects) > 1 and not center == "heliocentric":
        if output in ("return_text", "return_html"):
            to_return += f"{p}" + house_count(house_counts, output, bold, nobold, br)
        else:
            if output == "html":
                print(p)
            print(house_count(house_counts, output, bold, nobold, br))

    if complex_aspects:
        to_return += print_complex_aspects(
            complex_aspects,
            output,
            degree_in_minutes,
            degree_symbol,
            table_format,
            notime,
            bold,
            nobold,
            h4,
            h4_,
            p,
        )

    if output == "html":
        print("</div>")
    if output == "return_html":
        to_return += "</div>"

    if output in ("text", "html"):
        if not house_positions:
            print(f"{p}* No time of day specified. Houses cannot be calculated. ")
            print("  Aspects to the Ascendant and Midheaven are not available.")
            print(
                "  The positions of the Sun, Moon, Mercury, Venus, and Mars are uncertain.\n"
            )
            print(f"{p}  Please specify the time of birth for a complete chart.\n")
    else:
        if not house_positions:
            to_return += f"{p}* No time of day specified. Houses cannot be calculated. "
            to_return += (
                f"{p}  Aspects to the Ascendant and Midheaven are not available."
            )
            to_return += f"{p}  The positions of the Sun, Moon, Mercury, Venus, and Mars are uncertain.\n"
            to_return += (
                f"{p}  Please specify the time of birth for a complete chart.\n"
            )

    return to_return


def print_fixed_star_aspects(
    aspects,
    orb=1,
    minor_aspects=False,
    imprecise_aspects="off",
    notime=True,
    degree_in_minutes=False,
    house_positions=None,
    stars=None,
    output="text",
    show_aspect_score=False,
    all_stars=False,
    center="topocentric",
) -> str:
    """
    Prints aspects between planets and fixed stars with options for minor aspects, precision warnings, and house positions.

    Parameters:
    - aspects (list): Aspects between planets and fixed stars.
    - orb (float): Orb for aspect significance.
    - minor_aspects (bool): Include minor aspects.
    - imprecise_aspects (str): Handle imprecise aspects ('off' or 'warn').
    - notime (bool): Exclude time-dependent data.
    - degree_in_minutes (bool): Show angles in degrees, minutes, and seconds.
    - house_positions (dict, optional): Mapping of fixed stars to house poitions.
    - all_stars (bool): Include aspects for all stars or significant ones only.

    Outputs a formatted list of aspects to the console based on the provided parameters.
    """
    to_return = ""
    if output in ("html", "return_html"):
        table_format = "html"
        bold = "<b>"
        nobold = "</b>"
        br = "\n<br>"
        p = "\n<p>"
        h3 = "<h3>"
        h3_ = "</h3>"
    elif output == "text":
        table_format = "simple"
        bold = "\033[1m"
        nobold = "\033[0m"
        br = "\n"
        p = "\n"
        h3 = ""
        h3_ = ""
    elif output == "return_text":
        table_format = "simple"
        bold = ""
        nobold = ""
        br = "\n"
        p = "\n"
        h3 = ""
        h3_ = ""
    degree_symbol = "" if (os.name == "nt" and output == "html") else "°"

    if output in ("text", "html"):
        print(
            f"{p}{bold}{h3}Fixed Star Aspects ({orb}{degree_symbol} orb){nobold}",
            end="",
        )
        print(
            f"{bold} including minor aspects{nobold}" if minor_aspects else "", end=""
        )
        if notime:
            print(
                f"{bold} with Imprecise Aspects set to {imprecise_aspects}{nobold}",
                end="",
            )
        print(f"{h3_}")
    else:
        to_return += f"{p}{bold}{h3}Fixed Star Aspects ({orb}° orb){nobold}"
        if minor_aspects:
            to_return += f"{bold} including minor aspects{nobold}"
        if notime:
            to_return += f"{bold} with Imprecise Aspects set to {imprecise_aspects}{nobold}{br}{br}"
        to_return += f"{h3_}{nobold}"
    star_aspects_table_data = []

    aspect_type_counts = {}
    hard_count = 0
    soft_count = 0
    hard_count_score = 0
    soft_count_score = 0
    all_aspects = {**SOFT_ASPECTS, **HARD_ASPECTS}
    house_counts = {house: 0 for house in range(1, 13)}

    for aspect in aspects:
        planet, star_name, aspect_name, angle, house, aspect_score, aspect_comment = (
            aspect
        )
        if planet in ALWAYS_EXCLUDE_IF_NO_TIME:
            continue
        if (
            imprecise_aspects == "off"
            and planet in OFF_BY.keys()
            and OFF_BY[planet] > orb
        ):
            continue
        if degree_in_minutes:
            angle = coord_in_minutes(angle, output)
        else:
            angle = f"{angle:.2f}{degree_symbol}".strip("-")
        row = [planet, aspect_name, star_name, angle]
        if house_positions and not notime and center in ("geocentric", "topocentric"):
            row.insert(
                1, house_positions[planet].get("house", "Unknown")
            )  # Planet house
            row.insert(4, house)  # Star house
            house_counts[house] += 1
            house_counts[house_positions[planet].get("house", "Unknown")] += 1
        if notime and planet in OFF_BY.keys() and OFF_BY[planet] > orb:
            row.append(f" ±{OFF_BY[planet]}{degree_symbol}")

        if show_aspect_score:
            row.append(calculate_aspect_score(aspect_name, aspect[3], stars[star_name]))
        star_aspects_table_data.append(row)

        if aspect_name in aspect_type_counts:
            aspect_type_counts[aspect_name] += 1
        else:
            aspect_type_counts[aspect_name] = 1
        if aspect_name in HARD_ASPECTS:
            hard_count += 1
            hard_count_score += calculate_aspect_score(
                aspect_name, aspect[3], stars[star_name]
            )
        elif aspect_name in SOFT_ASPECTS:
            soft_count += 1
            # soft_count_score += aspect_score # it was like this before magnitude was taken into account (keeping if adding switch)
            soft_count_score += calculate_aspect_score(
                aspect_name, aspect[3], stars[star_name]
            )

    headers = ["Planet", "Aspect", "Star", "Margin"]

    if house_positions and (not notime) and (center in ("geocentric", "topocentric")):
        if output in ("html", "return_html"):
            headers.insert(1, "House")
            headers.insert(4, "House")
        else:
            headers.insert(1, "H")
            headers.insert(4, "H")

    if planet in OFF_BY.keys() and OFF_BY[planet] > orb and notime:
        headers.append("Off by")
    if show_aspect_score:
        headers.append("Score")

    if notime or center not in ("geocentric", "topocentric"):
        star_aspects_table_data.sort(key=lambda x: x[3])  # Sort by degree of aspect
    else:
        star_aspects_table_data.sort(key=lambda x: x[5])  # Sort by degree of aspect

    table = tabulate(
        star_aspects_table_data, headers=headers, tablefmt=table_format, floatfmt=".2f"
    )
    if output in ("text", "html"):
        if output == "html":
            print('<div class="table-container">')
        print(table + f"{br}", end="")
    if output in ("return_html"):
        if all_stars:
            to_return += '<div id="allfixedstarsection">'
        to_return += '<div class="table-container">'
    to_return += f"{br}{br}" + table

    aspect_data = list(aspect_type_counts.items())
    aspect_data.sort(key=lambda x: x[1], reverse=True)
    aspect_data = [
        [aspect_data[i][0], aspect_data[i][1], list(all_aspects[aspect[0]].values())[2]]
        for i, aspect in enumerate(aspect_data)
    ]
    headers = ["Aspect Type", "Count", "Meaning"]
    table = tabulate(aspect_data, headers=headers, tablefmt=table_format)

    if output in ("html", "return_html"):
        div_string = '</div><div style="text-align: left";>'
    else:
        div_string = ""

    if hard_count + soft_count > 0:
        if output in ("html, return_html"):
            row = [
                f"{bold}Hard Aspects:{nobold}",
                hard_count,
                f"{bold}Soft Aspects:{nobold}",
                soft_count,
                f"{bold}Score:{nobold}",
                f"{(hard_count_score + soft_count_score)/(hard_count+soft_count):.1f}".rstrip(
                    "0"
                ).rstrip(
                    "."
                ),
            ]
            score_table = tabulate([row], tablefmt="unsafehtml")
            aspect_count_text = f"{div_string}{p}{score_table}"
        else:
            aspect_count_text = f"{div_string}{p}{bold}Hard Aspects:{nobold} {hard_count}, {bold}Soft Aspects:{nobold} {soft_count}, {bold}Score:{nobold} {(hard_count_score + soft_count_score)/(hard_count+soft_count):.1f}".rstrip(
                "0"
            ).rstrip(
                "."
            )
    else:
        aspect_count_text = f"{div_string}{p}No aspects found."

    # Print counts of each aspect type
    if output in ("text", "html"):
        print(f"{p}{table}{br}{aspect_count_text}")
    if output in ("return_text", "return_html"):
        to_return += f"{br}" + table + aspect_count_text

    # House counts
    if not notime:
        if output in ("return_text", "return_html"):
            if output == "return_html":
                to_return += f"{p}"
            to_return += house_count(house_counts, output, bold, nobold, br)
            if output == "return_html":
                to_return += "</div>"
        else:
            if output == "html":
                print(p)
            print(house_count(house_counts, output, bold, nobold, br))
            if output == "html":
                print("</div>")

    if output == "return_html":
        if all_stars:
            to_return += "</div>"
        to_return += "</div>"
    if output == "html":
        if all_stars:
            print("</div>")
        print("</div>")

    return to_return
