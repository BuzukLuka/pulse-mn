"use client";
import { Alert, api, ApiError, Field, fmtDate, fmtMoney, PURCHASE_TONE, RequireRole, type Purchase } from "@pulse/shared";
import { useCallback, useEffect, useState } from "react";

interface Data { totals: { gross: number; vat: number; fee: number; net: number }; items: Purchase[] }

export default function Payments() {
  const [status, setStatus] = useState(""); const [d, setD] = useState<Data | null>(null);
  const [sel, setSel] = useState<Purchase | null>(null); const [reason, setReason] = useState(""); const [err, setErr] = useState("");
  const load = useCallback(() => api<Data>(`/admin/purchases/${status ? `?status=${status}` : ""}`).then(setD).catch(() => {}), [status]);
  useEffect(() => { load(); }, [load]);
  async function refund() {
    setErr("");
    try { await api(`/admin/purchases/${sel!.id}/refund/`, { method: "POST", body: { reason } }); setSel(null); setReason(""); load(); }
    catch (x) { setErr(x instanceof ApiError ? x.message : "Алдаа гарлаа."); }
  }
  return (
    <RequireRole roles={["admin"]}>
      <div className="page-head"><div><div className="eyebrow">ДЕМО горим</div><h1>Төлбөрийн хяналт</h1></div></div>
      <Alert tone="info">Төлбөрийн шлюз (QPay) болон И-баримт холбогдоогүй. Гэрээ байгуулсны дараа <code>PAYMENT_PROVIDER</code> тохиргоогоор асаана — бусад урсгал өөрчлөгдөхгүй.</Alert>
      {d && (
        <div className="grid" style={{ marginBottom: 16 }}>
          <div className="card kpi-card"><div className="muted">Нийт орлого</div><div className="stat">{fmtMoney(d.totals.gross)}</div></div>
          <div className="card kpi-card"><div className="muted">НӨАТ</div><div className="stat">{fmtMoney(d.totals.vat)}</div></div>
          <div className="card kpi-card"><div className="muted">Платформын шимтгэл</div><div className="stat">{fmtMoney(d.totals.fee)}</div></div>
          <div className="card kpi-card"><div className="muted">Сэтгүүлчдэд шилжүүлэх</div><div className="stat">{fmtMoney(d.totals.net)}</div></div>
        </div>
      )}
      <div className="pill-row" style={{ marginBottom: 12 }}>
        {[["", "Бүгд"], ["pending", "Хүлээгдэж буй"], ["paid", "Төлөгдсөн"], ["refunded", "Буцаасан"], ["cancelled", "Цуцалсан"]].map(([k, l]) =>
          <button key={k} className={`pill ${status === k ? "on" : ""}`} onClick={() => setStatus(k)}>{l}</button>)}
      </div>
      <div className="table-wrap"><table>
        <thead><tr><th>Нэхэмжлэх</th><th>Мэдээ</th><th>Редакц</th><th>Лиценз</th><th>Дүн</th><th>Төлөв</th><th /></tr></thead>
        <tbody>{d?.items.map((p) => (
          <tr key={p.id}><td><b>{p.invoice_code}</b><div className="muted">{fmtDate(p.created_at)}{p.ebarimt_no ? ` · ${p.ebarimt_no}` : ""}</div></td>
            <td>{p.content.title}<div className="muted">✍️ {p.content.author_name}</div></td><td>{p.buyer.name}</td><td>{p.license_label}</td>
            <td>{fmtMoney(p.amount)}<div className="muted">НӨАТ {fmtMoney(p.vat_amount)} · сэтгүүлчид {fmtMoney(p.author_net)}</div></td>
            <td><span className={`badge ${PURCHASE_TONE[p.status]}`}>{p.status_label}</span>{p.refund_reason && <div className="muted">{p.refund_reason}</div>}</td>
            <td>{p.status === "paid" && <button className="btn secondary sm" onClick={() => setSel(p)}>Буцаах</button>}</td></tr>
        ))}</tbody></table></div>
      {d?.items.length === 0 && <p className="muted">Төлбөр алга.</p>}
      {sel && (
        <div className="modal-bg" onClick={() => setSel(null)}><div className="modal" onClick={(e) => e.stopPropagation()}>
          <h2 style={{ marginTop: 0 }}>Буцаалт: {sel.invoice_code}</h2>
          {err && <Alert>{err}</Alert>}
          <Field label="Шалтгаан (заавал — редакц, сэтгүүлчид мэдэгдэнэ)"><textarea style={{ minHeight: 80 }} value={reason} onChange={(e) => setReason(e.target.value)} /></Field>
          <div className="row"><button className="btn danger" disabled={!reason.trim()} onClick={refund}>Буцаах</button><button className="btn secondary" onClick={() => setSel(null)}>Болих</button></div>
        </div></div>
      )}
    </RequireRole>
  );
}
