# AstroScript Constants File
# This file contains all constants, long dictionaries, and static HTML used in AstroScript

import swisseph as swe

############### ASPECT CONSTANTS ###############

ASPECT_TYPES = {
    "Conjunction": 0,
    "Opposition": 180,
    "Trine": 120,
    "Square": 90,
    "Sextile": 60,
}

MINOR_ASPECT_TYPES = {
    "Quincunx": 150,
    "Semi-Sextile": 30,
    "Semi-Square": 45,
    "Quintile": 72,
    "Bi-Quintile": 144,
    "Sesqui-Square": 135,
    "Septile": 51.4285714,
    "Novile": 40,
    "Decile": 36,
}

MAJOR_ASPECTS = {
    "Conjunction": {
        "Degrees": 0,
        "Score": 40,
        "Comment": "Impactful, varies by planets involved.",
    },
    "Opposition": {
        "Degrees": 180,
        "Score": 10,
        "Comment": "Polarities needing integration.",
    },
    "Square": {"Degrees": 90, "Score": 15, "Comment": "Tension and obstacles."},
    "Trine": {"Degrees": 120, "Score": 90, "Comment": "Promotes ease and talents."},
    "Sextile": {"Degrees": 60, "Score": 80, "Comment": "Opportunities and support."},
}

MINOR_ASPECTS = {
    "Semi-Square": {
        "Degrees": 45,
        "Score": 25,
        "Comment": "Friction and minor challenges.",
    },
    "Sesqui-Square": {
        "Degrees": 135,
        "Score": 20,
        "Comment": "Less intense square, irritation.",
    },
    "Semi-Sextile": {
        "Degrees": 30,
        "Score": 70,
        "Comment": "Slightly beneficial, subtle.",
    },
    "Quincunx": {
        "Degrees": 150,
        "Score": 30,
        "Comment": "Adjustment and misunderstandings.",
    },
    "Quintile": {"Degrees": 72, "Score": 75, "Comment": "Creativity and talent."},
    "Bi-Quintile": {
        "Degrees": 144,
        "Score": 75,
        "Comment": "Creative expression, like quintile.",
    },
    "Septile": {
        "Degrees": 51.4285714,
        "Score": 60,
        "Comment": "Spiritual insights, less tangible.",
    },
    "Novile": {
        "Degrees": 40,
        "Score": 65,
        "Comment": "Spiritual insights, harmonious.",
    },
    "Decile": {
        "Degrees": 36,
        "Score": 50,
        "Comment": "Growth opportunities, mild challenges.",
    },
}

ALL_ASPECTS = {**MAJOR_ASPECTS.copy(), **MINOR_ASPECTS}

# Dictionaries for hard and soft aspects based on the scores
HARD_ASPECTS = {name: info for name, info in ALL_ASPECTS.items() if info["Score"] < 50}
SOFT_ASPECTS = {name: info for name, info in ALL_ASPECTS.items() if info["Score"] >= 50}

############### PLANET AND CELESTIAL BODY CONSTANTS ###############

# Movement per day for each planet in degrees
OFF_BY = {
    "Sun": 1,
    "Moon": 13.2,
    "Mercury": 1.2,
    "Venus": 1.2,
    "Earth": 1,
    "Mars": 0.5,
    "Jupiter": 0.2,
    "Saturn": 0.1,
    "Uranus": 0.04,
    "Neptune": 0.03,
    "Pluto": 0.01,
    "Chiron": 0.02,
    "North Node": 0.05,
    "South Node": 0.05,
    "True Node": 0.05,
    "Lilith": 0.05,
    "Ascendant": 360,
    "Midheaven": 360,
    "IC": 360,
    "DC": 360,
    "Juno": 0.1,
    "Vesta": 0.12,
    "Pallas": 0.09,
    "Pholus": 0.06,
    "Ceres": 0.08,
}

ALWAYS_EXCLUDE_IF_NO_TIME = [
    "Ascendant",
    "Midheaven",
    "IC",
    "DC",
]  # Aspects that are always excluded if no time of day is specified

PLANETS = {
    "Sun": swe.SUN,
    "Moon": swe.MOON,
    "Mercury": swe.MERCURY,
    "Venus": swe.VENUS,
    "Mars": swe.MARS,
    "Jupiter": swe.JUPITER,
    "Saturn": swe.SATURN,
    "Uranus": swe.URANUS,
    "Neptune": swe.NEPTUNE,
    "Pluto": swe.PLUTO,
    "Chiron": swe.CHIRON,
    "Lilith": swe.MEAN_APOG,
    "North Node": swe.TRUE_NODE,
}

