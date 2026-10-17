"""One turn of the copilot: plan -> resolve -> execute operators -> write ledger -> narrate -> visual blocks."""
from __future__ import annotations

import json
import re
import time
from datetime import date, timedelta

from . import feedback, final_agent, llm, planner
from .engine.ops import Ops, Result
from .memory import Ledger
from .narrate import summarize

FEEDBACK_HINT = re.compile(r"\b(wrong|actually|really|measured|re-?measured|correct(?:ed|ion)?|note for|from now on|now wants|"
                           r"fyi|heads up|will be shut|shut in (?:from|since)|is running|back online|running fine|has been shut|"
                           r"not oil|was water|puddle)\b", re.I)
QUESTION = re.compile(r"\?\s*$|^(is|are|was|were|which|what|how|show|list|when|who|why|did|do|does|give|find)\b", re.I)

VIZ_OK = {"table", "bar", "line", "map", "heatmap", "card"}


class Copilot:
    def __init__(self, ledger: Ledger | None = None):
        self.ledger = ledger or Ledger()

    # ------------------------------------------------------------------
    def ask(self, user_id: str, conv_id: int, question: str, use_llm: bool | None = None) -> dict:
        t0 = time.time()
        d = self.ledger.data()
        ops = Ops(d)
        self.ledger.add_message(conv_id, "user", question)
        fin = final_agent.dispatch(self, user_id, conv_id, question, d, ops)
        if fin is not None:
            p, results, reply_notes = fin
            pre = {}
        else:
            pre = planner.pre_extract(question, d)
            fb = feedback.parse_feedback(question, d)
            is_feedback = bool(fb) or (bool(FEEDBACK_HINT.search(question)) and not QUESTION.search(question.strip()))
            if fb:
                p = fb
            else:
                router = planner.fallback_plan(question, pre)
                if use_llm is None:
                    use_llm = is_feedback or not router.get("_confident", True)
                p = planner.plan(question, d, use_llm=bool(use_llm))
                if is_feedback and p.get("intent") == "query" and "_router" in p:
                    p["intent"] = "unknown_feedback"
            results, reply_notes = [], []
        intent = p.get("intent", "query")
        if fin is not None:
            pass
        elif intent == "correction" and p.get("correction"):
            c = p["correction"]
            well = (pre.get("wells") or [c.get("well")])[0]
            field = c.get("field") or "wellhead_temp_c"
            val = c.get("value")
            if field == "spill_detected":
                val = 0
            on = _date(c.get("date"))
            results.append(self.ledger.record_correction(user_id, well, field, val, c.get("reason") or question, on=on, conv_id=conv_id))
        elif intent == "rule" and p.get("rule"):
            r = p["rule"]
            results.append(self.ledger.record_rule(user_id, r.get("scope_type", "well_type"), pre.get("well_type") or r.get("scope_id"),
                                                   r.get("key", "rca_corrective_count"), r.get("value"), r.get("equipment"),
                                                   r.get("reason") or question, conv_id=conv_id))
        elif intent == "statement" and p.get("statement"):
            s = p["statement"]
            well = (pre.get("wells") or [s.get("well")])[0]
            since, until = _date(s.get("since")), _date(s.get("until"))
            if since and not until and s.get("duration_days"):
                until = since + timedelta(days=int(s["duration_days"]))
            results.append(self.ledger.record_status(user_id, well, s.get("producing"), since, until, question,
                                                     shared=s.get("shared", True), conv_id=conv_id))
        elif intent == "unknown_feedback":
            reply_notes.append("I could not tell what to record from that. Is it a correction of a reading, a rule for a well type, or a status update?")
        else:
            for step in p["steps"][:3]:
                res = self.run_step(step, p, user_id, conv_id, ops, question)
                results.append(res)
        # visual choice: user-named wins when compatible with the data shape
        for r in results:
            want = p.get("viz")
            if want in VIZ_OK and r.viz.get("type") not in ("receipt",):
                if want == "map" and r.rows and "lat" not in r.rows[0]:
                    pass
                else:
                    r.viz = {**r.viz, "type": want}
        final_agent.apply_prefs(results, self.ledger.prefs(user_id))
        full = "\n\n".join(summarize(r) for r in results)
        text = "\n\n".join(summarize(r, brief=True) for r in results)
        if reply_notes:
            full = "\n".join(reply_notes) + ("\n\n" + full if full else "")
            text = "\n".join(reply_notes) + ("\n\n" + text if text else "")
        shared = self.shared_context(results, d)
        if shared:
            extra = "\n\n**Shared knowledge from other users:**\n" + "\n".join(f"- {s}" for s in shared)
            text += extra
            full += extra
        # remember entity sets for private recall
        for r in results:
            wells = sorted({row.get("Well") or row.get("asset_id") for row in r.rows if (row.get("Well") or row.get("asset_id"))})
            if wells and r.op not in ("correction", "rule_override", "statement"):
                ordered = [w for w, _ in r.facts.get("ranking", [])] or (r.facts.get("wells") if set(r.facts.get("wells") or []) == set(wells) else None) or wells
                self.ledger.save_result_set(user_id, conv_id, question, r.op, ordered, {})
        payload = _clean({"text": text, "full_text": full, "plan": _plan_view(p), "results": [r.to_dict() for r in results],
                          "ms": int((time.time() - t0) * 1000)})
        self.ledger.add_message(conv_id, "assistant", text, payload)
        return payload

    # ------------------------------------------------------------------
    def run_step(self, s: dict, p: dict, user_id, conv_id, ops: Ops, question: str) -> Result:
        d = ops.d
        wells = s.get("wells") or []
        if p.get("previous_reference"):
            ref = p["previous_reference"]
            sets = self.ledger.recall(user_id, conv_id=conv_id, count=ref.get("count"))
            if not sets:
                name = d.name(user_id)
                return Result("recall", "No earlier conversation",
                              notes=[f"I have no earlier conversation with {name} about those wells, so I can't tell which wells you mean. "
                                     f"Other people's conversations are private. Which wells do you want?"])
            wells = sets[0]["entity_ids"]
            p["_recalled"] = {"from_question": sets[0]["question"], "session_date": sets[0]["session_date"], "wells": wells}
        start, end, label = planner.resolve_period(s.get("period"), d)
        s["_period_label"] = label
        op = s["op"]
        area, wt = s.get("area"), s.get("well_type")
        if op == "well_status":
            if not wells:
                return Result("well_status", "Which well?", notes=["Which well do you mean (e.g. WELL-0001)?"])
            return ops.well_status(wells[0]) if len(wells) == 1 else ops.wells_status(wells=wells, producing=None)
        if op == "wells_status":
            prod = s.get("producing")
            return ops.wells_status(area=area, well_type=wt, producing=False if prod is None else prod, wells=wells or None)
        if op == "series":
            w = wells[0] if wells else None
            if not w:
                return Result("series", "Which well?", notes=["Which well do you mean?"])
            m = re.search(r"(\d+)\s*weeks", question)
            weeks = int(m.group(1)) if m else (s.get("weeks") or (None if start else 13))
            return ops.series(w, weeks=weeks, start=start if not m else None)
        if op == "downtime":
            why = bool(re.search(r"\bwhy\b|reason|cause|explain", question, re.I))
            top = s.get("top") or (5 if why and not wells else None)
            r = ops.downtime(area=area, well_type=wt, wells=wells or None, start=start, end=end, top=top, why=why)
            if top and not s.get("top"):
                r.notes.append(f"Showing the top {top} wells by downtime.")
            return r
        if op == "spills":
            r = ops.spills(area=area, well_type=wt, wells=wells or None, start=start, end=end,
                           viz="map" if p.get("viz") == "map" or re.search(r"\bmap\b|where", question, re.I) else None)
            return r
        if op == "spill_heatmap":
            return ops.spill_heatmap(int(s.get("year") or d.today.year), area=None)
        if op == "repairs":
            if not wells and not area:
                return Result("repairs", "Which wells?", notes=["Which wells or area do you mean?"])
            return ops.repairs(wells=wells or None, area=area, start=start, end=end, kind=s.get("maintenance_type"), equipment=s.get("equipment"))
        if op == "rca_due":
            eq = s.get("equipment") or ("pump_jack" if re.search(r"pump jack", question, re.I) else None)
            return ops.rca_due(area=area, well_type=wt, wells=wells or None, equipment=eq)
        if op == "compliance_audit":
            if not wells:
                return Result("compliance_audit", "Which well?", notes=["Which well do you mean?"])
            return ops.compliance_audit(wells[0], start, end)
        if op == "spills_check":
            proto = s.get("protocol") or ("SR-02" if re.search(r"contain", question, re.I) else "SR-01")
            return ops.spills_check(area=area, wells=wells or None, start=start, end=end, protocol=proto)
        if op == "spill_verdict":
            on = _date(s.get("date")) or _date_from_text(question, d.today)
            if not wells or not on:
                return Result("spill_verdict", "Which spill?", notes=["Which well and date?"])
            return ops.spill_verdict(wells[0], on)
        if op == "planned_downtime":
            return self.ledger.planned_downtime(wells[0]) if wells else Result("planned_downtime", "Which well?", notes=["Which well?"])
        if op == "regulator_events":
            return ops.regulator_events(area=area, well_type=wt, wells=wells or None, start=start, end=end,
                                        event_type=s.get("event_type"), fines_only=bool(s.get("fines_only")))
        if op == "repair_list":
            return ops.repair_list(wells=wells or None, area=area, start=start, end=end, kind=s.get("maintenance_type"),
                                   equipment=s.get("equipment"), latest=s.get("top"))
        if op == "list_wells":
            r = ops.list_wells(area=area, well_type=wt, wells=wells or None)
            if p.get("viz") == "map" or re.search(r"\bmap\b|where", question, re.I):
                r.viz = {"type": "map", "lat": "lat", "lon": "lon", "label": "Well"}
                r.columns = ["Well", "Type", "Area", "lat", "lon"]
            return r
        if op == "downtime_by_area":
            return ops.downtime_by_area(start=start, end=end)
        if op == "sql":
            return self.sql_query(s.get("query") or question, d)
        return self.search_docs(s.get("query") or question)

    def sql_query(self, question: str, d) -> Result:
        """Last resort for open-ended counting/grouping: the LLM writes ONE read-only SELECT over the raw tables."""
        import sqlite3

        from .config import DB_PATH
        res = Result("sql", "Query result")
        schema = """tables: wells(asset_id, name, well_type, area_id, team_id, in_charge_user_id, lat, lon, installed_on, recorded_status),
inspections(inspection_id, asset_id, inspected_at, inspector_user_id, method, ambient_temp_c, wellhead_temp_c, spill_detected, spill_area_pct, spill_est_volume_bbl, notes),
maintenance(maintenance_id, asset_id, started_at, completed_at, maintenance_type, equipment_kind, issue, action_taken, technician_user_id, contractor, downtime_hours, cost_labor, cost_parts, cost_total, triggered_by_inspection_id),
reg_events(event_id, asset_id, date, agency, event_type, protocol_id, related_inspection_id, hours_to_report, detail, fine_usd, status),
notes(note_id, asset_id, created_at, author_user_id, note_type, inspection_id, text, valid_from, valid_to), users(user_id, name, role, team_id), areas(area_id, name, team_id)."""
        from . import db as _db
        with _db.session() as _c:
            vals = {
                "maintenance.equipment_kind": [r[0] for r in _c.execute("SELECT DISTINCT equipment_kind FROM maintenance")],
                "maintenance.maintenance_type": [r[0] for r in _c.execute("SELECT DISTINCT maintenance_type FROM maintenance")],
                "reg_events.event_type": [r[0] for r in _c.execute("SELECT DISTINCT event_type FROM reg_events")],
                "notes.note_type": [r[0] for r in _c.execute("SELECT DISTINCT note_type FROM notes")],
                "wells.well_type": [r[0] for r in _c.execute("SELECT DISTINCT well_type FROM wells")],
                "wells.area_id": [r[0] for r in _c.execute("SELECT DISTINCT area_id FROM wells")],
            }
        schema += "\nExact stored values (use these spellings): " + json.dumps(vals) + "\nDates are ISO strings like 2026-10-15T08:00:00Z; use substr(col,1,4) for the year."
        prompt = (f"SQLite schema:\n{schema}\nToday is {d.today}. Write ONE read-only SELECT answering the question. Use readable names (join users/areas). "
                  f"Output only the SQL.\nQuestion: {question}\nSQL:")
        try:
            sql = llm.complete(prompt, purpose="sql", max_tokens=1500).strip().strip("`")
            sql = re.sub(r"^sql\s*", "", sql, flags=re.I).strip().rstrip(";")
            if not re.match(r"^(select|with)\b", sql, re.I) or re.search(r"\b(insert|update|delete|drop|alter|attach|pragma|create)\b", sql, re.I):
                raise ValueError("only a single read-only SELECT is allowed")
            con = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
            cur = con.execute(f"SELECT * FROM ({sql}) LIMIT 200")
            cols = [c[0] for c in cur.description]
            res.rows = [dict(zip(cols, row)) for row in cur.fetchall()]
            res.columns = cols
            res.viz = {"type": "table"}
            res.proof.append({"step": "Exploratory read-only query written by the model; check the SQL.", "rule": {"doc": "sql", "section": "", "quote": sql}})
            res.evidence.append({"id": "SQL", "type": "doc", "label": sql[:200]})
            res.notes.append("This answer comes from an exploratory query, not a built-in operator. SQL used: " + sql)
        except Exception as e:  # noqa: BLE001
            res.notes.append(f"I could not answer that with a reliable query ({e}). Try naming a well or area.")
        return res

    def search_docs(self, q: str) -> Result:
        from . import db
        stop = {"what", "which", "does", "the", "for", "and", "with", "how", "say", "says", "are", "was", "who", "when", "that", "this",
                "from", "into", "about", "there", "their", "have", "has", "will", "can", "any", "all", "our", "your", "manual", "sop"}
        terms = [t.lower() for t in re.findall(r"[A-Za-z0-9-]{3,}", q) if t.lower() not in stop]
        syn = {"report": ["notice", "filed", "written"], "reported": ["notice", "filed"], "regulator": ["commission", "agency", "regulatory"],
               "deadline": ["within", "hours", "days", "limit"], "limit": ["within", "hours", "days"], "fine": ["violation", "penalt"],
               "contain": ["contained", "containment"], "clean": ["cleanup", "remediation", "tph"], "cleanup": ["clean", "tph", "remediation"],
               "temperature": ["warmer", "ambient", "above"], "producing": ["active", "ambient", "above"], "alarm": ["shut", "inspect"]}
        expanded = set(terms)
        for tm in terms:
            expanded.update(syn.get(tm, []))
        res = Result("search_docs", "From the manuals, SOPs and reports")
        if not terms:
            return res
        match = " OR ".join(f'"{x}"' for x in sorted(expanded))
        chunks, protos = [], []
        with db.session() as con:
            for r in con.execute("SELECT ref, kind, title, text FROM chunks WHERE chunks MATCH ? AND kind IN ('manual','sop') ORDER BY bm25(chunks) LIMIT 25", (match,)):
                chunks.append((r["ref"], r["kind"], r["title"], r["text"]))
            for r in con.execute("SELECT doc_id, key, quote FROM rules WHERE key LIKE '%.text'"):
                protos.append((f"{r['doc_id']} {r['key'][:-5]}", "sop", r["doc_id"], r["quote"]))

        def score(c):
            low = (c[0] + " " + c[3]).lower()
            return sum(1 for x in expanded if x in low) + sum(1.5 for x in set(terms) if x in low)

        ranked = sorted(chunks, key=score, reverse=True)[:3] + sorted(protos, key=score, reverse=True)[:3]
        ranked = [c for c in ranked if score(c) > 0]
        res.rows = [{"ref": c[0], "kind": c[1], "text": c[3]} for c in ranked]
        res.evidence = [{"id": c[0], "type": "doc", "label": c[2]} for c in ranked]
        if ranked:
            try:
                ctx = "\n\n".join(f"[{c[0]}]\n{c[3][:1000]}" for c in ranked)
                ans = llm.complete(f"Answer the question using only these excerpts. Quote the number and cite the [ref] you used. Be brief.\n\n{ctx}\n\nQuestion: {q}",
                                   purpose="docs", max_tokens=700)
                res.notes.insert(0, ans.strip())
                res.rows = res.rows[:2]
            except Exception as ex:  # noqa: BLE001
                res.notes.append(f"(The model was unavailable, so these are the most relevant passages: {str(ex)[:80]})")
        res.viz = {"type": "text"}
        return res

    def shared_context(self, results: list[Result], d) -> list[str]:
        """Shared facts and claims about wells in this answer, from any user, with author and status."""
        wells = set()
        for r in results:
            if r.op in ("correction", "rule_override", "statement", "planned_downtime"):
                continue
            for row in r.rows:
                w = row.get("Well") or row.get("asset_id")
                if w:
                    wells.add(w)
        out = []
        if len(wells) > 12:
            return out
        for f in self.ledger.facts():
            if f["scope_id"] in wells and f["kind"] in ("shared_fact", "claim"):
                out.append(f"{f['scope_id']}: {d.name(f['author_id'])} said \"{f['text']}\" ({f['id']}, {f['status']})")
        return out


