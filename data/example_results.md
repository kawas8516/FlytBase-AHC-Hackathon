# Copilot results


## Q1. Michael Turner: Is WELL-0001 producing oil right now? When was it last inspected, and by whom?

**No, WELL-0001 is not producing oil right now.**
- Latest inspection INS-0001-0203 on 15 Oct 2026, by drone, by Ryan Brooks.
- The wellhead was 3.2 °C warmer than the air (25.6 vs 22.4 °C); the T200 limit is 15 °C, so it is below the limit.
- Reason: Note CTX-0001-003 by Jake Morales: Well shut in from 7 Oct for planned rod string replacement. Work order not yet in the maintenance system. Expected back online around 20 Oct.
- Inspector's remark: "Pump jack not moving."
- The recorded status still says active, which is out of date.

*Visual:* card · *Plan:* `[{"operation": "well_status", "wells": ["WELL-0001"]}]` · *0.8s*

*Evidence:* CTX-0001-003, INS-0001-0203, T200 9.3 Production temperature rule


## Q2. Michael Turner: Which wells in Northeast Block 8 are not producing oil right now, and why? Show them in a table.

**4 wells not producing in Northeast Block 8.** (WELL-0164, WELL-0170, WELL-0172 and WELL-0175)
- WELL-0164: 4.1 °C above air, recorded status active (out of date). No recorded reason. The inspector noted "Pump jack not moving.".
- WELL-0170: 2.9 °C above air, recorded status down. Repair MNT-0170-031, pump jack walking beam bearing wear, started 19 Sep 2026, still open.
- WELL-0172: 5.7 °C above air, recorded status active (out of date). Repair MNT-0172-028, flowline corrosion pinhole leak, started 3 Oct 2026, still open (inspector: "No stroke observed during flight.").
- WELL-0175: 0.4 °C above air, recorded status active (out of date). No recorded reason.
- Where nothing explains the stop, check the pump jack and prime mover on site; no cause is invented.

*Visual:* table · *Plan:* `[{"operation": "wells_status", "area": "Northeast Block 8"}]` · *0.1s*

*Evidence:* INS-0164-0205, INS-0170-0206, INS-0172-0206, INS-0175-0204, MNT-0170-031, MNT-0172-028, T200 9.3 Production temperature rule


## Q3. Michael Turner: Show a line chart of WELL-0001's wellhead temperature against air temperature for the last 13 weeks, and mark when it was not producing oil.

**13 readings from 23 Jul 2026 to 15 Oct 2026.** Not producing oil on 8 Oct 2026 and 15 Oct 2026.

*Visual:* line · *Plan:* `[{"operation": "series", "wells": ["WELL-0001"], "period": "last 13 weeks (18 Jul 2026 to 16 Oct 2026)"}]` · *0.0s*

*Evidence:* INS-0001-0191, INS-0001-0192, INS-0001-0193, INS-0001-0194, INS-0001-0195, INS-0001-0196, INS-0001-0197, INS-0001-0198, INS-0001-0199, INS-0001-0200, INS-0001-0201, INS-0001-0202, INS-0001-0203, T200 9.3 Production temperature rule


## Q4. Michael Turner: How many oil spills has WELL-0001 had in the last 4 years, and how much oil in total? List them in a table.

**6 spills, 15.1 barrels in total.**
- There were 7 detections; 1 corrected as not a spill and excluded.
- WELL-0001 16 Mar 2023: 0.5 bbl (minor)
- WELL-0001 27 Apr 2023: 2.6 bbl (moderate)
- WELL-0001 28 Sep 2023: 3.3 bbl (moderate)
- WELL-0001 19 Oct 2023: 0.3 bbl (minor)
- WELL-0001 11 Jun 2026: 6.8 bbl (reportable)
- WELL-0001 1 Oct 2026: 1.6 bbl (moderate)
- INS-0001-0070 (7 Mar 2024) was a detection corrected as not a spill by note CTX-0001-001; it does not count.

