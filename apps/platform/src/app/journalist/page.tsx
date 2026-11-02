"use client";
import {
  Alert, api, ApiError, fmtDate, fmtMoney, MEMBERSHIP_TONE, PURCHASE_TONE, RequireRole, STATUS_LABEL, StatusBadge, useAuth,
  type Content, type ContentStatus, type Membership, type Paginated, type PersonCard, type Purchase,
} from "@pulse/shared";
import { useCallback, useEffect, useState } from "react";

/** Баталгаажуулалт: зөвхөн баталгаажсан сэтгүүлч мэдээ шалгалтад илгээнэ. */
function VerificationBanner() {
  const { user } = useAuth();
  const [requested, setRequested] = useState(user?.verification_requested_at ?? null); const [err, setErr] = useState("");
  if (!user || user.is_verified) return null;
  async function request() {
    try { setRequested((await api<{ verification_requested_at: string }>("/auth/request-verification/", { method: "POST" })).verification_requested_at); }
    catch (x) { setErr(x instanceof ApiError ? x.message : "Илгээж чадсангүй."); }
  }
  return (
    <div className="alert info banner">
      <div><b>Таны бүртгэл баталгаажаагүй байна.</b> Ноорог хадгалж болно, харин шалгалтад илгээхийн тулд админ таны
        сэтгүүлчийн үнэмлэх / байгууллагыг шалгаж баталгаажуулах шаардлагатай.{err && <div className="error">{err}</div>}</div>
      {requested ? <span className="badge amber">Хүсэлт илгээсэн · {fmtDate(requested)}</span>
        : <button className="btn sm" onClick={request}>Баталгаажуулалт хүсэх</button>}
    </div>
  );
}

/** Редакцад нэгдэх: хүсэлт → редакц батална → мэдээгээ редакцаар дамжуулж илгээнэ. */
function NewsroomCard() {
  const [mine, setMine] = useState<Membership[]>([]); const [all, setAll] = useState<PersonCard[]>([]);
  const [pick, setPick] = useState(""); const [message, setMessage] = useState(""); const [err, setErr] = useState("");
  const load = useCallback(() => api<Membership[]>("/memberships/").then(setMine).catch(() => {}), []);
  useEffect(() => { load(); api<PersonCard[]>("/newsrooms/", { auth: false }).then(setAll).catch(() => {}); }, [load]);
  const taken = new Set(mine.filter((m) => m.status === "active" || m.status === "pending").map((m) => m.newsroom.id));
  async function join() {
    setErr("");
    try { await api("/memberships/", { method: "POST", body: { newsroom: Number(pick), message } }); setPick(""); setMessage(""); load(); }
    catch (x) { setErr(x instanceof ApiError ? x.message : "Илгээж чадсангүй."); }
  }
  async function leave(id: number) { if (window.confirm("Редакцаас гарах уу?")) { await api(`/memberships/${id}/end/`, { method: "POST" }); load(); } }
  return (
    <div className="card">
      <h3>🏢 Миний редакц</h3>
      <p className="muted" style={{ marginTop: 0 }}>Редакцад нэгдсэнээр мэдээгээ редакцаараа дамжуулж илгээх бөгөөд редакц шинэ мэдээ, редакторын шийдвэр бүрийн мэдэгдэл авна.</p>
      {mine.filter((m) => m.status !== "left").map((m) => (
        <div key={m.id} className="row spread review">
          <div><a href={`/newsrooms/${m.newsroom.id}`}><b>{m.newsroom.name}</b></a> <span className={`badge ${MEMBERSHIP_TONE[m.status]}`}>{m.status_label}</span></div>
          {(m.status === "active" || m.status === "pending") && <button className="btn ghost sm" onClick={() => leave(m.id)}>{m.status === "active" ? "Гарах" : "Цуцлах"}</button>}
        </div>
      ))}
      <div className="row" style={{ marginTop: 10 }}>
        <select value={pick} onChange={(e) => setPick(e.target.value)} style={{ flex: 1, minWidth: 160 }}>
          <option value="">Редакц сонгох…</option>
          {all.filter((n) => !taken.has(n.id)).map((n) => <option key={n.id} value={n.id}>{n.name}{n.is_verified ? " ✓" : ""}</option>)}
        </select>
        <input placeholder="Товч танилцуулга (заавал биш)" value={message} onChange={(e) => setMessage(e.target.value)} style={{ flex: 2, minWidth: 160 }} />
        <button className="btn sm" disabled={!pick} onClick={join}>Нэгдэх хүсэлт</button>
      </div>
      {err && <Alert>{err}</Alert>}
    </div>
  );
}

function Sales() {
  const [items, setItems] = useState<Purchase[]>([]);
  useEffect(() => { api<Purchase[]>("/purchases/").then(setItems).catch(() => {}); }, []);
  if (!items.length) return null;
  const paid = items.filter((p) => p.status === "paid").reduce((s, p) => s + p.amount, 0);
  return (
    <div className="card"><div className="row spread"><h3>💳 Борлуулалт (ДЕМО)</h3><b>{fmtMoney(paid)}</b></div>
      {items.map((p) => <div key={p.id} className="row spread review"><div><a href={`/news/${p.content.id}`}>{p.content.title}</a>
        <div className="muted">{p.buyer.name} · {fmtDate(p.created_at)}</div></div>
        <span className={`badge ${PURCHASE_TONE[p.status]}`}>{p.status_label} · {fmtMoney(p.amount)}</span></div>)}</div>
  );
}

export default function MyContent() {
  const [items, setItems] = useState<Content[]>([]); const [loaded, setLoaded] = useState(false);
  const [sum, setSum] = useState<Record<string, number> | null>(null); const [filter, setFilter] = useState("");
  useEffect(() => { api<Record<string, number>>("/content/summary/").then(setSum).catch(() => {}); }, []);
  useEffect(() => { api<Paginated<Content>>(`/content/${filter ? `?status=${filter}` : ""}`).then((d) => setItems(d.results)).finally(() => setLoaded(true)); }, [filter]);
  return (
    <RequireRole roles={["journalist"]}>
      <div className="page-head"><h1>Миний контент</h1><a className="btn" href="/journalist/new">+ Шинэ контент</a></div>
      <VerificationBanner />
      <div className="two"><NewsroomCard /><Sales /></div>
      {sum && (
        <div className="pill-row" style={{ margin: "12px 0" }}>
          <button className={`pill ${filter === "" ? "on" : ""}`} onClick={() => setFilter("")}>Бүгд {sum.total}</button>
          {(Object.keys(STATUS_LABEL) as ContentStatus[]).map((k) => <button key={k} className={`pill ${filter === k ? "on" : ""}`} onClick={() => setFilter(k)}>{STATUS_LABEL[k]} {sum[k] ?? 0}</button>)}
        </div>
      )}
      {loaded && items.length === 0 && <p className="muted">Контент алга. Эхний мэдээгээ оруулаарай.</p>}
      {items.map((c) => (
        <a key={c.id} href={`/journalist/${c.id}`} className="card row spread" style={{ color: "inherit" }}>
          <div><b>{c.title || "(гарчиггүй)"}</b><div className="muted">{c.province_name} · {fmtDate(c.created_at)}{c.newsroom_name ? ` · 🏢 ${c.newsroom_name}` : ""}{c.price ? ` · ${fmtMoney(c.price)}` : ""}</div>
            {c.status === "changes_requested" && <div className="error">Редакторын тайлбар: {c.review_reason}</div>}</div>
          <StatusBadge status={c.status} />
        </a>
      ))}
    </RequireRole>
  );
}
