"use client";
import { Alert, api, ApiError, COMPLAINT_KINDS, Field, useAuth } from "@pulse/shared";
import { useState } from "react";

/** Мэдээ / амлалт / үзүүлэлтийн талаар гомдол, санал илгээх. */
export default function ComplaintForm({ targetType, targetId }: { targetType: "content" | "pledge" | "indicator"; targetId: number }) {
  const { user } = useAuth();
  const [open, setOpen] = useState(false);
  const [f, setF] = useState({ kind: "wrong", text: "", evidence_url: "" });
  const [err, setErr] = useState<Record<string, string>>({}); const [ok, setOk] = useState(false);
  if (!user) return <p className="muted"><a href="/login">Нэвтэрч</a> гомдол, санал илгээнэ үү.</p>;
  async function send() {
    setErr({});
    try {
      await api("/complaints/", { method: "POST", body: { ...f, target_type: targetType, target_id: targetId } });
      setOk(true); setOpen(false);
    } catch (x) { setErr(x instanceof ApiError ? (x.status === 400 ? x.fieldErrors : { form: x.message }) : { form: "Алдаа гарлаа." }); }
  }
  if (ok) return <Alert tone="ok">Гомдол хүлээн авлаа. Админ шалгаж хариу өгнө.</Alert>;
  return (
    <div>
      {!open && <button className="btn secondary sm" onClick={() => setOpen(true)}>⚑ Гомдол / санал илгээх</button>}
      {open && (
        <div className="card">
          {err.form && <Alert>{err.form}</Alert>}
          <Field label="Төрөл"><select value={f.kind} onChange={(e) => setF({ ...f, kind: e.target.value })}>
            {COMPLAINT_KINDS.map(([k, l]) => <option key={k} value={k}>{l}</option>)}</select></Field>
          <Field label="Тайлбар" error={err.text}><textarea style={{ minHeight: 90 }} value={f.text} onChange={(e) => setF({ ...f, text: e.target.value })} /></Field>
          <Field label="Нотлох холбоос (заавал биш)" error={err.evidence_url}><input value={f.evidence_url} onChange={(e) => setF({ ...f, evidence_url: e.target.value })} /></Field>
          <div className="row"><button className="btn" onClick={send}>Илгээх</button><button className="btn secondary" onClick={() => setOpen(false)}>Болих</button></div>
        </div>
      )}
    </div>
  );
}
