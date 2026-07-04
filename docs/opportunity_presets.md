# Opportunity presets

Presets are transparent, version-controlled starting points for electional
searches. They define astrological rules and weights; they do not guarantee an
outcome. Copy a preset's JSON if you want to change its assumptions.

All required conditions must be active. Optional conditions do not exclude a
window but contribute their configured weight to its `0-100` score. Preset
condition IDs are namespaced, so presets can be combined with each other and
with custom conditions.

## `general_election`

A location-independent baseline for a generally workable start.

| Condition | Required | Weight |
| --- | --- | ---: |
| Moon is not Void of Course | yes | 3 |
| Mercury is direct | no | 1 |
| Venus is direct | no | 1 |

## `communication_and_contracts`

For conversations, publishing, negotiations, agreements, and signing
documents. Requires latitude and longitude because planetary hours are used.

| Condition | Required | Weight |
| --- | --- | ---: |
| Moon is not Void of Course | yes | 2 |
| Mercury is direct | yes | 3 |
| Mercury in Gemini, Virgo, or Aquarius | no | 1 |
| Mercury conjunct, trine, or sextile Jupiter within 2 degrees | no | 2 |
| Mercury planetary hour | no | 1 |

## `relationships_and_social`

For dates, celebrations, reconciliation, networking, and relationship-focused
starts. Requires latitude and longitude.

| Condition | Required | Weight |
| --- | --- | ---: |
| Moon is not Void of Course | yes | 2 |
| Venus is direct | yes | 3 |
| Venus in Taurus, Libra, or Pisces | no | 2 |
| Moon in Taurus, Cancer, Libra, or Pisces | no | 1 |
| Venus conjunct, trine, or sextile Jupiter within 2 degrees | no | 2 |
| Venus or Jupiter planetary hour | no | 1 |

## `creative_work`

For beginning artistic, design, writing, and other creative work. Requires
latitude and longitude.

| Condition | Required | Weight |
| --- | --- | ---: |
| Moon is not Void of Course | yes | 2 |
| Mercury is direct | no | 1 |
| Venus is direct | no | 1 |
| Moon in Taurus, Leo, Libra, or Pisces | no | 2 |
| Venus conjunct, trine, or sextile Neptune within 2 degrees | no | 2 |
| Sun, Venus, or Mercury planetary hour | no | 1 |

## `launch_and_business`

For launches, company starts, major releases, and commercially important
beginnings. Requires latitude and longitude.

| Condition | Required | Weight |
| --- | --- | ---: |
| Moon is not Void of Course | yes | 3 |
| Mercury is direct | yes | 2 |
| Jupiter is direct | no | 1 |
| Moon in Aries, Taurus, Leo, or Capricorn | no | 1 |
| Sun conjunct, trine, or sextile Jupiter within 2 degrees | no | 2 |
| Sun or Jupiter planetary hour | no | 1 |

## Using and extending presets

Reference one or more names in an opportunity rule file:

```json
{
  "start": "2026-08-01 00:00",
  "end": "2026-08-08 00:00",
  "timezone": "Europe/Stockholm",
  "latitude": 57.7089,
  "longitude": 11.9746,
  "presets": ["relationships_and_social"]
}
```

Add a `conditions` array to impose project-specific requirements. Custom IDs
must not duplicate any preset condition ID. Multiple presets are merged in list
order; all of their required conditions remain required and all weights count
toward the final score.

List the installed presets with:

```bash
python astro_script.py --list-opportunity-presets
```

The Python API provides `list_opportunity_presets()` and
`load_opportunity_preset(name)` from `astroscript.opportunity_presets` or
`astroscript.opportunity_search`.
