# 5-minute video script (your voice). Target 2:00 design + 3:00 live queries.

Before recording: server running (`python -m uvicorn copilot.api:app --port 8000`), open http://localhost:8000, click **Reset demo** (twice), user = Michael Turner, Session date = 01/15/2027. Pre-run each query once so results are fast, then Reset demo again.

## 0:00–0:25 Problem
Operators dig through inspections, repair reports, manuals and people's notes to answer "which wells are down, and why". We built a copilot that answers with the evidence, and remembers what people tell it.

## 0:25–2:00 System design (show the Rules drawer, then the Ledger drawer, then slide/diagram from README)
1. **Raw data is read-only; people's input goes in a ledger** with author, reason, scope, original kept. Every answer = data + documents + ledger.
2. **Rules are parsed from the manuals and SOPs**, not hard-coded. Open *Rules*: T200 15 °C, T350 20 °C, **T500 25 °C appeared with the test data and worked with no code change**; SR-01 deadline is 24 h before 1 Jan 2027 and 12 h after (SOP revision 5).
3. **Deterministic operators** do the maths (downtime, spills, gas-response audit, bypass/MOC audit, recalled pumps…); the model (Gemma) only helps with unusual phrasing. The final run needs no model call.
4. **Two memory levels**: shared ledger vs private per-user memory and preferences; hearsay stays unconfirmed; honest "the data doesn't say" answers.

## 2:00–5:00 Live (about 40 s each)
1. **Q1** "Map the reservoir pressure…" → no pressure data; explains what exists. *Say: it does not invent a map.*
2. **Q3 gas reports** → table with Met/Missed; click an evidence chip (CTX note) and "Show the work" (OPS-1 quote). *24 h vs 12 h rule from the SOP text.*
3. **Q4 bypasses** → WELL-0249 expired, WELL-0405 not approved, WELL-0248 allowed because MOC-2026-044 extended MOC-2026-031.
4. **Q8 memory chain**: as Nathan Pierce: pump swap on WELL-0333 (attributed). Switch to Olivia Grant: "Nathan told me…WELL-0577…" → stays unconfirmed. Switch to Robert Hayes: "Which recalled pumps are still in the ground?" → 8, WELL-0333 listed as replaced on Nathan's word, WELL-0577 still listed. Open *My memory* / *Ledger*.
5. **Q10** → stacked bar, weather vs parts by area. (If time: Q11 hotter region with the well-type caveat.)

## 5:00 Close
Accuracy comes from rules read from documents + deterministic operators + a ledger with provenance. Next: embeddings for free-form SOP questions, streaming, role-based permissions.

Tips: keep each answer on screen 3–4 s; use the one-click prompts on the landing screen; if a model call is slow, say so and move on (the final answers do not depend on it).
