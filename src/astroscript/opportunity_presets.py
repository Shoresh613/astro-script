"""Load the documented opportunity-rule presets bundled with AstroScript."""

from dataclasses import dataclass
import json
from pathlib import Path
import re
from typing import Any, Mapping, Sequence, Tuple


PRESET_DIRECTORY = Path(__file__).with_name("presets")
PRESET_NAME_PATTERN = re.compile(r"^[a-z0-9_]+$")


@dataclass(frozen=True)
class OpportunityPreset:
    name: str
    title: str
    description: str
    rationale: Tuple[str, ...]
    requires_location: bool
    conditions: Tuple[Mapping[str, Any], ...]


def list_opportunity_presets() -> Tuple[str, ...]:
    """Return the names of all bundled activity presets."""
    return tuple(sorted(path.stem for path in PRESET_DIRECTORY.glob("*.json")))


def _validate_string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Preset {field} must be a non-empty string.")
    return value.strip()


def load_opportunity_preset(name: str) -> OpportunityPreset:
    """Load and validate one bundled activity preset by name."""
    if not isinstance(name, str) or not PRESET_NAME_PATTERN.fullmatch(name):
        raise ValueError(f"Invalid opportunity preset name: {name}")
    available = list_opportunity_presets()
    if name not in available:
        raise ValueError(
            f"Unknown opportunity preset: {name}. Available presets: "
            f"{', '.join(available)}"
        )
    path = PRESET_DIRECTORY / f"{name}.json"
    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)
    if not isinstance(data, Mapping):
        raise ValueError(f"Opportunity preset '{name}' must be a JSON object.")
    allowed = {
        "name",
        "title",
        "description",
        "rationale",
        "requires_location",
        "conditions",
    }
    unknown = sorted(set(data) - allowed)
    if unknown:
        raise ValueError(
            f"Unknown fields in opportunity preset '{name}': {', '.join(unknown)}"
        )
    preset_name = _validate_string(data.get("name"), "name")
    if preset_name != name:
        raise ValueError(
            f"Opportunity preset file '{name}' declares name '{preset_name}'."
        )
    rationale = data.get("rationale")
    if (
        not isinstance(rationale, Sequence)
        or isinstance(rationale, (str, bytes))
        or not rationale
        or any(not isinstance(item, str) or not item.strip() for item in rationale)
    ):
        raise ValueError(
            f"Opportunity preset '{name}' requires non-empty rationale strings."
        )
    requires_location = data.get("requires_location")
    if not isinstance(requires_location, bool):
        raise ValueError(
            f"Opportunity preset '{name}' requires a boolean requires_location."
        )
    conditions = data.get("conditions")
    if (
        not isinstance(conditions, list)
        or not conditions
        or any(not isinstance(condition, Mapping) for condition in conditions)
    ):
        raise ValueError(
            f"Opportunity preset '{name}' requires a non-empty conditions array."
        )
    return OpportunityPreset(
        name=preset_name,
        title=_validate_string(data.get("title"), "title"),
        description=_validate_string(data.get("description"), "description"),
        rationale=tuple(item.strip() for item in rationale),
        requires_location=requires_location,
        conditions=tuple(dict(condition) for condition in conditions),
    )
