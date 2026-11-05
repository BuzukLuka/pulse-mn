"use client";
import { Alert, api, ApiError, Field, fmtDate, PledgeBadge, PledgeMap, PLEDGE_LABEL, Progress, RequireRole, Tabs, type Category as Cat, type Option, type Pledge, type PledgeStatus, type PledgeUpdate, type Politician } from "@pulse/shared";
import { useCallback, useEffect, useState } from "react";

export default function AdminPledges() {
  const [tab, setTab] = useState("pledges");
  const [pols, setPols] = useState<Politician[]>([]); const [pledges, setPledges] = useState<Pledge[]>([]);
  const [cats, setCats] = useState<Cat[]>([]); const [provinces, setProvinces] = useState<Option[]>([]);
  const [sel, setSel] = useState<Pledge | null>(null); const [plan, setPlan] = useState<Pledge | null>(null); const [msg, setMsg] = useState("");
  const load = useCallback(() => {
    api<Politician[]>("/pledges/politicians/").then(setPols); api<Pledge[]>("/pledges/").then(setPledges);
  }, []);
  useEffect(() => {
    load();
    api<Cat[]>("/catalog/categories/", { auth: false }).then(setCats); api<Option[]>("/catalog/provinces/", { auth: false }).then(setProvinces);
  }, [load]);
  return (
    <RequireRole roles={["admin", "editor"]}>
      <h1>Амлалтын бүртгэл</h1>
      {msg && <Alert tone="ok">{msg}</Alert>}
      <Tabs value={tab} onChange={setTab} tabs={[["pledges", "Амлалтууд"], ["queue", "Иргэний явцын мэдээ"], ["new", "+ Амлалт"], ["pol", "+ Албан тушаалтан"]]} />
      {tab === "pledges" && (
        <div className="table-wrap"><table><thead><tr><th>Албан тушаалтан</th><th>Амлалт</th><th>Төлөв</th><th>Явц / хугацаа</th><th>Нотолгоо</th><th /></tr></thead><tbody>
          {pledges.map((p) => <tr key={p.id}><td>{p.politician_name}</td><td>{p.text}<div className="muted">{p.category_name}</div></td><td><PledgeBadge status={p.status} /></td>
            <td style={{ minWidth: 140 }}><Progress value={p.progress} /><small className="muted">{p.progress}% · {p.deadline ? `⏳ ${p.deadline}` : "хугацаагүй"}{p.lat != null ? " · 📍" : ""}</small></td><td>{p.evidence_count}</td>
            <td><div className="row" style={{ gap: 6 }}><button className="btn sm" onClick={() => setPlan(p)}>Явц, хугацаа</button><button className="btn secondary sm" onClick={() => setSel(p)}>Төлөв</button></div></td></tr>)}</tbody></table></div>
      )}
      {tab === "queue" && <UpdateQueue onChange={load} />}
      {plan && <PlanModal pledge={plan} onClose={() => setPlan(null)} onSaved={() => { setPlan(null); setMsg("Явц, хугацаа, байршил хадгалагдлаа."); load(); }} />}
      {tab === "new" && <NewPledge pols={pols} cats={cats} onDone={() => { setMsg("Амлалт нэмэгдлээ."); setTab("pledges"); load(); }} />}
      {tab === "pol" && <NewPolitician provinces={provinces} onDone={() => { setMsg("Албан тушаалтан нэмэгдлээ."); setTab("new"); load(); }} />}
      {sel && <StatusModal pledge={sel} onClose={() => setSel(null)} onSaved={() => { setSel(null); setMsg("Төлөв хадгалагдлаа, түүхэд бүртгэгдлээ."); load(); }} />}
    </RequireRole>
  );
}

const errOf = (x: unknown) => (x instanceof ApiError ? (x.status === 400 ? x.fieldErrors : { form: x.message }) : { form: "Алдаа гарлаа." });

