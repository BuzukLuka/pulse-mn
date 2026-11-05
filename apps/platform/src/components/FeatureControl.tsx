"use client";
import { api, ApiError, fmtDateTime, type Content } from "@pulse/shared";
import { useState } from "react";

const HOURS = [6, 12, 24, 48, 72];

/** Топ мэдээ: сэтгүүлч хүсэлт гаргана (mode="request"), редакц / редактор хугацаагаар тавина (mode="decide"). */
export default function FeatureControl({ c, url, mode, onDone }: { c: Content; url: string; mode: "request" | "decide"; onDone: (c: Content) => void }) {
  const [hours, setHours] = useState(c.feature_request_hours ?? 24); const [err, setErr] = useState("");
  async function send(h: number) {
    setErr("");
    try { onDone(await api<Content>(url, { method: "POST", body: { hours: h } })); }
    catch (x) { setErr(x instanceof ApiError ? x.message : "Алдаа гарлаа."); }
  }
  return (
    <div className="card">
      <div className="row spread"><h3 style={{ margin: 0 }}>⭐ Топ мэдээ</h3>
        {c.is_featured ? <span className="badge green">Топод · {fmtDateTime(c.featured_until)} хүртэл</span>
          : c.feature_request_hours ? <span className="badge amber">Хүсэлт · {c.feature_request_hours} цаг</span> : null}</div>
      <div className="row" style={{ marginTop: 10 }}>
        <select value={hours} onChange={(e) => setHours(Number(e.target.value))}>{HOURS.map((h) => <option key={h} value={h}>{h} цаг</option>)}</select>
        {mode === "request"
          ? <button className="btn secondary sm" disabled={c.is_featured} onClick={() => send(hours)}>Топ болгох хүсэлт</button>
          : <><button className="btn sm" onClick={() => send(hours)}>{c.is_featured ? "Хугацаа сунгах" : "Топ болгох"}</button>
              {c.is_featured && <button className="btn ghost sm" onClick={() => send(0)}>Топоос буулгах</button>}</>}
      </div>
      {err && <div className="alert error" style={{ marginTop: 8 }}>{err}</div>}
    </div>
  );
}
