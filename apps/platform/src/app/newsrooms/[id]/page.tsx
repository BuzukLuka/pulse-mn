"use client";
import { api, fmtDate, initials, RatingBadge, RatingPanel, type PersonCard } from "@pulse/shared";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

interface NewsroomDetail extends PersonCard {
  journalists: PersonCard[];
  works: { id: number; title: string; published_at: string; author_name: string; province_name: string | null }[];
}

export default function NewsroomProfile() {
  const { id } = useParams<{ id: string }>();
  const [n, setN] = useState<NewsroomDetail | null>(null); const [err, setErr] = useState("");
  useEffect(() => { api<NewsroomDetail>(`/newsrooms/${id}/`, { auth: false }).then(setN).catch(() => setErr("Редакц олдсонгүй.")); }, [id]);
  if (err) return <div className="alert error">{err}</div>;
  if (!n) return <div className="skeleton" style={{ height: 240 }} />;
  return (
    <>
      <nav className="crumbs"><a href="/newsrooms">Редакцууд</a><span>/</span></nav>
      <div className="row" style={{ margin: "14px 0 20px" }}><div className="avatar" style={{ width: 64, height: 64, fontSize: 22 }}>{initials(n.name)}</div>
        <div><h1 style={{ margin: 0 }}>{n.name} {n.is_verified && <span className="badge green">Баталгаажсан редакц</span>}</h1>
          <div className="muted">{[n.province, `${n.members} сэтгүүлч`].filter(Boolean).join(" · ")}</div></div></div>
      <div className="article">
        <div>
          {n.bio && <div className="card prose">{n.bio}</div>}
          <h2>Сэтгүүлчид</h2>
          <div className="grid">{n.journalists.map((j) => (
            <a key={j.id} href={`/journalists/${j.id}`} className="card"><b>{j.name}</b> {j.is_verified && <span className="badge green">✓</span>}
              <div className="muted">{j.province ?? "—"} · {j.published} нийтлэл</div><RatingBadge r={j.rating} /></a>))}</div>
          {n.journalists.length === 0 && <p className="muted">Одоогоор сэтгүүлч алга.</p>}
          <h2>Редакцаар нийтлэгдсэн</h2>
          {n.works.map((w) => <div className="card" key={w.id}><a href={`/news/${w.id}`}><b>{w.title}</b></a><div className="muted">✍️ {w.author_name} · {w.province_name} · {fmtDate(w.published_at)}</div></div>)}
          {n.works.length === 0 && <p className="muted">Нийтлэгдсэн мэдээ алга.</p>}
        </div>
        <aside><RatingPanel targetId={n.id} targetLabel="Редакц" /></aside>
      </div>
    </>
  );
}