def _date(s) -> date | None:
    try:
        return date.fromisoformat(str(s)[:10]) if s else None
    except ValueError:
        return None


def _date_from_text(q: str, today: date) -> date | None:
    m = re.search(r"(\d{1,2})\s*(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s*(20\d\d)?", q, re.I)
    if not m:
        return None
    import pandas as pd
    y = int(m.group(3)) if m.group(3) else today.year
    dd = pd.Timestamp(f"{m.group(1)} {m.group(2)} {y}").date()
    return dd if dd <= today or m.group(3) else pd.Timestamp(f"{m.group(1)} {m.group(2)} {y - 1}").date()


def _plan_view(p: dict) -> dict:
    """The 'How I read this' chips."""
    chips = []
    for s in p.get("steps", []):
        c = {"operation": s.get("op")}
        for k in ("wells", "area", "well_type", "equipment", "protocol", "top", "date"):
            if s.get(k):
                c[k] = s[k]
        if s.get("_period_label") and s["_period_label"] != "all time":
            c["period"] = s["_period_label"]
        chips.append(c)
    return {"intent": p.get("intent"), "steps": chips, "viz": p.get("viz"), "recalled": p.get("_recalled"),
            "router": "keywords" if p.get("_router") else "llm"}


def _clean(o):
    """JSON-safe: numpy scalars to python, NaN/NaT to None, dates to strings."""
    import math

    import numpy as np
    import pandas as pd
    if isinstance(o, dict):
        return {str(k): _clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple, set)):
        return [_clean(v) for v in o]
    if isinstance(o, np.generic):
        o = o.item()
    if isinstance(o, float):
        return None if math.isnan(o) or math.isinf(o) else o
    if o is pd.NaT or o is None:
        return None
    if isinstance(o, (pd.Timestamp, date)):
        return str(o)
    return o
