"use client";
import { api, fmtDateTime, RequireRole, useAuth, type Notification, type Paginated } from "@pulse/shared";
import { useEffect, useState } from "react";

export default function Notifications() {
  const [items, setItems] = useState<Notification[]>([]);
  const load = () => api<Paginated<Notification>>("/notifications/").then((d) => setItems(d.results)).catch(() => {});
  useEffect(() => { load(); }, []);
  const read = async (id: number) => { await api(`/notifications/${id}/read/`, { method: "POST" }); load(); };
  const { user } = useAuth();
  // Мэдэгдлээс холбогдох хуудас руу: үүрэг бүрт өөр харагдац
  const link = (n: Notification) => !n.content_id ? (user?.role === "newsroom" ? "/newsroom" : null)
    : user?.role === "journalist" ? `/journalist/${n.content_id}` : user?.role === "editor" || user?.role === "admin" ? `/editor/${n.content_id}`
    : user?.role === "newsroom" ? "/newsroom" : `/news/${n.content_id}`;
  return (
    <RequireRole roles={["journalist", "editor", "admin", "newsroom", "citizen"]}>
      <h1>Мэдэгдэл</h1>
      {items.length === 0 && <p className="muted">Мэдэгдэл алга.</p>}
      {items.map((n) => (
        <div key={n.id} className="card row spread" style={{ opacity: n.is_read ? 0.6 : 1 }}>
          <div><b>{link(n) ? <a href={link(n)!} onClick={() => !n.is_read && read(n.id)}>{n.title}</a> : n.title}</b><div className="muted">{n.body}</div><small className="muted">{fmtDateTime(n.created_at)}</small></div>
          {!n.is_read && <button className="btn secondary sm" onClick={() => read(n.id)}>Уншсан</button>}
        </div>
      ))}
    </RequireRole>
  );
}
