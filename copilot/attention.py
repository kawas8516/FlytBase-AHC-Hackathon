"""Proactive feed: problems nobody asked about yet. Same operators as the answers, so they never disagree."""
from __future__ import annotations

from .engine.ops import Ops, fmt_day


def feed(ops: Ops, limit: int = 40) -> list[dict]:
    d = ops.d
    out = []
    lat = d.latest()
    for aid, row in lat.iterrows():
        w = d.well(aid)
        if not row.producing:
            why = ops.explain_down(aid, row)
            if not why["reasons"]:
                out.append({"severity": "high", "kind": "Down, no recorded reason", "well": aid,
                            "detail": f"{row.delta_c:.1f} °C above air on {fmt_day(row.day)}"
                                      + (f"; inspector: \"{why['remark']}\"" if why["remark"] else ""),
                            "ask": f"Is {aid} producing oil right now?"})
        if (w["recorded_status"] == "active") != bool(row.producing):
            out.append({"severity": "low", "kind": "Recorded status out of date", "well": aid,
                        "detail": f"System says {w['recorded_status']}, latest inspection says {'producing' if row.producing else 'not producing'}",
                        "ask": f"Is {aid} producing oil right now?"})
    a, b = d.window(90, "days")
    sp = ops.spill_rows(list(d.wells.asset_id), a, b)
    for _, r in sp[sp.real_spill].iterrows():
        for c in ops.spill_compliance(r):
            if c["status"] in ("breach", "pending", "stale") and c["protocol"] in ("SR-01", "SR-02", "SR-03", "RC-04", "report"):
                out.append({"severity": "high" if c["protocol"] in ("SR-01", "RC-04") else "medium",
                            "kind": f"{c['protocol']} {c['status']}", "well": r.asset_id, "detail": c["detail"],
                            "ask": f"Which rules has {r.asset_id} broken in the last 12 months, and what is still open?"})
    for x in ops.rca_due().rows:
        area = d.area_name.get(d.well(x["Well"])["area_id"])
        out.append({"severity": "medium", "kind": "RCA due", "well": x["Well"],
                    "detail": f"{x['Corrective repairs']} corrective {x['Equipment']} repairs in 12 months ({x['Rule']})",
                    "ask": f"Which wells in {area} need a root-cause analysis on their {x['Equipment']}?"})
    rank = {"high": 0, "medium": 1, "low": 2}
    out.sort(key=lambda x: (rank[x["severity"]], x["well"]))
    return out[:limit]
