"use client";
import { api, PledgeBar, PLEDGE_LABEL, PledgeBadge, PledgeMap, Progress, type Constituency, type Pledge, type PledgeStats, type PledgeStatus, type Politician } from "@pulse/shared";
import { useEffect, useMemo, useState } from "react";

const SYSTEM: Record<string, string> = { MAJORITARIAN: "Тойрог", PROPORTIONAL: "Намын жагсаалт" };

export default function PledgesPage() {
  const [pols, setPols] = useState<Politician[]>([]); const [sum, setSum] = useState<{ overall: PledgeStats } | null>(null);
  const [cons, setCons] = useState<Constituency[]>([]); const [con, setCon] = useState(""); const [sys, setSys] = useState("");
  const [picked, setPicked] = useState<number[]>([]); const [cmp, setCmp] = useState<Politician[]>([]);
  const [all, setAll] = useState<Pledge[]>([]); const [status, setStatus] = useState(""); const [q, setQ] = useState("");
  useEffect(() => {
    api("/pledges/summary/", { auth: false }).then(setSum).catch(() => {});
    api<Constituency[]>("/pledges/politicians/constituencies/", { auth: false }).then(setCons).catch(() => {});
  }, []);
  useEffect(() => {
    const p = new URLSearchParams(); if (con) p.set("constituency", con); if (sys) p.set("system", sys);
    api<Politician[]>(`/pledges/politicians/?${p}`, { auth: false }).then(setPols).catch(() => {});
  }, [con, sys]);
  useEffect(() => {
    const p = new URLSearchParams(); if (status) p.set("status", status); if (con) p.set("constituency", con);
    api<Pledge[]>(`/pledges/?${p}`, { auth: false }).then(setAll).catch(() => {});
  }, [status, con]);
  useEffect(() => {
    if (picked.length < 2) { setCmp([]); return; }
    api<Politician[]>(`/pledges/politicians/compare/?ids=${picked.join(",")}`, { auth: false }).then(setCmp).catch(() => {});
  }, [picked]);
  const toggle = (id: number) => setPicked((p) => (p.includes(id) ? p.filter((x) => x !== id) : [...p, id].slice(-3)));
  const shown = all.filter((p) => !q || (p.text + p.politician_name).toLowerCase().includes(q.toLowerCase()));
  const members = pols.filter((p) => !q || p.name.toLowerCase().includes(q.toLowerCase()));
  const points = useMemo(() => shown.filter((p) => p.lat != null && p.lng != null)
    .map((p) => ({ id: p.id, lat: p.lat!, lng: p.lng!, title: p.text, subtitle: `${p.politician_name}${p.location_name ? " · " + p.location_name : ""}`, progress: p.progress, href: `/pledges/${p.politician}` })), [shown]);
  const conName = cons.find((c) => String(c.constituency_number) === con)?.constituency_name;
  return (
    <>
      <h1>Амлалтын хяналт</h1>
      <p className="muted">УИХ-ын 126 гишүүний мэдээлэл <a href="https://parliament.mn" target="_blank" rel="noreferrer">parliament.mn</a>-ээс. Амлалт бүрийн явцыг баримт, иргэдийн баталгаажсан зургаар хянана.</p>
      <div className="card row" style={{ flexWrap: "wrap" }}>
        <select value={con} onChange={(e) => setCon(e.target.value)}>
          <option value="">Бүх тойрог</option>
          {cons.map((c) => <option key={c.constituency_number} value={c.constituency_number}>{c.constituency_number}-р тойрог · {c.constituency_name} ({c.members})</option>)}
        </select>
        <select value={sys} onChange={(e) => setSys(e.target.value)}><option value="">Бүх сонгогдсон</option>
          {Object.entries(SYSTEM).map(([k, v]) => <option key={k} value={k}>{v}</option>)}</select>
        <select value={status} onChange={(e) => setStatus(e.target.value)}><option value="">Бүх төлөв</option>
          {(Object.keys(PLEDGE_LABEL) as PledgeStatus[]).map((k) => <option key={k} value={k}>{PLEDGE_LABEL[k]}</option>)}</select>
        <input placeholder="Гишүүн, амлалт хайх…" value={q} onChange={(e) => setQ(e.target.value)} style={{ flex: 1, minWidth: 180 }} />
      </div>
      {sum && !con && <div className="card"><h3>Нийт биелэлт</h3><PledgeBar stats={sum.overall} /></div>}

      <h2>{conName ? `${conName} — амлалтын газрын зураг` : "Амлалтын газрын зураг"} <small className="muted">(3D · {points.length} байршил)</small></h2>
      <PledgeMap points={points} height={440} />
      <small className="muted">Өнгө: <b style={{ color: "#9ca3af" }}>●</b> эхлээгүй <b style={{ color: "#d97706" }}>●</b> эхэлсэн <b style={{ color: "#2563eb" }}>●</b> 50%+ <b style={{ color: "#16a34a" }}>●</b> дууссан · Барилгын 3D давхарга: © OpenStreetMap</small>

      <h2>Гишүүд <small className="muted">({members.length} · харьцуулахын тулд 2–3-ийг сонгоно)</small></h2>
      <div className="grid g-3">
        {members.map((p) => (
          <div className="card" key={p.id}>
            <div className="member">
              {p.photo_url ? <img src={p.photo_url} alt={p.name} loading="lazy" /> : null}
              <div style={{ flex: 1, minWidth: 0 }}>
                <a href={`/pledges/${p.id}`}><b>{p.name}</b></a>
                <div className="muted" style={{ fontSize: 13 }}>{p.party || "—"}</div>
                <div className="muted" style={{ fontSize: 13 }}>
                  {p.election_system === "MAJORITARIAN" ? `${p.constituency_number}-р тойрог · ${p.constituency_name}` : SYSTEM[p.election_system ?? ""] ?? p.position}
                  {p.votes ? ` · ${p.votes.toLocaleString()} санал` : ""}
                </div>
              </div>
              <button className={`pill ${picked.includes(p.id) ? "on" : ""}`} onClick={() => toggle(p.id)}>⇄</button>
            </div>
            <div style={{ marginTop: 10 }}>{p.stats.total ? <PledgeBar stats={p.stats} /> : <small className="muted">Амлалт бүртгэгдээгүй</small>}</div>
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
      <h2>Амлалтууд <small className="muted">({shown.length})</small></h2>
      {shown.length === 0 && <p className="muted">Амлалт олдсонгүй.</p>}
      {shown.map((p) => (
        <div key={p.id} className="card">
          <div className="row spread"><div><a href={`/pledges/${p.politician}`}>{p.politician_name}</a> — {p.text}
            <div className="muted">{p.category_name}{p.location_name ? ` · 📍 ${p.location_name}` : ""}{p.deadline ? ` · ⏳ ${p.deadline}` : ""} · нотолгоо {p.evidence_count} · иргэний мэдээ {p.updates_count}</div></div>
            <PledgeBadge status={p.status} /></div>
          <div className="row" style={{ marginTop: 8 }}><div style={{ flex: 1 }}><Progress value={p.progress} /></div><b>{p.progress}%</b></div>
        </div>
      ))}
    </>
  );
}
