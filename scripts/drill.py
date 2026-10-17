"""Generalization drill: build a mutated dataset root (new well type T500 with a 25 C rule, reworded manual, a new user)
and check that ingest + rules + engine adapt with no code change, against an independent pandas oracle.
Usage: python scripts/drill.py <sample-data dir> <scratch dir>"""
import json
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def build(src: Path, dst: Path):
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)
    # new well type: copy T350 manual, change threshold and wording
    man = (dst / "fleet/well-types/T350.md").read_text(encoding="utf-8")
    man = man.replace("T350", "T500").replace("**20 °C above\nambient**", "**25 °C above\nambient**").replace("20 °C", "25 °C")
    (dst / "fleet/well-types/T500.md").write_text(man, encoding="utf-8")
    changed = []
    for n in range(151, 161):
        f = dst / f"assets/WELL-{n:04d}/metadata.json"
        m = json.loads(f.read_text(encoding="utf-8"))
        m["well_type"] = "T500"
        f.write_text(json.dumps(m), encoding="utf-8")
        changed.append(m["asset_id"])
    users = json.loads((dst / "fleet/users.json").read_text(encoding="utf-8"))
    users["users"].append({"user_id": "U-999", "name": "Priya Nair", "role": "hse_officer", "team_id": "TEAM-NE"})
    (dst / "fleet/users.json").write_text(json.dumps(users), encoding="utf-8")
    return changed


def main():
    src, dst = Path(sys.argv[1]), Path(sys.argv[2])
    changed = build(src, dst)
    import os
    os.environ["DB_PATH"] = str(dst / "drill.db")
    from copilot import config
    from copilot import db
    db.DB_PATH = Path(os.environ["DB_PATH"])
    from copilot import ingest
    ingest.ingest([dst])
    from copilot.engine.ops import Ops
    from copilot.engine.views import Data
    d = Data()
    thr = d.rule_value("T500", "producing_delta_c")
    print("T500 threshold parsed:", thr, "| T500 rca:", d.rule_value("T500", "rca_corrective_count"), "(inherits via T200)")
    assert thr == 25.0
    # independent oracle: recompute downtime for the changed wells straight from the raw files
    ok = True
    for aid in changed:
        raw = [json.loads(l) for l in (dst / f"assets/{aid}/inspections.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
        oracle = 7 * sum(1 for r in raw if round(r["wellhead_temp_c"] - r["ambient_temp_c"], 2) < 25.0)
        got = Ops(d).downtime(wells=[aid]).rows[0]["Downtime days"]
        if oracle != got:
            ok = False
            print("MISMATCH", aid, oracle, got)
    print("downtime oracle on T500 wells:", "OK" if ok else "FAIL")
    print("users:", len(d.users), "| new user visible:", "Priya Nair" in d.user_name.values())
    s = Ops(d).wells_status(area="Northeast Block 8").rows
    print("NE-8 not producing (now with T500 rule):", [r["Well"] for r in s])
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
