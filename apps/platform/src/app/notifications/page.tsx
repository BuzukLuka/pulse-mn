"use client";
import { api, fmtAgo, RequireRole, useAuth, type Notification, type Paginated } from "@pulse/shared";
import { useEffect, useState } from "react";

export default function Notifications() {
  const [items, setItems] = useState<Notification[]>([]); const [sel, setSel] = useState<number[]>([]);
  const load = () => api<Paginated<Notification>>("/notifications/").then((d) => setItems(d.results)).catch(() => {});
  useEffect(() => { load(); }, []);
  const read = async (id: number) => { await api(`/notifications/${id}/read/`, { method: "POST" }); load(); };
  const readMany = async (ids?: number[]) => { await api("/notifications/read-many/", { method: "POST", body: ids ? { ids } : {} }); setSel([]); load(); };
  const { user } = useAuth();
  // Мэдэгдлээс холбогдох хуудас руу: үүрэг бүрт өөр харагдац
  const link = (n: Notification) => !n.content_id ? (user?.role === "newsroom" ? "/newsroom" : null)
    : user?.role === "journalist" ? `/journalist/${n.content_id}` : user?.role === "editor" || user?.role === "admin" ? `/editor/${n.content_id}`
    : user?.role === "newsroom" ? "/newsroom" : `/news/${n.content_id}`;
  const all = items.length > 0 && sel.length === items.length;
  const toggle = (id: number) => setSel((s) => (s.includes(id) ? s.filter((x) => x !== id) : [...s, id]));
  const unread = items.filter((n) => !n.is_read).length;
  return (
    <RequireRole roles={["journalist", "editor", "admin", "newsroom", "citizen"]}>
      <h1>Мэдэгдэл</h1>
      {items.length > 0 && (
        <div className="card row spread" style={{ position: "sticky", top: "calc(var(--topbar-h) + 8px)", zIndex: 5 }}>
          <label className="check-row" style={{ margin: 0 }}>
            <input type="checkbox" checked={all} ref={(el) => { if (el) el.indeterminate = sel.length > 0 && !all; }}
              onChange={() => setSel(all ? [] : items.map((n) => n.id))} /> Бүгдийг сонгох {sel.length > 0 && <span className="muted">({sel.length} сонгосон)</span>}
          </label>
          <div className="row" style={{ gap: 6 }}>
            <button className="btn secondary sm" disabled={!sel.length} onClick={() => readMany(sel)}>Сонгосныг уншсан болгох</button>
            <button className="btn ghost sm" disabled={!unread} onClick={() => readMany()}>Бүгдийг уншсан ({unread})</button>
          </div>
        </div>
      )}
      {items.length === 0 && <p className="muted">Мэдэгдэл алга.</p>}
      {items.map((n) => (
        <div key={n.id} className="card row spread" style={{ opacity: n.is_read ? 0.6 : 1, alignItems: "flex-start" }}>
          <label className="row" style={{ gap: 12, alignItems: "flex-start", flex: 1, margin: 0 }}>
            <input type="checkbox" checked={sel.includes(n.id)} onChange={() => toggle(n.id)} style={{ marginTop: 4 }} />
            <div><b>{link(n) ? <a href={link(n)!} onClick={() => !n.is_read && read(n.id)}>{n.title}</a> : n.title}</b><div className="muted">{n.body}</div><small className="muted">{fmtAgo(n.created_at)}</small></div>
          </label>
          {!n.is_read && <button className="btn secondary sm" onClick={() => read(n.id)}>Уншсан</button>}
        </div>
      ))}
    </RequireRole>
  );
}
