"use client";
import { Alert, api, COMPLAINT_KINDS, COMPLAINT_STATUS, ApiError, fmtDate, RequireRole, type Complaint, type Paginated } from "@pulse/shared";
import { useCallback, useEffect, useState } from "react";

export default function AdminComplaints() {
  const [status, setStatus] = useState("open"); const [d, setD] = useState<Paginated<Complaint> | null>(null);
  const [sel, setSel] = useState<Complaint | null>(null); const [res, setRes] = useState(""); const [err, setErr] = useState("");
  const load = useCallback(() => api<Paginated<Complaint>>(`/admin/complaints/?status=${status}`).then(setD), [status]);
  useEffect(() => { load(); }, [load]);
  const kind = (k: string) => COMPLAINT_KINDS.find(([x]) => x === k)?.[1] ?? k;
  async function resolve(st: "resolved" | "dismissed") {
    setErr("");
    try { await api(`/admin/complaints/${sel!.id}/resolve/`, { method: "POST", body: { status: st, resolution: res } }); setSel(null); setRes(""); load(); }
    catch (x) { setErr(x instanceof ApiError ? x.message : "Алдаа гарлаа."); }
  }
  const link = (c: Complaint) => c.target_type === "content" ? `/review/${c.target_id}` : null;
  return (
    <RequireRole roles={["admin"]}>
      <h1>Гомдол, санал</h1>
      <div className="pill-row" style={{ marginBottom: 12 }}>{Object.entries(COMPLAINT_STATUS).map(([k, l]) => <button key={k} className={`pill ${status === k ? "on" : ""}`} onClick={() => setStatus(k)}>{l}</button>)}</div>
      {d?.results.length === 0 && <p className="muted">Гомдол алга.</p>}
      {d?.results.map((c) => (
        <div className="card" key={c.id}>
          <div className="row spread"><b>{kind(c.kind)} · {c.target_type} #{c.target_id}</b><small className="muted">{c.reporter_email} · {fmtDate(c.created_at)}</small></div>
          <p>{c.text}</p>{c.evidence_url && <a href={c.evidence_url} target="_blank">Нотолгоо</a>}
          {c.resolution && <div className="alert info">Шийдвэр: {c.resolution}</div>}
          {c.status === "open" && <button className="btn secondary sm" onClick={() => setSel(c)}>Шийдвэрлэх</button>}
        </div>
      ))}
      {sel && (
        <div className="modal-bg" onClick={() => setSel(null)}><div className="modal" onClick={(e) => e.stopPropagation()}>
          <h2 style={{ marginTop: 0 }}>Гомдол #{sel.id}</h2><p>{sel.text}</p>
          {link(sel) && <p className="muted">Мэдээг <a href={`/content`}>Контент хяналт</a> хэсгээс нууж болно.</p>}
          {err && <Alert>{err}</Alert>}
          <div className="field"><span>Шийдвэрийн тайлбар (заавал, гомдол гаргагчид мэдэгдэнэ)</span><textarea value={res} onChange={(e) => setRes(e.target.value)} /></div>
          <div className="row"><button className="btn ok" onClick={() => resolve("resolved")}>Шийдвэрлэсэн</button><button className="btn secondary" onClick={() => resolve("dismissed")}>Хүлээн аваагүй</button><button className="btn secondary" onClick={() => setSel(null)}>Болих</button></div>
        </div></div>
      )}
    </RequireRole>
  );
}
