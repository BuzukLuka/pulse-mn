"use client";
import { api, initials, Shell, useAuth } from "@pulse/shared";
import { useEffect, useState, type ReactNode } from "react";

type Item = { href: string; label: string; children?: Item[] };
const L = (href: string, label: string, children?: Item[]): Item => ({ href, label, children });

// Мэдээний ангиллууд (catalog-ийн slug) — dropdown-оор шүүнэ
const SECTIONS = L("/", "Мэдээ", [
  L("/?c=politics", "Улс төр"), L("/?c=economy", "Эдийн засаг, санхүү"), L("/?c=infrastructure", "Дэд бүтэц"),
  L("/?c=education", "Боловсрол"), L("/?c=health", "Эрүүл мэнд"), L("/?c=environment", "Байгаль орчин"),
  L("/?c=agriculture", "Хөдөө аж ахуй"), L("/?c=population", "Хүн ам, нийгэм"), L("/", "Бүх мэдээ"),
]);
const BREAKING = L("/?fresh=24", "Шуурхай");
const DATA = L("/stats", "Мэдээлэл", [L("/stats", "Статистик"), L("/pledges", "Амлалтын хяналт"), L("/world", "Дэлхийд Монголын тухай")]);

/** Үүрэг бүрт зөвхөн өөрт хамаатай цэс. */
const NAV: Record<string, Item[]> = {
  guest: [SECTIONS, BREAKING, L("/world", "Дэлхийд"), DATA, L("/journalists", "Сэтгүүлчид", [L("/journalists", "Сэтгүүлчид"), L("/newsrooms", "Редакцууд")])],
  citizen: [SECTIONS, BREAKING, L("/world", "Дэлхийд"), DATA, L("/me", "Миний хэсэг", [L("/me", "Самбар"), L("/complaints", "Гомдол"), L("/notifications", "Мэдэгдэл"), L("/profile", "Профайл")])],
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

  const nav = (NAV[user?.role ?? "guest"] ?? NAV.guest).map((n) => n === BREAKING ? { ...n, label: "● Шуурхай" } : n);

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
