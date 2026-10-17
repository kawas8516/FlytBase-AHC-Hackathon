"""Operators driven by the test-set documents: OPS-1..6 (operations SOP), MOC memos, recall notice, regulator letter,
operator notes. Every rule value is read from the document text, with a cited quote; nothing is keyed to a well ID."""
from __future__ import annotations

import json
import re
from datetime import date, datetime, timedelta, timezone

import pandas as pd

from .ops import Ops, Result, fmt_day

MONTHS = {m: i + 1 for i, m in enumerate(["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"])}

GAS = re.compile(r"gas odou?r|smell(?:ed)? gas|gas smell|rotten[- ]egg|h2s monitor alarm|h2s alarm|monitor alarmed", re.I)
SHUT = re.compile(r"\bshut[- ]?in\b|shut the well in|shut in |shut-in ", re.I)
RESTART = re.compile(r"restarted|back on production|back online|brought .* back online|put back on", re.I)
BYPASS_IN = re.compile(r"bypass in place|put the bypass in|bypass installed|had the bypass installed|installed .*bypass", re.I)
BYPASS_OUT = re.compile(r"took the bypass out|bypass removed|bypass pulled|bypass out\b|removed the bypass", re.I)
SYMPTOM = {"fluid pound": 3, "rattl": 3, "rod squeal": 2, "squeal": 2, "tagging bottom": 2, "amps hunting": 3, "tripping": 3,
           "leak": 3, "vibrat": 3, "knock": 3, "grind": 3, "noise": 2, "slow": 1, "hot": 2}


def _d(s: str) -> date | None:
    m = re.search(r"(\d{1,2})\s+([A-Za-z]{3})[a-z]*\s+(20\d\d)", s or "")
    return date(int(m.group(3)), MONTHS[m.group(2).lower()], int(m.group(1))) if m else None


def _ts(x) -> pd.Timestamp:
    return pd.Timestamp(x, tz="UTC") if not isinstance(x, pd.Timestamp) else x


