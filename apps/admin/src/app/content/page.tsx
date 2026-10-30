"use client";
import { Alert, api, ApiError, fmtDate, qs, RequireRole, STATUS_LABEL, StatusBadge, type Content, type ContentStatus, type Paginated } from "@pulse/shared";
import { useCallback, useEffect, useState } from "react";

export default function ContentAdmin() {
  const [status, setStatus] = useState(""); const [q, setQ] = useState(""); const [data, setData] = useState<Paginated<Content> | null>(null); const [err, setErr] = useState("");
  const load = useCallback(() => api<Paginated<Content>>(`/admin/content/${qs({ status, q })}`).then(setData).catch(() => {}), [status, q]);
  useEffect(() => { const t = setTimeout(load, 250); return () => clearTimeout(t); }, [load]);
  async function act(c: Content, kind: "hide" | "restore") {
    const reason = window.prompt(kind === "hide" ? "Түр нуух шалтгаан:" : "Сэргээх шалтгаан:");
    if (!reason) return;
    try { await api(`/admin/content/${c.id}/${kind}/`, { method: "POST", body: { reason } }); setErr(""); load(); }
    catch (x) { setErr(x instanceof ApiError ? x.message : "Алдаа гарлаа."); }
  }
  return (
    <RequireRole roles={["admin"]}>
      <h1>Контент хяналт</h1>{err && <Alert>{err}</Alert>}
      <div className="card row">
        <input style={{ flex: 1 }} placeholder="Гарчигаар хайх" value={q} onChange={(e) => setQ(e.target.value)} />
        <select value={status} onChange={(e) => setStatus(e.target.value)}><option value="">Бүх төлөв</option>
          {Object.entries(STATUS_LABEL).map(([k, l]) => <option key={k} value={k}>{l}</option>)}</select>
      </div>
      <div className="table-wrap"><table>
        <thead><tr><th>Гарчиг</th><th>Сэтгүүлч</th><th>Аймаг</th><th>Огноо</th><th>Төлөв</th><th /></tr></thead>
        <tbody>{data?.results.map((c) => (
          <tr key={c.id}><td>{c.status === "published" ? <a href={`${process.env.NEXT_PUBLIC_PLATFORM_URL ?? ""}/news/${c.id}`} target="_blank">{c.title}</a> : c.title}</td>
            <td>{c.author_name}</td><td>{c.province_name}</td><td>{fmtDate(c.created_at)}</td><td><StatusBadge status={c.status as ContentStatus} /></td>
            <td>{c.status === "published" && <button className="btn danger sm" onClick={() => act(c, "hide")}>Түр нуух</button>}
              {c.status === "hidden" && <button className="btn ok sm" onClick={() => act(c, "restore")}>Сэргээх</button>}</td></tr>
        ))}</tbody></table></div>
    </RequireRole>
  );
}
