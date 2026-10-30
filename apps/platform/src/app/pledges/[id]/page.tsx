"use client";
import { api, fmtDate, PledgeBadge, PledgeBar, type Pledge, type Politician } from "@pulse/shared";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import ComplaintForm from "@/components/ComplaintForm";

export default function PoliticianPage() {
  const { id } = useParams<{ id: string }>();
  const [p, setP] = useState<Politician | null>(null); const [open, setOpen] = useState<Pledge | null>(null); const [err, setErr] = useState("");
  useEffect(() => { api<Politician>(`/pledges/politicians/${id}/`, { auth: false }).then(setP).catch(() => setErr("Олдсонгүй.")); }, [id]);
  async function show(pl: Pledge) { setOpen(await api<Pledge>(`/pledges/${pl.id}/`, { auth: false })); }
  if (err) return <div className="alert error">{err}</div>;
  if (!p) return <p className="muted">Ачаалж байна…</p>;
  return (
    <>
      <a href="/pledges">← Амлалтууд</a>
      <h1 style={{ marginTop: 8 }}>{p.name}</h1>
      <p className="muted">{p.position} · {p.party || "—"} · {p.province_name ?? "Улс"} · {p.term_year} оны сонгууль</p>
      <div className="card"><PledgeBar stats={p.stats} /><small className="muted">{p.stats.method}</small></div>
      <h2>Амлалтууд</h2>
      {p.pledges?.map((pl) => (
        <div key={pl.id} className="card">
          <div className="row spread"><div><b>{pl.text}</b><div className="muted">{pl.category_name} · Эх сурвалж: {pl.source}</div></div><PledgeBadge status={pl.status} /></div>
          <button className="btn secondary sm" onClick={() => (open?.id === pl.id ? setOpen(null) : show(pl))}>{open?.id === pl.id ? "Хаах" : `Нотолгоо, түүх (${pl.evidence_count})`}</button>
          {open?.id === pl.id && (
            <div style={{ marginTop: 12 }}>
              <h3>Нотлох баримт</h3>
              {open.evidence?.length ? open.evidence.map((e) => <div key={e.id} className="muted">📎 {fmtDate(e.date)} · {e.source}{e.url && <> · <a href={e.url} target="_blank">холбоос</a></>}{e.note && ` — ${e.note}`}</div>) : <p className="muted">Баримт бүртгэгдээгүй — «мэдээлэл дутуу».</p>}
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
