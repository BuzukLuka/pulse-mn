"use client";
import { api, RequireRole, ROLE_LABEL, STATUS_LABEL, STATUS_TONE, type ContentStatus, type Role, type Stats } from "@pulse/shared";
import { useEffect, useState } from "react";

const ROLE_ICON: Record<string, string> = { journalist: "✍️", editor: "🧐", newsroom: "🏢", citizen: "🙋", admin: "🛡️" };

export default function Dashboard() {
  const [s, setS] = useState<Stats | null>(null);
  useEffect(() => { api<Stats>("/admin/stats/").then(setS).catch(() => {}); }, []);
  const pct = (v: number, t: number) => (t ? Math.round((v / t) * 100) : 0);
  return (
    <RequireRole roles={["admin"]}>
      <div className="page-head">
        <div><div className="eyebrow"><span className="live" /> Шууд төлөв</div><h1>Самбар</h1></div>
        <div className="row"><a className="btn secondary" href="/audit">Аудит лог</a><a className="btn" href="/users">Хэрэглэгч удирдах</a></div>
      </div>
      {!s && <div className="grid">{[0, 1, 2, 3].map((i) => <div key={i} className="skeleton" style={{ height: 140 }} />)}</div>}
      {s && (
        <>
          <div className="kpis">
            <div className="card kpi-card"><div className="ico">👥</div><div className="muted">Нийт хэрэглэгч</div><div className="stat">{s.users_total}</div></div>
            <div className="card kpi-card"><div className="ico">📰</div><div className="muted">Нийт контент</div><div className="stat">{s.content_total}</div></div>
            <div className="card kpi-card"><div className="ico">⏳</div><div className="muted">Шалгалт хүлээж буй</div><div className="stat">{s.content_by_status.under_review ?? 0}</div></div>
            <div className="card kpi-card"><div className="ico">✅</div><div className="muted">Нийтлэгдсэн</div><div className="stat">{s.content_by_status.published ?? 0}</div></div>
          </div>
          <div className="two" style={{ marginTop: 8 }}>
            <div className="card">
              <h3>Контент төлвөөр</h3>
              {Object.entries(s.content_by_status).map(([k, v]) => (
                <div key={k} style={{ marginTop: 14 }}>
                  <div className="row spread"><span className={`badge ${STATUS_TONE[k as ContentStatus] ?? "gray"}`}>{STATUS_LABEL[k as ContentStatus] ?? k}</span><b>{v}</b></div>
                  <div className="meter"><i style={{ width: `${pct(v, s.content_total)}%` }} /></div>
                </div>
              ))}
              {Object.keys(s.content_by_status).length === 0 && <p className="muted">Контент алга.</p>}
            </div>
            <div className="card">
              <h3>Хэрэглэгч үүргээр</h3>
              {Object.entries(s.users_by_role).map(([k, v]) => (
                <div key={k} style={{ marginTop: 14 }}>
                  <div className="row spread"><span>{ROLE_ICON[k] ?? "•"} {ROLE_LABEL[k as Role] ?? k}</span><b>{v}</b></div>
                  <div className="meter"><i style={{ width: `${pct(v, s.users_total)}%`, background: "var(--blue)" }} /></div>
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </RequireRole>
  );
}
