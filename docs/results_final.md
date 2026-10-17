# Copilot results


---
*Ledger reset*


## Q1. Michael Turner: All our wells feed one reservoir. Map the reservoir pressure across the field from the pressure data.

- I can't map reservoir pressure: the data has no pressure readings. Inspections record wellhead and air temperature and spills; repairs, regulator events and notes have no reservoir or wellhead pressure values either.
- The only pressure numbers in the documents are design limits in the well-type manuals (e.g. maximum wellhead working pressure) and pressure-test settings in repair reports. They are equipment ratings, not reservoir measurements, so mapping them would be invented.
- What exists: wellhead and air temperature, spill detections, repairs and costs, regulator events, notes, manuals/SOPs. A pressure map would need downhole or wellhead pressure gauges added to the inspections.
- Closest honest proxy: which wells are producing right now (temperature rule) can be shown on a map if useful.

*Visual:* text · *Plan:* `[{"operation": "data_gap"}]` · *2.5s*

*Evidence:* Dataset Guide, T200 9.1


## Q2. Robert Hayes: Which well produced the most oil in 2026?

- I can't say which well produced the most oil in 2026: the data has no production volumes (no barrels, rates or meter readings). Producing or not is only inferred from wellhead temperature, once a week.
- Proxy only, not volume: 52 wells were producing at every inspection in 2026 (53 of 53 weekly inspections), so they tie on uptime and cannot be ranked by output.
- To answer properly we would need tank gauging or meter volumes per well.
- Wells tied at full uptime (first 10): WELL-0008, WELL-0016, WELL-0017, WELL-0024, WELL-0044, WELL-0050, WELL-0051, WELL-0106, WELL-0144, WELL-0147 ....

*Visual:* table · *Plan:* `[{"operation": "data_gap"}]` · *0.1s*

*Evidence:* Dataset Guide, T200 9.1


## Q3. Laura Simmons: Since 1 Nov 2026, every time an operator note reports gas at a well, did we get someone out to that well in time under our operating procedures? List every report and whether the response met the deadline.

**26 gas reports; 17 met the response deadline, 9 missed.**
- Well: WELL-0163; Area: Northeast Block 8; Reported at: 03 Nov 2026 20:55; Report: "H2S monitor alarmed at WELL-0163, crew moved upwind and reported it." (CTX-0163-002); Response: MNT-0163-019 at 14 Nov 2026 08:00; Hours to response: 251.1; Deadline: 24 h; Met / Missed: Missed
- Well: WELL-0149; Area: Northeast Block 7; Reported at: 06 Nov 2026 18:20; Report: "Strong gas odor around the WELL-0149 cellar, called it in to the supervisor." (CTX-0149-004); Response: MNT-0149-029 at 07 Nov 2026 08:00; Hours to response: 13.7; Deadline: 24 h; Met / Missed: Met
- Well: WELL-0165; Area: Northeast Block 8; Reported at: 13 Nov 2026 20:35; Report: "Rotten-egg smell at the WELL-0165 pad on arrival, called the HSE officer." (CTX-0165-001); Response: MNT-0165-031 at 14 Nov 2026 08:00; Hours to response: 11.4; Deadline: 24 h; Met / Missed: Met
- Well: WELL-0341; Area: Northwest Block 12; Reported at: 19 Nov 2026 07:40; Report: "H2S monitor alarmed at WELL-0341, crew moved upwind and reported it." (CTX-0341-002); Response: INS-0341-0109 at 17 Dec 2026 13:30; Hours to response: 677.8; Deadline: 24 h; Met / Missed: Missed
- Well: WELL-0091; Area: Southwest Block 24; Reported at: 27 Nov 2026 22:25; Report: "H2S monitor alarmed at WELL-0091, crew moved upwind and reported it." (CTX-0091-001); Response: MNT-0091-019 at 28 Nov 2026 08:00; Hours to response: 9.6; Deadline: 24 h; Met / Missed: Met
- Well: WELL-0423; Area: Northwest Block 12; Reported at: 03 Dec 2026 05:25; Report: "Gas odor reported by the pumper near WELL-0423 wellhead, area flagged off." (CTX-0423-002); Response: INS-0423-0213 at 03 Dec 2026 09:15; Hours to response: 3.8; Deadline: 24 h; Met / Missed: Met
- Well: WELL-0059; Area: Southwest Block 24; Reported at: 03 Dec 2026 06:10; Report: "Gas odor reported by the pumper near WELL-0059 wellhead, area flagged off." (CTX-0059-002); Response: INS-0059-0213 at 03 Dec 2026 12:15; Hours to response: 6.1; Deadline: 24 h; Met / Missed: Met
- Well: WELL-0332; Area: Northwest Block 12; Reported at: 03 Dec 2026 12:10; Report: "Gas odor reported by the pumper near WELL-0332 wellhead, area flagged off." (CTX-0332-004); Response: none; Hours to response: None; Deadline: 24 h; Met / Missed: Missed
- Well: WELL-0401; Area: Northwest Block 12; Reported at: 05 Dec 2026 13:50; Report: "H2S monitor alarmed at WELL-0401, crew moved upwind and reported it." (CTX-0401-002); Response: MNT-0401-033 at 11 Dec 2026 08:00; Hours to response: 138.2; Deadline: 24 h; Met / Missed: Missed
- Well: WELL-0189; Area: Northeast Block 8; Reported at: 10 Dec 2026 12:35; Report: "H2S monitor alarmed at WELL-0189, crew moved upwind and reported it." (CTX-0189-003); Response: MNT-0189-037 at 11 Dec 2026 08:00; Hours to response: 19.4; Deadline: 24 h; Met / Missed: Met
- Well: WELL-0403; Area: Northwest Block 12; Reported at: 10 Dec 2026 21:15; Report: "Rotten-egg smell at the WELL-0403 pad on arrival, called the HSE officer." (CTX-0403-004); Response: MNT-0403-024 at 11 Dec 2026 08:00; Hours to response: 10.8; Deadline: 24 h; Met / Missed: Met
- Well: WELL-0244; Area: Southeast Block 31; Reported at: 11 Dec 2026 05:25; Report: "Gas odor reported by the pumper near WELL-0244 wellhead, area flagged off." (CTX-0244-002); Response: MNT-0244-026 at 11 Dec 2026 08:00; Hours to response: 2.6; Deadline: 24 h; Met / Missed: Met
- Well: WELL-0040; Area: Southwest Block 23; Reported at: 12 Dec 2026 01:55; Report: "Rotten-egg smell at the WELL-0040 pad on arrival, called the HSE officer." (CTX-0040-002); Response: MNT-0040-029 at 12 Dec 2026 08:00; Hours to response: 6.1; Deadline: 24 h; Met / Missed: Met
- Well: WELL-0228; Area: Southeast Block 31; Reported at: 16 Dec 2026 19:50; Report: "Smelled gas downwind of WELL-0228 wellhead, backed off and called it in." (CTX-0228-004); Response: INS-0228-0144 at 17 Dec 2026 12:45; Hours to response: 16.9; Deadline: 24 h; Met / Missed: Met
- Well: WELL-0052; Area: Southwest Block 24; Reported at: 18 Dec 2026 06:45; Report: "Gas odor reported by the pumper near WELL-0052 wellhead, area flagged off." (CTX-0052-003); Response: none; Hours to response: None; Deadline: 24 h; Met / Missed: Missed
- Well: WELL-0370; Area: Northwest Block 12; Reported at: 21 Dec 2026 12:45; Report: "Strong gas odor around the WELL-0370 cellar, called it in to the supervisor." (CTX-0370-005); Response: MNT-0370-028 at 22 Dec 2026 08:00; Hours to response: 19.2; Deadline: 24 h; Met / Missed: Met
- Well: WELL-0362; Area: Northwest Block 12; Reported at: 24 Dec 2026 00:15; Report: "Gas odor reported by the pumper near WELL-0362 wellhead, area flagged off." (CTX-0362-002); Response: MNT-0362-030 at 25 Dec 2026 08:00; Hours to response: 31.8; Deadline: 24 h; Met / Missed: Missed
- Well: WELL-0161; Area: Northeast Block 8; Reported at: 25 Dec 2026 15:45; Report: "Smelled gas downwind of WELL-0161 wellhead, backed off and called it in." (CTX-0161-006); Response: INS-0161-0168 at 14 Jan 2027 11:00; Hours to response: 475.2; Deadline: 24 h; Met / Missed: Missed
- Well: WELL-0135; Area: Northeast Block 7; Reported at: 27 Dec 2026 03:50; Report: "Smelled gas downwind of WELL-0135 wellhead, backed off and called it in." (CTX-0135-009); Response: MNT-0135-034 at 27 Dec 2026 08:00; Hours to response: 4.2; Deadline: 24 h; Met / Missed: Met
- Well: WELL-0324; Area: Northwest Block 12; Reported at: 01 Jan 2027 22:40; Report: "Gas odor reported by the pumper near WELL-0324 wellhead, area flagged off." (CTX-0324-001); Response: MNT-0324-036 at 02 Jan 2027 08:00; Hours to response: 9.3; Deadline: 12 h; Met / Missed: Met
- Well: WELL-0330; Area: Northwest Block 12; Reported at: 02 Jan 2027 21:40; Report: "H2S monitor alarmed at WELL-0330, crew moved upwind and reported it." (CTX-0330-003); Response: MNT-0330-030 at 03 Jan 2027 08:00; Hours to response: 10.3; Deadline: 12 h; Met / Missed: Met
- Well: WELL-0599; Area: Southeast Block 32; Reported at: 06 Jan 2027 17:20; Report: "Strong gas odor around the WELL-0599 cellar, called it in to the supervisor." (CTX-0599-003); Response: INS-0599-0196 at 07 Jan 2027 09:45; Hours to response: 16.4; Deadline: 12 h; Met / Missed: Missed
- Well: WELL-0516; Area: Southeast Block 32; Reported at: 06 Jan 2027 21:15; Report: "Rotten-egg smell at the WELL-0516 pad on arrival, called the HSE officer." (CTX-0516-002); Response: INS-0516-0215 at 07 Jan 2027 12:15; Hours to response: 15.0; Deadline: 12 h; Met / Missed: Missed
- Well: WELL-0425; Area: Northwest Block 12; Reported at: 07 Jan 2027 05:20; Report: "Gas odor reported by the pumper near WELL-0425 wellhead, area flagged off." (CTX-0425-006); Response: INS-0425-0218 at 07 Jan 2027 09:00; Hours to response: 3.7; Deadline: 12 h; Met / Missed: Met
- Well: WELL-0465; Area: Southeast Block 32; Reported at: 08 Jan 2027 23:35; Report: "Strong gas odor around the WELL-0465 cellar, called it in to the supervisor." (CTX-0465-005); Response: MNT-0465-031 at 09 Jan 2027 08:00; Hours to response: 8.4; Deadline: 12 h; Met / Missed: Met
- Well: WELL-0137; Area: Northeast Block 7; Reported at: 10 Jan 2027 23:30; Report: "Gas odor reported by the pumper near WELL-0137 wellhead, area flagged off." (CTX-0137-004); Response: MNT-0137-032 at 11 Jan 2027 08:00; Hours to response: 8.5; Deadline: 12 h; Met / Missed: Met
- Deadline from OPS-1: 24 h for reports before 1 Jan 2027, 12 h from then. A response is a maintenance job start or a manual inspection after the note; drone inspections do not count.

