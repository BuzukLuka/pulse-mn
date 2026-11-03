"use client";
import { ApiError, Alert, AuthFrame, Field, useAuth } from "@pulse/shared";
import { useState, type FormEvent, type ReactNode } from "react";

const ROLES: [string, string, string][] = [["journalist", "✍️", "Сэтгүүлч"], ["newsroom", "🏢", "Редакци"], ["citizen", "🙋", "Иргэн"]];

export default function Register() {
  const { register } = useAuth();
  const [f, setF] = useState({ email: "", password: "", full_name: "", phone: "", organization: "", role: "journalist",
    press_card_no: "", legal_name: "", registry_no: "", responsible_editor: "" });
  const [ok, setOk] = useState({ accept_terms: false, accept_privacy: false, accept_ethics: false });
  const [errs, setErrs] = useState<Record<string, string>>({}); const [busy, setBusy] = useState(false);
  const set = (k: string) => (e: { target: { value: string } }) => setF({ ...f, [k]: e.target.value });
  const tick = (k: keyof typeof ok) => (e: { target: { checked: boolean } }) => setOk({ ...ok, [k]: e.target.checked });
  async function submit(e: FormEvent) {
    e.preventDefault(); setBusy(true); setErrs({});
    try {
      await register({ ...f, ...ok } as unknown as Record<string, string>);
      window.location.href = f.role === "journalist" ? "/journalist" : f.role === "newsroom" ? "/newsroom" : "/";
    } catch (x) { setErrs(x instanceof ApiError ? x.fieldErrors : { form: "Бүртгүүлж чадсангүй." }); }
    finally { setBusy(false); }
  }
  const Consent = ({ k, children }: { k: keyof typeof ok; children: ReactNode }) => (
    <>
      <label className="check-row consent"><input type="checkbox" checked={ok[k]} onChange={tick(k)} /> <span>{children}</span></label>
      {errs[k] && <small className="err">{errs[k]}</small>}
    </>
  );
  return (
    <AuthFrame title="Орон нутгийн дуу хоолой бол." text="Өөрийн аймаг, сумын болж буй үйл явдлыг баримттайгаар олон нийтэд хүргэ."
      points={[["🗺️", "21 аймаг, бүх сумын мэдээ"], ["🛡️", "Pulse Trust — баримт шалгах AI давхарга"], ["⚖️", "Хууль, ёс зүйн шаардлагыг маягт дээр нь тусгасан"]]}>
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
        <Field label={f.role === "newsroom" ? "Холбоо барих хүний нэр" : "Овог нэр"} error={errs.full_name}><input value={f.full_name} autoComplete="name" onChange={set("full_name")} /></Field>
        <Field label="Имэйл" error={errs.email}><input type="email" required autoComplete="email" value={f.email} onChange={set("email")} /></Field>
        <Field label="Нууц үг (8+ тэмдэгт)" error={errs.password}><input type="password" required autoComplete="new-password" value={f.password} onChange={set("password")} /></Field>
        <div className="two">
          <Field label="Утас" error={errs.phone}><input value={f.phone} autoComplete="tel" onChange={set("phone")} /></Field>
          {f.role !== "newsroom" && <Field label="Байгууллага" error={errs.organization}><input value={f.organization} onChange={set("organization")} /></Field>}
        </div>
        {f.role === "journalist" && (
          <Field label="Сэтгүүлчийн үнэмлэхийн дугаар (баталгаажуулалтад)" error={errs.press_card_no}><input value={f.press_card_no} onChange={set("press_card_no")} placeholder="заавал биш — дараа нь профайлаас оруулж болно" /></Field>
        )}
        {f.role === "newsroom" && (
          <div className="card" style={{ boxShadow: "none" }}>
            <b>Хуулийн этгээдийн мэдээлэл</b>
            <p className="muted" style={{ marginTop: 4 }}>Хэвлэн нийтэлсэн агуулгад хуулийн этгээд, хариуцлагатай эрхлэгч хариуцлага хүлээнэ.</p>
            <Field label="Хуулийн этгээдийн нэр" error={errs.legal_name}><input value={f.legal_name} onChange={set("legal_name")} placeholder="Жишээ: Говийн дуу ХХК" /></Field>
            <div className="two">
              <Field label="Регистрийн дугаар (7 орон)" error={errs.registry_no}><input value={f.registry_no} inputMode="numeric" maxLength={7} onChange={set("registry_no")} /></Field>
              <Field label="Хариуцлагатай эрхлэгч" error={errs.responsible_editor}><input value={f.responsible_editor} onChange={set("responsible_editor")} /></Field>
            </div>
          </div>
        )}
        <Consent k="accept_terms"><a href="/legal/terms" target="_blank">Үйлчилгээний нөхцөл</a>-ийг уншиж, зөвшөөрч байна.</Consent>
        <Consent k="accept_privacy">Хувийн мэдээллээ <a href="/legal/privacy" target="_blank">бодлогын</a> дагуу боловсруулахыг зөвшөөрч байна.</Consent>
        {f.role === "journalist" && <Consent k="accept_ethics"><a href="/legal/ethics" target="_blank">Сэтгүүлчийн ёс зүйн дүрэм</a>, <a href="/legal/journalists" target="_blank">хууль эрх зүйн шаардлага</a>-ыг мөрдөнө.</Consent>}
        <button className="btn lg" disabled={busy} style={{ marginTop: 12 }}>{busy ? "Бүртгэж байна…" : "Бүртгүүлэх →"}</button>
      </form>
    </AuthFrame>
  );
}
