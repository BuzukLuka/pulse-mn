"use client";
import {
  api, fmtDate, fmtMoney, MEMBERSHIP_TONE, PURCHASE_TONE, RatingBadge, RequireRole, STATUS_LABEL, StatusBadge, Tabs, useAuth,
  type Content, type ContentStatus, type Membership, type Purchase, type RatingSummary,
} from "@pulse/shared";
import { useCallback, useEffect, useState } from "react";
import { ApiError } from "@pulse/shared";

interface Summary { content: Record<string, number>; content_total: number; members: number; pending: number; purchases: number; rating: RatingSummary }

function ContentTab() {
  const [status, setStatus] = useState(""); const [items, setItems] = useState<Content[] | null>(null);
  useEffect(() => { api<Content[]>(`/newsroom/content/${status ? `?status=${status}` : ""}`).then(setItems).catch(() => setItems([])); }, [status]);
  return (
    <>
      <div className="pill-row" style={{ marginBottom: 12 }}>
        <button className={`pill ${status === "" ? "on" : ""}`} onClick={() => setStatus("")}>Бүгд</button>
        {(["under_review", "changes_requested", "published", "rejected"] as ContentStatus[]).map((k) =>
          <button key={k} className={`pill ${status === k ? "on" : ""}`} onClick={() => setStatus(k)}>{STATUS_LABEL[k]}</button>)}
      </div>
      {items?.length === 0 && <p className="muted">Энэ төлөвт мэдээ алга. Сэтгүүлчид мэдээгээ илгээхдээ танай редакцыг сонгосноор энд харагдана.</p>}
      {items?.map((c) => (
        <div key={c.id} className="card row spread">
          <div style={{ flex: 1, minWidth: 220 }}>
            <b>{c.status === "published" ? <a href={`/news/${c.id}`}>{c.title}</a> : c.title}</b>
            <div className="muted">✍️ {c.author_name} · {c.province_name} · илгээсэн {fmtDate(c.submitted_at)}</div>
            {c.review_reason && <div className="muted">Редакторын тайлбар: {c.review_reason}</div>}
          </div>
          <div className="row">{c.verification?.score != null && <span className="badge blue">Trust {c.verification.score}</span>}<StatusBadge status={c.status} />
            {c.is_featured && <span className="badge green">⭐ Топ</span>}
            {!c.is_featured && c.feature_request_hours && <span className="badge amber">Топ хүсэлт · {c.feature_request_hours}ц</span>}
            {c.review_by === "newsroom"
              ? <a className={`btn sm ${c.status === "under_review" ? "" : "secondary"}`} href={`/newsroom/review/${c.id}`}>{c.status === "under_review" ? "Шалгах →" : "Нээх"}</a>
              : <span className="badge gray" title="Гишүүн бус эсвэл баталгаажаагүй үед Pulse.mn шалгана">Pulse шалгана</span>}</div>
        </div>
      ))}
    </>
  );
}

