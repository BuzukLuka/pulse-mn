"use client";
import { Alert, api, ApiError, Field, fmtDateTime, qs, RequireRole, ROLE_LABEL, type Paginated, type Role, type User } from "@pulse/shared";
import { useCallback, useEffect, useState } from "react";

export default function Users() {
  const [q, setQ] = useState(""); const [role, setRole] = useState(""); const [data, setData] = useState<Paginated<User> | null>(null);
  const [page, setPage] = useState(1); const [sel, setSel] = useState<User | null>(null);
  const load = useCallback(() => api<Paginated<User>>(`/admin/users/${qs({ q, role, page })}`).then(setData).catch(() => {}), [q, role, page]);
  useEffect(() => { const t = setTimeout(load, 250); return () => clearTimeout(t); }, [load]);
  async function verify(u: User) {
    const reason = window.prompt(u.is_verified ? "Баталгаажуулалт цуцлах шалтгаан:" : "Баталгаажуулах үндэслэл (жишээ: үнэмлэх шалгасан):");
    if (!reason) return;
    try { await api(`/admin/users/${u.id}/verify/`, { method: "POST", body: { verified: !u.is_verified, reason } }); load(); } catch { /* ignore */ }
  }
  return (
    <RequireRole roles={["admin"]}>
      <h1>Хэрэглэгч, эрхийн удирдлага</h1>
      <div className="card row">
        <input style={{ flex: 1 }} placeholder="Имэйл / нэрээр хайх" value={q} onChange={(e) => { setQ(e.target.value); setPage(1); }} />
        <select value={role} onChange={(e) => { setRole(e.target.value); setPage(1); }}>
          <option value="">Бүх үүрэг</option>{Object.entries(ROLE_LABEL).map(([k, l]) => <option key={k} value={k}>{l}</option>)}
        </select>
      </div>
      <div className="table-wrap"><table>
        <thead><tr><th>Хэрэглэгч</th><th>Үүрэг</th><th>Төлөв</th><th>Сүүлд нэвтэрсэн</th><th /></tr></thead>
        <tbody>{data?.results.map((u) => (
          <tr key={u.id}><td><b>{u.full_name || "—"}</b> {u.is_verified && <span className="badge green">Баталгаажсан</span>}<div className="muted">{u.email}</div></td><td>{ROLE_LABEL[u.role]}</td>
            <td>{u.is_active ? <span className="badge green">Идэвхтэй</span> : <span className="badge red">Түр хаагдсан</span>}</td>
            <td>{fmtDateTime(u.last_login)}</td><td><button className="btn secondary sm" onClick={() => setSel(u)}>Эрх өөрчлөх</button>{u.role === "journalist" && <> <button className="btn secondary sm" onClick={() => verify(u)}>{u.is_verified ? "Баталгаажуулалт цуцлах" : "Сэтгүүлч баталгаажуулах"}</button></>}</td></tr>
        ))}</tbody>
      </table></div>
      {data && (data.next || data.previous) && <div className="row" style={{ marginTop: 12 }}>
        <button className="btn secondary sm" disabled={!data.previous} onClick={() => setPage(page - 1)}>← Өмнөх</button>
        <button className="btn secondary sm" disabled={!data.next} onClick={() => setPage(page + 1)}>Дараах →</button></div>}
      {sel && <AccessModal user={sel} onClose={() => setSel(null)} onSaved={() => { setSel(null); load(); }} />}
    </RequireRole>
  );
}

function AccessModal({ user, onClose, onSaved }: { user: User; onClose: () => void; onSaved: () => void }) {
  const [role, setRole] = useState<Role>(user.role); const [active, setActive] = useState(user.is_active);
  const [reason, setReason] = useState(""); const [err, setErr] = useState(""); const [busy, setBusy] = useState(false);
  async function save() {
    setBusy(true); setErr("");
    try { await api(`/admin/users/${user.id}/`, { method: "PATCH", body: { role, is_active: active, reason } }); onSaved(); }
    catch (x) {
      setErr(x instanceof ApiError && x.status === 409 ? "Сүүлчийн админы эрхийг хасах боломжгүй." : x instanceof ApiError && x.status === 422 ? "Шалтгаан заавал бичнэ үү." : "Хадгалж чадсангүй.");
    } finally { setBusy(false); }
  }
  return (
    <div className="modal-bg" onClick={onClose}><div className="modal" onClick={(e) => e.stopPropagation()}>
      <h2 style={{ marginTop: 0 }}>{user.email}</h2>
      {err && <Alert>{err}</Alert>}
      <Field label="Үүрэг"><select value={role} onChange={(e) => setRole(e.target.value as Role)}>{Object.entries(ROLE_LABEL).map(([k, l]) => <option key={k} value={k}>{l}</option>)}</select></Field>
      <label className="row" style={{ marginBottom: 12 }}><input type="checkbox" checked={active} onChange={(e) => setActive(e.target.checked)} /> Акаунт идэвхтэй</label>
      <Field label="Шалтгаан (заавал)"><textarea style={{ minHeight: 80 }} value={reason} onChange={(e) => setReason(e.target.value)} /></Field>
      <div className="row"><button className="btn" onClick={save} disabled={busy}>Хадгалах</button><button className="btn secondary" onClick={onClose}>Болих</button></div>
      <p className="muted">Хадгалахад хэрэглэгчийн идэвхтэй сесс цуцлагдаж, аудит лог бичигдэнэ.</p>
    </div></div>
  );
}
