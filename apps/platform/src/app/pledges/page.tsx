"use client";
import { api, PledgeBar, PLEDGE_LABEL, PledgeBadge, type Pledge, type PledgeStats, type PledgeStatus, type Politician } from "@pulse/shared";
import { useEffect, useState } from "react";

export default function PledgesPage() {
  const [pols, setPols] = useState<Politician[]>([]); const [sum, setSum] = useState<{ overall: PledgeStats; by_category: (PledgeStats & { category: string })[] } | null>(null);
  const [picked, setPicked] = useState<number[]>([]); const [cmp, setCmp] = useState<Politician[]>([]);
  const [all, setAll] = useState<Pledge[]>([]); const [status, setStatus] = useState(""); const [q, setQ] = useState("");
  useEffect(() => {
    api<Politician[]>("/pledges/politicians/", { auth: false }).then(setPols).catch(() => {});
    api("/pledges/summary/", { auth: false }).then(setSum).catch(() => {});
  }, []);
  useEffect(() => { api<Pledge[]>(`/pledges/${status ? `?status=${status}` : ""}`, { auth: false }).then(setAll).catch(() => {}); }, [status]);
  useEffect(() => {
    if (picked.length < 2) { setCmp([]); return; }
    api<Politician[]>(`/pledges/politicians/compare/?ids=${picked.join(",")}`, { auth: false }).then(setCmp).catch(() => {});
  }, [picked]);
  const toggle = (id: number) => setPicked((p) => (p.includes(id) ? p.filter((x) => x !== id) : [...p, id].slice(-3)));
  const shown = all.filter((p) => !q || (p.text + p.politician_name).toLowerCase().includes(q.toLowerCase()));
  return (
    <>
      <h1>Амлалтын хяналт</h1>
      <p className="muted">Нэр дэвшигч, албан тушаалтны амлалт нотлох баримтад суурилан хянагдана. Баримтгүй амлалт хувьд тооцогдохгүй.</p>
      {sum && <div className="card"><h3>Нийт биелэлт</h3><PledgeBar stats={sum.overall} /><small className="muted">{sum.overall.method}</small></div>}
      <h2>Албан тушаалтнууд <small className="muted">(харьцуулахын тулд 2–3-ийг сонгоно)</small></h2>
      <div className="grid">
        {pols.map((p) => (
          <div className="card" key={p.id}>
            <div className="row spread"><a href={`/pledges/${p.id}`}><h3>{p.name}</h3></a>
              <button className={`pill ${picked.includes(p.id) ? "on" : ""}`} onClick={() => toggle(p.id)}>Харьцуулах</button></div>
            <p className="muted">{p.position} · {p.party || "—"} · {p.province_name ?? "Улс"} · {p.term_year}</p>
            <PledgeBar stats={p.stats} />
          </div>
        ))}
      </div>
      {cmp.length >= 2 && (
        <div className="card"><h3>Харьцуулалт</h3>
          <div className="table-wrap"><table><thead><tr><th></th>{cmp.map((p) => <th key={p.id}>{p.name}</th>)}</tr></thead><tbody>
            {(["fulfilled", "in_progress", "not_fulfilled"] as PledgeStatus[]).map((k) => <tr key={k}><td>{PLEDGE_LABEL[k]}</td>{cmp.map((p) => <td key={p.id}>{p.stats.percent[k] ?? "—"}%</td>)}</tr>)}
            <tr><td>Нийт амлалт</td>{cmp.map((p) => <td key={p.id}>{p.stats.total}</td>)}</tr>
          </tbody></table></div></div>
      )}
      <h2>Бүх амлалт</h2>
      <div className="card row">
        <input placeholder="Хайх…" value={q} onChange={(e) => setQ(e.target.value)} style={{ flex: 1 }} />
        <select value={status} onChange={(e) => setStatus(e.target.value)}><option value="">Бүх төлөв</option>
          {(Object.keys(PLEDGE_LABEL) as PledgeStatus[]).map((k) => <option key={k} value={k}>{PLEDGE_LABEL[k]}</option>)}</select>
      </div>
      {shown.length === 0 && <p className="muted">Амлалт олдсонгүй.</p>}
      {shown.map((p) => <div key={p.id} className="card row spread"><div><a href={`/pledges/${p.politician}`}>{p.politician_name}</a> — {p.text}<div className="muted">{p.category_name} · нотолгоо {p.evidence_count}</div></div><PledgeBadge status={p.status} /></div>)}
    </>
  );
}
