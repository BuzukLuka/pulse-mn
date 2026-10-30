"use client";
import { api, initials, Shell, useAuth } from "@pulse/shared";
import { useEffect, useState, type ReactNode } from "react";

export default function AppShell({ children }: { children: ReactNode }) {
  const { user, logout } = useAuth();
  const [unread, setUnread] = useState(0);

  useEffect(() => {
    if (!user) { setUnread(0); return; }
    api<{ count: number }>("/notifications/unread_count/").then((d) => setUnread(d.count)).catch(() => {});
  }, [user]);

  const nav = [{ href: "/", label: "Мэдээ" }, { href: "/stats", label: "Статистик" }, { href: "/pledges", label: "Амлалт" },
    { href: "/journalists", label: "Сэтгүүлчид" }];
  if (user?.role === "journalist") nav.push({ href: "/journalist", label: "Миний контент" });
  if (user?.role === "editor" || user?.role === "admin") nav.push({ href: "/editor", label: "Шалгах жагсаалт" });
  if (user) nav.push({ href: "/complaints", label: "Гомдол" });

  return (
    <Shell nav={nav} right={
      user ? (
        <>
          {user.role === "journalist" && <a className="btn sm" href="/journalist/new">+ Шинэ контент</a>}
          <a href="/notifications" aria-label="Мэдэгдэл" className="btn ghost sm" style={{ position: "relative" }}>
            🔔{unread > 0 && <span className="badge red" style={{ position: "absolute", top: -4, right: -6, padding: "0 6px" }}>{unread}</span>}
          </a>
          <a href="/profile" title={user.full_name || user.email} className="row" style={{ gap: 8 }}>
            <span className="avatar sm">{initials(user.full_name || user.email)}</span>
          </a>
          <button className="btn secondary sm" onClick={logout}>Гарах</button>
        </>
      ) : (
        <><a href="/login" className="btn ghost sm">Нэвтрэх</a><a className="btn sm" href="/register">Бүртгүүлэх</a></>
      )
    }>{children}</Shell>
  );
}
