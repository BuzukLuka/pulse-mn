"use client";
import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from "react";
import { api, session, type Session } from "./api";
import type { Role, User } from "./types";

interface AuthCtx {
  user: User | null; ready: boolean;
  login(email: string, password: string): Promise<User>;
  register(data: Record<string, string>): Promise<User>;
  logout(): void;
}
const Ctx = createContext<AuthCtx>(null as unknown as AuthCtx);
export const useAuth = () => useContext(Ctx);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const s = session.get();
    if (!s) { setReady(true); return; }
    api<User>("/auth/me/").then(setUser).catch(() => session.set(null)).finally(() => setReady(true));
  }, []);

  const finish = useCallback((s: Session) => { session.set(s); setUser(s.user); return s.user; }, []);
  const login = useCallback(async (email: string, password: string) =>
    finish(await api<Session>("/auth/login/", { method: "POST", body: { email, password }, auth: false })), [finish]);
  const register = useCallback(async (data: Record<string, string>) =>
    finish(await api<Session>("/auth/register/", { method: "POST", body: data, auth: false })), [finish]);
  const logout = useCallback(() => { session.set(null); setUser(null); }, []);

  return <Ctx.Provider value={{ user, ready, login, register, logout }}>{children}</Ctx.Provider>;
}

/** Үүргээр хамгаалагдсан хуудас (T023). Эрхгүй бол "Хандах эрхгүй" мессеж. */
export function RequireRole({ roles, children, loginHref = "/login" }:
  { roles: Role[]; children: ReactNode; loginHref?: string }) {
  const { user, ready } = useAuth();
  if (!ready) return <p className="muted">Ачаалж байна…</p>;
  if (!user) return <div className="card"><p>Энэ хуудсыг үзэхийн тулд нэвтэрнэ үү.</p><a className="btn" href={loginHref}>Нэвтрэх</a></div>;
  if (!roles.includes(user.role)) return <div className="card error">Хандах эрхгүй. Таны үүрэг: {user.role}.</div>;
  return <>{children}</>;
}
