"""Gold answers from the Example Questions document, checked against the deterministic engine (no LLM).
Run: .venv/Scripts/python -m pytest -q"""
from datetime import date

import pytest

from copilot.engine.ops import Ops
from copilot.engine.views import Data
from copilot.memory import Ledger

U = {"michael": "U-201", "jessica": "U-202", "tyler": "U-204", "jake": "U-102", "laura": None}


@pytest.fixture(scope="module")
def ops():
    return Ops(Data())


@pytest.fixture()
def ledger(tmp_path):
    return Ledger(tmp_path / "mem.db")


def test_q1_well_0001_status(ops):
    r = ops.well_status("WELL-0001").rows[0]
    assert r["producing"] is False and r["last_inspection_id"] == "INS-0001-0203"
    assert r["inspector"] == "Ryan Brooks" and r["method"] == "drone" and r["delta_c"] == 3.2
    assert "CTX-0001-003" in r["reasons"][0] and r["status_stale"]


def test_q2_ne8_not_producing(ops):
    r = ops.wells_status(area="Northeast Block 8")
    assert [x["Well"] for x in r.rows] == ["WELL-0164", "WELL-0170", "WELL-0172", "WELL-0175"]
    by = {x["Well"]: x for x in r.rows}
    assert by["WELL-0164"]["Reason"].startswith("No recorded reason") and "Pump jack not moving" in by["WELL-0164"]["Reason"]
    assert "MNT-0170-031" in by["WELL-0170"]["Reason"] and "MNT-0172-028" in by["WELL-0172"]["Reason"]
    assert by["WELL-0175"]["Reason"] == "No recorded reason"
    assert by["WELL-0170"]["Recorded status"] == "down" and "out of date" in by["WELL-0164"]["Recorded status"]


def test_q3_series(ops):
    f = ops.series("WELL-0001", weeks=13).facts
    assert f["readings"] == 13 and f["from"] == "23 Jul 2026" and f["not_producing"] == ["8 Oct 2026", "15 Oct 2026"]


def test_q4_spills(ops):
    r = ops.spills(wells=["WELL-0001"], start=date(2022, 10, 17))
    assert r.facts["count"] == 6 and r.facts["total_bbl"] == 15.1 and r.facts["detections"] == 7


def test_q5_downtime_2025(ops):
    r = ops.downtime(wells=["WELL-0001"], start=date(2025, 1, 1), end=date(2025, 12, 31))
    assert r.rows[0]["Downtime days"] == 21


def test_q6_ne7_top3(ops):
    a, b = ops.d.window(4, "months")
    assert (a, b) == (date(2026, 6, 16), date(2026, 10, 16))
    r = ops.downtime(area="Northeast Block 7", start=a, end=b, top=3)
    assert r.facts["ranking"] == [("WELL-0121", 49), ("WELL-0107", 42), ("WELL-0138", 42)]
    assert r.facts["next"] == {"Well": "WELL-0119", "days": 28}


def test_q7_map(ops):
    a, b = ops.d.window(90, "days")
    r = ops.spills(area="Northeast Block 8", start=a, end=b, viz="map")
    assert sorted((x["Well"], x["Barrels"]) for x in r.rows) == [("WELL-0151", 4.5), ("WELL-0165", 1.2), ("WELL-0175", 3.9), ("WELL-0186", 0.6)]


def test_q8_heatmap(ops):
    r = ops.spill_heatmap(2026)
    assert r.facts["totals"] == {"Northeast Block 7": 37, "Northeast Block 8": 26, "Southwest Block 23": 35, "Southwest Block 24": 43}


def test_q9_compliance(ops):
    f = ops.compliance_audit("WELL-0001").facts
    assert f["breach_rules"] == ["SR-01", "SR-02", "SR-03", "RC-04"] and f["open_fines_usd"] == 5000


def test_q10_containment(ops):
    a, b = ops.d.window(90, "days")
    r = ops.spills_check(area="Southwest Block 24", start=a, end=b, protocol="SR-02")
    assert r.facts["wells"] == ["WELL-0082", "WELL-0100"]


