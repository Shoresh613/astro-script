def chart_output(name, utc_datetime, longitude, latitude, local_timezone, place, chart_type, second_datetime, second_name=None, second_longitude=None, second_latitude=None, second_local_timezone=None, second_place=None):
    try:
        from kerykeion import AstrologicalSubject, KerykeionChartSVG
    except ImportError:
        print("<br><p><h5>Please install the kerykeion package using 'pip install kerykeion' for graphical output of the chart.</h5></p>")
        return

    subject = AstrologicalSubject(name, utc_datetime=utc_datetime, year=utc_datetime.year, month=utc_datetime.month,
                                        day=utc_datetime.day, hour=utc_datetime.hour, minute=utc_datetime.minute, lng=longitude, lat=latitude,
                                    tz_str=str(local_timezone), city = place, nation="GB", online=False)
    if chart_type in ("Transit", "Synastry"):
        second_subject = AstrologicalSubject(name if chart_type=="Transit" else second_name, utc_datetime=second_datetime, year=second_datetime.year, month=second_datetime.month,
                                        day=second_datetime.day, hour=second_datetime.hour, minute=second_datetime.minute, lng=second_longitude, lat=second_latitude,
                                    tz_str=str(second_local_timezone), city = second_place, nation="GB", online=False)

    if chart_type == "Natal":
        chart = KerykeionChartSVG(subject, chart_type, new_output_directory="./")
    elif chart_type in ("Transit", "Synastry"):
        chart = KerykeionChartSVG(subject, chart_type, second_subject, new_output_directory="./")

    chart.makeSVG()
    #include the chart in the html output
    if name:
        print(f'<p><img src="{chart.output_directory}/{name.strip()} {chart_type.strip()}Chart.svg" alt="Astrological Chart" width="100%" height="100%">')