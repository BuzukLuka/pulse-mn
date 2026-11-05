"use client";
import { api, Cover, Empty, fmtDate, qs, type Category, type Content, type ExternalArticle, type Option, type Paginated } from "@pulse/shared";
import { useEffect, useState } from "react";

const imageOf = (c: Content) => c.media.find((m) => m.kind === "image")?.url;
const summaryOf = (c: Content, n = 160) => c.ai_summary || (c.body.length > n ? c.body.slice(0, n) + "…" : c.body);

function NewsCard({ c, lead }: { c: Content; lead?: boolean }) {
  return (
    <a href={`/news/${c.id}`} className={`card news-card ${lead ? "lead-card" : ""}`}>
      <Cover image={imageOf(c)} seed={c.category_slug} label={c.category_name} chip={c.category_name}
        trust={c.trust?.editor_verified ? c.trust.score : null} />
      <div className="body">
        <h3>{c.title}</h3>
        <p className="muted">{summaryOf(c, lead ? 260 : 160)}</p>
        <div className="meta"><span>📍 {c.province_name ?? "—"}</span><span>{fmtDate(c.published_at ?? c.event_date)}</span></div>
      </div>
    </a>
  );
}

function SideItem({ c }: { c: Content }) {
  return (
    <a href={`/news/${c.id}`} className="card">
      <Cover image={imageOf(c)} seed={c.category_slug} label="" />
      <div><h3>{c.title}</h3><div className="muted" style={{ fontSize: 13 }}>{c.category_name} · {fmtDate(c.published_at ?? c.event_date)}</div></div>
    </a>
  );
}

