"""Question -> validated plan (the 'How I read this' layer).
The LLM only fills slots. Code extracts what it can deterministically (well IDs, areas, visuals, periods)
and those values win over the LLM's."""
from __future__ import annotations

import json
import re
from datetime import date, timedelta

import pandas as pd

from . import llm
from .engine.views import Data

OPS = {
    "well_status": "Current state of ONE well: producing or not right now, last inspection, who inspected, why it is down. params: wells[1]",
    "wells_status": "List wells in an area/type that are (not) producing right now and why. params: area|well_type, producing (false = not producing)",
    "series": "Wellhead vs air temperature over time for one well. params: wells[1], period or weeks",
    "downtime": "Days not producing (7 per non-producing weekly inspection), per well, ranked. params: wells|area|well_type, period, top",
    "spills": "List/count/total barrels of real oil spills. params: wells|area, period. Use viz=map for 'where'/'on a map'",
    "spill_heatmap": "Spills by area x month for a year. params: year",
    "repairs": "Repairs and their cost. params: wells|area, period, equipment, maintenance_type",
    "rca_due": "Wells that need a root-cause analysis (repeated corrective repairs on the same equipment). params: area|wells|well_type, equipment",
    "compliance_audit": "Which rules/SOPs a well broke, fines, what is still open. params: wells[1], period",
    "spills_check": "Spills that broke or needed a protocol: SR-02 containment time limit, SR-01 regulator report. params: area|wells, period, protocol",
    "spill_verdict": "Was a specific detected spill real oil; disagreements about it. params: wells[1], date",
    "planned_downtime": "Planned/upcoming shut-ins or downtime for a well. params: wells[1]",
    "search_docs": "Question about rules, manuals, SOPs, procedures or report text with no computation. params: query",
}

INTENTS = {
    "query": "a question about the data",
    "correction": "user says a recorded value or the AI's estimate is wrong and gives the right value",
    "rule": "user sets a new rule/threshold for a well type or a well, replacing the manual's value",
    "statement": "user tells a fact about a well's state (shut in, down, running, back online, planned work) for others to know",
}

SYSTEM = """You turn an oil-field operator's message into a JSON plan for a deterministic engine. You never answer the question yourself.
Today is {today}. "Right now" means each well's latest inspection. Output ONLY one JSON object, no prose.

Intents: {intents}

Operations (pick one or more steps, in order):
{ops}

JSON shape:
{{"intent": "query|correction|rule|statement",
  "steps": [{{"op": "<operation>", "wells": ["WELL-0001"], "area": "<area name or null>", "well_type": "<type or null>",
             "period": {{"last": 90, "unit": "days|weeks|months|years"}} | {{"year": 2025}} | {{"from": "YYYY-MM-DD", "to": "YYYY-MM-DD"}} | null,
             "top": null, "producing": null, "equipment": "<pump_jack|flowline|rod_string|downhole_pump|wellhead|separator|prime_mover or null>",
             "protocol": "<SR-01|SR-02|... or null>", "date": "YYYY-MM-DD or null", "maintenance_type": "corrective|scheduled|null",
             "query": "<for search_docs>", "weeks": null}}],
  "previous_reference": {{"count": 3, "what": "wells"}} | null,
  "viz": "table|bar|line|map|heatmap|card|null",
  "correction": {{"well": "WELL-0001", "date": "YYYY-MM-DD", "field": "wellhead_temp_c|ambient_temp_c|spill_est_volume_bbl|spill_detected", "value": 0, "reason": "..."}} | null,
  "rule": {{"scope_type": "well_type|well", "scope_id": "T350", "key": "rca_corrective_count|producing_delta_c", "equipment": "pump_jack|null", "value": 2, "reason": "..."}} | null,
  "statement": {{"well": "WELL-0001", "producing": true|false, "since": "YYYY-MM-DD|null", "until": "YYYY-MM-DD|null", "duration_days": null, "shared": true}} | null}}

Rules:
- "the wells we discussed", "those wells", "yesterday's wells": set previous_reference (count if stated) and leave wells empty.
- "this year" = from {year}-01-01 to today. "this summer" = Jun 1 to Aug 31 of this year. Dates without a year are in {year} unless that is after today.
- A correction of a reading (temperature) uses wellhead_temp_c or ambient_temp_c; a correction of a spill size uses spill_est_volume_bbl; "not oil/was water/puddle" uses spill_detected with value false.
- "after 2 repairs, not 3" for RCA means rule key rca_corrective_count value 2.
- A statement that a well "is running/back online" means producing true; "shut in/down/planned work/workover" means producing false.
- If the user names a visual (table, bar chart, line chart, map, heatmap, card), set viz.

Examples:
Q: "Is WELL-0042 running right now?" -> {{"intent":"query","steps":[{{"op":"well_status","wells":["WELL-0042"]}}],"viz":null}}
Q: "Top 5 wells in Southwest Block 24 by downtime in the last 6 months, as a table" -> {{"intent":"query","steps":[{{"op":"downtime","area":"Southwest Block 24","period":{{"last":6,"unit":"months"}},"top":5}}],"viz":"table"}}
Q: "Which spills in Northeast Block 7 this year were not reported to the regulator in time?" -> {{"intent":"query","steps":[{{"op":"spills_check","area":"Northeast Block 7","period":{{"from":"{year}-01-01","to":"{today}"}},"protocol":"SR-01"}}]}}
Q: "The 3 Sep reading for WELL-0090 is wrong, the ambient was really 30.5 C, the sensor was in the sun" -> {{"intent":"correction","steps":[],"correction":{{"well":"WELL-0090","date":"{year}-09-03","field":"ambient_temp_c","value":30.5,"reason":"the sensor was in the sun"}}}}
Q: "For T200 wells we want an RCA on flowlines after 4 repairs" -> {{"intent":"rule","steps":[],"rule":{{"scope_type":"well_type","scope_id":"T200","key":"rca_corrective_count","equipment":"flowline","value":4,"reason":"team policy"}}}}
Q: "Heads up: WELL-0033 goes down on 2 Nov for 5 days of pump work" -> {{"intent":"statement","steps":[],"statement":{{"well":"WELL-0033","producing":false,"since":"{year}-11-02","until":null,"duration_days":5,"shared":true}}}}
Q: "What did repairs cost on the wells we talked about last time?" -> {{"intent":"query","steps":[{{"op":"repairs"}}],"previous_reference":{{"count":null,"what":"wells"}}}}
"""

