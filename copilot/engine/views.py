"""Derived views over the raw data plus ledger overlays. Pure pandas; every rule value comes from the rules table."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date, timedelta

import pandas as pd

from .. import db, rules
from ..config import TODAY


@dataclass
class Overlays:
    """Ledger facts relevant to derivation (filled by copilot.memory)."""
    data_corrections: list[dict] = field(default_factory=list)      # {id, target(inspection_id), field, original, value, author, reason}
    rule_overrides: list[dict] = field(default_factory=list)        # {id, scope_type, scope_id, key, equipment_kind, value, author, reason}
    well_facts: list[dict] = field(default_factory=list)            # shared_fact / claim rows from the ledger


class Data:
    def __init__(self, overlays: Overlays | None = None, today: date = TODAY):
        self.today = today
        self.ov = overlays or Overlays()
        with db.session() as con:
            q = lambda s: pd.read_sql_query(s, con)
            self.wells = q("SELECT * FROM wells")
            self.users = q("SELECT * FROM users")
            self.areas = q("SELECT * FROM areas")
            self.teams = q("SELECT * FROM teams")
            self.mnt = q("SELECT * FROM maintenance")
            self.reg = q("SELECT * FROM reg_events")
            self.notes = q("SELECT * FROM notes")
            self.rules = q("SELECT * FROM rules")
            self.reports = q("SELECT maintenance_id, asset_id, path, text FROM reports")
            ins = q("SELECT * FROM inspections")
        self.user_name = dict(zip(self.users.user_id, self.users.name))
        self.area_name = dict(zip(self.areas.area_id, self.areas.name))
        self.team_name = dict(zip(self.teams.team_id, self.teams.name))
        for df, col in ((self.mnt, "started_at"), (self.mnt, "completed_at")):
            df[col + "_dt"] = pd.to_datetime(df[col], utc=True, errors="coerce")
        self.reg["date_dt"] = pd.to_datetime(self.reg["date"], errors="coerce")
        self.ins = self._derive(ins)

    # ---------- rules ----------
    def rule(self, well_type: str | None, key: str):
        r = self.rules[(self.rules.scope == well_type) & (self.rules.key == key)]
        if r.empty:
            r = self.rules[(self.rules.scope == "fleet") & (self.rules.key == key)]
        return None if r.empty else r.iloc[0].to_dict()

    def rule_value(self, well_type, key, default=None):
        r = self.rule(well_type, key)
        return default if r is None or pd.isna(r["value"]) else float(r["value"])

    def spill_class(self, bbl: float | None) -> str | None:
        if bbl is None or pd.isna(bbl):
            return None
        rows = self.rules[self.rules.key.str.startswith("spill_class.")].copy()
        rows["cls"] = rows.key.str.split(".").str[1]
        rows = rows.sort_values("value")
        cls = None
        for _, r in rows.iterrows():
            if bbl >= r["value"]:
                cls = r["cls"]
        return cls

    def reportable_min(self) -> float:
        r = self.rule(None, "spill_class.reportable.min_bbl")
        return float(r["value"]) if r else 5.0

    # ---------- inspections ----------
    def _derive(self, ins: pd.DataFrame) -> pd.DataFrame:
        ins = ins.merge(self.wells[["asset_id", "well_type", "area_id", "lat", "lon"]], on="asset_id", how="left")
        ins["ts"] = pd.to_datetime(ins.inspected_at, utc=True)
        ins["day"] = ins.ts.dt.date
        ins["orig_wellhead_temp_c"] = ins.wellhead_temp_c
        ins["orig_ambient_temp_c"] = ins.ambient_temp_c
        ins["orig_volume_bbl"] = ins.spill_est_volume_bbl
        ins["corrections"] = [[] for _ in range(len(ins))]
        idx = {k: i for i, k in enumerate(ins.inspection_id)}
        # runtime ledger corrections (raw data or AI analysis)
        for c in self.ov.data_corrections:
            i = idx.get(c["target"])
            if i is None:
                continue
            col = {"wellhead_temp_c": "wellhead_temp_c", "ambient_temp_c": "ambient_temp_c",
                   "spill_est_volume_bbl": "spill_est_volume_bbl", "spill_detected": "spill_detected"}.get(c["field"])
            if col:
                ins.at[i, col] = c["value"]
                ins.at[i, "corrections"].append(c)
        thr = {t: self.rule_value(t, "producing_delta_c") for t in ins.well_type.dropna().unique()}
        ins["threshold_c"] = ins.well_type.map(thr)
        ins["delta_c"] = (ins.wellhead_temp_c - ins.ambient_temp_c).round(2)
        ins["producing"] = ins.delta_c >= ins.threshold_c
        # dataset corrections: a correction note naming an inspection overrides the detection
        corr = self.notes[(self.notes.note_type == "correction") & self.notes.inspection_id.notna()]
        corr_map = dict(zip(corr.inspection_id, corr.note_id))
        ins["correction_note"] = ins.inspection_id.map(corr_map)
        runtime_neg = {c["target"] for c in self.ov.data_corrections if c["field"] == "spill_detected" and not c["value"]}
        ins["real_spill"] = (ins.spill_detected == 1) & ins.correction_note.isna() & ~ins.inspection_id.isin(runtime_neg)
        ins["spill_class"] = [self.spill_class(v) if s else None for v, s in zip(ins.spill_est_volume_bbl, ins.real_spill)]
        return ins.sort_values(["asset_id", "ts"]).reset_index(drop=True)

    def latest(self) -> pd.DataFrame:
        """'Right now' = each well's latest inspection on or before today."""
        cur = self.ins[self.ins.day <= self.today]
        return cur.groupby("asset_id").tail(1).set_index("asset_id")

    # ---------- helpers ----------
    def name(self, uid):
        return self.user_name.get(uid, uid)

    def well(self, aid) -> dict:
        r = self.wells[self.wells.asset_id == aid]
        return {} if r.empty else r.iloc[0].to_dict()

    def area_id(self, text: str) -> str | None:
        t = text.strip().lower()
        for aid, nm in self.area_name.items():
            if t in (aid.lower(), (nm or "").lower()):
                return aid
        return None

    def window(self, n: int, unit: str) -> tuple[date, date]:
        """Period ending today. 'last 4 months' on 17 Oct = 16 Jun..16 Oct (inclusive, compared by date)."""
        end = self.today - timedelta(days=1)
        if unit.startswith("day"):
            start = self.today - timedelta(days=n)
        elif unit.startswith("week"):
            start = self.today - timedelta(days=7 * n)
        elif unit.startswith("month"):
            start = (pd.Timestamp(self.today) - pd.DateOffset(months=n) - pd.Timedelta(days=1)).date()
        else:
            start = (pd.Timestamp(self.today) - pd.DateOffset(years=n)).date()
        return start, end
