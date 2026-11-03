"use client";
import { AuthProvider, initials, Shell, useAuth } from "@pulse/shared";
import type { ReactNode } from "react";

function Frame({ children }: { children: ReactNode }) {
  const { user, logout } = useAuth();
  const nav = user?.role === "admin"
    ? [{ href: "/", label: "◎  Самбар" }, { href: "/users", label: "👥  Хэрэглэгч, эрх" }, { href: "/content", label: "📰  Контент хяналт" }, { href: "/pledges", label: "🎯  Амлалт" }, { href: "/stats", label: "📊  Статистик" }, { href: "/complaints", label: "💬  Гомдол" }, { href: "/payments", label: "💳  Төлбөр" }, { href: "/backup", label: "💾  Нөөцлөлт" }, { href: "/audit", label: "🧾  Аудит лог" }]
    : [];
  if (!user) return <Shell brand="Админ" nav={[]} footer={false}>{children}</Shell>;
  return (
    <Shell variant="app" brand="Админ" nav={nav} right={<>
      <div className="row" style={{ gap: 10 }}><span className="avatar sm">{initials(user.full_name || user.email)}</span><span className="muted">{user.email}</span></div>
      <button className="btn secondary sm" onClick={logout}>Гарах</button>
    </>}>
      {children}
    </Shell>
  );
}
export default function Providers({ children }: { children: ReactNode }) {
  return <AuthProvider><Frame>{children}</Frame></AuthProvider>;
}
