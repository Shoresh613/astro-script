"""Combine astrological conditions into ranked opportunity windows."""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import json
from math import ceil, floor
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple, Union

import pytz

from .aspect_search import (
    ANGULAR_TOLERANCE_DEGREES,
    DEDUPLICATION_TOLERANCE,
    MAX_PHASE_CHANGE_DEGREES,
    MAX_STEP,
    SUPPORTED_BODY_IDS,
    AspectSearchQuery,
    PositionProvider,
    _CachedPositions,
    _Position,
    _SwissEphemerisPositionProvider,
    _raw_phase,
    _refine_crossing,
    _refine_station,
    _unwrap_near,
    _validate_aware,
)
from .constants import ALL_ASPECTS, HOUSE_SYSTEMS
from .houses import calculate_house_cusps, find_house_number
from .zodiac import normalize_zodiac


PHASE_ANGLES = {
    "new": 0.0,
    "first_quarter": 90.0,
    "full": 180.0,
    "last_quarter": 270.0,
}
MATCH_TOLERANCE_DEGREES = 1e-6
NATAL_ANGLES = ("Ascendant", "Midheaven", "IC", "DC")
NATAL_HOUSE_CUSPS = tuple(f"House {number}" for number in range(1, 13))
NATAL_STATIC_PREFIX = "__natal__:"
ZODIAC_ORIGIN = "__zodiac_origin__"

__all__ = [
    "AspectCondition",
    "NatalAspectCondition",
    "TransitNatalHouseCondition",
    "MoonPhaseCondition",
    "NatalChart",
    "OpportunitySearchQuery",
    "ConditionEvaluation",
    "OpportunityWindow",
    "search_opportunities",
    "opportunity_query_from_dict",
    "load_opportunity_query",
]


@dataclass(frozen=True)
class AspectCondition:
    id: str
    body1: str
    body2: str
    aspects: Sequence[str]
    max_orb_degrees: float
    required: bool = True
    weight: float = 1.0


@dataclass(frozen=True)
class MoonPhaseCondition:
    id: str
    phase: str
    max_deviation_degrees: float
    required: bool = True
    weight: float = 1.0


@dataclass(frozen=True)
class NatalAspectCondition:
    id: str
    transit_body: str
    natal_target: str
    aspects: Sequence[str]
    max_orb_degrees: float
    required: bool = True
    weight: float = 1.0


@dataclass(frozen=True)
class TransitNatalHouseCondition:
    id: str
    transit_body: str
    houses: Sequence[int]
    required: bool = True
    weight: float = 1.0


@dataclass(frozen=True)
class NatalChart:
    datetime: datetime
    latitude: float
    longitude: float
    altitude: float = 0.0
    house_system: str = "Placidus"
    time_unknown: bool = False


Condition = Union[
    AspectCondition,
    MoonPhaseCondition,
    NatalAspectCondition,
    TransitNatalHouseCondition,
]


@dataclass(frozen=True)
class OpportunitySearchQuery:
    start: datetime
    end: datetime
    conditions: Sequence[Condition]
    timezone: str = "UTC"
    zodiac: str = "tropical"
    center: str = "geocentric"
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    altitude: float = 0.0
    natal_chart: Optional[NatalChart] = None


@dataclass(frozen=True)
class ConditionEvaluation:
    condition_id: str
    condition_type: str
    required: bool
    matched: bool
    score: float
    deviation_degrees: float
    max_deviation_degrees: float
    description: str


@dataclass(frozen=True)
class OpportunityWindow:
    start: datetime
    peak: datetime
    end: datetime
    score: float
    evaluations: Tuple[ConditionEvaluation, ...]


@dataclass(frozen=True)
class _ConditionActivity:
    start: datetime
    end: datetime
    peak_times: Tuple[datetime, ...]


@dataclass(frozen=True)
class _TimeWindow:
    start: datetime
    end: datetime


@dataclass(frozen=True)
class _NatalSnapshot:
    positions: Mapping[str, float]
    house_cusps: Optional[Tuple[float, ...]]


class _StaticOverlayProvider:
    def __init__(
        self,
        moving_provider: PositionProvider,
        static_positions: Mapping[str, float],
    ):
        self.moving_provider = moving_provider
        self.static_positions = static_positions

    def __call__(self, when: datetime, body: str) -> Any:
        if body in self.static_positions:
            return _Position(self.static_positions[body] % 360.0, 0.0)
        return self.moving_provider(when, body)


