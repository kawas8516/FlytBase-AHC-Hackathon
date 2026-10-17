import { useEffect, useRef, useState } from "react";
import Markdown from "react-markdown";
import { api, type Answer, type User } from "./api";
import { Viz } from "./Viz";

type Msg = { role: "user" | "assistant"; content: string; payload?: Answer | null; pending?: boolean };

const SUGGEST = [
  "Is WELL-0001 producing oil right now? When was it last inspected, and by whom?",
  "Which wells in Northeast Block 8 are not producing oil right now, and why? Show them in a table.",
  "Which 3 wells in Northeast Block 7 had the most downtime in the last 4 months? Show a bar chart.",
  "Show a heatmap of 2026 spills by geographic area and month.",
  "Which rules has WELL-0001 broken in the last 12 months, and what is still open?",
];

export default function App() {
  const [users, setUsers] = useState<User[]>([]);
  const [today, setToday] = useState("");
  const [nWells, setNWells] = useState(0);
  const [user, setUser] = useState("U-201");
  const [sessionDate, setSessionDate] = useState("");
  const [conv, setConv] = useState<number | null>(null);
  const [convs, setConvs] = useState<any[]>([]);
  const [msgs, setMsgs] = useState<Msg[]>([]);
  const [q, setQ] = useState("");
  const [busy, setBusy] = useState(false);
  const [drawer, setDrawer] = useState<{ kind: "record" | "ledger" | "proof"; data: any } | null>(null);
  const [attention, setAttention] = useState<any[]>([]);
  const end = useRef<HTMLDivElement>(null);

  useEffect(() => {
    api.meta().then((m) => { setUsers(m.users); setToday(m.today); setSessionDate(m.today); setNWells(m.wells); });
    api.attention().then(setAttention).catch(() => {});
  }, []);
  useEffect(() => { if (user) { api.convs(user).then(setConvs); setConv(null); setMsgs([]); } }, [user]);
  useEffect(() => { end.current?.scrollIntoView({ behavior: "smooth" }); }, [msgs]);

  const me = users.find((u) => u.user_id === user);

  async function ensureConv() {
    if (conv) return conv;
    const c = await api.newConv(user, sessionDate || today);
    setConv(c.conv_id);
    return c.conv_id;
  }

  async function send(text?: string) {
    const question = (text ?? q).trim();
    if (!question || busy) return;
    setQ("");
    setBusy(true);
    setMsgs((m) => [...m, { role: "user", content: question }, { role: "assistant", content: "", pending: true }]);
    try {
      const id = await ensureConv();
      const a = await api.ask(user, id, question);
      setMsgs((m) => [...m.slice(0, -1), { role: "assistant", content: a.text, payload: a }]);
      api.convs(user).then(setConvs);
      api.attention().then(setAttention).catch(() => {});
    } catch (e: any) {
      setMsgs((m) => [...m.slice(0, -1), { role: "assistant", content: `Error: ${e.message}` }]);
    } finally {
      setBusy(false);
    }
  }

  async function openConv(id: number) {
    setConv(id);
    const ms = await api.conv(id, user);
    setMsgs(ms.map((m) => ({ role: m.role as any, content: m.content, payload: m.payload })));
  }

  async function openEvidence(id: string) {
    try { setDrawer({ kind: "record", data: { id, ...(await api.record(id)) } }); }
    catch { setDrawer({ kind: "record", data: { id, error: "Not found" } }); }
  }

  return (
    <div className="app">
      <header className="top">
        <div className="brand"><span className="logo">◉</span> Wellspring <span className="muted">Asset Intelligence Copilot</span></div>
        <div className="controls">
          <label>User
            <select value={user} onChange={(e) => setUser(e.target.value)}>
              {users.map((u) => <option key={u.user_id} value={u.user_id}>{u.name} · {u.role.replace(/_/g, " ")}</option>)}
            </select>
          </label>
          <label title="Simulated date of this chat session, for 'yesterday' memory">Session date
            <input type="date" value={sessionDate} onChange={(e) => setSessionDate(e.target.value)} />
          </label>
          <button className="btn" onClick={() => { setConv(null); setMsgs([]); }}>New chat</button>
          <button className="btn ghost" onClick={async () => setDrawer({ kind: "ledger", data: await api.ledger() })}>Ledger</button>
        </div>
      </header>

      <aside className="side">
        <div className="side-section">
          <div className="side-title">Your conversations</div>
          {convs.length === 0 && <div className="muted small">None yet</div>}
          {convs.map((c) => (
            <button key={c.id} className={`conv ${c.id === conv ? "active" : ""}`} onClick={() => openConv(c.id)}>
              <span className="small muted">{c.session_date}</span>
              <span className="ellipsis">{c.first || "(empty)"}</span>
            </button>
          ))}
        </div>
        <div className="side-section grow">
          <div className="side-title">Needs attention <span className="count">{attention.length}</span></div>
          {attention.map((a, i) => (
            <button key={i} className={`attn ${a.severity}`} onClick={() => send(a.ask)}>
              <span className="attn-kind">{a.kind} · <b>{a.well}</b></span>
              <span className="small">{a.detail}</span>
            </button>
          ))}
        </div>
      </aside>

      <main className="chat">
        {msgs.length === 0 && (
          <div className="empty">
            <h1>Ask about your wells</h1>
            <p className="muted">{nWells} wells · today is {today} · signed in as {me?.name} ({me?.team})</p>
            <div className="suggest">{SUGGEST.map((s) => <button key={s} onClick={() => send(s)}>{s}</button>)}</div>
          </div>
        )}
        {msgs.map((m, i) => (
          <div key={i} className={`msg ${m.role}`}>
            {m.role === "user" ? <div className="bubble">{m.content}</div> : m.pending ? <div className="thinking">Reading the records…</div> : (
              <AnswerView m={m} onEvidence={openEvidence} onProof={(p) => setDrawer({ kind: "proof", data: p })} />
            )}
          </div>
        ))}
        <div ref={end} />
        <form className="composer" onSubmit={(e) => { e.preventDefault(); send(); }}>
          <input value={q} onChange={(e) => setQ(e.target.value)} placeholder={`Ask as ${me?.name ?? ""}… e.g. "Which wells in Northeast Block 7 need a root-cause analysis on their pump jack?"`} />
          <button className="btn primary" disabled={busy}>{busy ? "…" : "Ask"}</button>
        </form>
      </main>

      {drawer && (
        <aside className="drawer">
          <div className="drawer-head">
            <b>{drawer.kind === "record" ? drawer.data.id : drawer.kind === "ledger" ? "Ledger (shared knowledge)" : "Show the work"}</b>
            <button className="btn ghost" onClick={() => setDrawer(null)}>Close</button>
          </div>
          {drawer.kind === "record" && <RecordView d={drawer.data} />}
          {drawer.kind === "ledger" && <LedgerView rows={drawer.data} />}
          {drawer.kind === "proof" && <ProofView a={drawer.data} onEvidence={openEvidence} />}
        </aside>
      )}
    </div>
  );
}

