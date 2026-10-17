"""The Ledger: append-only human knowledge (corrections, rule overrides, shared facts, claims) plus per-user
conversation memory. Lives in memory.db so re-ingesting data never wipes it."""
from __future__ import annotations

import json
import re
import sqlite3
from datetime import date, datetime, timedelta, timezone

import pandas as pd

from .config import MEMORY_DB, TODAY
from .engine.ops import Ops, Result, fmt_day
from .engine.views import Data, Overlays

SCHEMA = """
CREATE TABLE IF NOT EXISTS facts(
  id TEXT PRIMARY KEY, kind TEXT, scope_type TEXT, scope_id TEXT, target TEXT, field TEXT, key TEXT,
  equipment_kind TEXT, original TEXT, value TEXT, valid_from TEXT, valid_to TEXT, author_id TEXT,
  reason TEXT, text TEXT, status TEXT, created_at TEXT, conv_id TEXT);
CREATE TABLE IF NOT EXISTS conversations(id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, session_date TEXT, created_at TEXT, title TEXT);
CREATE TABLE IF NOT EXISTS messages(id INTEGER PRIMARY KEY AUTOINCREMENT, conv_id INTEGER, role TEXT, content TEXT, payload TEXT, created_at TEXT);
CREATE TABLE IF NOT EXISTS result_sets(id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, conv_id INTEGER, session_date TEXT,
  question TEXT, op TEXT, entity_ids TEXT, params TEXT, created_at TEXT);
"""

