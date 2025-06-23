"""
Numerology calculation functions for the astro script.
Contains functions for calculating life path numbers, destiny numbers, and related numerological data.
"""

from datetime import datetime
from constants import NUMEROLOGY_CHART


def life_path_number(birthdate: datetime) -> dict:
    """
    Calculate the life path number from a birth date.

    Args:
        birthdate: datetime object representing birth date

    Returns:
        dict: life path number information
    """
    # Extract date components
    day = birthdate.day
    month = birthdate.month
    year = birthdate.year

    # Calculate life path number
    total = day + month + year

    # Reduce to single digit (except master numbers 11, 22, 33)
    while total > 9 and total not in [11, 22, 33]:
        total = sum(int(digit) for digit in str(total))

    # Get interpretation
    interpretations = {
        1: "The Leader - Independent, pioneering, ambitious",
        2: "The Cooperator - Diplomatic, peaceful, cooperative",
        3: "The Communicator - Creative, optimistic, expressive",
        4: "The Builder - Practical, hardworking, reliable",
        5: "The Freedom Seeker - Adventurous, versatile, curious",
        6: "The Nurturer - Caring, responsible, family-oriented",
        7: "The Seeker - Analytical, spiritual, introspective",
        8: "The Achiever - Ambitious, material success, authoritative",
        9: "The Humanitarian - Compassionate, generous, idealistic",
        11: "The Intuitive - Inspirational, spiritual, intuitive (Master Number)",
        22: "The Master Builder - Practical visionary, large-scale achievements (Master Number)",
        33: "The Master Teacher - Spiritual teacher, healer, compassionate service (Master Number)",
    }

    return {
        "number": total,
        "interpretation": interpretations.get(total, "Unknown"),
        "is_master_number": total in [11, 22, 33],
        "calculation": f"{day} + {month} + {year} = {day + month + year} → {total}",
    }


def destiny_number(full_name: str) -> dict:
    """
    Calculate the destiny number from a full name.

    Args:
        full_name: full name string

    Returns:
        dict: destiny number information
    """
    # Letter values in numerology
    letter_values = {
        "A": 1,
        "B": 2,
        "C": 3,
        "D": 4,
        "E": 5,
        "F": 6,
        "G": 7,
        "H": 8,
        "I": 9,
        "J": 1,
        "K": 2,
        "L": 3,
        "M": 4,
        "N": 5,
        "O": 6,
        "P": 7,
        "Q": 8,
        "R": 9,
        "S": 1,
        "T": 2,
        "U": 3,
        "V": 4,
        "W": 5,
        "X": 6,
        "Y": 7,
        "Z": 8,
    }

    # Clean name and calculate total
    name_upper = full_name.upper().replace(" ", "")
    total = sum(letter_values.get(char, 0) for char in name_upper if char.isalpha())

    # Store original total for calculation display
    original_total = total

    # Reduce to single digit (except master numbers)
    while total > 9 and total not in [11, 22, 33]:
        total = sum(int(digit) for digit in str(total))

    # Get interpretation
    interpretations = {
        1: "Natural leader, independent, original",
        2: "Cooperative, diplomatic, detail-oriented",
        3: "Creative, communicative, optimistic",
        4: "Organized, practical, hardworking",
        5: "Freedom-loving, adventurous, progressive",
        6: "Nurturing, responsible, healing",
        7: "Analytical, research-oriented, spiritual",
        8: "Business-minded, material success, ambitious",
        9: "Humanitarian, generous, artistic",
        11: "Inspirational, intuitive, spiritual teacher (Master Number)",
        22: "Master builder, practical visionary (Master Number)",
        33: "Master teacher, healer, compassionate service (Master Number)",
    }

    return {
        "number": total,
        "interpretation": interpretations.get(total, "Unknown"),
        "is_master_number": total in [11, 22, 33],
        "name": full_name,
        "calculation": f"Letters sum to {original_total} → {total}",
    }


def reduce_number(number: int) -> int:
    """
    Reduce a number to a single digit (except master numbers 11, 22, 33).

    Args:
        number: number to reduce

    Returns:
        int: reduced number
    """
    while number > 9 and number not in [11, 22, 33]:
        number = sum(int(digit) for digit in str(number))

    return number


