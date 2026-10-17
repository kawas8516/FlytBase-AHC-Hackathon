export type Evidence = { id: string; type: string; label: string };
export type Conflict = {
  kind: string; target: string; a?: string; b?: string; ask?: string; resolution?: string;
  items?: { note: string; author: string; role: string; text: string }[];
  agrees_with_data?: string[]; also_disagrees?: string[];
};
export type Proof = { step: string; rule?: { doc: string; section: string; quote: string; value?: number; via?: string } };
export type Result = {
  op: string; title: string; rows: Record<string, any>[]; columns: string[];
  viz: { type: string; [k: string]: any }; evidence: Evidence[]; proof: Proof[];
  facts: Record<string, any>; conflicts: Conflict[]; notes: string[];
};
export type Answer = {
  text: string; ms: number; results: Result[];
  plan: { intent: string; steps: Record<string, any>[]; viz?: string; recalled?: any; router: string };
};
export type User = { user_id: string; name: string; role: string; team: string };

async function j<T>(r: Promise<Response>): Promise<T> {
  const res = await r;
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export const api = {
  meta: () => j<{ users: User[]; wells: number; today: string; rules: any[] }>(fetch("/api/meta")),
  newConv: (user_id: string, session_date: string) =>
    j<{ conv_id: number }>(fetch("/api/conversations", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ user_id, session_date }) })),
  convs: (user_id: string) => j<any[]>(fetch(`/api/conversations?user_id=${user_id}`)),
  conv: (id: number, user_id: string) => j<{ role: string; content: string; payload: Answer | null }[]>(fetch(`/api/conversations/${id}?user_id=${user_id}`)),
  ask: (user_id: string, conv_id: number, question: string) =>
    j<Answer>(fetch("/api/ask", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ user_id, conv_id, question }) })),
  memory: (user_id: string) => j<any[]>(fetch(`/api/memory?user_id=${user_id}`)),
  ledger: () => j<any[]>(fetch("/api/ledger")),
  attention: () => j<any[]>(fetch("/api/attention")),
  record: (id: string) => j<any>(fetch(`/api/record/${encodeURIComponent(id)}`)),
  reset: () => j<any>(fetch("/api/reset", { method: "POST" })),
};