function NewPolitician({ provinces, onDone }: { provinces: Option[]; onDone: () => void }) {
  const [f, setF] = useState({ name: "", position: "", party: "", province: "", term_year: String(new Date().getFullYear()) });
  const [err, setErr] = useState<Record<string, string>>({});
  async function save() {
    setErr({});
    try { await api("/pledges/politicians/", { method: "POST", body: { ...f, province: f.province ? Number(f.province) : null, term_year: Number(f.term_year) } }); onDone(); }
    catch (x) { setErr(errOf(x)); }
  }
  const s = (k: keyof typeof f) => (e: { target: { value: string } }) => setF({ ...f, [k]: e.target.value });
  return (
    <div className="card">{err.form && <Alert>{err.form}</Alert>}{err.non_field_errors && <Alert>Энэ албан тушаалтан тухайн сонгуульд бүртгэгдсэн байна.</Alert>}
      <div className="two"><Field label="Нэр" error={err.name}><input value={f.name} onChange={s("name")} /></Field>
        <Field label="Албан тушаал" error={err.position}><input value={f.position} onChange={s("position")} /></Field>
        <Field label="Нам / эвсэл"><input value={f.party} onChange={s("party")} /></Field>
        <Field label="Аймаг"><select value={f.province} onChange={s("province")}><option value="">Улс</option>{provinces.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}</select></Field>
        <Field label="Сонгуулийн он" error={err.term_year}><input value={f.term_year} onChange={s("term_year")} /></Field></div>
      <button className="btn" onClick={save}>Хадгалах</button></div>
  );
}

function NewPledge({ pols, cats, onDone }: { pols: Politician[]; cats: Cat[]; onDone: () => void }) {
  const [f, setF] = useState({ politician: "", text: "", category: "", source: "", source_url: "" });
  const [err, setErr] = useState<Record<string, string>>({});
  async function save() {
    setErr({});
    try { await api("/pledges/", { method: "POST", body: { ...f, politician: Number(f.politician) || null, category: Number(f.category) || null } }); onDone(); }
    catch (x) { setErr(errOf(x)); }
  }
  const s = (k: keyof typeof f) => (e: { target: { value: string } }) => setF({ ...f, [k]: e.target.value });
  return (
    <div className="card">{err.form && <Alert>{err.form}</Alert>}
      <Field label="Албан тушаалтан" error={err.politician}><select value={f.politician} onChange={s("politician")}><option value="">—</option>{pols.map((p) => <option key={p.id} value={p.id}>{p.name} — {p.constituency_number ? `${p.constituency_number}-р тойрог ${p.constituency_name}` : p.party} ({p.term_year})</option>)}</select></Field>
      <Field label="Амлалтын текст" error={err.text}><textarea value={f.text} onChange={s("text")} style={{ minHeight: 90 }} /></Field>
      <div className="two"><Field label="Салбар" error={err.category}><select value={f.category} onChange={s("category")}><option value="">—</option>{cats.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}</select></Field>
        <Field label="Эх сурвалж" error={err.source}><input value={f.source} onChange={s("source")} /></Field></div>
      <Field label="Эх сурвалжийн холбоос" error={err.source_url}><input value={f.source_url} onChange={s("source_url")} /></Field>
      <p className="muted">Шинэ амлалт «Мэдээлэл дутуу» төлөвтэй эхэлнэ — төлөв өөрчлөхөд нотлох баримт заавал.</p>
      <button className="btn" onClick={save}>Хадгалах</button></div>
  );
}

