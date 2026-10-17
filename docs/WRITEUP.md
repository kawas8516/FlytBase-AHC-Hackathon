# Wellspring — Asset Intelligence Copilot

*Draft for the write-up (target 2 pages + a page of results). Rewrite in your own words before submitting: "the work must be your own". Numbers below are from `docs/results_final.md`, produced by `scripts/run_final.py` on the test dataset (600 wells, today = 15 Jan 2027).*

## Page 1 — System design

**Idea.** Operator questions are really questions about *which facts are true, for whom, at what scope, and why*: a stale recorded status, an inspection corrected as rainwater, a rule hidden in a manual, a supervisor changing a threshold, two people disagreeing. Raw records and documents are read-only. Everything people tell the copilot is appended to a **ledger** with author, reason, scope and the original value. Every answer is derived from raw data + documents + ledger, so a correction reaches every user at exactly its scope.

**Storage and retrieval.** Dataset roots load into SQLite (wells, inspections, maintenance, regulator events, notes, users, areas); manuals, SOPs, repair reports and notes are chunked by heading into an FTS5 index. Repair reports are parsed for facts that exist only there (containment hours, compliance-check rows, "Parts installed" pump model/serial/lot, soil-sample sentence). The ledger and each user's conversations live in a separate `memory.db`, so loading new data never wipes memory.

**Rules come from the documents.** At load time thresholds are parsed from manuals and SOPs into a `rules` table with document, section and quote: producing = wellhead ≥ N °C above air per well type (T200 15, T350 20, **T500 25, picked up automatically from the test data**), SR-01 deadline **with the revision in force on the discovery date** (24 h before 1 Jan 2027, 12 h after, from Spill Response SOP rev 5), SR-02..04, RC-01..05, RCA counts, spill classes. The test set's Operations SOP (OPS-1 gas response, OPS-2 bypass/MOC, OPS-3 status precedence, OPS-5 freeze checks), MOC memos, recall notice and regulator letter are read from their text, not hard-coded.

**Operators, not a free-form agent.** Questions are routed (keywords first, Gemma only when unsure) to deterministic operators that compute from data and return rows, evidence IDs, a proof (rule + quote) and a suggested visual: status, downtime, spills, repairs, RCA, compliance audit, gas-response audit, bypass/MOC audit, regulator-letter audit, recalled-pump inventory, status-precedence check, operator-note ranking, waiting-reason breakdown, temperature by area, plus document Q&A and a read-only SQL fallback. This keeps numbers exact and fast (the whole 21-turn final run takes under a minute).

**Honesty about what the data cannot say.** Asked for a reservoir pressure map, or the best producer, the copilot says the data has no pressure readings and no production volumes, explains what exists, and (for Q2) shows only a clearly labelled proxy. A judgement question (Q7, Q10, Q11) states its method and caveats.

**Memory, two levels.** *Shared:* corrections, type-wide rules and statements are ledger entries visible to everyone with author and status. *Private:* per-user result sets and preferences, selected by `user_id` in SQL; "the wells we discussed" resolves only from that user's own history, and presentation preferences ("sort by area, costs in $k") apply only to the person who set them.

**Feedback and conflicts.** Corrections, rules and statements are parsed deterministically. The original is kept; the receipt states author, reason, scope. A first-hand report from a supervisor is applied with attribution ("WELL-0333 counted as replaced on Nathan Pierce's word; work order not in the system"); a second-hand report ("Nathan told me…") is stored as *unconfirmed* and not applied; a claim that contradicts the data is shown against the data; disagreeing notes are shown side by side.

**Generative UI.** Status card, table, line chart with non-producing markers, bar and stacked bar, map, heatmap, change receipt, conflict card, evidence chips, "How I read this" chips, "Show the work" panel, Rules and Ledger drawers, user and session-date pickers.

