"""Crash/sanity sweep: unseen phrasings through the whole agent with the LLM disabled.
Flags exceptions, empty answers and 'which well?' dead ends. Usage: python scripts/fuzz_questions.py"""
import pathlib
import sys
import tempfile
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from copilot.agent import Copilot  # noqa: E402
from copilot.memory import Ledger  # noqa: E402

QS = [
    "Is WELL-0042 running?", "Status of WELL-0100", "Show me WELL-0150", "Which wells in Southwest Block 23 are down right now?",
    "List T200 wells that are not producing", "How many wells are not producing in the whole field?",
    "How many days was WELL-0007 down last year?", "Downtime for WELL-0121 in the last 6 months",
    "Which 5 wells in Southwest Block 24 had the most downtime this year? Show a bar chart.",
    "Top 3 wells by downtime in Northeast Block 8 since 1 Aug",
    "How many spills did Southwest Block 23 have in the last 6 months?", "Total oil spilled in 2025",
    "Show a map of all spills in Northeast Block 7 in the last 120 days", "List spills for WELL-0082 as a table",
    "Heatmap of spills by area and month for 2025", "Show a heatmap of 2024 spills",
    "What did repairs cost on WELL-0121 this year?", "Repair cost for Northeast Block 7 in 2026",
    "Show the repairs on WELL-0138 in the last 12 months", "What was the last repair on WELL-0010?",
    "Which wells in Northeast Block 7 need a root-cause analysis on their flowline?", "Which T350 wells need an RCA on the pump jack?",
    "What rules has WELL-0082 broken in the last 12 months?", "Is WELL-0100 compliant?",
    "Which fines were issued in Southwest Block 24?", "How much in fines is still open?",
    "Which spills in Northeast Block 7 in the last 90 days needed a report to the regulator?",
    "Which spills in Southwest Block 23 in the last 60 days were not contained within the limit?",
    "Was the 10 Sep spill at WELL-0082 real oil?", "Plot WELL-0121's wellhead vs air temperature for 20 weeks",
    "Compare downtime across the four areas this year", "What does the T350 manual say about the temperature limit?",
    "What is the deadline to report a spill to the regulator?", "Is any downtime planned for WELL-0001?",
    "Which wells are shut in?", "Where are the wells in Northeast Block 8? Show a map",
    "Which wells were down the longest this summer in Northeast Block 7, and why?",
    "Who inspected WELL-0001 last?", "How many wells are in Southwest Block 23?",
]


def main():
    b = Copilot(Ledger(pathlib.Path(tempfile.mkdtemp()) / "m.db"))
    c = b.ledger.new_conversation("U-201")
    bad = 0
    for q in QS:
        t = time.time()
        try:
            o = b.ask("U-201", c, q, use_llm=False)
            ops = [s.get("operation") for s in o["plan"]["steps"]]
            text = o["full_text"].replace("\n", " ")[:110]
            flag = ""
            if not o["full_text"].strip() or "Which well" in o["full_text"] or "Which wells or area" in o["full_text"]:
                flag = "  <-- CHECK"
                bad += 1
            print(f"{time.time()-t:4.1f}s {','.join(map(str, ops)):18s} {q[:62]:62s} | {text}{flag}")
        except Exception as e:  # noqa: BLE001
            bad += 1
            print(f"EXC  {q[:70]}: {type(e).__name__}: {e}")
    print("flagged:", bad)


if __name__ == "__main__":
    main()
