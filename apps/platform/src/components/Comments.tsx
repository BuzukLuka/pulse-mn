"use client";
import { api, ApiError, fmtDateTime, useAuth, type Paginated } from "@pulse/shared";
import { useCallback, useEffect, useState } from "react";

interface Comment { id: number; text: string; is_anonymous: boolean; author_name: string; mine: boolean; created_at: string }

/** Мэдээний сэтгэгдэл. Иргэн нэрээ нууцалж болно (бусдад «Нэргүй иргэн»). */
export default function Comments({ contentId }: { contentId: number }) {
  const { user } = useAuth();
  const [items, setItems] = useState<Comment[]>([]); const [text, setText] = useState(""); const [anon, setAnon] = useState(true);
  const [err, setErr] = useState(""); const [busy, setBusy] = useState(false);
  const load = useCallback(() => api<Paginated<Comment>>(`/comments/?content=${contentId}`, { auth: !!user }).then((d) => setItems(d.results)).catch(() => {}), [contentId, user]);
  useEffect(() => { load(); }, [load]);
  const isCitizen = user?.role === "citizen";
  async function send() {
    setBusy(true); setErr("");
    try { await api("/comments/", { method: "POST", body: { content: contentId, text, is_anonymous: isCitizen && anon } }); setText(""); load(); }
    catch (x) { setErr(x instanceof ApiError ? (Object.values(x.fieldErrors)[0] ?? x.message) : "Илгээж чадсангүй."); }
    finally { setBusy(false); }
  }
  async function remove(id: number) { await api(`/comments/${id}/`, { method: "DELETE" }); load(); }
  return (
    <section style={{ marginTop: 32 }}>
      <h2>Сэтгэгдэл ({items.length})</h2>
      {user ? (
        <div className="card">
          <textarea style={{ minHeight: 80, width: "100%" }} maxLength={1000} placeholder="Сэтгэгдлээ бичнэ үү…" value={text} onChange={(e) => setText(e.target.value)} />
          <div className="row spread" style={{ marginTop: 8 }}>
            {isCitizen ? <label className="check-row" style={{ margin: 0 }}><input type="checkbox" checked={anon} onChange={(e) => setAnon(e.target.checked)} /> Нэрээ нууцлах</label> : <span />}
            <button className="btn sm" disabled={busy || text.trim().length < 2} onClick={send}>Илгээх</button>
          </div>
          {err && <div className="alert error" style={{ marginTop: 8 }}>{err}</div>}
        </div>
      ) : <p className="muted"><a href="/login">Нэвтэрч</a> сэтгэгдэл бичнэ үү.</p>}
      {items.map((c) => (
        <div key={c.id} className="list-row">
          <div><b>{c.author_name}</b> <small className="muted">· {fmtDateTime(c.created_at)}</small><div>{c.text}</div></div>
          {(c.mine || user?.role === "admin") && <button className="btn ghost sm" onClick={() => remove(c.id)}>{c.mine ? "Устгах" : "Нуух"}</button>}
        </div>
      ))}
    </section>
  );
}
