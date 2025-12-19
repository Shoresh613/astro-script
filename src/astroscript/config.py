import os

import swisseph as swe

from db import db_manager

try:
    from timezonefinder import TimezoneFinder

    tz_finder_installed = True
except Exception:
    TimezoneFinder = None
    tz_finder_installed = False

EPHE = os.getenv("PRODUCTION_EPHE")
if EPHE:
    swe.set_ephe_path(EPHE)
else:
    if os.name == "nt":
        swe.set_ephe_path(".\ephe")
    else:
        swe.set_ephe_path("./ephe")

# Initialize database
# Keeping import-time init behavior from the original monolith.
db_manager.initialize_db()