PLANET_RETURN_DICT = {
    "Sun": {"constant": swe.SUN, "orbital_period_days": 365.25},
    "Moon": {"constant": swe.MOON, "orbital_period_days": 27.32},
    "Mercury": {"constant": swe.MERCURY, "orbital_period_days": 87.97},
    "Venus": {"constant": swe.VENUS, "orbital_period_days": 224.70},
    "Earth": {"constant": swe.EARTH, "orbital_period_days": 365},
    "Mars": {"constant": swe.MARS, "orbital_period_days": 686.98},  # 687 days
    "Jupiter": {
        "constant": swe.JUPITER,
        "orbital_period_days": 4332.59,  # (11.86 years)
    },
    "Saturn": {
        "constant": swe.SATURN,
        "orbital_period_days": 10759.22,  # (29.46 years)
    },
    "Uranus": {
        "constant": swe.URANUS,
        "orbital_period_days": 30685.49,  # (84.01 years)
    },
    "Neptune": {
        "constant": swe.NEPTUNE,
        "orbital_period_days": 60190.03,  # (164.8 years)
    },
    "Pluto": {"constant": swe.PLUTO, "orbital_period_days": 90560.00},  # (248 years)
}

ASTEROIDS = {
    "Ceres": swe.CERES,
    "Pholus": swe.PHOLUS,
    "Pallas": swe.PALLAS,
    "Juno": swe.JUNO,
    "Vesta": swe.VESTA,
}

############### ZODIAC CONSTANTS ###############

ZODIAC_ELEMENTS = {
    "Aries": "Fire",
    "Taurus": "Earth",
    "Gemini": "Air",
    "Cancer": "Water",
    "Leo": "Fire",
    "Virgo": "Earth",
    "Libra": "Air",
    "Scorpio": "Water",
    "Sagittarius": "Fire",
    "Capricorn": "Earth",
    "Aquarius": "Air",
    "Pisces": "Water",
}

ZODIAC_MODALITIES = {
    "Cardinal": ["Aries", "Cancer", "Libra", "Capricorn"],
    "Fixed": ["Taurus", "Leo", "Scorpio", "Aquarius"],
    "Mutable": ["Gemini", "Virgo", "Sagittarius", "Pisces"],
}

ZODIAC_SIGN_TO_MODALITY = {
    "Aries": "Cardinal",
    "Taurus": "Fixed",
    "Gemini": "Mutable",
    "Cancer": "Cardinal",
    "Leo": "Fixed",
    "Virgo": "Mutable",
    "Libra": "Cardinal",
    "Scorpio": "Fixed",
    "Sagittarius": "Mutable",
    "Capricorn": "Cardinal",
    "Aquarius": "Fixed",
    "Pisces": "Mutable",
}

ZODIAC_DEGREES = {
    "Aries": 0,
    "Taurus": 30,
    "Gemini": 60,
    "Cancer": 90,
    "Leo": 120,
    "Virgo": 150,
    "Libra": 180,
    "Scorpio": 210,
    "Sagittarius": 240,
    "Capricorn": 270,
    "Aquarius": 300,
    "Pisces": 330,
}

############### DIGNITY CONSTANTS ###############

# Dictionary definitions for planet dignity
RULERSHIP = {
    "Sun": "Leo",
    "Moon": "Cancer",
    "Mercury": ["Gemini", "Virgo"],
    "Venus": ["Taurus", "Libra"],
    "Mars": ["Aries", "Scorpio"],
    "Jupiter": ["Sagittarius", "Pisces"],
    "Saturn": ["Capricorn", "Aquarius"],
    "Uranus": "Aquarius",
    "Neptune": "Pisces",
    "Pluto": "Scorpio",
}

CLASSICAL_RULERSHIP = {
    "Sun": "Leo",
    "Moon": "Cancer",
    "Mercury": ["Gemini", "Virgo"],
    "Venus": ["Taurus", "Libra"],
    "Mars": ["Aries", "Scorpio"],
    "Jupiter": ["Sagittarius", "Pisces"],
    "Saturn": ["Capricorn", "Aquarius"],
}

FORMER_RULERS = {"Mars": "Scorpio", "Jupiter": "Pisces", "Saturn": "Aquarius"}

