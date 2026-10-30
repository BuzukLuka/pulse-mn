"use client";
import { ApiError, Alert, AuthFrame, Field, useAuth } from "@pulse/shared";
import { useState, type FormEvent } from "react";

const ROLES: [string, string, string][] = [["journalist", "✍️", "Сэтгүүлч"], ["newsroom", "🏢", "Редакци"], ["citizen", "🙋", "Иргэн"]];

export default function Register() {
  const { register } = useAuth();
  const [f, setF] = useState({ email: "", password: "", full_name: "", phone: "", organization: "", role: "journalist" });
  const [errs, setErrs] = useState<Record<string, string>>({}); const [busy, setBusy] = useState(false);
  const set = (k: string) => (e: { target: { value: string } }) => setF({ ...f, [k]: e.target.value });
  async function submit(e: FormEvent) {
    e.preventDefault(); setBusy(true); setErrs({});
    try { await register(f); window.location.href = f.role === "journalist" ? "/journalist" : "/"; }
    catch (x) { setErrs(x instanceof ApiError ? x.fieldErrors : { form: "Бүртгүүлж чадсангүй." }); }
    finally { setBusy(false); }
  }
  return (
    <AuthFrame title="Орон нутгийн дуу хоолой бол." text="Өөрийн аймаг, сумын болж буй үйл явдлыг баримттайгаар олон нийтэд хүргэ."
      points={[["🗺️", "21 аймаг, бүх сумын мэдээ"], ["🛡️", "Pulse Trust — баримт шалгах AI давхарга"], ["📈", "Албан ёсны статистиктай тулгана"]]}>
      <form onSubmit={submit}>
        <h1>Бүртгүүлэх</h1>
        <p className="muted" style={{ marginTop: 0, marginBottom: 24 }}>Бүртгэлтэй юу? <a href="/login">Нэвтрэх</a></p>
        {errs.form && <Alert>{errs.form}</Alert>}
        <div className="field" role="group" aria-label="Үүрэг">
          <span>Би…</span>
          <div className="pill-row">
            {ROLES.map(([k, i, l]) => <button type="button" key={k} aria-pressed={f.role === k} className={`pill ${f.role === k ? "on" : ""}`} onClick={() => setF({ ...f, role: k })}>{i} {l}</button>)}
          </div>
          {errs.role && <small className="err">{errs.role}</small>}
        </div>
        <Field label="Овог нэр" error={errs.full_name}><input value={f.full_name} autoComplete="name" onChange={set("full_name")} /></Field>
        <Field label="Имэйл" error={errs.email}><input type="email" required autoComplete="email" value={f.email} onChange={set("email")} /></Field>
        <Field label="Нууц үг (8+ тэмдэгт)" error={errs.password}><input type="password" required autoComplete="new-password" value={f.password} onChange={set("password")} /></Field>
        <div className="two">
          <Field label="Утас" error={errs.phone}><input value={f.phone} autoComplete="tel" onChange={set("phone")} /></Field>
          <Field label="Байгууллага" error={errs.organization}><input value={f.organization} onChange={set("organization")} /></Field>
        </div>
        <button className="btn lg" disabled={busy}>{busy ? "Бүртгэж байна…" : "Бүртгүүлэх →"}</button>
      </form>
    </AuthFrame>
  );
}
