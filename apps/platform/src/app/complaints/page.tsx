"use client";
import { api, COMPLAINT_KINDS, COMPLAINT_STATUS, fmtDate, RequireRole, type Complaint, type Paginated } from "@pulse/shared";
import { useEffect, useState } from "react";

export default function MyComplaints() {
  const [d, setD] = useState<Paginated<Complaint> | null>(null);
  useEffect(() => { api<Paginated<Complaint>>("/complaints/").then(setD).catch(() => {}); }, []);
  const kind = (k: string) => COMPLAINT_KINDS.find(([x]) => x === k)?.[1] ?? k;
  return (
    <RequireRole roles={["journalist", "editor", "newsroom", "citizen", "admin"]}>
      <h1>Миний гомдол, санал</h1>
      <p className="muted">Гомдлыг мэдээ, амлалтын хуудсан дээрх «Гомдол / санал илгээх» товчоор илгээнэ.</p>
      {d?.results.length === 0 && <p className="muted">Илгээсэн гомдол алга.</p>}
      {d?.results.map((c) => (
        <div className="card" key={c.id}>
          <div className="row spread"><b>{kind(c.kind)} · {c.target_type} #{c.target_id}</b><span className={`badge ${c.status === "open" ? "blue" : c.status === "resolved" ? "green" : "gray"}`}>{COMPLAINT_STATUS[c.status]}</span></div>
          <p>{c.text}</p>{c.resolution && <div className="alert info">Хариу: {c.resolution}</div>}<small className="muted">{fmtDate(c.created_at)}</small>
        </div>
      ))}
    </RequireRole>
  );
}
