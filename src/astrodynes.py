# astrodynes.py
import math
from typing import Dict, List, Tuple
import swisseph as swe

# ================== BOL CONFIG ==================

SIGN_NAMES = [
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
]

PLANETS = {
    "Sun": swe.SUN,
    "Moon": swe.MOON,
    "Mercury": swe.MERCURY,
    "Venus": swe.VENUS,
    "Mars": swe.MARS,
    "Jupiter": swe.JUPITER,
    "Saturn": swe.SATURN,
    "Uranus": swe.URANUS,
    "Neptune": swe.NEPTUNE,
    "Pluto": swe.PLUTO,
}
POINTS = ["Asc", "MC"]

# Base aspect power (perfect hit) in astrodynes
ASPECT_BASE_POWER = {
    0: 12,
    30: 5,
    45: 6,
    60: 9,
    90: 10,
    120: 10,
    135: 7,
    150: 6,
    180: 11,
}

# Aspect polarity per BOL: +1 harmonious, -1 discord, 0 neutral
ASPECT_POLARITY = {
    120: +1,
    60: +1,
    30: +1,
    180: -1,
    90: -1,
    135: -1,
    45: -1,
    0: 0,
    150: 0,
}

# Nature modifiers applied to every aspect a planet participates in
NATURE_BONUS = {"Jupiter": 0.5, "Saturn": -0.5, "Venus": 0.25, "Mars": -0.25}

# Orb tables by aspect, body group, and house class.
# House class: 'angular' (1/4/7/10), 'succedent' (2/5/8/11), 'cadent' (3/6/9/12)
# Group: 'SunMoon' vs 'planet' (Mercury counts as 'SunMoon' only for the *Mercury exception* rule)
# NOTE: Replace any of these with your exact BOL numbers when you finish transcribing the scan.
ORB_TABLE_BOL = {
    "conjunction": {
        "planet": {"succedent": 10.0, "angular": 12.0, "cadent": 8.0},
        "SunMoon": {"succedent": 13.0, "angular": 15.0, "cadent": 11.0},
    },
    "semisextile": {
        "planet": {"succedent": 2.0, "angular": 3.0, "cadent": 1.0},
        "SunMoon": {"succedent": 3.0, "angular": 4.0, "cadent": 2.0},
    },
    "sextile": {
        "planet": {"succedent": 6.0, "angular": 7.0, "cadent": 5.0},
        "SunMoon": {"succedent": 7.0, "angular": 8.0, "cadent": 6.0},
    },
    "square": {
        "planet": {"succedent": 8.0, "angular": 10.0, "cadent": 6.0},
        "SunMoon": {"succedent": 10.0, "angular": 12.0, "cadent": 8.0},
    },
    "trine": {
        "planet": {"succedent": 8.0, "angular": 10.0, "cadent": 6.0},
        "SunMoon": {"succedent": 10.0, "angular": 12.0, "cadent": 8.0},
    },
    "quincunx": {  # aka inconjunct
        "planet": {"succedent": 2.0, "angular": 3.0, "cadent": 1.0},
        "SunMoon": {"succedent": 3.0, "angular": 4.0, "cadent": 2.0},
    },
    "semisquare": {
        "planet": {"succedent": 4.0, "angular": 5.0, "cadent": 3.0},
        "SunMoon": {"succedent": 5.0, "angular": 6.0, "cadent": 4.0},
    },
    "sesquisquare": {
        "planet": {"succedent": 4.0, "angular": 5.0, "cadent": 3.0},
        "SunMoon": {"succedent": 5.0, "angular": 6.0, "cadent": 4.0},
    },
    "opposition": {
        "planet": {"succedent": 10.0, "angular": 12.0, "cadent": 8.0},
        "SunMoon": {"succedent": 13.0, "angular": 15.0, "cadent": 11.0},
    },
    "parallel": {
        "planet": {"succedent": 1.0, "angular": 1.0, "cadent": 1.0},
        "SunMoon": {"succedent": 1.0, "angular": 1.0, "cadent": 1.0},
    },
}