*Visual:* table · *Plan:* `[{"operation": "spills", "wells": ["WELL-0001"], "period": "last 4 years (17 Oct 2022 to 16 Oct 2026)"}]` · *0.0s*

*Evidence:* CTX-0001-001, INS-0001-0021, INS-0001-0027, INS-0001-0048, INS-0001-0051, INS-0001-0070, INS-0001-0185, INS-0001-0201


## Q5. Michael Turner: How many days was WELL-0001 down in 2025?

**WELL-0001 was down 21 days** (3 weekly inspections found it not producing oil).
- Not-producing inspections: INS-0001-0140, INS-0001-0152, INS-0001-0153
- Window: 2025-01-01 to 2025-12-31.

*Visual:* bar · *Plan:* `[{"operation": "downtime", "wells": ["WELL-0001"], "period": "2025"}]` · *0.0s*

*Evidence:* Dataset Guide: downtime, INS-0001-0140, INS-0001-0152, INS-0001-0153, T200 9.3 Production temperature rule


## Q7. Michael Turner: Show on a map every well in Northeast Block 8 with a real spill in the last 90 days.

**4 spills, 10.2 barrels in total.**
- There were 6 detections; 2 corrected as not a spill and excluded.
- WELL-0151 24 Sep 2026: 4.5 bbl (moderate)
- WELL-0165 30 Jul 2026: 1.2 bbl (moderate)
- WELL-0175 30 Jul 2026: 3.9 bbl (moderate)
- WELL-0186 23 Jul 2026: 0.6 bbl (minor)
- INS-0194-0192 (23 Jul 2026) was a detection corrected as not a spill by note CTX-0194-002; it does not count.
- INS-0199-0200 (10 Sep 2026) was a detection corrected as not a spill by note CTX-0199-002; it does not count.

*Visual:* map · *Plan:* `[{"operation": "spills", "area": "Northeast Block 8", "period": "last 90 days (19 Jul 2026 to 16 Oct 2026)"}]` · *0.0s*

*Evidence:* CTX-0194-002, CTX-0199-002, INS-0151-0201, INS-0165-0194, INS-0175-0193, INS-0186-0097, INS-0194-0192, INS-0199-0200


## Q8. Michael Turner: Show a heatmap of 2026 spills by geographic area and month.

**Northeast Block 7: 37; Northeast Block 8: 26; Southwest Block 23: 35; Southwest Block 24: 43** (corrected detections removed).
- 17 detections in this period were corrected as not a spill (rain, shadow, produced water) and excluded.

*Visual:* heatmap · *Plan:* `[{"operation": "spill_heatmap", "period": "2026"}]` · *0.0s*

*Evidence:* CTX-0003-002, CTX-0004-001, CTX-0011-001, CTX-0015-002, CTX-0024-001, CTX-0054-002, CTX-0062-001, CTX-0080-002, CTX-0081-001, CTX-0107-002, CTX-0119-001, CTX-0120-001, CTX-0121-001, CTX-0122-002, CTX-0183-001, CTX-0194-002, CTX-0199-002, INS-0001-0185, INS-0001-0201, INS-0002-0105, INS-0003-0183, INS-0004-0190, INS-0005-0174, INS-0005-0183, INS-0007-0178, INS-0010-0181, INS-0011-0201, INS-0013-0165, INS-0013-0177, INS-0013-0183, INS-0013-0188, INS-0015-0166, INS-0015-0205, INS-0017-0188, INS-0017-0198, INS-0018-0178, INS-0021-0182, INS-0022-0195, INS-0023-0181, INS-0024-0172 …


## Q9. Michael Turner: Which rules has WELL-0001 broken in the last 12 months, and what is still open?

