// Builds docs/Wellspring_writeup.docx : page 1 system design, page 2 results. Run: node scripts/make_writeup.js
const fs = require("fs");
const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, WidthType, ShadingType, BorderStyle, PageBreak, AlignmentType } = require("docx");

const FONT = "Calibri";
const M = 864; // 0.6 inch margins
const W = 12240 - 2 * M; // usable width in DXA (US Letter)

const t = (text, o = {}) => new TextRun({ text, font: FONT, size: o.size || 19, bold: o.bold, italics: o.italics, color: o.color });
// paragraph from segments: strings or [text, {bold:true}]
const p = (segs, o = {}) => new Paragraph({
  spacing: { before: o.before ?? 0, after: o.after ?? 50, line: o.line || 240 },
  alignment: o.align, keepNext: o.keepNext,
  children: (Array.isArray(segs) ? segs : [segs]).map(s => typeof s === "string" ? t(s, o) : t(s[0], { ...o, ...s[1] })),
});
const h = (text) => new Paragraph({
  spacing: { before: 90, after: 30 }, keepNext: true,
  border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: "C2410C", space: 1 } },
  children: [t(text, { bold: true, size: 21, color: "9A3412" })],
});

const page1 = [
  new Paragraph({ spacing: { after: 20 }, children: [t("Wellspring: Asset Intelligence Copilot", { bold: true, size: 32 })] }),
  p([["Page 1 of 2: system design.", { bold: true }], " FlytBase Hacktoberfest 2026 hack day. Models: Gemma 4 (free tier). Cost: USD 0."], { color: "57534E", after: 40 }),

  h("Core idea: a ledger, not a pile of prompts"),
  p("Operator questions are really questions about which facts are true, for whom, at what scope, and why: a stale recorded status, an inspection later corrected as rainwater, a threshold hidden in a manual, a supervisor changing a rule for one well type, two people disagreeing. Records and documents are read-only. Everything people tell the copilot (a corrected reading, a rule, a status) is appended to a ledger with author, reason, scope and the original value kept. Every answer is derived from data + documents + ledger, so a correction reaches every user at exactly the scope it was given."),

  h("How data is stored, indexed and retrieved"),
  p("Dataset roots load into SQLite (wells, inspections, repairs, regulator events, notes, users, areas) and a full-text index over manuals, SOPs, MOC memos, the recall notice, the regulator letter, repair reports and notes. Repair reports are parsed for facts that exist only there: containment hours, compliance-check rows, installed pump model/serial/lot, and the soil-sample sentence. Ledger and per-user conversations live in a separate database so loading new data never wipes memory. The test set (600 wells, 7 areas, today = 15 Jan 2027) loads with one command; late-entered records are ordered by their own dates."),

  h("Rules come from the documents, not the code"),
  p("At load time thresholds are parsed from the manuals and SOPs into a rules table with document, section and quote: producing = wellhead at least N °C above air per well type (T200 15, T350 20, T500 25: the new type needed no code change); SR-01 report deadline with the revision in force on the discovery date (24 h before 1 Jan 2027, 12 h after, from Spill Response SOP rev 5); containment, verification, RCA counts, spill classes. The Operations SOP (gas response OPS-1, bypass/MOC OPS-2, status precedence OPS-3, freeze checks OPS-5), MOC memos (an extension memo replaces the expiry date), the recall lots and the regulator letter are read from their own text."),

  h("Tools: deterministic operators"),
  p("A question is routed (keywords first; Gemma only when unsure) to an operator that computes from data and returns rows, evidence IDs, a proof (rule + quote) and a suggested visual: well status with why-down (open repair > valid note > statement > inspector remark > \"no recorded reason\"), downtime (7 days per non-producing weekly inspection, never repair hours), spills with corrections applied, repair cost, RCA due, compliance audit, gas-response audit, bypass/MOC audit, regulator-letter audit, recalled-pump inventory, status-precedence check, operator-note ranking, waiting reasons, temperature by area, document Q&A, and a read-only SQL fallback. Numbers are exact and a 21-turn run takes under a minute."),

  h("How numbers, documents and notes combine"),
  p("Inspections give the state; the manual for the well type gives the rule; reports give facts found nowhere else; operator notes and ledger statements give reasons and recency (OPS-3: the most recent of the latest inspection and the latest shut-in/restart note wins). Each answer cites the INS / MNT / REG / CTX / LDG records and the SOP section, and \"Show the work\" lists the rule and the quote."),

  h("Two memory levels"),
  p([["Shared:", { bold: true }], " corrections, type-wide rules and statements are ledger entries visible to everyone, with author and status. ", ["Private:", { bold: true }], " each user's result sets and preferences are selected by user ID in SQL, so \"the wells we discussed\" resolves only from that user's own history, and \"just for me: sort by area, costs in $k\" applies only to them."]),

  h("Feedback, conflicts and honesty"),
  p("Corrections, rules and statements are parsed without a model. A first-hand supervisor report is applied with attribution (\"counted as replaced on Nathan Pierce's word; work order not in the system\"); a second-hand report (\"Nathan told me…\") is stored as unconfirmed and not applied; a claim that contradicts the data is shown against the data; disagreeing notes are shown side by side. When the data cannot answer (no pressure readings, no production volumes) the copilot says so and offers only a labelled proxy."),

  h("Generative UI, models and what next"),
  p("Status card, table, line chart with non-producing markers, bar and stacked bar, map, heatmap, change receipt, conflict card, evidence chips, plan chips (\"How I read this\"), proof, Rules and Ledger drawers, user and session-date pickers. Gemma 4 (31B and 26B, free tier) with an OpenRouter fallback handles unusual phrasing, document Q&A and exploratory SQL; none of the final answers needed it (median call about 30 s, which is why correctness-critical paths do not wait on it). Next: streaming, embeddings for free-form SOP questions, a number checker behind LLM narration, role-based permission for who may change rules."),
];

