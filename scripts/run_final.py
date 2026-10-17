"""Run a scripted list of questions (users, new chats, session dates) through the copilot.
Writes <out>.md and <out>.json for the results page.
Usage: python scripts/run_final.py questions.json [--reset] [--out results]"""
import argparse
import json
import sys
import time
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from copilot import db  # noqa: E402
from copilot.agent import Copilot  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("questions")
    ap.add_argument("--out", default="results")
    ap.add_argument("--reset", action="store_true", help="clear the ledger and conversations first")
    args = ap.parse_args()
    items = json.loads(Path(args.questions).read_text(encoding="utf-8"))
    bot = Copilot()
    if args.reset:
        bot.ledger.reset()
    with db.session() as con:
        users = {r["name"].lower(): r["user_id"] for r in con.execute("SELECT user_id, name FROM users")}
    convs: dict = {}
    md, js = ["# Copilot results\n"], []
    for i, it in enumerate(items, 1):
        if it.get("reset"):
            bot.ledger.reset()
            convs.clear()
            md.append("\n---\n*Ledger reset*\n")
            continue
        uid = users.get(it.get("user", "Michael Turner").lower(), it.get("user"))
        key = (uid, it.get("chat", "default"))
        if key not in convs or it.get("new_chat"):
            sd = date.fromisoformat(it["session_date"]) if it.get("session_date") else None
            convs[key] = bot.ledger.new_conversation(uid, sd)
        t = time.time()
        try:
            out = bot.ask(uid, convs[key], it["question"])
        except Exception as e:  # noqa: BLE001
            import traceback
            traceback.print_exc()
            out = {"text": f"ERROR: {e}", "results": [], "plan": {}}
        secs = time.time() - t
        ev = sorted({e["id"] for r in out["results"] for e in r["evidence"]})
        viz = [r["viz"]["type"] for r in out["results"]]
        md.append(f"\n## {it.get('id', i)}. {it.get('user', '')}: {it['question']}\n")
        md.append(out["text"])
        md.append(f"\n*Visual:* {', '.join(viz)} · *Plan:* `{json.dumps(out.get('plan', {}).get('steps'))}` · *{secs:.1f}s*")
        md.append(f"\n*Evidence:* {', '.join(ev[:40])}{' …' if len(ev) > 40 else ''}\n")
        js.append({"item": it, "answer": out, "secs": secs})
        print(f"[{i}/{len(items)}] {secs:.1f}s {it['question'][:70]}", flush=True)
    Path(args.out + ".md").write_text("\n".join(md), encoding="utf-8")
    Path(args.out + ".json").write_text(json.dumps(js, indent=1, default=str), encoding="utf-8")
    print("wrote", args.out + ".md")


if __name__ == "__main__":
    main()
