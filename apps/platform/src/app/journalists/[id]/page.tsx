"use client";
import { api, fmtDate } from "@pulse/shared";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

export default function JournalistProfile() {
  const { id } = useParams<{ id: string }>();
  const [j, setJ] = useState<any>(null); const [err, setErr] = useState("");
  useEffect(() => { api(`/journalists/${id}/`, { auth: false }).then(setJ).catch(() => setErr("Профайл олдсонгүй.")); }, [id]);
  if (err) return <div className="alert error">{err}</div>;
  if (!j) return <p className="muted">Ачаалж байна…</p>;
  return (
    <>
      <a href="/journalists">← Сэтгүүлчид</a>
      <div className="row" style={{ margin: "12px 0" }}><div className="avatar">{j.full_name.slice(0, 1)}</div>
        <div><h1 style={{ margin: 0 }}>{j.full_name} {j.is_verified && <span className="badge green">Баталгаажсан сэтгүүлч</span>}</h1>
          <div className="muted">{[j.organization, j.province, j.email, j.phone].filter(Boolean).join(" · ")}</div></div></div>
      {j.bio && <div className="card prose">{j.bio}</div>}
      {j.experiences?.length > 0 && <div className="card"><h3>Ажлын туршлага</h3>{j.experiences.map((e: any) => <div key={e.id}>{e.organization} — {e.position} <span className="muted">{e.period}</span></div>)}</div>}
      <h2>Портфолио</h2>
      {j.portfolio?.length ? j.portfolio.map((p: any) => <div className="card" key={p.id}><b>{p.title}</b> <span className="tag">{p.kind}</span> <span className="muted">{p.year ?? ""}</span>{p.url && <> · <a href={p.url} target="_blank">холбоос</a></>}</div>) : <p className="muted">Портфолио хоосон.</p>}
      <h2>Pulse.mn дээр нийтлэгдсэн</h2>
      {j.works?.map((w: any) => <div className="card" key={w.id}><a href={`/news/${w.id}`}>{w.title}</a><div className="muted">{w.province_name} · {fmtDate(w.published_at)}</div></div>)}
      {j.works?.length === 0 && <p className="muted">Одоогоор нийтлэгдсэн мэдээ алга.</p>}
    </>
  );
}
