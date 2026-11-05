"use client";
import { api, fmtDateTime, RequireRole, StatusBadge, Tabs, useAuth, type Content, type Paginated } from "@pulse/shared";
import { useEffect, useState } from "react";

const TABS: [string, string][] = [["under_review", "Шалгах"], ["changes_requested", "Засварт"], ["rejected", "Татгалзсан"], ["published", "Нийтлэгдсэн"]];

export default function Queue() {
  const { user } = useAuth();
  const [tab, setTab] = useState("under_review"); const [items, setItems] = useState<Content[]>([]); const [loaded, setLoaded] = useState(false);
  useEffect(() => { setLoaded(false); api<Paginated<Content>>(`/review/?status=${tab}`).then((d) => setItems(d.results)).finally(() => setLoaded(true)); }, [tab]);
  return (
    <RequireRole roles={["editor", "admin"]}><div className="dash">
      <div className="page-head">
        <div><div className="eyebrow">{user?.newsroom_org_name ? `«${user.newsroom_org_name}» редакц` : "Pulse.mn"}</div><h1>Шалгах жагсаалт</h1></div>
      </div>
      <Tabs tabs={TABS} value={tab} onChange={setTab} />
      {loaded && items.length === 0 && <p className="muted">Хоосон.</p>}
      {items.length > 0 && (
        <div className="table-wrap"><table>
          <thead><tr><th>Гарчиг</th><th>Сэтгүүлч</th><th>Аймаг</th><th>Ирсэн</th><th>Төлөв</th></tr></thead>
          <tbody>{items.map((c) => (
            <tr key={c.id} onClick={() => { window.location.href = `/editor/${c.id}`; }} style={{ cursor: "pointer" }}>
              <td><a href={`/editor/${c.id}`}><b>{c.title}</b></a></td><td>{c.author_name}</td><td>{c.province_name}</td>
              <td>{fmtDateTime(c.submitted_at)}</td><td><StatusBadge status={c.status} /></td></tr>
          ))}</tbody>
        </table></div>
      )}
    </div></RequireRole>
  );
}