function AnswerView({ m, onEvidence, onProof }: { m: Msg; onEvidence: (id: string) => void; onProof: (a: Answer) => void }) {
  const a = m.payload;
  return (
    <div className="answer">
      {a?.plan?.steps?.length ? (
        <div className="plan">
          <span className="plan-label">How I read this</span>
          {a.plan.steps.map((s, i) => Object.entries(s).map(([k, v]) => <span key={i + k} className="pchip"><i>{k}</i> {Array.isArray(v) ? v.join(", ") : String(v)}</span>))}
          {a.plan.viz && <span className="pchip"><i>visual</i> {a.plan.viz}</span>}
          {a.plan.recalled && <span className="pchip memory"><i>recalled</i> {a.plan.recalled.wells.join(", ")} from your chat on {a.plan.recalled.session_date}</span>}
          <span className="pchip ghost"><i>router</i> {a.plan.router}</span>
        </div>
      ) : a?.plan?.intent && a.plan.intent !== "query" ? <div className="plan"><span className="plan-label">Understood as</span><span className="pchip"><i>intent</i> {a.plan.intent}</span></div> : null}
      <div className="md"><Markdown>{m.content}</Markdown></div>
      {a?.results.map((r, i) => (
        <div key={i}>
          {r.conflicts?.length ? r.conflicts.map((c, j) => (
            <div key={j} className="conflict">
              <div className="eyebrow">Conflict · {c.kind.replace(/_/g, " ")} · {c.target}</div>
              {c.items ? c.items.map((it) => <div key={it.note}><b>{it.author}</b> ({it.role.replace(/_/g, " ")}): "{it.text}" <button className="chip" onClick={() => onEvidence(it.note)}>{it.note}</button></div>)
                : <><div><b>Says:</b> {c.a}</div><div><b>But:</b> {c.b}</div></>}
              {c.resolution && <div className="muted">{c.resolution}</div>}
              {c.ask && <div className="ask">{c.ask}</div>}
            </div>
          )) : null}
          <Viz r={r} onEvidence={onEvidence} />
        </div>
      ))}
      {a && (
        <div className="evidence">
          <span className="plan-label">Evidence</span>
          {dedupe(a.results.flatMap((r) => r.evidence)).slice(0, 30).map((e) => (
            <button key={e.id} className={`chip ${e.type}`} title={e.label} onClick={() => onEvidence(e.id)}>{e.id}</button>
          ))}
          <button className="btn tiny" onClick={() => onProof(a)}>Show the work</button>
          <span className="muted small">{(a.ms / 1000).toFixed(1)} s</span>
        </div>
      )}
    </div>
  );
}