*Visual:* table · *Plan:* `[{"operation": "gas_response"}]` · *0.7s*

*Evidence:* CTX-0040-002, CTX-0052-003, CTX-0059-002, CTX-0091-001, CTX-0135-009, CTX-0137-004, CTX-0149-004, CTX-0161-006, CTX-0163-002, CTX-0165-001, CTX-0189-003, CTX-0228-004, CTX-0244-002, CTX-0324-001, CTX-0330-003, CTX-0332-004, CTX-0341-002, CTX-0362-002, CTX-0370-005, CTX-0401-002, CTX-0403-004, CTX-0423-002, CTX-0425-006, CTX-0465-005, CTX-0516-002, CTX-0599-003, INS-0059-0213, INS-0161-0168, INS-0228-0144, INS-0341-0109, INS-0423-0213, INS-0425-0218, INS-0516-0215, INS-0599-0196, MNT-0040-029, MNT-0091-019, MNT-0135-034, MNT-0137-032, MNT-0149-029, MNT-0163-019 …


## Q4. Chris Dalton: Across all areas, which temporary flowline bypasses are in place right now, and is each one allowed? Also list any bypass, past or present, that stayed in after its approval ran out or was never approved at all.

**3 bypasses in place now; 5 violations (past or present).**
- Well: WELL-0405; Area: Northwest Block 12; Bypass in: 20 Dec 2026; Bypass out: still in; Approval: none; Approval valid until: —; Status: Not approved
- Well: WELL-0249; Area: Southeast Block 31; Bypass in: 25 Nov 2026; Bypass out: still in; Approval: MOC-2026-036; Approval valid until: 15 Dec 2026; Status: Expired
- Well: WELL-0248; Area: Southeast Block 31; Bypass in: 5 Nov 2026; Bypass out: still in; Approval: MOC-2026-031 (extended by MOC-2026-044); Approval valid until: 28 Feb 2027; Status: Allowed
- Well: WELL-0158; Area: Northeast Block 8; Bypass in: 20 Nov 2026; Bypass out: 28 Dec 2026; Approval: MOC-2026-036; Approval valid until: 15 Dec 2026; Status: Expired
- Well: WELL-0561; Area: Southeast Block 32; Bypass in: 8 Dec 2026; Bypass out: 19 Dec 2026; Approval: none; Approval valid until: —; Status: Not approved
- Well: WELL-0087; Area: Southwest Block 24; Bypass in: 2 Dec 2026; Bypass out: 6 Jan 2027; Approval: MOC-2026-036; Approval valid until: 15 Dec 2026; Status: Expired
- Well: WELL-0356; Area: Northwest Block 12; Bypass in: 18 Nov 2026; Bypass out: 5 Dec 2026; Approval: MOC-2026-036; Approval valid until: 15 Dec 2026; Status: Allowed
- Well: WELL-0461; Area: Southeast Block 32; Bypass in: 14 Nov 2026; Bypass out: 12 Dec 2026; Approval: MOC-2026-036; Approval valid until: 15 Dec 2026; Status: Allowed
- Well: WELL-0476; Area: Southeast Block 32; Bypass in: 22 Oct 2026; Bypass out: 18 Nov 2026; Approval: MOC-2026-031 (extended by MOC-2026-044); Approval valid until: 28 Feb 2027; Status: Allowed
- Well: WELL-0013; Area: Southwest Block 23; Bypass in: 10 Nov 2026; Bypass out: 8 Jan 2027; Approval: MOC-2026-031 (extended by MOC-2026-044); Approval valid until: 28 Feb 2027; Status: Allowed
- Well: WELL-0062; Area: Southwest Block 24; Bypass in: 2 Nov 2026; Bypass out: 27 Nov 2026; Approval: MOC-2026-031 (extended by MOC-2026-044); Approval valid until: 28 Feb 2027; Status: Allowed
- Well: WELL-0284; Area: Southwest Block 24; Bypass in: 12 Nov 2026; Bypass out: 10 Dec 2026; Approval: MOC-2026-036; Approval valid until: 15 Dec 2026; Status: Allowed
- In place right now: WELL-0405 (Not approved), WELL-0249 (Expired), WELL-0248 (Allowed).
- Violations, past or present: WELL-0405 (Not approved), WELL-0249 (Expired), WELL-0158 (Expired), WELL-0561 (Not approved), WELL-0087 (Expired).
- OPS-2: allowed only on a well named in an unexpired MOC; an extension memo replaces the expiry (MOC-2026-044 extends MOC-2026-031 to 28 Feb 2027); in place from the note that puts it in to the note that takes it out.

