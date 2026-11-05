"use client";
import { api, Empty, fmtDateTime, qs, type Category, type ExternalArticle, type Paginated } from "@pulse/shared";
import { useEffect, useState } from "react";

interface Sources { sources: { key: string; name: string; home: string; enabled: boolean; count: number }[]; last_run: { at: string; added: number } | null }

const title = (a: ExternalArticle) => a.title_mn || a.title;

/** Эх сайтын зураг (холбоосоор). Ачаалагдахгүй бол нууна. */
function Img({ a }: { a: ExternalArticle }) {
  const [ok, setOk] = useState(true);
  if (!a.image_url || !ok) return null;
  return (
    // eslint-disable-next-line @next/next/no-img-element
    <img className="nyt-img" src={a.image_url} alt="" loading="lazy" referrerPolicy="no-referrer" style={{ aspectRatio: "3 / 2" }} onError={() => setOk(false)} />
  );
}

function Story({ a, size = "md", summary = true }: { a: ExternalArticle; size?: "lg" | "md" | "sm"; summary?: boolean }) {
  return (
    <a href={a.url} target="_blank" rel="noopener noreferrer" className={`nyt-story ${size}`}>
      {size !== "sm" && <Img a={a} />}
      <h3>{title(a)}</h3>
      {summary && a.summary_mn && <p>{a.summary_mn.slice(0, size === "lg" ? 260 : 140)}</p>}
      <div className="nyt-meta">{a.source_name}{a.category_name ? ` · ${a.category_name}` : ""} · {fmtDateTime(a.published_at)}</div>
    </a>
  );
}

export default function WorldNews() {
  const [data, setData] = useState<Paginated<ExternalArticle> | null>(null); const [src, setSrc] = useState<Sources | null>(null);
  const [source, setSource] = useState(""); const [category, setCategory] = useState(""); const [page, setPage] = useState(1);
  const [categories, setCategories] = useState<Category[]>([]); const [err, setErr] = useState("");
  useEffect(() => { api<Category[]>("/catalog/categories/", { auth: false }).then(setCategories).catch(() => {}); }, []);
  useEffect(() => {
    api<Paginated<ExternalArticle>>(`/world-news/${qs({ source, category, page })}`, { auth: false })
      .then((d) => { setData(d); setErr(""); api<Sources>("/world-news/sources/", { auth: false }).then(setSrc).catch(() => {}); })
      .catch(() => setErr("Ачаалж чадсангүй."));
  }, [source, category, page]);

  const items = data?.results ?? [];
  const lead = items.find((a) => a.image_url) ?? items[0];       // зурагтай мэдээг тэргүүлэх байранд
  const rest = items.filter((a) => a !== lead);
  const second = rest.filter((a) => a.image_url).slice(0, 2);
  const list = rest.filter((a) => !second.includes(a)).slice(0, 6);
  const grid = rest.filter((a) => !second.includes(a) && !list.includes(a));

  return (
    <div className="nyt">
      <header className="nyt-mast">
        <h1>Дэлхийд Монголын тухай</h1>
        <div className="nyt-sub">{src?.last_run ? `Шинэчилсэн ${fmtDateTime(src.last_run.at)} · ` : ""}AI шүүлт</div>
        <nav className="nyt-sections">
          <button className={category === "" ? "on" : ""} onClick={() => { setCategory(""); setPage(1); }}>Бүгд</button>
          {categories.map((c) => <button key={c.id} className={String(c.id) === category ? "on" : ""} onClick={() => { setCategory(String(c.id)); setPage(1); }}>{c.name}</button>)}
          <select value={source} onChange={(e) => { setSource(e.target.value); setPage(1); }} aria-label="Эх сурвалж">
            <option value="">Бүх эх сурвалж</option>
            {src?.sources.filter((s) => s.enabled && s.count > 0).map((s) => <option key={s.key} value={s.key}>{s.name}</option>)}
          </select>
        </nav>
      </header>

      {err && <div className="alert error">{err}</div>}
      {!data && !err && <div className="skeleton" style={{ height: 420 }} />}
      {data && items.length === 0 && <Empty title="Мэдээ олдсонгүй" />}

      {lead && (
        <section className="nyt-top">
          <div className="nyt-col lead"><Story a={lead} size="lg" /></div>
          <div className="nyt-col mid">{second.map((a) => <Story key={a.id} a={a} />)}</div>
          <div className="nyt-col side">{list.map((a) => <Story key={a.id} a={a} size="sm" />)}</div>
        </section>
      )}
      {grid.length > 0 && <section className="nyt-grid">{grid.map((a) => <Story key={a.id} a={a} summary={false} />)}</section>}

      {data && (data.next || data.previous) && (
        <div className="pager">
          <button className="btn secondary sm" disabled={!data.previous} onClick={() => setPage(page - 1)}>← Өмнөх</button>
          <span className="muted">Хуудас {page}</span>
          <button className="btn secondary sm" disabled={!data.next} onClick={() => setPage(page + 1)}>Дараах →</button>
        </div>
      )}
    </div>
  );
}
