"use client";
import { useCallback, useEffect, useState, type CSSProperties } from "react";
import { api, ApiError } from "./api";
import { useAuth } from "./auth";
import { fmtDate, fmtDateTime } from "./labels";
import type { HistoryItem, RatingSuggestion, RatingSummary } from "./types";

/** Одоор харуулах үнэлгээ (бутархай одыг хэсэгчлэн будна). */
export function Stars({ value, size = 16 }: { value: number | null; size?: number }) {
  const v = value ?? 0;
  return (
    <span className="stars" style={{ fontSize: size }} aria-label={value ? `${value} / 5` : "Үнэлгээгүй"}>
      {[1, 2, 3, 4, 5].map((i) => <i key={i} style={{ "--fill": `${Math.max(0, Math.min(1, v - i + 1)) * 100}%` } as CSSProperties}>★</i>)}
    </span>
  );
}

export const RatingBadge = ({ r }: { r: RatingSummary }) =>
  <span className="row" style={{ gap: 6 }}><Stars value={r.avg} size={14} /><small className="muted">{r.avg ?? "—"} ({r.count})</small></span>;

interface RatingData {
  summary: RatingSummary; mine: { score: number; comment: string } | null;
  items: { id: number; score: number; comment: string; rater: string; rater_role: string; updated_at: string }[];
}

/** Үнэлгээ харуулах + өгөх + AI-ийн санал (сэтгүүлч, редакцын профайлд). */
export function RatingPanel({ targetId, targetLabel }: { targetId: number; targetLabel: string }) {
  const { user } = useAuth();
  const [d, setD] = useState<RatingData | null>(null); const [ai, setAi] = useState<RatingSuggestion | null>(null);
  const [score, setScore] = useState(0); const [comment, setComment] = useState("");
  const [msg, setMsg] = useState(""); const [err, setErr] = useState("");
  const load = useCallback(() => api<RatingData>(`/ratings/?target=${targetId}`, { auth: !!user }).then((x) => {
    setD(x); if (x.mine) { setScore(x.mine.score); setComment(x.mine.comment); }
  }).catch(() => {}), [targetId, user]);
  useEffect(() => { load(); api<RatingSuggestion>(`/ratings/suggest/?target=${targetId}`, { auth: false }).then(setAi).catch(() => {}); }, [load, targetId]);

  async function submit() {
    setErr(""); setMsg("");
    try { await api("/ratings/", { method: "POST", body: { target: targetId, score, comment } }); setMsg("Үнэлгээ хадгалагдлаа."); load(); }
    catch (x) { setErr(x instanceof ApiError ? x.message : "Хадгалж чадсангүй."); }
  }
  if (!d) return null;
  const s = d.summary; const canRate = user && user.id !== targetId;
  return (
    <div className="card">
      <div className="rating-head">
        <div><div className="stat">{s.avg ?? "—"}</div><Stars value={s.avg} size={20} /><div className="muted">{s.count} үнэлгээ</div></div>
        <div className="dist">{[5, 4, 3, 2, 1].map((k) => (
          <div key={k} className="row" style={{ gap: 8 }}><small style={{ width: 14 }}>{k}</small>
            <div className="meter" style={{ flex: 1, marginTop: 0 }}><i style={{ width: `${s.count ? (s.distribution[k] / s.count) * 100 : 0}%`, background: "var(--amber)" }} /></div>
            <small className="muted" style={{ width: 20 }}>{s.distribution[k]}</small></div>))}</div>
      </div>
      {ai && (
        <div className="alert info" style={{ marginTop: 14 }}>
          <div className="row spread"><b>✨ AI-ийн санал болгох үнэлгээ: {ai.score} / 5</b><small>{ai.source === "gemini" ? "Gemini" : "Үзүүлэлтэд суурилсан"}</small></div>
          <ul style={{ margin: "6px 0 0", paddingLeft: 18 }}>{ai.reasons.map((r) => <li key={r}>{r}</li>)}</ul>
          <small className="muted">{targetLabel} хэрхэн үнэлэгдэх ёстойг баримтаар санал болгоно. Эцсийн үнэлгээг та өгнө.</small>
        </div>
      )}
      {canRate ? (
        <div style={{ marginTop: 14 }}>
          <b>{d.mine ? "Таны үнэлгээ (засах)" : "Үнэлгээ өгөх"}</b>
          <div className="row" style={{ margin: "8px 0" }}>
            {[1, 2, 3, 4, 5].map((i) => <button key={i} type="button" className={`star-btn ${i <= score ? "on" : ""}`} onClick={() => setScore(i)} aria-label={`${i} од`}>★</button>)}
            {ai && <button type="button" className="btn ghost sm" onClick={() => setScore(Math.round(ai.score))}>AI саналыг ашиглах</button>}
          </div>
          <textarea style={{ minHeight: 70, width: "100%" }} placeholder="Сэтгэгдэл (заавал биш)" value={comment} onChange={(e) => setComment(e.target.value)} />
          {err && <div className="alert error" style={{ marginTop: 8 }}>{err}</div>}{msg && <div className="alert ok" style={{ marginTop: 8 }}>{msg}</div>}
          <button className="btn sm" style={{ marginTop: 8 }} disabled={!score} onClick={submit}>Хадгалах</button>
        </div>
      ) : !user && <p className="muted" style={{ marginTop: 12 }}><a href="/login">Нэвтэрч</a> үнэлгээ өгнө үү.</p>}
      {d.items.length > 0 && <div style={{ marginTop: 16 }}>{d.items.slice(0, 6).map((r) => (
        <div key={r.id} className="review"><div className="row spread"><b>{r.rater}</b><Stars value={r.score} size={13} /></div>
          {r.comment && <div className="muted">{r.comment}</div>}<small className="muted">{fmtDate(r.updated_at)}</small></div>))}</div>}
    </div>
  );
}

/** Контентын төлвийн түүх (хэзээ, хэн, ямар шийдвэр). */
export function Timeline({ items }: { items: HistoryItem[] }) {
  return (
    <ol className="timeline">
      {items.map((h, i) => (
        <li key={i} className={h.to ?? h.action}>
          <b>{h.label}</b> <small className="muted">{fmtDateTime(h.at)}{h.actor ? ` · ${h.actor}` : ""}</small>
          {h.reason && <div className="muted">“{h.reason}”</div>}
        </li>
      ))}
    </ol>
  );
}
