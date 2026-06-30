import os
import uuid
from datetime import timezone
from pathlib import Path
from urllib.parse import quote
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from astroscript.constants import HOUSE_SYSTEMS
from astroscript.zodiac import is_sidereal


KERYKEION_HOUSE_SYSTEM_ALIASES = {
    "E": "N",  # Swiss Ephemeris: Equal, first house fixed at 0 Aries.
}
KERYKEION_PERSPECTIVES = {
    "geocentric": "Apparent Geocentric",
    "heliocentric": "Heliocentric",
    "topocentric": "Topocentric",
}
HELIOCENTRIC_EXCLUDED_POINTS = {
    "Sun",
    "Moon",
    "Mean_North_Lunar_Node",
    "True_North_Lunar_Node",
    "Mean_South_Lunar_Node",
    "True_South_Lunar_Node",
    "Mean_Lilith",
    "True_Lilith",
    "Ascendant",
    "Medium_Coeli",
    "Descendant",
    "Imum_Coeli",
}


def normalize_chart_theme(chart_theme):
    return "dark" if chart_theme == "dark" else "classic"


def default_chart_filename(name, chart_type):
    subject_name = (name or "Chart").strip() or "Chart"
    chart_type_name = chart_type.strip()
    return f"{subject_name} - {chart_type_name} Chart.svg"


def dark_chart_filename(name, chart_type):
    subject_name = (name or "Chart").strip() or "Chart"
    chart_type_name = chart_type.strip()
    return f"{subject_name} - {chart_type_name} Chart Dark.svg"


def _django_output_paths(chart_folder):
    try:
        from django.conf import settings

        if settings.configured:
            return (
                Path(settings.MEDIA_ROOT) / "generated_charts" / chart_folder,
                f"/chart-image/{quote(chart_folder)}",
            )
    except Exception:
        pass
    return None


def _standalone_output_paths(chart_folder):
    folder = "media" if os.getenv("PRODUCTION_EPHE") else "static"
    folder_slash = "/" if os.getenv("PRODUCTION_EPHE") else ""
    project_root = Path(__file__).resolve().parents[2]
    return project_root / folder / chart_folder, f"{folder_slash}{folder}/{quote(chart_folder)}"


def _output_paths(chart_folder):
    return _django_output_paths(chart_folder) or _standalone_output_paths(chart_folder)


def normalize_house_system_identifier(house_system):
    identifier = HOUSE_SYSTEMS.get(house_system, house_system or "P")
    identifier = KERYKEION_HOUSE_SYSTEM_ALIASES.get(identifier, identifier)
    return None if identifier == "G" else identifier


def normalize_perspective(center):
    return KERYKEION_PERSPECTIVES.get(
        (center or "topocentric").strip().lower(),
        "Topocentric",
    )


def kerykeion_active_points(default_active_points, node, center):
    active_points = list(default_active_points)
    if (node or "true").strip().lower() == "mean":
        replacements = {
            "True_North_Lunar_Node": "Mean_North_Lunar_Node",
            "True_South_Lunar_Node": "Mean_South_Lunar_Node",
        }
        active_points = [replacements.get(point, point) for point in active_points]

    if (center or "topocentric").strip().lower() == "heliocentric":
        active_points = [
            point
            for point in active_points
            if point not in HELIOCENTRIC_EXCLUDED_POINTS
        ]
        if "Earth" not in active_points:
            active_points.append("Earth")

    return active_points


def kerykeion_local_datetime(utc_datetime, local_timezone):
    if utc_datetime.tzinfo is None:
        utc_datetime = utc_datetime.replace(tzinfo=timezone.utc)

    timezone_name = (
        getattr(local_timezone, "zone", None)
        or getattr(local_timezone, "key", None)
        or str(local_timezone or "UTC")
    )
    try:
        target_timezone = ZoneInfo(timezone_name)
    except (ValueError, ZoneInfoNotFoundError):
        timezone_name = "UTC"
        target_timezone = timezone.utc

    return utc_datetime.astimezone(target_timezone), timezone_name


