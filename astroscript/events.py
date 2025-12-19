from datetime import datetime, timedelta

import pytz

import db_manager

from .time_utils import convert_to_utc

def get_davison_data(names, guid=None):
    datetimes = []
    longitudes = []
    latitudes = []
    altitudes = []

    ### NEED TO CHECK NOTIME FOR EVENTS HERE
    for name in names:
        name = name.strip()
        event = db_manager.get_event(name, guid)
        if event:
            datetime_str = event["datetime"]
            timezone_str = event["timezone"]
            # print(f'DEBUG: datetime:{event["datetime"]}')
            # print(f'DEBUG: timezone: {event["timezone"]}')
            if timezone_str == "LMT":
                timezone = "LMT"
            else:
                timezone = pytz.timezone(timezone_str)
            try:
                dt = datetime.strptime(datetime_str, "%Y-%m-%dT%H:%M")
            except ValueError as ex:
                try:
                    dt = datetime.strptime(datetime_str, "%Y-%m-%dT%H:%M:%S")
                except ValueError as ex:
                    print(f"Error parsing datetime for {name}: ({ex})")
            # dt_with_tz = timezone.localize(dt)
            utc_datetime = convert_to_utc(dt, timezone)
            datetimes.append(utc_datetime.astimezone(pytz.utc))
            # datetimes.append(dt_with_tz)
            longitudes.append(event["longitude"])
            latitudes.append(event["latitude"])
            altitudes.append(event["altitude"])
        else:
            print(
                f"\nNo data found for {name}. First create the event by specifying the event details including the name.\n"
            )

    if datetimes:
        total_seconds = sum(
            (
                dt.astimezone(pytz.utc) - datetime(1970, 1, 1, tzinfo=pytz.utc)
            ).total_seconds()
            for dt in datetimes
        )
        avg_seconds = total_seconds / len(datetimes)
        avg_datetime_utc = datetime(1970, 1, 1, tzinfo=pytz.utc) + timedelta(
            seconds=avg_seconds
        )
        avg_datetime_naive = avg_datetime_utc.replace(tzinfo=None)
    else:
        avg_datetime_str = "No datetimes to average"

    # Calculate the average longitude and latitude
    avg_longitude = (
        sum(longitudes) / len(longitudes) if longitudes else "No longitudes to average"
    )
    avg_latitude = (
        sum(latitudes) / len(latitudes) if latitudes else "No latitudes to average"
    )
    avg_altitude = (
        sum(altitudes) / len(altitudes) if altitudes else "No altitudes to average"
    )

    # Store the location in the db
    db_manager.save_location(
        str(avg_latitude) + "," + str(avg_longitude),
        avg_latitude,
        avg_longitude,
        avg_altitude,
    )

    return avg_datetime_naive, avg_longitude, avg_latitude, avg_altitude


def load_event(name, guid=None):
    """
    Load event details from a SQL database file based on the given event name.

    Attempts to read from a specified file and retrieve event information for a named event.
    If successful, returns the event details; otherwise, provides an appropriate message.

    Parameters:
    - name (str): The name of the event to retrieve information for.

    Returns:
    - dict or bool: Event details as a dictionary if found, False otherwise.

    Raises:
    - FileNotFoundError: If the specified file does not exist.
    """

    event = db_manager.get_event(name, guid=guid)
    if event:
        return {
            "name": name,
            "location": event["location"],
            "datetime": event["datetime"],
            "timezone": event["timezone"],
            "latitude": event["latitude"],
            "longitude": event["longitude"],
            "altitude": event["altitude"],
            "notime": event["notime"],
        }
    else:
        print(f"No entry found for {name}.")
        return False
