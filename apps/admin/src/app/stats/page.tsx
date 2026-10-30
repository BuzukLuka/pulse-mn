"use client";
import { Alert, api, ApiError, Field, fmtDateTime, RequireRole, Tabs, type Category, type DataSource, type Indicator, type IndicatorValue, type Option } from "@pulse/shared";
import { useCallback, useEffect, useState } from "react";

const errOf = (x: unknown) => (x instanceof ApiError ? (x.status === 400 ? x.fieldErrors : { form: x.message }) : { form: "Алдаа гарлаа." });

export default function AdminStats() {
  const [tab, setTab] = useState("sources");
  const [sources, setSources] = useState<DataSource[]>([]); const [inds, setInds] = useState<Indicator[]>([]);
  const [cats, setCats] = useState<Category[]>([]); const [provinces, setProvinces] = useState<Option[]>([]);
  const [msg, setMsg] = useState("");
  const load = useCallback(() => { api<DataSource[]>("/admin/stats/sources/").then(setSources); api<Indicator[]>("/admin/stats/indicators/").then(setInds); }, []);
  useEffect(() => { load(); api<Category[]>("/catalog/categories/", { auth: false }).then(setCats); api<Option[]>("/catalog/provinces/", { auth: false }).then(setProvinces); }, [load]);
  return (
    <RequireRole roles={["admin"]}>
      <h1>Эх сурвалж, статистик</h1>
      {msg && <Alert tone="ok">{msg}</Alert>}
      <Tabs value={tab} onChange={setTab} tabs={[["sources", "Эх сурвалж"], ["inds", "Үзүүлэлт, утга"]]} />
      {tab === "sources" && <Sources sources={sources} reload={load} say={setMsg} />}
      {tab === "inds" && <Indicators inds={inds} sources={sources} cats={cats} provinces={provinces} reload={load} say={setMsg} />}
    </RequireRole>
  );
}

function Sources({ sources, reload, say }: { sources: DataSource[]; reload: () => void; say: (s: string) => void }) {
  const [f, setF] = useState({ name: "", kind: "manual", url: "", frequency: "yearly" }); const [err, setErr] = useState<Record<string, string>>({});
  const [file, setFile] = useState<{ id: number; f: File | null } | null>(null);
  async function add() { setErr({}); try { await api("/admin/stats/sources/", { method: "POST", body: f }); setF({ ...f, name: "", url: "" }); say("Эх сурвалж нэмэгдлээ."); reload(); } catch (x) { setErr(errOf(x)); } }
  async function imp(s: DataSource) {
    setErr({});
    try {
      const fd = new FormData(); if (file?.id === s.id && file.f) fd.append("file", file.f);
      const r = await api<{ imported: number; errors: string[] }>(`/admin/stats/sources/${s.id}/import/`, { method: "POST", body: fd });
      say(`${r.imported} мөр импортлогдлоо.${r.errors?.length ? ` Алдаа: ${r.errors.slice(0, 3).join("; ")}` : ""}`); reload();
    } catch (x) { setErr(errOf(x)); reload(); }
  }
  return (
    <>
      {err.form && <Alert>{err.form}</Alert>}{err.file && <Alert>{err.file}</Alert>}
      <div className="card"><h3>Шинэ эх сурвалж</h3>
        <div className="two"><Field label="Нэр" error={err.name}><input value={f.name} onChange={(e) => setF({ ...f, name: e.target.value })} /></Field>
          <Field label="Төрөл"><select value={f.kind} onChange={(e) => setF({ ...f, kind: e.target.value })}><option value="manual">Гараар</option><option value="official">Албан ёсны (импорт)</option><option value="api_csv">CSV холбоос</option></select></Field>
          <Field label="CSV холбоос (https)" error={err.url}><input value={f.url} onChange={(e) => setF({ ...f, url: e.target.value })} /></Field>
          <Field label="Шинэчлэлт"><select value={f.frequency} onChange={(e) => setF({ ...f, frequency: e.target.value })}><option value="daily">Өдөр бүр</option><option value="monthly">Сар бүр</option><option value="quarterly">Улирал бүр</option><option value="yearly">Жил бүр</option></select></Field></div>
        <button className="btn" onClick={add}>Нэмэх</button></div>
      <div className="table-wrap"><table><thead><tr><th>Эх сурвалж</th><th>Төлөв</th><th>Сүүлд</th><th>CSV импорт</th></tr></thead><tbody>
        {sources.map((s) => (
          <tr key={s.id}><td><b>{s.name}</b><div className="muted">{s.indicator_count} үзүүлэлт · {s.url || "холбоосгүй"}</div></td>
            <td><span className={`badge ${s.status === "ok" ? "green" : s.status === "error" ? "red" : "gray"}`}>{s.status}</span>{s.last_error && <div className="error">{s.last_error}</div>}</td>
            <td>{fmtDateTime(s.last_synced_at)}</td>
            <td><input type="file" accept=".csv" onChange={(e) => setFile({ id: s.id, f: e.target.files?.[0] ?? null })} /> <button className="btn secondary sm" onClick={() => imp(s)}>{s.url && !(file?.id === s.id && file.f) ? "Холбоосоос шинэчлэх" : "Импортлох"}</button></td></tr>))}
      </tbody></table></div>
      <p className="muted">CSV баганууд: <code>indicator,province,year,value</code> (province хоосон бол улсын дүн). Алдаатай мөрийг алгасч, өмнөх зөв утгыг хэвээр үлдээнэ.</p>
    </>
  );
}