*Visual:* table · *Plan:* `[{"operation": "bypasses"}]` · *0.3s*

*Evidence:* CTX-0013-002, CTX-0013-005, CTX-0062-002, CTX-0062-005, CTX-0087-001, CTX-0087-004, CTX-0158-003, CTX-0158-005, CTX-0248-002, CTX-0249-002, CTX-0284-002, CTX-0284-003, CTX-0356-002, CTX-0356-003, CTX-0405-003, CTX-0461-002, CTX-0461-003, CTX-0476-002, CTX-0476-003, CTX-0561-004, CTX-0561-005, MOC-2026-031, MOC-2026-036, MOC-2026-044


## Q5. Michael Turner: The State Oil & Gas Commission wrote to us in November 2026 about spills. Which of our spills does the letter cover, and on which ones are we not compliant? Show me a table.

**6 spills covered by the letter; 3 not compliant: WELL-0123, WELL-0182 and WELL-0262.**
- Well: WELL-0119; Area: Northeast Block 7; Inspection: INS-0119-0209, 5 Nov 2026; Volume (bbl): 6.0; Clean-up job: MNT-0119-029; Compliant?: Yes — report says "Soil samples sent to the lab."
- Well: WELL-0123; Area: Northeast Block 7; Inspection: INS-0123-0093, 24 Sep 2026; Volume (bbl): 6.0; Clean-up job: MNT-0123-014; Compliant?: No — clean-up report has no lab soil samples (field readings do not count)
- Well: WELL-0277; Area: Northeast Block 7; Inspection: INS-0277-0205, 1 Oct 2026; Volume (bbl): 6.2; Clean-up job: MNT-0277-031; Compliant?: Yes — report says "Soil samples sent to the lab."
- Well: WELL-0168; Area: Northeast Block 8; Inspection: INS-0168-0190, 11 Jun 2026; Volume (bbl): 5.6; Clean-up job: MNT-0168-024; Compliant?: Yes — report says "Soil samples sent to the lab."
- Well: WELL-0182; Area: Northeast Block 8; Inspection: INS-0182-0208, 3 Dec 2026; Volume (bbl): 5.2; Clean-up job: MNT-0182-028; Compliant?: No — clean-up report has no lab soil samples (field readings do not count)
- Well: WELL-0262; Area: Northeast Block 8; Inspection: INS-0262-0218, 7 Jan 2027; Volume (bbl): 6.1; Clean-up job: MNT-0262-029; Compliant?: No — clean-up report has no lab soil samples (field readings do not count)
- Letter scope: reportable spills (≥ 5 bbl, after corrections) in Northeast Block 7, Northeast Block 8 since 1 Jun 2026; lab results due 15 Jan 2027; HSE rule: compliant only if the clean-up report contains "Soil samples sent to the lab.".

*Visual:* table · *Plan:* `[{"operation": "letter_compliance"}]` · *0.1s*

*Evidence:* INS-0119-0209, INS-0123-0093, INS-0168-0190, INS-0182-0208, INS-0262-0218, INS-0277-0205, MNT-0119-029, MNT-0123-014, MNT-0168-024, MNT-0182-028, MNT-0262-029, MNT-0277-031, regulator-letter-2026-11-20


## Q6. Nathan Pierce: Across the whole field, not just my area, for which wells do the latest inspection and the operator notes disagree about whether the well is producing oil? For each one, what is its real status right now, and why?

**12 wells where the latest inspection and operator notes disagree.**
- Well: WELL-0323; Area: Northwest Block 12; Latest inspection: INS-0323-0219, 14 Jan 2027: 24.5 °C above air → producing; Latest operator note: 14 Jan 2027 19:20: "Shut-in WELL-0323 after the pumper reported a stuffing box leak." (CTX-0323-002); Status now: Not producing oil (shut in); Why: operator note on 14 Jan 19:20 is newer than the inspection; OPS-3: a newer shut-in note wins over the reading
- Well: WELL-0355; Area: Northwest Block 12; Latest inspection: INS-0355-0213, 14 Jan 2027: 31.1 °C above air → producing; Latest operator note: 14 Jan 2027 19:05: "Found WELL-0355 leaking at the stuffing box, shut the well in." (CTX-0355-004); Status now: Not producing oil (shut in); Why: operator note on 14 Jan 19:05 is newer than the inspection; OPS-3: a newer shut-in note wins over the reading
- Well: WELL-0422; Area: Northwest Block 12; Latest inspection: INS-0422-0215, 14 Jan 2027: 27.7 °C above air → producing; Latest operator note: 14 Jan 2027 21:35: "Shut in WELL-0422 for the night, high pressure alarm on the separator." (CTX-0422-003); Status now: Not producing oil (shut in); Why: operator note on 14 Jan 21:35 is newer than the inspection; OPS-3: a newer shut-in note wins over the reading
- Well: WELL-0249; Area: Southeast Block 31; Latest inspection: INS-0249-0120, 14 Jan 2027: 5.9 °C above air → not producing; Latest operator note: 13 Jan 2027 09:40: "WELL-0249 drive tripping on underload, restarted from the panel." (CTX-0249-004); Status now: Not producing oil; Why: inspection on 14 Jan 12:00 is newer than the note; OPS-3: the most recent evidence wins
- Well: WELL-0479; Area: Southeast Block 32; Latest inspection: INS-0479-0213, 14 Jan 2027: 23.6 °C above air → producing; Latest operator note: 14 Jan 2027 15:35: "Found WELL-0479 leaking at the stuffing box, shut the well in." (CTX-0479-004); Status now: Not producing oil (shut in); Why: operator note on 14 Jan 15:35 is newer than the inspection; OPS-3: a newer shut-in note wins over the reading
- Well: WELL-0481; Area: Southeast Block 32; Latest inspection: INS-0481-0220, 14 Jan 2027: 22.4 °C above air → producing; Latest operator note: 14 Jan 2027 18:50: "Shut in WELL-0481 for the night, high pressure alarm on the separator." (CTX-0481-006); Status now: Not producing oil (shut in); Why: operator note on 14 Jan 18:50 is newer than the inspection; OPS-3: a newer shut-in note wins over the reading
- Well: WELL-0010; Area: Southwest Block 23; Latest inspection: INS-0010-0219, 14 Jan 2027: 17.5 °C above air → not producing; Latest operator note: 09 Jan 2027 04:00: "Restarted WELL-0010 after the crew cleared the lockout." (CTX-0010-004); Status now: Not producing oil; Why: inspection on 14 Jan 14:00 is newer than the note; OPS-3: the most recent evidence wins
- Well: WELL-0026; Area: Southwest Block 23; Latest inspection: INS-0026-0216, 14 Jan 2027: 5.4 °C above air → not producing; Latest operator note: 15 Jan 2027 10:25: "WELL-0026 put back on production after the repair crew finished." (CTX-0026-001); Status now: Producing oil (unconfirmed); Why: operator note on 15 Jan 10:25 is newer than the inspection; OPS-3: a restart note makes it producing until an inspection confirms
- Well: WELL-0032; Area: Southwest Block 23; Latest inspection: INS-0032-0219, 14 Jan 2027: 7.4 °C above air → not producing; Latest operator note: 15 Jan 2027 10:25: "Brought WELL-0032 back online after the pump change." (CTX-0032-006); Status now: Producing oil (unconfirmed); Why: operator note on 15 Jan 10:25 is newer than the inspection; OPS-3: a restart note makes it producing until an inspection confirms
- Well: WELL-0033; Area: Southwest Block 23; Latest inspection: INS-0033-0222, 14 Jan 2027: 10.0 °C above air → not producing; Latest operator note: 15 Jan 2027 10:25: "Restarted WELL-0033, unit running smooth." (CTX-0033-003); Status now: Producing oil (unconfirmed); Why: operator note on 15 Jan 10:25 is newer than the inspection; OPS-3: a restart note makes it producing until an inspection confirms
- Well: WELL-0044; Area: Southwest Block 23; Latest inspection: INS-0044-0218, 14 Jan 2027: 23.7 °C above air → producing; Latest operator note: 14 Jan 2027 13:05: "Shut in WELL-0044 at the wellhead, flowline leak suspected." (CTX-0044-008); Status now: Not producing oil (shut in); Why: operator note on 14 Jan 13:05 is newer than the inspection; OPS-3: a newer shut-in note wins over the reading
- Well: WELL-0046; Area: Southwest Block 23; Latest inspection: INS-0046-0220, 14 Jan 2027: 2.1 °C above air → not producing; Latest operator note: 15 Jan 2027 10:25: "WELL-0046 put back on production after the repair crew finished." (CTX-0046-004); Status now: Producing oil (unconfirmed); Why: operator note on 15 Jan 10:25 is newer than the inspection; OPS-3: a restart note makes it producing until an inspection confirms
- Status follows OPS-3 of the Operations SOP (rev 2): the most recent of the latest inspection (after data corrections) and the latest shut-in/restart operator note.