EXALTATION = {
    "Sun": "Aries",
    "Moon": "Taurus",
    "Mercury": "Virgo",
    "Venus": "Pisces",
    "Mars": "Capricorn",
    "Jupiter": "Cancer",
    "Saturn": "Libra",
    "Uranus": "Scorpio",
    "Neptune": "Leo",
    "Pluto": "Aquarius",
}

DETRIMENT = {
    "Sun": "Aquarius",
    "Moon": "Capricorn",
    "Mercury": ["Sagittarius", "Pisces"],
    "Venus": ["Aries", "Scorpio"],
    "Mars": ["Taurus", "Libra"],
    "Jupiter": ["Gemini", "Virgo"],
    "Saturn": ["Cancer", "Leo"],
    "Uranus": "Leo",
    "Neptune": "Virgo",
    "Pluto": "Taurus",
}

FALL = {
    "Sun": "Libra",
    "Moon": "Scorpio",
    "Mercury": "Pisces",
    "Venus": "Virgo",
    "Mars": "Cancer",
    "Jupiter": "Capricorn",
    "Saturn": "Aries",
    "Uranus": "Taurus",
    "Neptune": "Aquarius",
    "Pluto": "Leo",
}

############### DECAN RULERS ###############

DECAN_RULERS_CLASSICAL = {  # Classical rulers
    "Aries": ["Mars", "Sun", "Jupiter"],
    "Taurus": ["Venus", "Mercury", "Saturn"],
    "Gemini": ["Mercury", "Venus", "Saturn"],
    "Cancer": ["Moon", "Mars", "Jupiter"],
    "Leo": ["Sun", "Jupiter", "Mars"],
    "Virgo": ["Mercury", "Saturn", "Venus"],
    "Libra": ["Venus", "Saturn", "Mercury"],
    "Scorpio": ["Mars", "Sun", "Venus"],
    "Sagittarius": ["Jupiter", "Mars", "Sun"],
    "Capricorn": ["Saturn", "Venus", "Mercury"],
    "Aquarius": ["Saturn", "Mercury", "Venus"],
    "Pisces": ["Jupiter", "Mars", "Sun"],
}

DECAN_RULERS_MODERN = {  # Including modern planets
    "Aries": ["Mars", "Sun", "Jupiter"],
    "Taurus": ["Venus", "Mercury", "Saturn"],
    "Gemini": ["Mercury", "Venus", "Uranus"],
    "Cancer": ["Moon", "Pluto", "Neptune"],
    "Leo": ["Sun", "Jupiter", "Mars"],
    "Virgo": ["Mercury", "Saturn", "Venus"],
    "Libra": ["Venus", "Uranus", "Mercury"],
    "Scorpio": ["Mars", "Neptune", "Moon"],
    "Sagittarius": ["Jupiter", "Mars", "Sun"],
    "Capricorn": ["Saturn", "Venus", "Mercury"],
    "Aquarius": ["Uranus", "Mercury", "Venus"],
    "Pisces": ["Neptune", "Moon", "Pluto"],
}

############### HOUSE SYSTEMS ###############

HOUSE_SYSTEMS = {
    "Placidus": "P",
    "Koch": "K",
    "Porphyrius": "O",
    "Regiomontanus": "R",
    "Campanus": "C",
    "Equal (Ascendant cusp 1)": "A",
    "Equal (Aries cusp 1)": "E",
    "Vehlow equal": "V",
    "Axial rotation system/Meridian system/Zariel system": "X",
    "Horizon/Azimuthal system": "H",
    "Polich/Page/Topocentric": "T",
    "Alcabitius": "B",
    "Gauquelin sectors": "G",
    "Sripati": "S",
    "Morinus": "M",
}

############### DEFAULT SETTINGS ###############

import pytz

# Default settings if no arguments are passed
DEFAULT_SETTINGS = {
    "timezone": pytz.timezone("Europe/Stockholm"),
    "transits_timezone": pytz.timezone("Europe/Stockholm"),
    "place_name": "Sahlgrenska",
    "transits_location": "Göteborg",
    "latitude": 57.6828,
    "longitude": 11.9624,
    "altitude": 0,
    "imprecise_aspects": "warn",  # ["off", "warn"]
    "minor_aspects": False,
    "show_brief_aspects": False,
    "show_score": False,
    "degree_in_minutes": False,
    "node": "true",  # true node is more accurate than mean node
    "all_stars": False,  # only astrologically known stars
    "house_cusps": False,
    "output_type": "text",
}

