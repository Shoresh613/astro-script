# AstroScript

AstroScript is a powerful astrology software tool designed to calculate astrological data that can be used for interpretations. It leverages the Swiss Ephemeris for precise planetary and house calculations, and offers extensive features including planet positions, house positions, aspect calculations, and fixed star conjunctions.

## Features

- **Planetary Calculations**: Provides detailed longitude, zodiac sign, and retrograde information for all major and some minor celestial bodies.
- **House Calculations**: Supports multiple house systems, including Placidus, Koch, and others, for accurate astrological house placement.
- **Aspect Analysis**: Calculates major and minor astrological aspects between planets and fixed stars.
- **Moon Phase Calculation**: Determines the current phase of the Moon and its illumination.
- **Fixed Star Aspects**: Lists aspects between planets and fixed stars, considering the house placement of each fixed star.
- **Location Handling**: Uses Nominatim via the geopy library to convert location names to geographic coordinates, with the ability to save and retrieve frequently used locations.

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Shoresh613/astro-script.git
   cd AstroScript
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up the ephemeris:**
   - Download the necessary ephemeris files from [http://www.astro.com/swisseph/](http://www.astro.com/swisseph/)
   - Place them in the `./ephe/` directory.

## Usage

### Command Line Interface

You can run AstroScript with the following command:

```bash
python astroscript.py --name "John Doe" --date "2021-12-25 15:30" --location "New York, USA"
```


### Options

- `--name`: Name of the person or event.
- `--date`: Date and time of the event in local time (format: YYYY-MM-DD HH:MM:SS).
- `--location`: Location name for looking up geographic coordinates.
- `--latitude` and `--longitude`: Specific latitude and longitude to use.
- `--timezone`: Timezone of the location.
- `--house_system`: House system to use, defaults to Placidus.
- `--output_type`: Format of the output (`text`, `return_text`, `html`).

For a complete list of options, call:

```bash
python astroscript.py -h
```

### GUI Integration

AstroScript includes a graphical user interface developed with the Kivy framework, offering a more interactive way to input data and display astrological calculations. Here's a brief overview of the GUI functionalities:

1. **Interactive Forms**: Users can input data through text fields, dropdowns, and date/time pickers.
2. **Responsive Layout**: The GUI adapts to different device screen sizes, making it usable on both desktop and mobile platforms.
3. **Real-Time Results Display**: Calculations are shown immediately on the screen, with options to navigate between input and results screens easily. The results can be copied to clipboard.
4. **Customizable Options**: Users can choose different astrological options such as house systems, aspects types, and whether to include minor aspects.

#### Running the GUI

To launch the GUI, run the following command:

```bash
python main.py
```

This starts the application, where you can navigate through the input screen to enter event details and view calculated results in real-time.

## File Management

AstroScript interacts with various files to store and retrieve data, enhancing functionality and user experience.

### Ephemeris Files

- **Location**: `./ephe/`
- **Purpose**: Store astronomical data needed for precise planetary calculations.
- **Setup**: Users must download these files from external sources (e.g., [http://www.astro.com/swisseph/](http://www.astro.com/swisseph/)) and place them in the designated directory.

### Location Files

- **Filename**: `saved_locations.json`
- **Purpose**: Saves geographic coordinates of frequently used locations to minimize repeated API calls.
- **Usage**: Automatically updated when users add new locations through the GUI or script.

### Event Files

- **Filename**: `saved_events.json`
- **Purpose**: Stores details of astrological events, such as dates, times, and locations, for quick retrieval.
- **Usage**: Users can save event details for future reference, which facilitates repeated analyses without re-entering data. This is done automatically whenever a name is given as an argument.

### Time Zone Files

- **Filename**: `timezones.txt`
- **Purpose**: Lists available time zones used for accurate time conversions.
- **Usage**: Read by the system to populate time zone options in the GUI, ensuring that users can select their appropriate time zone easily.

These files are crucial for AstroScript's operation, allowing it to perform accurate calculations and provide a seamless user experience. Users are encouraged to back up these files regularly, especially if they store important event data.

## Font Management

AstroScript's GUI utilizes custom fonts to enhance the readability of the results. Here are details on the font used:

### Roboto Mono

- **Font Family**: Roboto Mono
- **Usage**: This monospaced font is used when showing the results in the GUI, ensuring clear and consistent readability.
- **Location**: Fonts are stored under the `fonts/` directory.
- **Setup**: The Roboto Mono font files are included with the application (see licence information). Users do not need to install or manage these fonts separately.

## To do
I'm working on getting Buildozer package it as an Android package for installing as an app. That's the big thing. Then there are smaller things.

## Contributing

Contributions to AstroScript are welcome! Please fork the repository and submit pull requests with your enhancements, or open issues for any bugs or new feature requests.

## License

This project is licensed under the MIT License - see the LICENSE.md file for details.