function dedupe<T extends { id: string }>(xs: T[]) {
  const s = new Set<string>();
  return xs.filter((x) => (s.has(x.id) ? false : (s.add(x.id), true)));
}

function RecordView({ d }: { d: any }) {
  if (d.error) return <p className="muted">{d.error}</p>;
  return (
    <div className="record">
      <div className="eyebrow">{d.type}</div>
      {d.record && <dl className="kv">{Object.entries(d.record).filter(([k]) => !["text", "equipment_json", "evidence_json"].includes(k) || d.type !== "doc").map(([k, v]) => <><dt key={k}>{k}</dt><dd key={k + "v"}>{String(v ?? "")}</dd></>)}</dl>}
      {d.report && <div className="md report"><Markdown>{d.report}</Markdown></div>}
    </div>
  );
}

function LedgerView({ rows }: { rows: any[] }) {
  if (!rows.length) return <p className="muted">Nothing recorded yet. Corrections, rules and statements from any user appear here, with author and scope.</p>;
  return (
    <div className="ledger">
      {rows.map((f) => (
        <div key={f.id} className={`lrow ${f.status}`}>
          <div className="eyebrow">{f.id} · {f.kind.replace(/_/g, " ")} · {f.status}</div>
          <div><b>{f.author}</b> on {f.scope_type} <b>{f.scope_id}</b>{f.target ? ` (${f.target})` : ""}</div>
          {f.field && f.original != null && <div>{f.field}: <s>{f.original}</s> → <b>{f.value}</b></div>}
          {f.key && <div>{f.key}{f.equipment_kind ? ` (${f.equipment_kind})` : ""}: {f.original} → <b>{f.value}</b></div>}
          {f.text && <div className="muted">"{f.text}"</div>}
          {f.reason && <div className="muted small">Why: {f.reason}</div>}
        </div>
      ))}
    </div>
  );
}

function ProofView({ a, onEvidence }: { a: Answer; onEvidence: (id: string) => void }) {
  return (
    <div className="proof">
      {a.results.map((r, i) => (
        <div key={i} className="proof-block">
          <div className="eyebrow">Operator · {r.op}</div>
          <div className="proof-title">{r.title}</div>
          {r.proof.map((p, j) => (
            <div key={j} className="proof-step">
              <div>{p.step}</div>
              {p.rule && <blockquote>{p.rule.doc} · {p.rule.section}{p.rule.via ? ` (via ${p.rule.via})` : ""}<br /><i>{p.rule.quote}</i></blockquote>}
            </div>
          ))}
          <div className="small muted">Key facts: {JSON.stringify(r.facts)}</div>
          <div className="evidence">{r.evidence.map((e) => <button key={e.id} className={`chip ${e.type}`} onClick={() => onEvidence(e.id)}>{e.id}</button>)}</div>
        </div>
      ))}
    </div>
  );
}