def test_q11_q16_private_memory(ledger):
    ops = ledger.ops()
    c1 = ledger.new_conversation(U["michael"], date(2026, 10, 16))
    a, b = ops.d.window(4, "months")
    r = ops.downtime(area="Northeast Block 7", start=a, end=b, top=3)
    ledger.save_result_set(U["michael"], c1, "Q6", "downtime", [w for w, _ in r.facts["ranking"]], {})
    c2 = ledger.new_conversation(U["michael"], date(2026, 10, 17))
    sets = ledger.recall(U["michael"], conv_id=c2, count=3)
    wells = sets[0]["entity_ids"]
    cost = ops.repairs(wells=wells, start=date(2026, 1, 1), end=ops.d.today).facts["costs"]
    assert cost == {"WELL-0121": 25794, "WELL-0107": 5176, "WELL-0138": 46942}
    c3 = ledger.new_conversation(U["jessica"], date(2026, 10, 17))
    assert ledger.recall(U["jessica"], conv_id=c3, count=3) == []


def test_q12_q15_raw_correction(ledger):
    r = ledger.record_correction(U["michael"], "WELL-0164", "wellhead_temp_c", 41.0, "handheld thermal gun faulty; re-measured", on=date(2026, 10, 15))
    assert r.rows[0]["Inspection"] == "INS-0164-0205" and float(r.rows[0]["Original (kept)"]) == 24.0
    assert r.facts["producing"] and r.facts["delta_c"] == 21.1 and r.conflicts
    q2 = ledger.ops().wells_status(area="Northeast Block 8")
    assert [x["Well"] for x in q2.rows] == ["WELL-0170", "WELL-0172", "WELL-0175"]
    assert any("WELL-0164 is no longer listed" in n for n in q2.notes)
    s = ledger.ops().well_status("WELL-0164")  # Jessica's view: shared correction applies
    assert s.rows[0]["producing"] and s.conflicts and "Michael Turner" in s.notes[0]


def test_q13_q15_analysis_correction(ledger):
    r = ledger.record_correction(U["michael"], "WELL-0151", "spill_est_volume_bbl", 5.4, "field crew measured", on=date(2026, 9, 24))
    assert r.rows[0]["Inspection"] == "INS-0151-0201" and float(r.rows[0]["Original (kept)"]) == 4.5
    text = " ".join(r.notes)
    assert "SR-01" in text and "possible breach" in text and "23 Nov 2026" in text and "moderate" in text and "6.4" in text
    ops = ledger.ops()
    a, b = ops.d.window(90, "days")
    q = ops.spills_check(area="Northeast Block 8", start=a, end=b, protocol="SR-01")
    assert q.facts["wells"] == ["WELL-0151"]


def test_q14_type_rule(ledger):
    assert ledger.ops().rca_due(area="Northeast Block 7", equipment="pump_jack").facts["wells"] == ["WELL-0108", "WELL-0121", "WELL-0138"]
    ledger.record_rule(U["michael"], "well_type", "T350", "rca_corrective_count", 2, equipment_kind="pump_jack")
    r = ledger.ops().rca_due(area="Northeast Block 7", equipment="pump_jack")
    assert r.facts["wells"] == ["WELL-0108", "WELL-0120", "WELL-0121", "WELL-0138"]
    assert r.facts["diff_vs_manual"]["added"] == ["WELL-0120"]


def test_q16_shared_fact(ledger):
    ledger.record_status(U["jake"], "WELL-0007", False, date(2026, 10, 17), date(2026, 10, 27), "Shut in from 17 Oct for a 10-day planned workover")
    r = ledger.planned_downtime("WELL-0007")
    assert r.rows and "Jake Morales" in r.rows[0]["Source"] and r.rows[0]["From"] == "17 Oct 2026"


def test_q17_claims(ledger):
    a = ledger.record_status(U["michael"], "WELL-0175", False, date(2026, 10, 14), None, "Shut in for planned work since 14 Oct")
    assert a.facts["verdict"] == "corroborated"
    b = ledger.record_status(U["tyler"], "WELL-0175", True, None, None, "WELL-0175 is running fine")
    assert b.facts["status"] == "unconfirmed" and "0.4" in b.conflicts[0]["b"] and "Jessica Reed" in b.conflicts[0]["b"]
    assert any("Michael Turner" in x for x in b.conflicts[0]["agrees_with_data"])
    c = ledger.record_status(U["jake"], "WELL-0001", True, date(2026, 10, 14), None, "WELL-0001 is back online since 14 Oct")
    assert c.facts["status"] == "unconfirmed" and any("20 Oct" in x for x in c.conflicts[0]["agrees_with_data"] + c.conflicts[0]["also_disagrees"])


def test_q18_disagreeing_notes(ops):
    r = ops.spill_verdict("WELL-0101", date(2026, 8, 20))
    assert r.facts["real"] and r.conflicts[0]["kind"] == "notes_disagree" and "MNT-0101-029" in r.conflicts[0]["resolution"]
