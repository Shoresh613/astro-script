from kerykeion import AstrologicalSubject, KerykeionChartSVG

def chart_output(name, utc_datetime, longitude, latitude, local_timezone, place):
    subject = AstrologicalSubject(name, utc_datetime=utc_datetime, year=utc_datetime.year, month=utc_datetime.month,
                                        day=utc_datetime.day, hour=utc_datetime.hour, minute=utc_datetime.minute, lng=longitude, lat=latitude,
                                    tz_str=str(local_timezone), city = place, nation="GB", online=False)

    chart = KerykeionChartSVG(subject, chart_type="Natal", new_output_directory="./")
    chart.makeSVG()
    #include the chart in the html output
    if name:
        print(f'<img src="{chart.output_directory}/{name.strip()}NatalChart.svg" alt="Astrological Chart" width="100%" height="100%">')