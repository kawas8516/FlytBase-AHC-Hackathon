"""Load one or more dataset roots (fleet/ + assets/) into SQLite. Idempotent; later roots override earlier ones by key."""
import json
import re
import sys
from pathlib import Path

from . import db
from .config import data_dirs


def _jsonl(path: Path):
    if not path.exists():
        return
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    yield json.loads(line)
                except json.JSONDecodeError:
                    continue


def _json(path: Path, default=None):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def chunk_markdown(text: str):
    """Split on markdown headings; yields (section_label, body)."""
    parts = re.split(r"(?m)^(#{1,4} .+)$", text)
    head, buf = "intro", parts[0]
    if buf.strip():
        yield head, buf.strip()
    for i in range(1, len(parts), 2):
        title = parts[i].lstrip("# ").strip()
        body = parts[i + 1].strip() if i + 1 < len(parts) else ""
        if body:
            yield title, f"{title}\n{body}"


def add_doc(con, doc_id, kind, path, title, text, asset_id=""):
    con.execute("INSERT OR REPLACE INTO docs VALUES (?,?,?,?,?)", (doc_id, kind, str(path), title, text))
    con.execute("DELETE FROM chunks WHERE ref LIKE ?", (doc_id + "#%",))
    for label, body in chunk_markdown(text):
        con.execute("INSERT INTO chunks(ref,kind,asset_id,title,text) VALUES (?,?,?,?,?)",
                    (f"{doc_id}#{label}", kind, asset_id, title, body))


def ingest_fleet(con, fleet: Path):
    areas = _json(fleet / "areas.json", {}) or {}
    for a in areas.get("areas", []):
        c = a.get("center") or {}
        con.execute("INSERT OR REPLACE INTO areas VALUES (?,?,?,?,?)",
                    (a["area_id"], a.get("name"), a.get("team_id"), c.get("lat"), c.get("lon")))
    for t in areas.get("teams", []):
        con.execute("INSERT OR REPLACE INTO teams VALUES (?,?,?)", (t["team_id"], t.get("name"), t.get("lead_user_id")))
    for u in (_json(fleet / "users.json", {}) or {}).get("users", []):
        con.execute("INSERT OR REPLACE INTO users VALUES (?,?,?,?)",
                    (u["user_id"], u.get("name"), u.get("role"), u.get("team_id")))
    for kind, sub in (("manual", "well-types"), ("sop", "sops")):
        for p in sorted((fleet / sub).glob("*.md")) if (fleet / sub).exists() else []:
            text = p.read_text(encoding="utf-8")
            m = re.match(r"#\s+(.+)", text)
            add_doc(con, p.stem, kind, p, m.group(1).strip() if m else p.stem, text)


def ingest_well(con, wdir: Path):
    meta = _json(wdir / "metadata.json")
    if not meta:
        return 0
    aid = meta["asset_id"]
    loc = meta.get("location") or {}
    last = meta.get("last_inspection") or {}
    con.execute("INSERT OR REPLACE INTO wells VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", (
        aid, meta.get("name"), meta.get("well_type"), meta.get("area_id"), meta.get("team_id"),
        meta.get("in_charge_user_id"), loc.get("lat"), loc.get("lon"), meta.get("installed_on"),
        meta.get("recorded_status"), last.get("inspection_id") if isinstance(last, dict) else last,
        json.dumps(meta.get("equipment", []))))
    n = 0
    for r in _jsonl(wdir / "inspections.jsonl"):
        con.execute("INSERT OR REPLACE INTO inspections VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", (
            r["inspection_id"], aid, r.get("inspected_at"), r.get("inspector_user_id"), r.get("method"),
            r.get("ambient_temp_c"), r.get("wellhead_temp_c"), int(bool(r.get("spill_detected"))),
            r.get("spill_area_pct"), r.get("spill_est_volume_bbl"), r.get("notes") or "",
            json.dumps(r.get("evidence_images", []))))
        n += 1
    for r in _jsonl(wdir / "maintenance.jsonl"):
        c = r.get("cost_usd") or {}
        con.execute("INSERT OR REPLACE INTO maintenance VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (
            r["maintenance_id"], aid, r.get("started_at"), r.get("completed_at"), r.get("maintenance_type"),
            r.get("equipment_kind"), r.get("issue"), r.get("action_taken"), r.get("technician_user_id"),
            r.get("contractor"), r.get("downtime_hours"), c.get("labor"), c.get("parts"), c.get("total"),
            r.get("triggered_by_inspection_id"), r.get("report_file")))
        rf = r.get("report_file")
        if rf:
            p = (wdir / rf)
            if not p.exists():
                p = wdir / "maintenance-reports" / Path(rf).name
            if p.exists():
                text = p.read_text(encoding="utf-8")
                con.execute("INSERT OR REPLACE INTO reports VALUES (?,?,?,?,NULL)",
                            (r["maintenance_id"], aid, str(p), text))
                add_doc(con, r["maintenance_id"], "report", p, f"Maintenance report {r['maintenance_id']}", text, aid)
    for r in _jsonl(wdir / "regulatory-events.jsonl"):
        con.execute("INSERT OR REPLACE INTO reg_events VALUES (?,?,?,?,?,?,?,?,?,?,?)", (
            r["event_id"], aid, r.get("date"), r.get("agency"), r.get("event_type"), r.get("protocol_id"),
            r.get("related_inspection_id"), r.get("hours_to_report"), r.get("detail"),
            r.get("fine_usd") or 0, r.get("status")))
    for r in _jsonl(wdir / "context.jsonl"):
        con.execute("INSERT OR REPLACE INTO notes VALUES (?,?,?,?,?,?,?,?,?)", (
            r["note_id"], aid, r.get("created_at"), r.get("author_user_id"), r.get("note_type"),
            r.get("inspection_id"), r.get("text"), r.get("valid_from"), r.get("valid_to")))
        con.execute("DELETE FROM chunks WHERE ref=?", (r["note_id"],))
        con.execute("INSERT INTO chunks(ref,kind,asset_id,title,text) VALUES (?,?,?,?,?)",
                    (r["note_id"], "note", aid, f"Note {r['note_id']}", r.get("text") or ""))
    return n


def ingest(roots=None, reset=True):
    roots = roots or data_dirs()
    if reset and db.DB_PATH.exists():
        db.DB_PATH.unlink()
    with db.session() as con:
        con.executescript(db.SCHEMA)
        total = 0
        for root in roots:
            if (root / "fleet").exists():
                ingest_fleet(con, root / "fleet")
            assets = root / "assets"
            for wdir in sorted(assets.iterdir()) if assets.exists() else []:
                if wdir.is_dir():
                    total += ingest_well(con, wdir)
    from . import reports, rules  # noqa: late import avoids cycle
    rules.build()
    reports.build()
    return total


if __name__ == "__main__":
    n = ingest([Path(a) for a in sys.argv[1:]] or None)
    with db.session() as con:
        for t in ("wells", "inspections", "maintenance", "reports", "reg_events", "notes", "users", "rules"):
            print(t, con.execute(f"select count(*) from {t}").fetchone()[0])
