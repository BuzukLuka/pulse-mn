"use client";
import { api, ApiError, fmtDateTime, fmtMoney, useAuth, type Purchase, type PurchaseQuote } from "@pulse/shared";
import { useEffect, useState } from "react";

/** Редакц мэдээний лиценз худалдан авах. Төлбөрийн шлюз холбогдох хүртэл ДЕМО provider ашиглана. */
export default function PurchaseBox({ contentId, price, authorName }: { contentId: number; price: number; authorName: string }) {
  const { user } = useAuth();
  const isNewsroom = user?.role === "newsroom";
  const [q, setQ] = useState<PurchaseQuote | null>(null); const [p, setP] = useState<Purchase | null>(null);
  const [license, setLicense] = useState("standard"); const [agree, setAgree] = useState(false);
  const [open, setOpen] = useState(false); const [busy, setBusy] = useState(false); const [err, setErr] = useState("");
  useEffect(() => {
    if (!isNewsroom) return;
    api<PurchaseQuote>(`/purchases/quote/?content=${contentId}`).then(setQ).catch(() => {});
    api<Purchase[]>(`/purchases/?content=${contentId}`).then((l) => setP(l.find((x) => x.status === "pending" || x.status === "paid") ?? null)).catch(() => {});
  }, [isNewsroom, contentId]);

  async function call(fn: () => Promise<Purchase>) {
    setBusy(true); setErr("");
    try { const r = await fn(); setP(r); return r; } catch (x) { setErr(x instanceof ApiError ? x.message : "Алдаа гарлаа."); return null; } finally { setBusy(false); }
  }
  const create = async () => { if (await call(() => api<Purchase>("/purchases/", { method: "POST", body: { content: contentId, license_type: license, accept_terms: agree } }))) setOpen(true); };
  const confirm = () => call(() => api<Purchase>(`/purchases/${p!.id}/confirm/`, { method: "POST" }));
  const cancel = async () => { if (await call(() => api<Purchase>(`/purchases/${p!.id}/cancel/`, { method: "POST" }))) { setP(null); setOpen(false); } };
  const opt = q?.options.find((o) => o.license_type === license);

  return (
    <div className="card">
      <div className="row spread"><h3 style={{ margin: 0 }}>💳 Редакцад лицензлэх</h3><b>{fmtMoney(price)}-с</b></div>
      <p className="muted">Энэ мэдээг өөрийн сувагт ашиглах эрхийг {authorName}-аас худалдан авна. <a href="/legal/newsrooms" target="_blank">Лицензийн нөхцөл</a></p>
      {!user && <p className="muted"><a href="/login">Редакцын бүртгэлээр нэвтэрч</a> худалдан авна.</p>}
      {user && !isNewsroom && <p className="muted">Зөвхөн редакцын бүртгэл худалдан авна.</p>}

      {isNewsroom && !p && q && (
        <>
          <div className="pill-row" style={{ margin: "8px 0" }}>
            {q.options.map((o) => <button key={o.license_type} type="button" disabled={!o.available} className={`pill ${license === o.license_type ? "on" : ""}`}
              onClick={() => setLicense(o.license_type)}>{o.label} · {fmtMoney(o.amount)}{!o.available ? " (боломжгүй)" : ""}</button>)}
          </div>
          {opt && (
            <table style={{ fontSize: 13, marginBottom: 10 }}><tbody>
              <tr><td>Нийт (НӨАТ орсон)</td><td><b>{fmtMoney(opt.amount)}</b></td></tr>
              <tr><td>НӨАТ 10%</td><td>{fmtMoney(opt.vat_amount)}</td></tr>
              <tr><td>Платформын шимтгэл {q.fee_pct}%</td><td>{fmtMoney(opt.platform_fee)}</td></tr>
              <tr><td>Сэтгүүлчид очих</td><td>{fmtMoney(opt.author_net)}</td></tr>
            </tbody></table>
          )}
          <label className="check-row consent"><input type="checkbox" checked={agree} onChange={(e) => setAgree(e.target.checked)} />
            <span>Эх сурвалж (Pulse.mn, зохиогч)-ийг заан, утгыг нь алдагдуулахгүй ашиглана.</span></label>
          <button className="btn" disabled={busy || !agree || !opt?.available} onClick={create}>Нэхэмжлэх үүсгэх</button>
        </>
      )}
      {isNewsroom && p?.status === "paid" && (
        <div className="alert ok">✓ {p.license_label} · төлөгдсөн {fmtDateTime(p.paid_at)}<br />
          Нэхэмжлэх {p.invoice_code} · И-баримт {p.ebarimt_no}{p.demo ? " (ДЕМО)" : ""}</div>
      )}
      {isNewsroom && p?.status === "pending" && !open && <button className="btn secondary" onClick={() => setOpen(true)}>Нэхэмжлэх харах · төлбөр хүлээгдэж буй</button>}
      {err && <div className="alert error">{err}</div>}

      {open && p?.status === "pending" && (
        <div className="modal-bg" onClick={() => setOpen(false)}><div className="modal" onClick={(e) => e.stopPropagation()}>
          <h2 style={{ marginTop: 0 }}>Нэхэмжлэх</h2>
          {p.demo && <div className="alert info"><b>ДЕМО горим.</b> QPay / банкны шлюз, И-баримт холбогдоогүй тул мөнгө шилжихгүй. Доорх товч төлбөр төлөгдсөнийг дуурайна. <a href="/legal/payments" target="_blank">Дэлгэрэнгүй</a></div>}
          <div className="invoice">
            <div className="muted">Нэхэмжлэхийн дугаар</div><div className="code">{p.invoice_code}</div>
            <div className="row spread" style={{ marginTop: 10 }}><span>{p.content.title}</span><b>{fmtMoney(p.amount)}</b></div>
            <small className="muted">{p.license_label} · НӨАТ {fmtMoney(p.vat_amount)} · Хүлээн авагч: {p.content.author_name} · Лавлах: {p.provider_ref}</small>
          </div>
          <div className="row"><button className="btn ok" disabled={busy} onClick={confirm}>Төлбөр төлсөн — баталгаажуулах</button>
            <button className="btn secondary" disabled={busy} onClick={cancel}>Цуцлах</button></div>
        </div></div>
      )}
    </div>
  );
}
