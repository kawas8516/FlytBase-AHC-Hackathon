"""Deterministic parsing of feedback messages (corrections, rules, statements). Never waits on an LLM.
Returns a plan dict like planner.plan(), or None when the message is not recognisably feedback."""
from __future__ import annotations

import re
from datetime import date, timedelta

from .engine.views import Data

MON = {m: i + 1 for i, m in enumerate(["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"])}
EQUIP = {"pump jack": "pump_jack", "pump_jack": "pump_jack", "flowline": "flowline", "rod string": "rod_string",
         "downhole pump": "downhole_pump", "wellhead": "wellhead", "separator": "separator"}
NUMW = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6}
Q_START = re.compile(r"^\s*(is|are|was|were|which|what|how|show|list|when|who|why|did|do|does|give|find|can|could)\b", re.I)


def _n(s: str) -> int:
    return int(s) if s.isdigit() else NUMW[s.lower()]


def parse_date(text: str, today: date) -> date | None:
    m = re.search(r"\b(\d{1,2})(?:st|nd|rd|th)?\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?(?:\s+(20\d\d))?", text, re.I)
    if not m:
        return None
    y = int(m.group(3)) if m.group(3) else today.year
    try:
        dd = date(y, MON[m.group(2).lower()[:3]], int(m.group(1)))
    except ValueError:
        return None
    if not m.group(3) and dd > today + timedelta(days=200):
        dd = date(y - 1, dd.month, dd.day)
    return dd


def parse_feedback(q: str, d: Data) -> dict | None:
    ql = q.lower().strip()
    if ql.endswith("?") or Q_START.match(ql):
        return None
    wells = [w.upper() for w in re.findall(r"WELL-\d{3,5}", q, re.I)]
    today = d.today
    flat = re.sub(r"\s+", " ", q).strip()

    # 1) a rule for a well type
    m = re.search(r"\b(?:all|every|for)\s+(t\d+\w*)\s+wells\b", ql) or re.search(r"\b(t\d+\w*)\s+wells\b", ql)
    n = re.search(r"after\s+(\d+|one|two|three|four|five)\s+(?:repairs?|corrective|failures?|events?)", ql)
    if m and n and re.search(r"root.?cause|\brca\b|analysis", ql):
        eq = next((v for k, v in EQUIP.items() if k in ql), None)
        return {"intent": "rule", "steps": [], "_router": "parser",
                "rule": {"scope_type": "well_type", "scope_id": m.group(1).upper(), "key": "rca_corrective_count",
                         "equipment": eq, "value": _n(n.group(1)), "reason": flat}}

    # 2) correction of the AI's analysis (spill volume)
    if wells and re.search(r"\bbbl\b|barrel", ql):
        vols = [float(x) for x in re.findall(r"(\d+(?:\.\d+)?)\s*(?:bbl|barrels?)", ql)]
        if len(vols) >= 2 or re.search(r"not\s+\d|instead|actually", ql):
            dt = parse_date(q, today)
            return {"intent": "correction", "steps": [], "_router": "parser",
                    "correction": {"well": wells[0], "date": str(dt) if dt else "", "field": "spill_est_volume_bbl",
                                   "value": vols[-1], "reason": flat}}

    # 3) "that was a puddle, not oil"
    if wells and re.search(r"not (?:an? )?(?:crude|oil|spill)|was (?:only )?(?:water|rain|a puddle|mud)|puddle|rainwater|shadow", ql):
        dt = parse_date(q, today)
        return {"intent": "correction", "steps": [], "_router": "parser",
                "correction": {"well": wells[0], "date": str(dt) if dt else "", "field": "spill_detected", "value": 0, "reason": flat}}

    # 4) correction of a raw reading
    if wells and re.search(r"\b(reading|temperature|temp|wellhead|measured|re-?measured)\b", ql) and \
            re.search(r"wrong|incorrect|faulty|error|mistake|not right|bad reading", ql):
        vals = re.findall(r"(\d+(?:\.\d+)?)\s*°?\s*c\b", ql)
        if vals:
            field = "ambient_temp_c" if re.search(r"\b(air|ambient)\b", ql) and "wellhead" not in ql else "wellhead_temp_c"
            parts = re.split(r"(?<=[.;])\s+", flat, maxsplit=1)
            dt = parse_date(q, today)
            return {"intent": "correction", "steps": [], "_router": "parser",
                    "correction": {"well": wells[0], "date": str(dt) if dt else "", "field": field,
                                   "value": float(vals[-1]), "reason": parts[1] if len(parts) > 1 else flat}}

    # 5) a statement about a well's state
    if wells:
        down = re.search(r"shut[- ]?in|shut down|will be down|is down|down for|planned (?:work|maintenance|workover|shutdown)|workover|offline|stopped", ql)
        up = re.search(r"running|back online|online since|producing|back up|restarted|working fine|is fine", ql)
        if down or up:
            since = None
            mm = re.search(r"(?:from|since|on|starting|starts?)\s+(\d{1,2}(?:st|nd|rd|th)?\s+[a-z]{3,9}(?:\s+20\d\d)?)", q, re.I)
            if mm:
                since = parse_date(mm.group(1), today)
            dur = re.search(r"(\d+)[- ]day", ql) or re.search(r"for (?:about |around )?(\d+)\s+days", ql)
            return {"intent": "statement", "steps": [], "_router": "parser",
                    "statement": {"well": wells[0], "producing": False if down else True,
                                  "since": str(since) if since else None, "until": None,
                                  "duration_days": int(dur.group(1)) if dur else None, "shared": True}}
    return None
