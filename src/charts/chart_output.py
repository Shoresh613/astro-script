import os
from pathlib import Path


def normalize_chart_theme(chart_theme):
    return "dark" if chart_theme == "dark" else "classic"


def default_chart_filename(name, chart_type):
    subject_name = (name or "").strip()
    chart_type_name = chart_type.strip()
    if subject_name:
        return f"{subject_name} - {chart_type_name} Chart.svg"
    return f" - {chart_type_name} Chart.svg"


def dark_chart_filename(name, chart_type):
    subject_name = (name or "").strip()
    chart_type_name = chart_type.strip()
    if subject_name:
        return f"{subject_name} - {chart_type_name} Chart Dark.svg"
    return f" - {chart_type_name} Chart Dark.svg"


def legacy_chart_filename(name, chart_type):
    subject_name = (name or "").strip()
    chart_type_name = chart_type.strip()
    if subject_name:
        return f"{subject_name} {chart_type_name}Chart.svg"
    return f"{chart_type_name}Chart.svg"


def chart_output(name, utc_datetime, longitude, latitude, local_timezone, place, chart_type, output_type, second_datetime, second_name=None, second_longitude=None, second_latitude=None, second_local_timezone=None, second_place=None, guid=None, chart_theme=None):

    if os.getenv("PRODUCTION_EPHE"):
        folder = "media"
        folder_slash = "/"
    else:
        folder = "static"
        folder_slash = ""

    THIS_FOLDER = Path(__file__).resolve().parents[2]

    try:
        from kerykeion import AstrologicalSubject, KerykeionChartSVG
    except ImportError:
        if output_type == 'html':
            print("<br><p><h5>Please install the kerykeion package using 'pip install kerykeion' for graphical output of the chart.</h5></p>")
        else:
            print("\n\nPlease install the kerykeion package using 'pip install kerykeion' for graphical output of the chart.")
        return "Please install the kerykeion package using 'pip install kerykeion' for graphical output of the chart."

    kerykeion_theme = normalize_chart_theme(chart_theme)
    chart_filename = default_chart_filename(name, chart_type)
    output_chart_filename = (
        dark_chart_filename(name, chart_type)
        if kerykeion_theme == "dark"
        else chart_filename
    )

    subject = AstrologicalSubject(name, utc_datetime=utc_datetime, year=utc_datetime.year, month=utc_datetime.month,
                                        day=utc_datetime.day, hour=utc_datetime.hour, minute=utc_datetime.minute, lng=longitude, lat=latitude,
                                    tz_str=str(local_timezone), city = place, nation="GB", online=False)
    if chart_type in ("Transit", "Synastry"):
        second_subject = AstrologicalSubject(name if chart_type=="Transit" else second_name, utc_datetime=second_datetime, year=second_datetime.year, month=second_datetime.month,
                                        day=second_datetime.day, hour=second_datetime.hour, minute=second_datetime.minute, lng=second_longitude, lat=second_latitude,
                                    tz_str=str(second_local_timezone), city = second_place, nation="GB", online=False)

    if chart_type == "Natal":
        if output_type=='html':
            chart = KerykeionChartSVG(subject, chart_type, new_output_directory=f"{THIS_FOLDER}", theme=kerykeion_theme)
        else:
            chart = KerykeionChartSVG(subject, chart_type, new_output_directory=f"{THIS_FOLDER}/{folder}/{guid}", theme=kerykeion_theme)
    elif chart_type in ("Transit", "Synastry"):
        if output_type=='html':
            chart = KerykeionChartSVG(subject, chart_type, second_subject, new_output_directory=f"{THIS_FOLDER}/", theme=kerykeion_theme)
        else:
            chart = KerykeionChartSVG(subject, chart_type, second_subject, new_output_directory=f"{THIS_FOLDER}/{folder}/{guid}", theme=kerykeion_theme)
    if output_type == 'html':
        output_directory = THIS_FOLDER
    else:
        output_directory = f"{THIS_FOLDER}/{folder}/{guid}"
    
    os.makedirs(output_directory, exist_ok=True)

    chart.makeSVG()
    if output_chart_filename != chart_filename:
        generated_chart = Path(output_directory) / chart_filename
        legacy_chart = Path(output_directory) / legacy_chart_filename(name, chart_type)
        themed_chart = Path(output_directory) / output_chart_filename
        if generated_chart.exists():
            generated_chart.replace(themed_chart)
        elif legacy_chart.exists():
            legacy_chart.replace(themed_chart)

    image_filename = output_chart_filename if kerykeion_theme == "dark" else legacy_chart_filename(name, chart_type)
    print(f'</div></table><p><img src="{chart.output_directory}/{image_filename}" alt="Astrological Chart" width="100%" height="100%">')
    if name:
        if os.getenv("PRODUCTION_EPHE"):
            return f'</div></table><p><img src="{folder_slash}{folder}/{guid}/{image_filename}" alt="Astrological Chart" width="100%" height="100%" style="z-index: 1000; position: relative;>'
        else:
            return f'</div></table><p><img src="{folder_slash}{folder}/{guid}/{image_filename}" alt="Astrological Chart" width="100%" height="100%" style="z-index: 1000; position: relative;>'
    else:
        if os.getenv("PRODUCTION_EPHE"):
            if guid == None:
                return f'</div></table><p><img src="{folder_slash}{folder}/None/{image_filename}" alt="Astrological Chart" width="100%" height="100%" style="z-index: 1000; position: relative;>'
            else:
                return f'</div></table><p><img src="{folder_slash}{folder}/{guid}/{image_filename}" alt="Astrological Chart" width="100%" height="100%" style="z-index: 1000; position: relative;>'
        else:
            return f'</div></table><p><img src="{folder_slash}{folder}/{guid}/{image_filename}" alt="Astrological Chart" width="100%" height="100%" style="z-index: 1000; position: relative;>'

    #     return f'</div></table><p><img src="static/{guid}/{name.strip()} {chart_type.strip()}Chart.svg" alt="Astrological Chart" width="100%" height="100%" style="z-index: 1000; position: relative;>'
    # else:
    #     return f'</div></table><p><img src="static/{guid}/{chart_type.strip()}Chart.svg" alt="Astrological Chart" width="100%" height="100%" style="z-index: 1000; position: relative;>'

    # elif output_type == 'return_html':
    #     chart.makeSVG(output_directory)
    #     return f'<p><img src="{output_directory}/{name.strip()} {chart_type.strip()}Chart.svg" alt="Astrological Chart" width="100%" height="100%">'
