"use client";
import { api, fmtDate, RequireRole, STATUS_LABEL, StatusBadge, type Content, type ContentStatus, type Paginated } from "@pulse/shared";
import { useEffect, useState } from "react";

export default function MyContent() {
  const [items, setItems] = useState<Content[]>([]); const [loaded, setLoaded] = useState(false);
  const [sum, setSum] = useState<Record<string, number> | null>(null); const [filter, setFilter] = useState("");
  useEffect(() => { api<Record<string, number>>("/content/summary/").then(setSum).catch(() => {}); }, []);
  useEffect(() => { api<Paginated<Content>>(`/content/${filter ? `?status=${filter}` : ""}`).then((d) => setItems(d.results)).finally(() => setLoaded(true)); }, [filter]);
  return (
    <RequireRole roles={["journalist"]}>
      <div className="row spread"><h1>Миний контент</h1><a className="btn" href="/journalist/new">+ Шинэ контент</a></div>
      {sum && (
        <div className="pill-row" style={{ marginBottom: 12 }}>
          <button className={`pill ${filter === "" ? "on" : ""}`} onClick={() => setFilter("")}>Бүгд {sum.total}</button>
          {(Object.keys(STATUS_LABEL) as ContentStatus[]).map((k) => <button key={k} className={`pill ${filter === k ? "on" : ""}`} onClick={() => setFilter(k)}>{STATUS_LABEL[k]} {sum[k] ?? 0}</button>)}
        </div>
      )}
      {loaded && items.length === 0 && <p className="muted">Контент алга. Эхний мэдээгээ оруулаарай.</p>}
      {items.map((c) => (
        <a key={c.id} href={`/journalist/${c.id}`} className="card row spread" style={{ color: "inherit" }}>
          <div><b>{c.title || "(гарчиггүй)"}</b><div className="muted">{c.province_name} · {fmtDate(c.created_at)}</div>
            {c.status === "changes_requested" && <div className="error">Редакторын тайлбар: {c.review_reason}</div>}</div>
          <StatusBadge status={c.status} />
        </a>
      ))}
    </RequireRole>
  );
}
