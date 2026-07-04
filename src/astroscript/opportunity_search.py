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
    DEFAULT_BODY_IDS,
    MAX_PHASE_CHANGE_DEGREES,
    MAX_STEP,
    AspectSearchQuery,
    PositionProvider,
    _CachedPositions,
    _SwissEphemerisPositionProvider,
    _raw_phase,
    _refine_crossing,
    _refine_station,
    _unwrap_near,
    _validate_aware,
)
from .constants import ALL_ASPECTS
from .zodiac import normalize_zodiac


PHASE_ANGLES = {
    "new": 0.0,
    "first_quarter": 90.0,
    "full": 180.0,
    "last_quarter": 270.0,
}
MATCH_TOLERANCE_DEGREES = 1e-6

__all__ = [
    "AspectCondition",
    "MoonPhaseCondition",
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


Condition = Union[AspectCondition, MoonPhaseCondition]


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


def _canonical_phase(value: str) -> str:
    return value.strip().lower().replace("-", "_").replace(" ", "_")


def _number(value: Any, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field} must be a number.")
    return float(value)


def _validate_condition(condition: Condition) -> None:
    if not isinstance(condition.id, str) or not condition.id.strip():
        raise ValueError("Every condition requires a non-empty id.")
    if not isinstance(condition.required, bool):
        raise ValueError(f"Condition '{condition.id}' required must be boolean.")
    weight = _number(condition.weight, f"Condition '{condition.id}' weight")
    if weight <= 0:
        raise ValueError(f"Condition '{condition.id}' weight must be greater than 0.")

    if isinstance(condition, AspectCondition):
        if condition.body1 not in DEFAULT_BODY_IDS:
            raise ValueError(f"Unsupported celestial body: {condition.body1}")
        if condition.body2 not in DEFAULT_BODY_IDS:
            raise ValueError(f"Unsupported celestial body: {condition.body2}")
        if condition.body1 == condition.body2:
            raise ValueError(f"Condition '{condition.id}' requires two different bodies.")
        if (
            isinstance(condition.aspects, (str, bytes))
            or not isinstance(condition.aspects, Sequence)
            or not condition.aspects
        ):
            raise ValueError(f"Condition '{condition.id}' requires at least one aspect.")
        if any(not isinstance(name, str) for name in condition.aspects):
            raise ValueError(f"Condition '{condition.id}' aspects must be strings.")
        unknown = [name for name in condition.aspects if name not in ALL_ASPECTS]
        if unknown:
            raise ValueError(f"Unknown aspects: {', '.join(unknown)}")
        if len(set(condition.aspects)) != len(condition.aspects):
            raise ValueError(f"Condition '{condition.id}' contains duplicate aspects.")
        maximum = _number(
            condition.max_orb_degrees,
            f"Condition '{condition.id}' max_orb_degrees",
        )
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

    if maximum <= 0 or maximum > 180:
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
                for offset, destination in (
                    (-tolerance, boundaries),
                    (0.0, peaks),
                    (tolerance, boundaries),
                ):
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
) -> ConditionEvaluation:
    if isinstance(condition, AspectCondition):
        first = positions.get(when, condition.body1)
        second = positions.get(when, condition.body2)
        phase = _raw_phase(first, second)
        separation = min(phase, 360.0 - phase)
        choices = [
            (
                abs(separation - float(ALL_ASPECTS[name]["Degrees"])),
                index,
                name,
                float(ALL_ASPECTS[name]["Degrees"]),
            )
            for index, name in enumerate(condition.aspects)
        ]
        deviation, _, aspect_name, target = min(choices)
        maximum = float(condition.max_orb_degrees)
        matched = deviation <= maximum + MATCH_TOLERANCE_DEGREES
        score = max(0.0, 1.0 - deviation / maximum) * 100.0
        description = (
            f"{condition.body1} {aspect_name} {condition.body2}: "
            f"orb {deviation:.4f}° / {maximum:.4f}°"
        )
        condition_type = "aspect"
    else:
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
    else:
        phase = _canonical_phase(condition.phase)
        targets = [(phase, PHASE_ANGLES[phase])]
        tolerance = float(condition.max_deviation_degrees)
        body1, body2 = "Moon", "Sun"

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

    if start == end:
        evaluation = _evaluate_condition(condition, start, positions)
        return [
            _ConditionActivity(start, end, (start,))
        ] if evaluation.matched else []

    activities = []
    for left, right in zip(points, points[1:]):
        if right <= left:
            continue
        midpoint = left + (right - left) / 2
        if _evaluate_condition(condition, midpoint, positions).matched:
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
    provider = _position_provider or _SwissEphemerisPositionProvider(
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
    positions = _CachedPositions(provider)
    activities: Dict[str, List[_ConditionActivity]] = {
        condition.id: _condition_activities(
            condition, start, end, positions
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
                _evaluate_condition(condition, candidate, positions)
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
    )
    _validate_query(query)
    return query


def load_opportunity_query(path: Union[str, Path]) -> OpportunitySearchQuery:
    with open(path, "r", encoding="utf-8") as file:
        return opportunity_query_from_dict(json.load(file))
