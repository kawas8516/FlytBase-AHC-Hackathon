import { Bar, BarChart, CartesianGrid, Legend, Line, LineChart, ReferenceDot, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { CircleMarker, MapContainer, Popup, TileLayer, Tooltip as LTooltip } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import type { Result } from "./api";

const C = { well: "#c2410c", air: "#2563eb", bar: "#0f766e", down: "#dc2626" };

export function Viz({ r, onEvidence }: { r: Result; onEvidence: (id: string) => void }) {
  const t = r.viz?.type;
  if (!r.rows?.length || t === "text") return null;
  if (t === "card") return r.op === "spill_verdict" ? <SpillCard r={r} /> : <StatusCard r={r} onEvidence={onEvidence} />;
  if (t === "line") return <Line13 r={r} />;
  if (t === "bar") return <BarV r={r} />;
  if (t === "map") return <MapV r={r} />;
  if (t === "heatmap") return <Heat r={r} />;
  if (t === "stacked") return <Stacked r={r} />;
  if (t === "receipt") return <Receipt r={r} onEvidence={onEvidence} />;
  return <Table r={r} onEvidence={onEvidence} />;
}

const ID = /^(WELL|INS|MNT|REG|CTX|LDG)-[\w-]+$/;
function Cell({ v, onEvidence }: { v: any; onEvidence: (id: string) => void }) {
  if (typeof v === "string" && ID.test(v) && !v.startsWith("WELL")) return <button className="chip" onClick={() => onEvidence(v)}>{v}</button>;
  if (typeof v === "number") return <span className="num">{v.toLocaleString()}</span>;
  return <>{String(v ?? "")}</>;
}

function Table({ r, onEvidence }: { r: Result; onEvidence: (id: string) => void }) {
  const cols = r.columns?.length ? r.columns.filter((c) => !["lat", "lon", "month", "year"].includes(c)) : Object.keys(r.rows[0]);
  return (
    <div className="tablewrap">
      <table>
        <thead><tr>{cols.map((c) => <th key={c}>{c}</th>)}</tr></thead>
        <tbody>
          {r.rows.slice(0, 200).map((row, i) => (
            <tr key={i} className={row.Status === "Breach" ? "bad" : row.Status === "Pending" ? "warn" : ""}>
              {cols.map((c) => <td key={c}><Cell v={row[c]} onEvidence={onEvidence} /></td>)}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function StatusCard({ r, onEvidence }: { r: Result; onEvidence: (id: string) => void }) {
  const c = r.rows[0];
  if (!c.asset_id) return <Table r={r} onEvidence={onEvidence} />;
  const pct = Math.max(0, Math.min(100, (c.delta_c / (c.threshold_c * 2)) * 100));
  return (
    <div className="card">
      <div className="card-head">
        <div>
          <div className="eyebrow">{c.well_type} · {c.area}</div>
          <div className="card-title">{c.asset_id} <span className="muted">{c.name}</span></div>
        </div>
        <span className={`pill ${c.producing ? "ok" : "bad"}`}>{c.producing ? "Producing" : "Not producing"}</span>
      </div>
      <div className="gauge">
        <div className="gauge-bar"><div className="gauge-fill" style={{ width: `${pct}%`, background: c.producing ? "#0f766e" : "#dc2626" }} /><div className="gauge-mark" style={{ left: "50%" }} /></div>
        <div className="gauge-labels"><span>Wellhead {c.delta_c} °C above air</span><span>limit {c.threshold_c} °C</span></div>
      </div>
      <dl className="kv">
        <dt>Last inspection</dt><dd><button className="chip" onClick={() => onEvidence(c.last_inspection_id)}>{c.last_inspection_id}</button> {c.last_inspected} · {c.method} · {c.inspector}</dd>
        <dt>Readings</dt><dd>{Number(c.wellhead_temp_c).toFixed(1)} °C wellhead, {Number(c.ambient_temp_c).toFixed(1)} °C air</dd>
        <dt>Recorded status</dt><dd className={c.status_stale ? "warntext" : ""}>{c.recorded_status}</dd>
        {c.reasons?.length ? <><dt>Why</dt><dd>{c.reasons.join("; ")}</dd></> : null}
        {c.inspector_remark ? <><dt>Inspector</dt><dd>"{c.inspector_remark}"</dd></> : null}
      </dl>
      {c.evidence_images?.length ? (
        <div className="thumbs">
          {c.evidence_images.map((p: string) => (
            <div key={p} className={`thumb ${p.includes("thermal") ? "thermal" : ""}`} title={p}>
              <span>{p.includes("thermal") ? `thermal · Δ${c.delta_c}°C` : "rgb"}</span><small>{p.split("/").pop()}</small>
            </div>
          ))}
        </div>
      ) : null}
    </div>
  );
}

function SpillCard({ r }: { r: Result }) {
  const c = r.rows[0];
  return (
    <div className="card">
      <div className="card-head">
        <div><div className="eyebrow">Spill detection</div><div className="card-title">{c.inspection_id}</div></div>
        <span className={`pill ${c.verdict === "real spill" ? "bad" : "ok"}`}>{c.verdict}</span>
      </div>
      <dl className="kv">
        <dt>Volume (AI)</dt><dd>{c.volume_bbl} bbl</dd>
        <dt>Inspector</dt><dd>"{c.remark}"</dd>
        <dt>Formal correction</dt><dd>{c.formal_correction.length ? c.formal_correction.join(", ") : "none"}</dd>
        <dt>Repairs</dt><dd>{c.repairs.join(", ") || "none"}</dd>
      </dl>
    </div>
  );
}

function Line13({ r }: { r: Result }) {
  const data = r.rows;
  return (
    <div className="chart">
      <ResponsiveContainer width="100%" height={280}>
        <LineChart data={data} margin={{ top: 10, right: 20, bottom: 10, left: 0 }}>
          <CartesianGrid stroke="#e7e5e4" vertical={false} />
          <XAxis dataKey="label" tick={{ fontSize: 11 }} />
          <YAxis unit="°C" tick={{ fontSize: 11 }} />
          <Tooltip />
          <Legend />
          <Line dataKey="wellhead_temp_c" name="Wellhead" stroke={C.well} strokeWidth={2} dot={{ r: 3 }} isAnimationActive={false} />
          <Line dataKey="ambient_temp_c" name="Air" stroke={C.air} strokeWidth={2} dot={false} isAnimationActive={false} />
          {data.filter((d) => !d.producing).map((d, i) => (
            <ReferenceDot key={d.label} x={d.label} y={d.wellhead_temp_c} r={7} fill={C.down} stroke="#fff" ifOverflow="visible" label={i === 0 ? { value: "not producing", position: "top", fontSize: 10, fill: C.down } : undefined} />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

function BarV({ r }: { r: Result }) {
  const x = r.viz.x || r.columns[0];
  const y = r.viz.y || r.columns.find((c) => typeof r.rows[0][c] === "number") || r.columns[1];
  return (
    <div className="chart">
      <ResponsiveContainer width="100%" height={260}>
        <BarChart data={r.rows} margin={{ top: 20, right: 20, bottom: 10, left: 0 }}>
          <CartesianGrid stroke="#e7e5e4" vertical={false} />
          <XAxis dataKey={x} tick={{ fontSize: 11 }} />
          <YAxis tick={{ fontSize: 11 }} />
          <Tooltip />
          <Bar dataKey={y} fill={C.bar} radius={[4, 4, 0, 0]} label={{ position: "top", fontSize: 11 }} isAnimationActive={false} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

const STACK = ["#0f766e", "#c2410c", "#2563eb", "#7c3aed"];
function Stacked({ r }: { r: Result }) {
  const series: string[] = r.viz.series || [];
  return (
    <div className="chart">
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={r.rows} margin={{ top: 20, right: 20, bottom: 10, left: 0 }}>
          <CartesianGrid stroke="#e7e5e4" vertical={false} />
          <XAxis dataKey={r.viz.x || "Area"} tick={{ fontSize: 11 }} />
          <YAxis allowDecimals={false} tick={{ fontSize: 11 }} label={{ value: "jobs", angle: -90, position: "insideLeft", fontSize: 11 }} />
          <Tooltip />
          <Legend />
          {series.map((s, i) => <Bar key={s} dataKey={s} stackId="a" fill={STACK[i % STACK.length]} isAnimationActive={false} />)}
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

function MapV({ r }: { r: Result }) {
  const pts = r.rows.filter((p) => p.lat && p.lon);
  if (!pts.length) return null;
  const lat = pts.reduce((s, p) => s + p.lat, 0) / pts.length, lon = pts.reduce((s, p) => s + p.lon, 0) / pts.length;
  return (
    <div className="map">
      <MapContainer center={[lat, lon]} zoom={12} style={{ height: 320, width: "100%" }} scrollWheelZoom={false}>
        <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" attribution="&copy; OpenStreetMap" />
        {pts.map((p, i) => (
          <CircleMarker key={i} center={[p.lat, p.lon]} radius={6 + (p.Barrels || 1) * 1.5} pathOptions={{ color: "#b91c1c", fillOpacity: 0.6 }}>
            <LTooltip permanent direction="right">{p.Well} · {p.Barrels} bbl</LTooltip>
            <Popup>{p.Well}<br />{p.Date}<br />{p.Barrels} bbl<br />{p.lat}, {p.lon}</Popup>
          </CircleMarker>
        ))}
      </MapContainer>
    </div>
  );
}

function Heat({ r }: { r: Result }) {
  const cols: string[] = r.viz.cols;
  const max = Math.max(1, ...r.rows.flatMap((row) => cols.map((c) => row[c] || 0)));
  return (
    <div className="tablewrap">
      <table className="heat">
        <thead><tr><th>{r.viz.row}</th>{cols.map((c) => <th key={c}>{c}</th>)}<th>Total</th></tr></thead>
        <tbody>
          {r.rows.map((row) => (
            <tr key={row[r.viz.row]}>
              <td className="rowhead">{row[r.viz.row]}</td>
              {cols.map((c) => {
                const v = row[c] || 0;
                return <td key={c} style={{ background: `rgba(194, 65, 12, ${0.08 + 0.8 * (v / max)})`, color: v / max > 0.55 ? "#fff" : "#1c1917" }}>{v}</td>;
              })}
              <td className="num strong">{row.Total}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function Receipt({ r, onEvidence }: { r: Result; onEvidence: (id: string) => void }) {
  return (
    <div className="receipt">
      <div className="eyebrow">Recorded in the ledger · original kept</div>
      {r.rows.map((row, i) => (
        <dl className="kv" key={i}>
          {Object.entries(row).map(([k, v]) => (
            <><dt key={k}>{k}</dt><dd key={k + "v"} className={k.startsWith("Original") ? "was" : k.startsWith("Corrected") || k === "New value" ? "now" : ""}><Cell v={v} onEvidence={onEvidence} /></dd></>
          ))}
        </dl>
      ))}
    </div>
  );
}
