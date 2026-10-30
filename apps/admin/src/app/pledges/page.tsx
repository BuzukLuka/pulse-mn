"use client";
import { Alert, api, ApiError, Field, fmtDate, PledgeBadge, PLEDGE_LABEL, RequireRole, Tabs, type Category as Cat, type Option, type Pledge, type PledgeStatus, type Politician } from "@pulse/shared";
import { useCallback, useEffect, useState } from "react";

export default function AdminPledges() {
  const [tab, setTab] = useState("pledges");
  const [pols, setPols] = useState<Politician[]>([]); const [pledges, setPledges] = useState<Pledge[]>([]);
  const [cats, setCats] = useState<Cat[]>([]); const [provinces, setProvinces] = useState<Option[]>([]);
  const [sel, setSel] = useState<Pledge | null>(null); const [msg, setMsg] = useState("");
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
      <Tabs value={tab} onChange={setTab} tabs={[["pledges", "Амлалтууд"], ["new", "+ Амлалт"], ["pol", "+ Албан тушаалтан"]]} />
      {tab === "pledges" && (
        <div className="table-wrap"><table><thead><tr><th>Албан тушаалтан</th><th>Амлалт</th><th>Төлөв</th><th>Нотолгоо</th><th /></tr></thead><tbody>
          {pledges.map((p) => <tr key={p.id}><td>{p.politician_name}</td><td>{p.text}<div className="muted">{p.category_name}</div></td><td><PledgeBadge status={p.status} /></td><td>{p.evidence_count}</td>
            <td><button className="btn secondary sm" onClick={() => setSel(p)}>Төлөв өөрчлөх</button></td></tr>)}</tbody></table></div>
      )}
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
      <Field label="Албан тушаалтан" error={err.politician}><select value={f.politician} onChange={s("politician")}><option value="">—</option>{pols.map((p) => <option key={p.id} value={p.id}>{p.name} ({p.term_year})</option>)}</select></Field>
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
