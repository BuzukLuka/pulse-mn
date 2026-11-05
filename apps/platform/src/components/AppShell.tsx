"use client";
import { api, initials, Shell, useAuth } from "@pulse/shared";
import { useEffect, useState, type ReactNode } from "react";

type Item = { href: string; label: string };
const L = (href: string, label: string): Item => ({ href, label });

/** Үүрэг бүрт зөвхөн өөрт хамаатай цэс. */
const NAV: Record<string, Item[]> = {
  guest: [L("/", "Мэдээ"), L("/world", "Дэлхийд"), L("/stats", "Статистик"), L("/pledges", "Амлалт"), L("/journalists", "Сэтгүүлчид"), L("/newsrooms", "Редакцууд")],
  citizen: [L("/", "Мэдээ"), L("/world", "Дэлхийд"), L("/stats", "Статистик"), L("/pledges", "Амлалт"), L("/me", "Миний хэсэг"), L("/complaints", "Гомдол")],
  journalist: [L("/journalist", "Миний контент"), L("/journalist/new", "Шинэ контент"), L("/newsrooms", "Редакцууд"), L("/", "Мэдээ"), L("/profile", "Профайл")],
  newsroom: [L("/newsroom", "Редакцын самбар"), L("/journalists", "Сэтгүүлчид"), L("/", "Мэдээ"), L("/world", "Дэлхийд"), L("/profile", "Профайл")],
  editor: [L("/editor", "Шалгах жагсаалт"), L("/", "Мэдээ"), L("/profile", "Профайл")],
  admin: [L("/editor", "Шалгах жагсаалт"), L("/", "Мэдээ"), L("/complaints", "Гомдол")],
};

export default function AppShell({ children }: { children: ReactNode }) {
  const { user, logout } = useAuth();
  const [unread, setUnread] = useState(0);

  useEffect(() => {
    if (!user) { setUnread(0); return; }
    api<{ count: number }>("/notifications/unread_count/").then((d) => setUnread(d.count)).catch(() => {});
  }, [user]);

  const nav = NAV[user?.role ?? "guest"] ?? NAV.guest;

  return (
    <Shell nav={nav} right={
      user ? (
        <>
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