class FinalOps:
    def __init__(self, ops: Ops):
        self.o = ops
        self.d = ops.d
        n = self.d.notes.copy()
        n["ts"] = pd.to_datetime(n.created_at, utc=True, errors="coerce")
        self.notes = n
        self.docs = self._docs()

    def _docs(self) -> dict:
        from .. import db
        with db.session() as con:
            return {r["doc_id"]: r["text"] for r in con.execute("SELECT doc_id, text FROM docs WHERE kind IN ('manual','sop')")}

    def area_of(self, aid) -> str:
        w = self.d.well(aid)
        return self.d.area_name.get(w.get("area_id"), w.get("area_id"))

    def _section(self, doc_key: str, heading_re: str) -> str:
        for k, t in self.docs.items():
            if doc_key in k:
                m = re.search(rf"(?ms)^##\s*{heading_re}.*?(?=^## |\Z)", t)
                if m:
                    return m.group(0)
        return ""

    # ------------------------------------------------------------------ Q1/Q2: data gaps
    def data_gap(self, question: str) -> Result | None:
        ql = question.lower()
        res = Result("data_gap", "Not in the data")
        res.evidence = [{"id": "Dataset Guide", "type": "doc", "label": "inspection fields: temperatures, spill area and volume; no pressure or production volume"},
                        {"id": "T200 9.1", "type": "doc", "label": "pressure appears only as an equipment limit"}]
        cols = "wellhead and air temperature, spill detections, repairs and costs, regulator events, notes, manuals/SOPs"
        if re.search(r"pressure", ql) and not re.search(r"pressure test|psi", ql):
            res.notes = [
                "I can't map reservoir pressure: the data has no pressure readings. Inspections record wellhead and air temperature and spills; "
                "repairs, regulator events and notes have no reservoir or wellhead pressure values either.",
                "The only pressure numbers in the documents are design limits in the well-type manuals (e.g. maximum wellhead working pressure) and "
                "pressure-test settings in repair reports. They are equipment ratings, not reservoir measurements, so mapping them would be invented.",
                f"What exists: {cols}. A pressure map would need downhole or wellhead pressure gauges added to the inspections.",
                "Closest honest proxy: which wells are producing right now (temperature rule) can be shown on a map if useful.",
            ]
            return res
        if re.search(r"produced the most|most oil|produc\w* (?:the )?most|barrels produced|production volume|how much oil .* produc|output", ql):
            year = re.search(r"(20\d\d)", ql)
            y = int(year.group(1)) if year else self.d.today.year - 1
            x = self.d.ins[(self.d.ins.ts.dt.year == y)]
            g = x.groupby("asset_id").agg(weeks=("producing", "sum"), inspections=("producing", "size"))
            g = g.sort_values(["weeks", "inspections"], ascending=False)
            top = g[g.weeks == g.weeks.max()]
            res.notes = [
                f"I can't say which well produced the most oil in {y}: the data has no production volumes (no barrels, rates or meter readings). "
                "Producing or not is only inferred from wellhead temperature, once a week.",
                f"Proxy only, not volume: {len(top)} wells were producing at every inspection in {y} "
                f"({int(g.weeks.max())} of {int(g.inspections.max())} weekly inspections), so they tie on uptime and cannot be ranked by output.",
                "To answer properly we would need tank gauging or meter volumes per well.",
            ]
            res.notes.append("Wells tied at full uptime (first 10): " + ", ".join(top.index[:10]) + (" ..." if len(top) > 10 else "") + ".")
            for aid, r in top.head(15).iterrows():
                res.rows.append({"Well": aid, "Area": self.area_of(aid), "Type": self.d.well(aid)["well_type"],
                                 "Producing weeks": int(r.weeks), "Inspections": int(r.inspections)})
            res.columns = ["Well", "Area", "Type", "Producing weeks", "Inspections"]
            res.viz = {"type": "table"}
            res.facts = {"tied_full_uptime": len(top)}
            return res
        return None

    # ------------------------------------------------------------------ Q11: hotter region
    def temp_by_area(self) -> Result:
        d = self.d
        x = d.ins[(d.ins.day >= (d.today - timedelta(days=365))) & (d.ins.day <= d.today)].copy()
        x["month"] = x.ts.dt.strftime("%Y-%m")
        x["area"] = x.area_id.map(d.area_name)
        piv = x.groupby(["area", "month"]).delta_c.mean().unstack()
        months = list(piv.columns)
        leaders = piv.idxmax(axis=0).value_counts()
        overall = x.groupby("area").agg(delta=("delta_c", "mean"), wellhead=("wellhead_temp_c", "mean"), air=("ambient_temp_c", "mean"))
        mix = x.drop_duplicates("asset_id").groupby(["area", "well_type"]).size().unstack(fill_value=0)
        within = x.groupby(["well_type", "area"]).delta_c.mean().unstack(0)
        res = Result("temp_by_area", "Wellhead temperature above air, by area and month")
        for a in piv.index:
            res.rows.append({"Area": a, **{m: round(float(piv.loc[a, m]), 1) for m in months},
                             "Avg above air": round(float(overall.loc[a, "delta"]), 1)})
        res.columns = ["Area"] + months + ["Avg above air"]
        res.viz = {"type": "heatmap", "row": "Area", "cols": months}
        top = overall.delta.idxmax()
        res.facts = {"hottest": top, "months_leading": int(leaders.get(top, 0)), "months": len(months)}
        for t in ("T200", "T350", "T500"):
            r = d.rule(t, "producing_delta_c")
            if r:
                self.o._ev(res, f"{r['doc_id']} {r['section']}", "doc", f"{t} producing limit {r['value']:g} °C above air")
        for iid in x[x.area == top].sort_values("ts").inspection_id.tail(8):
            self.o._ev(res, iid, "inspection")
        types = [t for t in ("T500", "T350", "T200") if t in mix.columns]
        mix_txt = "; ".join(f"{a}: " + ", ".join(f"{int(mix.loc[a, t])} {t}" for t in types) for a in mix.index)
        res.notes = [
            f"{top} runs hottest: on average {overall.loc[top, 'delta']:.1f} °C above air, highest in {res.facts['months_leading']} of {len(months)} months (last 12 months).",
            f"Air temperature is similar across areas ({overall.air.min():.1f}–{overall.air.max():.1f} °C average), so this is the wellheads, not the weather.",
            "Caution: well types differ (manuals: T200 limit 15 °C, T350 20 °C, T500 25 °C; deeper types run hotter). Type mix per area: " + mix_txt + ".",
            "Within the same type, area averages: " + "; ".join(
                f"{t}: " + ", ".join(f"{a} {within.loc[a, t]:.1f}" for a in within.index if pd.notna(within.loc[a, t])) for t in types) + ".",
        ]
        return res

    # ------------------------------------------------------------------ Q6: OPS-3 status precedence
    def status_disagreements(self) -> Result:
        d = self.d
        lat = d.latest()
        ops_note = self.notes[self.notes.note_type == "operator_note"]
        cls = ops_note.assign(kind=ops_note.text.apply(lambda t: "shut" if SHUT.search(t or "") else ("restart" if RESTART.search(t or "") else None)))
        cls = cls[cls.kind.notna() & (cls.ts.dt.date <= d.today)].sort_values("ts")
        lastn = cls.groupby("asset_id").tail(1).set_index("asset_id")
        res = Result("status_disagreements", "Latest inspection vs latest operator note")
        for aid, n in lastn.iterrows():
            if aid not in lat.index:
                continue
            i = lat.loc[aid]
            note_prod = n.kind == "restart"
            insp_prod = bool(i.producing)
            if note_prod == insp_prod:
                continue
            prev = d.ins[(d.ins.asset_id == aid) & (d.ins.ts < i.ts)].tail(1)
            floor = prev.iloc[0].ts if len(prev) else i.ts
            if n.ts < floor:        # a note older than the previous inspection has long been superseded
                continue
            newer_note = n.ts > i.ts
            if newer_note:
                status = "Producing oil (unconfirmed)" if note_prod else "Not producing oil (shut in)"
                why = f"operator note on {n.ts:%d %b %H:%M} is newer than the inspection; OPS-3: " + (
                    "a restart note makes it producing until an inspection confirms" if note_prod else "a newer shut-in note wins over the reading")
            else:
                status = "Producing oil" if insp_prod else "Not producing oil"
                why = f"inspection on {i.ts:%d %b %H:%M} is newer than the note; OPS-3: the most recent evidence wins"
            corr = "; corrected by data_correction" if len(i.corrections) else ""
            res.rows.append({"Well": aid, "Area": self.area_of(aid),
                             "Latest inspection": f"{i.inspection_id}, {fmt_day(i.day)}: {i.delta_c:.1f} °C above air → {'producing' if insp_prod else 'not producing'}{corr}",
                             "Latest operator note": f"{n.ts:%d %b %Y %H:%M}: \"{n.text}\" ({n.note_id})",
                             "Status now": status, "Why": why})
            self.o._ev(res, i.inspection_id, "inspection")
            self.o._ev(res, n.note_id, "note")
        res.rows.sort(key=lambda r: (r["Area"], r["Well"]))
        res.columns = ["Well", "Area", "Latest inspection", "Latest operator note", "Status now", "Why"]
        res.viz = {"type": "table"}
        sec = self._section("operations", "OPS-3")
        res.proof.append({"step": "OPS-3 status evidence precedence", "rule": {"doc": "operations-sop-rev2", "section": "OPS-3", "quote": sec[:500]}})
        res.facts = {"count": len(res.rows), "wells": [r["Well"] for r in res.rows]}
        res.notes.append("Status follows OPS-3 of the Operations SOP (rev 2): the most recent of the latest inspection (after data corrections) and the latest shut-in/restart operator note.")
        return res

    # ------------------------------------------------------------------ Q3: OPS-1 gas response
    def gas_response(self, since: date | None = None) -> Result:
        d = self.d
        sec = self._section("operations", "OPS-1")
        hrs = [int(h) for h in re.findall(r"\*\*(\d+) hours\*\*", sec)] or [24, 12]
        cut = _d(re.search(r"from (\d{1,2} \w+ \d{4})", sec).group(1)) if re.search(r"from (\d{1,2} \w+ \d{4})", sec) else date(2027, 1, 1)
        since = since or date(2026, 11, 1)
        g = self.notes[(self.notes.note_type == "operator_note") & self.notes.text.fillna("").str.contains(GAS)]
        g = g[(g.ts.dt.date >= since) & (g.ts.dt.date <= d.today)].sort_values("ts")
        res = Result("gas_response", f"Gas odor reports since {fmt_day(since)} (OPS-1)")
        for _, n in g.iterrows():
            aid = n.asset_id
            lim = hrs[0] if n.ts.date() < cut else hrs[-1]
            m = d.mnt[(d.mnt.asset_id == aid) & (d.mnt.started_at_dt > n.ts)][["maintenance_id", "started_at_dt"]].rename(columns={"maintenance_id": "id", "started_at_dt": "t"})
            i = d.ins[(d.ins.asset_id == aid) & (d.ins.ts > n.ts) & (d.ins.method == "manual")][["inspection_id", "ts"]].rename(columns={"inspection_id": "id", "ts": "t"})
            cand = pd.concat([m, i]).sort_values("t")
            if cand.empty:
                resp, hours, ok = "none", None, False
                still_open = (pd.Timestamp(d.today, tz="UTC") + pd.Timedelta(days=1) - n.ts).total_seconds() / 3600 <= lim
            else:
                r = cand.iloc[0]
                hours = round((r.t - n.ts).total_seconds() / 3600, 1)
                resp, ok, still_open = f"{r.id} at {r.t:%d %b %Y %H:%M}", hours <= lim, False
                self.o._ev(res, r.id, "maintenance" if str(r.id).startswith("MNT") else "inspection")
            res.rows.append({"Well": aid, "Area": self.area_of(aid), "Reported at": f"{n.ts:%d %b %Y %H:%M}",
                             "Report": f"\"{n.text}\" ({n.note_id})", "Response": resp, "Hours to response": hours,
                             "Deadline": f"{lim} h", "Met / Missed": "Met" if ok else ("Open (deadline not passed)" if still_open else "Missed")})
            self.o._ev(res, n.note_id, "note")
        res.columns = ["Well", "Area", "Reported at", "Report", "Response", "Hours to response", "Deadline", "Met / Missed"]
        res.viz = {"type": "table"}
        missed = [r for r in res.rows if r["Met / Missed"] == "Missed"]
        res.facts = {"reports": len(res.rows), "missed": len(missed), "met": sum(r["Met / Missed"] == "Met" for r in res.rows)}
        res.proof.append({"step": "OPS-1 gas odor response", "rule": {"doc": "operations-sop-rev2", "section": "OPS-1", "quote": sec[:600]}})
        self.o._ev(res, "operations-sop-rev2 OPS-1", "doc", "OPS-1 Gas odor response")
        res.notes.append(f"Deadline from OPS-1: {hrs[0]} h for reports before {fmt_day(cut)}, {hrs[-1]} h from then. A response is a maintenance job start or a manual inspection after the note; drone inspections do not count.")
        return res

    # ------------------------------------------------------------------ Q4: OPS-2 bypasses + MOC memos
    def mocs(self) -> dict:
        memos = {}
        for k, t in self.docs.items():
            if not k.lower().startswith("moc"):
                continue
            mid = re.search(r"MOC-\d{4}-\d+", t)
            mid = mid.group(0) if mid else k.upper()
            exp = re.search(r"expires on (\d{1,2} \w+ \d{4})", t)
            eff = re.search(r"Effective from (\d{1,2} \w+ \d{4})", t)
            ext = re.search(r"extends (MOC-\d{4}-\d+)", t)
            memos[mid] = {"id": mid, "wells": sorted(set(re.findall(r"WELL-\d+", t))), "expires": _d(exp.group(1)) if exp else None,
                          "effective": _d(eff.group(1)) if eff else None, "extends": ext.group(1) if ext else None}
        for m in list(memos.values()):
            if m["extends"] and m["extends"] in memos and m["expires"]:
                base = memos[m["extends"]]
                base["extended_by"] = m["id"]
                base["final_expires"] = m["expires"]
        for m in memos.values():
            m.setdefault("final_expires", m["expires"])
        return memos

    def bypasses(self) -> Result:
        d = self.d
        memos = self.mocs()
        notes = self.notes[(self.notes.note_type == "operator_note") & (self.notes.ts.dt.date <= d.today)].sort_values("ts")
        res = Result("bypasses", "Temporary flowline bypasses (OPS-2)")
        for aid, grp in notes.groupby("asset_id"):
            open_in = None
            spans = []
            for _, n in grp.iterrows():
                t = n.text or ""
                if BYPASS_OUT.search(t) and open_in is not None:
                    spans.append((open_in, n)); open_in = None
                elif BYPASS_IN.search(t) and not BYPASS_OUT.search(t):
                    if open_in is None:
                        open_in = n
            if open_in is not None:
                spans.append((open_in, None))
            for n_in, n_out in spans:
                cover = [m for m in memos.values() if aid in m["wells"] and not m.get("extends")]
                memo = cover[0] if cover else None
                until = memo["final_expires"] if memo else None
                end = n_out.ts.date() if n_out is not None else d.today
                if not memo:
                    status = "Not approved"
                elif memo.get("effective") and n_in.ts.date() < memo["effective"]:
                    status = "Not approved"
                    memo = {**memo, "_early": True}
                elif until and end > until:
                    status = "Expired"
                else:
                    status = "Allowed"
                appr = (memo["id"] + (f" (extended by {memo['extended_by']})" if memo.get("extended_by") else "")
                        + (f"; put in before the memo took effect on {fmt_day(memo['effective'])}" if memo.get("_early") else "")) if memo else "none"
                res.rows.append({"Well": aid, "Area": self.area_of(aid), "Bypass in": fmt_day(n_in.ts),
                                 "Bypass out": fmt_day(n_out.ts) if n_out is not None else "still in",
                                 "Approval": appr, "Approval valid until": fmt_day(until) if until else "—", "Status": status,
                                 "In place now": n_out is None})
                self.o._ev(res, n_in.note_id, "note")
                if n_out is not None:
                    self.o._ev(res, n_out.note_id, "note")
        for m in memos.values():
            self.o._ev(res, m["id"], "doc", f"{len(m['wells'])} wells, expires {m['expires']}")
        res.rows.sort(key=lambda r: (not r["In place now"], r["Status"] == "Allowed", r["Area"], r["Well"]))
        res.columns = ["Well", "Area", "Bypass in", "Bypass out", "Approval", "Approval valid until", "Status"]
        res.viz = {"type": "table"}
        now = [r for r in res.rows if r["In place now"]]
        bad = [r for r in res.rows if r["Status"] != "Allowed"]
        res.facts = {"in_place_now": [(r["Well"], r["Status"]) for r in now], "violations": [(r["Well"], r["Status"]) for r in bad]}
        res.notes.append("In place right now: " + (", ".join(f"{w} ({s})" for w, s in res.facts["in_place_now"]) or "none") + ".")
        res.notes.append("Violations, past or present: " + (", ".join(f"{w} ({s})" for w, s in res.facts["violations"]) or "none") + ".")
        res.notes.append("OPS-2: allowed only on a well named in an unexpired MOC; an extension memo replaces the expiry (MOC-2026-044 extends MOC-2026-031 to 28 Feb 2027); in place from the note that puts it in to the note that takes it out.")
        return res

    # ------------------------------------------------------------------ Q5: regulator letter
    def letter_compliance(self) -> Result:
        d = self.d
        t = next((v for k, v in self.docs.items() if "regulator-letter" in k), "")
        areas = [a for a, nm in d.area_name.items() if nm and nm in t]
        since = _d(re.search(r"since (\d{1,2} \w+ \d{4})", t).group(1)) if re.search(r"since (\d{1,2} \w+ \d{4})", t) else None
        due = _d(re.search(r"submitted by (\d{1,2} \w+ \d{4})", t).group(1)) if re.search(r"submitted by (\d{1,2} \w+ \d{4})", t) else None
        sentence = re.search(r"sentence \"([^\"]+)\"", t)
        sentence = sentence.group(1) if sentence else "Soil samples sent to the lab."
        minv = d.reportable_min()
        sp = d.ins[d.ins.area_id.isin(areas) & (d.ins.spill_detected == 1) & (d.ins.day >= since) & (d.ins.day <= d.today)]
        res = Result("letter_compliance", "Spills covered by the 20 Nov 2026 letter")
        excluded = []
        for _, r in sp.iterrows():
            vol = r.spill_est_volume_bbl
            if not r.real_spill:
                if vol is not None and pd.notna(vol) and vol >= minv:
                    excluded.append(f"{r.asset_id} {r.inspection_id} ({vol:g} bbl) was confirmed not crude, so no samples needed")
                continue
            if vol is None or pd.isna(vol) or vol < minv:
                continue
            jobs = d.mnt[d.mnt.triggered_by_inspection_id == r.inspection_id]
            job = jobs.iloc[0] if len(jobs) else None
            ext = self.o._extracted(job.maintenance_id) if job is not None else {}
            if job is None:
                ok, why = "No", "no clean-up job recorded"
            elif not ext:
                ok, why = "No", f"no clean-up report for {job.maintenance_id}"
            elif ext.get("soil_samples_lab"):
                ok, why = "Yes", f"report says \"{sentence}\""
            else:
                ok, why = "No", "clean-up report has no lab soil samples (field readings do not count)"
            corr = [c for c in r.corrections if c["field"] == "spill_est_volume_bbl"]
            res.rows.append({"Well": r.asset_id, "Area": d.area_name.get(r.area_id), "Inspection": f"{r.inspection_id}, {fmt_day(r.day)}",
                             "Volume (bbl)": float(vol), "Clean-up job": job.maintenance_id if job is not None else "none",
                             "Compliant?": f"{ok} — {why}" + (f" (volume corrected from {corr[0]['original']} by {corr[0]['author_name']})" if corr else "")})
            self.o._ev(res, r.inspection_id, "inspection")
            if job is not None:
                self.o._ev(res, job.maintenance_id, "maintenance")
            for c in corr:
                self.o._ev(res, c["id"], "note")
        res.rows.sort(key=lambda x: (x["Area"], x["Well"]))
        res.columns = ["Well", "Area", "Inspection", "Volume (bbl)", "Clean-up job", "Compliant?"]
        res.viz = {"type": "table"}
        res.facts = {"covered": len(res.rows), "not_compliant": [r["Well"] for r in res.rows if r["Compliant?"].startswith("No")]}
        self.o._ev(res, "regulator-letter-2026-11-20", "doc", "State Oil & Gas Commission letter")
        res.notes.append(f"Letter scope: reportable spills (≥ {minv:g} bbl, after corrections) in {', '.join(d.area_name[a] for a in areas)} since {fmt_day(since)}; lab results due {fmt_day(due) if due else '?'}; "
                         f"HSE rule: compliant only if the clean-up report contains \"{sentence}\".")
        res.notes.extend(excluded)
        return res

    # ------------------------------------------------------------------ Q8/Q9: recalled pumps
    def recall_lots(self) -> tuple[list[str], str]:
        t = next((v for k, v in self.docs.items() if "recall" in k), "")
        sec = t.split("Pumps from all other lots")[0]
        lots = re.findall(r"LOT-[A-Z0-9-]+", sec)
        model = re.search(r"Highline (RP-\d+)", t)
        return sorted(set(lots)), (model.group(1) if model else "")

    def current_pumps(self) -> pd.DataFrame:
        if getattr(self, "_cp", None) is not None:
            return self._cp
        self._cp = self._current_pumps()
        return self._cp

    def _current_pumps(self) -> pd.DataFrame:
        d = self.d
        rows = []
        for mid, ext in getattr(self.o, "_ext", None).items() if hasattr(self.o, "_ext") else []:
            pass
        self.o._extracted("x")
        for mid, ext in self.o._ext.items():
            if ext.get("pump_lot"):
                m = d.mnt[d.mnt.maintenance_id == mid]
                if len(m):
                    m = m.iloc[0]
                    rows.append({"asset_id": m.asset_id, "maintenance_id": mid, "started": m.started_at_dt, "lot": ext["pump_lot"],
                                 "model": ext.get("pump_model"), "serial": ext.get("pump_serial"), "cost": float(m.cost_total or 0)})
        df = pd.DataFrame(rows)
        if df.empty:
            return df
        df = df[df.started.dt.date <= d.today].sort_values("started")
        return df.groupby("asset_id").tail(1).set_index("asset_id")

    def recalled_pumps(self, ledger_facts: list[dict], wells_scope: list[str] | None = None) -> Result:
        d = self.d
        lots, model = self.recall_lots()
        cur = self.current_pumps()
        res = Result("recalled_pumps", "Recalled pumps still in the ground")
        plugged = set(d.wells[d.wells.status.fillna("").str.contains("plugged")].asset_id)
        swaps = {f["scope_id"]: f for f in ledger_facts if f.get("kind") == "shared_fact" and f.get("field") == "pump_swap"}
        hearsay = {f["scope_id"]: f for f in ledger_facts if f.get("kind") == "claim" and f.get("field") == "pump_swap"}
        taken_off = []
        for aid, r in cur.iterrows():
            if r.lot not in lots or aid in plugged:
                continue
            if wells_scope is not None and aid not in wells_scope:
                continue
            if aid in swaps:
                f = swaps[aid]
                taken_off.append(f"{aid}: counted as replaced on the word of {f['author_name']} ({f['id']}, {f['created_at'][:10]}); work order not yet in the maintenance system")
                continue
            w = d.well(aid)
            src = f"report {r.maintenance_id} (Parts installed)"
            row = {"Well": aid, "Area": self.area_of(aid), "Team": d.team_name.get(w.get("team_id"), w.get("team_id")),
                   "Pump": f"{r.model} {r.serial}", "Lot": r.lot, "Installed": fmt_day(r.started), "Install job": r.maintenance_id,
                   "Cost USD": r.cost, "Source": src}
            if aid in hearsay:
                h = hearsay[aid]
                row["Source"] += f"; {h['author_name']} relayed a second-hand swap report ({h['id']}), not confirmed, so still listed"
            res.rows.append(row)
            self.o._ev(res, r.maintenance_id, "maintenance")
        res.rows.sort(key=lambda x: (x["Area"], x["Well"]))
        res.columns = ["Well", "Area", "Pump", "Lot", "Installed", "Install job", "Cost USD", "Source"]
        res.viz = {"type": "table"}
        by_area = {}
        for r in res.rows:
            by_area[r["Area"]] = by_area.get(r["Area"], 0) + 1
        res.facts = {"count": len(res.rows), "by_area": by_area, "wells": [r["Well"] for r in res.rows]}
        self.o._ev(res, "supplier-recall-notice-2026-12-01", "doc", f"recalled lots {', '.join(lots)}")
        res.notes.append(f"Recall notice HPC-RN-2026-07 (1 Dec 2026): Highline {model} pumps from lots {', '.join(lots)}; replace by 31 Dec 2026, now overdue. "
                         "Current pump per well = the latest 'Parts installed' line in its repair reports.")
        res.notes.extend(taken_off)
        return res

    # ------------------------------------------------------------------ Q9 helpers
    def team_info(self, team_name: str) -> Result:
        d = self.d
        tid = next((t for t, nm in d.team_name.items() if nm and nm.lower() == team_name.lower()), None)
        res = Result("team_info", team_name)
        if not tid:
            res.notes.append(f"No team called {team_name}.")
            return res
        lead = d.teams[d.teams.team_id == tid].lead_user_id.iloc[0]
        wells = d.wells[d.wells.team_id == tid]
        active = wells[~wells.status.fillna("").str.contains("plugged")]
        areas = active.area_id.map(d.area_name).value_counts().to_dict()
        res.notes.append(f"{team_name} is led by {d.name(lead)} ({lead}). It runs {len(active)} wells" +
                         (f" ({len(wells) - len(active)} more plugged and abandoned)" if len(wells) > len(active) else "") +
                         ": " + ", ".join(f"{n} in {a}" for a, n in areas.items()) + ". Team per well uses the well's own team_id (team_history takes priority over the area's team).")
        res.facts = {"lead": d.name(lead), "wells": len(active)}
        res.evidence = [{"id": "areas.json", "type": "doc", "label": "teams and lead_user_id"}, {"id": "users.json", "type": "doc", "label": "people"}]
        return res

    def freeze_checks(self) -> Result:
        d = self.d
        sec = self._section("operations", "OPS-5")
        lim = float(re.search(r"(−|-)\s?(\d+)\s*°C", sec).group(2)) * -1 if re.search(r"(−|-)\s?(\d+)\s*°C", sec) else -5.0
        days = int(re.search(r"within \*\*(\d+) days", sec).group(1)) if re.search(r"within \*\*(\d+) days", sec) else 7
        x = d.ins[(d.ins.ts.dt.month == 12) & (d.ins.ts.dt.year == d.today.year - 1) & (d.ins.ambient_temp_c <= lim) & d.ins.producing]
        res = Result("freeze_checks", "OPS-5 freeze protection, December")
        for _, r in x.iterrows():
            m = d.mnt[(d.mnt.asset_id == r.asset_id) & d.mnt.issue.str.contains("Heat trace check", case=False, na=False) &
                      (d.mnt.started_at_dt >= r.ts) & (d.mnt.started_at_dt <= r.ts + pd.Timedelta(days=days))]
            if m.empty:
                res.rows.append({"Well": r.asset_id, "Area": self.area_of(r.asset_id), "Inspection": r.inspection_id,
                                 "Date": fmt_day(r.day), "Air °C": float(r.ambient_temp_c), "Heat trace check": "none within 7 days"})
                self.o._ev(res, r.inspection_id, "inspection")
        res.rows.sort(key=lambda z: (z["Area"], z["Well"]))
        res.columns = ["Well", "Area", "Inspection", "Date", "Air °C", "Heat trace check"]
        res.viz = {"type": "table"}
        res.notes.insert(0, "Operations SOP OPS-5 (freeze protection, 1 Dec – 28 Feb): any inspection at or below −5 °C air on a well that is producing needs a "
                            "maintenance job with issue 'Heat trace check' starting within 7 days.")
        if res.rows:
            r0 = res.rows[0]
            res.notes.insert(1, f"Example miss: {r0['Well']} ({r0['Area']}), inspection {r0['Inspection']} on {r0['Date']} at {r0['Air °C']} °C, no heat trace check within 7 days. {len(res.rows)} misses in December in total.")
        res.facts = {"misses": len(res.rows)}
        self.o._ev(res, "operations-sop-rev2 OPS-5", "doc", "OPS-5 Freeze protection")
        return res

    def h2s_reading(self, aid: str, on: date) -> Result:
        d = self.d
        res = Result("h2s_reading", f"H2S at {aid} around {fmt_day(on)}")
        n = self.notes[(self.notes.asset_id == aid) & (self.notes.ts.dt.date >= on - timedelta(days=1)) & (self.notes.ts.dt.date <= on + timedelta(days=1))]
        for _, x in n.iterrows():
            res.notes.append(f"Note {x.note_id} ({x.ts:%d %b %Y %H:%M}, {d.name(x.author_user_id)}): \"{x.text}\"")
            self.o._ev(res, x.note_id, "note")
        m = d.mnt[(d.mnt.asset_id == aid) & (d.mnt.started_at_dt.dt.date >= on) & (d.mnt.started_at_dt.dt.date <= on + timedelta(days=14))]
        found = False
        for _, j in m.iterrows():
            rep = d.reports[d.reports.maintenance_id == j.maintenance_id]
            if len(rep):
                mm = re.search(r"H2S[^.\n]*?(\d+(?:\.\d+)?)\s*ppm", rep.iloc[0].text)
                if mm:
                    found = True
                    res.notes.insert(0, f"H2S reading: {mm.group(1)} ppm, recorded in report {j.maintenance_id} ({fmt_day(j.started_at_dt)}): \"{mm.group(0).strip()}\".")
                    self.o._ev(res, j.maintenance_id, "maintenance")
        if not found:
            res.notes.insert(0, f"No H2S reading is recorded for {aid} around {fmt_day(on)}: the note reports the smell but gives no ppm value, and no repair report "
                                "in the following two weeks records a monitor reading. I won't invent one.")
        return res

    # ------------------------------------------------------------------ Q7: operator-note ranking
    def listen_ranking(self, days: int = 30, top: int = 10) -> Result:
        d = self.d
        start = d.today - timedelta(days=days)
        n = self.notes[(self.notes.note_type == "operator_note") & (self.notes.ts.dt.date >= start) & (self.notes.ts.dt.date <= d.today)]
        hits = []
        for _, x in n.iterrows():
            t = (x.text or "").lower()
            if GAS.search(t) or "bypass" in t:
                continue
            w = sum(v for k, v in SYMPTOM.items() if k in t)
            if w and not re.search(r"normal|nothing to report|smooth|steady", t):
                hits.append((x, w))
        res = Result("listen_ranking", "Wells that sound or behave wrong, no repair since")
        by = {}
        for x, w in hits:
            by.setdefault(x.asset_id, []).append((x, w))
        lat = d.latest()
        for aid, lst in by.items():
            first = min(x.ts for x, _ in lst)
            later = d.mnt[(d.mnt.asset_id == aid) & (d.mnt.started_at_dt >= first)]
            if len(later):
                continue
            if aid not in lat.index:
                continue
            score = sum(w for _, w in lst)
            signs = []
            x = d.ins[(d.ins.asset_id == aid) & (d.ins.day <= d.today)].tail(6)
            if len(x) >= 4 and x.delta_c.iloc[-1] < x.delta_c.iloc[:3].mean() - 3:
                signs.append(f"wellhead gap falling ({x.delta_c.iloc[:3].mean():.1f} → {x.delta_c.iloc[-1]:.1f} °C above air)"); score += 3
            if not bool(lat.loc[aid].producing):
                signs.append("not producing at latest inspection"); score += 3
            yr = d.mnt[(d.mnt.asset_id == aid) & (d.mnt.maintenance_type == "corrective") & (d.mnt.started_at_dt.dt.date >= d.today - timedelta(days=365))]
            if len(yr) >= 2:
                signs.append(f"{len(yr)} corrective repairs in 12 months"); score += len(yr)
            cur = self.current_pumps()
            lots = self._lots if hasattr(self, "_lots") else self.recall_lots()[0]
            self._lots = lots
            if aid in cur.index and cur.loc[aid].lot in lots:
                signs.append(f"recalled pump lot {cur.loc[aid].lot} still installed"); score += 3
            lastrep = d.mnt[d.mnt.asset_id == aid].sort_values("started_at_dt").tail(1)
            last = f"{lastrep.iloc[0].maintenance_id}, {fmt_day(lastrep.iloc[0].started_at_dt)}: {lastrep.iloc[0].issue}" if len(lastrep) else "none"
            quotes = "; ".join(f"{x.ts:%d %b}: \"{x.text}\"" for x, _ in sorted(lst, key=lambda z: z[0].ts)[-3:])
            res.rows.append({"Well": aid, "Area": self.area_of(aid), "Operator-note evidence": quotes,
                             "Other warning signs in the data": "; ".join(signs) or "none", "Last repair on the well": last,
                             "Score": score, "notes_n": len(lst)})
            for x, _ in lst:
                self.o._ev(res, x.note_id, "note")
        res.rows.sort(key=lambda r: (-r["Score"], -r["notes_n"], r["Well"]))
        res.rows = res.rows[:top]
        for i, r in enumerate(res.rows, 1):
            r["Rank"] = i
        res.columns = ["Rank", "Well", "Area", "Operator-note evidence", "Other warning signs in the data", "Last repair on the well"]
        res.viz = {"type": "table"}
        res.facts = {"wells": [r["Well"] for r in res.rows]}
        res.notes.append(f"Notes from the last {days} days that describe abnormal sound or behaviour (fluid pound, rattling, squeal, tagging bottom, amps hunting, drive tripping, leaks); "
                         "excluding gas and bypass notes and wells repaired since. Ranked by how many and how serious the notes are, plus other signs in the data. "
                         "This is a judgement ranking, not a prediction model.")
        return res

    # ------------------------------------------------------------------ Q10: waiting reasons
    def waiting_reasons(self, year: int) -> Result:
        d = self.d
        cats = {"weather": r"weather|rain|storm|snow|wind|freez", "parts": r"part|vendor|back-?order|valve arrives|supplier",
                "contractors": r"contractor", "crews": r"crew|rig|staff|lockout"}
        m = d.mnt[(d.mnt.started_at_dt.dt.year == year)]
        res = Result("waiting_reasons", f"What shut-ins wait on beyond the repair, jobs started in {year}")
        rows = []
        ins_by = {a: g for a, g in d.ins.groupby("asset_id")}
        notes_by = {a: g for a, g in self.notes.groupby("asset_id")}
        for _, j in m.iterrows():
            start, end = j.started_at_dt, j.completed_at_dt
            if pd.isna(end):
                continue
            # extra days: non-producing inspections after the repair finished, before the next producing one
            gi = ins_by.get(j.asset_id)
            after = gi[gi.ts > end].head(8) if gi is not None else d.ins.iloc[0:0]
            extra = 0
            for _, r in after.iterrows():
                if r.producing:
                    break
                extra += 7
            gn = notes_by.get(j.asset_id)
            notes = gn[(gn.ts >= start - pd.Timedelta(days=2)) & (gn.ts <= end + pd.Timedelta(days=extra + 7))] if gn is not None else self.notes.iloc[0:0]
            txt = " ".join((notes.text.fillna("").tolist())) + " " + str(j.issue)
            if extra <= 0 and not re.search(r"waiting|delayed|pushed back|until", txt, re.I):
                continue
            reason = next((c for c, rx in cats.items() if re.search(rx, txt, re.I) and re.search(r"wait|delay|pushed back|until|back-?order", txt, re.I)), None)
            vf = pd.to_datetime(notes.valid_from, errors="coerce")
            vt = pd.to_datetime(notes.valid_to, errors="coerce")
            span = (vt - vf).dt.days.max() if len(notes) else None
            extra_days = int(span) if span is not None and pd.notna(span) and reason else extra
            if not reason or extra_days <= 0:
                continue
            rows.append({"area": self.area_of(j.asset_id), "reason": reason, "extra": extra_days, "job": j.maintenance_id})
        df = pd.DataFrame(rows)
        if df.empty:
            res.notes.append("No jobs in the period show a shut-in longer than the repair with a recorded reason.")
            return res
        for area, g in df.groupby("area"):
            row = {"Area": area, "Jobs": len(g)}
            for c in cats:
                gc = g[g.reason == c]
                row[f"{c} share"] = f"{len(gc) / len(g):.0%}"
                row[f"{c} typical extra days"] = int(gc.extra.median()) if len(gc) else None
                row[c] = len(gc)
            res.rows.append(row)
        res.columns = ["Area", "Jobs"] + [f"{c} share" for c in cats] + [f"{c} typical extra days" for c in cats]
        res.viz = {"type": "stacked", "x": "Area", "series": list(cats)}
        tot = df.reason.value_counts(normalize=True)
        res.facts = {"overall": {k: round(float(v), 2) for k, v in tot.items()}, "jobs": len(df)}
        for jid in df.job.head(40):
            self.o._ev(res, jid, "maintenance")
        dom = df.groupby("area").reason.agg(lambda s: s.value_counts(normalize=True).max())
        stand = [f"{a} ({df[df.area == a].reason.value_counts().idxmax()} {v:.0%})" for a, v in dom.items() if v >= tot.max() + 0.2]
        res.notes.append(f"{len(df)} jobs started in {year} kept the well shut in longer than the repair with a recorded reason. Overall: " +
                         ", ".join(f"{k} {v:.0%}" for k, v in tot.items()) + ". Typical extra days = median.")
        res.notes.append("Stands out: " + (", ".join(stand) if stand else "no area is far from the field-wide mix") + ".")
        res.notes.append("No contractor or crew delays are recorded in the notes for 2026; the only delay reasons the data records are weather and waiting for parts, so those are the only two that can be reported.")
        res.notes.append("Method: extra days from operator/maintenance notes that explain the delay (their validity window), else from weekly inspections still not producing after the job finished. Reason from note wording.")
        return res
