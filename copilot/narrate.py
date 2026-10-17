"""Deterministic answer text for every operator. The LLM may rephrase it, but this text alone is a complete,
correct answer, so the copilot still works when the model is rate-limited."""
from __future__ import annotations

from .engine.ops import Result


def _list(xs):
    xs = list(xs)
    return xs[0] if len(xs) == 1 else ", ".join(xs[:-1]) + " and " + xs[-1] if xs else ""


ROW_OPS = {"gas_response", "bypasses", "letter_compliance", "status_disagreements", "recalled_pumps", "recalled_followup", "listen_ranking", "waiting_reasons", "priority", "freeze_checks", "list_wells", "regulator_events", "repair_list", "downtime_by_area", "sql", "wells_status", "spills", "rca_due", "compliance_audit", "spills_check", "repairs", "downtime", "planned_downtime"}


def summarize(r: Result, brief: bool = False) -> str:
    try:
        out = _summarize(r, brief)
    except Exception:  # noqa: BLE001  never let a formatting error hide an answer
        out = f"**{r.title}.**" + "".join(f"\n- {n}" for n in r.notes)
    if brief and r.op in ("correction", "rule_override", "statement"):
        keep = [ln for ln in out.split("\n") if not (ln.startswith("- Ledger id") or ln.startswith("- **Conflict")
                or ln.startswith("- **People disagree") or ln.startswith("  - "))]
        return "\n".join(keep)
    if not brief or r.op not in ROW_OPS or r.op in GENERIC or r.viz.get("type") in (None, "text", "card", "receipt"):
        return out
    keep = [ln for ln in out.split("\n") if not ln.startswith("- ") or "corrected" in ln or "no longer listed" in ln or "Where nothing" in ln
            or "Next is" in ln or "Window" in ln or "Reportable means" in ln or "based on" in ln or "because of" in ln]
    return "\n".join(keep)


GENERIC = {"gas_response", "bypasses", "letter_compliance", "status_disagreements", "recalled_pumps", "recalled_followup", "listen_ranking",
           "waiting_reasons", "priority", "data_gap", "team_info", "freeze_checks", "h2s_reading", "temp_by_area"}


