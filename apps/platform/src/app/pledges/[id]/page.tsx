"use client";
import { api, DeadlineLine, fmtDate, PledgeBadge, PledgeBar, PledgeMap, Progress, useAuth, type Pledge, type PledgeUpdate, type Politician } from "@pulse/shared";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import ComplaintForm from "@/components/ComplaintForm";
import PledgeUpdateForm from "@/components/PledgeUpdateForm";

export default function PoliticianPage() {
  const { id } = useParams<{ id: string }>(); const { user } = useAuth();
  const [p, setP] = useState<Politician | null>(null); const [open, setOpen] = useState<Pledge | null>(null); const [err, setErr] = useState("");
  const [ups, setUps] = useState<PledgeUpdate[]>([]); const [form, setForm] = useState(false);
  useEffect(() => { api<Politician>(`/pledges/politicians/${id}/`, { auth: false }).then(setP).catch(() => setErr("Олдсонгүй.")); }, [id]);
  async function show(pl: Pledge) {
    setForm(false); setUps([]);
    setOpen(await api<Pledge>(`/pledges/${pl.id}/`, { auth: false }));
    api<PledgeUpdate[]>(`/pledges/${pl.id}/updates/`, { auth: false }).then(setUps).catch(() => {});
  }
  if (err) return <div className="alert error">{err}</div>;
  if (!p) return <p className="muted">Ачаалж байна…</p>;
  const pledges = p.pledges ?? [];
  const points = pledges.filter((x) => x.lat != null && x.lng != null).map((x) => ({ id: x.id, lat: x.lat!, lng: x.lng!, title: x.text, subtitle: x.location_name, progress: x.progress }));
  const avg = pledges.length ? Math.round(pledges.reduce((s, x) => s + (x.progress ?? 0), 0) / pledges.length) : 0;
  return (
    <>
      <a href="/pledges">← Амлалтууд</a>
      <div className="member" style={{ marginTop: 12 }}>
        {p.photo_url && <img src={p.photo_url} alt={p.name} style={{ width: 88, height: 88 }} />}
        <div>
          <h1 style={{ margin: 0 }}>{p.name}</h1>
          <p className="muted" style={{ margin: "4px 0" }}>{p.position} · {p.party || "—"} · {p.term_year} оны сонгууль</p>
          <p className="muted" style={{ margin: 0 }}>
            {p.election_system === "MAJORITARIAN" ? `${p.constituency_number}-р тойрог · ${p.constituency_name}` : p.election_system === "PROPORTIONAL" ? "Намын жагсаалтаар" : p.province_name ?? ""}
            {p.votes ? ` · ${p.votes.toLocaleString()} санал` : ""}
            {p.profile_url && <> · <a href={p.profile_url} target="_blank" rel="noreferrer">parliament.mn профайл ↗</a></>}
          </p>
        </div>
      </div>
      <div className="grid g-2" style={{ marginTop: 16 }}>
        <div className="card"><h3>Биелэлт (төлвөөр)</h3>{p.stats.total ? <PledgeBar stats={p.stats} /> : <small className="muted">Амлалт бүртгэгдээгүй</small>}</div>
        <div className="card"><h3>Дундаж явц</h3><div className="row"><div style={{ flex: 1 }}><Progress value={avg} /></div><b>{avg}%</b></div>
          <small className="muted">{pledges.length} амлалт · {pledges.filter((x) => x.deadline && new Date(x.deadline) < new Date() && x.progress < 100).length} нь хугацаа хэтэрсэн</small></div>
      </div>
      {points.length > 0 && <><h2>Мөрийн хөтөлбөрийн байршлууд</h2><PledgeMap points={points} height={380} /></>}
      <h2>Амлалтууд</h2>
      {pledges.length === 0 && <p className="muted">Мөрийн хөтөлбөрийн амлалт хараахан бүртгэгдээгүй. Pulse.mn эх сурвалжтайгаар оруулна.</p>}
      {pledges.map((pl) => (
        <div key={pl.id} className="card">
          <div className="row spread"><div><b>{pl.text}</b>
            <div className="muted">{pl.category_name}{pl.location_name ? ` · 📍 ${pl.location_name}` : ""} · Эх сурвалж: {pl.source_url ? <a href={pl.source_url} target="_blank" rel="noreferrer">{pl.source}</a> : pl.source}</div></div>
            <PledgeBadge status={pl.status} /></div>
          <div className="row" style={{ marginTop: 10 }}><div style={{ flex: 1 }}><Progress value={pl.progress} /></div><b>{pl.progress}%</b></div>
          <DeadlineLine start={pl.created_at} deadline={pl.deadline} progress={pl.progress} />
          <div className="row" style={{ marginTop: 8 }}>
            <button className="btn secondary sm" onClick={() => (open?.id === pl.id ? setOpen(null) : show(pl))}>{open?.id === pl.id ? "Хаах" : `Явц, нотолгоо (${pl.evidence_count + pl.updates_count})`}</button>
          </div>
          {open?.id === pl.id && (
            <div style={{ marginTop: 12 }}>
              <h3>Иргэдийн баталгаажсан явцын мэдээ</h3>
              {ups.length ? <div className="upd-grid">{ups.map((u) => (
                <figure key={u.id} style={{ margin: 0 }}>
                  {u.photo_url && <a href={u.photo_url} target="_blank" rel="noreferrer"><img src={u.photo_url} alt="" loading="lazy" /></a>}
                  <figcaption style={{ fontSize: 13 }}>{u.text}<div className="muted">✓ {fmtDate(u.created_at)} · {u.author_name}{u.progress_claim != null ? ` · ${u.progress_claim}%` : ""}</div></figcaption>
                </figure>))}</div> : <p className="muted">Баталгаажсан мэдээ алга.</p>}
              {user ? (form ? <div style={{ marginTop: 12 }}><PledgeUpdateForm pledge={open} /></div>
                : <button className="btn sm" style={{ marginTop: 12 }} onClick={() => setForm(true)}>📷 Явцын мэдээ, зураг оруулах</button>)
                : <p className="muted" style={{ marginTop: 12 }}><a href="/login">Нэвтэрч</a> явцын зураг, мэдээ оруулна уу.</p>}
              <h3 style={{ marginTop: 16 }}>Нотлох баримт</h3>
              {open.evidence?.length ? open.evidence.map((e) => <div key={e.id} className="muted">📎 {fmtDate(e.date)} · {e.source}{e.url && <> · <a href={e.url} target="_blank" rel="noreferrer">холбоос</a></>}{e.note && ` — ${e.note}`}</div>) : <p className="muted">Баримт бүртгэгдээгүй — «мэдээлэл дутуу».</p>}
              <h3 style={{ marginTop: 12 }}>Төлвийн түүх</h3>
              {open.history?.map((h) => <div key={h.id} className="muted">{fmtDate(h.created_at)} · {h.old_status} → <b>{h.new_status}</b> · {h.reason}</div>)}
              <div style={{ marginTop: 12 }}><ComplaintForm targetType="pledge" targetId={pl.id} /></div>
            </div>
          )}
        </div>
      ))}
    </>
  );
}