def _canonical_phase(value: str) -> str:
    return value.strip().lower().replace("-", "_").replace(" ", "_")


def _number(value: Any, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field} must be a number.")
    return float(value)


def _validate_aspect_names(
    condition_id: str,
    aspects: Sequence[str],
) -> None:
    if (
        isinstance(aspects, (str, bytes))
        or not isinstance(aspects, Sequence)
        or not aspects
    ):
        raise ValueError(f"Condition '{condition_id}' requires at least one aspect.")
    if any(not isinstance(name, str) for name in aspects):
        raise ValueError(f"Condition '{condition_id}' aspects must be strings.")
    unknown = [name for name in aspects if name not in ALL_ASPECTS]
    if unknown:
        raise ValueError(f"Unknown aspects: {', '.join(unknown)}")
    if len(set(aspects)) != len(aspects):
        raise ValueError(f"Condition '{condition_id}' contains duplicate aspects.")


def _normalize_house_system(value: str) -> str:
    if not isinstance(value, str):
        raise ValueError("natal_chart house_system must be a string.")
    normalized = HOUSE_SYSTEMS.get(value, value)
    if normalized not in set(HOUSE_SYSTEMS.values()):
        raise ValueError(f"Unsupported natal house system: {value}")
    return normalized


def _natal_target_names() -> Tuple[str, ...]:
    return tuple(SUPPORTED_BODY_IDS) + NATAL_ANGLES + NATAL_HOUSE_CUSPS


def _condition_requires_natal_houses(condition: Condition) -> bool:
    return isinstance(condition, TransitNatalHouseCondition) or (
        isinstance(condition, NatalAspectCondition)
        and condition.natal_target in NATAL_ANGLES + NATAL_HOUSE_CUSPS
    )


def _validate_condition(condition: Condition) -> None:
    if not isinstance(condition.id, str) or not condition.id.strip():
        raise ValueError("Every condition requires a non-empty id.")
    if not isinstance(condition.required, bool):
        raise ValueError(f"Condition '{condition.id}' required must be boolean.")
    weight = _number(condition.weight, f"Condition '{condition.id}' weight")
    if weight <= 0:
        raise ValueError(f"Condition '{condition.id}' weight must be greater than 0.")

    if isinstance(condition, AspectCondition):
        if condition.body1 not in SUPPORTED_BODY_IDS:
            raise ValueError(f"Unsupported celestial body: {condition.body1}")
        if condition.body2 not in SUPPORTED_BODY_IDS:
            raise ValueError(f"Unsupported celestial body: {condition.body2}")
        if condition.body1 == condition.body2:
            raise ValueError(f"Condition '{condition.id}' requires two different bodies.")
        _validate_aspect_names(condition.id, condition.aspects)
        maximum = _number(
            condition.max_orb_degrees,
            f"Condition '{condition.id}' max_orb_degrees",
        )
    elif isinstance(condition, NatalAspectCondition):
        if condition.transit_body not in SUPPORTED_BODY_IDS:
            raise ValueError(f"Unsupported celestial body: {condition.transit_body}")
        if condition.natal_target not in _natal_target_names():
            raise ValueError(f"Unsupported natal target: {condition.natal_target}")
        _validate_aspect_names(condition.id, condition.aspects)
        maximum = _number(
            condition.max_orb_degrees,
            f"Condition '{condition.id}' max_orb_degrees",
        )
    elif isinstance(condition, TransitNatalHouseCondition):
        if condition.transit_body not in SUPPORTED_BODY_IDS:
            raise ValueError(f"Unsupported celestial body: {condition.transit_body}")
        if (
            isinstance(condition.houses, (str, bytes))
            or not isinstance(condition.houses, Sequence)
            or not condition.houses
        ):
            raise ValueError(f"Condition '{condition.id}' requires natal houses.")
        if any(
            isinstance(house, bool) or not isinstance(house, int)
            for house in condition.houses
        ):
            raise ValueError(f"Condition '{condition.id}' houses must be integers.")
        if any(house < 1 or house > 12 for house in condition.houses):
            raise ValueError(f"Condition '{condition.id}' houses must be between 1 and 12.")
        if len(set(condition.houses)) != len(condition.houses):
            raise ValueError(f"Condition '{condition.id}' contains duplicate houses.")
        maximum = None
    elif isinstance(condition, MoonPhaseCondition):
        if not isinstance(condition.phase, str):
            raise ValueError(f"Condition '{condition.id}' phase must be a string.")
        phase = _canonical_phase(condition.phase)
        if phase not in PHASE_ANGLES:
            raise ValueError(f"Unknown moon phase: {condition.phase}")
        maximum = _number(
            condition.max_deviation_degrees,
            f"Condition '{condition.id}' max_deviation_degrees",
        )
    else:
        raise TypeError("Unsupported opportunity condition type.")

    if maximum is not None and (maximum <= 0 or maximum > 180):
        raise ValueError(
            f"Condition '{condition.id}' maximum deviation must be above 0 "
            "and at most 180 degrees."
        )


