"""Search for exact aspects between moving celestial bodies."""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from math import ceil, floor
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence, Tuple

import swisseph as swe

from .constants import MAJOR_ASPECTS, PLANETS
from .zodiac import calculation_flags, normalize_zodiac


MAX_STEP = timedelta(hours=6)
MAX_PHASE_CHANGE_DEGREES = 2.0
TIME_TOLERANCE = timedelta(seconds=1)
DEDUPLICATION_TOLERANCE = timedelta(seconds=2)
ANGULAR_TOLERANCE_DEGREES = 1e-7

# PLANETS is mutated by parts of the legacy calculation flow. Keep a stable set of
# bodies with real Swiss Ephemeris identifiers for aspect searches.
DEFAULT_BODY_IDS = {
    name: body_id for name, body_id in PLANETS.items() if isinstance(body_id, int)
}
DEFAULT_BODIES = tuple(DEFAULT_BODY_IDS)


@dataclass(frozen=True)
class AspectSearchQuery:
    """Parameters for an inclusive exact-aspect search."""

    start: datetime
    end: datetime
    zodiac: str = "tropical"
    center: str = "geocentric"
    bodies: Optional[Sequence[str]] = None
    aspect_types: Optional[Mapping[str, Any]] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    altitude: float = 0.0


@dataclass(frozen=True)
class AspectEvent:
    """One exact aspect, with its calculated positions at the exact UTC time."""

    exact_at: datetime
    body1: str
    body2: str
    aspect: str
    aspect_angle: float
    body1_longitude: float
    body2_longitude: float
    body1_speed: float
    body2_speed: float


@dataclass(frozen=True)
class _Position:
    longitude: float
    speed: float


PositionProvider = Callable[[datetime, str], Any]


class _SwissEphemerisPositionProvider:
    def __init__(self, query: AspectSearchQuery):
        self.zodiac = normalize_zodiac(query.zodiac)
        self.center = query.center.strip().lower()
        self.latitude = query.latitude
        self.longitude = query.longitude
        self.altitude = query.altitude or 0.0

        if self.center not in {"geocentric", "topocentric"}:
            raise ValueError(
                "Aspect searches support geocentric or topocentric calculations."
            )
        if self.center == "topocentric":
            if self.latitude is None or self.longitude is None:
                raise ValueError(
                    "Topocentric aspect searches require latitude and longitude."
                )
            swe.set_topo(
                float(self.longitude), float(self.latitude), float(self.altitude)
            )

        self.flags = calculation_flags(
            self.zodiac, swe.FLG_SWIEPH | swe.FLG_SPEED
        )
        if self.center == "topocentric":
            self.flags |= swe.FLG_TOPOCTR

    def __call__(self, when: datetime, body: str) -> _Position:
        utc = when.astimezone(timezone.utc)
        julian_day = swe.julday(
            utc.year,
            utc.month,
            utc.day,
            utc.hour
            + utc.minute / 60.0
            + utc.second / 3600.0
            + utc.microsecond / 3_600_000_000.0,
        )
        values, _ = swe.calc_ut(julian_day, DEFAULT_BODY_IDS[body], self.flags)
        return _Position(values[0] % 360.0, values[3])


class _CachedPositions:
    def __init__(self, provider: PositionProvider):
        self.provider = provider
        self.cache: Dict[Tuple[datetime, str], _Position] = {}

    def get(self, when: datetime, body: str) -> _Position:
        key = (when, body)
        if key not in self.cache:
            value = self.provider(when, body)
            if isinstance(value, _Position):
                position = value
            else:
                position = _Position(float(value[0]) % 360.0, float(value[1]))
            self.cache[key] = position
        return self.cache[key]


def _validate_aware(value: datetime, name: str) -> datetime:
    if not isinstance(value, datetime):
        raise TypeError(f"{name} must be a datetime.")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must include timezone information.")
    return value.astimezone(timezone.utc)


def _normalize_aspects(
    aspect_types: Optional[Mapping[str, Any]],
) -> Tuple[Tuple[str, float], ...]:
    definitions = MAJOR_ASPECTS if aspect_types is None else aspect_types
    normalized = []
    for name, definition in definitions.items():
        if isinstance(definition, Mapping):
            if "Degrees" not in definition:
                raise ValueError(f"Aspect '{name}' has no Degrees value.")
            angle = float(definition["Degrees"])
        else:
            angle = float(definition)
        if angle < 0 or angle > 180:
            raise ValueError(f"Aspect '{name}' must be between 0 and 180 degrees.")
        normalized.append((name, angle))
    if not normalized:
        raise ValueError("At least one aspect type is required.")
    return tuple(normalized)