def _summarize(r: Result, brief: bool = False) -> str:
    f = r.facts
    op = r.op
    out = []
    if op == "well_status" and r.rows:
        c = r.rows[0]
        out.append(f"**{'Yes' if c['producing'] else 'No'}, {c['asset_id']} is {'producing' if c['producing'] else 'not producing'} oil right now.**")
        out.append(f"- Latest inspection {c['last_inspection_id']} on {c['last_inspected']}, by {c['method']}, by {c['inspector']}.")
        out.append(f"- The wellhead was {c['delta_c']} °C warmer than the air ({c['wellhead_temp_c']} vs {c['ambient_temp_c']} °C); "
                   f"the {c['well_type']} limit is {c['threshold_c']:g} °C, so it is {'above' if c['producing'] else 'below'} the limit.")
        for x in c["reasons"]:
            out.append(f"- Reason: {x}")
        if c.get("inspector_remark"):
            out.append(f"- Inspector's remark: \"{c['inspector_remark']}\"")
        if c["status_stale"]:
            out.append(f"- The recorded status still says {c['recorded_status'].replace(' (out of date)', '')}, which is out of date.")
    elif op == "wells_status":
        out.append(f"**{f['count']} well{'s' if f['count'] != 1 else ''} {r.title[6:] if r.title.startswith('Wells ') else r.title}.**"
                   + (f" ({_list(f['wells'])})" if f["count"] else ""))
        for x in r.rows:
            out.append(f"- {x['Well']}: {x['Wellhead above air']} above air, recorded status {x['Recorded status']}. {x['Reason']}.")
    elif op == "series":
        out.append(f"**{f['readings']} readings from {f['from']} to {f['to']}.** "
                   + (f"Not producing oil on {_list(f['not_producing'])}." if f["not_producing"] else "Producing at every reading."))
    elif op == "downtime":
        rk = f["ranking"]
        if len(rk) == 1:
            w, days = rk[0]
            out.append(f"**{w} was down {days} days** ({days // 7} weekly inspection{'s' if days != 7 else ''} found it not producing oil).")
            for x in r.rows:
                out.append(f"- Not-producing inspections: {x['Not-producing inspections'] or 'none'}")
        else:
            out.append("**" + "; ".join(f"{w}: {dd} days" for w, dd in rk) + "**")
            for x in r.rows:
                if x.get("Why"):
                    out.append(f"- {x['Well']} ({x['Downtime days']} days): {x['Why']}")
            if f.get("next"):
                out.append(f"- Next is {f['next']['Well']} at {f['next']['days']} days.")
        if f.get("window") and f["window"][0] != "None":
            out.append(f"- Window: {f['window'][0]} to {f['window'][1]}.")
    elif op == "spills":
        out.append(f"**{f['count']} spill{'s' if f['count'] != 1 else ''}, {f['total_bbl']} barrels in total.**")
        if f["corrected"]:
            out.append(f"- There were {f['detections']} detections; {f['corrected']} corrected as not a spill and excluded.")
        for x in r.rows[:25]:
            out.append(f"- {x['Well']} {x['Date']}: {x['Barrels']} bbl ({x['Class']}){' — ' + x['Volume note'] if x.get('Volume note') else ''}")
    elif op == "spill_heatmap":
        out.append("**" + "; ".join(f"{a}: {t}" for a, t in f["totals"].items()) + "** (corrected detections removed).")
    elif op == "repairs":
        if f.get("costs"):
            out.append("**" + " · ".join(f"{w}: USD {c:,.0f}" for w, c in f["costs"].items()) + "**")
    elif op == "rca_due":
        out.append(f"**{_list(f['wells']) or 'No wells'}{' need' if f['wells'] else ' need'} a root-cause analysis.**")
        for x in r.rows:
            out.append(f"- {x['Well']} ({x['Type']}): {x['Corrective repairs']} corrective {x['Equipment']} repairs in 12 months ({x['Repairs']}); rule: {x['Rule']}.")
    elif op == "compliance_audit":
        out.append(f"**{f['breaches']} breach{'es' if f['breaches'] != 1 else ''}"
                   + (f"; USD {f['fines_usd']:,.0f} in fines" + (", still open" if f['open_fines_usd'] else "") if f["fines_usd"] else "") + ".**")
        for x in r.rows:
            out.append(f"- [{x['Status']}] {x['Rule']}: {x['Detail']}")
    elif op == "spills_check":
        out.append(f"**{f['count']} spill{'s' if f['count'] != 1 else ''}{': ' + _list(f['wells']) if f['wells'] else ''}.**")
        for x in r.rows:
            out.append(f"- {x['Well']} ({x['Inspection']}, {x['Date']}, {x['Barrels']} bbl): {x['Detail']}")
    elif op == "spill_verdict" and r.rows:
        x = r.rows[0]
        out.append(f"**{'Yes' if f['real'] else 'No'}.** Inspection {x['inspection_id']} flagged a {x['volume_bbl']} bbl spill (\"{x['remark']}\").")
    elif op == "planned_downtime":
        out.append(f"**{'Yes' if r.rows else 'No'}.**")
        for x in r.rows:
            out.append(f"- From {x['From']}{' until ' + x['Until'] if x['Until'] else ''}: {x['What']} (source: {x['Source']})")
    elif op in ("correction", "rule_override", "statement"):
        out.append(f"**{r.title}.**")
        for x in r.rows:
            out.append("- " + "; ".join(f"{k}: {v}" for k, v in x.items()))
    elif op == "regulator_events":
        out.append(f"**{f['count']} regulator event{'s' if f['count'] != 1 else ''}; fines USD {f['fines_usd']:,.0f} (open USD {f['open_fines_usd']:,.0f}).**")
        for x in r.rows[:20]:
            out.append(f"- {x['Date']} {x['Well']} {x['Type']} {x['Protocol']}: USD {x['Fine USD']:,.0f}, {x['Status']}. {x['Detail']}")
    elif op == "repair_list":
        out.append(f"**{f['count']} repair{'s' if f['count'] != 1 else ''}, USD {f['total_usd']:,.0f} in total.**")
        for x in r.rows[:20]:
            out.append(f"- {x['Repair']} ({x['Started']}, {x['Equipment']}, {x['Type']}): {x['Issue']}; USD {x['Cost USD']:,.0f}" + (f"; root cause: {x['Root cause']}" if x["Root cause"] else ""))
    elif op == "downtime_by_area":
        out.append("**" + "; ".join(f"{a}: {v} days" for a, v in f["by_area"].items()) + "**")
    elif op == "list_wells":
        out.append(f"**{f['count']} wells** (" + ", ".join(f"{n} {t}" for t, n in f["by_type"].items()) + ").")
    elif op == "sql":
        out.append(f"**{len(r.rows)} row{'s' if len(r.rows) != 1 else ''}** from a read-only query.")
    elif op == "search_docs":
        for x in r.rows[:4]:
            out.append(f"- **{x['ref']}**: {x['text'][:400]}")
    for c in r.conflicts:
        if c["kind"] == "notes_disagree":
            out.append("- **People disagree:** " + "; ".join(f"{i['author']} ({i['role'].replace('_', ' ')}, {i['note']}): \"{i['text']}\"" for i in c["items"]))
            out.append(f"- {c['resolution']}")
        else:
            out.append(f"- **Conflict:** {c['a']} vs {c['b']}")
            if c.get("agrees_with_data"):
                out.append(f"  - The data matches: {_list(c['agrees_with_data'])}")
            if c.get("also_disagrees"):
                out.append(f"  - Also disagrees: {_list(c['also_disagrees'])}")
            out.append(f"  - {c['ask']}")
    if r.op in GENERIC and not out:
        head = {"gas_response": lambda: f"**{f['reports']} gas reports; {f['met']} met the response deadline, {f['missed']} missed.**",
                "bypasses": lambda: f"**{len(f['in_place_now'])} bypasses in place now; {len(f['violations'])} violations (past or present).**",
                "letter_compliance": lambda: f"**{f['covered']} spills covered by the letter; {len(f['not_compliant'])} not compliant" + (": " + _list(f['not_compliant']) if f['not_compliant'] else "") + ".**",
                "status_disagreements": lambda: f"**{f['count']} wells where the latest inspection and operator notes disagree.**",
                "recalled_pumps": lambda: f"**{f['count']} recalled pumps still in the ground.**",
                "recalled_followup": lambda: f"**{len(r.rows)} of those wells are not producing.**",
                "listen_ranking": lambda: f"**Top {len(r.rows)} wells most likely to need a repair.**",
                "waiting_reasons": lambda: f"**Reasons shut-ins outlast the repair, by area.**",
                "temp_by_area": lambda: f"**{f['hottest']} runs hottest.**",
                "freeze_checks": lambda: f"**{f['misses']} missed heat-trace checks in December.**"}.get(r.op)
        if head:
            out.append(head())
        elif r.op not in ("data_gap", "team_info", "h2s_reading"):
            out.append(f"**{r.title}.**")
        if not brief and r.op != "data_gap":
            for x in r.rows[:30]:
                out.append("- " + "; ".join(f"{k}: {v}" for k, v in x.items() if k not in ("lat", "lon", "In place now", "notes_n")))
    corrected = [n for n in r.notes if n.endswith("it does not count.")]
    for n in r.notes:
        if len(corrected) > 3 and n in corrected:
            continue
        out.append(f"- {n}")
    if len(corrected) > 3:
        out.append(f"- {len(corrected)} detections in this period were corrected as not a spill (rain, shadow, produced water) and excluded.")
    return "\n".join(out)