# Parallel configuration (declination)
PARALLEL_ORB_DEG = 1.0  # 1° orb in declination
PARALLEL_PERFECT_POWER = 12.0  # same as perfect conjunction in stronger house
COUNT_CONTRAPARALLEL = False  # set True if you want to include contraparallels

# House cusp power (weaker, stronger) & angle baseline
HOUSE_CUSP_POWER_WS = {
    1: (12.50, 14.50),
    2: (12.00, 14.00),
    3: (7.50, 8.00),
    4: (12.00, 14.00),
    5: (7.00, 7.50),
    6: (6.50, 7.00),
    7: (13.00, 15.00),
    8: (10.00, 10.90),
    9: (9.30, 10.00),
    10: (13.00, 15.00),
    11: (10.90, 11.90),
    12: (8.60, 9.30),
}
ASC_MC_CUSP_POWER = 15.0

# Rulerships & dignities
RULERS_DOMICILE = {
    0: ["Mars"],
    1: ["Venus"],
    2: ["Mercury"],
    3: ["Moon"],
    4: ["Sun"],
    5: ["Mercury"],
    6: ["Venus"],
    7: ["Pluto", "Mars"],
    8: ["Jupiter"],
    9: ["Saturn"],
    10: ["Uranus", "Saturn"],
    11: ["Neptune", "Jupiter"],
}
RULERS_EXALTATION = {
    0: ["Sun"],
    1: ["Moon"],
    3: ["Jupiter"],
    5: ["Mercury"],
    6: ["Saturn"],
    9: ["Mars"],
    11: ["Venus"],
}
EXALT_DEGREES = {
    ("Sun", "Aries"): 19.0,
    ("Moon", "Taurus"): 3.0,
    ("Mercury", "Virgo"): 15.0,
    ("Venus", "Pisces"): 27.0,
    ("Mars", "Capricorn"): 28.0,
    ("Jupiter", "Cancer"): 15.0,
    ("Saturn", "Libra"): 21.0,
}
DIGNITY_WEIGHTS = {
    "MR": 5.0,
    "Exalt": 3.0,
    "ExaltDegree": 4.0,
    "Fall": -3.0,
    "FallDegree": -4.0,
    "Home": 2.0,
    "Detriment": -2.0,
}

# ================== HELPERS ==================


def angle_delta(a, b):
    return abs((a - b + 180.0) % 360.0 - 180.0)


def orb_weight_linear(delta, max_orb):
    return max(0.0, 1.0 - delta / max_orb)


def arc_fraction(a, b, x):
    a, b, x = a % 360.0, b % 360.0, x % 360.0
    span = (b - a) % 360.0
    run = (x - a) % 360.0
    return 0.0 if span == 0 else run / span


def deg_in_sign(lon):
    return lon % 30.0


def sign_idx_to_name(i):
    return SIGN_NAMES[i]


def sign_name_to_idx(s):
    return SIGN_NAMES.index(s)


def fall_of(planet):
    for (p, sign), deg in EXALT_DEGREES.items():
        if p == planet:
            opp = (sign_name_to_idx(sign) + 6) % 12
            return SIGN_NAMES[opp], deg
    return None, None


def is_ruled_by(planet, sign_idx, rule_map):
    return planet in rule_map.get(sign_idx, [])


def house_class(h):
    return (
        "angular"
        if h in (1, 4, 7, 10)
        else ("succedent" if h in (2, 5, 8, 11) else "cadent")
    )


def aspect_kind(angle):
    return {
        0: "conjunction",
        30: "semisextile",
        45: "semisquare",
        60: "sextile",
        90: "square",
        120: "trine",
        135: "sesquisquare",
        150: "quincunx",
        180: "opposition",
    }[angle]


