"use client";
import { Alert, ApiError, AuthFrame, Field, useAuth } from "@pulse/shared";
import { useState, type FormEvent } from "react";

export default function Login() {
  const { login, logout } = useAuth();
  const [email, setEmail] = useState(""); const [password, setPassword] = useState(""); const [err, setErr] = useState("");
  async function submit(e: FormEvent) {
    e.preventDefault(); setErr("");
    try {
      const u = await login(email, password);
      if (u.role !== "admin") { logout(); setErr("Энэ самбарт зөвхөн администратор нэвтэрнэ."); return; }
      window.location.href = "/";
    } catch (x) { setErr(x instanceof ApiError && x.status === 401 ? "Имэйл эсвэл нууц үг буруу." : "Нэвтэрч чадсангүй."); }
  }
  return (
    <AuthFrame title="Удирдлагын самбар" text="Хэрэглэгч, эрх, контент, амлалт, статистик болон аудитын бүртгэлийг нэг дороос удирдана."
      points={[["👥", "Эрх, үүрэг удирдах"], ["🧾", "Бүх үйлдлийн аудит лог"], ["💾", "Нөөцлөлт, сэргээлт"]]}>
      <form onSubmit={submit}>
        <h1>Админ нэвтрэлт</h1>
        <p className="muted" style={{ marginTop: 0, marginBottom: 24 }}>Зөвхөн администратор эрхтэй хэрэглэгч.</p>
        {err && <Alert>{err}</Alert>}
        <Field label="Имэйл"><input type="email" required autoComplete="email" value={email} onChange={(e) => setEmail(e.target.value)} /></Field>
        <Field label="Нууц үг"><input type="password" required autoComplete="current-password" value={password} onChange={(e) => setPassword(e.target.value)} /></Field>
        <button className="btn lg">Нэвтрэх →</button>
      </form>
    </AuthFrame>
  );
}
