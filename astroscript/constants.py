import swisseph as swe

############### Constants ###############
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
# Global formatting variables set in main depending on output type
bold = "\033[1m"
nobold = "\033[0m"
br = "\n"
p = "\n"
h1 = ""
h2 = ""
h3 = ""
h4 = ""
h1_ = ""
h2_ = ""
h3_ = ""
h4_ = ""