def _normalize_bodies(bodies: Optional[Sequence[str]]) -> Tuple[str, ...]:
    selected = tuple(bodies) if bodies is not None else DEFAULT_BODIES
    if len(selected) < 2:
        raise ValueError("At least two celestial bodies are required.")
    unknown = [body for body in selected if body not in DEFAULT_BODY_IDS]
    if unknown:
        raise ValueError(f"Unsupported celestial bodies: {', '.join(unknown)}")
    if len(set(selected)) != len(selected):
        raise ValueError("Celestial bodies may only be selected once.")
    return selected


def _raw_phase(first: _Position, second: _Position) -> float:
    return (first.longitude - second.longitude) % 360.0


def _unwrap_near(raw_phase: float, reference: float) -> float:
    return raw_phase + 360.0 * round((reference - raw_phase) / 360.0)


def _target_branches(angle: float) -> Tuple[float, ...]:
    if angle == 0:
        return (0.0,)
    if angle == 180:
        return (180.0,)
    return (angle, -angle)


def _target_levels(start_phase: float, end_phase: float, angle: float) -> List[float]:
    low, high = sorted((start_phase, end_phase))
    levels = []
    for branch in _target_branches(angle):
        first_k = ceil(
            (low - ANGULAR_TOLERANCE_DEGREES - branch) / 360.0
        )
        last_k = floor(
            (high + ANGULAR_TOLERANCE_DEGREES - branch) / 360.0
        )
        levels.extend(branch + 360.0 * k for k in range(first_k, last_k + 1))
    return sorted(set(levels))


def _relative_state(
    positions: _CachedPositions,
    when: datetime,
    body1: str,
    body2: str,
) -> Tuple[float, float]:
    first = positions.get(when, body1)
    second = positions.get(when, body2)
    return _raw_phase(first, second), first.speed - second.speed


def _refine_station(
    positions: _CachedPositions,
    body1: str,
    body2: str,
    start: datetime,
    end: datetime,
    start_speed: float,
    end_speed: float,
) -> datetime:
    if abs(start_speed) < ANGULAR_TOLERANCE_DEGREES:
        return start
    if abs(end_speed) < ANGULAR_TOLERANCE_DEGREES:
        return end

    left, right = start, end
    left_speed = start_speed
    while right - left > TIME_TOLERANCE:
        middle = left + (right - left) / 2
        _, middle_speed = _relative_state(positions, middle, body1, body2)
        if abs(middle_speed) < ANGULAR_TOLERANCE_DEGREES:
            return middle
        if left_speed * middle_speed <= 0:
            right = middle
        else:
            left = middle
            left_speed = middle_speed
    return left + (right - left) / 2


def _refine_crossing(
    positions: _CachedPositions,
    body1: str,
    body2: str,
    start: datetime,
    end: datetime,
    start_phase: float,
    end_phase: float,
    target: float,
) -> Optional[datetime]:
    start_error = start_phase - target
    end_error = end_phase - target
    if abs(start_error) <= ANGULAR_TOLERANCE_DEGREES:
        return start
    if abs(end_error) <= ANGULAR_TOLERANCE_DEGREES:
        return end
    if start_error * end_error > 0:
        return None

    left, right = start, end
    left_phase, right_phase = start_phase, end_phase
    left_error = start_error
    while right - left > TIME_TOLERANCE:
        middle = left + (right - left) / 2
        raw_middle, _ = _relative_state(positions, middle, body1, body2)
        fraction = (middle - left) / (right - left)
        reference = left_phase + (right_phase - left_phase) * fraction
        middle_phase = _unwrap_near(raw_middle, reference)
        middle_error = middle_phase - target
        if abs(middle_error) <= ANGULAR_TOLERANCE_DEGREES:
            return middle
        if left_error * middle_error <= 0:
            right = middle
            right_phase = middle_phase
        else:
            left = middle
            left_phase = middle_phase
            left_error = middle_error
    return left + (right - left) / 2


def _events_for_segment(
    positions: _CachedPositions,
    body1: str,
    body2: str,
    start: datetime,
    end: datetime,
    start_phase: float,
    end_phase: float,
    aspects: Tuple[Tuple[str, float], ...],
) -> List[Tuple[datetime, str, float]]:
    candidates = []
    for aspect_name, aspect_angle in aspects:
        for target in _target_levels(start_phase, end_phase, aspect_angle):
            exact_at = _refine_crossing(
                positions,
                body1,
                body2,
                start,
                end,
                start_phase,
                end_phase,
                target,
            )
            if exact_at is not None:
                candidates.append((exact_at, aspect_name, aspect_angle))
    return candidates


