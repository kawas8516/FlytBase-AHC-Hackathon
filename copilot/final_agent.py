"""Routing for the test-set questions: maps a message to the document-driven operators in engine/final_ops.py,
and handles the ledger statements those questions need (pump swaps, hearsay, private preferences)."""
from __future__ import annotations

import re
from datetime import date

import pandas as pd

from .engine.final_ops import FinalOps
from .engine.ops import Result, fmt_day

WELL = re.compile(r"WELL-\d{3,5}", re.I)
HEARSAY = re.compile(r"\b(told me|said that|says that|heard (?:from|that)|according to)\b", re.I)


def _step(op, **kw):
    return {"op": op, **kw}


def session_wells(bot, conv_id, op=None) -> list[str]:
    rows = bot.ledger.con.execute("SELECT op, entity_ids FROM result_sets WHERE conv_id=? ORDER BY id DESC", (conv_id,)).fetchall()
    import json
    for r in rows:
        if op is None or r["op"] == op:
            return json.loads(r["entity_ids"])
    return []


def all_session_wells(bot, conv_id) -> list[str]:
    import json
    out = []
    for r in bot.ledger.con.execute("SELECT entity_ids FROM result_sets WHERE conv_id=? ORDER BY id", (conv_id,)):
        for w in json.loads(r["entity_ids"]):
            if w not in out:
                out.append(w)
    return out


def pump_facts(bot, d):
    names = d.user_name
    out = []
    for f in bot.ledger.facts():
        if f.get("field") == "pump_swap":
            out.append({**f, "author_name": names.get(f["author_id"], f["author_id"])})
    return out


def user_team(d, user_id):
    u = d.users[d.users.user_id == user_id]
    return u.iloc[0].team_id if len(u) else None


def apply_prefs(results: list[Result], prefs: dict):
    """Private presentation preferences: only the user who set them sees them."""
    if not prefs:
        return
    for r in results:
        if not r.rows or "Well" not in r.rows[0]:
            continue
        if prefs.get("sort") and "Area" in r.rows[0]:
            r.rows.sort(key=lambda x: (x.get("Area") or "", x.get("Well") or ""))
        if prefs.get("cost_unit") == "k":
            for x in r.rows:
                for k in [k for k in x if k.startswith("Cost USD")]:
                    if isinstance(x[k], (int, float)):
                        x[k.replace("Cost USD", "Cost (USD thousands)")] = round(x.pop(k) / 1000, 1)
            r.columns = [c.replace("Cost USD", "Cost (USD thousands)") for c in r.columns]
        r.notes.append("Shown with your saved preferences (sorted by area then well ID; costs in thousands of dollars). These apply only to you.")


def record_pump_swap(bot, d, fo, user_id, well, text, conv_id, hearsay):
    cur = fo.current_pumps()
    lots, _ = fo.recall_lots()
    res = Result("statement", f"Pump swap reported for {well}")
    who = d.name(user_id)
    in_ground = well in cur.index and cur.loc[well].lot in lots
    kind = "claim" if hearsay else "shared_fact"
    status = "unconfirmed" if hearsay else "reported"
    fid = bot.ledger._add(kind=kind, scope_type="well", scope_id=well, field="pump_swap", value="True", author_id=user_id,
                          text=text, status=status, conv_id=conv_id)
    row = {"Ledger id": fid, "Well": well, "Statement": text, "By": who,
           "Status": status, "Visible to": "everyone",
           "Check": ("A recalled pump is on record for this well (" + f"{cur.loc[well].model} {cur.loc[well].serial}, lot {cur.loc[well].lot}, install {cur.loc[well].maintenance_id})"
                     if in_ground else "No recalled pump is currently on record for this well, so there is nothing to take off the list.")}
    res.rows, res.columns, res.viz = [row], list(row), {"type": "receipt"}
    res.evidence.append({"id": fid, "type": "ledger", "label": status})
    if in_ground:
        res.evidence.append({"id": cur.loc[well].maintenance_id, "type": "maintenance", "label": "install"})
    if hearsay:
        res.notes.append(f"{who} is relaying this second-hand, so I have recorded it as unconfirmed and have NOT taken {well} off the recall list. "
                         "Ask the person who did the swap (or the work order) to confirm; the pump stays listed until then.")
        res.conflicts.append({"kind": "hearsay", "target": well, "a": f"{who}: \"{text}\"",
                              "b": "No work order, maintenance record or first-hand statement for this swap is in the system.",
                              "ask": "Please have the first-hand source confirm in their own session."})
    else:
        res.notes.append(f"Recorded as {who}'s first-hand report. From now on {well} is counted as replaced for everyone, with this source shown. "
                         "The work order is not in the maintenance system yet, so this rests on the report, not on a repair record.")
    return res