def obliquity_true_deg(jd_ut):
    xx, _ = swe.calc_ut(jd_ut, swe.ECL_NUT, 0)  # xx[0]=true obliquity (deg)
    return xx[0]


# ================== CORE CLASS ==================


class AstrodyneCalculator:
    """
    BOL-style Astrodynes with zodiacal aspects, declination Parallels,
    dignities/MR, and BOL sign/house totals.
    """

    def __init__(
        self,
        y: int,
        m: int,
        d: int,
        hour_utc: float,
        lat: float,
        lon: float,
        house_system: str = "P",
        ephe_path: str = None,
    ):
        self.jd_ut = swe.julday(y, m, d, hour_utc)
        self.lat, self.lon = lat, lon
        self.house_system = house_system
        if ephe_path:
            swe.set_ephe_path(ephe_path)
        swe.set_topo(lon, lat, 0)
        self.positions = self._compute_positions()
        self.houses = self._compute_houses()
        self._eps_true = math.radians(obliquity_true_deg(self.jd_ut))

    # ---------- positions & houses ----------

    def _compute_positions(self) -> Dict[str, Dict]:
        pos = {}
        # We need both ecliptic longitudes and declinations
        flags_eq = swe.FLG_SWIEPH | swe.FLG_SPEED | swe.FLG_EQUATORIAL
        flags_ec = swe.FLG_SWIEPH | swe.FLG_SPEED
        for name, body in PLANETS.items():
            xx_eq, _ = swe.calc_ut(
                self.jd_ut, body, flags_eq
            )  # RA, Dec, Dist, RA_speed...
            xx_ec, _ = swe.calc_ut(
                self.jd_ut, body, flags_ec
            )  # Lon, Lat, Dist, Lon_speed...
            lon = xx_ec[0] % 360.0
            pos[name] = {
                "lon": lon,
                "sign": int(lon // 30),
                "speed": xx_ec[3],
                "dec": xx_eq[1],
            }
        return pos

    def _compute_houses(self):
        hs = self.house_system.encode()
        hcusps, ascmc, _ = swe.houses_ex(self.jd_ut, self.lat, self.lon, hs, b"T")
        cusps = [None] + [c % 360.0 for c in hcusps[:12]]
        asc, mc = ascmc[0] % 360.0, ascmc[1] % 360.0
        planet_houses = {}
        for name, p in self.positions.items():
            h = swe.house_pos(asc, mc, self.lat, hcusps, p["lon"], 0.0, hs)[0]
            planet_houses[name] = max(1, min(12, int(math.ceil(h))))
        return {"cusps": cusps, "asc": asc, "mc": mc, "planet_houses": planet_houses}

    # ---------- house power interpolation ----------

    def _house_power_for(self, house: int, lon: float) -> float:
        n1, n2 = house, (1 if house == 12 else house + 1)
        weak, strong = HOUSE_CUSP_POWER_WS[house]
        frac = arc_fraction(self.houses["cusps"][n1], self.houses["cusps"][n2], lon)
        return strong + frac * (weak - strong)

    # ---------- points, declinations, parallels ----------

    def _all_points(self) -> Dict[str, Dict]:
        pts = {**self.positions}

        # declinations for angles from ecliptic longitude (lat=0)
        def dec_from_lon(lon_deg):
            lon = math.radians(lon_deg % 360.0)
            dec = math.degrees(math.sin(self._eps_true) * math.sin(lon))
            return dec

        asc_lon, mc_lon = self.houses["asc"], self.houses["mc"]
        pts["Asc"] = {
            "lon": asc_lon,
            "sign": int(asc_lon // 30),
            "speed": 0.0,
            "dec": dec_from_lon(asc_lon),
        }
        pts["MC"] = {
            "lon": mc_lon,
            "sign": int(mc_lon // 30),
            "speed": 0.0,
            "dec": dec_from_lon(mc_lon),
        }
        return pts

    def _parallel_hits(self, include_contra: bool = COUNT_CONTRAPARALLEL) -> List[Dict]:
        pts = self._all_points()
        names = list(pts.keys())
        hits = []
        orb_min = PARALLEL_ORB_DEG * 60.0
        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                a, b = names[i], names[j]
                da, db = pts[a]["dec"], pts[b]["dec"]
                same_sign = (
                    (da == 0 and db == 0) or (da > 0 and db > 0) or (da < 0 and db < 0)
                )
                sep_min = abs(abs(da) - abs(db)) * 60.0
                if same_sign and sep_min <= orb_min:
                    hits.append(
                        {"p1": a, "p2": b, "kind": "parallel", "sep_arcmin": sep_min}
                    )
                elif include_contra and (not same_sign) and sep_min <= orb_min:
                    hits.append(
                        {
                            "p1": a,
                            "p2": b,
                            "kind": "contraparallel",
                            "sep_arcmin": sep_min,
                        }
                    )
        return hits

    # ---------- zodiacal aspects ----------

    def _house_of_point(self, name: str) -> int:
        if name in PLANETS:
            return self.houses["planet_houses"][name]
        return 1 if name == "Asc" else 10

    def _house_class_of_point(self, name: str) -> str:
        return house_class(self._house_of_point(name))

    def _max_orb_for(self, angle: int, a: str, b: str) -> float:
        kind = aspect_kind(angle)

        # Mercury exception: treat Mercury as Sun/Moon group when computing its orb
        def group(name):
            if name in ("Sun", "Moon"):
                return "SunMoon"
            if name == "Mercury":
                return "SunMoon"
            return "planet"

        ga, gb = group(a), group(b)
        cla, clb = self._house_class_of_point(a), self._house_class_of_point(b)
        oa = ORB_TABLE_BOL[kind][ga][cla]
        ob = ORB_TABLE_BOL[kind][gb][clb]
        return max(oa, ob)

    def _aspect_hits(self) -> List[Dict]:
        pts = self._all_points()
        names = list(pts.keys())
        hits = []
        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                a, b = names[i], names[j]
                sep = angle_delta(pts[a]["lon"], pts[b]["lon"])
                for ang, base in ASPECT_BASE_POWER.items():
                    delta = min(abs(sep - ang), abs(360.0 - (sep - ang)))
                    mo = self._max_orb_for(ang, a, b)
                    if delta <= mo:
                        hits.append(
                            {
                                "p1": a,
                                "p2": b,
                                "angle": ang,
                                "orb_w": orb_weight_linear(delta, mo),
                                "base_power": base,
                                "polarity": ASPECT_POLARITY[ang],
                            }
                        )
        return hits

    # ---------- dignities & MR ----------

    def mutual_receptions(self):
        pairs, names = [], list(PLANETS.keys())
        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                a, b = names[i], names[j]
                sa, sb = self.positions[a]["sign"], self.positions[b]["sign"]
                if is_ruled_by(a, sb, RULERS_DOMICILE) and is_ruled_by(
                    b, sa, RULERS_DOMICILE
                ):
                    pairs.append((a, SIGN_NAMES[sa], b, SIGN_NAMES[sb], "domicile"))
        return pairs

    def _apply_dignities(self, per_point: Dict[str, Dict]):
        # Home / Detriment, Exalt / Fall (+degree), MR (+5)
        for name in PLANETS.keys():
            lon = self.positions[name]["lon"]
            sidx = self.positions[name]["sign"]
            sign = SIGN_NAMES[sidx]
            # Home/Detriment
            if is_ruled_by(name, sidx, RULERS_DOMICILE):
                b = DIGNITY_WEIGHTS["Home"]
                per_point[name]["power"] += abs(b)
                per_point[name]["harmony"] += b
            elif is_ruled_by(name, (sidx + 6) % 12, RULERS_DOMICILE):
                b = abs(DIGNITY_WEIGHTS["Detriment"])
                per_point[name]["power"] += b
                per_point[name]["discord"] += b
            # Exalt/Fall (+degree)
            if is_ruled_by(name, sidx, RULERS_EXALTATION):
                b = DIGNITY_WEIGHTS["Exalt"]
                per_point[name]["power"] += b
                per_point[name]["harmony"] += b
                ed = EXALT_DEGREES.get((name, sign))
                if ed is not None and abs(deg_in_sign(lon) - ed) <= 1.0:
                    b2 = DIGNITY_WEIGHTS["ExaltDegree"]
                    per_point[name]["power"] += b2
                    per_point[name]["harmony"] += b2
            fs, fd = fall_of(name)
            if fs == sign:
                b = abs(DIGNITY_WEIGHTS["Fall"])
                per_point[name]["power"] += b
                per_point[name]["discord"] += b
                if fd is not None and abs(deg_in_sign(lon) - fd) <= 1.0:
                    b2 = abs(DIGNITY_WEIGHTS["FallDegree"])
                    per_point[name]["power"] += b2
                    per_point[name]["discord"] += b2

        for a, _, b, _, _ in self.mutual_receptions():
            for n in (a, b):
                per_point[n]["power"] += DIGNITY_WEIGHTS["MR"]
                per_point[n]["harmony"] += DIGNITY_WEIGHTS["MR"]

    # ---------- sign & house totals per BOL ----------

    def _sign_house_power_from_rules(self, per_point: Dict[str, Dict]):
        pts = self._all_points()
        house_of = {**self.houses["planet_houses"], "Asc": 1, "MC": 10}

        cusp_signs = [int(self.houses["cusps"][i] // 30) for i in range(1, 13)]
        sign_on_cusp_count = {i: 0 for i in range(12)}
        for s in cusp_signs:
            sign_on_cusp_count[s] += 1

        # find intercepted signs (no cusps)
        intercepted = [i for i in range(12) if sign_on_cusp_count[i] == 0]
        # map intercepted sign to containing house (by midpoint)
        hs = self.house_system.encode()
        hcusps = [0.0] + [self.houses["cusps"][i] for i in range(1, 13)]
        asc, mc = self.houses["asc"], self.houses["mc"]
        intercepted_house = {}
        for s in intercepted:
            midlon = (s * 30.0 + 15.0) % 360.0
            h = swe.house_pos(asc, mc, self.lat, hcusps[1:], midlon, 0.0, hs)[0]
            intercepted_house[s] = max(1, min(12, int(math.ceil(h))))

        def ruler_avg_power(sidx):
            rulers = RULERS_DOMICILE.get(sidx, [])
            return (
                0.0
                if not rulers
                else sum(per_point[r]["power"] for r in rulers) / len(rulers)
            )

        # Sign totals
        sign_power = {name: 0.0 for name in SIGN_NAMES}
        for sidx in range(12):
            avg = ruler_avg_power(sidx)
            m = sign_on_cusp_count[sidx]
            unocc = 0.25 * avg if m == 0 else 0.5 * avg * m
            sign_power[SIGN_NAMES[sidx]] += unocc
        for n, p in pts.items():
            sign_power[SIGN_NAMES[p["sign"]]] += per_point[n]["power"]

        # House totals
        house_power = {h: 0.0 for h in range(1, 13)}
        for h in range(1, 13):
            sidx = cusp_signs[h - 1]
            house_power[h] += 0.5 * ruler_avg_power(sidx)
            for s, hh in intercepted_house.items():
                if hh == h:
                    house_power[h] += 0.25 * ruler_avg_power(s)
            for n in list(PLANETS.keys()) + POINTS:
                if house_of[n] == h:
                    house_power[h] += per_point[n]["power"]
        return sign_power, house_power

    # ---------- main score ----------

    def score(self, normalize_to: float = None) -> Dict[str, Dict]:
        points = list(PLANETS.keys()) + POINTS
        per_point = {n: {"power": 0.0, "harmony": 0.0, "discord": 0.0} for n in points}

        # Baseline: interpolated house power for planets; angles baseline
        for name in PLANETS.keys():
            h = self.houses["planet_houses"][name]
            lon = self.positions[name]["lon"]
            per_point[name]["power"] += self._house_power_for(h, lon)
        per_point["Asc"]["power"] += ASC_MC_CUSP_POWER
        per_point["MC"]["power"] += ASC_MC_CUSP_POWER

        # Zodiacal aspects
        pts = self._all_points()
        for hit in self._aspect_hits():
            n1, n2 = hit["p1"], hit["p2"]
            s = hit["base_power"] * hit["orb_w"]
            pol = hit["polarity"]
            for n in (n1, n2):
                per_point[n]["power"] += abs(s)
                if pol > 0:
                    per_point[n]["harmony"] += s
                elif pol < 0:
                    per_point[n]["discord"] += s
                nb = NATURE_BONUS.get(n, 0.0)
                if nb > 0:
                    per_point[n]["harmony"] += abs(s) * nb
                elif nb < 0:
                    per_point[n]["discord"] += abs(s) * (-nb)

        # Declination Parallels (minute rule)
        orb_min = PARALLEL_ORB_DEG * 60.0
        for ph in self._parallel_hits(include_contra=COUNT_CONTRAPARALLEL):
            n1, n2 = ph["p1"], ph["p2"]
            dist_from_limit = orb_min - ph["sep_arcmin"]
            s = (dist_from_limit * PARALLEL_PERFECT_POWER) / 60.0  # add to power
            for n in (n1, n2):
                per_point[n]["power"] += max(0.0, s)  # floor at 0
                # keep parallels neutral for H/D; still apply nature modifiers if desired:
                nb = NATURE_BONUS.get(n, 0.0)
                if nb > 0:
                    per_point[n]["harmony"] += max(0.0, s) * nb
                elif nb < 0:
                    per_point[n]["discord"] += max(0.0, s) * (-nb)
            # If you want contraparallel to count as discordant, add: per_point[*]['discord'] += s

        # Essential dignities and Mutual Reception
        self._apply_dignities(per_point)

        # Optional normalization (of planetary totals only; BOL examples use raw values)
        if normalize_to:
            tot = sum(v["power"] for v in per_point.values())
            if tot > 0:
                k = normalize_to / tot
                for v in per_point.values():
                    v["power"] *= k
                    v["harmony"] *= k
                    v["discord"] *= k

        # BOL Sign/House totals from planet/angle powers
        sign_power, house_power = self._sign_house_power_from_rules(per_point)

        return {
            "planets": per_point,
            "signs": sign_power,
            "houses": house_power,
            "receptions": self.mutual_receptions(),
        }


# =============== quick demo ===============
if __name__ == "__main__":
    # Example (not John Edwards): 1984-01-01 12:00 UTC, 40N, 74W
    calc = AstrodyneCalculator(1984, 1, 1, 12.0, lat=40.0, lon=-74.0, house_system="P")
    out = calc.score(normalize_to=None)
    print("Planetary Power:")
    for k, v in sorted(out["planets"].items(), key=lambda kv: -kv[1]["power"]):
        print(
            f"{k:8s}  P={v['power']:6.2f}  H={v['harmony']:6.2f}  D={v['discord']:6.2f}"
        )
    print("\nSign Power:")
    for s, val in sorted(out["signs"].items(), key=lambda kv: -kv[1]):
        print(f"{s:12s} {val:7.2f}")
    print("\nHouse Power:")
    for h, val in sorted(out["houses"].items(), key=lambda kv: -kv[1]):
        print(f"House {h:2d}  {val:7.2f}")
    print("\nMutual Receptions:", out["receptions"])
