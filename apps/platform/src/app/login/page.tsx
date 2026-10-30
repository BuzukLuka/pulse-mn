"use client";
import { ApiError, Alert, AuthFrame, Field, useAuth } from "@pulse/shared";
import { useState, type FormEvent } from "react";

export default function Login() {
  const { login } = useAuth();
  const [email, setEmail] = useState(""); const [password, setPassword] = useState("");
  const [err, setErr] = useState(""); const [busy, setBusy] = useState(false);
  async function submit(e: FormEvent) {
    e.preventDefault(); setBusy(true); setErr("");
    try {
      const u = await login(email, password);
      window.location.href = u.role === "journalist" ? "/journalist" : u.role === "editor" ? "/editor" : "/";
    } catch (x) { setErr(x instanceof ApiError && x.status === 401 ? "Имэйл эсвэл нууц үг буруу, эсвэл бүртгэл түр хаагдсан байна." : "Нэвтэрч чадсангүй."); }
    finally { setBusy(false); }
  }
  return (
    <AuthFrame title="Тавтай морил буцаад." text="Мэдээгээ оруулж, шалгалтын явцаа хянаж, уншигчидтайгаа баталгаатай мэдээллээр холбогдоорой."
      points={[["📝", "Мэдээ, зураг, видеогоо нэг дор оруулна"], ["✨", "AI ангилал, түлхүүр үг санал болгоно"], ["✓", "Редактор баримтыг тулган баталгаажуулна"]]}>
      <form onSubmit={submit}>
        <h1>Нэвтрэх</h1>
        <p className="muted" style={{ marginTop: 0, marginBottom: 24 }}>Бүртгэлгүй юу? <a href="/register">Бүртгүүлэх</a></p>
        {err && <Alert>{err}</Alert>}
        <Field label="Имэйл"><input type="email" required autoComplete="email" placeholder="name@example.mn" value={email} onChange={(e) => setEmail(e.target.value)} /></Field>
        <Field label="Нууц үг"><input type="password" required autoComplete="current-password" placeholder="••••••••" value={password} onChange={(e) => setPassword(e.target.value)} /></Field>
        <button className="btn lg" disabled={busy}>{busy ? "Нэвтэрч байна…" : "Нэвтрэх →"}</button>
      </form>
    </AuthFrame>
  );
}
