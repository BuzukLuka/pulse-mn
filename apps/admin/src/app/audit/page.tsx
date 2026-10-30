"use client";
import { api, AuditEntry, fmtDateTime, RequireRole, type Paginated } from "@pulse/shared";
import { useEffect, useState } from "react";

export default function Audit() {
  const [page, setPage] = useState(1); const [data, setData] = useState<Paginated<AuditEntry> | null>(null);
  useEffect(() => { api<Paginated<AuditEntry>>(`/admin/audit/?page=${page}`).then(setData).catch(() => {}); }, [page]);
  return (
    <RequireRole roles={["admin"]}>
      <h1>Аудит лог</h1>
      <div className="table-wrap"><table>
        <thead><tr><th>Хэзээ</th><th>Хэн</th><th>Үйлдэл</th><th>Объект</th><th>Өмнөх → Шинэ</th><th>Шалтгаан</th></tr></thead>
        <tbody>{data?.results.map((a) => (
          <tr key={a.id}><td>{fmtDateTime(a.created_at)}</td><td>{a.actor_email ?? "систем"}</td><td><code>{a.action}</code></td>
            <td>{a.entity_type} #{a.entity_id}</td><td><small>{JSON.stringify(a.before)} → {JSON.stringify(a.after)}</small></td><td>{a.reason}</td></tr>
        ))}</tbody></table></div>
      {data && <div className="row" style={{ marginTop: 12 }}>
        <button className="btn secondary sm" disabled={!data.previous} onClick={() => setPage(page - 1)}>← Өмнөх</button>
        <button className="btn secondary sm" disabled={!data.next} onClick={() => setPage(page + 1)}>Дараах →</button></div>}
    </RequireRole>
  );
}
