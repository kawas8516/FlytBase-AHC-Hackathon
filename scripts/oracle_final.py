"""Independent cross-check for final questions Q3, Q4, Q5, Q6. Reads the raw dataset files directly (no copilot code)
and compares with docs/results_final.json. Usage: python scripts/oracle_final.py <test-data/dataset>"""
import json
import re
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "../flytbase-ahc-swe-asset-intelligence-dataset/test-data/dataset")
TODAY = date(2027, 1, 15)


def ts(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00")).replace(tzinfo=None)


def jl(p):
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()] if p.exists() else []


wells = {}
for wd in sorted((ROOT / "assets").iterdir()):
    m = json.loads((wd / "metadata.json").read_text(encoding="utf-8"))
    wells[m["asset_id"]] = {"meta": m, "ins": jl(wd / "inspections.jsonl"), "mnt": jl(wd / "maintenance.jsonl"), "notes": jl(wd / "context.jsonl"), "dir": wd}
areas = {a["area_id"]: a["name"] for a in json.loads((ROOT / "fleet/areas.json").read_text(encoding="utf-8"))["areas"]}
limit = {"T200": 15, "T350": 20, "T500": 25}  # from the three manuals (checked by hand)


def type_at(m, d):
    for seg in m.get("type_history") or []:
        f = date.fromisoformat(seg["from"]) if seg.get("from") else date.min
        t = date.fromisoformat(seg["to"]) if seg.get("to") else date.max
        if f <= d <= t:
            return seg["well_type"]
    return m["well_type"]


def corrected(w):
    dc = {(n["inspection_id"], n["field"]): n["corrected_value"] for n in w["notes"] if n["note_type"] == "data_correction"}
    out = []
    for r in w["ins"]:
        r = dict(r)
        for f in ("wellhead_temp_c", "ambient_temp_c", "spill_est_volume_bbl"):
            if (r["inspection_id"], f) in dc:
                r[f] = dc[(r["inspection_id"], f)]
        out.append(r)
    return sorted(out, key=lambda r: r["inspected_at"])


# ---- Q3
gas_re = re.compile(r"gas odou?r|smell(?:ed)? gas|gas smell|rotten[- ]egg|h2s monitor alarm", re.I)
q3 = {"reports": 0, "met": 0, "missed": 0}
for aid, w in wells.items():
    for n in w["notes"]:
        if n["note_type"] != "operator_note" or not gas_re.search(n["text"]):
            continue
        t = ts(n["created_at"])
        if not (date(2026, 11, 1) <= t.date() <= TODAY):
            continue
        q3["reports"] += 1
        lim = 24 if t.date() < date(2027, 1, 1) else 12
        cands = [ts(j["started_at"]) for j in w["mnt"] if ts(j["started_at"]) > t] + \
                [ts(i["inspected_at"]) for i in w["ins"] if i["method"] == "manual" and ts(i["inspected_at"]) > t]
        if cands and (min(cands) - t).total_seconds() / 3600 <= lim:
            q3["met"] += 1
        elif cands or (datetime.combine(TODAY + timedelta(days=1), datetime.min.time()) - t).total_seconds() / 3600 > lim:
            q3["missed"] += 1

# ---- Q4
memos = {}
for f in (ROOT / "fleet/sops").glob("moc-*.md"):
    t = f.read_text(encoding="utf-8")
    mid = re.search(r"MOC-\d{4}-\d+", t).group(0)
    exp = datetime.strptime(re.search(r"expires on (\d{1,2} \w+ \d{4})", t).group(1), "%d %b %Y").date()
    ext = re.search(r"extends (MOC-\d{4}-\d+)", t)
    memos[mid] = {"wells": set(re.findall(r"WELL-\d+", t)), "exp": exp, "ext": ext.group(1) if ext else None}
for m in list(memos.values()):
    if m["ext"]:
        memos[m["ext"]]["exp"] = m["exp"]