def personality_number(full_name: str) -> dict:
    """
    Calculate the personality number from consonants in the name.

    Args:
        full_name: full name string

    Returns:
        dict: personality number information
    """
    letter_values = {
        "A": 1,
        "B": 2,
        "C": 3,
        "D": 4,
        "E": 5,
        "F": 6,
        "G": 7,
        "H": 8,
        "I": 9,
        "J": 1,
        "K": 2,
        "L": 3,
        "M": 4,
        "N": 5,
        "O": 6,
        "P": 7,
        "Q": 8,
        "R": 9,
        "S": 1,
        "T": 2,
        "U": 3,
        "V": 4,
        "W": 5,
        "X": 6,
        "Y": 7,
        "Z": 8,
    }

    vowels = "AEIOU"
    name_upper = full_name.upper().replace(" ", "")

    # Sum consonants only
    consonant_total = sum(
        letter_values.get(char, 0)
        for char in name_upper
        if char.isalpha() and char not in vowels
    )

    original_total = consonant_total
    reduced_number = reduce_number(consonant_total)

    interpretations = {
        1: "Appears confident, independent, leadership qualities",
        2: "Appears gentle, cooperative, diplomatic",
        3: "Appears creative, charming, expressive",
        4: "Appears reliable, practical, hardworking",
        5: "Appears dynamic, versatile, freedom-loving",
        6: "Appears caring, responsible, nurturing",
        7: "Appears mysterious, analytical, reserved",
        8: "Appears successful, authoritative, ambitious",
        9: "Appears generous, humanitarian, artistic",
        11: "Appears inspiring, intuitive, spiritual (Master Number)",
        22: "Appears practical yet visionary (Master Number)",
        33: "Appears compassionate, teaching-oriented (Master Number)",
    }

    return {
        "number": reduced_number,
        "interpretation": interpretations.get(reduced_number, "Unknown"),
        "is_master_number": reduced_number in [11, 22, 33],
        "calculation": f"Consonants sum to {original_total} → {reduced_number}",
    }


def soul_urge_number(full_name: str) -> dict:
    """
    Calculate the soul urge number from vowels in the name.

    Args:
        full_name: full name string

    Returns:
        dict: soul urge number information
    """
    letter_values = {
        "A": 1,
        "B": 2,
        "C": 3,
        "D": 4,
        "E": 5,
        "F": 6,
        "G": 7,
        "H": 8,
        "I": 9,
        "J": 1,
        "K": 2,
        "L": 3,
        "M": 4,
        "N": 5,
        "O": 6,
        "P": 7,
        "Q": 8,
        "R": 9,
        "S": 1,
        "T": 2,
        "U": 3,
        "V": 4,
        "W": 5,
        "X": 6,
        "Y": 7,
        "Z": 8,
    }

    vowels = "AEIOU"
    name_upper = full_name.upper().replace(" ", "")

    # Sum vowels only
    vowel_total = sum(
        letter_values.get(char, 0) for char in name_upper if char in vowels
    )

    original_total = vowel_total
    reduced_number = reduce_number(vowel_total)

    interpretations = {
        1: "Desires independence, leadership, originality",
        2: "Desires peace, cooperation, partnership",
        3: "Desires creative expression, communication, joy",
        4: "Desires security, order, practical achievement",
        5: "Desires freedom, adventure, variety",
        6: "Desires to nurture, serve, create harmony",
        7: "Desires understanding, analysis, spiritual growth",
        8: "Desires material success, recognition, achievement",
        9: "Desires to serve humanity, artistic expression",
        11: "Desires to inspire, illuminate, serve spiritually (Master Number)",
        22: "Desires to build something lasting and meaningful (Master Number)",
        33: "Desires to teach, heal, and serve with compassion (Master Number)",
    }

    return {
        "number": reduced_number,
        "interpretation": interpretations.get(reduced_number, "Unknown"),
        "is_master_number": reduced_number in [11, 22, 33],
        "calculation": f"Vowels sum to {original_total} → {reduced_number}",
    }


