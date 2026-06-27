import swisseph as swe


ZODIAC_CHOICES = ("tropical", "sidereal", "vedic")


def normalize_zodiac(zodiac=None):
    """Return the canonical zodiac name used by the calculation layer."""
    normalized = (zodiac or "tropical").strip().lower()
    if normalized == "vedic":
        return "sidereal"
    if normalized not in ("tropical", "sidereal"):
        raise ValueError(
            f"Unsupported zodiac '{zodiac}'. Choose tropical, sidereal, or vedic."
        )
    return normalized


def is_sidereal(zodiac=None):
    return normalize_zodiac(zodiac) == "sidereal"


def configure_zodiac(zodiac=None):
    """Configure Swiss Ephemeris and return the canonical zodiac name."""
    normalized = normalize_zodiac(zodiac)
    if normalized == "sidereal":
        swe.set_sid_mode(swe.SIDM_LAHIRI)
    return normalized


def calculation_flags(zodiac=None, base_flags=0):
    normalized = configure_zodiac(zodiac)
    if normalized == "sidereal":
        return base_flags | swe.FLG_SIDEREAL
    return base_flags


def zodiac_label(zodiac=None):
    if is_sidereal(zodiac):
        return "Sidereal (Lahiri/Vedic)"
    return "Tropical"


def get_ayanamsha_ut(jd, zodiac=None):
    if not is_sidereal(zodiac):
        return None
    configure_zodiac(zodiac)
    return swe.get_ayanamsa_ut(jd)
