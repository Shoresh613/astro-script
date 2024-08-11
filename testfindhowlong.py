import swisseph as swe
from datetime import datetime, timedelta

def find_aspect_timings(body1, body2, target_angle, orb, reference_date, max_days=5):
    swe.set_ephe_path('./ephe/')  # Set the path to your ephemeris files

    def calculate_angle(time):
        jd = swe.julday(time.year, time.month, time.day, time.hour + time.minute / 60.0 + time.second / 3600.0)
        pos1 = swe.calc_ut(jd, body1)[0][0]
        pos2 = swe.calc_ut(jd, body2)[0][0]
        angle = abs(pos1 - pos2) % 360
        return min(angle, 360 - angle)

    def binary_search(start, end, target, compare_func):
        while (end - start) > timedelta(minutes=1):
            mid = start + (end - start) / 2
            if compare_func(calculate_angle(mid), target):
                end = mid
            else:
                start = mid
        return start

    # Find exact aspect
    start = reference_date - timedelta(days=max_days)
    end = reference_date + timedelta(days=max_days)
    exact_time = binary_search(start, end, target_angle, lambda a, t: abs(a - t) < 0.01)

    # Determine if the aspect is applying or separating
    angle_before = calculate_angle(exact_time - timedelta(hours=1))
    angle_after = calculate_angle(exact_time + timedelta(hours=1))
    is_applying = abs(angle_before - target_angle) > abs(angle_after - target_angle)

    # Find when aspect leaves orb
    if is_applying:
        orb_exceeded_time = binary_search(exact_time, end, target_angle + orb, lambda a, t: a > t)
    else:
        orb_exceeded_time = binary_search(exact_time, end, target_angle - orb, lambda a, t: a < t)

    exact_elapsed = (exact_time - reference_date).total_seconds()
    orb_exceeded_elapsed = (orb_exceeded_time - reference_date).total_seconds()

    return exact_elapsed, orb_exceeded_elapsed

def seconds_to_dhms(seconds):
    is_negative = seconds < 0
    seconds = abs(seconds)
    days, remainder = divmod(seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{'-' if is_negative else ''}{int(days)} days, {int(hours)} hours, {int(minutes)} minutes, {int(seconds)} seconds"

# Example usage
reference_date = datetime(2024, 7, 15, 18, 0)  # Your specified date
exact_seconds, orb_exceeded_seconds = find_aspect_timings(swe.MARS, swe.URANUS, 0, 1, reference_date)

exact_dhms = seconds_to_dhms(exact_seconds)
orb_exceeded_dhms = seconds_to_dhms(orb_exceeded_seconds)

print(f"Exact aspect {'occurred' if exact_seconds <= 0 else 'will occur'} {abs(exact_seconds):.2f} seconds {'before' if exact_seconds <= 0 else 'after'} the reference date ({exact_dhms})")
print(f"Aspect will exceed orb {orb_exceeded_seconds:.2f} seconds after the reference date ({orb_exceeded_dhms})")

print(f"\nDebug Info:")
print(f"Reference Date: {reference_date}")
print(f"Exact Time: {reference_date + timedelta(seconds=exact_seconds)}")
print(f"Orb Exceeded Time: {reference_date + timedelta(seconds=orb_exceeded_seconds)}")