function MembersTab({ onChange }: { onChange: () => void }) {
  const [items, setItems] = useState<Membership[]>([]);
  const load = useCallback(() => api<Membership[]>("/newsroom/members/").then(setItems).catch(() => {}), []);
  useEffect(() => { load(); }, [load]);
  async function decide(id: number, approve: boolean) { await api(`/newsroom/members/${id}/decide/`, { method: "POST", body: { approve } }); load(); onChange(); }
  async function remove(id: number) { if (window.confirm("Сэтгүүлчийг редакцаас хасах уу?")) { await api(`/memberships/${id}/end/`, { method: "POST" }); load(); onChange(); } }
  const pending = items.filter((m) => m.status === "pending"); const active = items.filter((m) => m.status === "active");
  return (
    <>
      <h3>Нэгдэх хүсэлт ({pending.length})</h3>
      {pending.length === 0 && <p className="muted">Шинэ хүсэлт алга.</p>}
      {pending.map((m) => (
        <div key={m.id} className="card row spread">
          <div><a href={`/journalists/${m.journalist.id}`}><b>{m.journalist.name}</b></a> {m.journalist.is_verified && <span className="badge green">Баталгаажсан</span>}
            <div className="muted">{m.journalist.province ?? "—"} · {m.journalist.published} нийтлэл · {fmtDate(m.created_at)}</div>
            {m.message && <div>“{m.message}”</div>}<RatingBadge r={m.journalist.rating} /></div>
          <div className="row"><button className="btn ok sm" onClick={() => decide(m.id, true)}>Батлах</button><button className="btn secondary sm" onClick={() => decide(m.id, false)}>Татгалзах</button></div>
        </div>
      ))}
      <h3 style={{ marginTop: 24 }}>Манай сэтгүүлчид ({active.length})</h3>
      <div className="grid">{active.map((m) => (
        <div key={m.id} className="card">
          <div className="row spread"><a href={`/journalists/${m.journalist.id}`}><b>{m.journalist.name}</b></a><span className={`badge ${MEMBERSHIP_TONE[m.status]}`}>{m.status_label}</span></div>
          <div className="muted">{m.journalist.province ?? "—"} · {m.journalist.published} нийтлэл</div>
          <RatingBadge r={m.journalist.rating} />
          <div style={{ marginTop: 8 }}><a className="btn secondary sm" href={`/journalists/${m.journalist.id}#rate`}>Үнэлэх</a> <button className="btn ghost sm" onClick={() => remove(m.id)}>Хасах</button></div>
        </div>))}</div>
    </>
  );
}

function PurchasesTab() {
  const [items, setItems] = useState<Purchase[]>([]);
  useEffect(() => { api<Purchase[]>("/purchases/").then(setItems).catch(() => {}); }, []);
  return (
    <>
      {items.length === 0 && <p className="muted">Худалдан авалт алга.</p>}
      {items.map((p) => (
        <div key={p.id} className="card row spread">
          <div><a href={`/news/${p.content.id}`}><b>{p.content.title}</b></a><div className="muted">✍️ {p.content.author_name} · {p.invoice_code} · {fmtDate(p.created_at)}</div></div>
          <span className={`badge ${PURCHASE_TONE[p.status]}`}>{p.status_label} · {fmtMoney(p.amount)}</span>
        </div>))}
    </>
  );
}

export default function NewsroomDashboard() {
  const { user } = useAuth();
  const [tab, setTab] = useState("content"); const [s, setS] = useState<Summary | null>(null);
  const loadSummary = useCallback(() => api<Summary>("/newsroom/summary/").then(setS).catch(() => {}), []);
  useEffect(() => { if (user?.role === "newsroom") loadSummary(); }, [user, loadSummary]);
  return (
    <RequireRole roles={["newsroom"]}><div className="dash">
      <div className="page-head"><div><div className="eyebrow">Редакцын самбар</div><h1>{user?.full_name || user?.organization || "Редакц"}</h1></div>
        {user && <a className="btn secondary" href={`/newsrooms/${user.id}`}>Нийтийн хуудас</a>}</div>
      {user && !user.is_verified && <div className="alert info">Редакцын бүртгэл баталгаажаагүй байна. Админ баталгаажуулснаар нийтийн хуудсанд ✓ тэмдэг гарна.</div>}
      {s && (
        <div className="kpis">
          <div className="card kpi-card"><div className="ico">📰</div><div className="muted">Ирсэн мэдээ</div><div className="stat">{s.content_total}</div><small className="muted">Нийтлэгдсэн {s.content.published ?? 0} · хянагдаж буй {s.content.under_review ?? 0}</small></div>
          <div className="card kpi-card"><div className="ico">👥</div><div className="muted">Сэтгүүлч</div><div className="stat">{s.members}</div><small className="muted">{s.pending} хүсэлт хүлээгдэж буй</small></div>
          <div className="card kpi-card"><div className="ico">⭐</div><div className="muted">Редакцын үнэлгээ</div><div className="stat">{s.rating.avg ?? "—"}</div><small className="muted">{s.rating.count} үнэлгээ</small></div>
          <div className="card kpi-card"><div className="ico">💳</div><div className="muted">Худалдан авсан</div><div className="stat">{s.purchases}</div><small className="muted">ДЕМО төлбөр</small></div>
        </div>
      )}
      <Tabs tabs={[["content", `Ирсэн мэдээ${s?.content.under_review ? ` (${s.content.under_review})` : ""}`], ["members", `Сэтгүүлчид${s?.pending ? ` (${s.pending})` : ""}`], ["editors", "Редакторууд"], ["purchases", "Худалдан авалт"]]} value={tab} onChange={setTab} />
      {tab === "content" && <ContentTab />}
      {tab === "members" && <MembersTab onChange={loadSummary} />}
      {tab === "editors" && <EditorsTab />}
      {tab === "purchases" && <PurchasesTab />}
    </div></RequireRole>
  );
}