**4 breaches; USD 5,000 in fines, still open.**
- [Breach] SR-01: Written report filed after 41 hours (REG-0001-001), limit 24 hours
- [Breach] SR-02: Contained after about 7 hours (limit 4); found only in report MNT-0001-029
- [Breach] SR-03: Clean-up verification due by 10 Aug 2026, still open
- [Breach] RC-04: Notice REG-0001-002 needed a response by 30 Jul 2026; none recorded
- [Fine] SR-01: Notice of violation REG-0001-002: USD 5,000 fine, open
- [Pending] Manual §10 RCA: Root-cause analysis due on the flowline: 3 corrective repairs in 12 months (MNT-0001-028, MNT-0001-029, MNT-0001-032); the report for MNT-0001-032 marks it as "Action required"
- [Pending] T200 manual §4: Planned shut-in from 7 Oct 2026 not yet recorded in the maintenance system, required before work starts (note CTX-0001-003)
- [Met] SR-02: Contained after about 1.7 hours (limit 4); found only in report MNT-0001-032
- [Met] RC-02: Yearly flowline test done on 7 Mar 2026 (MNT-0001-026)

*Visual:* table · *Plan:* `[{"operation": "compliance_audit", "wells": ["WELL-0001"], "period": "last 12 months (16 Oct 2025 to 16 Oct 2026)"}]` · *0.1s*

*Evidence:* CTX-0001-003, INS-0001-0185, INS-0001-0201, MNT-0001-026, MNT-0001-028, MNT-0001-029, MNT-0001-032, REG-0001-001, REG-0001-002, REG-0001-003, regulatory-compliance-sop RC-02, regulatory-compliance-sop RC-04, spill-response-sop SR-01, spill-response-sop SR-02, spill-response-sop SR-03


## Q10. Michael Turner: In Southwest Block 24, which spills in the last 90 days were not contained within the SOP time limit?

- **spill-response-sop#4. Protocols**: 4. Protocols
| Protocol ID | Requirement |
|---|---|
| **SR-01** | For a **reportable or major** spill, phone the State Oil & Gas Commission immediately, then file the **written notice** (volume, affected area, cleanup plan) within **24 hours** of discovery, or within **2 hours** for a major spill. Discovery time is the time of the inspection that detected the spill. `hours_to_report` in the data 
- **regulatory-compliance-sop#2. Protocols**: 2. Protocols
| Protocol ID | Requirement | Evidence in the data |
|---|---|---|
| **RC-01** | Every well must be inspected at least once every **14 days**. | `inspections.jsonl` timestamps |
| **RC-02** | Every flowline must pass an **integrity test once per calendar year**. | `maintenance.jsonl` entries with issue "Annual flowline integrity test" |
| **RC-03** | Any well down for more than **14 c
- **field-work-sop#3. Protocols**: 3. Protocols
| Protocol ID | Requirement |
|---|---|
| **WS-01** | Hold and record a **pre-job safety meeting** (job safety analysis) with the whole crew before any work starts. |
| **WS-02** | **Isolate energy** before touching moving or pressurised equipment. Stop the prime mover at the bottom of the stroke, set and chain the brake, lock and tag the motor disconnect, close and tag the wellhead w

*Visual:* text · *Plan:* `[{"operation": "search_docs", "area": "Southwest Block 24", "period": "last 90 days (19 Jul 2026 to 16 Oct 2026)"}]` · *57.4s*

*Evidence:* field-work-sop#3. Protocols, regulatory-compliance-sop#2. Protocols, spill-response-sop#4. Protocols


## Q6/Q11 day 1. Michael Turner: Which 3 wells in Northeast Block 7 had the most downtime in the last 4 months? Show a bar chart.

**WELL-0121: 49 days; WELL-0107: 42 days; WELL-0138: 42 days**
- Next is WELL-0119 at 28 days.
- Window: 2026-06-16 to 2026-10-16.

*Visual:* bar · *Plan:* `[{"operation": "downtime", "area": "Northeast Block 7", "top": 3, "period": "last 4 months (16 Jun 2026 to 16 Oct 2026)"}]` · *0.0s*

