"use client";
import { api, fmtDateTime, fmtNum, LineChart, qs, Tabs, type Category, type Indicator, type Option } from "@pulse/shared";
import { useEffect, useState } from "react";

type Series = { indicator: Indicator; series: { year: number; value: number }[] };
type Cmp = { indicator: Indicator; rows: { province: string; year: number; value: number }[] };

/** Статистикийн самбар: албан ёсны үзүүлэлт, динамик, аймгуудын харьцуулалт. */
export default function Stats() {
  const [tab, setTab] = useState("overview");
  const [provinces, setProvinces] = useState<Option[]>([]); const [cats, setCats] = useState<Category[]>([]);
  const [province, setProvince] = useState(""); const [category, setCategory] = useState("");
  const [list, setList] = useState<Indicator[]>([]); const [sel, setSel] = useState<Indicator | null>(null);
  const [series, setSeries] = useState<Series | null>(null); const [cmp, setCmp] = useState<Cmp | null>(null);
  const [err, setErr] = useState("");

  useEffect(() => {
    api<Option[]>("/catalog/provinces/", { auth: false }).then(setProvinces).catch(() => {});
    api<Category[]>("/catalog/categories/", { auth: false }).then(setCats).catch(() => {});
  }, []);
  useEffect(() => {
    api<Indicator[]>(`/stats/indicators/${qs({ province, category })}`, { auth: false })
      .then((d) => { setList(d); setErr(""); setSel((s) => d.find((x) => x.id === s?.id) ?? d[0] ?? null); })
      .catch(() => setErr("Статистик ачаалж чадсангүй."));
  }, [province, category]);
  useEffect(() => {
    if (!sel) { setSeries(null); setCmp(null); return; }
    api<Series>(`/stats/indicators/${sel.id}/series/${qs({ province })}`, { auth: false }).then(setSeries).catch(() => setSeries(null));
    api<Cmp>(`/stats/compare/?indicator=${sel.id}`, { auth: false }).then(setCmp).catch(() => setCmp(null));
  }, [sel, province]);

  const max = Math.max(1, ...(cmp?.rows.map((r) => r.value) ?? [1]));
  return (
    <>
      <h1>Статистикийн самбар</h1>
      <p className="muted">Зөвхөн албан ёсны эх сурвалжаас бүртгэсэн үзүүлэлт. Мэдээн дэх тоог энэ өгөгдлөөр автоматаар тулгадаг.</p>
      <div className="card row">
        <select value={province} onChange={(e) => setProvince(e.target.value)}><option value="">Улсын дүн</option>{provinces.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}</select>
        <select value={category} onChange={(e) => setCategory(e.target.value)}><option value="">Бүх салбар</option>{cats.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}</select>
      </div>
      {err && <div className="alert error">{err}</div>}
      {list.length === 0 && !err && <div className="alert info">Сонгосон шүүлтүүрт өгөгдөл алга. Өөр аймаг/салбар сонгоно уу.</div>}
      <div className="grid">
        {list.map((i) => (
          <button key={i.id} className="card kpi" style={{ textAlign: "left", cursor: "pointer", outline: sel?.id === i.id ? "2px solid var(--brand)" : "none" }} onClick={() => setSel(i)}>
            <span className="muted">{i.name}</span>
            <span className="stat">{fmtNum(i.value)} <small className="muted">{i.unit}</small></span>
            <span className={i.change_pct === null || i.change_pct === undefined ? "muted" : i.change_pct >= 0 ? "up" : "down"}>
              {i.change_pct === null || i.change_pct === undefined ? "өмнөх жилгүй" : `${i.change_pct >= 0 ? "▲" : "▼"} ${Math.abs(i.change_pct)}%`} · {i.year}
            </span>
            <small className="muted">{i.source_name} · шинэчлэгдсэн {fmtDateTime(i.updated_at)}</small>
          </button>
        ))}
      </div>
      {sel && (
        <>
          <h2>{sel.name}</h2>
          <Tabs tabs={[["overview", "Динамик"], ["compare", "Аймгуудын харьцуулалт"]]} value={tab} onChange={setTab} />
          {tab === "overview" && <div className="card">{series && <LineChart points={series.series} unit={sel.unit} />}<p className="muted">Эх сурвалж: {sel.source_name} · {sel.frequency}</p></div>}
          {tab === "compare" && (
            <div className="card">
              {cmp?.rows.length ? cmp.rows.map((r) => (
                <div key={r.province} className="check-row"><span style={{ width: 110 }}>{r.province}</span>
                  <div className="bar" style={{ flex: 1 }}><span className="seg blue" style={{ width: `${(r.value / max) * 100}%` }} /></div>
                  <b style={{ width: 120, textAlign: "right" }}>{fmtNum(r.value)}</b></div>
              )) : <p className="muted">Харьцуулах аймгийн өгөгдөл алга.</p>}
              {cmp?.rows[0] && <p className="muted">Нэгж: {sel.unit} · Он: {cmp.rows[0].year} (бүх аймаг ижил нэгж, ижил хугацаатай)</p>}
            </div>
          )}
        </>
      )}
    </>
  );
}
