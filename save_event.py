import json
import os
from datetime import datetime

# Function to update or add new entries to the JSON file
def update_json_file(filename, new_data):
    # Check if the file exists
    if os.path.exists(filename):
        # File exists, so read the current data
        with open(filename, 'r') as file:
            try:
                data = json.load(file)
            except json.JSONDecodeError:
                # File is empty or corrupted
                data = {}
    else:
        # File does not exist, start with an empty dictionary
        data = {}

    # Update the dictionary with new_data
    # This will add new entries and update existing ones with the same keys
    data.update(new_data)

    # Write the updated dictionary back to the file
    with open(filename, 'w') as file:
        json.dump(data, file, indent=4)

# Example new data to add/update
new_people_data = {
    "John Doe": {
        "location": "Gothenburg, Sweden",
        "datetime": datetime(1990, 5, 24, 14, 30).isoformat(),
        "latitude": 57.7089,
        "longitude": 11.9746
    },
    "Alice Johnson": {
        "location": "Malmö, Sweden",
        "datetime": datetime(1992, 11, 5, 8, 45).isoformat(),
        "latitude": 55.6050,
        "longitude": 13.0038
    },
    "Pelle Hansson": {
        "location": "Stockholm, Sweden",
        "datetime": datetime(1932, 3, 12, 10, 45).isoformat(),
        "latitude": 555.6050,
        "longitude": 13.0038
    },
}

# Specify the filename where you want to save/update the JSON data
filename = 'saved_events.json'  # Adjust the path as necessary

# Update the JSON file with new data
update_json_file(filename, new_people_data)

print(f"Data updated in {filename}")
