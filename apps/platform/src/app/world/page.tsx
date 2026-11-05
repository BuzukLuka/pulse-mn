"use client";
import { api, Empty, fmtDateTime, qs, type Category, type ExternalArticle, type Paginated } from "@pulse/shared";
import { useEffect, useState } from "react";

interface Sources { sources: { key: string; name: string; home: string; enabled: boolean; count: number }[]; last_run: { at: string; added: number } | null }
const LANG: Record<string, string> = { mn: "🇲🇳 Монгол", en: "🇬🇧 Англи", ru: "🇷🇺 Орос" };

export default function WorldNews() {
  const [data, setData] = useState<Paginated<ExternalArticle> | null>(null); const [src, setSrc] = useState<Sources | null>(null);
  const [source, setSource] = useState(""); const [category, setCategory] = useState(""); const [q, setQ] = useState(""); const [page, setPage] = useState(1);
  const [categories, setCategories] = useState<Category[]>([]); const [err, setErr] = useState("");
  useEffect(() => {
    api<Category[]>("/catalog/categories/", { auth: false }).then(setCategories).catch(() => {});
  }, []);
  useEffect(() => {
    const t = setTimeout(() => {
      api<Paginated<ExternalArticle>>(`/world-news/${qs({ source, category, q, page })}`, { auth: false })
        .then((d) => { setData(d); setErr(""); api<Sources>("/world-news/sources/", { auth: false }).then(setSrc).catch(() => {}); })
        .catch(() => setErr("Мэдээ ачаалж чадсангүй."));
    }, 250);
    return () => clearTimeout(t);
  }, [source, category, q, page]);

  return (
    <>
      <div className="page-head">
        <div><div className="eyebrow"><span className="live" /> AI · Дэлхийн хэвлэл</div><h1>Дэлхийд Монголын тухай</h1></div>
        {src?.last_run && <small className="muted">Сүүлд шинэчилсэн: {fmtDateTime(src.last_run.at)}</small>}
      </div>
      <div className="filters">
        <div className="pill-row">
          <button className={`pill ${source === "" ? "on" : ""}`} onClick={() => { setSource(""); setPage(1); }}>Бүх эх сурвалж</button>
          {src?.sources.filter((s) => s.enabled && s.count > 0).map((s) => (
            <button key={s.key} className={`pill ${source === s.key ? "on" : ""}`} onClick={() => { setSource(s.key); setPage(1); }}>{s.name} · {s.count}</button>))}
        </div>
        <div className="row">
          <input placeholder="Хайх…" value={q} onChange={(e) => { setQ(e.target.value); setPage(1); }} />
          <select value={category} onChange={(e) => { setCategory(e.target.value); setPage(1); }}>
            <option value="">Бүх сэдэв</option>{categories.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}</select>
        </div>
      </div>
      {err && <div className="alert error">{err}</div>}
      {!data && !err && <div className="grid">{[0, 1, 2].map((i) => <div key={i} className="skeleton" style={{ height: 180 }} />)}</div>}
      {data && data.results.length === 0 && <Empty title="Мэдээ олдсонгүй">Шүүлтүүрээ өөрчилж үзнэ үү. Эх сурвалжуудыг 3 цаг тутам шинэчилнэ.</Empty>}
      <div className="grid">
        {data?.results.map((a) => (
          <a key={a.id} href={a.url} target="_blank" rel="noopener noreferrer" className="card world-card">
            <div className="src"><b>{a.source_name}</b><span>{LANG[a.language] ?? a.language}</span>{a.category_name && <span className="badge gray">{a.category_name}</span>}</div>
            <h3 style={{ margin: 0 }}>{a.title_mn || a.title}</h3>
            {a.title_mn && <small className="muted">{a.title}</small>}
            {a.summary_mn && <p className="muted" style={{ margin: 0 }}>{a.summary_mn.slice(0, 220)}</p>}
            <div className="src" style={{ marginTop: "auto" }}><span>{fmtDateTime(a.published_at)}</span>
              <span>{a.ai_source === "gemini" ? "✨ Gemini" : "Дүрмийн шүүлтүүр"}</span><span>Эх сурвалж ↗</span></div>
          </a>
        ))}
      </div>
      {data && (data.next || data.previous) && (
        <div className="pager">
          <button className="btn secondary sm" disabled={!data.previous} onClick={() => setPage(page - 1)}>← Өмнөх</button>
          <span className="muted">Хуудас {page}</span>
          <button className="btn secondary sm" disabled={!data.next} onClick={() => setPage(page + 1)}>Дараах →</button>
        </div>
      )}
      <p className="muted" style={{ marginTop: 20 }}>Эх сурвалж руу холбоно. Албан ёсны тоо — <a href="/stats">Статистик</a>.</p>
    </>
  );
}