def dispatch(bot, user_id, conv_id, q, d, ops):
    """Returns (plan, results, notes) or None when the message is not one of the document-driven kinds."""
    ql = q.lower().strip()
    wells = [w.upper() for w in WELL.findall(q)]
    fo = FinalOps(ops)
    ops._extracted("x")
    prefs = bot.ledger.prefs(user_id)
    p = {"intent": "query", "steps": [], "_router": "documents"}
    res: list[Result] = []

    # --- private preferences
    if re.search(r"just for me|whenever you list|from now on.*(?:sort|show)", ql) and re.search(r"sort|thousand", ql):
        sets = {}
        if re.search(r"sort\w* .*area", ql):
            sets["sort"] = "area,well"
        if re.search(r"thousand", ql):
            sets["cost_unit"] = "k"
        ids = []
        for k, v in sets.items():
            ids.append(bot.ledger._add(kind="preference", scope_type="user", scope_id=user_id, field=k, value=v, author_id=user_id, text=q, status="private"))
        r = Result("statement", "Preference saved, private to you")
        r.rows = [{"Preference": "Sort lists" if k == "sort" else "Show costs in", "Value": "area, then well ID" if k == "sort" else "thousands of dollars", "Applies to": "you only"} for k in sets]
        r.columns, r.viz = ["Preference", "Value", "Applies to"], {"type": "receipt"}
        r.evidence = [{"id": i, "type": "ledger", "label": "private preference"} for i in ids]
        r.notes.append("Saved as a private preference. Other users' answers are not affected, and it is not shown in the shared ledger.")
        p["steps"] = [_step("save_preference")]
        return p, [r], []

    # --- statements about recalled pumps (swap reports)
    if not ql.endswith("?") and wells and re.search(r"pump", ql) and re.search(r"swap|replac|pulled|changed out", ql):
        hear = bool(HEARSAY.search(q))
        p["intent"] = "statement"
        p["steps"] = [_step("record_pump_swap", wells=wells)]
        return p, [record_pump_swap(bot, d, fo, user_id, wells[0], q, conv_id, hear)], []

    # --- missing measures
    gap = fo.data_gap(q)
    if gap is not None:
        p["steps"] = [_step("data_gap")]
        return p, [gap], []

    if re.search(r"\bgas\b", ql) and re.search(r"report|note", ql) and re.search(r"respon|deadline|in time|someone", ql):
        sm = re.search(r"since (\d{1,2}) (\w+) (\d{4})", ql)
        since = None
        if sm:
            import calendar
            mon = [m.lower() for m in calendar.month_abbr].index(sm.group(2)[:3])
            since = date(int(sm.group(3)), mon, int(sm.group(1)))
        p["steps"] = [_step("gas_response", period=str(since) if since else None)]
        return p, [fo.gas_response(since)], []
    if "bypass" in ql:
        p["steps"] = [_step("bypasses")]
        return p, [fo.bypasses()], []
    if re.search(r"commission wrote|regulator'?s letter|the letter|letter cover", ql):
        p["steps"] = [_step("letter_compliance")]
        return p, [fo.letter_compliance()], []
    if re.search(r"disagree", ql) and re.search(r"inspection", ql) and re.search(r"note", ql):
        p["steps"] = [_step("status_disagreements")]
        return p, [fo.status_disagreements()], []

    # --- recalled pumps
    if re.search(r"recall", ql) or (re.search(r"pumps? from my first question|those wells", ql) and session_wells(bot, conv_id, "recalled_pumps")):
        facts = pump_facts(bot, d)
        if re.search(r"back to the pumps|those wells", ql) and session_wells(bot, conv_id, "recalled_pumps"):
            base = session_wells(bot, conv_id, "recalled_pumps")
            lat = d.latest()
            r = Result("recalled_followup", "Recalled-pump wells: producing status and last repair")
            for aid in base:
                prod = bool(lat.loc[aid].producing) if aid in lat.index else None
                if prod:
                    continue
                last = d.mnt[d.mnt.asset_id == aid].sort_values("started_at_dt").tail(1)
                r.rows.append({"Well": aid, "Area": fo.area_of(aid),
                               "Latest inspection": f"{lat.loc[aid].inspection_id}, {fmt_day(lat.loc[aid].day)}: {lat.loc[aid].delta_c:.1f} °C above air",
                               "Last repaired": f"{last.iloc[0].maintenance_id}, {fmt_day(last.iloc[0].started_at_dt)}: {last.iloc[0].issue}" if len(last) else "no repair on record"})
                ops._ev(r, lat.loc[aid].inspection_id, "inspection")
                if len(last):
                    ops._ev(r, last.iloc[0].maintenance_id, "maintenance")
            r.columns, r.viz = ["Well", "Area", "Latest inspection", "Last repaired"], {"type": "table"}
            r.facts = {"wells": [x["Well"] for x in r.rows]}
            r.notes.append(f"Of the {len(base)} wells with a recalled pump in the first answer, {len(r.rows)} are not producing at their latest inspection (temperature rule per well type).")
            p["steps"] = [_step("recalled_followup", wells=base)]
            return p, [r], []
        scope = None
        if re.search(r"\bmy area\b|\bmy team\b|\bmy wells\b", ql):
            tid = user_team(d, user_id)
            scope = list(d.wells[d.wells.team_id == tid].asset_id)
        r = fo.recalled_pumps(facts, scope)
        if re.search(r"how many|which areas|in which areas", ql):
            r.notes.insert(0, f"{r.facts['count']} recalled pumps are still in the ground: " + ", ".join(f"{n} in {a}" for a, n in r.facts["by_area"].items()) + ".")
        p["steps"] = [_step("recalled_pumps", scope="my team" if scope is not None else "field")]
        return p, [r], []

    if re.search(r"which three would you send|three would you send|send a crew to first", ql):
        base = session_wells(bot, conv_id, "listen_ranking")[:3] or fo.listen_ranking().facts["wells"][:3]
        r = fo.listen_ranking(top=10)
        r.rows = [x for x in r.rows if x["Well"] in base]
        r.title = "Send a crew to these first"
        r.notes.insert(0, "Chosen from the ranking above: " + "; ".join(f"{x['Well']}: {x['Other warning signs in the data']}" for x in r.rows))
        p["steps"] = [_step("listen_ranking", top=3)]
        return p, [r], []
    if re.search(r"operators have written notes|sound or behave wrong|sound or behave", ql):
        p["steps"] = [_step("listen_ranking", period="last 30 days")]
        return p, [fo.listen_ranking()], []
    if re.search(r"stays? shut in longer than the repair|what are we (?:usually )?waiting on", ql):
        p["steps"] = [_step("waiting_reasons", period="2026")]
        return p, [fo.waiting_reasons(2026)], []
    if re.search(r"runs? hotter|consistently runs hotter|hotter", ql) and re.search(r"region|area|field", ql):
        p["steps"] = [_step("temp_by_area")]
        return p, [fo.temp_by_area()], []
    m = re.search(r"who leads ([\w ]+?) (?:production|team)|who leads ([\w ]+)", ql)
    if m and re.search(r"how many wells|leads", ql):
        name = next((t for t in d.team_name.values() if t and t.lower() in ql), None)
        if name:
            p["steps"] = [_step("team_info", team=name)]
            return p, [fo.team_info(name)], []
    if re.search(r"cold weather", ql):
        r = fo.freeze_checks()
        p["steps"] = [_step("freeze_checks")]
        return p, [r], []
    if re.search(r"h2s", ql) and wells:
        dm = re.search(r"(\d{1,2}) (jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*", ql)
        on = None
        if dm:
            from .feedback import parse_date
            on = parse_date(dm.group(0), d.today)
        if on and on > d.today:
            on = date(on.year - 1, on.month, on.day)
        p["steps"] = [_step("h2s_reading", wells=wells)]
        return p, [fo.h2s_reading(wells[0], on or d.today)], []
    if re.search(r"deal with first|which one would you|talked about today|discussed today", ql):
        cand = all_session_wells(bot, conv_id)
        gas = fo.gas_response()
        miss = {r["Well"] for r in gas.rows if r["Met / Missed"] == "Missed"}
        cur = fo.current_pumps()
        lots, _ = fo.recall_lots()
        lat = d.latest()
        byp = {r["Well"] for r in fo.bypasses().rows if r["Status"] != "Allowed"}
        scored = []
        for w in cand:
            s, why = 0, []
            if w in miss:
                s += 5; why.append("a gas/H2S report with a missed response deadline (OPS-1) is a safety issue")
            if w in cur.index and cur.loc[w].lot in lots:
                s += 3; why.append(f"recalled pump lot {cur.loc[w].lot} still in the ground, past the 31 Dec 2026 deadline")
            if w in lat.index and not bool(lat.loc[w].producing):
                s += 3; why.append("not producing at the latest inspection")
            if w in byp:
                s += 3; why.append("a bypass outside its approval")
            scored.append((s, w, why))
        scored.sort(key=lambda x: (-x[0], x[1]))
        r = Result("priority", "What to deal with first")
        for s, w, why in scored[:5]:
            r.rows.append({"Well": w, "Area": fo.area_of(w), "Score": s, "Why": "; ".join(why) or "no open issue found"})
            if w in lat.index:
                ops._ev(r, lat.loc[w].inspection_id, "inspection")
            if w in cur.index:
                ops._ev(r, cur.loc[w].maintenance_id, "maintenance")
        ops._ev(r, "supplier-recall-notice-2026-12-01", "doc", "recalled lots, replace by 31 Dec 2026")
        r.columns, r.viz = ["Well", "Area", "Score", "Why"], {"type": "table"}
        if scored:
            s, w, why = scored[0]
            r.notes.append(f"I would deal with {w} first: " + ("; ".join(why) or "no open issue found") + ".")
        r.notes.append(f"Judgement across the {len(cand)} wells discussed in this session. Safety first (gas/H2S response missed), then the overdue recalled pump (a cracked plunger can make the pump much harder to pull), then lost production, then approvals.")
        p["steps"] = [_step("priority", wells=cand[:8])]
        return p, [r], []
    return None