function StatusModal({ pledge, onClose, onSaved }: { pledge: Pledge; onClose: () => void; onSaved: () => void }) {
  const [status, setStatus] = useState<PledgeStatus>(pledge.status);
  const [reason, setReason] = useState(""); const [ev, setEv] = useState({ kind: "document", source: "", date: "", url: "", note: "" });
  const [err, setErr] = useState("");
  async function save() {
    setErr("");
    try { await api(`/pledges/${pledge.id}/update-status/`, { method: "POST", body: { status, reason, evidence: ev } }); onSaved(); }
    catch (x) { setErr(x instanceof ApiError ? (x.status === 400 ? Object.values(x.fieldErrors).join(" ") : x.message) : "Алдаа гарлаа."); }
  }
  return (
    <div className="modal-bg" onClick={onClose}><div className="modal" onClick={(e) => e.stopPropagation()}>
      <h2 style={{ marginTop: 0 }}>Төлөв өөрчлөх</h2><p className="muted">{pledge.text}</p>
      {err && <Alert>{err}</Alert>}
      <Field label="Шинэ төлөв"><select value={status} onChange={(e) => setStatus(e.target.value as PledgeStatus)}>{(Object.keys(PLEDGE_LABEL) as PledgeStatus[]).map((k) => <option key={k} value={k}>{PLEDGE_LABEL[k]}</option>)}</select></Field>
      <Field label="Шалтгаан (заавал)"><textarea style={{ minHeight: 60 }} value={reason} onChange={(e) => setReason(e.target.value)} /></Field>
      <h3>Нотлох баримт (заавал)</h3>
      <div className="two"><Field label="Эх сурвалж"><input value={ev.source} onChange={(e) => setEv({ ...ev, source: e.target.value })} /></Field>
        <Field label="Огноо"><input type="date" value={ev.date} onChange={(e) => setEv({ ...ev, date: e.target.value })} /></Field></div>
      <Field label="Холбоос"><input value={ev.url} onChange={(e) => setEv({ ...ev, url: e.target.value })} /></Field>
      <div className="row"><button className="btn" onClick={save}>Хадгалах</button><button className="btn secondary" onClick={onClose}>Болих</button></div>
    </div></div>
  );
}

/** Admin: хэрэгжих хугацаа, явцын хувь, газрын зураг дээрх байршил; урьдчилан баталгаажсан барилгын зураг. */
function PlanModal({ pledge, onClose, onSaved }: { pledge: Pledge; onClose: () => void; onSaved: () => void }) {
  const [deadline, setDeadline] = useState(pledge.deadline ?? ""); const [progress, setProgress] = useState(pledge.progress);
  const [loc, setLoc] = useState(pledge.location_name); const [pos, setPos] = useState(pledge.lat != null && pledge.lng != null ? { lat: pledge.lat, lng: pledge.lng } : null);
  const [photo, setPhoto] = useState<File | null>(null); const [note, setNote] = useState(""); const [err, setErr] = useState(""); const [busy, setBusy] = useState(false);
  async function save() {
    setErr(""); setBusy(true);
    try {
      await api(`/pledges/${pledge.id}/`, { method: "PATCH", body: { deadline: deadline || null, progress, location_name: loc, lat: pos?.lat ?? null, lng: pos?.lng ?? null } });
      if (photo) {  // урьдчилан баталгаажсан зураг: оруулаад шууд баталгаажуулна (AI шалгалтын тэмдэглэлтэй)
        const fd = new FormData(); fd.append("text", note.trim().length >= 10 ? note : `Pulse.mn баталгаажуулсан зураг: ${pledge.text.slice(0, 120)}`);
        fd.append("photo", photo); fd.append("progress", String(progress));
        if (pos) { fd.append("lat", String(pos.lat)); fd.append("lng", String(pos.lng)); }
        const u = await api<PledgeUpdate>(`/pledges/${pledge.id}/updates/`, { method: "POST", body: fd });
        await api(`/admin/pledge-updates/${u.id}/review/`, { method: "POST", body: { approve: true, note: "Pulse.mn урьдчилан баталгаажуулсан", progress } });
      }
      onSaved();
    } catch (x) { setErr(x instanceof ApiError ? (x.status === 400 ? Object.values(x.fieldErrors).join(" ") : x.message) : "Алдаа гарлаа."); }
    finally { setBusy(false); }
  }
  return (
    <div className="modal-bg" onClick={onClose}><div className="modal" style={{ maxWidth: 760 }} onClick={(e) => e.stopPropagation()}>
      <h2 style={{ marginTop: 0 }}>Явц, хугацаа, байршил</h2><p className="muted">{pledge.politician_name} — {pledge.text}</p>
      {err && <Alert>{err}</Alert>}
      <div className="two">
        <Field label="Хэрэгжих эцсийн хугацаа"><input type="date" value={deadline} onChange={(e) => setDeadline(e.target.value)} /></Field>
        <Field label={`Явц: ${progress}%`}><input type="range" min={0} max={100} step={5} value={progress} onChange={(e) => setProgress(Number(e.target.value))} /></Field>
      </div>
      <Field label="Байршлын нэр"><input value={loc} placeholder="Жишээ: Хан-Уул дүүрэг, 15-р хороо" onChange={(e) => setLoc(e.target.value)} /></Field>
      <PledgeMap height={280} points={[]} picked={pos} onPick={(lat, lng) => setPos({ lat, lng })} />
      <small className="muted">Газрын зураг дээр дарж байршлыг заана{pos ? ` · ${pos.lat}, ${pos.lng}` : ""}.</small>
      <h3>Урьдчилан баталгаажсан зураг (заавал биш)</h3>
      <div className="two"><Field label="Зураг"><input type="file" accept="image/jpeg,image/png,image/webp" onChange={(e) => setPhoto(e.target.files?.[0] ?? null)} /></Field>
        <Field label="Тайлбар"><input value={note} onChange={(e) => setNote(e.target.value)} placeholder="Жишээ: барилгын ажил 40% — 2026.10.01" /></Field></div>
      <div className="row"><button className="btn" disabled={busy} onClick={save}>{busy ? "Хадгалж байна…" : "Хадгалах"}</button><button className="btn secondary" onClick={onClose}>Болих</button></div>
    </div></div>
  );
}