*Evidence:* Dataset Guide: downtime, INS-0107-0194, INS-0107-0195, INS-0107-0196, INS-0107-0197, INS-0107-0198, INS-0107-0199, INS-0121-0189, INS-0121-0200, INS-0121-0201, INS-0121-0202, INS-0121-0203, INS-0121-0205, INS-0121-0206, INS-0138-0195, INS-0138-0196, INS-0138-0200, INS-0138-0201, INS-0138-0206, INS-0138-0207, T200 9.3 Production temperature rule, T350 3. Production temperature rule


## Q11 day 2. Michael Turner: For the three wells we discussed yesterday, what have repairs cost this year?

**WELL-0107: USD 5,176 · WELL-0121: USD 25,794 · WELL-0138: USD 46,942**

*Visual:* bar · *Plan:* `[{"operation": "repairs", "period": "01 Jan 2026 to 17 Oct 2026"}]` · *0.0s*

*Evidence:* MNT-0107-025, MNT-0107-026, MNT-0107-027, MNT-0107-028, MNT-0107-029, MNT-0107-030, MNT-0121-029, MNT-0121-030, MNT-0121-031, MNT-0121-032, MNT-0121-033, MNT-0121-034, MNT-0121-035, MNT-0138-026, MNT-0138-027, MNT-0138-028, MNT-0138-029, MNT-0138-030, MNT-0138-031, MNT-0138-032, MNT-0138-033, MNT-0138-034, MNT-0138-035


## Q12. Michael Turner: The 15 Oct reading for WELL-0164 is wrong. The handheld thermal gun used in that inspection was faulty; the field crew re-measured the wellhead at 41.0 °C.

**Correction recorded against INS-0164-0205.**
- Ledger id: LDG-0001; Inspection: INS-0164-0205; Field: wellhead_temp_c; Original (kept): 24.0; Corrected to: 41.0; By: Michael Turner; Reason: The handheld thermal gun used in that inspection was faulty; the field crew re-measured the wellhead at 41.0 °C.; Scope: well WELL-0164 only
- **Conflict:** Michael Turner: wellhead 41.0 °C (producing) vs Same inspection, Tyler Hughes noted: "Pump jack not moving."
  - Michael Turner, please confirm: the inspector's note disagrees with the corrected reading.
- With 41 °C against 19.9 °C air (21.1 °C warmer, above the T200 limit of 15 °C), WELL-0164 is producing oil.

*Visual:* receipt · *Plan:* `[]` · *0.8s*

*Evidence:* INS-0164-0205, LDG-0001, T200 9.3 Production temperature rule


## Q12b. Michael Turner: Which wells in Northeast Block 8 are not producing oil right now, and why? Show them in a table.

**3 wells not producing in Northeast Block 8.** (WELL-0170, WELL-0172 and WELL-0175)
- WELL-0170: 2.9 °C above air, recorded status down. Repair MNT-0170-031, pump jack walking beam bearing wear, started 19 Sep 2026, still open.
- WELL-0172: 5.7 °C above air, recorded status active (out of date). Repair MNT-0172-028, flowline corrosion pinhole leak, started 3 Oct 2026, still open (inspector: "No stroke observed during flight.").
- WELL-0175: 0.4 °C above air, recorded status active (out of date). No recorded reason.
- WELL-0164 is no longer listed: Michael Turner corrected INS-0164-0205 wellhead_temp_c from 24.0 to 41.0 (The handheld thermal gun used in that inspection was faulty; the field crew re-measured the wellhead at 41.0 °C.), which puts it 21.1 °C above air, above the 15 °C limit.
- Where nothing explains the stop, check the pump jack and prime mover on site; no cause is invented.

*Visual:* table · *Plan:* `[{"operation": "wells_status", "area": "Northeast Block 8"}]` · *0.1s*

