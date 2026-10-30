"use client";
import { Alert, api, ApiError, Field, RequireRole, ROLE_LABEL, useAuth, type Experience, type Option, type PortfolioItem, type User } from "@pulse/shared";
import { useEffect, useState } from "react";

export default function Profile() {
  const { user } = useAuth();
  const [u, setU] = useState<User | null>(null); const [provinces, setProvinces] = useState<Option[]>([]);
  const [exp, setExp] = useState<Experience[]>([]); const [port, setPort] = useState<PortfolioItem[]>([]);
  const [msg, setMsg] = useState(""); const [err, setErr] = useState<Record<string, string>>({});
  useEffect(() => {
    if (!user) return;
    api<User>("/auth/me/").then((d) => { setU(d); setExp(d.experiences ?? []); setPort(d.portfolio ?? []); });
    api<Option[]>("/catalog/provinces/", { auth: false }).then(setProvinces);
  }, [user]);
  if (!u) return <RequireRole roles={["journalist", "editor", "newsroom", "citizen", "admin"]}><p className="muted">Ачаалж байна…</p></RequireRole>;
  const set = (k: keyof User, v: any) => setU({ ...u, [k]: v });
  async function save() {
    setErr({}); setMsg("");
    try {
      await api("/auth/me/", { method: "PATCH", body: { full_name: u!.full_name, phone: u!.phone, organization: u!.organization, bio: u!.bio,
        province: u!.province || null, show_email: u!.show_email, show_phone: u!.show_phone, show_org: u!.show_org } });
      if (u!.role === "journalist") {
        await api("/profile/experiences/", { method: "PUT", body: exp.filter((e) => e.organization.trim()) });
        await api("/profile/portfolio/", { method: "PUT", body: port.filter((p) => p.title.trim()).map((p) => ({ ...p, year: p.year || null })) });
      }
      setMsg("Профайл хадгалагдлаа.");
    } catch (x) { setErr(x instanceof ApiError ? (x.status === 400 ? x.fieldErrors : { form: x.message }) : { form: "Алдаа гарлаа." }); }
  }
  return (
    <RequireRole roles={["journalist", "editor", "newsroom", "citizen", "admin"]}>
      <h1>Миний профайл</h1>
      <p className="muted">{u.email} · {ROLE_LABEL[u.role]} {u.is_verified && <span className="badge green">Баталгаажсан</span>}</p>
      {msg && <Alert tone="ok">{msg}</Alert>}{err.form && <Alert>{err.form}</Alert>}
      <div className="card">
        <div className="two">
          <Field label="Нэр" error={err.full_name}><input value={u.full_name} onChange={(e) => set("full_name", e.target.value)} /></Field>
          <Field label="Утас" error={err.phone}><input value={u.phone} onChange={(e) => set("phone", e.target.value)} /></Field>
          <Field label="Байгууллага"><input value={u.organization} onChange={(e) => set("organization", e.target.value)} /></Field>
          <Field label="Аймаг"><select value={u.province ?? ""} onChange={(e) => set("province", e.target.value ? Number(e.target.value) : null)}>
            <option value="">—</option>{provinces.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}</select></Field>
        </div>
        <Field label="Товч танилцуулга"><textarea style={{ minHeight: 100 }} value={u.bio} onChange={(e) => set("bio", e.target.value)} /></Field>
        <h3>Нийтэд харагдах мэдээлэл</h3>
        {([["show_org", "Байгууллага, туршлага"], ["show_email", "Имэйл"], ["show_phone", "Утас"]] as const).map(([k, l]) => (
          <label key={k} className="check-row"><input type="checkbox" checked={!!u[k]} onChange={(e) => set(k, e.target.checked)} /> {l}</label>))}
      </div>
      {u.role === "journalist" && (
        <>
          <div className="card"><div className="row spread"><h3>Ажлын туршлага</h3><button className="btn secondary sm" onClick={() => setExp([...exp, { organization: "", position: "", period: "" }])}>+ Нэмэх</button></div>
            {exp.map((e, i) => <div className="row" key={i}>
              <input placeholder="Байгууллага" value={e.organization} onChange={(ev) => setExp(exp.map((x, j) => j === i ? { ...x, organization: ev.target.value } : x))} />
              <input placeholder="Албан тушаал" value={e.position} onChange={(ev) => setExp(exp.map((x, j) => j === i ? { ...x, position: ev.target.value } : x))} />
              <input placeholder="2020–2024" value={e.period} onChange={(ev) => setExp(exp.map((x, j) => j === i ? { ...x, period: ev.target.value } : x))} />
              <button className="btn secondary sm" onClick={() => setExp(exp.filter((_, j) => j !== i))}>×</button></div>)}</div>
          <div className="card"><div className="row spread"><h3>Портфолио</h3><button className="btn secondary sm" onClick={() => setPort([...port, { title: "", kind: "news", year: null, url: "" }])}>+ Нэмэх</button></div>
            {port.map((p, i) => <div className="row" key={i}>
              <input placeholder="Гарчиг" value={p.title} onChange={(ev) => setPort(port.map((x, j) => j === i ? { ...x, title: ev.target.value } : x))} />
              <select value={p.kind} onChange={(ev) => setPort(port.map((x, j) => j === i ? { ...x, kind: ev.target.value } : x))}>
                {["news", "article", "photo", "video", "document"].map((k) => <option key={k}>{k}</option>)}</select>
              <input placeholder="Он" style={{ width: 80 }} value={p.year ?? ""} onChange={(ev) => setPort(port.map((x, j) => j === i ? { ...x, year: ev.target.value ? Number(ev.target.value) : null } : x))} />
              <input placeholder="Холбоос" value={p.url} onChange={(ev) => setPort(port.map((x, j) => j === i ? { ...x, url: ev.target.value } : x))} />
              <button className="btn secondary sm" onClick={() => setPort(port.filter((_, j) => j !== i))}>×</button></div>)}</div>
        </>
      )}
      <button className="btn" onClick={save}>Хадгалах</button>
      {u.role === "journalist" && <> <a className="btn secondary" href={`/journalists/${u.id}`}>Нийтийн профайл харах</a></>}
    </RequireRole>
  );
}