/** Иргэдийн оруулсан явцын мэдээ: AI урьдчилсан шалгалт → админ баталгаажуулна / татгалзана. */
function UpdateQueue({ onChange }: { onChange: () => void }) {
  const [status, setStatus] = useState("pending"); const [rows, setRows] = useState<PledgeUpdate[]>([]); const [note, setNote] = useState<Record<number, string>>({});
  const load = useCallback(() => { api<{ results: PledgeUpdate[] }>(`/admin/pledge-updates/?status=${status}`).then((r) => setRows(r.results)).catch(() => setRows([])); }, [status]);
  useEffect(load, [load]);
  async function review(u: PledgeUpdate, approve: boolean) {
    await api(`/admin/pledge-updates/${u.id}/review/`, { method: "POST", body: { approve, note: note[u.id] ?? "", progress: approve ? u.progress_claim : null } });
    load(); onChange();
  }
  return (
    <>
      <Tabs value={status} onChange={setStatus} tabs={[["pending", "Шалгах"], ["verified", "Баталгаажсан"], ["rejected", "Татгалзсан"]]} />
      {rows.length === 0 && <p className="muted">Мэдээ алга.</p>}
      {rows.map((u) => (
        <div key={u.id} className="card">
          <div className="row" style={{ alignItems: "flex-start", gap: 16 }}>
            {u.photo_url ? <a href={u.photo_url} target="_blank" rel="noreferrer"><img src={u.photo_url} alt="" style={{ width: 180, aspectRatio: "4/3", objectFit: "cover", borderRadius: 6 }} /></a> : <div className="muted" style={{ width: 180 }}>Зураггүй</div>}
            <div style={{ flex: 1 }}>
              <b>{u.politician_name}</b> — {u.pledge_text}
              <p style={{ margin: "6px 0" }}>{u.text}</p>
              <div className="muted">{u.author_name} · {fmtDate(u.created_at)}{u.progress_claim != null ? ` · иргэний үнэлгээ ${u.progress_claim}%` : ""}{u.lat != null ? ` · 📍 ${u.lat}, ${u.lng}` : ""}</div>
              <div style={{ marginTop: 6 }}><span className={`badge ${(u.ai_check.score ?? 0) >= 70 ? "green" : (u.ai_check.score ?? 0) >= 40 ? "amber" : "red"}`}>AI оноо {u.ai_check.score}/100</span>
                {u.ai_check.flags?.map((f) => <span key={f} className="badge amber" style={{ marginLeft: 6 }}>{f}</span>)}</div>
              {status === "pending" ? (
                <div className="row" style={{ marginTop: 8 }}>
                  <input placeholder="Тэмдэглэл" value={note[u.id] ?? ""} onChange={(e) => setNote({ ...note, [u.id]: e.target.value })} style={{ flex: 1 }} />
                  <button className="btn sm" onClick={() => review(u, true)}>✓ Баталгаажуулах</button>
                  <button className="btn secondary sm" onClick={() => review(u, false)}>Татгалзах</button>
                </div>) : u.review_note && <div className="muted">Тэмдэглэл: {u.review_note}</div>}
            </div>
          </div>
        </div>
      ))}
    </>
  );
}
