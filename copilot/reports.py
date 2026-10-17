"""Pull facts that exist only inside free-text maintenance reports."""
import json
import re

from . import db


def _flat(t: str) -> str:
    return re.sub(r"\s+", " ", t.replace("*", ""))


def extract(text: str) -> dict:
    flat = _flat(text)
    out: dict = {"compliance": [], "action_required": []}
    m = re.search(r"Triggered by:\s*inspection (INS-[\w-]+)", flat)
    out["inspection_id"] = m.group(1) if m else None
    m = re.search(r"contained (?:about |after about |after |within )?(\d+(?:\.\d+)?) hours?", flat, re.I)
    out["containment_hours"] = float(m.group(1)) if m else None
    if m:
        s = max(0, m.start() - 40)
        out["containment_quote"] = flat[s:m.end() + 30].strip()
    m = re.search(r"estimated (\d+(?:\.\d+)?) bbl", flat)
    out["reported_volume_bbl"] = float(m.group(1)) if m else None
    for line in text.splitlines():
        cells = [c.strip().replace("*", "") for c in line.strip().strip("|").split("|")]
        if len(cells) == 3 and cells[0] not in ("Protocol", "---", "") and not set(cells[0]) <= set("-:"):
            if re.search(r"(Met|Not met|In progress|Pending|Action required|N/A)", cells[1], re.I):
                out["compliance"].append({"protocol": cells[0], "result": cells[1], "detail": cells[2]})
                if cells[1].lower().startswith("action"):
                    out["action_required"].append(f"{cells[0]}: {cells[2]}")
    m = re.search(r"\((minor|moderate|reportable|major) class\)", flat, re.I) or \
        re.search(r"(minor|moderate|reportable|major) spill", flat, re.I)
    out["spill_class_stated"] = m.group(1).lower() if m else None
    m = re.search(r"Parts installed:\s*(.+?)(?:\n|$)", text.replace("*", ""))
    if m:
        line = m.group(1).strip()
        out["parts_installed"] = line
        lm = re.search(r"\blot\s+([A-Z0-9-]+)", line, re.I)
        sm = re.search(r"\bserial\s+([A-Z0-9-]+)", line, re.I)
        mm = re.match(r"(.+?)\s+pump", line, re.I)
        out["pump_lot"] = lm.group(1) if lm else None
        out["pump_serial"] = sm.group(1) if sm else None
        out["pump_model"] = mm.group(1).strip() if mm else line.split(",")[0]
    m = re.search(r"Follow-up:\s*(.+?)(?:\n|$)", text.replace("*", ""))
    out["follow_up"] = m.group(1).strip() if m else None
    out["soil_samples_lab"] = "soil samples sent to the lab" in flat.lower()
    out["reporting_duty_stated"] = any(c["protocol"] == "SR-01" for c in out["compliance"])
    m = re.search(r"## Root cause\s+(.+?)(?:\n## |\Z)", text, re.S)
    out["root_cause"] = _flat(m.group(1)).strip() if m else None
    m = re.search(r"\|\s*\*\*Total\*\*\s*\|\s*\*\*([\d,]+)\*\*", text)
    out["cost_total"] = float(m.group(1).replace(",", "")) if m else None
    return out


def build():
    with db.session() as con:
        for r in con.execute("SELECT maintenance_id, text FROM reports").fetchall():
            con.execute("UPDATE reports SET extracted_json=? WHERE maintenance_id=?",
                        (json.dumps(extract(r["text"])), r["maintenance_id"]))