interface Staff { id: number; email: string; full_name: string; is_active: boolean; last_login: string | null; decisions: number }

/** Редакцын редакторууд: редакц өөрөө үүсгэж, идэвхгүй болгоно. Тэд «Шалгах жагсаалт»-аас танай мэдээг шалгана. */
function EditorsTab() {
  const [items, setItems] = useState<Staff[]>([]); const [f, setF] = useState({ email: "", full_name: "", password: "" });
  const [err, setErr] = useState(""); const [ok, setOk] = useState("");
  const load = useCallback(() => api<Staff[]>("/newsroom/editors/").then(setItems).catch(() => {}), []);
  useEffect(() => { load(); }, [load]);
  async function add() {
    setErr(""); setOk("");
    try { await api("/newsroom/editors/", { method: "POST", body: f }); setOk(`${f.email} нэмэгдлээ.`); setF({ email: "", full_name: "", password: "" }); load(); }
    catch (x) { setErr(x instanceof ApiError ? x.message : "Нэмж чадсангүй."); }
  }
  async function toggle(u: Staff) { await api(`/newsroom/editors/${u.id}/active/`, { method: "POST", body: { active: !u.is_active } }); load(); }
  return (
    <div className="g-3">
      <div className="card">
        <h3>Редактор нэмэх</h3>
        <input placeholder="Нэр" value={f.full_name} onChange={(e) => setF({ ...f, full_name: e.target.value })} style={{ width: "100%", marginBottom: 8 }} />
        <input placeholder="Имэйл" type="email" value={f.email} onChange={(e) => setF({ ...f, email: e.target.value })} style={{ width: "100%", marginBottom: 8 }} />
        <input placeholder="Анхны нууц үг (8+)" type="password" value={f.password} onChange={(e) => setF({ ...f, password: e.target.value })} style={{ width: "100%", marginBottom: 8 }} />
        <button className="btn sm" disabled={!f.email || !f.full_name || f.password.length < 8} onClick={add}>Нэмэх</button>
        {err && <div className="alert error" style={{ marginTop: 8 }}>{err}</div>}{ok && <div className="alert ok" style={{ marginTop: 8 }}>{ok}</div>}
      </div>
      <div className="card span-2">
        <h3>Редакторууд ({items.filter((u) => u.is_active).length})</h3>
        {items.length === 0 && <p className="muted">Редактор алга.</p>}
        {items.map((u) => (
          <div key={u.id} className="list-row">
            <div><b>{u.full_name}</b> <span className={`badge ${u.is_active ? "green" : "gray"}`}>{u.is_active ? "Идэвхтэй" : "Хаалттай"}</span>
              <div className="muted">{u.email} · {u.decisions} шийдвэр · сүүлд {fmtDate(u.last_login)}</div></div>
            <button className="btn secondary sm" onClick={() => toggle(u)}>{u.is_active ? "Хаах" : "Нээх"}</button>
          </div>
        ))}
      </div>
    </div>
  );
}
