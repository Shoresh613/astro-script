def life_path_number(birthdate):
    """
    Calculate the Life Path Number based on the birthdate.
    The birthdate should be a datetime.date object.
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


def destiny_number(full_name):
    """
    Calculate the Destiny Number based on the full name.
    The full_name should be a string containing the first, middle, and last names.
    """
    # Pythagorean numerology letter to number mapping
    numerology_chart = {
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

    total = 0
    for char in full_name.upper():
        if char.isalpha():
            total += numerology_chart.get(char, 0)

    # Reduce to a single digit or master number (11, 22, 33)
    return reduce_number(total)


def reduce_number(number):
    """
    Reduce a number to a single digit or a master number (11, 22, 33).
    """
    while number > 9 and number not in [11, 22, 33]:
        number = sum(int(digit) for digit in str(number))
    return number