def _validate_query(query: OpportunitySearchQuery) -> Tuple[datetime, datetime]:
    start = _validate_aware(query.start, "start")
    end = _validate_aware(query.end, "end")
    if end < start:
        raise ValueError("end must be greater than or equal to start.")
    if (
        isinstance(query.conditions, (str, bytes))
        or not isinstance(query.conditions, Sequence)
        or not query.conditions
    ):
        raise ValueError("At least one opportunity condition is required.")
    ids = []
    for condition in query.conditions:
        _validate_condition(condition)
        ids.append(condition.id)
    if len(ids) != len(set(ids)):
        raise ValueError("Condition ids must be unique.")

    natal_conditions = [
        condition
        for condition in query.conditions
        if isinstance(
            condition, (NatalAspectCondition, TransitNatalHouseCondition)
        )
    ]
    if natal_conditions and query.natal_chart is None:
        raise ValueError("Natal conditions require natal_chart data.")
    if query.natal_chart is not None:
        natal = query.natal_chart
        _validate_aware(natal.datetime, "natal_chart datetime")
        _number(natal.latitude, "natal_chart latitude")
        _number(natal.longitude, "natal_chart longitude")
        _number(natal.altitude, "natal_chart altitude")
        if not isinstance(natal.time_unknown, bool):
            raise ValueError("natal_chart time_unknown must be boolean.")
        _normalize_house_system(natal.house_system)
        if natal.time_unknown and any(
            _condition_requires_natal_houses(condition)
            for condition in natal_conditions
        ):
            raise ValueError(
                "Natal houses and angles require a known birth time."
            )

    if not isinstance(query.zodiac, str):
        raise ValueError("zodiac must be a string.")
    normalize_zodiac(query.zodiac)
    if not isinstance(query.center, str):
        raise ValueError("center must be a string.")
    center = query.center.strip().lower()
    if center not in {"geocentric", "topocentric"}:
        raise ValueError(
            "Opportunity searches support geocentric or topocentric calculations."
        )
    if center == "topocentric" and (
        query.latitude is None or query.longitude is None
    ):
        raise ValueError(
            "Topocentric opportunity searches require latitude and longitude."
        )
    if not isinstance(query.timezone, str):
        raise ValueError("timezone must be a string.")
    pytz.timezone(query.timezone)
    for field, value in (
        ("latitude", query.latitude),
        ("longitude", query.longitude),
        ("altitude", query.altitude),
    ):
        if value is not None:
            _number(value, field)
    return start, end


def _static_natal_key(target: str) -> str:
    return f"{NATAL_STATIC_PREFIX}{target}"


def _effective_natal_datetime(natal: NatalChart) -> datetime:
    if not natal.time_unknown:
        return natal.datetime
    local_noon = datetime(
        natal.datetime.year,
        natal.datetime.month,
        natal.datetime.day,
        12,
    )
    natal_timezone = natal.datetime.tzinfo
    if hasattr(natal_timezone, "localize"):
        return natal_timezone.localize(local_noon, is_dst=None)
    return local_noon.replace(tzinfo=natal_timezone)


