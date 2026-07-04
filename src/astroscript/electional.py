"""Shared calculations for electional opportunity conditions."""

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from typing import List, Sequence

import pytz
import swisseph as swe


ZODIAC_SIGNS = (
    "Aries",
    "Taurus",
    "Gemini",
    "Cancer",
    "Leo",
    "Virgo",
    "Libra",
    "Scorpio",
    "Sagittarius",
    "Capricorn",
    "Aquarius",
    "Pisces",
)
PLANETARY_HOUR_RULERS = (
    "Sun",
    "Moon",
    "Mercury",
    "Venus",
    "Mars",
    "Jupiter",
    "Saturn",
)
CHALDEAN_ORDER = (
    "Saturn",
    "Jupiter",
    "Mars",
    "Sun",
    "Venus",
    "Mercury",
    "Moon",
)
WEEKDAY_RULERS = {
    0: "Moon",
    1: "Mars",
    2: "Mercury",
    3: "Jupiter",
    4: "Venus",
    5: "Saturn",
    6: "Sun",
}


@dataclass(frozen=True)
class PlanetaryHour:
    start: datetime
    end: datetime
    ruler: str
    day_ruler: str
    hour_number: int


def _julian_day(when: datetime) -> float:
    utc = when.astimezone(timezone.utc)
    return swe.julday(
        utc.year,
        utc.month,
        utc.day,
        utc.hour
        + utc.minute / 60.0
        + utc.second / 3600.0
        + utc.microsecond / 3_600_000_000.0,
    )


def _datetime_from_julian_day(julian_day: float) -> datetime:
    epoch = datetime(2000, 1, 1, 12, tzinfo=timezone.utc)
    return epoch + timedelta(days=julian_day - 2451545.0)


def _solar_event(
    local_day: date,
    local_timezone,
    latitude: float,
    longitude: float,
    altitude: float,
    event: int,
) -> datetime:
    local_midnight = local_timezone.localize(
        datetime.combine(local_day, time.min), is_dst=None
    )
    status, result = swe.rise_trans(
        tjdut=_julian_day(local_midnight),
        body=swe.SUN,
        geopos=(float(longitude), float(latitude), float(altitude)),
        rsmi=event,
    )
    if status != 0:
        event_name = "sunrise" if event == swe.CALC_RISE else "sunset"
        raise ValueError(
            f"Could not calculate {event_name} for {local_day.isoformat()} "
            "at the specified location."
        )
    return _datetime_from_julian_day(result[0])


def planetary_hours_for_day(
    local_day: date,
    timezone_name: str,
    latitude: float,
    longitude: float,
    altitude: float = 0.0,
) -> List[PlanetaryHour]:
    """Return the 24 unequal planetary hours beginning at local sunrise."""
    local_timezone = pytz.timezone(timezone_name)
    sunrise = _solar_event(
        local_day,
        local_timezone,
        latitude,
        longitude,
        altitude,
        swe.CALC_RISE,
    )
    sunset = _solar_event(
        local_day,
        local_timezone,
        latitude,
        longitude,
        altitude,
        swe.CALC_SET,
    )
    next_sunrise = _solar_event(
        local_day + timedelta(days=1),
        local_timezone,
        latitude,
        longitude,
        altitude,
        swe.CALC_RISE,
    )
    if not sunrise < sunset < next_sunrise:
        raise ValueError(
            f"Invalid sunrise/sunset sequence for {local_day.isoformat()}."
        )

    day_ruler = WEEKDAY_RULERS[local_day.weekday()]
    first_index = CHALDEAN_ORDER.index(day_ruler)
    day_length = (sunset - sunrise) / 12
    night_length = (next_sunrise - sunset) / 12
    hours = []
    for index in range(24):
        if index < 12:
            start = sunrise + day_length * index
            end = sunrise + day_length * (index + 1)
        else:
            night_index = index - 12
            start = sunset + night_length * night_index
            end = sunset + night_length * (night_index + 1)
        hours.append(
            PlanetaryHour(
                start=start,
                end=end,
                ruler=CHALDEAN_ORDER[(first_index + index) % 7],
                day_ruler=day_ruler,
                hour_number=index + 1,
            )
        )
    return hours


def planetary_hours_between(
    start: datetime,
    end: datetime,
    timezone_name: str,
    latitude: float,
    longitude: float,
    altitude: float = 0.0,
) -> List[PlanetaryHour]:
    """Return planetary hours intersecting an inclusive UTC interval."""
    local_timezone = pytz.timezone(timezone_name)
    first_day = start.astimezone(local_timezone).date() - timedelta(days=1)
    last_day = end.astimezone(local_timezone).date()
    result = []
    local_day = first_day
    while local_day <= last_day:
        result.extend(
            hour
            for hour in planetary_hours_for_day(
                local_day,
                timezone_name,
                latitude,
                longitude,
                altitude,
            )
            if hour.end >= start and hour.start <= end
        )
        local_day += timedelta(days=1)
    ordered = sorted(result, key=lambda hour: hour.start)
    normalized: List[PlanetaryHour] = []
    for hour in ordered:
        if normalized and abs(normalized[-1].end - hour.start) <= timedelta(seconds=1):
            previous = normalized[-1]
            normalized[-1] = PlanetaryHour(
                start=previous.start,
                end=hour.start,
                ruler=previous.ruler,
                day_ruler=previous.day_ruler,
                hour_number=previous.hour_number,
            )
        normalized.append(hour)
    return normalized


def planetary_hour_at(
    when: datetime,
    timezone_name: str,
    latitude: float,
    longitude: float,
    altitude: float = 0.0,
) -> PlanetaryHour:
    """Return the planetary hour containing an aware datetime."""
    for hour in planetary_hours_between(
        when,
        when,
        timezone_name,
        latitude,
        longitude,
        altitude,
    ):
        if hour.start <= when < hour.end:
            return hour
    raise ValueError("Could not determine the planetary hour.")


def validate_planetary_hour_rulers(rulers: Sequence[str]) -> None:
    unknown = [ruler for ruler in rulers if ruler not in PLANETARY_HOUR_RULERS]
    if unknown:
        raise ValueError(f"Unknown planetary-hour rulers: {', '.join(unknown)}")
