import os
import uuid
from pathlib import Path
from urllib.parse import quote

from astroscript.zodiac import is_sidereal


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


def legacy_chart_filename(name, chart_type):
    subject_name = (name or "").strip()
    chart_type_name = chart_type.strip()
    if subject_name:
        return f"{subject_name} {chart_type_name}Chart.svg"
    return f"{chart_type_name}Chart.svg"


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
):
    chart_folder = str(guid or uuid.uuid4().hex)
    output_directory, chart_url_prefix = _output_paths(chart_folder)

    try:
        from kerykeion import AstrologicalSubject, KerykeionChartSVG
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
    chart_filename = default_chart_filename(subject_name, chart_type)
    output_chart_filename = (
        dark_chart_filename(subject_name, chart_type)
        if kerykeion_theme == "dark"
        else chart_filename
    )

    subject_kwargs = {
        "year": utc_datetime.year,
        "month": utc_datetime.month,
        "day": utc_datetime.day,
        "hour": utc_datetime.hour,
        "minute": utc_datetime.minute,
        "lng": longitude,
        "lat": latitude,
        "tz_str": str(local_timezone),
        "city": place,
        "nation": "GB",
        "online": False,
    }
    if is_sidereal(zodiac):
        subject_kwargs.update(zodiac_type="Sidereal", sidereal_mode="LAHIRI")

    subject = AstrologicalSubject(subject_name, **subject_kwargs)
    if chart_type in ("Transit", "Synastry"):
        second_subject_name = (name if chart_type == "Transit" else second_name) or ""
        second_subject_kwargs = {
            "year": second_datetime.year,
            "month": second_datetime.month,
            "day": second_datetime.day,
            "hour": second_datetime.hour,
            "minute": second_datetime.minute,
            "lng": second_longitude,
            "lat": second_latitude,
            "tz_str": str(second_local_timezone),
            "city": second_place,
            "nation": "GB",
            "online": False,
        }
        if is_sidereal(zodiac):
            second_subject_kwargs.update(
                zodiac_type="Sidereal", sidereal_mode="LAHIRI"
            )
        second_subject = AstrologicalSubject(
            second_subject_name.strip() or "Chart", **second_subject_kwargs
        )

    if chart_type == "Natal":
        chart = KerykeionChartSVG(
            subject,
            chart_type,
            new_output_directory=str(output_directory),
            theme=kerykeion_theme,
        )
    elif chart_type in ("Transit", "Synastry"):
        chart = KerykeionChartSVG(
            subject,
            chart_type,
            second_subject,
            new_output_directory=str(output_directory),
            theme=kerykeion_theme,
        )
    else:
        return f"Unsupported chart type: {chart_type}"

    os.makedirs(output_directory, exist_ok=True)
    chart.makeSVG()

    if output_chart_filename != chart_filename:
        generated_chart = output_directory / chart_filename
        legacy_chart = output_directory / legacy_chart_filename(subject_name, chart_type)
        themed_chart = output_directory / output_chart_filename
        if generated_chart.exists():
            generated_chart.replace(themed_chart)
        elif legacy_chart.exists():
            legacy_chart.replace(themed_chart)

    chart_url = f"{chart_url_prefix}/{quote(output_chart_filename)}"
    print(
        f'</div></table><p><img src="{chart.output_directory}/{output_chart_filename}" '
        'alt="Astrological Chart" width="100%" height="100%">'
    )
    return (
        f'</div></table><p><img src="{chart_url}" alt="Astrological Chart" '
        'width="100%" height="100%" style="z-index: 1000; position: relative;">'
    )
