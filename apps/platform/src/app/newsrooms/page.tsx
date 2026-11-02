"use client";
import { api, initials, RatingBadge, type PersonCard } from "@pulse/shared";
import { useEffect, useState } from "react";

export default function Newsrooms() {
  const [list, setList] = useState<PersonCard[] | null>(null);
  useEffect(() => { api<PersonCard[]>("/newsrooms/", { auth: false }).then(setList).catch(() => setList([])); }, []);
  return (
    <>
      <div className="page-head"><div><div className="eyebrow">Хамтрагчид</div><h1>Редакцууд</h1></div></div>
      <p className="muted" style={{ marginTop: -10 }}>Сэтгүүлчид редакцад нэгдэж мэдээгээ редакцаар дамжуулан илгээдэг. Үнэлгээ нь хэрэглэгчдийн өгсөн оноо юм.</p>
      <div className="grid">
        {list?.map((n) => (
          <a key={n.id} href={`/newsrooms/${n.id}`} className="card row" style={{ alignItems: "flex-start" }}>
            <div className="avatar">{initials(n.name)}</div>
            <div><b>{n.name}</b> {n.is_verified && <span className="badge green">✓</span>}
              <div className="muted">{n.province ?? "—"} · {n.members} сэтгүүлч</div><RatingBadge r={n.rating} /></div>
          </a>
        ))}
      </div>
      {list?.length === 0 && <p className="muted">Бүртгэлтэй редакц алга.</p>}
    </>
  );
}