*Evidence:* INS-0170-0206, INS-0172-0206, INS-0175-0204, LDG-0001, MNT-0170-031, MNT-0172-028, T200 9.3 Production temperature rule


## Q13. Michael Turner: The AI estimated the 24 Sep spill at WELL-0151 as 4.5 bbl. The field crew measured 5.4 bbl.

**Correction recorded against INS-0151-0201.**
- Ledger id: LDG-0002; Inspection: INS-0151-0201; Field: spill_est_volume_bbl; Original (kept): 4.5; Corrected to: 5.4; By: Michael Turner; Reason: The AI estimated the 24 Sep spill at WELL-0151 as 4.5 bbl. The field crew measured 5.4 bbl.; Scope: well WELL-0151 only
- SR-01: Reportable spill (5.4 bbl): written notice due within 24 hours of 24 Sep 2026 15:30; none recorded (possible breach)
- SR-02: Contained after about 6.4 hours (limit 4); found only in report MNT-0151-025
- SR-03: Clean-up verification due by 23 Nov 2026
- report: Report MNT-0151-025 classed the spill as "moderate" and listed no reporting duty; with the current volume (5.4 bbl) it is reportable, so that no longer holds

*Visual:* receipt · *Plan:* `[]` · *0.8s*

*Evidence:* INS-0151-0201, LDG-0002, MNT-0151-025, spill-response-sop SR-01, spill-response-sop SR-03


## Q14a. Michael Turner: Which wells in Northeast Block 7 need a root-cause analysis on their pump jack?

**WELL-0108, WELL-0121 and WELL-0138 need a root-cause analysis.**
- WELL-0108 (T350): 3 corrective pump jack repairs in 12 months (MNT-0108-024, MNT-0108-026, MNT-0108-028); rule: T350 manual (3).
- WELL-0121 (T200): 3 corrective pump jack repairs in 12 months (MNT-0121-031, MNT-0121-034, MNT-0121-035); rule: T200 manual (3).
- WELL-0138 (T350): 3 corrective pump jack repairs in 12 months (MNT-0138-031, MNT-0138-032, MNT-0138-034); rule: T350 manual (3).

*Visual:* table · *Plan:* `[{"operation": "rca_due", "area": "Northeast Block 7", "equipment": "pump_jack"}]` · *0.3s*

*Evidence:* MNT-0108-024, MNT-0108-026, MNT-0108-028, MNT-0121-031, MNT-0121-034, MNT-0121-035, MNT-0138-031, MNT-0138-032, MNT-0138-034, T200 10. Maintenance escalation, T350 6. Maintenance escalation


## Q14b. Michael Turner: Note for all T350 wells: our team now wants a pump jack root-cause analysis after 2 repairs, not 3.

**Rule recorded.**
- Ledger id: LDG-0003; Applies to: all T350 wells; Rule: rca_corrective_count (pump jack); Manual value: 3.0; New value: 2; By: Michael Turner
- Applies only to T350 wells; other types keep the manual value.

*Visual:* receipt · *Plan:* `[]` · *0.0s*

*Evidence:* LDG-0003


## Q14c. Michael Turner: Which wells in Northeast Block 7 need a root-cause analysis on their pump jack?

**WELL-0108, WELL-0120, WELL-0121 and WELL-0138 need a root-cause analysis.**
- WELL-0108 (T350): 3 corrective pump jack repairs in 12 months (MNT-0108-024, MNT-0108-026, MNT-0108-028); rule: Michael Turner's rule for T350 (2).
- WELL-0120 (T350): 2 corrective pump jack repairs in 12 months (MNT-0120-025, MNT-0120-030); rule: Michael Turner's rule for T350 (2).
- WELL-0121 (T200): 3 corrective pump jack repairs in 12 months (MNT-0121-031, MNT-0121-034, MNT-0121-035); rule: T200 manual (3).
- WELL-0138 (T350): 3 corrective pump jack repairs in 12 months (MNT-0138-031, MNT-0138-032, MNT-0138-034); rule: Michael Turner's rule for T350 (2).
- WELL-0120 (T350, 2 repairs) is included because of Michael Turner's rule for T350 (2), not the manual.