**Models and cost.** Gemma 4 (`gemma-4-31b-it`, `gemma-4-26b-a4b-it`, free tier), OpenRouter fallback. None of the final-run answers needed the model; it is used for unusual phrasing, document Q&A and exploratory SQL (56 logged calls during development, median ~30 s each, free tier). Cost: USD 0.

**What next.** Streaming; embeddings for free-form SOP questions; LLM narration behind a number checker; role-based permission for who may change rules; a production forecast if volumes were available; editing plan chips to re-run without the model.

## Page 2 — Results on the final questions

| Q | Answer (summary) | What worked / what did not |
|---|---|---|
| 1 Reservoir pressure | Cannot map it: no pressure readings anywhere in the data; only equipment limits in manuals. Lists what exists. | Refusing to invent a map is the point. No visual produced, by design. |
| 2 Best producer | Cannot say: no production volumes. 52 wells were producing at all 53 inspections in 2026 (tie on uptime). | Proxy is labelled as uptime, not output. |
| 3 Gas reports | 26 reports since 1 Nov; 17 met the deadline, **9 missed** (24 h before 1 Jan 2027, 12 h after); e.g. WELL-0163 responded after 251 h, WELL-0341 after 678 h. | Response = job start or *manual* inspection after the note; drone inspections excluded per OPS-1. |
| 4 Bypasses | 3 in place now: **WELL-0405 not approved**, **WELL-0249 expired** (MOC-2026-036 ran out 15 Dec), WELL-0248 allowed (MOC-2026-031 extended by -044 to 28 Feb 2027). 5 violations in total incl. WELL-0158, -0087 (expired), -0561 (not approved). | MOC extension handled (expiry replaced). |
| 5 Regulator letter | 6 reportable spills in Block 7/8 since 1 Jun 2026; **3 not compliant** (WELL-0123, -0182, -0262: no "Soil samples sent to the lab." in the clean-up report). WELL-0067's volume was corrected to 5.6 bbl but is outside these two areas. | Corrections applied before the 5 bbl test; not-crude detections excluded. |
| 6 Which status is right | 12 wells where latest inspection and a newer operator note disagree, with OPS-3 outcome (6 "not producing (shut in)", 4 "producing (unconfirmed)", 2 inspection newer than the note). | Notes older than the previous inspection are treated as superseded. |
| 7 Operator notes | Top 10 ranked with quoted notes and other signs; crew first to **WELL-0010, WELL-0263, WELL-0175**. | Heuristic score, not a forecast model; says so. |
| 8 Who told you that | Nathan's first-hand swap on WELL-0333 applied (attributed); Olivia's second-hand WELL-0577 swap stored unconfirmed and not applied; Nathan's sort/$k preference private; his area view lists 3 pumps in $k. | Sources named in every turn. |
| 9 One conversation | 8 recalled pumps (2 NE-8, 3 NW-12, 1 SE-32, 2 SW-23); Northwest Production led by Nathan Pierce, 150 wells; OPS-5: 4 missed heat-trace checks in December; no H2S reading is recorded for WELL-0332 (not invented); 2 recalled-pump wells not producing; deal with **WELL-0160** first. | Session memory across topics works; H2S answer is an honest "not recorded". |
| 10 Waiting on | 35 jobs: weather 63%, parts 37%; typical extra days weather 21, parts 14 (35 in Southeast Block 32); stands out: Block 7 and Northwest Block 12 all weather, Southwest Block 24 all parts. | Contractors and crews never appear as reasons in the notes, so they show 0. |
| 11 Hotter region | Southeast Block 31 (31.5 °C above air, hottest in 13 of 13 months), but it has the most T500 wells; within the same type, area averages differ by only about 1–2.5 °C. | The answer carries the well-type caveat. |

**What did not work / limits.** Gemma is slow (median 30 s) and sometimes errors, so every question that matters is deterministic; free-form questions outside the operators fall back to document search or SQL and are slower and less reliable. Q10's reasons are limited to what notes record.
