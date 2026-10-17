"""Deterministic operators. Each returns a Result: rows + evidence + proof + default visual.

Operators never hardcode IDs, thresholds or dates; rules come from Data.rule(), today from Data.today.
"""
from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from datetime import date, timedelta

import pandas as pd

from .views import Data

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


@dataclass
class Result:
    op: str
    title: str
    rows: list[dict] = field(default_factory=list)
    columns: list[str] = field(default_factory=list)
    viz: dict = field(default_factory=lambda: {"type": "text"})
    evidence: list[dict] = field(default_factory=list)
    proof: list[dict] = field(default_factory=list)
    facts: dict = field(default_factory=dict)        # key numbers for narration / checking
    conflicts: list[dict] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)   # caveats the answer must mention

    def to_dict(self):
        return asdict(self)


def fmt_day(d) -> str:
    d = pd.Timestamp(d)
    return f"{d.day} {MONTHS[d.month - 1]} {d.year}"


def _r(x, n=1):
    return None if x is None or pd.isna(x) else round(float(x), n)


class Ops:
    def __init__(self, data: Data):
        self.d = data

    # ------------------------------------------------------------------ evidence helpers
    def _ev(self, res: Result, id_, type_, label=""):
        if id_ and not any(e["id"] == id_ for e in res.evidence):
            res.evidence.append({"id": id_, "type": type_, "label": label})

    def _rule_proof(self, res: Result, well_type, key, text):
        r = self.d.rule(well_type, key)
        if r:
            res.proof.append({"step": text, "rule": {"doc": r["doc_id"], "section": r["section"], "quote": r["quote"],
                                                     "value": r["value"], "via": r.get("via")}})
            self._ev(res, f"{r['doc_id']} {r['section']}", "doc", r["quote"][:120] if r["quote"] else "")
        return r

    def _scope_wells(self, area=None, well_type=None, wells=None) -> list[str]:
        w = self.d.wells
        if wells:
            w = w[w.asset_id.isin(wells)]
        if area:
            aid = self.d.area_id(area) or area
            w = w[w.area_id == aid]
        if well_type:
            w = w[w.well_type == well_type]
        return list(w.asset_id)

    # ------------------------------------------------------------------ status
    def open_repairs(self, aid, on: date | None = None) -> pd.DataFrame:
        on = on or self.d.today
        m = self.d.mnt
        return m[(m.asset_id == aid) & (m.started_at_dt.dt.date <= on) &
                 (m.completed_at_dt.isna() | (m.completed_at_dt.dt.date > on))]

    def valid_notes(self, aid, on: date) -> pd.DataFrame:
        n = self.d.notes
        n = n[(n.asset_id == aid) & (n.note_type != "correction")]
        if n.empty:
            return n
        vf = pd.to_datetime(n.valid_from, errors="coerce")
        vt = pd.to_datetime(n.valid_to, errors="coerce")
        ts = pd.Timestamp(on)
        return n[(vf <= ts) & (vt.isna() | (vt >= ts))]

    def explain_down(self, aid, row) -> dict:
        """Why a well is not producing at a given inspection. Order: open repair > valid note > ledger fact > inspector remark."""
        day = row["day"]
        reasons, refs = [], []
        rep = self.open_repairs(aid, day)
        for _, m in rep.iterrows():
            end = m.completed_at_dt
            still = end is pd.NaT or pd.isna(end) or end.date() > self.d.today
            eq = m.equipment_kind.replace("_", " ")
            issue = m.issue[0].lower() + m.issue[1:]
            what = issue if issue.startswith(eq) else f"{eq} {issue}"
            reasons.append(f"Repair {m.maintenance_id}, {what}, "
                           f"started {fmt_day(m.started_at_dt)}" + (", still open" if still else f", until {fmt_day(end)}"))
            refs.append(("maintenance", m.maintenance_id))
        for _, n in self.valid_notes(aid, day).iterrows():
            if re.search(r"shut|down|stop|workover|waiting|maint|replace|tie-in", n.text, re.I):
                reasons.append(f"Note {n.note_id} by {self.d.name(n.author_user_id)}: {n.text}")
                refs.append(("note", n.note_id))
        for f in self.d.ov.well_facts:
            if f.get("scope_id") == aid and f["kind"] == "shared_fact" and f.get("field") == "producing" and f.get("status") != "contradicted":
                vf = f.get("valid_from") and date.fromisoformat(f["valid_from"])
                vt = f.get("valid_to") and date.fromisoformat(f["valid_to"])
                if (not vf or vf <= day) and (not vt or vt >= day):
                    reasons.append(f"{f['author_name']} said: {f['text']}")
                    refs.append(("ledger", f["id"]))
        remark = (row.get("notes") or "").strip()
        return {"reasons": reasons, "refs": refs, "remark": remark}

    def well_status(self, aid: str) -> Result:
        d = self.d
        w = d.well(aid)
        if not w:
            return Result("well_status", f"{aid} not found", notes=[f"No well {aid} in the data."])
        lat = d.latest()
        if aid not in lat.index:
            return Result("well_status", f"{aid}: no inspections yet", notes=["No inspection on record."])
        row = lat.loc[aid]
        res = Result("well_status", f"{aid} status")
        prod = bool(row.producing)
        self._rule_proof(res, w["well_type"], "producing_delta_c",
                         f"{w['well_type']} producing rule: wellhead must be at least {row.threshold_c:g} °C above air")
        self._ev(res, row.inspection_id, "inspection", f"{fmt_day(row.day)} by {d.name(row.inspector_user_id)}")
        why = self.explain_down(aid, row) if not prod else {"reasons": [], "refs": [], "remark": (row.notes or "")}
        for t, i in why["refs"]:
            self._ev(res, i, t)
        stale = (w["recorded_status"] == "active") != prod
        recorded = w["recorded_status"] + (" (out of date)" if stale else "")
        card = {
            "asset_id": aid, "name": w["name"], "well_type": w["well_type"], "area": d.area_name.get(w["area_id"]),
            "producing": prod, "delta_c": _r(row.delta_c), "threshold_c": row.threshold_c,
            "wellhead_temp_c": _r(row.wellhead_temp_c), "ambient_temp_c": _r(row.ambient_temp_c),
            "last_inspection_id": row.inspection_id, "last_inspected": fmt_day(row.day), "method": row.method,
            "inspector": d.name(row.inspector_user_id), "recorded_status": recorded, "status_stale": stale,
            "reasons": why["reasons"], "inspector_remark": why["remark"],
            "evidence_images": json.loads(row.evidence_json or "[]"),
            "lat": w["lat"], "lon": w["lon"],
        }
        for c in row.corrections:
            card.setdefault("corrections", []).append(c)
            self._ev(res, c["id"], "ledger", f"correction by {c['author_name']}")
            res.notes.append(f"The {c['field']} of {c['target']} was corrected by {c['author_name']} from {c['original']} to {c['value']} ({c['reason']}). Original kept.")
            if why["remark"]:
                res.conflicts.append({"kind": "correction_vs_note", "target": c["target"],
                                      "a": f"{c['author_name']}: {c['field']} = {c['value']}",
                                      "b": f"Inspector {d.name(row.inspector_user_id)} noted: \"{why['remark']}\"",
                                      "ask": f"Please confirm the corrected reading for {c['target']}."})
        if not prod and not why["reasons"]:
            res.notes.append("No recorded reason for the stop. Suggest a site check of the pump jack and prime mover.")
        res.rows = [card]
        res.viz = {"type": "card"}
        res.facts = {"producing": prod, "delta_c": _r(row.delta_c), "inspection_id": row.inspection_id}
        return res

    def wells_status(self, area=None, well_type=None, producing: bool | None = False, wells=None) -> Result:
        d = self.d
        ids = self._scope_wells(area, well_type, wells)
        lat = d.latest()
        lat = lat[lat.index.isin(ids)]
        if producing is not None:
            lat = lat[lat.producing == producing]
        scope = d.area_name.get(d.area_id(area) or "", area) if area else "the field"
        res = Result("wells_status", f"Wells {'not ' if producing is False else ''}producing in {scope}")
        for aid, row in lat.sort_index().iterrows():
            w = d.well(aid)
            prod = bool(row.producing)
            why = self.explain_down(aid, row) if not prod else {"reasons": [], "refs": [], "remark": row.notes or ""}
            stale = (w["recorded_status"] == "active") != prod
            reason = "; ".join(why["reasons"])
            if not prod and not reason:
                reason = "No recorded reason" + (f". The inspector noted \"{why['remark']}\"" if why["remark"] else "")
            elif why["remark"] and not prod:
                reason += f" (inspector: \"{why['remark']}\")"
            corr = [f"{c['field']} corrected by {c['author_name']} ({c['original']} to {c['value']})" for c in row.corrections]
            res.rows.append({"Well": aid, "Type": w["well_type"], "Wellhead above air": f"{row.delta_c:.1f} °C",
                             "Last inspected": fmt_day(row.day),
                             "Recorded status": w["recorded_status"] + (" (out of date)" if stale else ""),
                             "Reason": reason if not prod else "", "Corrections": "; ".join(corr)})
            self._ev(res, row.inspection_id, "inspection")
            for t, i in why["refs"]:
                self._ev(res, i, t)
            for c in row.corrections:
                self._ev(res, c["id"], "ledger")
        # wells that dropped out because of a correction must be explained
        if producing is False:
            all_lat = d.latest()
            for aid, row in all_lat[all_lat.index.isin(ids) & all_lat.producing].iterrows():
                for c in row.corrections:
                    orig_delta = (c["original"] if c["field"] == "wellhead_temp_c" else row.wellhead_temp_c) - row.ambient_temp_c
                    if orig_delta < row.threshold_c:
                        res.notes.append(f"{aid} is no longer listed: {c['author_name']} corrected {c['target']} "
                                         f"{c['field']} from {c['original']} to {c['value']} ({c['reason']}), "
                                         f"which puts it {row.delta_c:.1f} °C above air, above the {row.threshold_c:g} °C limit.")
                        self._ev(res, c["id"], "ledger")
        types = sorted(set(d.wells[d.wells.asset_id.isin([r["Well"] for r in res.rows])].well_type))
        for t in types:
            self._rule_proof(res, t, "producing_delta_c", f"{t}: producing when wellhead is at least {d.rule_value(t, 'producing_delta_c'):g} °C above air")
        if any(r["Reason"].startswith("No recorded reason") for r in res.rows):
            res.notes.append("Where nothing explains the stop, check the pump jack and prime mover on site; no cause is invented.")
        res.columns = ["Well", "Type", "Wellhead above air", "Last inspected", "Recorded status", "Reason", "Corrections"]
        if not any(r["Corrections"] for r in res.rows):
            res.columns.remove("Corrections")
        res.viz = {"type": "table"}
        res.facts = {"count": len(res.rows), "wells": [r["Well"] for r in res.rows]}
        return res

    # ------------------------------------------------------------------ time series
    def series(self, aid: str, weeks: int | None = 13, start: date | None = None, end: date | None = None) -> Result:
        d = self.d
        x = d.ins[(d.ins.asset_id == aid) & (d.ins.day <= (end or d.today))]
        if start:
            x = x[x.day >= start]
        elif weeks:
            x = x.tail(weeks)
        res = Result("series", f"{aid} wellhead vs air temperature")
        w = d.well(aid)
        self._rule_proof(res, w.get("well_type"), "producing_delta_c", "Not producing when the gap is below the type limit")
        for _, r in x.iterrows():
            res.rows.append({"date": str(r.day), "label": fmt_day(r.day), "wellhead_temp_c": _r(r.wellhead_temp_c),
                             "ambient_temp_c": _r(r.ambient_temp_c), "delta_c": _r(r.delta_c), "producing": bool(r.producing),
                             "inspection_id": r.inspection_id})
            self._ev(res, r.inspection_id, "inspection")
        down = [r["label"] for r in res.rows if not r["producing"]]
        res.columns = ["label", "wellhead_temp_c", "ambient_temp_c", "delta_c", "producing"]
        res.viz = {"type": "line", "x": "label", "series": ["wellhead_temp_c", "ambient_temp_c"], "marker": "producing"}
        res.facts = {"readings": len(res.rows), "not_producing": down,
                     "from": res.rows[0]["label"] if res.rows else None, "to": res.rows[-1]["label"] if res.rows else None}
        return res

    # ------------------------------------------------------------------ downtime
    def downtime(self, area=None, well_type=None, wells=None, start=None, end=None, top: int | None = None, why: bool = False) -> Result:
        d = self.d
        ids = self._scope_wells(area, well_type, wells)
        x = d.ins[d.ins.asset_id.isin(ids)]
        if start:
            x = x[x.day >= start]
        if end:
            x = x[x.day <= end]
        down = x[~x.producing]
        g = down.groupby("asset_id").inspection_id.apply(list)
        rows = []
        for aid in ids:
            lst = g.get(aid, [])
            rows.append({"Well": aid, "Type": d.well(aid)["well_type"], "Downtime days": 7 * len(lst), "Inspections": lst})
        rows.sort(key=lambda r: (-r["Downtime days"], r["Well"]))
        res = Result("downtime", "Downtime")
        res.proof.append({"step": "Downtime = 7 days per weekly inspection that found the well not producing; missed inspections add nothing; repair downtime_hours not used.",
                          "rule": {"doc": "Dataset Guide", "section": "Inspections", "quote": "every inspection in a period that finds the well not producing oil counts as 7 days of downtime"}})
        self._ev(res, "Dataset Guide: downtime", "doc")
        for t in sorted(set(r["Type"] for r in rows)):
            self._rule_proof(res, t, "producing_delta_c", f"{t} producing limit")
        shown = rows[:top] if top else rows
        if top and len(rows) > top:
            res.facts["next"] = {"Well": rows[top]["Well"], "days": rows[top]["Downtime days"]}
        for r in shown:
            for i in r["Inspections"]:
                self._ev(res, i, "inspection")
        res.rows = [{k: v for k, v in r.items()} for r in shown]
        for r in res.rows:
            insp_ids = r.pop("Inspections")
            r["Not-producing inspections"] = ", ".join(insp_ids)
            if why:
                reasons, refs = [], []
                for iid in insp_ids:
                    row = d.ins[d.ins.inspection_id == iid].iloc[0]
                    ex = self.explain_down(r["Well"], row)
                    for text, ref in zip(ex["reasons"], ex["refs"]):
                        if text not in reasons:
                            reasons.append(text)
                            refs.append(ref)
                    if not ex["reasons"] and ex["remark"] and f"Inspector: \"{ex['remark']}\"" not in reasons:
                        reasons.append(f"Inspector: \"{ex['remark']}\"")
                r["Why"] = "; ".join(reasons[:4]) if reasons else "No recorded reason for the stopped inspections"
                for t, i in refs[:8]:
                    self._ev(res, i, t)
        res.columns = ["Well", "Type", "Downtime days"] + (["Why"] if why else ["Not-producing inspections"])
        res.viz = {"type": "bar" if len(shown) <= 12 else "table", "x": "Well", "y": "Downtime days"}
        res.facts.update({"window": [str(start), str(end)], "ranking": [(r["Well"], r["Downtime days"]) for r in shown]})
        return res

    # ------------------------------------------------------------------ spills
    def spill_rows(self, ids, start=None, end=None) -> pd.DataFrame:
        x = self.d.ins[self.d.ins.asset_id.isin(ids) & (self.d.ins.spill_detected == 1)]
        if start:
            x = x[x.day >= start]
        if end:
            x = x[x.day <= end]
        return x

    def spills(self, area=None, well_type=None, wells=None, start=None, end=None, viz: str | None = None) -> Result:
        d = self.d
        ids = self._scope_wells(area, well_type, wells)
        x = self.spill_rows(ids, start, end)
        real = x[x.real_spill]
        res = Result("spills", "Spills")
        for _, r in x[~x.real_spill].iterrows():
            res.notes.append(f"{r.inspection_id} ({fmt_day(r.day)}) was a detection corrected as not a spill"
                             + (f" by note {r.correction_note}" if isinstance(r.correction_note, str) else "") + "; it does not count.")
            self._ev(res, r.inspection_id, "inspection")
            if isinstance(r.correction_note, str):
                self._ev(res, r.correction_note, "note")
        for _, r in real.iterrows():
            corr = [c for c in r.corrections if c["field"] == "spill_est_volume_bbl"]
            res.rows.append({"Well": r.asset_id, "Date": fmt_day(r.day), "Inspection": r.inspection_id,
                             "Barrels": _r(r.spill_est_volume_bbl), "Area % of pad": _r(r.spill_area_pct),
                             "Class": r.spill_class, "lat": r.lat, "lon": r.lon,
                             "Area": d.area_name.get(r.area_id), "month": int(r.ts.month), "year": int(r.ts.year),
                             "Volume note": (f"corrected by {corr[0]['author_name']} from AI estimate {corr[0]['original']}" if corr else "")})
            self._ev(res, r.inspection_id, "inspection")
            for c in corr:
                self._ev(res, c["id"], "ledger")
        res.proof.append({"step": "Corrected detections removed (correction notes win).",
                          "rule": {"doc": "spill-response-sop", "section": "7. False positives", "quote": "Corrected detections do not count as spills for reporting or statistics."}})
        total = round(sum(r["Barrels"] or 0 for r in res.rows), 1)
        res.facts = {"count": len(res.rows), "total_bbl": total, "detections": len(x), "corrected": int((~x.real_spill).sum())}
        res.columns = ["Well", "Date", "Inspection", "Barrels", "Class"] + (["Volume note"] if any(r["Volume note"] for r in res.rows) else [])
        res.viz = {"type": viz or "table"}
        if viz == "map":
            res.columns = ["Well", "Date", "Barrels", "lat", "lon"]
            res.viz = {"type": "map", "lat": "lat", "lon": "lon", "label": "Well"}
        return res

    def spill_heatmap(self, year: int, area=None) -> Result:
        res = self.spills(area=area, start=date(year, 1, 1), end=min(date(year, 12, 31), self.d.today))
        last_month = 12 if year < self.d.today.year else self.d.today.month
        months = MONTHS[:last_month]
        areas = sorted(self.d.areas.area_id, key=lambda a: self.d.area_name[a])
        matrix = []
        for a in areas:
            nm = self.d.area_name[a]
            vals = [sum(1 for r in res.rows if r["Area"] == nm and r["month"] == m + 1) for m in range(last_month)]
            matrix.append({"Area": nm, **dict(zip(months, vals)), "Total": sum(vals)})
        res.op, res.title = "spill_heatmap", f"{year} spills by area and month"
        res.facts["totals"] = {m["Area"]: m["Total"] for m in matrix}
        res.rows, res.columns = matrix, ["Area"] + months + ["Total"]
        res.viz = {"type": "heatmap", "row": "Area", "cols": months}
        return res

    # ------------------------------------------------------------------ repairs
    def repairs(self, wells=None, area=None, start=None, end=None, kind=None, equipment=None) -> Result:
        d = self.d
        ids = self._scope_wells(area, None, wells)
        m = d.mnt[d.mnt.asset_id.isin(ids)]
        if start:
            m = m[m.started_at_dt.dt.date >= start]
        if end:
            m = m[m.started_at_dt.dt.date <= end]
        if kind:
            m = m[m.maintenance_type == kind]
        if equipment:
            m = m[m.equipment_kind == equipment]
        res = Result("repairs", "Repair cost")
        for aid in ids:
            mm = m[m.asset_id == aid]
            res.rows.append({"Well": aid, "Repairs": len(mm), "Cost USD": round(float(mm.cost_total.sum()), 0),
                             "Corrective": int((mm.maintenance_type == "corrective").sum())})
            for i in mm.maintenance_id:
                self._ev(res, i, "maintenance")
        res.proof.append({"step": "A repair belongs to a period by its start date; cost = cost_usd.total.",
                          "rule": {"doc": "Example Questions", "section": "conventions", "quote": "A repair belongs to a period by its start date."}})
        res.columns = ["Well", "Repairs", "Corrective", "Cost USD"]
        res.viz = {"type": "bar", "x": "Well", "y": "Cost USD"} if len(ids) <= 12 else {"type": "table"}
        res.facts = {"costs": {r["Well"]: r["Cost USD"] for r in res.rows}}
        return res

    # ------------------------------------------------------------------ RCA
    def rca_due(self, area=None, well_type=None, wells=None, equipment: str | None = None) -> Result:
        d = self.d
        ids = self._scope_wells(area, well_type, wells)
        res = Result("rca_due", "Root-cause analysis due")
        manual_hits, eff_hits = [], []
        for aid in ids:
            wt = d.well(aid)["well_type"]
            months = int(d.rule_value(wt, "rca_window_months", 12))
            start = (pd.Timestamp(d.today) - pd.DateOffset(months=months)).date()
            m = d.mnt[(d.mnt.asset_id == aid) & (d.mnt.maintenance_type == "corrective") &
                      (d.mnt.started_at_dt.dt.date >= start) & (d.mnt.started_at_dt.dt.date <= d.today)]
            if equipment:
                m = m[m.equipment_kind == equipment]
            for eq, grp in m.groupby("equipment_kind"):
                base = d.rule_value(wt, "rca_corrective_count", 3)
                ov = self._override(aid, wt, "rca_corrective_count", eq)
                limit = ov["value"] if ov else base
                row = {"Well": aid, "Type": wt, "Equipment": eq.replace("_", " "), "Corrective repairs": len(grp),
                       "Repairs": ", ".join(grp.maintenance_id), "Limit": int(limit),
                       "Rule": (f"{ov['author_name']}'s rule for {ov['scope_id']} ({int(limit)})" if ov else f"{wt} manual ({int(base)})")}
                if len(grp) >= base:
                    manual_hits.append(row)
                if len(grp) >= limit:
                    eff_hits.append(row)
                    for i in grp.maintenance_id:
                        self._ev(res, i, "maintenance")
                    if ov:
                        self._ev(res, ov["id"], "ledger", f"rule by {ov['author_name']}")
        for t in sorted(set(d.wells[d.wells.asset_id.isin(ids)].well_type)):
            self._rule_proof(res, t, "rca_corrective_count", f"{t}: RCA after N corrective repairs on the same equipment in 12 months")
        res.rows = sorted(eff_hits, key=lambda r: r["Well"])
        res.columns = ["Well", "Type", "Equipment", "Corrective repairs", "Rule", "Repairs"]
        res.viz = {"type": "table"}
        mh = {r["Well"] + r["Equipment"] for r in manual_hits}
        added = [r for r in res.rows if r["Well"] + r["Equipment"] not in mh]
        if added:
            res.facts["diff_vs_manual"] = {"added": [r["Well"] for r in added], "manual": sorted(r["Well"] for r in manual_hits)}
            for r in added:
                res.notes.append(f"{r['Well']} ({r['Type']}, {r['Corrective repairs']} repairs) is included because of {r['Rule']}, not the manual.")
        res.facts["wells"] = [r["Well"] for r in res.rows]
        return res

    def _override(self, aid, wt, key, equipment):
        best = None
        for o in self.d.ov.rule_overrides:
            if o["key"] != key or (o.get("equipment_kind") and o["equipment_kind"] != equipment):
                continue
            if (o["scope_type"] == "well" and o["scope_id"] == aid) or (o["scope_type"] == "well_type" and o["scope_id"] == wt):
                if best is None or o["scope_type"] == "well":
                    best = o
        return best

    # ------------------------------------------------------------------ compliance
    def _report_for(self, inspection_id) -> dict | None:
        m = self.d.mnt[self.d.mnt.triggered_by_inspection_id == inspection_id]
        for _, r in m.iterrows():
            rep = self.d.reports[self.d.reports.maintenance_id == r.maintenance_id]
            if not rep.empty:
                with_db = self._extracted(r.maintenance_id)
                return {"maintenance_id": r.maintenance_id, **with_db}
        return None

    def _extracted(self, mid) -> dict:
        from .. import db
        if not hasattr(self, "_ext"):
            with db.session() as con:
                self._ext = {r[0]: json.loads(r[1] or "{}") for r in con.execute("SELECT maintenance_id, extracted_json FROM reports")}
        return self._ext.get(mid, {})

    def spill_compliance(self, spill_row) -> list[dict]:
        """Every SOP check for one real spill. Status: breach | pending | met | n/a."""
        d = self.d
        r = spill_row
        ins_id, disc = r.inspection_id, r.ts
        vol = r.spill_est_volume_bbl
        cls = d.spill_class(vol)
        reportable = vol is not None and not pd.isna(vol) and vol >= d.reportable_min()
        major = cls == "major"
        ev = d.reg[d.reg.related_inspection_id == ins_id]
        rep = self._report_for(ins_id)
        out = []
        # SR-01
        if reportable:
            lim = d.rule_value(None, "SR-01.major_deadline_hours" if major else "SR-01.deadline_hours", 24)
            before = d.rule_value(None, "SR-01.legacy_before")
            if not major and before and int(f"{disc:%Y%m%d}") < int(before):
                lim = d.rule_value(None, "SR-01.legacy_deadline_hours", lim)
            filed = ev[ev.event_type == "spill_report_filed"]
            if not filed.empty:
                h = float(filed.iloc[0].hours_to_report)
                out.append({"protocol": "SR-01", "status": "breach" if h > lim else "met",
                            "detail": f"Written report filed after {h:g} hours ({filed.iloc[0].event_id}), limit {lim:g} hours",
                            "refs": [filed.iloc[0].event_id]})
            else:
                due = disc + pd.Timedelta(hours=lim)
                past = pd.Timestamp(d.today, tz="UTC") > due
                out.append({"protocol": "SR-01", "status": "breach" if past else "pending",
                            "detail": f"Reportable spill ({vol:g} bbl): written notice due within {lim:g} hours of "
                                      f"{fmt_day(disc)} {disc:%H:%M}; none recorded" + (" (possible breach)" if past else ""),
                            "refs": []})
        # SR-02 containment (report-only fact)
        lim2 = d.rule_value(None, "SR-02.deadline_hours", 4)
        if rep and rep.get("containment_hours") is not None:
            h = rep["containment_hours"]
            out.append({"protocol": "SR-02", "status": "breach" if h > lim2 else "met",
                        "detail": f"Contained after about {h:g} hours (limit {lim2:g}); found only in report {rep['maintenance_id']}",
                        "refs": [rep["maintenance_id"]]})
        # SR-03 verification for reportable spills
        if reportable:
            days = d.rule_value(None, "SR-03.deadline_days", 60)
            due = (disc + pd.Timedelta(days=days)).date()
            passed = ev[(ev.event_type == "site_inspection") & (ev.status == "closed")]
            openv = ev[(ev.event_type == "site_inspection") & (ev.status == "open")]
            if not passed.empty:
                out.append({"protocol": "SR-03", "status": "met", "detail": f"Verified by {passed.iloc[0].event_id}", "refs": [passed.iloc[0].event_id]})
            else:
                st = "breach" if d.today > due else "pending"
                out.append({"protocol": "SR-03", "status": st,
                            "detail": f"Clean-up verification due by {fmt_day(due)}" + (", still open" if st == "breach" else ""),
                            "refs": list(openv.event_id)})
        # NOVs and RC-04
        rc_days = d.rule_value(None, "RC-04.deadline_days", 30)
        for _, n in ev[ev.event_type == "notice_of_violation"].iterrows():
            due = (n.date_dt + pd.Timedelta(days=rc_days)).date()
            resp = d.reg[(d.reg.asset_id == r.asset_id) & (d.reg.event_type == "nov_response_filed") &
                         ((d.reg.related_inspection_id == ins_id) | (d.reg.date_dt >= n.date_dt))]
            if resp.empty:
                st = "breach" if d.today > due else "pending"
                out.append({"protocol": "RC-04", "status": st,
                            "detail": f"Notice {n.event_id} needed a response by {fmt_day(due)}; none recorded",
                            "refs": [n.event_id]})
            else:
                out.append({"protocol": "RC-04", "status": "met", "detail": f"Response {resp.iloc[0].event_id}", "refs": [resp.iloc[0].event_id]})
            out.append({"protocol": n.protocol_id or "NOV", "status": "fine",
                        "detail": f"Notice of violation {n.event_id}: USD {n.fine_usd:,.0f} fine, {n.status}",
                        "refs": [n.event_id], "fine": float(n.fine_usd or 0), "fine_status": n.status})
        # stale statements inside the report (Q13): class / reporting duty no longer match current volume
        if rep:
            stated = rep.get("spill_class_stated")
            if stated and cls and stated != cls:
                out.append({"protocol": "report", "status": "stale",
                            "detail": f"Report {rep['maintenance_id']} classed the spill as \"{stated}\" and "
                                      f"{'listed no reporting duty' if not rep.get('reporting_duty_stated') else 'listed reporting'}; "
                                      f"with the current volume ({vol:g} bbl) it is {cls}, so that no longer holds",
                            "refs": [rep["maintenance_id"]]})
        return out

    def compliance_audit(self, aid: str, start=None, end=None) -> Result:
        d = self.d
        start = start or (pd.Timestamp(d.today) - pd.DateOffset(months=12)).date()
        end = end or d.today
        res = Result("compliance_audit", f"{aid} compliance")
        w = d.well(aid)
        sp = self.spill_rows([aid], start, end)
        breaches, pending, met, fines = [], [], [], []
        for _, r in sp[sp.real_spill].iterrows():
            for c in self.spill_compliance(r):
                c = {**c, "spill": f"{fmt_day(r.day)} spill of {r.spill_est_volume_bbl:g} bbl ({r.inspection_id})"}
                self._ev(res, r.inspection_id, "inspection")
                for ref in c["refs"]:
                    self._ev(res, ref, "maintenance" if ref.startswith("MNT") else "regulatory")
                {"breach": breaches, "pending": pending, "met": met, "fine": fines, "stale": pending}.get(c["status"], met).append(c)
        # RCA (open action)
        rca = self.rca_due(wells=[aid])
        for row in rca.rows:
            mids = row["Repairs"].split(", ")
            ext = self._extracted(mids[-1])
            flag = "; the report for " + mids[-1] + " marks it as \"Action required\"" if ext.get("action_required") else ""
            pending.append({"protocol": "Manual §10 RCA", "status": "pending",
                            "detail": f"Root-cause analysis due on the {row['Equipment']}: {row['Corrective repairs']} corrective repairs in 12 months ({row['Repairs']}){flag}",
                            "refs": mids})
            for i in mids:
                self._ev(res, i, "maintenance")
        # planned shut-in note without a maintenance record (manual §4)
        for _, n in d.notes[(d.notes.asset_id == aid) & (d.notes.note_type != "correction")].iterrows():
            if re.search(r"not (yet )?in the maintenance system|no work order", n.text, re.I):
                vf = pd.to_datetime(n.valid_from).date()
                if vf >= start:
                    pending.append({"protocol": f"{w['well_type']} manual §4", "status": "pending",
                                    "detail": f"Planned shut-in from {fmt_day(vf)} not yet recorded in the maintenance system, required before work starts (note {n.note_id})",
                                    "refs": [n.note_id]})
                    self._ev(res, n.note_id, "note")
        # RC-02 annual flowline test
        tests = d.mnt[(d.mnt.asset_id == aid) & d.mnt.issue.str.contains("integrity test", case=False, na=False) &
                      (d.mnt.started_at_dt.dt.year == d.today.year)]
        if not tests.empty:
            t = tests.iloc[-1]
            met.append({"protocol": "RC-02", "status": "met", "detail": f"Yearly flowline test done on {fmt_day(t.started_at_dt)} ({t.maintenance_id})", "refs": [t.maintenance_id]})
            self._ev(res, t.maintenance_id, "maintenance")
        else:
            pending.append({"protocol": "RC-02", "status": "pending", "detail": f"No flowline integrity test recorded in {d.today.year} yet", "refs": []})
        # RC-01 inspection gap
        gap_lim = d.rule_value(None, "RC-01.interval_days", 14)
        x = d.ins[(d.ins.asset_id == aid) & (d.ins.day >= start) & (d.ins.day <= end)].ts
        gaps = x.diff().dt.days
        for i, g in gaps[gaps > gap_lim].items():
            breaches.append({"protocol": "RC-01", "status": "breach", "detail": f"{int(g)} days without inspection before {fmt_day(x[i])}", "refs": []})
        for p in ("SR-01", "SR-02", "SR-03", "RC-04", "RC-02"):
            r = d.rule(None, f"{p}.text")
            if r:
                self._ev(res, f"{r['doc_id']} {p}", "doc", r["quote"][:140])
        total_fine = sum(f["fine"] for f in fines)
        open_fine = sum(f["fine"] for f in fines if f["fine_status"] == "open")
        res.rows = ([{"Status": "Breach", "Rule": b["protocol"], "Detail": b["detail"], "Spill": b.get("spill", "")} for b in breaches] +
                    [{"Status": "Fine", "Rule": f["protocol"], "Detail": f["detail"], "Spill": f.get("spill", "")} for f in fines] +
                    [{"Status": "Pending", "Rule": p["protocol"], "Detail": p["detail"], "Spill": p.get("spill", "")} for p in pending] +
                    [{"Status": "Met", "Rule": m["protocol"], "Detail": m["detail"], "Spill": m.get("spill", "")} for m in met])
        res.columns = ["Status", "Rule", "Detail", "Spill"]
        res.viz = {"type": "table"}
        res.facts = {"breaches": len(breaches), "breach_rules": [b["protocol"] for b in breaches],
                     "fines_usd": total_fine, "open_fines_usd": open_fine, "pending": len(pending)}
        return res

    def spills_check(self, area=None, start=None, end=None, protocol: str = "SR-02", wells=None) -> Result:
        """Spills in scope that breach (SR-02) or need (SR-01) a protocol."""
        d = self.d
        ids = self._scope_wells(area, None, wells)
        sp = self.spill_rows(ids, start, end)
        res = Result("spills_check", f"Spills checked against {protocol}")
        for _, r in sp[sp.real_spill].iterrows():
            checks = [c for c in self.spill_compliance(r) if c["protocol"] == protocol]
            for c in checks:
                if protocol == "SR-02" and c["status"] != "breach":
                    continue
                res.rows.append({"Well": r.asset_id, "Date": fmt_day(r.day), "Inspection": r.inspection_id,
                                 "Barrels": _r(r.spill_est_volume_bbl), "Status": c["status"], "Detail": c["detail"]})
                self._ev(res, r.inspection_id, "inspection")
                for ref in c["refs"]:
                    self._ev(res, ref, "maintenance" if ref.startswith("MNT") else "regulatory")
                for cc in r.corrections:
                    self._ev(res, cc["id"], "ledger")
                    res.notes.append(f"{r.inspection_id} volume corrected by {cc['author_name']} from {cc['original']} to {cc['value']} bbl.")
        if protocol == "SR-01":
            lim = d.reportable_min()
            res.notes.append(f"Reportable means {lim:g} bbl or more (Spill Response SOP §3); no other spill in the period reached it." if res.rows else
                             f"No spill in the period reached {lim:g} bbl.")
        r = d.rule(None, f"{protocol}.text")
        if r:
            res.proof.append({"step": f"{protocol}: {r['quote']}", "rule": {"doc": r["doc_id"], "section": protocol, "quote": r["quote"]}})
            self._ev(res, f"{r['doc_id']} {protocol}", "doc", r["quote"][:140])
        res.columns = ["Well", "Date", "Inspection", "Barrels", "Status", "Detail"]
        res.viz = {"type": "table"}
        res.facts = {"count": len(res.rows), "wells": [r["Well"] for r in res.rows]}
        return res

    def regulator_events(self, area=None, well_type=None, wells=None, start=None, end=None, event_type=None, fines_only=False) -> Result:
        d = self.d
        ids = set(self._scope_wells(area, well_type, wells))
        x = d.reg[d.reg.asset_id.isin(ids)]
        if start:
            x = x[x.date_dt.dt.date >= start]
        if end:
            x = x[x.date_dt.dt.date <= end]
        if event_type:
            x = x[x.event_type == event_type]
        if fines_only:
            x = x[x.fine_usd > 0]
        res = Result("regulator_events", "Regulator events")
        for _, r in x.sort_values("date_dt").iterrows():
            res.rows.append({"Event": r.event_id, "Date": fmt_day(r.date_dt), "Well": r.asset_id, "Type": r.event_type.replace("_", " "),
                             "Protocol": r.protocol_id or "", "Fine USD": float(r.fine_usd or 0), "Status": r.status, "Detail": r.detail})
            self._ev(res, r.event_id, "regulatory")
        res.columns = ["Event", "Date", "Well", "Type", "Protocol", "Fine USD", "Status", "Detail"]
        res.viz = {"type": "table"}
        res.facts = {"count": len(res.rows), "fines_usd": float(x.fine_usd.fillna(0).sum()),
                     "open_fines_usd": float(x[x.status == "open"].fine_usd.fillna(0).sum()),
                     "wells": sorted({r["Well"] for r in res.rows})}
        return res

    def repair_list(self, wells=None, area=None, start=None, end=None, kind=None, equipment=None, latest: int | None = None) -> Result:
        d = self.d
        ids = self._scope_wells(area, None, wells)
        m = d.mnt[d.mnt.asset_id.isin(ids)]
        if start:
            m = m[m.started_at_dt.dt.date >= start]
        if end:
            m = m[m.started_at_dt.dt.date <= end]
        if kind:
            m = m[m.maintenance_type == kind]
        if equipment:
            m = m[m.equipment_kind == equipment]
        m = m.sort_values("started_at_dt", ascending=False)
        if latest:
            m = m.head(latest)
        res = Result("repair_list", "Repairs")
        for _, r in m.iterrows():
            ext = self._extracted(r.maintenance_id)
            res.rows.append({"Repair": r.maintenance_id, "Well": r.asset_id, "Started": fmt_day(r.started_at_dt), "Type": r.maintenance_type,
                             "Equipment": r.equipment_kind.replace("_", " "), "Issue": r.issue, "Action": r.action_taken,
                             "Cost USD": float(r.cost_total or 0), "Root cause": ext.get("root_cause") or ""})
            self._ev(res, r.maintenance_id, "maintenance")
        res.columns = ["Repair", "Well", "Started", "Type", "Equipment", "Issue", "Cost USD", "Root cause"]
        res.viz = {"type": "table"}
        res.facts = {"count": len(res.rows), "total_usd": float(m.cost_total.fillna(0).sum()), "wells": sorted(set(m.asset_id))}
        return res

    def list_wells(self, area=None, well_type=None, wells=None) -> Result:
        d = self.d
        ids = self._scope_wells(area, well_type, wells)
        w = d.wells[d.wells.asset_id.isin(ids)]
        res = Result("list_wells", "Wells")
        lat = d.latest()
        for _, r in w.iterrows():
            prod = None
            if r.asset_id in lat.index:
                prod = bool(lat.loc[r.asset_id].producing)
            res.rows.append({"Well": r.asset_id, "Type": r.well_type, "Area": d.area_name.get(r.area_id), "Team": d.team_name.get(r.team_id),
                             "In charge": d.name(r.in_charge_user_id), "Installed": str(r.installed_on)[:10],
                             "Producing now": "yes" if prod else ("no" if prod is False else "unknown"), "Barrels": None, "lat": r.lat, "lon": r.lon})
        res.columns = ["Well", "Type", "Area", "In charge", "Installed", "Producing now"]
        res.viz = {"type": "table"}
        res.facts = {"count": len(res.rows), "by_type": {t: int((w.well_type == t).sum()) for t in sorted(w.well_type.dropna().unique())}}
        return res

    def downtime_by_area(self, start=None, end=None) -> Result:
        d = self.d
        x = d.ins
        if start:
            x = x[x.day >= start]
        if end:
            x = x[x.day <= end]
        down = x[~x.producing]
        res = Result("downtime_by_area", "Downtime by area")
        for aid, nm in sorted(d.area_name.items(), key=lambda kv: kv[1]):
            n = int((down.area_id == aid).sum())
            res.rows.append({"Area": nm, "Downtime days": 7 * n, "Wells": int((d.wells.area_id == aid).sum())})
        res.columns = ["Area", "Downtime days", "Wells"]
        res.viz = {"type": "bar", "x": "Area", "y": "Downtime days"}
        res.facts = {"by_area": {r["Area"]: r["Downtime days"] for r in res.rows}}
        res.proof.append({"step": "Downtime = 7 days per non-producing weekly inspection, summed per area.",
                          "rule": {"doc": "Dataset Guide", "section": "Inspections", "quote": "every inspection in a period that finds the well not producing oil counts as 7 days of downtime"}})
        return res

    # ------------------------------------------------------------------ spill verdict (disagreeing notes)
    def spill_verdict(self, aid: str, on: date) -> Result:
        d = self.d
        x = d.ins[(d.ins.asset_id == aid) & (d.ins.day == on)]
        res = Result("spill_verdict", f"{aid} spill on {fmt_day(on)}")
        if x.empty:
            res.notes.append(f"No inspection of {aid} on {fmt_day(on)}.")
            return res
        r = x.iloc[0]
        self._ev(res, r.inspection_id, "inspection")
        notes = d.notes[(d.notes.asset_id == aid) & d.notes.text.str.contains(r.inspection_id, na=False)]
        formal = notes[notes.note_type == "correction"]
        informal = notes[notes.note_type != "correction"]
        repairs = d.mnt[d.mnt.triggered_by_inspection_id == r.inspection_id]
        for _, n in notes.iterrows():
            self._ev(res, n.note_id, "note")
        for i in repairs.maintenance_id:
            self._ev(res, i, "maintenance")
        stands = bool(r.real_spill)
        res.rows = [{"inspection_id": r.inspection_id, "detected": bool(r.spill_detected), "volume_bbl": _r(r.spill_est_volume_bbl),
                     "remark": r.notes, "verdict": "real spill" if stands else "not a spill",
                     "formal_correction": list(formal.note_id), "repairs": list(repairs.maintenance_id)}]
        if len(informal) >= 2 or (len(informal) and not formal.empty):
            res.conflicts.append({"kind": "notes_disagree", "target": r.inspection_id,
                                  "items": [{"note": n.note_id, "author": d.name(n.author_user_id),
                                             "role": d.users.set_index("user_id").role.get(n.author_user_id, ""), "text": n.text}
                                            for _, n in informal.iterrows()],
                                  "resolution": ("A formal correction exists, so it wins." if not formal.empty else
                                                 "Neither note is a formal correction" + (f", and spill repair {', '.join(repairs.maintenance_id)} was done" if len(repairs) else "") +
                                                 ", so the detection stands.")})
        res.viz = {"type": "card"}
        res.facts = {"real": stands, "volume": _r(r.spill_est_volume_bbl)}
        return res
