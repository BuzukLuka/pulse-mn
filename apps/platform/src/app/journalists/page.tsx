"use client";
import { api, initials, RatingBadge, type RatingSummary } from "@pulse/shared";
import { useEffect, useState } from "react";

export default function Journalists() {
  const [list, setList] = useState<{ id: number; full_name: string; is_verified: boolean; province: string | null; rating: RatingSummary;
    topics: { name: string; count: number }[]; published: number }[] | null>(null);
  useEffect(() => { api("/journalists/", { auth: false }).then(setList).catch(() => setList([])); }, []);
  return (
    <>
      <div className="page-head"><div><div className="eyebrow">Орон нутгийн дуу хоолой</div><h1>Сэтгүүлчид</h1></div><a className="btn secondary" href="/newsrooms">Редакцууд →</a></div>
      <div className="grid">
        {list?.map((j) => (
          <a key={j.id} href={`/journalists/${j.id}`} className="card row" style={{ alignItems: "flex-start" }}>
            <div className="avatar">{initials(j.full_name)}</div>
            <div><b>{j.full_name}</b> {j.is_verified && <span className="badge green">Баталгаажсан</span>}<div className="muted">{j.province ?? "—"}</div>
              <RatingBadge r={j.rating} />
              {j.topics.length > 0 ? <div className="topics">{j.topics.map((t, i) => <span key={t.name} className={`badge ${i === 0 ? "blue" : "gray"}`}>{t.name} · {t.count}</span>)}</div>
                : <small className="muted">Нийтлэл алга</small>}</div>
          </a>
        ))}
      </div>
      {list?.length === 0 && <p className="muted">Бүртгэлтэй сэтгүүлч алга.</p>}
    </>
  );
}