def _build_natal_snapshot(
    query: OpportunitySearchQuery,
    injected_provider: Optional[PositionProvider],
) -> Optional[_NatalSnapshot]:
    natal = query.natal_chart
    if natal is None:
        return None

    natal_datetime = _effective_natal_datetime(natal).astimezone(timezone.utc)
    natal_provider = injected_provider or _SwissEphemerisPositionProvider(
        AspectSearchQuery(
            start=natal_datetime,
            end=natal_datetime,
            zodiac=query.zodiac,
            center=query.center,
            bodies=tuple(SUPPORTED_BODY_IDS),
            latitude=natal.latitude,
            longitude=natal.longitude,
            altitude=natal.altitude,
        )
    )
    natal_bodies = {
        condition.natal_target
        for condition in query.conditions
        if isinstance(condition, NatalAspectCondition)
        and condition.natal_target in SUPPORTED_BODY_IDS
    }
    positions = {}
    for body in natal_bodies:
        value = natal_provider(natal_datetime, body)
        longitude = value.longitude if isinstance(value, _Position) else value[0]
        positions[body] = float(longitude) % 360.0

    house_cusps = None
    if not natal.time_unknown:
        cusps, ascmc = calculate_house_cusps(
            natal_datetime,
            float(natal.latitude),
            float(natal.longitude),
            h_sys=_normalize_house_system(natal.house_system),
            zodiac=query.zodiac,
        )
        house_cusps = tuple(float(value) % 360.0 for value in cusps[:12])
        positions.update(
            {
                "Ascendant": float(ascmc[0]) % 360.0,
                "Midheaven": float(ascmc[1]) % 360.0,
                "IC": house_cusps[3],
                "DC": house_cusps[6],
            }
        )
        positions.update(
            {
                f"House {index + 1}": longitude
                for index, longitude in enumerate(house_cusps)
            }
        )
    return _NatalSnapshot(positions=positions, house_cusps=house_cusps)


def _aspect_branches(angle: float) -> Tuple[float, ...]:
    if angle == 0:
        return (0.0,)
    if angle == 180:
        return (180.0,)
    return (angle, 360.0 - angle)


def _oriented_target_levels(
    start_phase: float,
    end_phase: float,
    target: float,
) -> List[float]:
    low, high = sorted((start_phase, end_phase))
    first_k = ceil(
        (low - ANGULAR_TOLERANCE_DEGREES - target) / 360.0
    )
    last_k = floor(
        (high + ANGULAR_TOLERANCE_DEGREES - target) / 360.0
    )
    return [target + 360.0 * k for k in range(first_k, last_k + 1)]


def _deduplicate_times(values: Sequence[datetime]) -> List[datetime]:
    result = []
    for value in sorted(values):
        if not result or value - result[-1] > DEDUPLICATION_TOLERANCE:
            result.append(value)
    return result


def _collect_phase_crossings(
    start: datetime,
    end: datetime,
    body1: str,
    body2: str,
    targets: Sequence[Tuple[str, float]],
    tolerance: float,
    positions: _CachedPositions,
) -> Tuple[List[datetime], List[datetime]]:
    """Return orb-boundary crossings and exact target crossings."""
    boundaries: List[datetime] = []
    peaks: List[datetime] = []
    current = start
    first = positions.get(current, body1)
    second = positions.get(current, body2)
    current_phase = _raw_phase(first, second)

    while current < end:
        start_speed = first.speed - second.speed
        if abs(start_speed) > 0:
            step = timedelta(
                days=min(
                    MAX_STEP.total_seconds() / 86400.0,
                    MAX_PHASE_CHANGE_DEGREES / abs(start_speed),
                )
            )
        else:
            step = MAX_STEP
        next_time = min(current + step, end)
        next_first = positions.get(next_time, body1)
        next_second = positions.get(next_time, body2)
        raw_next = _raw_phase(next_first, next_second)
        next_phase = _unwrap_near(raw_next, current_phase)
        end_speed = next_first.speed - next_second.speed

        segments = [(current, next_time, current_phase, next_phase)]
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
            station_first = positions.get(station, body1)
            station_second = positions.get(station, body2)
            raw_station = _raw_phase(station_first, station_second)
            elapsed = (station - current) / (next_time - current)
            reference = current_phase + (next_phase - current_phase) * elapsed
            station_phase = _unwrap_near(raw_station, reference)
            segments = [
                (current, station, current_phase, station_phase),
                (station, next_time, station_phase, next_phase),
            ]

        for segment_start, segment_end, phase_start, phase_end in segments:
            for _, target in targets:
                crossings = (
                    ((0.0, boundaries),)
                    if tolerance == 0
                    else (
                        (-tolerance, boundaries),
                        (0.0, peaks),
                        (tolerance, boundaries),
                    )
                )
                for offset, destination in crossings:
                    for level in _oriented_target_levels(
                        phase_start, phase_end, target + offset
                    ):
                        crossing = _refine_crossing(
                            positions,
                            body1,
                            body2,
                            segment_start,
                            segment_end,
                            phase_start,
                            phase_end,
                            level,
                        )
                        if crossing is not None:
                            destination.append(crossing)

        current = next_time
        first, second = next_first, next_second
        current_phase = next_phase

    return _deduplicate_times(boundaries), _deduplicate_times(peaks)