def create_subject(
    subject_factory,
    name,
    utc_datetime,
    longitude,
    latitude,
    local_timezone,
    place,
    subject_settings,
):
    local_datetime, timezone_name = kerykeion_local_datetime(
        utc_datetime,
        local_timezone,
    )
    return subject_factory.from_birth_data(
        name=name,
        year=local_datetime.year,
        month=local_datetime.month,
        day=local_datetime.day,
        hour=local_datetime.hour,
        minute=local_datetime.minute,
        seconds=local_datetime.second,
        lng=longitude,
        lat=latitude,
        tz_str=timezone_name,
        city=place,
        nation="GB",
        online=False,
        **subject_settings,
    )


def chart_output(
    name,
    utc_datetime,
    longitude,
    latitude,
    local_timezone,
    place,
    chart_type,
    output_type,
    second_datetime,
    second_name=None,
    second_longitude=None,
    second_latitude=None,
    second_local_timezone=None,
    second_place=None,
    guid=None,
    chart_theme=None,
    zodiac="tropical",
    house_system="Placidus",
    center="topocentric",
    node="true",
):
    chart_folder = str(guid or uuid.uuid4().hex)
    output_directory, chart_url_prefix = _output_paths(chart_folder)

    try:
        from kerykeion import AstrologicalSubjectFactory, ChartDataFactory, ChartDrawer
        from kerykeion.settings.config_constants import DEFAULT_ACTIVE_POINTS
    except ImportError:
        if output_type == "html":
            print(
                "<br><p><h5>Please install the kerykeion package using "
                "'pip install kerykeion' for graphical output of the chart.</h5></p>"
            )
        else:
            print(
                "\n\nPlease install the kerykeion package using "
                "'pip install kerykeion' for graphical output of the chart."
            )
        return (
            "Please install the kerykeion package using 'pip install kerykeion' "
            "for graphical output of the chart."
        )

    subject_name = (name or "Chart").strip() or "Chart"
    kerykeion_theme = normalize_chart_theme(chart_theme)
    houses_system_identifier = normalize_house_system_identifier(house_system)
    if houses_system_identifier is None:
        return (
            '<p class="text-muted">The SVG chart is unavailable for Gauquelin '
            "sectors; the calculated text remains available.</p>"
        )

    active_points = kerykeion_active_points(DEFAULT_ACTIVE_POINTS, node, center)
    subject_settings = {
        "houses_system_identifier": houses_system_identifier,
        "perspective_type": normalize_perspective(center),
        "active_points": active_points,
    }
    if is_sidereal(zodiac):
        subject_settings.update(zodiac_type="Sidereal", sidereal_mode="LAHIRI")

    chart_filename = default_chart_filename(subject_name, chart_type)
    output_chart_filename = (
        dark_chart_filename(subject_name, chart_type)
        if kerykeion_theme == "dark"
        else chart_filename
    )

    subject = create_subject(
        AstrologicalSubjectFactory,
        subject_name,
        utc_datetime,
        longitude,
        latitude,
        local_timezone,
        place,
        subject_settings,
    )
    second_subject = None
    if chart_type in ("Transit", "Synastry"):
        second_subject_name = (name if chart_type == "Transit" else second_name) or ""
        second_subject = create_subject(
            AstrologicalSubjectFactory,
            second_subject_name.strip() or "Chart",
            second_datetime,
            second_longitude,
            second_latitude,
            second_local_timezone,
            second_place,
            subject_settings,
        )

    if chart_type == "Natal":
        chart_data = ChartDataFactory.create_natal_chart_data(
            subject,
            active_points=active_points,
        )
    elif chart_type == "Transit":
        chart_data = ChartDataFactory.create_transit_chart_data(
            subject,
            second_subject,
            active_points=active_points,
        )
    elif chart_type == "Synastry":
        chart_data = ChartDataFactory.create_synastry_chart_data(
            subject,
            second_subject,
            active_points=active_points,
        )
    else:
        return f"Unsupported chart type: {chart_type}"

    os.makedirs(output_directory, exist_ok=True)
    chart = ChartDrawer(chart_data, theme=kerykeion_theme)
    chart.save_svg(
        output_path=output_directory,
        filename=output_chart_filename.removesuffix(".svg"),
    )

    chart_url = f"{chart_url_prefix}/{quote(output_chart_filename)}"
    print(
        f'</div></table><p><img src="{output_directory}/{output_chart_filename}" '
        'alt="Astrological Chart" width="100%" height="100%">'
    )
    return (
        f'</div></table><p><img src="{chart_url}" alt="Astrological Chart" '
        'width="100%" height="100%" style="z-index: 1000; position: relative;">'
    )