function Indicators({ inds, sources, cats, provinces, reload, say }: { inds: Indicator[]; sources: DataSource[]; cats: Category[]; provinces: Option[]; reload: () => void; say: (s: string) => void }) {
  const [f, setF] = useState({ name: "", aliases: "", unit: "", category: "", source: "" }); const [err, setErr] = useState<Record<string, string>>({});
  const [sel, setSel] = useState<Indicator | null>(null);
  async function add() {
    setErr({});
    try { await api("/admin/stats/indicators/", { method: "POST", body: { ...f, category: Number(f.category) || null, source: Number(f.source) || null } }); setF({ name: "", aliases: "", unit: "", category: "", source: "" }); say("Үзүүлэлт нэмэгдлээ."); reload(); }
    catch (x) { setErr(errOf(x)); }
  }
  const s = (k: keyof typeof f) => (e: { target: { value: string } }) => setF({ ...f, [k]: e.target.value });
  return (
    <>
      <div className="card"><h3>Шинэ үзүүлэлт</h3>{err.form && <Alert>{err.form}</Alert>}
        <div className="two"><Field label="Нэр" error={err.name}><input value={f.name} onChange={s("name")} /></Field>
          <Field label="Нэгж" error={err.unit}><input value={f.unit} onChange={s("unit")} placeholder="хүн, толгой, %…" /></Field>
          <Field label="Салбар" error={err.category}><select value={f.category} onChange={s("category")}><option value="">—</option>{cats.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}</select></Field>
          <Field label="Эх сурвалж" error={err.source}><select value={f.source} onChange={s("source")}><option value="">—</option>{sources.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}</select></Field></div>
        <Field label="Мэдээнээс таних өөр нэрс (таслалаар)"><input value={f.aliases} onChange={s("aliases")} /></Field>
        <button className="btn" onClick={add}>Нэмэх</button></div>
      <div className="table-wrap"><table><thead><tr><th>Үзүүлэлт</th><th>Нэгж</th><th>Эх сурвалж</th><th /></tr></thead><tbody>
        {inds.map((i) => <tr key={i.id}><td><b>{i.name}</b><div className="muted">{i.category_name}</div></td><td>{i.unit}</td><td>{i.source_name}</td><td><button className="btn secondary sm" onClick={() => setSel(i)}>Утга, түүх</button></td></tr>)}</tbody></table></div>
      {sel && <Values ind={sel} provinces={provinces} onClose={() => setSel(null)} say={say} />}
    </>
  );
}

function Values({ ind, provinces, onClose, say }: { ind: Indicator; provinces: Option[]; onClose: () => void; say: (s: string) => void }) {
  const [vals, setVals] = useState<IndicatorValue[]>([]); const [f, setF] = useState({ province: "", year: String(new Date().getFullYear()), value: "", reason: "" });
  const [err, setErr] = useState("");
  const load = useCallback(() => api<IndicatorValue[]>(`/admin/stats/indicators/${ind.id}/values/`).then(setVals), [ind.id]);
  useEffect(() => { load(); }, [load]);
  async function save() {
    setErr("");
    try { await api(`/admin/stats/indicators/${ind.id}/values/`, { method: "POST", body: f }); say("Утга хадгалагдлаа (өмнөх утга түүхэд үлдсэн)."); setF({ ...f, value: "", reason: "" }); load(); }
    catch (x) { setErr(x instanceof ApiError ? (x.status === 400 ? Object.values(x.fieldErrors).join(" ") : x.message) : "Алдаа гарлаа."); }
  }
  async function restore(hid: number) {
    const reason = window.prompt("Сэргээх шалтгаан:"); if (!reason) return;
    try { await api(`/admin/stats/history/${hid}/restore/`, { method: "POST", body: { reason } }); say("Өмнөх утга сэргээгдлээ."); load(); } catch { setErr("Сэргээж чадсангүй."); }
  }
  return (
    <div className="modal-bg" onClick={onClose}><div className="modal" style={{ maxWidth: 760, maxHeight: "90vh", overflow: "auto" }} onClick={(e) => e.stopPropagation()}>
      <h2 style={{ marginTop: 0 }}>{ind.name} <small className="muted">({ind.unit})</small></h2>{err && <Alert>{err}</Alert>}
      <div className="two">
        <Field label="Аймаг"><select value={f.province} onChange={(e) => setF({ ...f, province: e.target.value })}><option value="">Улсын дүн</option>{provinces.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}</select></Field>
        <Field label="Он"><input value={f.year} onChange={(e) => setF({ ...f, year: e.target.value })} /></Field>
        <Field label="Утга"><input value={f.value} onChange={(e) => setF({ ...f, value: e.target.value })} /></Field>
        <Field label="Шалтгаан (заавал)"><input value={f.reason} onChange={(e) => setF({ ...f, reason: e.target.value })} /></Field></div>
      <button className="btn" onClick={save}>Хадгалах</button>
      <div className="table-wrap" style={{ marginTop: 12 }}><table><thead><tr><th>Аймаг</th><th>Он</th><th>Утга</th><th>Түүх</th></tr></thead><tbody>
        {vals.map((v) => <tr key={v.id}><td>{v.province_name ?? "Улс"}</td><td>{v.year}</td><td><b>{v.value}</b></td>
          <td>{v.history.slice(0, 4).map((h) => <div key={h.id} className="muted">{h.old_value ?? "—"} → {h.new_value} · {h.reason} {h.old_value !== null && <button className="btn secondary sm" onClick={() => restore(h.id)}>Сэргээх</button>}</div>)}</td></tr>)}</tbody></table></div>
      <button className="btn secondary" style={{ marginTop: 12 }} onClick={onClose}>Хаах</button>
    </div></div>
  );
}