DEFAULT_ORBS = {
    "Orb": 1,  # General default orb size
    "Orb Major": 6.0,  # Default orb size for major aspects
    "Orb Minor": 1.5,  # Default orb size for minor aspects
    "Orb Fixed Star": 1.0,  # Default orb size for fixed star aspects
    "Orb Asteroid": 1.5,  # Default orb size for fixed star aspects
    "Orb Transit Fast": 1.5,  # Default orb size for fast-moving planet transits
    "Orb Transit Slow": 1.0,  # Default orb size for slow-moving planet transits
    "Orb Synastry Fast": 3.0,  # Default orb size for fast-moving planet synastry
    "Orb Synastry Slow": 2.0,  # Default orb size for slow-moving planet synastry
}

# Default Output settings
DEFAULT_OUTPUT_SETTINGS = {
    "hide_planetary_positions": False,
    "hide_planetary_aspects": False,
    "hide_fixed_star_aspects": False,
    "hide_asteroid_aspects": False,
    "show_transits": False,
    "show_synastry": False,
}

############### HTML TEMPLATES ###############

HTML_ERROR_TEMPLATE = """<!DOCTYPE html> 
<html> 
<head> 
    <meta charset="UTF-8"> 
    <meta name="viewport" content="width=device-width, initial-scale=1.0"> 
</head> 
<body> 
    <div><p>{error_message}</p></div> 
</body> 
</html>"""

HTML_CHART_TEMPLATE = """
<!DOCTYPE html>
    <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>AstroScript Chart</title>

            <style>
                body {
                    font-family: Arial, sans-serif;
                    color: #333;
                    background-color: #f4f4f4;
                    margin: 0px;
                    padding-left: 8px;
                    padding-right: 8px;
                }

                h1, h2, h3 {
                    color: #35424a;
                    margin-bottom: 1em;
                    line-height: 1.3;
                }

                h1 {
                    font-size: 2.5rem; /* Responsive font size */
                }
                h2 {
                    font-size: 2.0rem;
                }
                h3 {
                    font-size: 1.75rem;
                }
                p {
                    font-size: 1.2rem;
                    line-height: 1.6;
                }

                th, td {
                    padding: 8px 10px;
                    text-align: left;
                    border-bottom: 1px solid #ddd;
                }

                th {
                    background-color: #35424a;
                    color: white;
                }

                img {
                    max-height: 90vh;   /* vh unit represents a percentage of the viewport height */
                    width: auto;        /* Maintains the aspect ratio of the image */
                    display: block;
                }
                .table-container {
                    display: flex;
                    flex-wrap: wrap;
                    justify-content: space-around; /* This will space out the tables evenly */
                    align-items: flex-start; /* Aligns tables to the top */
                }
                .content-block {
                    margin-bottom: 20px; /* Separation between different blocks */
                }
                table {
                    width: auto;
                    margin-top: 20px;
                    border-collapse: collapse;
                    display: block;
                    flex: 1 1 300px; /* Flex-grow, flex-shrink, and base width */
                    margin: 10px; /* Adds some space between tables */
                    max-width: 100%; /* Ensures table does not overflow its container */
                    // overflow-x: auto; /* Allows horizontal scrolling if needed */
                    display: block;
                }
                .stack-vertical {
                    flex: 0 0 100%; /* Forces the table to take up 100% width of the flex container */
                    margin: 10px 0; /* Vertical margin for spacing, no horizontal margins */
                }

                @media (max-width: 768px) {
                    .table-container {
                        flex-direction: column;
                    }
                }
            </style>
        </head>
        <body>"""

############### NUMEROLOGY CONSTANTS ###############

# Pythagorean numerology letter to number mapping
NUMEROLOGY_CHART = {
    "A": 1,
    "J": 1,
    "S": 1,
    "B": 2,
    "K": 2,
    "T": 2,
    "C": 3,
    "L": 3,
    "U": 3,
    "D": 4,
    "M": 4,
    "V": 4,
    "E": 5,
    "N": 5,
    "W": 5,
    "F": 6,
    "O": 6,
    "X": 6,
    "G": 7,
    "P": 7,
    "Y": 7,
    "H": 8,
    "Q": 8,
    "Z": 8,
    "I": 9,
    "R": 9,
}