export default function Home() {
  const [q, setQ] = useState(""); const [province, setProvince] = useState(""); const [category, setCategory] = useState("");
  const [page, setPage] = useState(1);
  const [provinces, setProvinces] = useState<Option[]>([]); const [categories, setCategories] = useState<Category[]>([]);
  const [data, setData] = useState<Paginated<Content> | null>(null); const [err, setErr] = useState("");

  useEffect(() => {
    api<Option[]>("/catalog/provinces/", { auth: false }).then(setProvinces).catch(() => {});
    api<Category[]>("/catalog/categories/", { auth: false }).then(setCategories).catch(() => {});
  }, []);
  useEffect(() => {
    const t = setTimeout(() => {
      api<Paginated<Content>>(`/news/${qs({ q, province, category, page })}`, { auth: false })
        .then((d) => { setData(d); setErr(""); }).catch(() => setErr("Мэдээ ачаалж чадсангүй. Backend ажиллаж байгаа эсэхийг шалгана уу."));
    }, 250);
    return () => clearTimeout(t);
  }, [q, province, category, page]);

  const results = data?.results ?? [];
  const showFeatured = page === 1 && !q && results.length >= 3;
  const [lead, ...rest] = results;
  const side = showFeatured ? rest.slice(0, 3) : [];
  const grid = showFeatured ? rest.slice(3) : results;
  const filtered = !!(q || province || category);

  return (
    <>
      <section className="hero">
        <svg className="pulse-line" viewBox="0 0 640 160" fill="none" aria-hidden>
          <path d="M0 90h180l22-58 34 112 30-96 20 42h70l16-30 18 30h250" stroke="#e8432a" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
        <div className="eyebrow"><span className="live" /> Шууд · Орон нутгаас</div>
        <h1>Мэдээ бүр <em>шалгагдсан</em>.</h1>
        <p className="lead">21 аймгийн шалгагдсан мэдээ нэг дор.</p>
        <label className="search">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" aria-hidden><circle cx="11" cy="11" r="7" /><path d="m20 20-3.5-3.5" /></svg>
          <input aria-label="Хайх" placeholder="Түлхүүр үг, аймаг, сэдвээр хайх…" value={q} onChange={(e) => { setQ(e.target.value); setPage(1); }} />
          {q && <button className="btn sm secondary" onClick={() => setQ("")}>Цэвэрлэх</button>}
        </label>
        <div className="hero-stats">
          <div><b>{data?.count ?? "—"}</b><span>Баталгаажсан мэдээ</span></div>
          <div><b>{provinces.length || "21"}</b><span>Аймаг, нийслэл</span></div>
          <div><b>AI + 👤</b><span>Давхар шалгалт</span></div>
        </div>
      </section>

      <div className="filters">
        <div className="pill-row" role="tablist" aria-label="Ангилал">
          <button className={`pill ${category === "" ? "on" : ""}`} onClick={() => { setCategory(""); setPage(1); }}>Бүгд</button>
          {categories.map((c) => (
            <button key={c.id} className={`pill ${String(c.id) === category ? "on" : ""}`} onClick={() => { setCategory(String(c.id)); setPage(1); }}>{c.name}</button>
          ))}
        </div>
        <select aria-label="Аймаг" value={province} onChange={(e) => { setProvince(e.target.value); setPage(1); }}>
          <option value="">📍 Бүх аймаг</option>{provinces.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
        </select>
      </div>

      {err && <div className="alert error">{err}</div>}

      {!data && !err && (
        <div className="grid">{[0, 1, 2].map((i) => <div key={i} className="skeleton" style={{ height: 320 }} />)}</div>
      )}

      {data && results.length === 0 && (
        filtered
          ? <Empty title="Илэрц олдсонгүй" action={<button className="btn secondary" onClick={() => { setQ(""); setProvince(""); setCategory(""); }}>Шүүлтүүр цэвэрлэх</button>}>
              Өөр түлхүүр үг, ангилал эсвэл аймгаар хайгаад үзээрэй.
            </Empty>
          : <Empty title="Удахгүй анхны мэдээ гарна" action={<div className="row" style={{ justifyContent: "center" }}><a className="btn" href="/stats">Статистик үзэх</a><a className="btn secondary" href="/pledges">Амлалтын хяналт</a></div>}>
              Редактор шалгаж баталгаажуулсан мэдээ энд гарна. Тэр хооронд аймгуудын статистик, албан тушаалтны амлалтын биелэлтийг үзээрэй.
            </Empty>
      )}

      {showFeatured && (
        <section className="featured">
          <NewsCard c={lead} lead />
          <div className="side-list">{side.map((c) => <SideItem key={c.id} c={c} />)}</div>
        </section>
      )}

      {grid.length > 0 && (
        <>
          {showFeatured && <h2>Сүүлийн мэдээ</h2>}
          <div className="grid">{grid.map((c) => <NewsCard key={c.id} c={c} />)}</div>
        </>
      )}

      <WorldStrip />

      {data && (data.next || data.previous) && (
        <div className="pager">
          <button className="btn secondary sm" disabled={!data.previous} onClick={() => setPage(page - 1)}>← Өмнөх</button>
          <span className="muted">Хуудас {page}</span>
          <button className="btn secondary sm" disabled={!data.next} onClick={() => setPage(page + 1)}>Дараах →</button>
        </div>
      )}
    </>
  );
}

/** AI-аар шүүсэн «Дэлхийд Монголын тухай» мэдээний тасалбар. */
function WorldStrip() {
  const [items, setItems] = useState<ExternalArticle[]>([]);
  useEffect(() => { api<Paginated<ExternalArticle>>("/world-news/", { auth: false }).then((d) => setItems(d.results.slice(0, 4))).catch(() => {}); }, []);
  if (!items.length) return null;
  return (
    <section style={{ marginTop: 36 }}>
      <div className="row spread"><h2 style={{ margin: 0 }}>🌍 Дэлхийд Монголын тухай</h2><a href="/world">Бүгдийг харах →</a></div>
      <div className="grid">{items.map((a) => (
        <a key={a.id} href={a.url} target="_blank" rel="noopener noreferrer" className="card world-card">
          <div className="src"><b>{a.source_name}</b>{a.category_name && <span className="badge gray">{a.category_name}</span>}</div>
          <h3 style={{ margin: 0, fontSize: 15.5 }}>{a.title_mn || a.title}</h3>
          <small className="muted">{fmtDate(a.published_at)} · эх сурвалж ↗</small>
        </a>))}</div>
    </section>
  );
}