VIZ_WORDS = [("heatmap", "heatmap"), ("heat map", "heatmap"), ("line chart", "line"), ("bar chart", "bar"), ("bar graph", "bar"),
             ("on a map", "map"), ("map", "map"), ("table", "table"), ("card", "card"), ("chart", None)]


def _num_word(s):
    w = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10, "twelve": 12}
    return int(s) if s.isdigit() else w.get(s.lower())


def pre_extract(q: str, d: Data) -> dict:
    """Deterministic slots that override the LLM."""
    out: dict = {}
    wells = re.findall(r"WELL-\d{3,5}", q, re.I)
    if wells:
        out["wells"] = [w.upper() for w in wells]
    ql = q.lower()
    for aid, nm in sorted(d.area_name.items(), key=lambda x: -len(x[1] or "")):
        if nm and nm.lower() in ql or re.search(rf"\b{re.escape(aid.lower())}\b", ql):
            out["area"] = nm
            break
    for t in sorted(d.wells.well_type.dropna().unique()):
        if re.search(rf"\b{t.lower()}\b", ql):
            out["well_type"] = t
    for word, v in VIZ_WORDS:
        if word in ql:
            out["viz"] = v
            break
    m = re.search(r"(?:last|past|previous)\s+(\d+|one|two|three|four|five|six|seven|eight|nine|ten|twelve)?\s*(day|week|month|year)s?", ql)
    if m:
        out["period"] = {"last": _num_word(m.group(1)) if m.group(1) else 1, "unit": m.group(2) + "s"}
    m = re.search(r"\bin (20\d\d)\b|\bof (20\d\d)\b|\b(20\d\d) spills\b", ql)
    if m and "period" not in out:
        out["period"] = {"year": int(next(g for g in m.groups() if g))}
    if re.search(r"\bthis year\b", ql):
        out["period"] = {"from": f"{d.today.year}-01-01", "to": d.today.isoformat()}
    m = re.search(r"\b(?:top|which)\s+(\d+|three|five|ten)\b", ql)
    if m:
        out["top"] = _num_word(m.group(1))
    m = re.search(r"\b(?:the|those|these)\s+(\d+|two|three|four|five)\s+wells\b.*\b(?:discussed|talked|looked|yesterday|earlier|last time)", ql)
    if m or re.search(r"wells we (?:discussed|talked about|looked at)", ql):
        out["previous_reference"] = {"count": _num_word(m.group(1)) if m else None, "what": "wells"}
    return out


