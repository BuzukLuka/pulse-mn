"use client";
import { Alert, api, ApiError, Field, fmtDate, LEGAL_BASES, qs, RequireRole, STATUS_LABEL, StatusBadge, type Content, type ContentStatus, type Paginated } from "@pulse/shared";
import { useCallback, useEffect, useState } from "react";

export default function ContentAdmin() {
  const [status, setStatus] = useState(""); const [q, setQ] = useState(""); const [data, setData] = useState<Paginated<Content> | null>(null); const [err, setErr] = useState("");
  const load = useCallback(() => api<Paginated<Content>>(`/admin/content/${qs({ status, q })}`).then(setData).catch(() => {}), [status, q]);
  useEffect(() => { const t = setTimeout(load, 250); return () => clearTimeout(t); }, [load]);
  const [sel, setSel] = useState<{ c: Content; kind: "hide" | "restore" } | null>(null);
  const [reason, setReason] = useState(""); const [basis, setBasis] = useState("other");
  async function act() {
    if (!sel) return;
    try { await api(`/admin/content/${sel.c.id}/${sel.kind}/`, { method: "POST", body: { reason, legal_basis: basis } }); setErr(""); setSel(null); setReason(""); load(); }
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
            <td>{c.status === "published" && <button className="btn danger sm" onClick={() => setSel({ c, kind: "hide" })}>Түр нуух</button>}
              {c.status === "hidden" && <button className="btn ok sm" onClick={() => setSel({ c, kind: "restore" })}>Сэргээх</button>}</td></tr>
        ))}</tbody></table></div>
      {sel && (
        <div className="modal-bg" onClick={() => setSel(null)}><div className="modal" onClick={(e) => e.stopPropagation()}>
          <h2 style={{ marginTop: 0 }}>{sel.kind === "hide" ? "Түр нуух" : "Сэргээх"}: {sel.c.title}</h2>
          {sel.kind === "hide" && <Field label="Хууль зүйн үндэслэл"><select value={basis} onChange={(e) => setBasis(e.target.value)}>
            {LEGAL_BASES.map(([k, l]) => <option key={k} value={k}>{l}</option>)}</select></Field>}
          <Field label="Тайлбар (шийдвэрийн дугаар, гомдлын №, г.м.) — сэтгүүлчид мэдэгдэнэ"><textarea style={{ minHeight: 80 }} value={reason} onChange={(e) => setReason(e.target.value)} /></Field>
          <div className="row"><button className={`btn ${sel.kind === "hide" ? "danger" : "ok"}`} disabled={!reason.trim()} onClick={act}>Баталгаажуулах</button>
            <button className="btn secondary" onClick={() => setSel(null)}>Болих</button></div>
          <p className="muted">Үйлдэл аудит логт хууль зүйн үндэслэлийн хамт бүртгэгдэнэ.</p>
        </div></div>
      )}
    </RequireRole>
  );
}