def _circular_deviation(value: float, target: float) -> float:
    return abs((value - target + 180.0) % 360.0 - 180.0)


def _evaluate_condition(
    condition: Condition,
    when: datetime,
    positions: _CachedPositions,
    natal_snapshot: Optional[_NatalSnapshot],
) -> ConditionEvaluation:
    if isinstance(condition, (AspectCondition, NatalAspectCondition)):
        if isinstance(condition, AspectCondition):
            body1 = condition.body1
            body2 = condition.body2
            aspects = condition.aspects
            maximum = float(condition.max_orb_degrees)
            label = f"{condition.body1} {{aspect}} {condition.body2}"
            condition_type = "aspect"
        else:
            body1 = condition.transit_body
            body2 = _static_natal_key(condition.natal_target)
            aspects = condition.aspects
            maximum = float(condition.max_orb_degrees)
            label = (
                f"Transit {condition.transit_body} {{aspect}} "
                f"natal {condition.natal_target}"
            )
            condition_type = "natal_aspect"
        first = positions.get(when, body1)
        second = positions.get(when, body2)
        phase = _raw_phase(first, second)
        separation = min(phase, 360.0 - phase)
        choices = [
            (
                abs(separation - float(ALL_ASPECTS[name]["Degrees"])),
                index,
                name,
                float(ALL_ASPECTS[name]["Degrees"]),
            )
            for index, name in enumerate(aspects)
        ]
        deviation, _, aspect_name, target = min(choices)
        matched = deviation <= maximum + MATCH_TOLERANCE_DEGREES
        score = max(0.0, 1.0 - deviation / maximum) * 100.0
        description = (
            f"{label.format(aspect=aspect_name)}: "
            f"orb {deviation:.4f}° / {maximum:.4f}°"
        )
    elif isinstance(condition, MoonPhaseCondition):
        moon = positions.get(when, "Moon")
        sun = positions.get(when, "Sun")
        phase_angle = _raw_phase(moon, sun)
        phase = _canonical_phase(condition.phase)
        target = PHASE_ANGLES[phase]
        deviation = _circular_deviation(phase_angle, target)
        maximum = float(condition.max_deviation_degrees)
        matched = deviation <= maximum + MATCH_TOLERANCE_DEGREES
        score = max(0.0, 1.0 - deviation / maximum) * 100.0
        description = (
            f"Moon phase {phase}: angle {phase_angle:.4f}°, "
            f"deviation {deviation:.4f}° / {maximum:.4f}°"
        )
        condition_type = "moon_phase"
    else:
        if natal_snapshot is None or natal_snapshot.house_cusps is None:
            raise ValueError("Natal house conditions require calculated house cusps.")
        transit = positions.get(when, condition.transit_body)
        house = find_house_number(
            transit.longitude, natal_snapshot.house_cusps
        )
        matched = house in condition.houses
        score = 100.0 if matched else 0.0
        deviation = 0.0 if matched else 1.0
        maximum = 0.0
        description = (
            f"Transit {condition.transit_body} in natal house {house}; "
            f"allowed {', '.join(str(value) for value in condition.houses)}"
        )
        condition_type = "transit_natal_house"

    return ConditionEvaluation(
        condition_id=condition.id,
        condition_type=condition_type,
        required=condition.required,
        matched=matched,
        score=score,
        deviation_degrees=deviation,
        max_deviation_degrees=maximum,
        description=description,
    )


def _merge_activities(
    activities: Sequence[_ConditionActivity],
) -> List[_ConditionActivity]:
    merged: List[_ConditionActivity] = []
    for activity in sorted(activities, key=lambda item: (item.start, item.end)):
        if (
            merged
            and activity.start - merged[-1].end <= DEDUPLICATION_TOLERANCE
        ):
            previous = merged[-1]
            merged[-1] = _ConditionActivity(
                start=previous.start,
                end=max(previous.end, activity.end),
                peak_times=tuple(
                    _deduplicate_times(previous.peak_times + activity.peak_times)
                ),
            )
        else:
            merged.append(activity)
    return merged


