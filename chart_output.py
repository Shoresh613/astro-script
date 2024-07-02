import os

def chart_output(name, utc_datetime, longitude, latitude, local_timezone, place, chart_type, output_type, second_datetime, second_name=None, second_longitude=None, second_latitude=None, second_local_timezone=None, second_place=None, guid=None):

    if os.getenv("PRODUCTION_EPHE"):
        folder = "media"
    else:
        folder = "static"

    try:
        from kerykeion import AstrologicalSubject, KerykeionChartSVG
    except ImportError:
        if output_type == 'html':
            print("<br><p><h5>Please install the kerykeion package using 'pip install kerykeion' for graphical output of the chart.</h5></p>")
        else:
            print("\n\nPlease install the kerykeion package using 'pip install kerykeion' for graphical output of the chart.")
        return "Please install the kerykeion package using 'pip install kerykeion' for graphical output of the chart."

    subject = AstrologicalSubject(name, utc_datetime=utc_datetime, year=utc_datetime.year, month=utc_datetime.month,
                                        day=utc_datetime.day, hour=utc_datetime.hour, minute=utc_datetime.minute, lng=longitude, lat=latitude,
                                    tz_str=str(local_timezone), city = place, nation="GB", online=False)
    if chart_type in ("Transit", "Synastry"):
        second_subject = AstrologicalSubject(name if chart_type=="Transit" else second_name, utc_datetime=second_datetime, year=second_datetime.year, month=second_datetime.month,
                                        day=second_datetime.day, hour=second_datetime.hour, minute=second_datetime.minute, lng=second_longitude, lat=second_latitude,
                                    tz_str=str(second_local_timezone), city = second_place, nation="GB", online=False)

    if chart_type == "Natal":
        if output_type=='html':
            chart = KerykeionChartSVG(subject, chart_type, new_output_directory="./")
        else:
            chart = KerykeionChartSVG(subject, chart_type, new_output_directory=f"./{folder}/{guid}")
    elif chart_type in ("Transit", "Synastry"):
        if output_type=='html':
            chart = KerykeionChartSVG(subject, chart_type, second_subject, new_output_directory="./")
        else:
            chart = KerykeionChartSVG(subject, chart_type, second_subject, new_output_directory=f"./{folder}/{guid}")
    if output_type == 'html':
        output_directory = "."
    else:
        output_directory = f"./{folder}/{guid}"
    
    os.makedirs(output_directory, exist_ok=True)

    chart.makeSVG()
    print(f'</div></table><p><img src="{chart.output_directory}/{name.strip()} {chart_type.strip()}Chart.svg" alt="Astrological Chart" width="100%" height="100%">')
    if name:
        return f'</div></table><p><img src="{folder}/{guid}/{name.strip()} {chart_type.strip()}Chart.svg" alt="Astrological Chart" width="100%" height="100%" style="z-index: 1000; position: relative;>'
    else:
        return f'</div></table><p><img src="{folder}/{guid}/{chart_type.strip()}Chart.svg" alt="Astrological Chart" width="100%" height="100%" style="z-index: 1000; position: relative;>'

    #     return f'</div></table><p><img src="static/{guid}/{name.strip()} {chart_type.strip()}Chart.svg" alt="Astrological Chart" width="100%" height="100%" style="z-index: 1000; position: relative;>'
    # else:
    #     return f'</div></table><p><img src="static/{guid}/{chart_type.strip()}Chart.svg" alt="Astrological Chart" width="100%" height="100%" style="z-index: 1000; position: relative;>'

    # elif output_type == 'return_html':
    #     chart.makeSVG(output_directory)
    #     return f'<p><img src="{output_directory}/{name.strip()} {chart_type.strip()}Chart.svg" alt="Astrological Chart" width="100%" height="100%">'