// ---- page 2
const B = { style: BorderStyle.SINGLE, size: 4, color: "D6D3D1" };
const borders = { top: B, bottom: B, left: B, right: B };
const cols = [900, 5700, W - 6600];
const cell = (segs, w, o = {}) => new TableCell({
  width: { size: w, type: WidthType.DXA }, borders,
  shading: o.head ? { fill: "F5F5F4", type: ShadingType.CLEAR, color: "auto" } : undefined,
  margins: { top: 25, bottom: 25, left: 70, right: 70 },
  children: [p(segs, { size: 17, after: 0, line: 230, bold: o.head })],
});
const row = (q, a, n, head) => new TableRow({ tableHeader: !!head, cantSplit: true, children: [cell(q, cols[0], { head }), cell(a, cols[1], { head }), cell(n, cols[2], { head })] });

const rows = [
  ["Q", "Answer (summary)", "What worked / limits"],
  ["1 Pressure map", "Cannot be mapped: the data has no pressure readings. Pressure appears only as equipment limits in the manuals. It lists what the data does hold.", "Declining to invent a map is the intended behaviour; no visual produced."],
  ["2 Best producer", "Cannot be answered: no production volumes. As a labelled proxy, 52 wells were producing at all 53 weekly inspections in 2026, a tie on uptime.", "Proxy is clearly marked as uptime, not output."],
  ["3 Gas reports", "26 reports since 1 Nov: 17 met the deadline, 9 missed (24 h before 1 Jan 2027, 12 h after). E.g. WELL-0163 responded after 251 h, WELL-0341 after 678 h.", "Response = job start or manual inspection after the note; drone inspections do not count (OPS-1)."],
  ["4 Bypasses", "In place now: WELL-0405 not approved, WELL-0249 expired (MOC-2026-036 ended 15 Dec), WELL-0248 allowed (MOC-2026-031 extended by -044 to 28 Feb 2027). 5 violations in total, also WELL-0158 and -0087 (expired), -0561 (not approved).", "Extension memo replaces the expiry; table has all required columns."],
  ["5 Regulator letter", "6 reportable spills in Blocks 7 and 8 since 1 Jun 2026; 3 not compliant: WELL-0123, -0182, -0262 (no \"Soil samples sent to the lab.\" in the clean-up report).", "Volume corrections applied before the 5 bbl test; not-crude detections excluded."],
  ["6 Which status is right", "12 wells where the latest inspection and a recent operator note disagree: 6 \"not producing (shut in)\", 4 \"producing (unconfirmed)\", 2 where the inspection is newer, with the OPS-3 reason for each.", "Notes older than the previous inspection are treated as superseded."],
  ["7 Operator notes", "Top 10 ranked with quoted notes and other signs. Crew first to WELL-0010, WELL-0263, WELL-0175 (falling wellhead gap, not producing, repeated repairs).", "A heuristic score, not a forecast; stated as such."],
  ["8 Who told you that", "Nathan's first-hand swap on WELL-0333 applied with attribution; Olivia's second-hand WELL-0577 swap stored as unconfirmed, pump stays listed; Nathan's sort and $k preference private; his area view shows 3 pumps with install cost in $k.", "Every turn names the source of each fact."],
  ["9 One conversation", "8 recalled pumps (2 NE-8, 3 NW-12, 1 SE-32, 2 SW-23); Northwest Production led by Nathan Pierce, 150 wells; OPS-5: 4 missed heat-trace checks in December; no H2S reading recorded for WELL-0332 (not invented); 2 recalled-pump wells not producing; deal with WELL-0160 first (overdue recall, not producing).", "Context carries across topics in one session; the H2S answer is an honest \"not recorded\"."],
  ["10 Waiting on", "35 jobs: weather 63%, parts 37%; typical extra days 21 (weather), 14 (parts), 35 for parts in Southeast Block 32. Stands out: Northeast Block 7 and Northwest Block 12 all weather, Southwest Block 24 all parts.", "Contractors and crews never appear in the notes, so they show 0; stacked bar by area."],
  ["11 Hotter region", "Southeast Block 31 runs hottest (31.5 °C above air, top in 13 of 13 months), but it has the most T500 wells; within one well type the area averages differ by only about 1 to 2.5 °C.", "The answer carries the well-type caveat."],
];