def _condition_activities(
    condition: Condition,
    start: datetime,
    end: datetime,
    positions: _CachedPositions,
    natal_snapshot: Optional[_NatalSnapshot],
) -> List[_ConditionActivity]:
    if isinstance(condition, AspectCondition):
        targets = []
        for aspect_name in condition.aspects:
            angle = float(ALL_ASPECTS[aspect_name]["Degrees"])
            targets.extend(
                (aspect_name, branch) for branch in _aspect_branches(angle)
            )
        tolerance = float(condition.max_orb_degrees)
        body1, body2 = condition.body1, condition.body2
        categorical = False
    elif isinstance(condition, NatalAspectCondition):
        targets = []
        for aspect_name in condition.aspects:
            angle = float(ALL_ASPECTS[aspect_name]["Degrees"])
            targets.extend(
                (aspect_name, branch) for branch in _aspect_branches(angle)
            )
        tolerance = float(condition.max_orb_degrees)
        body1 = condition.transit_body
        body2 = _static_natal_key(condition.natal_target)
        categorical = False
    elif isinstance(condition, MoonPhaseCondition):
        phase = _canonical_phase(condition.phase)
        targets = [(phase, PHASE_ANGLES[phase])]
        tolerance = float(condition.max_deviation_degrees)
        body1, body2 = "Moon", "Sun"
        categorical = False
    else:
        if natal_snapshot is None or natal_snapshot.house_cusps is None:
            raise ValueError("Natal house conditions require calculated house cusps.")
        targets = [
            (f"House {index + 1}", longitude)
            for index, longitude in enumerate(natal_snapshot.house_cusps)
        ]
        tolerance = 0.0
        body1, body2 = condition.transit_body, ZODIAC_ORIGIN
        categorical = True

    boundaries, peaks = _collect_phase_crossings(
        start,
        end,
        body1,
        body2,
        targets,
        tolerance,
        positions,
    )
    points = _deduplicate_times([start, *boundaries, end])
    if categorical:
        peaks = []

    if start == end:
        evaluation = _evaluate_condition(
            condition, start, positions, natal_snapshot
        )
        return [
            _ConditionActivity(start, end, (start,))
        ] if evaluation.matched else []

    activities = []
    for left, right in zip(points, points[1:]):
        if right <= left:
            continue
        midpoint = left + (right - left) / 2
        if _evaluate_condition(
            condition, midpoint, positions, natal_snapshot
        ).matched:
            active_peaks = tuple(
                peak for peak in peaks if left <= peak <= right
            )
            activities.append(_ConditionActivity(left, right, active_peaks))
    return _merge_activities(activities)


def _merge_time_windows(windows: Sequence[_TimeWindow]) -> List[_TimeWindow]:
    merged: List[_TimeWindow] = []
    for window in sorted(windows, key=lambda item: (item.start, item.end)):
        if merged and window.start <= merged[-1].end:
            previous = merged[-1]
            merged[-1] = _TimeWindow(previous.start, max(previous.end, window.end))
        else:
            merged.append(window)
    return merged


def _intersect_windows(
    windows: Sequence[_TimeWindow],
    activities: Sequence[_ConditionActivity],
) -> List[_TimeWindow]:
    intersections = []
    for window in windows:
        for activity in activities:
            start = max(window.start, activity.start)
            end = min(window.end, activity.end)
            if start <= end:
                intersections.append(_TimeWindow(start, end))
    return _merge_time_windows(intersections)