def birthday_number(birthdate: datetime) -> dict:
    """
    Calculate the birthday number (just the day of birth).

    Args:
        birthdate: datetime object

    Returns:
        dict: birthday number information
    """
    day = birthdate.day
    reduced_day = reduce_number(day)

    interpretations = {
        1: "Independent, pioneering, natural leader",
        2: "Cooperative, diplomatic, peacemaker",
        3: "Creative, optimistic, expressive",
        4: "Practical, organized, reliable",
        5: "Adventurous, freedom-loving, versatile",
        6: "Nurturing, responsible, home-oriented",
        7: "Analytical, introspective, spiritual",
        8: "Ambitious, business-minded, successful",
        9: "Humanitarian, artistic, generous",
        10: "Independent leader with practical skills",
        11: "Intuitive, inspirational, spiritual (Master Number)",
        22: "Master builder, practical visionary (Master Number)",
        29: "Intuitive, diplomatic, humanitarian",
    }

    # For birthday numbers, we often keep the original day if it's significant
    display_number = day if day in [11, 22, 29] or day <= 9 else reduced_day

    return {
        "number": display_number,
        "interpretation": interpretations.get(
            display_number, f"Characteristics of {reduced_day}"
        ),
        "is_master_number": display_number in [11, 22],
        "original_day": day,
    }


def calculate_all_numerology(full_name: str, birthdate: datetime) -> dict:
    """
    Calculate all numerology numbers for a person.

    Args:
        full_name: full name
        birthdate: birth date

    Returns:
        dict: all numerology calculations
    """
    return {
        "life_path": life_path_number(birthdate),
        "destiny": destiny_number(full_name),
        "personality": personality_number(full_name),
        "soul_urge": soul_urge_number(full_name),
        "birthday": birthday_number(birthdate),
    }


def numerology_compatibility(life_path1: int, life_path2: int) -> dict:
    """
    Calculate numerology compatibility between two life path numbers.

    Args:
        life_path1: first person's life path number
        life_path2: second person's life path number

    Returns:
        dict: compatibility information
    """
    # Compatibility matrix (simplified)
    compatibility_scores = {
        (1, 1): 70,
        (1, 2): 60,
        (1, 3): 85,
        (1, 4): 50,
        (1, 5): 90,
        (1, 6): 65,
        (1, 7): 40,
        (1, 8): 80,
        (1, 9): 75,
        (1, 11): 85,
        (1, 22): 70,
        (1, 33): 60,
        (2, 2): 85,
        (2, 3): 70,
        (2, 4): 90,
        (2, 5): 45,
        (2, 6): 95,
        (2, 7): 75,
        (2, 8): 80,
        (2, 9): 85,
        (2, 11): 90,
        (2, 22): 80,
        (2, 33): 85,
        (3, 3): 80,
        (3, 4): 40,
        (3, 5): 95,
        (3, 6): 75,
        (3, 7): 60,
        (3, 8): 65,
        (3, 9): 90,
        (3, 11): 85,
        (3, 22): 70,
        (3, 33): 90,
        # Add more combinations as needed...
    }

    # Get score (checking both directions)
    score = (
        compatibility_scores.get((life_path1, life_path2))
        or compatibility_scores.get((life_path2, life_path1))
        or 50
    )

    # Determine compatibility level
    if score >= 80:
        level = "Excellent"
    elif score >= 60:
        level = "Good"
    elif score >= 40:
        level = "Fair"
    else:
        level = "Challenging"

    return {
        "score": score,
        "level": level,
        "description": f"{life_path1} and {life_path2} compatibility",
    }


def life_path_number_simple(birthdate: datetime) -> int:
    """
    Calculate the Life Path Number based on the birthdate (original style).
    Returns just the number as an integer to match original behavior.
    """
    total = 0
    # Sum of the digits of the day
    for digit in str(birthdate.day):
        total += int(digit)
    # Sum of the digits of the month
    for digit in str(birthdate.month):
        total += int(digit)
    # Sum of the digits of the year
    for digit in str(birthdate.year):
        total += int(digit)

    # Reduce to a single digit or master number (11, 22, 33)
    return reduce_number(total)


def destiny_number_simple(full_name: str) -> int:
    """
    Calculate the Destiny Number based on the full name (original style).
    Returns just the number as an integer to match original behavior.
    """
    total = 0
    for char in full_name.upper():
        if char.isalpha():
            total += NUMEROLOGY_CHART.get(char, 0)

    # Reduce to a single digit or master number (11, 22, 33)
    return reduce_number(total)
