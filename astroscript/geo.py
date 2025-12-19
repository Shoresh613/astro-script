from geopy.geocoders import Nominatim
import requests

import db_manager

def get_coordinates(location_name: str):
    """
    Returns the geographic coordinates (latitude, longitude) of a specified location name.

    Loads the coordinates from a JSON file if the location has been previously saved, othwerwise
    utilizes the Nominatim geocoder from the geopy library to convert a location name (such as a street address,
    city, or country) into geographic coordinates. The function is initialized with a user_agent named
    "AstroScript" for the Nominatim API, which has a limit of 1 request/second.
    Saves the coordinates to a JSON file, so that internet access and API calls are minimized.

    Parameters:
    - location_name (str): The name of the location for which to obtain geographic coordinates.

    Returns:
    - tuple: A tuple containing the latitude, longitude and altitude of the specified location.

    Note:
    - The accuracy of the coordinates returned depends on the specificity of the location name provided.
    - Ensure compliance with Nominatim's usage policy when using this function.
    """

    location_details = db_manager.load_location(location_name)
    if location_details:
        return (
            location_details[0],
            location_details[1],
            location_details[2],
        )  # Latitude, Longitude, Altitude
    else:
        try:
            geolocator = Nominatim(user_agent="AstroScript")
        except Exception as e:
            print(f"Error initializing geolocator: {e}")
            return None, None, None

        try:
            location = geolocator.geocode(location_name)
        except Exception as e:
            print(
                f"Error getting location {location_name}, check internet connection, spelling, choose nearby location, or specify place using --place and enter coordinates using --latitude, --longitude: {e}"
            )
            return None, None, None
        if location is None:
            db_manager.save_location(location_name, None, None, None)
            return None, None, None
        altitude = get_altitude(location.latitude, location.longitude, location_name)

        db_manager.save_location(
            location_name, location.latitude, location.longitude, altitude
        )

        return location.latitude, location.longitude, altitude


def get_altitude(lat, lon, location_name):

    if location_name != "Davison chart":
        location_details = db_manager.load_location(location_name)
        if location_details:
            return location_details[2]  # Altitude

    try:
        url = f"https://api.open-elevation.com/api/v1/lookup?locations={lat},{lon}"
        response = requests.get(url)
        results = response.json()["results"]
        if results:
            return results[0]["elevation"]
    except Exception as e:
        print(f"Error getting altitude: {e}")
        return None
