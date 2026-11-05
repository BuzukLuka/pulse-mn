"use client";
import { api, fmtDate, initials, TrustCard, type Content } from "@pulse/shared";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import ComplaintForm from "@/components/ComplaintForm";
import PurchaseBox from "@/components/PurchaseBox";
import Comments from "@/components/Comments";

export default function NewsDetail() {
  const { id } = useParams<{ id: string }>();
  const [c, setC] = useState<Content | null>(null); const [err, setErr] = useState("");
  useEffect(() => { api<Content>(`/news/${id}/`, { auth: false }).then(setC).catch(() => setErr("Мэдээ олдсонгүй.")); }, [id]);
  if (err) return <div className="alert error">{err}</div>;
  if (!c) return (
    <div className="article"><div><div className="skeleton" style={{ height: 48, marginBottom: 16 }} /><div className="skeleton" style={{ height: 360 }} /></div>
      <div className="skeleton" style={{ height: 280 }} /></div>
  );
  const images = c.media.filter((m) => m.kind === "image");
  const [heroImg, ...moreImgs] = images;
  return (
    <article className="article">
      <div>
        <nav className="crumbs"><a href="/">Мэдээ</a><span>/</span>{c.category_name && <span className="badge gray">{c.category_name}</span>}
          {c.trust?.editor_verified && <span className="badge green">✓ Баталгаажсан</span>}</nav>
        <h1>{c.title}</h1>
        <div className="byline">
          <span className="avatar">{initials(c.author_name)}</span>
          <div style={{ flex: 1, minWidth: 180 }}>
            <a href={`/journalists/${c.author}`} style={{ color: "var(--text)", fontWeight: 700 }}>{c.author_name}</a>
            <div className="muted">{c.newsroom_name && <><a href={`/newsrooms/${c.newsroom}`}>🏢 {c.newsroom_name}</a> · </>}Нийтэлсэн {fmtDate(c.published_at)} · Үйл явдал {fmtDate(c.event_date)}{c.event_time ? ` ${c.event_time.slice(0, 5)}` : ""}</div>
          </div>
          <span className="muted">📍 {c.province_name}{c.district_name ? ` / ${c.district_name}` : ""}{c.location_detail ? ` · ${c.location_detail}` : ""}</span>
        </div>
        {(c.disclosure?.sponsored || c.disclosure?.political_ad) && (
          <div className="disclosure">📢 <span>{c.disclosure.political_ad ? "Улс төрийн сурталчилгаа" : "Ивээн тэтгэсэн материал"} · Захиалагч: {c.disclosure.sponsor_name}</span></div>
        )}
        {/* eslint-disable-next-line @next/next/no-img-element */}
        {heroImg && <img className="hero-img" src={heroImg.url} alt={heroImg.original_name} />}
        {c.ai_summary && <div className="card ai"><div className="eyebrow" style={{ color: "var(--violet)" }}>✨ Товч агуулга · AI</div><div>{c.ai_summary}</div></div>}
        <div className="text">{c.body}</div>
        {moreImgs.length > 0 && (
          <div className="media-grid" style={{ marginTop: 24 }}>
            {/* eslint-disable-next-line @next/next/no-img-element */}
            {moreImgs.map((m) => <img key={m.id} src={m.url} alt={m.original_name} />)}
          </div>
        )}
        {c.media.filter((m) => m.kind === "video").map((m) => <video key={m.id} src={m.url} controls style={{ width: "100%", borderRadius: 16, marginTop: 20 }} />)}
        {c.corrections?.map((x) => (
          <div key={x.id} className={`card ${x.kind === "reply" ? "correction reply" : "correction"}`} style={{ marginTop: 20 }}>
            <b>{x.kind === "reply" ? "💬" : "✏️"} {x.kind_label}</b> <small className="muted">· {fmtDate(x.created_at)}</small><div>{x.text}</div></div>
        ))}
        {c.disclosure?.conflict_of_interest && <p className="muted" style={{ marginTop: 20 }}><b>Ашиг сонирхлын мэдэгдэл:</b> {c.disclosure.conflict_of_interest}</p>}
        <p className="muted" style={{ marginTop: 28 }}><b>Эх сурвалж:</b> {c.source}</p>
        <div>{c.tags.map((t) => <span className="tag" key={t}>#{t}</span>)}</div>
        <Comments contentId={c.id} />
      </div>
      <aside>
        {c.trust && <TrustCard pub={c.trust} />}
        {!!c.price && <PurchaseBox contentId={c.id} price={c.price} authorName={c.author_name} />}
        {c.pledge_items && c.pledge_items.length > 0 && (
          <div className="card"><h3>🎯 Холбогдох амлалт</h3>
            {c.pledge_items.map((p) => <div key={p.id} style={{ marginTop: 10, fontSize: 14 }}><a href={`/pledges/${p.politician_id}`}><b>{p.politician}</b></a><div className="muted">{p.text}</div></div>)}</div>
        )}
        <div className="card"><h3>Алдаа олсон уу?</h3><p className="muted" style={{ marginTop: 0 }}>Баримтын зөрүү, буруу мэдээллийг мэдэгдээрэй.</p>
          <ComplaintForm targetType="content" targetId={c.id} /></div>
      </aside>
    </article>
  );
}