*Visual:* table · *Plan:* `[{"operation": "status_disagreements"}]` · *1.6s*

*Evidence:* CTX-0010-004, CTX-0026-001, CTX-0032-006, CTX-0033-003, CTX-0044-008, CTX-0046-004, CTX-0249-004, CTX-0323-002, CTX-0355-004, CTX-0422-003, CTX-0479-004, CTX-0481-006, INS-0010-0219, INS-0026-0216, INS-0032-0219, INS-0033-0222, INS-0044-0218, INS-0046-0220, INS-0249-0120, INS-0323-0219, INS-0355-0213, INS-0422-0215, INS-0479-0213, INS-0481-0220


## Q7.1. Robert Hayes: Over the last month the operators have written notes about wells that sound or behave wrong. Which of those wells haven't had a repair since? Rank the 10 most likely to need a repair in the next 90 days, other than a spill clean-up, and quote the notes as evidence.

**Top 10 wells most likely to need a repair.**
- Well: WELL-0010; Area: Southwest Block 23; Operator-note evidence: 10 Jan: "Rod squeal at WELL-0010 stuffing box, greased the polished rod."; 13 Jan: "Rod squeal at WELL-0010 stuffing box, greased the polished rod."; 14 Jan: "Heard fluid pound on WELL-0010, unit still running."; Other warning signs in the data: wellhead gap falling (30.0 → 17.5 °C above air); not producing at latest inspection; 4 corrective repairs in 12 months; Last repair on the well: MNT-0010-031, 8 Jan 2027: Flowline leak causing spill; Score: 21; Rank: 1
- Well: WELL-0263; Area: Southwest Block 23; Operator-note evidence: 11 Jan: "Heard fluid pound on WELL-0263, unit still running."; 14 Jan: "Rod squeal at WELL-0263 stuffing box, greased the polished rod."; Other warning signs in the data: wellhead gap falling (32.7 → 4.0 °C above air); not producing at latest inspection; 4 corrective repairs in 12 months; recalled pump lot LOT-2410-B still installed; Last repair on the well: MNT-0263-035, 9 Jan 2027: Flowline corrosion pinhole leak; Score: 20; Rank: 2
- Well: WELL-0175; Area: Northeast Block 8; Operator-note evidence: 17 Dec: "Heard fluid pound on WELL-0175, unit still running."; 21 Dec: "Rod squeal at WELL-0175 stuffing box, greased the polished rod."; 26 Dec: "WELL-0175 tagging bottom on the downstroke, adjust spacing next visit."; Other warning signs in the data: wellhead gap falling (28.9 → 5.5 °C above air); not producing at latest inspection; 3 corrective repairs in 12 months; Last repair on the well: MNT-0175-035, 28 Nov 2026: Scheduled wellhead valve service; Score: 18; Rank: 3
- Well: WELL-0197; Area: Northeast Block 8; Operator-note evidence: 04 Jan: "Pumper reports rattling at WELL-0197 pump jack, keep an eye on it."; 08 Jan: "Heard fluid pound on WELL-0197, unit still running."; 12 Jan: "Heard fluid pound on WELL-0197, unit still running."; Other warning signs in the data: wellhead gap falling (21.4 → 1.2 °C above air); not producing at latest inspection; 2 corrective repairs in 12 months; Last repair on the well: MNT-0197-029, 1 Jan 2027: Sucker rod parted; Score: 17; Rank: 4
- Well: WELL-0097; Area: Southwest Block 24; Operator-note evidence: 10 Jan: "Rod squeal at WELL-0097 stuffing box, greased the polished rod."; 14 Jan: "Rod squeal at WELL-0097 stuffing box, greased the polished rod."; Other warning signs in the data: wellhead gap falling (32.0 → 6.5 °C above air); not producing at latest inspection; 3 corrective repairs in 12 months; Last repair on the well: MNT-0097-036, 8 Jan 2027: Flowline leak causing spill; Score: 17; Rank: 5
- Well: WELL-0005; Area: Southwest Block 23; Operator-note evidence: 24 Dec: "Heard fluid pound on WELL-0005, unit still running."; 30 Dec: "WELL-0005 tagging bottom on the downstroke, adjust spacing next visit."; 08 Jan: "Rod squeal at WELL-0005 stuffing box, greased the polished rod."; Other warning signs in the data: wellhead gap falling (29.2 → 25.2 °C above air); 4 corrective repairs in 12 months; Last repair on the well: MNT-0005-035, 14 Dec 2026: Scheduled lubrication and belt inspection; Score: 16; Rank: 6
- Well: WELL-0332; Area: Northwest Block 12; Operator-note evidence: 31 Dec: "Rod squeal at WELL-0332 stuffing box, greased the polished rod."; 03 Jan: "Pumper reports rattling at WELL-0332 pump jack, keep an eye on it."; Other warning signs in the data: wellhead gap falling (22.7 → 0.5 °C above air); not producing at latest inspection; 2 corrective repairs in 12 months; Last repair on the well: MNT-0332-033, 20 Nov 2026: Flowline leak causing spill; Score: 15; Rank: 7
- Well: WELL-0182; Area: Northeast Block 8; Operator-note evidence: 27 Dec: "Pumper reports rattling at WELL-0182 pump jack, keep an eye on it."; 30 Dec: "WELL-0182 tagging bottom on the downstroke, adjust spacing next visit."; 05 Jan: "Heard fluid pound on WELL-0182, unit still running."; Other warning signs in the data: 6 corrective repairs in 12 months; Last repair on the well: MNT-0182-029, 26 Dec 2026: Walking beam bearing wear; Score: 14; Rank: 8
- Well: WELL-0344; Area: Northwest Block 12; Operator-note evidence: 21 Dec: "Drive on WELL-0344 showing amps hunting between 38 and 44 A."; 24 Dec: "Drive on WELL-0344 showing amps hunting between 38 and 44 A."; 04 Jan: "WELL-0344 drive tripping on and off overnight, reset it each time."; Other warning signs in the data: 5 corrective repairs in 12 months; Last repair on the well: MNT-0344-035, 1 Dec 2026: Scheduled wellhead valve service; Score: 14; Rank: 9
- Well: WELL-0219; Area: Southeast Block 31; Operator-note evidence: 05 Jan: "WELL-0219 drive tripping on underload, restarted from the panel."; 13 Jan: "Drive on WELL-0219 showing amps hunting between 38 and 44 A."; Other warning signs in the data: wellhead gap falling (33.2 → 4.5 °C above air); not producing at latest inspection; 2 corrective repairs in 12 months; Last repair on the well: MNT-0219-022, 24 Nov 2026: Scheduled wellhead valve service; Score: 14; Rank: 10
- Notes from the last 30 days that describe abnormal sound or behaviour (fluid pound, rattling, squeal, tagging bottom, amps hunting, drive tripping, leaks); excluding gas and bypass notes and wells repaired since. Ranked by how many and how serious the notes are, plus other signs in the data. This is a judgement ranking, not a prediction model.

