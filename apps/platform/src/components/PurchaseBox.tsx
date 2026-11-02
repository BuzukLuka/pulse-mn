"use client";
import { api, ApiError, fmtDateTime, fmtMoney, useAuth, type Purchase } from "@pulse/shared";
import { useEffect, useState } from "react";

/** Редакц мэдээ худалдан авах — ДЕМО төлбөр (нэхэмжлэх үүсгэж, гараар баталгаажуулна). */
export default function PurchaseBox({ contentId, price, authorName }: { contentId: number; price: number; authorName: string }) {
  const { user } = useAuth();
  const [p, setP] = useState<Purchase | null>(null); const [open, setOpen] = useState(false);
  const [busy, setBusy] = useState(false); const [err, setErr] = useState("");
  const isNewsroom = user?.role === "newsroom";
  useEffect(() => {
    if (isNewsroom) api<Purchase[]>(`/purchases/?content=${contentId}`).then((l) => setP(l.find((x) => x.status !== "cancelled") ?? null)).catch(() => {});
  }, [isNewsroom, contentId]);

  async function call(fn: () => Promise<Purchase>) {
    setBusy(true); setErr("");
    try { setP(await fn()); } catch (x) { setErr(x instanceof ApiError ? x.message : "Алдаа гарлаа."); } finally { setBusy(false); }
  }
  const create = () => call(() => api<Purchase>("/purchases/", { method: "POST", body: { content: contentId } })).then(() => setOpen(true));
  const confirm = () => call(() => api<Purchase>(`/purchases/${p!.id}/confirm/`, { method: "POST" }));
  const cancel = () => call(() => api<Purchase>(`/purchases/${p!.id}/cancel/`, { method: "POST" })).then(() => { setP(null); setOpen(false); });

  return (
    <div className="card">
      <div className="row spread"><h3 style={{ margin: 0 }}>💳 Редакцад худалдаалах</h3><b>{fmtMoney(price)}</b></div>
      <p className="muted">Редакц энэ мэдээг өөрийн сувагт ашиглах эрхийг {authorName}-аас худалдан авна.</p>
      {!user && <p className="muted"><a href="/login">Редакцын бүртгэлээр нэвтэрч</a> худалдан авна.</p>}
      {user && !isNewsroom && <p className="muted">Зөвхөн редакцын бүртгэл худалдан авна.</p>}
      {isNewsroom && !p && <button className="btn" disabled={busy} onClick={create}>Худалдан авах</button>}
      {isNewsroom && p?.status === "paid" && <div className="alert ok">✓ Төлөгдсөн ({fmtDateTime(p.paid_at)}). Ашиглах эрх нээгдлээ · {p.invoice_code}</div>}
      {isNewsroom && p?.status === "pending" && !open && <button className="btn secondary" onClick={() => setOpen(true)}>Нэхэмжлэх харах · төлбөр хүлээгдэж буй</button>}
      {err && <div className="alert error">{err}</div>}
      {open && p?.status === "pending" && (
        <div className="modal-bg" onClick={() => setOpen(false)}><div className="modal" onClick={(e) => e.stopPropagation()}>
          <h2 style={{ marginTop: 0 }}>Нэхэмжлэх</h2>
          <div className="alert info"><b>ДЕМО горим.</b> Бодит төлбөрийн систем (QPay, банк) холбогдоогүй тул мөнгө шилжихгүй. Доорх товч төлбөр төлөгдсөнийг дуурайна.</div>
          <div className="invoice">
            <div className="muted">Нэхэмжлэхийн дугаар</div><div className="code">{p.invoice_code}</div>
            <div className="row spread" style={{ marginTop: 10 }}><span>{p.content.title}</span><b>{fmtMoney(p.amount)}</b></div>
            <small className="muted">Хүлээн авагч: {p.content.author_name}</small>
          </div>
          <div className="row"><button className="btn ok" disabled={busy} onClick={confirm}>Төлбөр төлсөн — баталгаажуулах</button>
            <button className="btn secondary" disabled={busy} onClick={cancel}>Цуцлах</button></div>
        </div></div>
      )}
    </div>
  );
}
