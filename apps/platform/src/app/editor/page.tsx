"use client";
import { api, fmtDateTime, RequireRole, StatusBadge, type Content, type Paginated } from "@pulse/shared";
import { useEffect, useState } from "react";

const TABS = [["under_review", "Шинээр ирсэн / шалгаж буй"], ["changes_requested", "Засварт буцаасан"], ["rejected", "Татгалзсан"], ["published", "Нийтлэгдсэн"]];

export default function Queue() {
  const [tab, setTab] = useState("under_review"); const [items, setItems] = useState<Content[]>([]); const [loaded, setLoaded] = useState(false);
  useEffect(() => { setLoaded(false); api<Paginated<Content>>(`/review/?status=${tab}`).then((d) => setItems(d.results)).finally(() => setLoaded(true)); }, [tab]);
  return (
    <RequireRole roles={["editor", "admin"]}>
      <h1>Шалгах контентын жагсаалт</h1>
      <div className="row" style={{ marginBottom: 12 }}>
        {TABS.map(([k, l]) => <button key={k} className={`btn sm ${tab === k ? "" : "secondary"}`} onClick={() => setTab(k)}>{l}</button>)}
      </div>
      {loaded && items.length === 0 && <p className="muted">Жагсаалт хоосон байна.</p>}
      {items.map((c) => (
        <a key={c.id} href={`/editor/${c.id}`} className="card row spread" style={{ color: "inherit" }}>
          <div><b>{c.title}</b><div className="muted">{c.author_name} · {c.province_name} · {c.category_name} · Ирсэн: {fmtDateTime(c.submitted_at)}</div></div>
          <StatusBadge status={c.status} />
        </a>
      ))}
    </RequireRole>
  );
}