bin_re = re.compile(r"bypass in place|put the bypass in|bypass installed|had the bypass installed", re.I)
bout_re = re.compile(r"took the bypass out|bypass removed|bypass pulled", re.I)
q4 = {"now": [], "violations": []}
for aid, w in wells.items():
    notes = sorted([n for n in w["notes"] if n["note_type"] == "operator_note" and "bypass" in n["text"].lower() and ts(n["created_at"]).date() <= TODAY],
                   key=lambda n: n["created_at"])
    cur = None
    spans = []
    for n in notes:
        if bout_re.search(n["text"]) and cur:
            spans.append((cur, n)); cur = None
        elif bin_re.search(n["text"]) and not cur:
            cur = n
    if cur:
        spans.append((cur, None))
    for a, b in spans:
        memo = next((m for k, m in memos.items() if aid in m["wells"] and not m["ext"]), None)
        end = ts(b["created_at"]).date() if b else TODAY
        st = "Not approved" if not memo else ("Expired" if end > memo["exp"] else "Allowed")
        if b is None:
            q4["now"].append((aid, st))
        if st != "Allowed":
            q4["violations"].append((aid, st))

# ---- Q5
q5 = {"covered": [], "not_compliant": []}
for aid, w in wells.items():
    if w["meta"]["area_id"] not in ("NE-07", "NE-08"):
        continue
    notcrude = {n["inspection_id"] for n in w["notes"] if n["note_type"] == "correction" and n.get("inspection_id")}
    for r in corrected(w):
        d = ts(r["inspected_at"]).date()
        if not r["spill_detected"] or r["inspection_id"] in notcrude or d < date(2026, 6, 1) or d > TODAY:
            continue
        if (r["spill_est_volume_bbl"] or 0) < 5:
            continue
        q5["covered"].append(aid)
        job = next((j for j in w["mnt"] if j.get("triggered_by_inspection_id") == r["inspection_id"]), None)
        txt = (w["dir"] / job["report_file"]).read_text(encoding="utf-8") if job and job.get("report_file") and (w["dir"] / job["report_file"]).exists() else ""
        if "Soil samples sent to the lab." not in txt:
            q5["not_compliant"].append(aid)

# ---- Q6
shut_re = re.compile(r"\bshut[- ]?in\b|shut the well in|shut in ", re.I)
rest_re = re.compile(r"restarted|back on production|back online|put back on", re.I)
q6 = []
for aid, w in wells.items():
    if "plugged" in (w["meta"].get("status") or "") or "plugged" in (w["meta"].get("recorded_status") or ""):
        continue
    ins = [r for r in corrected(w) if ts(r["inspected_at"]).date() <= TODAY]
    if not ins:
        continue
    last, prev = ins[-1], (ins[-2] if len(ins) > 1 else ins[-1])
    lt = ts(last["inspected_at"])
    prod = round(last["wellhead_temp_c"] - last["ambient_temp_c"], 2) >= limit[type_at(w["meta"], lt.date())]
    sr = [n for n in w["notes"] if n["note_type"] == "operator_note" and ts(n["created_at"]).date() <= TODAY and (shut_re.search(n["text"]) or rest_re.search(n["text"]))]
    if not sr:
        continue
    n = max(sr, key=lambda n: n["created_at"])
    nprod = bool(rest_re.search(n["text"])) and not shut_re.search(n["text"])
    if nprod != prod and ts(n["created_at"]) >= ts(prev["inspected_at"]):
        q6.append(aid)

# ---- compare
res = {x["item"]["id"]: x["answer"] for x in json.loads(Path("docs/results_final.json").read_text(encoding="utf-8"))}
f3 = res["Q3"]["results"][0]["facts"]
f4 = res["Q4"]["results"][0]["facts"]
f5 = res["Q5"]["results"][0]["facts"]
f6 = res["Q6"]["results"][0]["facts"]
checks = [
    ("Q3 reports/met/missed", (q3["reports"], q3["met"], q3["missed"]), (f3["reports"], f3["met"], f3["missed"])),
    ("Q4 in place now", sorted(q4["now"]), sorted(map(tuple, f4["in_place_now"]))),
    ("Q4 violations", sorted(q4["violations"]), sorted(map(tuple, f4["violations"]))),
    ("Q5 covered", len(q5["covered"]), f5["covered"]),
    ("Q5 not compliant", sorted(q5["not_compliant"]), sorted(f5["not_compliant"])),
    ("Q6 wells", sorted(q6), sorted(f6["wells"])),
]
bad = 0
for name, oracle, copilot in checks:
    ok = oracle == copilot
    bad += not ok
    print(f"{'OK  ' if ok else 'DIFF'} {name}: oracle={oracle} copilot={copilot}")
sys.exit(1 if bad else 0)