def resolve_period(p, d: Data) -> tuple[date | None, date | None, str]:
    if not p:
        return None, None, "all time"
    if "last" in p and p.get("last"):
        a, b = d.window(int(p["last"]), str(p.get("unit", "days")))
        return a, b, f"last {p['last']} {p.get('unit')} ({a:%d %b %Y} to {b:%d %b %Y})"
    if "year" in p and p.get("year"):
        y = int(p["year"])
        return date(y, 1, 1), min(date(y, 12, 31), d.today), str(y)
    a = date.fromisoformat(p["from"]) if p.get("from") else None
    b = date.fromisoformat(p["to"]) if p.get("to") else d.today
    return a, b, f"{a:%d %b %Y} to {b:%d %b %Y}" if a else f"until {b:%d %b %Y}"


def plan(question: str, d: Data, use_llm=True) -> dict:
    pre = pre_extract(question, d)
    p = None
    if use_llm:
        sys = SYSTEM.format(today=d.today.isoformat(), year=d.today.year,
                            intents="\n".join(f"- {k}: {v}" for k, v in INTENTS.items()),
                            ops="\n".join(f"- {k}: {v}" for k, v in OPS.items()))
        try:
            p = llm.complete_json(f"Message: {question}\nJSON:", system=sys, purpose="plan", max_tokens=3000)
        except Exception as e:  # noqa: BLE001
            p = {"_error": str(e)}
    if not p or "_error" in p or not isinstance(p.get("steps", []), list):
        p = {**(p or {}), **fallback_plan(question, pre)}
    p.setdefault("steps", [])
    p.setdefault("intent", "query")
    # deterministic slots win
    if pre.get("viz"):
        p["viz"] = pre["viz"]
    if pre.get("previous_reference"):
        p["previous_reference"] = pre["previous_reference"]
    for s in p["steps"]:
        if s.get("op") not in OPS:
            s["op"] = "search_docs"
            s.setdefault("query", question)
        if pre.get("wells") and not p.get("previous_reference"):
            s["wells"] = pre["wells"] if s["op"] not in ("well_status", "series", "compliance_audit", "spill_verdict", "planned_downtime") or not s.get("wells") else s["wells"]
        if pre.get("area"):
            s["area"] = pre["area"]
        if pre.get("period") and s["op"] not in ("well_status", "wells_status", "planned_downtime", "spill_heatmap"):
            s["period"] = pre["period"]
        if pre.get("top") and s["op"] in ("downtime", "repairs", "spills"):
            s["top"] = pre["top"]
        if s["op"] == "spill_heatmap" and not s.get("year"):
            per = s.get("period") or pre.get("period") or {}
            s["year"] = per.get("year") or d.today.year
    return p


def fallback_plan(q: str, pre: dict) -> dict:
    """Keyword router used when the LLM is unavailable. Covers the common question shapes."""
    ql = q.lower()
    wells = pre.get("wells", [])
    st = {"wells": wells, "area": pre.get("area"), "period": pre.get("period"), "top": pre.get("top")}
    if re.search(r"heatmap|by (?:geographic )?area and month", ql):
        op = "spill_heatmap"
    elif re.search(r"root.cause|\brca\b", ql):
        op = "rca_due"; st["equipment"] = "pump_jack" if "pump jack" in ql else ("flowline" if "flowline" in ql else None)
    elif re.search(r"rules? .*broken|breach|violat|compliance|still open", ql):
        op = "compliance_audit"
    elif re.search(r"contain", ql):
        op = "spills_check"; st["protocol"] = "SR-02"
    elif re.search(r"report(?:ed)? to the regulator|needed a report|reportable", ql):
        op = "spills_check"; st["protocol"] = "SR-01"
    elif re.search(r"real oil|was the .* spill", ql):
        op = "spill_verdict"
        m = re.search(r"(\d{1,2}) (jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)", ql)
        if m:
            st["date"] = str(pd.Timestamp(f"{m.group(1)} {m.group(2)} {pre.get('year', 2026)}").date())
    elif re.search(r"spill", ql):
        op = "spills"
    elif re.search(r"planned|upcoming|scheduled shut", ql) and wells:
        op = "planned_downtime"
    elif re.search(r"down|downtime", ql) and re.search(r"how many days|most|longest|downtime", ql):
        op = "downtime"
    elif re.search(r"cost|repair", ql):
        op = "repairs"
    elif re.search(r"temperature|line chart|over time", ql):
        op = "series"
    elif re.search(r"planned", ql):
        op = "planned_downtime"
    elif wells and len(wells) == 1:
        op = "well_status"
    elif re.search(r"not producing|producing", ql):
        op = "wells_status"; st["producing"] = False
    else:
        op = "search_docs"; st["query"] = q
    return {"intent": "query", "steps": [{"op": op, **st}], "_router": "keywords"}