NOT_RUNNING = re.compile(r"not moving|no stroke|not running|stopped|seized|not turning", re.I)


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class Ledger:
    def __init__(self, path=MEMORY_DB):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.con = sqlite3.connect(path, check_same_thread=False)
        self.con.row_factory = sqlite3.Row
        self.con.executescript(SCHEMA)
        self.version = self._count()
        self._data: Data | None = None
        self._data_version = -1

    def _count(self):
        return self.con.execute("SELECT count(*) FROM facts").fetchone()[0]

    def reset(self):
        for t in ("facts", "conversations", "messages", "result_sets"):
            self.con.execute(f"DELETE FROM {t}")
        self.con.commit()
        self.version += 1

    # ------------------------------------------------------------------ data with overlays applied
    def data(self, today: date = TODAY) -> Data:
        if self._data is None or self._data_version != self.version or self._data.today != today:
            from . import db
            with db.session() as con:
                names = dict(con.execute("SELECT user_id, name FROM users").fetchall())
            self._data = Data(self.overlays(names), today)
            self._data_version = self.version
        return self._data

    def ops(self, today: date = TODAY) -> Ops:
        return Ops(self.data(today))

    def facts(self, kind=None, scope_id=None):
        q, a = "SELECT * FROM facts WHERE 1=1", []
        if kind:
            q += " AND kind=?"; a.append(kind)
        if scope_id:
            q += " AND scope_id=?"; a.append(scope_id)
        return [dict(r) for r in self.con.execute(q + " ORDER BY created_at, id", a)]

    def overlays(self, names=None) -> Overlays:
        names = names or {}
        ov = Overlays()
        for f in self.facts():
            f["author_name"] = names.get(f["author_id"], f["author_id"])
            if f["kind"] in ("data_correction", "analysis_correction"):
                ov.data_corrections.append({**f, "original": _num(f["original"]), "value": _num(f["value"])})
            elif f["kind"] == "rule_override":
                ov.rule_overrides.append({**f, "value": float(f["value"])})
            else:
                ov.well_facts.append(f)
        return ov

    def _add(self, **kw) -> str:
        fid = f"LDG-{self._count() + 1:04d}"
        cols = ["id", "kind", "scope_type", "scope_id", "target", "field", "key", "equipment_kind", "original", "value",
                "valid_from", "valid_to", "author_id", "reason", "text", "status", "created_at", "conv_id"]
        kw.update(id=fid, created_at=kw.get("created_at") or _now())
        self.con.execute(f"INSERT INTO facts({','.join(cols)}) VALUES ({','.join('?' * len(cols))})",
                         [None if kw.get(c) is None else str(kw.get(c)) for c in cols])
        self.con.commit()
        self.version += 1
        return fid

    # ------------------------------------------------------------------ writes (slots already extracted; code resolves records)
    def resolve_inspection(self, well: str, on: date | None, inspection_id: str | None = None, field=None) -> pd.Series | None:
        d = self.data()
        x = d.ins[d.ins.asset_id == well]
        if inspection_id:
            x = x[x.inspection_id == inspection_id]
        elif on:
            x = x[(pd.to_datetime(x.day) - pd.Timestamp(on)).abs() <= pd.Timedelta(days=3)]
            if field == "spill_est_volume_bbl":
                x = x[x.spill_detected == 1] if (x.spill_detected == 1).any() else x
            x = x.iloc[(pd.to_datetime(x.day) - pd.Timestamp(on)).abs().argsort()] if len(x) else x
        else:
            x = x.tail(1)
        return None if x.empty else x.iloc[0]

    def record_correction(self, user_id, well, field, value, reason, on: date | None = None, inspection_id=None, conv_id=None) -> Result:
        """Correct a raw reading (wellhead/ambient temp) or the AI's analysis (spill volume / detection)."""
        row = self.resolve_inspection(well, on, inspection_id, field)
        d = self.data()
        if row is None:
            return Result("correction", "Correction not recorded", notes=[f"I could not find an inspection of {well} on {fmt_day(on) if on else 'that date'}. Which inspection do you mean?"])
        orig_col = {"wellhead_temp_c": "orig_wellhead_temp_c", "ambient_temp_c": "orig_ambient_temp_c",
                    "spill_est_volume_bbl": "orig_volume_bbl"}.get(field, field)
        original = row[orig_col] if orig_col in row else None
        kind = "analysis_correction" if field.startswith("spill") else "data_correction"
        fid = self._add(kind=kind, scope_type="well", scope_id=well, target=row.inspection_id, field=field,
                        original=original, value=value, author_id=user_id, reason=reason, status="applied", conv_id=conv_id)
        ops = self.ops()
        res = Result("correction", f"Correction recorded against {row.inspection_id}")
        res.evidence = [{"id": row.inspection_id, "type": "inspection", "label": ""}, {"id": fid, "type": "ledger", "label": "correction"}]
        res.rows = [{"Ledger id": fid, "Inspection": row.inspection_id, "Field": field, "Original (kept)": original,
                     "Corrected to": value, "By": d.name(user_id), "Reason": reason, "Scope": f"well {well} only"}]
        res.columns = list(res.rows[0])
        res.viz = {"type": "receipt"}
        new = ops.d.ins[ops.d.ins.inspection_id == row.inspection_id].iloc[0]
        if field in ("wellhead_temp_c", "ambient_temp_c"):
            res.facts = {"delta_c": round(float(new.delta_c), 1), "threshold_c": new.threshold_c, "producing": bool(new.producing),
                         "wellhead": float(new.wellhead_temp_c), "ambient": float(new.ambient_temp_c)}
            ops._rule_proof(res, new.well_type, "producing_delta_c", f"{new.well_type} producing limit")
            res.notes.append(f"With {new.wellhead_temp_c:g} °C against {new.ambient_temp_c:g} °C air ({new.delta_c:.1f} °C warmer, "
                             f"{'above' if new.producing else 'below'} the {new.well_type} limit of {new.threshold_c:g} °C), "
                             f"{well} is {'producing' if new.producing else 'not producing'} oil.")
            if new.producing and NOT_RUNNING.search(new.notes or ""):
                res.conflicts.append({"kind": "correction_vs_note", "target": row.inspection_id,
                                      "a": f"{d.name(user_id)}: wellhead {value} °C (producing)",
                                      "b": f"Same inspection, {d.name(row.inspector_user_id)} noted: \"{new.notes}\"",
                                      "ask": f"{d.name(user_id)}, please confirm: the inspector's note disagrees with the corrected reading."})
        if field == "spill_est_volume_bbl":
            res.facts = {"class": ops.d.spill_class(float(value)), "volume": float(value)}
            for c in ops.spill_compliance(new):
                if c["status"] in ("breach", "pending", "stale"):
                    res.notes.append(f"{c['protocol']}: {c['detail']}" + "")
                    for ref in c["refs"]:
                        res.evidence.append({"id": ref, "type": "maintenance" if ref.startswith("MNT") else "regulatory", "label": ""})
            for p in ("SR-01", "SR-03"):
                r = ops.d.rule(None, f"{p}.text")
                if r:
                    res.evidence.append({"id": f"{r['doc_id']} {p}", "type": "doc", "label": r["quote"][:140]})
        return res

    def record_rule(self, user_id, scope_type, scope_id, key, value, equipment_kind=None, reason="", conv_id=None) -> Result:
        d = self.data()
        base = d.rule_value(scope_id if scope_type == "well_type" else d.well(scope_id).get("well_type"), key)
        fid = self._add(kind="rule_override", scope_type=scope_type, scope_id=scope_id, key=key, equipment_kind=equipment_kind,
                        original=base, value=value, author_id=user_id, reason=reason, status="applied", conv_id=conv_id)
        res = Result("rule_override", "Rule recorded")
        res.rows = [{"Ledger id": fid, "Applies to": f"all {scope_id} wells" if scope_type == "well_type" else scope_id,
                     "Rule": key + (f" ({equipment_kind.replace('_', ' ')})" if equipment_kind else ""),
                     "Manual value": base, "New value": value, "By": d.name(user_id)}]
        res.columns = list(res.rows[0])
        res.viz = {"type": "receipt"}
        res.evidence = [{"id": fid, "type": "ledger", "label": "rule override"}]
        res.notes.append(f"Applies only to {scope_id}" + (" wells; other types keep the manual value." if scope_type == "well_type" else "."))
        return res

    def record_status(self, user_id, well, producing: bool | None, since: date | None, until: date | None, text: str,
                      shared=True, conv_id=None) -> Result:
        """A person states something about a well's state. Check it against the data before accepting it."""
        d = self.data()
        ops = Ops(d)
        res = Result("statement", f"Statement about {well}")
        x = d.ins[(d.ins.asset_id == well) & (d.ins.day <= d.today)]
        if since:
            x = x[x.day >= since]
        verdict, detail = "unverifiable", "No inspection since then to check against."
        if producing is not None and not x.empty:
            last = x.iloc[-1]
            res.evidence.append({"id": last.inspection_id, "type": "inspection", "label": ""})
            ok = bool(last.producing) == producing
            verdict = "corroborated" if ok else "contradicted"
            detail = (f"The {fmt_day(last.day)} inspection (by {d.name(last.inspector_user_id)}) shows the wellhead "
                      f"{last.delta_c:.1f} °C above the air, so the well is {'producing' if last.producing else 'not producing'} oil.")
        # other people's statements and notes about this well, each with the state it implies
        others = []
        for f in self.facts(scope_id=well):
            if f["kind"] in ("shared_fact", "claim") and f.get("value") not in (None, "None"):
                others.append((f["value"] == "True", f"{d.name(f['author_id'])}: \"{f['text']}\" ({f['id']}, {f['status']})"))
        data_state = bool(x.iloc[-1].producing) if not x.empty else None
        if data_state is False:
            for t, i in ops.explain_down(well, x.iloc[-1])["refs"]:
                if t == "note":
                    n = d.notes[d.notes.note_id == i].iloc[0]
                    others.append((False, f"note {i} by {d.name(n.author_user_id)}: \"{n.text}\""))
                    res.evidence.append({"id": i, "type": "note", "label": ""})
                    if producing is True and n.valid_to:
                        others.append((False, f"note {i} expects a return around {fmt_day(n.valid_to)}"))
        agrees = [s for v, s in others if data_state is not None and v == data_state]
        disagrees = [s for v, s in others if producing is not None and v != producing and s not in agrees]
        status = "unconfirmed" if verdict == "contradicted" else ("corroborated" if verdict == "corroborated" else "reported")
        kind = "shared_fact" if verdict != "contradicted" and shared else "claim"
        fid = self._add(kind=kind, scope_type="well", scope_id=well, field="producing", value=producing,
                        valid_from=since.isoformat() if since else None, valid_to=until.isoformat() if until else None,
                        author_id=user_id, text=text, status=status, conv_id=conv_id)
        res.evidence.append({"id": fid, "type": "ledger", "label": status})
        res.rows = [{"Ledger id": fid, "Well": well, "Statement": text, "By": d.name(user_id), "Status": status,
                     "Check": detail, "Visible to": "everyone" if shared else "you"}]
        res.columns = list(res.rows[0])
        res.viz = {"type": "receipt"}
        res.facts = {"verdict": verdict, "status": status}
        if verdict == "contradicted":
            res.conflicts.append({"kind": "claim_vs_data", "target": well, "a": f"{d.name(user_id)}: \"{text}\"", "b": detail,
                                  "agrees_with_data": agrees, "also_disagrees": disagrees,
                                  "ask": f"{d.name(user_id)}, can you confirm? Your statement is kept on record as unconfirmed."})
        elif disagrees:
            res.conflicts.append({"kind": "people_disagree", "target": well, "a": f"{d.name(user_id)}: \"{text}\"",
                                  "b": "; ".join(disagrees), "ask": "Both statements are kept; please confirm which is right."})
        return res

    def planned_downtime(self, well) -> Result:
        d = self.data()
        res = Result("planned_downtime", f"Planned downtime for {well}")
        for f in self.facts(scope_id=well):
            if f["kind"] in ("shared_fact", "claim") and f["value"] == "False" and (not f["valid_to"] or f["valid_to"] >= d.today.isoformat()):
                res.rows.append({"From": fmt_day(f["valid_from"]) if f["valid_from"] else "", "Until": fmt_day(f["valid_to"]) if f["valid_to"] else "",
                                 "What": f["text"], "Source": f"{d.name(f['author_id'])} ({f['id']}, {f['status']})"})
                res.evidence.append({"id": f["id"], "type": "ledger", "label": d.name(f["author_id"])})
        ops = Ops(d)
        for _, n in d.notes[(d.notes.asset_id == well) & (d.notes.note_type != "correction")].iterrows():
            if n.valid_to and n.valid_to >= d.today.isoformat() and re.search(r"shut|planned|workover|down", n.text, re.I):
                res.rows.append({"From": fmt_day(n.valid_from), "Until": fmt_day(n.valid_to), "What": n.text, "Source": f"note {n.note_id} by {d.name(n.author_user_id)}"})
                res.evidence.append({"id": n.note_id, "type": "note", "label": ""})
        for _, m in d.mnt[(d.mnt.asset_id == well) & (d.mnt.started_at_dt.dt.date >= d.today) & (d.mnt.maintenance_type == "scheduled")].iterrows():
            res.rows.append({"From": fmt_day(m.started_at_dt), "Until": fmt_day(m.completed_at_dt), "What": m.issue, "Source": m.maintenance_id})
            res.evidence.append({"id": m.maintenance_id, "type": "maintenance", "label": ""})
        res.columns = ["From", "Until", "What", "Source"]
        res.viz = {"type": "table"}
        res.facts = {"count": len(res.rows)}
        if not res.rows:
            res.notes.append(f"No planned downtime is recorded for {well}.")
        return res

    # ------------------------------------------------------------------ private conversation memory
    def new_conversation(self, user_id, session_date: date | None = None, title="") -> int:
        cur = self.con.execute("INSERT INTO conversations(user_id, session_date, created_at, title) VALUES (?,?,?,?)",
                               (user_id, (session_date or TODAY).isoformat(), _now(), title))
        self.con.commit()
        return cur.lastrowid

    def conversation(self, conv_id):
        r = self.con.execute("SELECT * FROM conversations WHERE id=?", (conv_id,)).fetchone()
        return dict(r) if r else None

    def add_message(self, conv_id, role, content, payload=None):
        self.con.execute("INSERT INTO messages(conv_id, role, content, payload, created_at) VALUES (?,?,?,?,?)",
                         (conv_id, role, content, json.dumps(payload) if payload else None, _now()))
        self.con.commit()

    def messages(self, conv_id, user_id):
        """Messages of a conversation, only if it belongs to user_id (isolation enforced here, not in the prompt)."""
        return [dict(r) for r in self.con.execute(
            "SELECT m.* FROM messages m JOIN conversations c ON c.id=m.conv_id WHERE m.conv_id=? AND c.user_id=? ORDER BY m.id",
            (conv_id, user_id))]

    def save_result_set(self, user_id, conv_id, question, op, entity_ids, params):
        c = self.conversation(conv_id)
        self.con.execute("INSERT INTO result_sets(user_id, conv_id, session_date, question, op, entity_ids, params, created_at) VALUES (?,?,?,?,?,?,?,?)",
                         (user_id, conv_id, c["session_date"] if c else TODAY.isoformat(), question, op, json.dumps(entity_ids),
                          json.dumps(params, default=str), _now()))
        self.con.commit()

    def recall(self, user_id, conv_id=None, before: date | None = None, count: int | None = None) -> list[dict]:
        """Earlier result sets of THIS user only (other conversations). Newest first; optional size match ('the three wells')."""
        q = "SELECT * FROM result_sets WHERE user_id=?"
        a = [user_id]
        if conv_id:
            q += " AND conv_id != ?"; a.append(conv_id)
        if before:
            q += " AND session_date <= ?"; a.append(before.isoformat())
        rows = [dict(r) for r in self.con.execute(q + " ORDER BY session_date DESC, id DESC", a)]
        for r in rows:
            r["entity_ids"] = json.loads(r["entity_ids"])
        if count:
            rows = [r for r in rows if len(r["entity_ids"]) == count]
        return rows

    def conversations(self, user_id):
        return [dict(r) for r in self.con.execute("SELECT * FROM conversations WHERE user_id=? ORDER BY id DESC", (user_id,))]


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return v
