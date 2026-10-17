"""Parse thresholds out of manuals and SOPs. Nothing here is keyed to a specific well type or ID."""
import re

from . import db

WORDS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6}


def _clean(t: str) -> str:
    return re.sub(r"\s+", " ", t.replace("*", "").replace("`", ""))


def _num(s: str) -> float:
    s = s.lower()
    return float(WORDS[s]) if s in WORDS else float(s.replace(",", ""))


def _sections(text: str):
    """(section_number_or_title, body) from markdown headings."""
    parts = re.split(r"(?m)^(#{2,4} .+)$", text)
    for i in range(1, len(parts), 2):
        yield parts[i].lstrip("# ").strip(), parts[i + 1]


def parse_manual(doc_id: str, text: str) -> tuple[list[tuple], str | None]:
    """Returns rule tuples (key, value, unit, section, quote) and an inherit-from type if the manual defers."""
    out = []
    for sec, body in _sections(text):
        flat = _clean(body)
        sec_id = sec.split(" ")[0].rstrip(".") if sec[:1].isdigit() else sec

        def add(key, m, unit, scope_text=flat):
            s = max(0, m.start() - 60)
            out.append((key, _num(m.group(1)), unit, sec, scope_text[s:m.end() + 80].strip()))

        m = re.search(r"at least (\d+(?:\.\d+)?)\s*°C\s*(?:above|over)\s*ambient", flat, re.I)
        if m:
            add("producing_delta_c", m, "°C")
        m = re.search(r"at or below (\d+(?:\.\d+)?)\s*°C", flat, re.I)
        if m:
            add("temp_alarm_c", m, "°C")
        m = re.search(r"more than (\d+(?:\.\d+)?)\s*% of the pad", flat, re.I)
        if m:
            add("spill_shutin_pad_pct", m, "%")
        m = re.search(r"(\w+) or more\s+corrective (?:maintenance )?events", flat, re.I) or \
            re.search(r"RCA after (\w+) corrective", flat, re.I)
        if m and (m.group(1).lower() in WORDS or m.group(1).isdigit()):
            add("rca_corrective_count", m, "events")
            m2 = re.search(r"(\d+) months", flat)
            if m2:
                add("rca_window_months", m2, "months")
        m = re.search(r"more than (\d+) consecutive days", flat, re.I)
        if m:
            add("downtime_report_days", m, "days")
    inherit = None
    m = re.search(r"Same as (T\d+\w*)", _clean(text))
    if m:
        inherit = m.group(1)
    return out, inherit


def parse_sop(doc_id: str, text: str):
    out = []
    for line in text.splitlines():
        m = re.match(r"\|\s*\*\*([A-Z]{2}-\d{2})\*\*\s*\|(.+)\|?\s*$", line)
        if m:
            pid, flat = m.group(1), _clean(m.group(2))
            out.append((f"{pid}.text", None, "", pid, flat))
            hrs = re.findall(r"within (\d+(?:\.\d+)?) hours?", flat, re.I)
            if hrs:
                out.append((f"{pid}.deadline_hours", float(hrs[0]), "hours", pid, flat))
                if len(hrs) > 1:
                    out.append((f"{pid}.major_deadline_hours", float(hrs[1]), "hours", pid, flat))
            for pat, key, unit in (
                (r"within (\d+) days", "deadline_days", "days"),
                (r"every (\d+) days", "interval_days", "days"),
                (r"once per calendar year", "interval_years", "years"),
                (r"at least (\d+) soil samples", "min_samples", "samples"),
                (r"(\d+(?:\.\d+)?)% TPH or less", "tph_target_pct", "%"),
                (r"more than (\d+) consecutive days", "consecutive_days", "days"),
            ):
                mm = re.search(pat, flat, re.I)
                if mm:
                    val = float(mm.group(1)) if mm.groups() else 1.0
                    out.append((f"{pid}.{key}", val, unit, pid, flat))
            continue
        m = re.match(r"\|\s*(Minor|Moderate|Reportable|Major)\s*\|\s*([^|]+)\|", line)
        if m:
            cls, vol = m.group(1).lower(), _clean(m.group(2))
            lo = re.search(r"(\d+(?:\.\d+)?)\s*bbl", vol)
            if cls == "minor":
                lo_v = 0.0
            else:
                lo_v = float(lo.group(1)) if lo else None
            if lo_v is not None:
                out.append((f"spill_class.{cls}.min_bbl", lo_v, "bbl", "3. Spill classes", line.strip()))
    return out


def build():
    with db.session() as con:
        con.execute("DELETE FROM rules")
        inherit = {}
        for d in con.execute("SELECT doc_id, kind, text FROM docs WHERE kind IN ('manual','sop')").fetchall():
            if d["kind"] == "manual":
                rules, inh = parse_manual(d["doc_id"], d["text"])
                if inh and inh != d["doc_id"]:
                    inherit[d["doc_id"]] = inh
                for key, val, unit, sec, quote in rules:
                    con.execute("INSERT OR REPLACE INTO rules VALUES (?,?,?,?,?,?,?,?)",
                                (d["doc_id"], key, val, unit, d["doc_id"], sec, quote, None))
            else:
                for key, val, unit, sec, quote in parse_sop(d["doc_id"], d["text"]):
                    con.execute("INSERT OR REPLACE INTO rules VALUES (?,?,?,?,?,?,?,?)",
                                ("fleet", key, val, unit, d["doc_id"], sec, quote, None))
        # a manual that says "Same as T200 section 10" inherits missing keys from that type (marked via=)
        for typ, src in inherit.items():
            for r in con.execute("SELECT * FROM rules WHERE scope=?", (src,)).fetchall():
                if not con.execute("SELECT 1 FROM rules WHERE scope=? AND key=?", (typ, r["key"])).fetchone():
                    con.execute("INSERT INTO rules VALUES (?,?,?,?,?,?,?,?)",
                                (typ, r["key"], r["value"], r["unit"], r["doc_id"], r["section"], r["quote"], src))


def get(con, well_type: str | None, key: str):
    """Rule row for a well type, falling back to fleet scope."""
    for scope in (well_type, "fleet"):
        if scope:
            r = con.execute("SELECT * FROM rules WHERE scope=? AND key=?", (scope, key)).fetchone()
            if r:
                return r
    return None
