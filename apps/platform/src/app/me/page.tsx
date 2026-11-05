"use client";
import {
  api, COMPLAINT_KINDS, COMPLAINT_STATUS, fmtDate, RequireRole, useAuth, type Complaint, type Notification, type Paginated,
} from "@pulse/shared";
import { useEffect, useState } from "react";

const TONE: Record<string, string> = { open: "amber", resolved: "green", dismissed: "gray" };
const LINKS: [string, string, string][] = [["/", "📰", "Мэдээ"], ["/world", "🌍", "Дэлхийд"], ["/stats", "📊", "Статистик"], ["/pledges", "🎯", "Амлалт"]];

/** Иргэний хэсэг: гомдлын явц, мэдэгдэл, хурдан холбоос. */
export default function CitizenHome() {
  const { user } = useAuth();
  const [complaints, setComplaints] = useState<Complaint[]>([]); const [notes, setNotes] = useState<Notification[]>([]);
  useEffect(() => {
    if (!user) return;
    api<Paginated<Complaint>>("/complaints/").then((d) => setComplaints(d.results)).catch(() => {});
    api<Paginated<Notification>>("/notifications/").then((d) => setNotes(d.results)).catch(() => {});
  }, [user]);
  const count = (st: string) => complaints.filter((c) => c.status === st).length;
  const kind = (k: string) => COMPLAINT_KINDS.find(([x]) => x === k)?.[1] ?? k;
  return (
    <RequireRole roles={["citizen"]}><div className="dash">
      <div className="page-head"><h1>Сайн байна уу, {user?.full_name || "иргэн"}</h1><a className="btn secondary" href="/profile">Профайл</a></div>
      <div className="kpis">
        <div className="card kpi-card"><div className="muted">Гомдол</div><div className="stat">{complaints.length}</div></div>
        <div className="card kpi-card"><div className="muted">Шийдвэрлэгдэж буй</div><div className="stat">{count("open")}</div></div>
        <div className="card kpi-card"><div className="muted">Шийдвэрлэсэн</div><div className="stat">{count("resolved")}</div></div>
        <div className="card kpi-card"><div className="muted">Шинэ мэдэгдэл</div><div className="stat">{notes.filter((n) => !n.is_read).length}</div></div>
      </div>
      <div className="g-3">
        <div className="card span-2">
          <h3>Миний гомдол</h3>
          {complaints.length === 0 && <p className="muted">Гомдол алга. Мэдээн дээрх «Гомдол / санал» товчоор илгээнэ.</p>}
          {complaints.map((c) => (
            <div key={c.id} className="list-row">
              <div><b>{kind(c.kind)}</b> <span className="muted">· {c.target_type} #{c.target_id} · {fmtDate(c.created_at)}</span>
                <div className="muted">{c.text.slice(0, 120)}</div>{c.resolution && <div>↳ {c.resolution}</div>}</div>
              <span className={`badge ${TONE[c.status]}`}>{COMPLAINT_STATUS[c.status]}</span>
            </div>
          ))}
        </div>
        <div className="card">
          <h3>Мэдэгдэл</h3>
          {notes.length === 0 && <p className="muted">Мэдэгдэл алга.</p>}
          {notes.slice(0, 6).map((n) => (
            <div key={n.id} className="list-row" style={{ opacity: n.is_read ? 0.6 : 1 }}>
              <div><b>{n.title}</b><div className="muted">{fmtDate(n.created_at)}</div></div>
            </div>
          ))}
          <a href="/notifications">Бүгд →</a>
        </div>
      </div>
      <div className="g-4" style={{ marginTop: 12 }}>
        {LINKS.map(([href, ico, label]) => <a key={href} href={href} className="card"><span style={{ fontSize: 20 }}>{ico}</span> <b>{label}</b></a>)}
      </div>
    </div></RequireRole>
  );
}