*Visual:* table · *Plan:* `[{"operation": "listen_ranking"}]` · *3.8s*

*Evidence:* CTX-0005-004, CTX-0005-005, CTX-0005-006, CTX-0010-005, CTX-0010-006, CTX-0010-007, CTX-0020-006, CTX-0020-007, CTX-0020-008, CTX-0021-005, CTX-0025-002, CTX-0025-003, CTX-0030-001, CTX-0030-002, CTX-0030-004, CTX-0032-005, CTX-0042-001, CTX-0042-003, CTX-0043-004, CTX-0043-005, CTX-0043-006, CTX-0044-006, CTX-0044-007, CTX-0044-008, CTX-0051-003, CTX-0054-006, CTX-0061-004, CTX-0061-005, CTX-0062-006, CTX-0065-004, CTX-0076-005, CTX-0076-006, CTX-0076-008, CTX-0080-005, CTX-0083-004, CTX-0089-001, CTX-0094-006, CTX-0097-002, CTX-0097-003, CTX-0098-004 …


## Q7.2. Robert Hayes: Which three would you send a crew to first this week, and why?

**Top 3 wells most likely to need a repair.**
- Well: WELL-0010; Area: Southwest Block 23; Operator-note evidence: 10 Jan: "Rod squeal at WELL-0010 stuffing box, greased the polished rod."; 13 Jan: "Rod squeal at WELL-0010 stuffing box, greased the polished rod."; 14 Jan: "Heard fluid pound on WELL-0010, unit still running."; Other warning signs in the data: wellhead gap falling (30.0 → 17.5 °C above air); not producing at latest inspection; 4 corrective repairs in 12 months; Last repair on the well: MNT-0010-031, 8 Jan 2027: Flowline leak causing spill; Score: 21; Rank: 1
- Well: WELL-0263; Area: Southwest Block 23; Operator-note evidence: 11 Jan: "Heard fluid pound on WELL-0263, unit still running."; 14 Jan: "Rod squeal at WELL-0263 stuffing box, greased the polished rod."; Other warning signs in the data: wellhead gap falling (32.7 → 4.0 °C above air); not producing at latest inspection; 4 corrective repairs in 12 months; recalled pump lot LOT-2410-B still installed; Last repair on the well: MNT-0263-035, 9 Jan 2027: Flowline corrosion pinhole leak; Score: 20; Rank: 2
- Well: WELL-0175; Area: Northeast Block 8; Operator-note evidence: 17 Dec: "Heard fluid pound on WELL-0175, unit still running."; 21 Dec: "Rod squeal at WELL-0175 stuffing box, greased the polished rod."; 26 Dec: "WELL-0175 tagging bottom on the downstroke, adjust spacing next visit."; Other warning signs in the data: wellhead gap falling (28.9 → 5.5 °C above air); not producing at latest inspection; 3 corrective repairs in 12 months; Last repair on the well: MNT-0175-035, 28 Nov 2026: Scheduled wellhead valve service; Score: 18; Rank: 3
- Chosen from the ranking above: WELL-0010: wellhead gap falling (30.0 → 17.5 °C above air); not producing at latest inspection; 4 corrective repairs in 12 months; WELL-0263: wellhead gap falling (32.7 → 4.0 °C above air); not producing at latest inspection; 4 corrective repairs in 12 months; recalled pump lot LOT-2410-B still installed; WELL-0175: wellhead gap falling (28.9 → 5.5 °C above air); not producing at latest inspection; 3 corrective repairs in 12 months
- Notes from the last 30 days that describe abnormal sound or behaviour (fluid pound, rattling, squeal, tagging bottom, amps hunting, drive tripping, leaks); excluding gas and bypass notes and wells repaired since. Ranked by how many and how serious the notes are, plus other signs in the data. This is a judgement ranking, not a prediction model.

*Visual:* table · *Plan:* `[{"operation": "listen_ranking", "top": 3}]` · *3.8s*

*Evidence:* CTX-0005-004, CTX-0005-005, CTX-0005-006, CTX-0010-005, CTX-0010-006, CTX-0010-007, CTX-0020-006, CTX-0020-007, CTX-0020-008, CTX-0021-005, CTX-0025-002, CTX-0025-003, CTX-0030-001, CTX-0030-002, CTX-0030-004, CTX-0032-005, CTX-0042-001, CTX-0042-003, CTX-0043-004, CTX-0043-005, CTX-0043-006, CTX-0044-006, CTX-0044-007, CTX-0044-008, CTX-0051-003, CTX-0054-006, CTX-0061-004, CTX-0061-005, CTX-0062-006, CTX-0065-004, CTX-0076-005, CTX-0076-006, CTX-0076-008, CTX-0080-005, CTX-0083-004, CTX-0089-001, CTX-0094-006, CTX-0097-002, CTX-0097-003, CTX-0098-004 …


## Q8.1. Nathan Pierce: WELL-0333's recalled pump was swapped out yesterday. The work order isn't in the system yet. Please count it as replaced from now on.

**Pump swap reported for WELL-0333.**
- Ledger id: LDG-0001; Well: WELL-0333; Statement: WELL-0333's recalled pump was swapped out yesterday. The work order isn't in the system yet. Please count it as replaced from now on.; By: Nathan Pierce; Status: reported; Visible to: everyone; Check: A recalled pump is on record for this well (Highline RP-175 SN-507591, lot LOT-2409-A, install MNT-0333-024)
- Recorded as Nathan Pierce's first-hand report. From now on WELL-0333 is counted as replaced for everyone, with this source shown. The work order is not in the maintenance system yet, so this rests on the report, not on a repair record.

*Visual:* receipt · *Plan:* `[{"operation": "record_pump_swap", "wells": ["WELL-0333"]}]` · *0.2s*

*Evidence:* LDG-0001, MNT-0333-024


## Q8.2. Nathan Pierce: Also, just for me: whenever you list wells, sort them by area and then by well ID, and show costs in thousands of dollars.

**Preference saved, private to you.**
- Preference: Sort lists; Value: area, then well ID; Applies to: you only
- Preference: Show costs in; Value: thousands of dollars; Applies to: you only
- Saved as a private preference. Other users' answers are not affected, and it is not shown in the shared ledger.

*Visual:* receipt · *Plan:* `[{"operation": "save_preference"}]` · *2.5s*

*Evidence:* LDG-0002, LDG-0003


## Q8.3. Robert Hayes: Which recalled pumps are still in the ground right now?