const page2 = [
  new Paragraph({ pageBreakBefore: true, spacing: { after: 20 }, children: [t("Results on the final questions", { bold: true, size: 32 })] }),
  p([["Page 2 of 2.", { bold: true }], " Test dataset: 600 wells, today = 15 Jan 2027. All 21 turns ran in one pass in under a minute; none needed the language model. Q3 to Q6 were recomputed by a separate script straight from the raw files (scripts/oracle_final.py) and match exactly. Full answers with evidence IDs are in results_final.md. Code: MIT licence."], { color: "57534E", after: 60 }),
  new Table({
    width: { size: W, type: WidthType.DXA }, columnWidths: cols,
    rows: rows.map((r, i) => row(i === 0 ? r[0] : [[r[0], { bold: true }]], r[1], r[2], i === 0)),
  }),
  h("What did not work, and why"),
  p("Gemma is slow (median about 30 s per call) and sometimes errors, so every question that matters is answered by deterministic operators; free-form questions outside the operators fall back to document search or SQL and are slower and less reliable. Q10's reasons are limited to what notes record. One well (WELL-0010) changed type mid-history; readings now use the type in force on their date. Q7's ranking and Q11's comparison are judgement calls whose method and caveats are stated in the answer. Where the data cannot answer (Q1, Q2, Q9 H2S) the copilot says so rather than guessing."),
];

const doc = new Document({
  creator: "Wellspring", title: "Wellspring write-up",
  styles: { default: { document: { run: { font: FONT, size: 18 } } } },
  sections: [{
    properties: { page: { size: { width: 12240, height: 15840 }, margin: { top: M, bottom: M - 100, left: M, right: M } } },
    children: [...page1, ...page2],
  }],
});
Packer.toBuffer(doc).then(b => { fs.writeFileSync("docs/Wellspring_writeup.docx", b); console.log("wrote docs/Wellspring_writeup.docx"); });
