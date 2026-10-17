# Final-2-hours runbook (test data at 16:00 IST)

1. Download / clone the test dataset. Note whether it is a full replacement (one root with fleet/ + assets/) or an addition.
2. Set `DATA_DIRS` in `.env` (comma separated roots; sample first, test second if it is an addition; test only if it replaces).
   Set `TODAY` if the final questions say a different "today" (default 2026-10-17).
3. `python -m copilot.ingest` — prints counts. Check: wells, inspections, `rules` count, and that any NEW well type shows a `producing_delta_c`:
   `python -c "from copilot import db; c=db.connect(); [print(tuple(r)) for r in c.execute(\"select scope,key,value from rules where key='producing_delta_c'\")]"`
4. `python -m pytest -q` (sample-specific numbers will fail on new data; the point is it runs; skip if data replaced).
5. Smoke: start the server, open the UI, click "Needs attention", ask one question per operator type.
6. Write the final questions into `scripts/final_questions.json` (same shape as `example_questions.json`: user, question, optional chat/new_chat/session_date). Use the people/order the questions specify.
7. `python scripts/run_final.py scripts/final_questions.json --reset --out results_final`
8. Read `results_final.md` against each question. Anything wrong: fix, re-run (the run takes seconds; LLM only on odd phrasing).
9. Page 2 of the write-up = `results_final.md` condensed. Screenshots from the UI for the video.

If the LLM is rate-limited the copilot still answers (deterministic narration, keyword router). Check `data/llm_calls.jsonl` for failures.