def _event_at(
    positions: _CachedPositions,
    exact_at: datetime,
    body1: str,
    body2: str,
    aspect_name: str,
    aspect_angle: float,
) -> AspectEvent:
    first = positions.get(exact_at, body1)
    second = positions.get(exact_at, body2)
    return AspectEvent(
        exact_at=exact_at.astimezone(timezone.utc),
        body1=body1,
        body2=body2,
        aspect=aspect_name,
        aspect_angle=aspect_angle,
        body1_longitude=first.longitude,
        body2_longitude=second.longitude,
        body1_speed=first.speed,
        body2_speed=second.speed,
    )


def _deduplicate(events: List[AspectEvent]) -> List[AspectEvent]:
    events.sort(key=lambda event: (event.exact_at, event.body1, event.body2, event.aspect))
    result = []
    last_seen: Dict[Tuple[str, str, str], datetime] = {}
    for event in events:
        key = (event.body1, event.body2, event.aspect)
        previous = last_seen.get(key)
        if previous is not None and event.exact_at - previous <= DEDUPLICATION_TOLERANCE:
            continue
        result.append(event)
        last_seen[key] = event.exact_at
    return result


def _single_instant_events(
    positions: _CachedPositions,
    when: datetime,
    bodies: Tuple[str, ...],
    aspects: Tuple[Tuple[str, float], ...],
) -> List[AspectEvent]:
    events = []
    for index, body1 in enumerate(bodies):
        for body2 in bodies[index + 1 :]:
            phase, _ = _relative_state(positions, when, body1, body2)
            for aspect_name, aspect_angle in aspects:
                distance = min(
                    abs(phase - branch) % 360.0
                    for branch in _target_branches(aspect_angle)
                )
                distance = min(distance, 360.0 - distance)
                if distance <= ANGULAR_TOLERANCE_DEGREES:
                    events.append(
                        _event_at(
                            positions,
                            when,
                            body1,
                            body2,
                            aspect_name,
                            aspect_angle,
                        )
                    )
    return events


def search_exact_aspects(
    query: AspectSearchQuery,
    *,
    _position_provider: Optional[PositionProvider] = None,
) -> List[AspectEvent]:
    """Return exact moving-body aspects in the inclusive query period."""

    start = _validate_aware(query.start, "start")
    end = _validate_aware(query.end, "end")
    if end < start:
        raise ValueError("end must be greater than or equal to start.")

    bodies = _normalize_bodies(query.bodies)
    aspects = _normalize_aspects(query.aspect_types)
    provider = _position_provider or _SwissEphemerisPositionProvider(query)
    positions = _CachedPositions(provider)

    if start == end:
        return _single_instant_events(positions, start, bodies, aspects)

    events = []
    current = start
    current_states = {body: positions.get(current, body) for body in bodies}
    unwrapped_phases: Dict[Tuple[str, str], float] = {}
    for index, body1 in enumerate(bodies):
        for body2 in bodies[index + 1 :]:
            unwrapped_phases[(body1, body2)] = _raw_phase(
                current_states[body1], current_states[body2]
            )

    while current < end:
        speeds = [state.speed for state in current_states.values()]
        max_relative_speed = max(speeds) - min(speeds)
        if max_relative_speed > 0:
            step = timedelta(
                days=min(
                    MAX_STEP.total_seconds() / 86400.0,
                    MAX_PHASE_CHANGE_DEGREES / max_relative_speed,
                )
            )
        else:
            step = MAX_STEP
        next_time = min(current + step, end)
        next_states = {body: positions.get(next_time, body) for body in bodies}

        for index, body1 in enumerate(bodies):
            for body2 in bodies[index + 1 :]:
                pair = (body1, body2)
                start_phase = unwrapped_phases[pair]
                raw_next = _raw_phase(next_states[body1], next_states[body2])
                end_phase = _unwrap_near(raw_next, start_phase)
                start_speed = current_states[body1].speed - current_states[body2].speed
                end_speed = next_states[body1].speed - next_states[body2].speed

                segments = [(current, next_time, start_phase, end_phase)]
                if start_speed * end_speed < 0:
                    station = _refine_station(
                        positions,
                        body1,
                        body2,
                        current,
                        next_time,
                        start_speed,
                        end_speed,
                    )
                    raw_station, _ = _relative_state(
                        positions, station, body1, body2
                    )
                    elapsed = (station - current) / (next_time - current)
                    reference = start_phase + (end_phase - start_phase) * elapsed
                    station_phase = _unwrap_near(raw_station, reference)
                    segments = [
                        (current, station, start_phase, station_phase),
                        (station, next_time, station_phase, end_phase),
                    ]

                for segment in segments:
                    for exact_at, aspect_name, aspect_angle in _events_for_segment(
                        positions, body1, body2, *segment, aspects
                    ):
                        events.append(
                            _event_at(
                                positions,
                                exact_at,
                                body1,
                                body2,
                                aspect_name,
                                aspect_angle,
                            )
                        )

                unwrapped_phases[pair] = end_phase

        current = next_time
        current_states = next_states

    return _deduplicate(events)
