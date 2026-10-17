# Narration script: read this over docs/demo/wellspring_demo_silent.mp4 (3:28)
Start times are approximate (from the synthetic voice); match the screen, not the clock. Speak a little slower than normal.

**0:00  [slide:title]**

This is Wellspring, a copilot that answers operators' plain-English questions about their wells, with the evidence, and remembers what people tell it. The test set has six hundred wells, seven areas, and new documents.

**0:14  [slide:idea]**

The core idea is a ledger, not a pile of prompts. Records and documents stay read-only. Everything people tell the copilot, a correction, a rule, a status, goes into a ledger with who said it, why, at what scope, and the original value is kept. Every answer is built from data, documents and the ledger.

**0:35  [slide:arch]**

Data is loaded into a database and a search index. Rules are parsed out of the manuals, SOPs, memos, the recall notice and the regulator letter. Deterministic operators do the maths and return rows, evidence and proof. The language model, Gemma, is only used for unusual phrasing, and none of the final answers needed it.

**0:56  [rules]**

Here are the rules the copilot read from the documents. T200 needs fifteen degrees above air, T350 twenty. The new T500 well type from the test data, twenty-five, was picked up automatically with no code change. Even the S R zero one deadline follows the SOP revision: twenty-four hours before January first, twelve hours after.

**1:20  [ask:q1:Michael Turner]**

First, an honest answer. Asked to map reservoir pressure, it says the data has no pressure readings. Pressure appears only as equipment limits in the manuals, so a map would be invented. It does not make one up.

**1:37  [ask:q3:Laura Simmons]**

Gas reports. Under the operations SOP, every gas or H2S note needs a field response, a repair job or a manual inspection, within twenty-four hours before January first and twelve hours after. Twenty-six reports, nine missed. Each row shows the note, the response record and the hours.

**2:02  [ask:q4:Chris Dalton]**

Temporary bypasses. The copilot reads the management of change memos. Well zero-four-zero-five has no approval. Well zero-two-four-nine is past its expiry. Well zero-two-four-eight is allowed because memo forty-four extended memo thirty-one. And every row cites its notes and memo.

**2:24  [ask:q8a:Nathan Pierce]**

Now memory. Nathan Pierce, a supervisor, reports that the recalled pump on well three-three-three was swapped. The copilot records it as his first-hand report, with the work order missing, and applies it for everyone.

**2:42  [ask:q8b:Olivia Grant]**

Olivia Grant says Nathan told her another pump was swapped. That is second-hand, so it is stored as unconfirmed and the pump stays on the recall list until someone confirms.

**2:57  [ask:q8c:Robert Hayes]**

Robert Hayes asks which recalled pumps are still in the ground. Eight wells. Well three-three-three is off the list, with Nathan named as the source. The other pump is still listed.

**3:12  [ledger]**

The ledger shows what is shared with everyone: who said it, the status, and the original. Private preferences and each person's own conversations are kept apart, so one person's history never leaks to another.

**3:26  [ask:q10:Michael Turner]**

Last, a judgement question. When a well stays shut in longer than the repair, what are we waiting on? Weather accounts for sixty-three percent and parts for thirty-seven. Contractors and crews never appear in the notes, so it says so, and flags the areas that stand out.

**3:46  [slide:close]**

In short: rules read from the documents, deterministic operators, a ledger with provenance, and honest answers when the data cannot say. Thank you.