*Visual:* table · *Plan:* `[{"operation": "rca_due", "area": "Northeast Block 7", "equipment": "pump_jack"}]` · *1.2s*

*Evidence:* LDG-0003, MNT-0108-024, MNT-0108-026, MNT-0108-028, MNT-0120-025, MNT-0120-030, MNT-0121-031, MNT-0121-034, MNT-0121-035, MNT-0138-031, MNT-0138-032, MNT-0138-034, T200 10. Maintenance escalation, T350 6. Maintenance escalation


## Q15a. Jessica Reed: Is WELL-0164 producing oil right now?

**Yes, WELL-0164 is producing oil right now.**
- Latest inspection INS-0164-0205 on 15 Oct 2026, by manual, by Tyler Hughes.
- The wellhead was 21.1 °C warmer than the air (41.0 vs 19.9 °C); the T200 limit is 15 °C, so it is above the limit.
- Inspector's remark: "Pump jack not moving."
- **Conflict:** Michael Turner: wellhead_temp_c = 41.0 vs Inspector Tyler Hughes noted: "Pump jack not moving."
  - Please confirm the corrected reading for INS-0164-0205.
- The wellhead_temp_c of INS-0164-0205 was corrected by Michael Turner from 24.0 to 41.0 (The handheld thermal gun used in that inspection was faulty; the field crew re-measured the wellhead at 41.0 °C.). Original kept.

*Visual:* card · *Plan:* `[{"operation": "well_status", "wells": ["WELL-0164"]}]` · *0.0s*

*Evidence:* INS-0164-0205, LDG-0001, T200 9.3 Production temperature rule


## Q15b. Laura Simmons: Which spills in Northeast Block 8 in the last 90 days needed a report to the regulator?

**1 spill: WELL-0151.**
- WELL-0151 (INS-0151-0201, 24 Sep 2026, 5.4 bbl): Reportable spill (5.4 bbl): written notice due within 24 hours of 24 Sep 2026 15:30; none recorded (possible breach)
- INS-0151-0201 volume corrected by Michael Turner from 4.5 to 5.4 bbl.
- Reportable means 5 bbl or more (Spill Response SOP §3); no other spill in the period reached it.

*Visual:* table · *Plan:* `[{"operation": "spills_check", "area": "Northeast Block 8", "protocol": "SR-01", "period": "last 90 days (19 Jul 2026 to 16 Oct 2026)"}]` · *0.1s*

*Evidence:* INS-0151-0201, LDG-0002, spill-response-sop SR-01


## Q16a. Jake Morales: FYI for everyone: WELL-0007 will be shut in from 17 Oct for a 10-day planned workover.

**Statement about WELL-0007.**
- Ledger id: LDG-0004; Well: WELL-0007; Statement: FYI for everyone: WELL-0007 will be shut in from 17 Oct for a 10-day planned workover.; By: Jake Morales; Status: reported; Check: No inspection since then to check against.; Visible to: everyone

*Visual:* receipt · *Plan:* `[]` · *0.0s*

*Evidence:* LDG-0004


## Q16b. Michael Turner: Is any downtime planned for WELL-0007?

**Yes.**
- From 17 Oct 2026 until 27 Oct 2026: FYI for everyone: WELL-0007 will be shut in from 17 Oct for a 10-day planned workover. (source: Jake Morales (LDG-0004, reported))

*Visual:* table · *Plan:* `[{"operation": "planned_downtime", "wells": ["WELL-0007"]}]` · *0.8s*

*Evidence:* LDG-0004


## Q16c. Jessica Reed: For the three wells we discussed yesterday, what have repairs cost this year?

