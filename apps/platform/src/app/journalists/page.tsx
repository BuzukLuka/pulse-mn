"use client";
import { api } from "@pulse/shared";
import { useEffect, useState } from "react";

export default function Journalists() {
  const [list, setList] = useState<{ id: number; full_name: string; is_verified: boolean; province: string | null }[]>([]);
  useEffect(() => { api("/journalists/", { auth: false }).then(setList).catch(() => {}); }, []);
  return (
    <>
      <h1>Сэтгүүлчид</h1>
      <div className="grid">
        {list.map((j) => (
          <a key={j.id} href={`/journalists/${j.id}`} className="card row" style={{ color: "inherit" }}>
            <div className="avatar">{j.full_name.slice(0, 1)}</div>
            <div><b>{j.full_name}</b> {j.is_verified && <span className="badge green">Баталгаажсан</span>}<div className="muted">{j.province ?? "—"}</div></div>
          </a>
        ))}
      </div>
      {list.length === 0 && <p className="muted">Бүртгэлтэй сэтгүүлч алга.</p>}
    </>
  );
}