**8 recalled pumps still in the ground.**
- Well: WELL-0156; Area: Northeast Block 8; Team: Northeast Production; Pump: Highline RP-175 SN-952958; Lot: LOT-2409-A; Installed: 27 Jun 2026; Install job: MNT-0156-027; Cost USD: 23398.0; Source: report MNT-0156-027 (Parts installed)
- Well: WELL-0160; Area: Northeast Block 8; Team: Northeast Production; Pump: Highline RP-175 SN-429965; Lot: LOT-2409-C; Installed: 18 Jul 2026; Install job: MNT-0160-028; Cost USD: 33086.0; Source: report MNT-0160-028 (Parts installed)
- Well: WELL-0305; Area: Northwest Block 12; Team: Northwest Production; Pump: Highline RP-175 SN-978137; Lot: LOT-2409-A; Installed: 16 Oct 2026; Install job: MNT-0305-032; Cost USD: 24528.0; Source: report MNT-0305-032 (Parts installed)
- Well: WELL-0426; Area: Northwest Block 12; Team: Northwest Production; Pump: Highline RP-175 SN-880271; Lot: LOT-2409-C; Installed: 19 Jun 2026; Install job: MNT-0426-030; Cost USD: 24044.0; Source: report MNT-0426-030 (Parts installed)
- Well: WELL-0428; Area: Northwest Block 12; Team: Northwest Production; Pump: Highline RP-175 SN-708611; Lot: LOT-2410-B; Installed: 7 Mar 2026; Install job: MNT-0428-022; Cost USD: 27074.0; Source: report MNT-0428-022 (Parts installed)
- Well: WELL-0577; Area: Southeast Block 32; Team: Southeast Production; Pump: Highline RP-175 SN-757468; Lot: LOT-2409-A; Installed: 31 Jul 2026; Install job: MNT-0577-028; Cost USD: 25500.0; Source: report MNT-0577-028 (Parts installed)
- Well: WELL-0031; Area: Southwest Block 23; Team: Southwest Production; Pump: Highline RP-175 SN-664877; Lot: LOT-2409-A; Installed: 24 Apr 2026; Install job: MNT-0031-027; Cost USD: 19625.0; Source: report MNT-0031-027 (Parts installed)
- Well: WELL-0263; Area: Southwest Block 23; Team: Southwest Production; Pump: Highline RP-175 SN-187332; Lot: LOT-2410-B; Installed: 16 Oct 2026; Install job: MNT-0263-033; Cost USD: 17254.0; Source: report MNT-0263-033 (Parts installed)
- Recall notice HPC-RN-2026-07 (1 Dec 2026): Highline RP-175 pumps from lots LOT-2409-A, LOT-2409-C, LOT-2410-B; replace by 31 Dec 2026, now overdue. Current pump per well = the latest 'Parts installed' line in its repair reports.
- WELL-0333: counted as replaced on the word of Nathan Pierce (LDG-0001, 2027-01-15); work order not yet in the maintenance system

*Visual:* table · *Plan:* `[{"operation": "recalled_pumps"}]` · *2.7s*

*Evidence:* MNT-0031-027, MNT-0156-027, MNT-0160-028, MNT-0263-033, MNT-0305-032, MNT-0426-030, MNT-0428-022, MNT-0577-028, supplier-recall-notice-2026-12-01


## Q8.4. Olivia Grant: Nathan told me the recalled pump on WELL-0577 was swapped as well. Take it off the recall list.

**Pump swap reported for WELL-0577.**
- Ledger id: LDG-0004; Well: WELL-0577; Statement: Nathan told me the recalled pump on WELL-0577 was swapped as well. Take it off the recall list.; By: Olivia Grant; Status: unconfirmed; Visible to: everyone; Check: A recalled pump is on record for this well (Highline RP-175 SN-757468, lot LOT-2409-A, install MNT-0577-028)
- **Conflict:** Olivia Grant: "Nathan told me the recalled pump on WELL-0577 was swapped as well. Take it off the recall list." vs No work order, maintenance record or first-hand statement for this swap is in the system.
  - Please have the first-hand source confirm in their own session.
- Olivia Grant is relaying this second-hand, so I have recorded it as unconfirmed and have NOT taken WELL-0577 off the recall list. Ask the person who did the swap (or the work order) to confirm; the pump stays listed until then.

*Visual:* receipt · *Plan:* `[{"operation": "record_pump_swap", "wells": ["WELL-0577"]}]` · *0.3s*

*Evidence:* LDG-0004, MNT-0577-028


## Q8.5. Nathan Pierce: Show me the recalled pumps that are still in the ground in my area, and what it cost to install each one.

**3 recalled pumps still in the ground.**
- Well: WELL-0305; Area: Northwest Block 12; Team: Northwest Production; Pump: Highline RP-175 SN-978137; Lot: LOT-2409-A; Installed: 16 Oct 2026; Install job: MNT-0305-032; Source: report MNT-0305-032 (Parts installed); Cost (USD thousands): 24.5
- Well: WELL-0426; Area: Northwest Block 12; Team: Northwest Production; Pump: Highline RP-175 SN-880271; Lot: LOT-2409-C; Installed: 19 Jun 2026; Install job: MNT-0426-030; Source: report MNT-0426-030 (Parts installed); Cost (USD thousands): 24.0
- Well: WELL-0428; Area: Northwest Block 12; Team: Northwest Production; Pump: Highline RP-175 SN-708611; Lot: LOT-2410-B; Installed: 7 Mar 2026; Install job: MNT-0428-022; Source: report MNT-0428-022 (Parts installed); Cost (USD thousands): 27.1
- Recall notice HPC-RN-2026-07 (1 Dec 2026): Highline RP-175 pumps from lots LOT-2409-A, LOT-2409-C, LOT-2410-B; replace by 31 Dec 2026, now overdue. Current pump per well = the latest 'Parts installed' line in its repair reports.
- WELL-0333: counted as replaced on the word of Nathan Pierce (LDG-0001, 2027-01-15); work order not yet in the maintenance system
- Shown with your saved preferences (sorted by area then well ID; costs in thousands of dollars). These apply only to you.

*Visual:* table · *Plan:* `[{"operation": "recalled_pumps"}]` · *2.7s*

*Evidence:* MNT-0305-032, MNT-0426-030, MNT-0428-022, supplier-recall-notice-2026-12-01


## Q9.1. Robert Hayes: How many recalled pumps are still in the ground, and in which areas?

**8 recalled pumps still in the ground.**
- Well: WELL-0156; Area: Northeast Block 8; Team: Northeast Production; Pump: Highline RP-175 SN-952958; Lot: LOT-2409-A; Installed: 27 Jun 2026; Install job: MNT-0156-027; Cost USD: 23398.0; Source: report MNT-0156-027 (Parts installed)
- Well: WELL-0160; Area: Northeast Block 8; Team: Northeast Production; Pump: Highline RP-175 SN-429965; Lot: LOT-2409-C; Installed: 18 Jul 2026; Install job: MNT-0160-028; Cost USD: 33086.0; Source: report MNT-0160-028 (Parts installed)
- Well: WELL-0305; Area: Northwest Block 12; Team: Northwest Production; Pump: Highline RP-175 SN-978137; Lot: LOT-2409-A; Installed: 16 Oct 2026; Install job: MNT-0305-032; Cost USD: 24528.0; Source: report MNT-0305-032 (Parts installed)
- Well: WELL-0426; Area: Northwest Block 12; Team: Northwest Production; Pump: Highline RP-175 SN-880271; Lot: LOT-2409-C; Installed: 19 Jun 2026; Install job: MNT-0426-030; Cost USD: 24044.0; Source: report MNT-0426-030 (Parts installed)
- Well: WELL-0428; Area: Northwest Block 12; Team: Northwest Production; Pump: Highline RP-175 SN-708611; Lot: LOT-2410-B; Installed: 7 Mar 2026; Install job: MNT-0428-022; Cost USD: 27074.0; Source: report MNT-0428-022 (Parts installed)
- Well: WELL-0577; Area: Southeast Block 32; Team: Southeast Production; Pump: Highline RP-175 SN-757468; Lot: LOT-2409-A; Installed: 31 Jul 2026; Install job: MNT-0577-028; Cost USD: 25500.0; Source: report MNT-0577-028 (Parts installed); Olivia Grant relayed a second-hand swap report (LDG-0004), not confirmed, so still listed
- Well: WELL-0031; Area: Southwest Block 23; Team: Southwest Production; Pump: Highline RP-175 SN-664877; Lot: LOT-2409-A; Installed: 24 Apr 2026; Install job: MNT-0031-027; Cost USD: 19625.0; Source: report MNT-0031-027 (Parts installed)
- Well: WELL-0263; Area: Southwest Block 23; Team: Southwest Production; Pump: Highline RP-175 SN-187332; Lot: LOT-2410-B; Installed: 16 Oct 2026; Install job: MNT-0263-033; Cost USD: 17254.0; Source: report MNT-0263-033 (Parts installed)
- 8 recalled pumps are still in the ground: 2 in Northeast Block 8, 3 in Northwest Block 12, 1 in Southeast Block 32, 2 in Southwest Block 23.
- Recall notice HPC-RN-2026-07 (1 Dec 2026): Highline RP-175 pumps from lots LOT-2409-A, LOT-2409-C, LOT-2410-B; replace by 31 Dec 2026, now overdue. Current pump per well = the latest 'Parts installed' line in its repair reports.
- WELL-0333: counted as replaced on the word of Nathan Pierce (LDG-0001, 2027-01-15); work order not yet in the maintenance system

