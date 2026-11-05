"use client";
import { api, ApiError, PledgeMap, type Pledge, type PledgeUpdate } from "@pulse/shared";
import { useState } from "react";

/** Нэвтэрсэн иргэн амлалтын явцын мэдээг зураг, байршилтай оруулна. AI урьдчилан шалгаад админ баталгаажуулна. */
export default function PledgeUpdateForm({ pledge }: { pledge: Pledge }) {
  const [text, setText] = useState(""); const [file, setFile] = useState<File | null>(null);
  const [pos, setPos] = useState<{ lat: number; lng: number } | null>(null); const [progress, setProgress] = useState("");
  const [res, setRes] = useState<PledgeUpdate | null>(null); const [err, setErr] = useState(""); const [busy, setBusy] = useState(false);
  function locate() {
    navigator.geolocation?.getCurrentPosition((p) => setPos({ lat: +p.coords.latitude.toFixed(6), lng: +p.coords.longitude.toFixed(6) }),
      () => setErr("Байршил авч чадсангүй — газрын зураг дээр дарж сонгоно уу."));
  }
  async function send() {
    setBusy(true); setErr("");
    const fd = new FormData(); fd.append("text", text);
    if (file) fd.append("photo", file);
    if (pos) { fd.append("lat", String(pos.lat)); fd.append("lng", String(pos.lng)); }
    if (progress) fd.append("progress", progress);
    try { setRes(await api<PledgeUpdate>(`/pledges/${pledge.id}/updates/`, { method: "POST", body: fd })); }
    catch (x) { setErr(x instanceof ApiError ? x.message : "Алдаа гарлаа."); } finally { setBusy(false); }
  }
  if (res) return (
    <div className="alert">
      <b>Хүлээн авлаа — шалгаж байна.</b> AI урьдчилсан оноо: {res.ai_check.score}/100
      {res.ai_check.flags?.length ? <ul style={{ margin: "6px 0 0" }}>{res.ai_check.flags.map((f) => <li key={f}>{f}</li>)}</ul> : null}
      <div className="muted">Pulse.mn-ийн админ баталгаажуулсны дараа нийтэд харагдана.</div>
    </div>
  );
  return (
    <div className="card" style={{ background: "#fafafa" }}>
      <h3 style={{ marginTop: 0 }}>📷 Явцын мэдээ оруулах</h3>
      <textarea rows={3} placeholder="Юу харсан бэ? (жишээ: цэцэрлэгийн барилгын суурь цутгагдсан, 2 давхар хүртэл өрсөн)" value={text} onChange={(e) => setText(e.target.value)} style={{ width: "100%" }} />
      <div className="row" style={{ flexWrap: "wrap", marginTop: 8 }}>
        <input type="file" accept="image/jpeg,image/png,image/webp" capture="environment" onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
        <select value={progress} onChange={(e) => setProgress(e.target.value)}><option value="">Явц (миний үнэлгээ)</option>
          {[0, 10, 25, 50, 75, 90, 100].map((v) => <option key={v} value={v}>{v}%</option>)}</select>
        <button className="btn ghost sm" type="button" onClick={locate}>📍 Миний байршил</button>
        {pos && <small className="muted">{pos.lat}, {pos.lng}</small>}
      </div>
      <div style={{ marginTop: 8 }}>
        <PledgeMap height={220} onPick={(lat, lng) => setPos({ lat, lng })} picked={pos}
          points={pledge.lat != null && pledge.lng != null ? [{ id: pledge.id, lat: pledge.lat, lng: pledge.lng, title: pledge.location_name || "Амлалтын байршил", progress: pledge.progress }] : []} />
        <small className="muted">Газрын зураг дээр дарж зургаа авсан газраа заана. Зураг давхардсан, байршлаас хол бол AI анхааруулна.</small>
      </div>
      {err && <div className="alert error" style={{ marginTop: 8 }}>{err}</div>}
      <button className="btn sm" style={{ marginTop: 8 }} disabled={busy || text.trim().length < 10} onClick={send}>{busy ? "Илгээж байна…" : "Илгээх"}</button>
    </div>
  );
}
