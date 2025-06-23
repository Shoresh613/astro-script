#!/usr/bin/env python3
"""
AstroScript - Compatibility wrapper for the refactored astrological calculation tool.

This file maintains backward compatibility with the original astro_script.py while
the actual implementation has been moved to astro_script_main.py and modular components.

Usage:
    python astro_script.py [arguments]

This will call the main function from the refactored astro_script_main.py
"""

# Import the main function from the refactored entry point
from astro_script_main import main

# Import all the key functions for backward compatibility
from astro_calculations import (
    calculate_planet_positions,
    calculate_house_positions,
    convert_to_utc,
)
from aspect_analysis import calculate_planetary_aspects
from chart_patterns import find_t_squares, find_grand_trines, find_yod
from geo_time_utils import get_coordinates, get_location_info, parse_date
from data_manager import load_event, save_event, list_saved_events
from output_formatter import *
from numerology import calculate_all_numerology
from fixed_stars_arabic_parts import *

# For any code that might import specific functions from astro_script
__all__ = [
    "main",
    "calculate_planet_positions",
    "calculate_house_positions",
    "calculate_planetary_aspects",
    "get_coordinates",
    "parse_date",
    "load_event",
    "save_event",
]

if __name__ == "__main__":
    main()