**Shared knowledge from other users:**
- WELL-0577: Olivia Grant said "Nathan told me the recalled pump on WELL-0577 was swapped as well. Take it off the recall list." (LDG-0004, unconfirmed)

*Visual:* table · *Plan:* `[{"operation": "recalled_pumps"}]` · *0.2s*

*Evidence:* MNT-0031-027, MNT-0156-027, MNT-0160-028, MNT-0263-033, MNT-0305-032, MNT-0426-030, MNT-0428-022, MNT-0577-028, supplier-recall-notice-2026-12-01


## Q9.2. Robert Hayes: Different topic. Who leads Northwest Production, and how many wells does that team run?

- Northwest Production is led by Nathan Pierce (U-601). It runs 150 wells: 150 in Northwest Block 12. Team per well uses the well's own team_id (team_history takes priority over the area's team).

*Visual:* text · *Plan:* `[{"operation": "team_info"}]` · *0.1s*

*Evidence:* areas.json, users.json


## Q9.3. Robert Hayes: What does our operations SOP say about cold weather? Name one well that missed the check in December.

**4 missed heat-trace checks in December.**
- Well: WELL-0310; Area: Northwest Block 12; Inspection: INS-0310-0213; Date: 17 Dec 2026; Air °C: -6.0; Heat trace check: none within 7 days
- Well: WELL-0354; Area: Northwest Block 12; Inspection: INS-0354-0215; Date: 17 Dec 2026; Air °C: -11.4; Heat trace check: none within 7 days
- Well: WELL-0486; Area: Southeast Block 32; Inspection: INS-0486-0219; Date: 31 Dec 2026; Air °C: -7.0; Heat trace check: none within 7 days
- Well: WELL-0531; Area: Southeast Block 32; Inspection: INS-0531-0217; Date: 31 Dec 2026; Air °C: -5.3; Heat trace check: none within 7 days
- Operations SOP OPS-5 (freeze protection, 1 Dec – 28 Feb): any inspection at or below −5 °C air on a well that is producing needs a maintenance job with issue 'Heat trace check' starting within 7 days.
- Example miss: WELL-0310 (Northwest Block 12), inspection INS-0310-0213 on 17 Dec 2026 at -6.0 °C, no heat trace check within 7 days. 4 misses in December in total.

*Visual:* table · *Plan:* `[{"operation": "freeze_checks"}]` · *0.2s*

*Evidence:* INS-0310-0213, INS-0354-0215, INS-0486-0219, INS-0531-0217, operations-sop-rev2 OPS-5


## Q9.4. Robert Hayes: An operator reported a gas smell at WELL-0332 on 3 Dec. What was the H2S reading?

- No H2S reading is recorded for WELL-0332 around 3 Dec 2026: the note reports the smell but gives no ppm value, and no repair report in the following two weeks records a monitor reading. I won't invent one.
- Note CTX-0332-004 (03 Dec 2026 12:10, Rachel Dunn): "Gas odor reported by the pumper near WELL-0332 wellhead, area flagged off."

*Visual:* text · *Plan:* `[{"operation": "h2s_reading", "wells": ["WELL-0332"]}]` · *0.1s*

*Evidence:* CTX-0332-004


## Q9.5. Robert Hayes: Back to the pumps from my first question: which of those wells are not producing oil right now, and when was each one last repaired?

**2 of those wells are not producing.**
- Well: WELL-0160; Area: Northeast Block 8; Latest inspection: INS-0160-0217, 14 Jan 2027: 3.8 °C above air; Last repaired: MNT-0160-032, 15 Jan 2027: Walking beam bearing wear
- Well: WELL-0263; Area: Southwest Block 23; Latest inspection: INS-0263-0219, 14 Jan 2027: 4.0 °C above air; Last repaired: MNT-0263-035, 9 Jan 2027: Flowline corrosion pinhole leak
- Of the 8 wells with a recalled pump in the first answer, 2 are not producing at their latest inspection (temperature rule per well type).

*Visual:* table · *Plan:* `[{"operation": "recalled_followup", "wells": ["WELL-0156", "WELL-0160", "WELL-0305", "WELL-0426", "WELL-0428", "WELL-0577", "WELL-0031", "WELL-0263"]}]` · *0.3s*

*Evidence:* INS-0160-0217, INS-0263-0219, MNT-0160-032, MNT-0263-035


## Q9.6. Robert Hayes: Of all the wells we've talked about today, which one would you deal with first, and why?

**What to deal with first.**
- Well: WELL-0160; Area: Northeast Block 8; Score: 6; Why: recalled pump lot LOT-2409-C still in the ground, past the 31 Dec 2026 deadline; not producing at the latest inspection
- Well: WELL-0263; Area: Southwest Block 23; Score: 6; Why: recalled pump lot LOT-2410-B still in the ground, past the 31 Dec 2026 deadline; not producing at the latest inspection
- Well: WELL-0031; Area: Southwest Block 23; Score: 3; Why: recalled pump lot LOT-2409-A still in the ground, past the 31 Dec 2026 deadline
- Well: WELL-0156; Area: Northeast Block 8; Score: 3; Why: recalled pump lot LOT-2409-A still in the ground, past the 31 Dec 2026 deadline
- Well: WELL-0305; Area: Northwest Block 12; Score: 3; Why: recalled pump lot LOT-2409-A still in the ground, past the 31 Dec 2026 deadline
- I would deal with WELL-0160 first: recalled pump lot LOT-2409-C still in the ground, past the 31 Dec 2026 deadline; not producing at the latest inspection.
- Judgement across the 12 wells discussed in this session. Safety first (gas/H2S response missed), then the overdue recalled pump (a cracked plunger can make the pump much harder to pull), then lost production, then approvals.

*Visual:* table · *Plan:* `[{"operation": "priority", "wells": ["WELL-0156", "WELL-0160", "WELL-0305", "WELL-0426", "WELL-0428", "WELL-0577", "WELL-0031", "WELL-0263"]}]` · *1.6s*

*Evidence:* INS-0031-0215, INS-0156-0217, INS-0160-0217, INS-0263-0219, INS-0305-0216, MNT-0031-027, MNT-0156-027, MNT-0160-028, MNT-0263-033, MNT-0305-032, supplier-recall-notice-2026-12-01


## Q10. Michael Turner: When a well stays shut in longer than the repair itself, what are we usually waiting on: parts, crews, contractors or weather? Break it down by area for jobs started in 2026, with the typical number of extra days, and tell me if any area stands out.