- I have no earlier conversation with Jessica Reed about those wells, so I can't tell which wells you mean. Other people's conversations are private. Which wells do you want?

*Visual:* text · *Plan:* `[{"operation": "repairs"}]` · *0.0s*

*Evidence:* 


## Q17a. Michael Turner: WELL-0175 has been shut in for planned work since 14 Oct.

**Statement about WELL-0175.**
- Ledger id: LDG-0005; Well: WELL-0175; Statement: WELL-0175 has been shut in for planned work since 14 Oct.; By: Michael Turner; Status: corroborated; Check: The 15 Oct 2026 inspection (by Jessica Reed) shows the wellhead 0.4 °C above the air, so the well is not producing oil.; Visible to: everyone

*Visual:* receipt · *Plan:* `[]` · *0.0s*

*Evidence:* INS-0175-0204, LDG-0005


## Q17b. Tyler Hughes: WELL-0175 is running fine.

**Statement about WELL-0175.**
- Ledger id: LDG-0006; Well: WELL-0175; Statement: WELL-0175 is running fine.; By: Tyler Hughes; Status: unconfirmed; Check: The 15 Oct 2026 inspection (by Jessica Reed) shows the wellhead 0.4 °C above the air, so the well is not producing oil.; Visible to: everyone
- **Conflict:** Tyler Hughes: "WELL-0175 is running fine." vs The 15 Oct 2026 inspection (by Jessica Reed) shows the wellhead 0.4 °C above the air, so the well is not producing oil.
  - The data matches: Michael Turner: "WELL-0175 has been shut in for planned work since 14 Oct." (LDG-0005, corroborated)
  - Tyler Hughes, can you confirm? Your statement is kept on record as unconfirmed.

*Visual:* receipt · *Plan:* `[]` · *0.9s*

*Evidence:* INS-0175-0204, LDG-0006


## Q17c. Jake Morales: WELL-0001 is back online since 14 Oct.

**Statement about WELL-0001.**
- Ledger id: LDG-0007; Well: WELL-0001; Statement: WELL-0001 is back online since 14 Oct.; By: Jake Morales; Status: unconfirmed; Check: The 15 Oct 2026 inspection (by Ryan Brooks) shows the wellhead 3.2 °C above the air, so the well is not producing oil.; Visible to: everyone
- **Conflict:** Jake Morales: "WELL-0001 is back online since 14 Oct." vs The 15 Oct 2026 inspection (by Ryan Brooks) shows the wellhead 3.2 °C above the air, so the well is not producing oil.
  - The data matches: note CTX-0001-003 by Jake Morales: "Well shut in from 7 Oct for planned rod string replacement. Work order not yet in the maintenance system. Expected back online around 20 Oct." and note CTX-0001-003 expects a return around 20 Oct 2026
  - Jake Morales, can you confirm? Your statement is kept on record as unconfirmed.

*Visual:* receipt · *Plan:* `[]` · *0.9s*

*Evidence:* CTX-0001-003, INS-0001-0203, LDG-0007


## Q18. Laura Simmons: Was the 20 Aug spill at WELL-0101 real oil?

**Yes.** Inspection INS-0101-0197 flagged a 1.0 bbl spill ("Oil sheen around cellar.").
- **People disagree:** Ryan Brooks (field inspector, CTX-0101-002): "Inspection INS-0101-0197: I think this was only produced water, not crude."; Chris Dalton (hse officer, CTX-0101-003): "Inspection INS-0101-0197: sampled the stain, it is crude oil. The detection stands."
- Neither note is a formal correction, and spill repair MNT-0101-029 was done, so the detection stands.

*Visual:* card · *Plan:* `[{"operation": "spill_verdict", "wells": ["WELL-0101"], "date": "2026-08-20"}]` · *0.8s*

*Evidence:* CTX-0101-002, CTX-0101-003, INS-0101-0197, MNT-0101-029