def search_opportunities(
    query: OpportunitySearchQuery,
    *,
    _position_provider: Optional[PositionProvider] = None,
) -> List[OpportunityWindow]:
    """Return ranked windows where every required condition is active."""
    start, end = _validate_query(query)
    moving_provider = _position_provider or _SwissEphemerisPositionProvider(
        AspectSearchQuery(
            start=start,
            end=end,
            zodiac=query.zodiac,
            center=query.center,
            bodies=("Sun", "Moon"),
            latitude=query.latitude,
            longitude=query.longitude,
            altitude=query.altitude,
        )
    )
    natal_snapshot = _build_natal_snapshot(query, _position_provider)
    static_positions = {ZODIAC_ORIGIN: 0.0}
    if natal_snapshot is not None:
        static_positions.update(
            {
                _static_natal_key(target): longitude
                for target, longitude in natal_snapshot.positions.items()
            }
        )
    positions = _CachedPositions(
        _StaticOverlayProvider(moving_provider, static_positions)
    )
    activities: Dict[str, List[_ConditionActivity]] = {
        condition.id: _condition_activities(
            condition, start, end, positions, natal_snapshot
        )
        for condition in query.conditions
    }

    candidate_windows = [_TimeWindow(start, end)]
    for condition in query.conditions:
        if condition.required:
            candidate_windows = _intersect_windows(
                candidate_windows, activities[condition.id]
            )
            if not candidate_windows:
                return []

    results = []
    for window in candidate_windows:
        candidate_times = [
            window.start,
            window.start + (window.end - window.start) / 2,
            window.end,
        ]
        for condition in query.conditions:
            for activity in activities[condition.id]:
                candidate_times.extend(
                    peak
                    for peak in activity.peak_times
                    if window.start <= peak <= window.end
                )
        candidate_times = _deduplicate_times(candidate_times)

        best_time = None
        best_score = -1.0
        best_evaluations: Tuple[ConditionEvaluation, ...] = ()
        total_weight = sum(float(condition.weight) for condition in query.conditions)
        for candidate in candidate_times:
            evaluations = tuple(
                _evaluate_condition(
                    condition, candidate, positions, natal_snapshot
                )
                for condition in query.conditions
            )
            if any(
                evaluation.required and not evaluation.matched
                for evaluation in evaluations
            ):
                continue
            score = sum(
                evaluation.score * float(condition.weight)
                for condition, evaluation in zip(query.conditions, evaluations)
            ) / total_weight
            if score > best_score + 1e-9:
                best_time = candidate
                best_score = score
                best_evaluations = evaluations

        if best_time is not None:
            results.append(
                OpportunityWindow(
                    start=window.start.astimezone(timezone.utc),
                    peak=best_time.astimezone(timezone.utc),
                    end=window.end.astimezone(timezone.utc),
                    score=best_score,
                    evaluations=best_evaluations,
                )
            )
    return sorted(results, key=lambda item: (-item.score, item.peak, item.start))


def _parse_local_datetime(value: Any, field: str) -> datetime:
    if not isinstance(value, str):
        raise ValueError(f"{field} must be a local datetime string.")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as error:
        raise ValueError(f"{field} must use YYYY-MM-DD HH:MM format.") from error
    if parsed.tzinfo is not None:
        raise ValueError(f"{field} must not contain a UTC offset; use timezone.")
    return parsed


def _validate_json_keys(
    value: Mapping[str, Any],
    allowed: Sequence[str],
    context: str,
) -> None:
    unknown = sorted(set(value) - set(allowed))
    if unknown:
        raise ValueError(f"Unknown {context} fields: {', '.join(unknown)}")


def _natal_chart_from_dict(data: Any) -> Optional[NatalChart]:
    if data is None:
        return None
    if not isinstance(data, Mapping):
        raise ValueError("natal_chart must be a JSON object.")
    _validate_json_keys(
        data,
        (
            "datetime",
            "timezone",
            "latitude",
            "longitude",
            "altitude",
            "house_system",
            "time_unknown",
        ),
        "natal_chart",
    )
    timezone_name = data.get("timezone")
    if not isinstance(timezone_name, str):
        raise ValueError("natal_chart timezone must be a string.")
    local_timezone = pytz.timezone(timezone_name)
    time_unknown = data.get("time_unknown", False)
    if not isinstance(time_unknown, bool):
        raise ValueError("natal_chart time_unknown must be boolean.")
    local_datetime = _parse_local_datetime(
        data.get("datetime"), "natal_chart datetime"
    )
    if time_unknown:
        local_datetime = local_datetime.replace(
            hour=12, minute=0, second=0, microsecond=0
        )
    try:
        natal_datetime = local_timezone.localize(local_datetime, is_dst=None)
    except (pytz.AmbiguousTimeError, pytz.NonExistentTimeError):
        raise ValueError("natal_chart datetime must be an unambiguous local time.")
    return NatalChart(
        datetime=natal_datetime,
        latitude=data.get("latitude"),
        longitude=data.get("longitude"),
        altitude=data.get("altitude", 0.0),
        house_system=data.get("house_system", "Placidus"),
        time_unknown=time_unknown,
    )