**Reasons shut-ins outlast the repair, by area.**
- Area: Northeast Block 7; Jobs: 3; weather share: 100%; weather typical extra days: 21; weather: 3; parts share: 0%; parts typical extra days: None; parts: 0; contractors share: 0%; contractors typical extra days: None; contractors: 0; crews share: 0%; crews typical extra days: None; crews: 0
- Area: Northeast Block 8; Jobs: 2; weather share: 50%; weather typical extra days: 21; weather: 1; parts share: 50%; parts typical extra days: 14; parts: 1; contractors share: 0%; contractors typical extra days: None; contractors: 0; crews share: 0%; crews typical extra days: None; crews: 0
- Area: Northwest Block 12; Jobs: 7; weather share: 100%; weather typical extra days: 21; weather: 7; parts share: 0%; parts typical extra days: None; parts: 0; contractors share: 0%; contractors typical extra days: None; contractors: 0; crews share: 0%; crews typical extra days: None; crews: 0
- Area: Southeast Block 31; Jobs: 7; weather share: 71%; weather typical extra days: 21; weather: 5; parts share: 29%; parts typical extra days: 14; parts: 2; contractors share: 0%; contractors typical extra days: None; contractors: 0; crews share: 0%; crews typical extra days: None; crews: 0
- Area: Southeast Block 32; Jobs: 8; weather share: 38%; weather typical extra days: 21; weather: 3; parts share: 62%; parts typical extra days: 35; parts: 5; contractors share: 0%; contractors typical extra days: None; contractors: 0; crews share: 0%; crews typical extra days: None; crews: 0
- Area: Southwest Block 23; Jobs: 5; weather share: 60%; weather typical extra days: 21; weather: 3; parts share: 40%; parts typical extra days: 14; parts: 2; contractors share: 0%; contractors typical extra days: None; contractors: 0; crews share: 0%; crews typical extra days: None; crews: 0
- Area: Southwest Block 24; Jobs: 3; weather share: 0%; weather typical extra days: None; weather: 0; parts share: 100%; parts typical extra days: 14; parts: 3; contractors share: 0%; contractors typical extra days: None; contractors: 0; crews share: 0%; crews typical extra days: None; crews: 0
- 35 jobs started in 2026 kept the well shut in longer than the repair with a recorded reason. Overall: weather 63%, parts 37%. Typical extra days = median.
- Stands out: Northeast Block 7 (weather 100%), Northwest Block 12 (weather 100%), Southwest Block 24 (parts 100%).
- No contractor or crew delays are recorded in the notes for 2026; the only delay reasons the data records are weather and waiting for parts, so those are the only two that can be reported.
- Method: extra days from operator/maintenance notes that explain the delay (their validity window), else from weekly inspections still not producing after the job finished. Reason from note wording.

*Visual:* stacked · *Plan:* `[{"operation": "waiting_reasons"}]` · *7.3s*

*Evidence:* MNT-0002-018, MNT-0020-033, MNT-0020-034, MNT-0045-025, MNT-0045-026, MNT-0072-028, MNT-0072-029, MNT-0078-022, MNT-0116-012, MNT-0133-020, MNT-0199-025, MNT-0209-019, MNT-0216-034, MNT-0217-019, MNT-0217-020, MNT-0226-025, MNT-0227-021, MNT-0241-028, MNT-0258-027, MNT-0273-015, MNT-0338-023, MNT-0366-026, MNT-0369-027, MNT-0380-028, MNT-0380-029, MNT-0414-028, MNT-0448-024, MNT-0461-022, MNT-0463-020, MNT-0492-013, MNT-0510-031, MNT-0510-032, MNT-0515-019, MNT-0520-026, MNT-0588-022


## Q11. Olivia Grant: Which region of the field consistently runs hotter?

**Southeast Block 31 runs hottest.**
- Area: Northeast Block 7; 2026-01: 27.6; 2026-02: 27.6; 2026-03: 26.7; 2026-04: 27.3; 2026-05: 26.6; 2026-06: 27.3; 2026-07: 27.2; 2026-08: 26.9; 2026-09: 27.0; 2026-10: 26.7; 2026-11: 27.2; 2026-12: 27.0; 2027-01: 26.4; Avg above air: 27.1
- Area: Northeast Block 8; 2026-01: 26.6; 2026-02: 26.2; 2026-03: 26.4; 2026-04: 26.7; 2026-05: 27.2; 2026-06: 26.8; 2026-07: 27.2; 2026-08: 26.4; 2026-09: 26.9; 2026-10: 27.0; 2026-11: 25.8; 2026-12: 24.5; 2027-01: 25.3; Avg above air: 26.4
- Area: Northwest Block 12; 2026-01: 29.0; 2026-02: 28.2; 2026-03: 28.6; 2026-04: 28.3; 2026-05: 27.7; 2026-06: 27.8; 2026-07: 28.7; 2026-08: 28.8; 2026-09: 27.7; 2026-10: 28.7; 2026-11: 28.1; 2026-12: 27.8; 2027-01: 28.0; Avg above air: 28.3
- Area: Southeast Block 31; 2026-01: 31.2; 2026-02: 31.1; 2026-03: 30.6; 2026-04: 31.2; 2026-05: 31.8; 2026-06: 31.3; 2026-07: 32.6; 2026-08: 32.1; 2026-09: 30.5; 2026-10: 32.3; 2026-11: 32.1; 2026-12: 31.1; 2027-01: 30.2; Avg above air: 31.5
- Area: Southeast Block 32; 2026-01: 28.6; 2026-02: 29.1; 2026-03: 29.3; 2026-04: 28.8; 2026-05: 28.1; 2026-06: 28.9; 2026-07: 28.4; 2026-08: 29.7; 2026-09: 28.3; 2026-10: 29.5; 2026-11: 29.1; 2026-12: 28.4; 2027-01: 27.8; Avg above air: 28.8
- Area: Southwest Block 23; 2026-01: 27.8; 2026-02: 26.6; 2026-03: 26.8; 2026-04: 26.8; 2026-05: 26.7; 2026-06: 26.8; 2026-07: 27.4; 2026-08: 27.4; 2026-09: 27.1; 2026-10: 27.7; 2026-11: 27.2; 2026-12: 26.6; 2027-01: 24.9; Avg above air: 27.0
- Area: Southwest Block 24; 2026-01: 26.8; 2026-02: 26.8; 2026-03: 26.8; 2026-04: 26.6; 2026-05: 26.6; 2026-06: 27.0; 2026-07: 26.4; 2026-08: 26.3; 2026-09: 26.2; 2026-10: 27.1; 2026-11: 26.5; 2026-12: 26.5; 2027-01: 26.5; Avg above air: 26.6
- Southeast Block 31 runs hottest: on average 31.5 °C above air, highest in 13 of 13 months (last 12 months).
- Air temperature is similar across areas (21.6–21.8 °C average), so this is the wellheads, not the weather.
- Caution: well types differ (manuals: T200 limit 15 °C, T350 20 °C, T500 25 °C; deeper types run hotter). Type mix per area: Northeast Block 7: 1 T500, 28 T350, 33 T200; Northeast Block 8: 1 T500, 23 T350, 38 T200; Northwest Block 12: 34 T500, 45 T350, 71 T200; Southeast Block 31: 29 T500, 7 T350, 14 T200; Southeast Block 32: 37 T500, 51 T350, 62 T200; Southwest Block 23: 4 T500, 23 T350, 36 T200; Southwest Block 24: 0 T500, 23 T350, 40 T200.
- Within the same type, area averages: T500: Northeast Block 7 35.9, Northeast Block 8 36.7, Northwest Block 12 34.3, Southeast Block 31 35.1, Southeast Block 32 34.5, Southwest Block 23 35.3; T350: Northeast Block 7 29.4, Northeast Block 8 29.6, Northwest Block 12 29.4, Southeast Block 31 30.4, Southeast Block 32 29.7, Southwest Block 23 29.7, Southwest Block 24 29.6; T200: Northeast Block 7 24.8, Northeast Block 8 24.2, Northwest Block 12 24.7, Southeast Block 31 24.4, Southeast Block 32 24.7, Southwest Block 23 24.3, Southwest Block 24 24.9.

*Visual:* heatmap · *Plan:* `[{"operation": "temp_by_area"}]` · *0.3s*

*Evidence:* INS-0201-0218, INS-0202-0214, INS-0208-0010, INS-0213-0221, INS-0226-0216, INS-0230-0219, INS-0245-0215, INS-0250-0153, T200 9.3 Production temperature rule, T350 3. Production temperature rule, T500 3. Production temperature rule
