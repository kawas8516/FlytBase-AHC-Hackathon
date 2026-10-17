# Wellspring: Asset Intelligence Copilot

A chat copilot for oil-field operators. Ask in plain English about wells, spills, downtime, repairs and compliance; get an answer with the right visual, the records and documents it used, and the rule it applied. Built for the FlytBase Hacktoberfest 2026 hack day.

**Core idea: a ledger, not a pile of prompts.** Raw records, manuals and SOPs are read-only. Everything people tell the copilot (a corrected reading, a new rule for a well type, "WELL-0007 is shut in from 17 Oct") is appended to a ledger with author, reason, scope and the original value. Every answer is derived from raw data + ledger, so corrections apply to everyone, at the scope they were given, and nothing is silently overwritten.

## What it does
- **Grounded answers.** Producing/not producing, downtime, spills, repair cost, RCA due, compliance audit (SR-01..04, RC-01..05), fines, containment times that exist only in free-text repair reports.
- **Rules from the documents.** Thresholds (15 °C for T200, 20 °C for T350, 24 h report limit, 4 h containment, 60-day verification ...) are parsed out of the manuals and SOPs at load time and cited in the answer. A new well type in new data works with no code change.
- **Generative UI.** Status card, table, line chart (non-producing readings marked), bar chart, map, heatmap, evidence chips, "Show the work" panel, plan chips ("How I read this"). A visual named in the question wins; otherwise one is chosen from the shape of the answer.
- **Two-level memory.** Shared: corrections, rules and statements are visible to every user, with author and status. Private: "the three wells we discussed yesterday" resolves only from that user's own conversations (enforced in SQL).
- **Honesty about conflicts.** A statement that contradicts the data is stored as *unconfirmed* and the contradiction is shown; two people disagreeing are both shown; a correction that disagrees with an inspector's note is applied and flagged.
- **Attention feed.** Down-with-no-reason wells, stale recorded status, SR-01/02 breaches, RCA due. Same operators as the answers, so feed and chat cannot disagree.

## Architecture
```
 dataset roots ──► ingest ──► data.db (SQLite)   rules table (parsed from manuals/SOPs)
                                  │               report facts (containment hours, compliance rows)
 memory.db (never wiped) ◄── ledger writes        FTS5 index over manuals, SOPs, reports, notes
        │                         │
        ▼                         ▼
   user question ─► planner ─► deterministic operators (pandas) ─► Result{rows, evidence, proof, viz}
   (feedback parsed by rules,        │
    LLM only when unsure)            └─► narration (deterministic) ─► React UI
```
- `copilot/ingest.py` loads one or more dataset roots (later roots override earlier by key). `memory.db` is separate so re-ingesting never wipes memory.
- `copilot/rules.py` parses thresholds from manuals and SOPs. `copilot/reports.py` extracts report-only facts.
- `copilot/engine/views.py` derives producing, downtime (7 days per non-producing weekly inspection), real spills (dataset corrections and runtime corrections applied, originals kept). `copilot/engine/ops.py` holds the operators.
- `copilot/memory.py` is the ledger and the per-user conversation memory. `copilot/feedback.py` parses corrections/rules/statements without an LLM.
- `copilot/planner.py` + `copilot/agent.py`: slot extraction (deterministic first; Gemma 4 plans when the keyword router is unsure; read-only SQL as a last resort).
- `web/`: React + Vite + Recharts + Leaflet.

## Run
```
python -m venv .venv && .venv\Scripts\pip install fastapi "uvicorn[standard]" pandas httpx pydantic pytest python-dotenv openai
copy .env.example .env      # set GOOGLE_API_KEY, OPENROUTER_API_KEY, DATA_DIRS, TODAY
.venv\Scripts\python -m copilot.ingest            # loads DATA_DIRS (comma separated roots)
cd web && npm install && npm run build && cd ..
.venv\Scripts\python -m uvicorn copilot.api:app --port 8000     # http://localhost:8000
.venv\Scripts\python -m pytest -q                 # 17 scenario tests, no LLM needed
.venv\Scripts\python scripts/run_final.py scripts/example_questions.json --reset --out results
```
Models: Gemma 4 (`gemma-4-31b-it`, `gemma-4-26b-a4b-it`) on Google AI Studio, fallback `nvidia/nemotron-3-super-120b-a12b:free` on OpenRouter. The copilot answers the example scenarios with zero LLM calls; the LLM is used for unusual phrasing, document Q&A and exploratory SQL. Every call is logged to `data/llm_calls.jsonl`.

## Tests
`tests/test_engine.py` checks all 18 example scenarios against the expected answers (numbers, IDs, scopes, conflicts). `scripts/drill.py` builds a mutated dataset (new well type T500 at 25 °C, new user) and checks the engine against an independent oracle.

All data is synthetic and supplied by the organisers. MIT licensed.

## Test dataset and final questions
```
# .env: DATA_DIRS=<path>/test-data/dataset   TODAY=2027-01-15
.venv\Scripts\python -m copilot.ingest
.venv\Scripts\python scripts/run_final.py scripts/final_questions.json --reset --out results_final   # writes results_final.md/.json
```
`copilot/engine/final_ops.py` holds the operators driven by the test-set documents (gas response OPS-1, bypass/MOC OPS-2, status precedence OPS-3, freeze checks OPS-5, recall notice, regulator letter, operator-note ranking, waiting reasons, temperature by area, data-gap answers). `copilot/final_agent.py` routes questions to them and handles pump-swap statements, hearsay and private preferences. Results of the final run: `docs/results_final.md`.
Sample-data tests: `DB_PATH=data/sample.db DATA_DIRS=<sample-data> TODAY=2026-10-17 python -m copilot.ingest && python -m pytest -q`.