def opportunity_query_from_dict(data: Mapping[str, Any]) -> OpportunitySearchQuery:
    """Build and validate an opportunity query from its JSON-compatible form."""
    if not isinstance(data, Mapping):
        raise ValueError("Opportunity rules must be a JSON object.")
    _validate_json_keys(
        data,
        (
            "start",
            "end",
            "timezone",
            "zodiac",
            "center",
            "latitude",
            "longitude",
            "altitude",
            "natal_chart",
            "conditions",
        ),
        "top-level",
    )
    timezone_name = data.get("timezone", "UTC")
    if not isinstance(timezone_name, str):
        raise ValueError("timezone must be a string.")
    local_timezone = pytz.timezone(timezone_name)
    try:
        start = local_timezone.localize(
            _parse_local_datetime(data.get("start"), "start"), is_dst=None
        )
        end = local_timezone.localize(
            _parse_local_datetime(data.get("end"), "end"), is_dst=None
        )
    except (pytz.AmbiguousTimeError, pytz.NonExistentTimeError):
        raise ValueError("start and end must be unambiguous local times.")

    raw_conditions = data.get("conditions")
    if not isinstance(raw_conditions, list) or not raw_conditions:
        raise ValueError("conditions must be a non-empty JSON array.")
    conditions: List[Condition] = []
    for index, raw in enumerate(raw_conditions):
        if not isinstance(raw, Mapping):
            raise ValueError(f"Condition {index + 1} must be a JSON object.")
        condition_type = raw.get("type")
        common = {"id", "type", "required", "weight"}
        if condition_type == "aspect":
            _validate_json_keys(
                raw,
                tuple(common | {"body1", "body2", "aspects", "max_orb_degrees"}),
                f"condition {index + 1}",
            )
            conditions.append(
                AspectCondition(
                    id=raw.get("id"),
                    body1=raw.get("body1"),
                    body2=raw.get("body2"),
                    aspects=raw.get("aspects"),
                    max_orb_degrees=raw.get("max_orb_degrees"),
                    required=raw.get("required", True),
                    weight=raw.get("weight", 1.0),
                )
            )
        elif condition_type == "natal_aspect":
            _validate_json_keys(
                raw,
                tuple(
                    common
                    | {
                        "transit_body",
                        "natal_target",
                        "aspects",
                        "max_orb_degrees",
                    }
                ),
                f"condition {index + 1}",
            )
            conditions.append(
                NatalAspectCondition(
                    id=raw.get("id"),
                    transit_body=raw.get("transit_body"),
                    natal_target=raw.get("natal_target"),
                    aspects=raw.get("aspects"),
                    max_orb_degrees=raw.get("max_orb_degrees"),
                    required=raw.get("required", True),
                    weight=raw.get("weight", 1.0),
                )
            )
        elif condition_type == "transit_natal_house":
            _validate_json_keys(
                raw,
                tuple(common | {"transit_body", "houses"}),
                f"condition {index + 1}",
            )
            conditions.append(
                TransitNatalHouseCondition(
                    id=raw.get("id"),
                    transit_body=raw.get("transit_body"),
                    houses=raw.get("houses"),
                    required=raw.get("required", True),
                    weight=raw.get("weight", 1.0),
                )
            )
        elif condition_type == "moon_phase":
            _validate_json_keys(
                raw,
                tuple(
                    common
                    | {"phase", "max_deviation_degrees"}
                ),
                f"condition {index + 1}",
            )
            conditions.append(
                MoonPhaseCondition(
                    id=raw.get("id"),
                    phase=raw.get("phase"),
                    max_deviation_degrees=raw.get("max_deviation_degrees"),
                    required=raw.get("required", True),
                    weight=raw.get("weight", 1.0),
                )
            )
        else:
            raise ValueError(f"Unknown condition type: {condition_type}")

    query = OpportunitySearchQuery(
        start=start,
        end=end,
        conditions=tuple(conditions),
        timezone=timezone_name,
        zodiac=data.get("zodiac", "tropical"),
        center=data.get("center", "geocentric"),
        latitude=data.get("latitude"),
        longitude=data.get("longitude"),
        altitude=data.get("altitude", 0.0),
        natal_chart=_natal_chart_from_dict(data.get("natal_chart")),
    )
    _validate_query(query)
    return query


def load_opportunity_query(path: Union[str, Path]) -> OpportunitySearchQuery:
    with open(path, "r", encoding="utf-8") as file:
        return opportunity_query_from_dict(json.load(file))
