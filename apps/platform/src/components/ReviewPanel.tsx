"use client";
import {
  Alert, api, ApiError, fmtDate, PERSONAL_DATA, RequireRole, StatusBadge, Tabs, TrustCard, type Content, type Correction, type Role, type Verification,
} from "@pulse/shared";
import { useParams } from "next/navigation";
import FeatureControl from "@/components/FeatureControl";
import { useEffect, useMemo, useState } from "react";

const DECISIONS = [["approve", "Зөвшөөрөх (нийтлэх)", "ok"], ["return", "Засварт буцаах", "secondary"], ["reject", "Татгалзах", "danger"]] as const;

/** Үгийн түвшний энгийн diff (LCS) — шинэ/устсан хэсгийг тодруулна. */
function diffWords(a: string, b: string) {
  const x = a.split(/(\s+)/), y = b.split(/(\s+)/);
  const m = x.length, n = y.length;
  const dp = Array.from({ length: m + 1 }, () => new Array(n + 1).fill(0));
  for (let i = m - 1; i >= 0; i--) for (let j = n - 1; j >= 0; j--) dp[i][j] = x[i] === y[j] ? dp[i + 1][j + 1] + 1 : Math.max(dp[i + 1][j], dp[i][j + 1]);
  const out: { t: string; k: "eq" | "add" | "del" }[] = [];
  let i = 0, j = 0;
  while (i < m && j < n) {
    if (x[i] === y[j]) { out.push({ t: x[i], k: "eq" }); i++; j++; }
    else if (dp[i + 1][j] >= dp[i][j + 1]) out.push({ t: x[i++], k: "del" });
    else out.push({ t: y[j++], k: "add" });
  }
  while (i < m) out.push({ t: x[i++], k: "del" });
  while (j < n) out.push({ t: y[j++], k: "add" });
  return out;
}

/** Мэдээ шалгаж шийдвэр гаргах дэлгэц — Pulse.mn-ийн редактор (base="/review") болон
 *  баталгаажсан редакц (base="/newsroom/content") хоёулаа ашиглана. */
export default function ReviewPanel({ base, back, roles, who }: { base: string; back: string; roles: Role[]; who: string }) {
  const { id } = useParams<{ id: string }>();
  const [c, setC] = useState<Content | null>(null); const [err, setErr] = useState("");
  const [tab, setTab] = useState("content");
  const [decision, setDecision] = useState<string>("return"); const [reason, setReason] = useState("");
  const [checks, setChecks] = useState<Record<string, boolean>>({});
  const [busy, setBusy] = useState(false); const [aiBusy, setAiBusy] = useState(false); const [done, setDone] = useState("");
  const load = () => api<Content>(`${base}/${id}/`).then((d) => { setC(d); setChecks(d.review_checklist ?? {}); }).catch(() => setErr("Контент олдсонгүй."));
  useEffect(() => { load(); /* eslint-disable-next-line */ }, [id]);

  async function aiCheck() {
    setAiBusy(true); setErr("");
    try { const r = await api<Verification>(`${base}/${id}/ai-check/`, { method: "POST" }); setC((x) => (x ? { ...x, verification: { ...r, editor_verified: false } } : x)); }
    catch { setErr("AI шалгалт амжилтгүй."); } finally { setAiBusy(false); }
  }
  async function submit() {
    setBusy(true); setErr(""); setDone("");
    try {
      await api(`${base}/${id}/decide/`, { method: "POST", body: { decision, reason, checklist: checks } });
      setDone("Шийдвэр хадгалагдлаа. Сэтгүүлчид мэдэгдэл илгээгдлээ."); load();
    } catch (x) {
      setErr(x instanceof ApiError && x.status === 422 ? x.message : x instanceof ApiError ? x.message : "Алдаа гарлаа.");
    } finally { setBusy(false); }
  }
  const diff = useMemo(() => {
    const v = c?.versions ?? [];
    return v.length >= 2 ? diffWords(v[v.length - 2].body, v[v.length - 1].body) : null;
  }, [c]);

  if (!c) return <RequireRole roles={roles}>{err ? <Alert>{err}</Alert> : <p className="muted">Ачаалж байна…</p>}</RequireRole>;
  const open = c.status === "under_review" && (c.can_decide ?? true);
  const comp = c.compliance ?? {};
  const dups = c.duplicates ?? [];
  const mismatch = c.verification?.checks.find((k) => k.key === "claims")?.items?.filter((i) => i.mismatch) ?? [];
  return (
    <RequireRole roles={roles}>
      <a href={back}>← Жагсаалт</a>
      <div className="row spread" style={{ marginTop: 8 }}><h1>{c.title}</h1><StatusBadge status={c.status} /></div>
      <p className="muted">{c.author_name} · {c.province_name}{c.district_name ? ` / ${c.district_name}` : ""} · {c.category_name} · {c.content_type} · Огноо: {fmtDate(c.event_date)} · Лиценз: {c.license} · {c.copyright_declared ? "Эрхийн мэдэгдэл ✓" : "Эрхийн мэдэгдэлгүй"}</p>
      <Tabs value={tab} onChange={setTab} tabs={[["content", "Агуулга"], ["trust", `Pulse Trust${dups.length ? ` (${dups.length} төстэй)` : ""}`], ["versions", `Хувилбар (${c.versions?.length ?? 0})`]]} />

      {tab === "content" && (
        <>
          <div className="card prose">{c.body}</div>
          <div className="card"><b>Эх сурвалж:</b> {c.source}</div>
          <div className="card"><h3>⚖️ Сэтгүүлчийн хууль ёсны мэдэгдэл</h3>
            <div>{comp.facts_verified ? "✓" : "✕"} Баримт шалгасан · {comp.no_defamation ? "✓" : "✕"} Гүтгэлэггүй</div>
            <div>Хувь хүний мэдээлэл: {PERSONAL_DATA.find(([k]) => k === comp.personal_data)?.[1] ?? "—"}</div>
            {comp.minors_involved && <div>Хүүхэд оролцсон · {comp.minors_protected ? "нууцалсан ✓" : "нууцлаагүй ✕"}</div>}
            {(comp.sponsored || comp.political_ad) && <div className="error">📢 {comp.political_ad ? "Улс төрийн сурталчилгаа" : "Ивээн тэтгэсэн"} · {comp.sponsor_name}</div>}
            {comp.conflict_of_interest && <div>Ашиг сонирхол: {comp.conflict_of_interest}</div>}</div>
          {c.pledge_items && c.pledge_items.length > 0 && <div className="card"><h3>Холбосон амлалт</h3>{c.pledge_items.map((p) => <div key={p.id}>{p.politician}: {p.text}</div>)}</div>}
          <div className="card">
            <h3>Медиа</h3>
            {c.media.length === 0 && <p className="muted">Хавсаргасан файл алга.</p>}
            <div className="media-grid">{c.media.filter((m) => m.kind === "image").map((m) => (
              // eslint-disable-next-line @next/next/no-img-element
              <img key={m.id} src={m.url} alt={m.original_name} />))}</div>
            {c.media.filter((m) => m.kind !== "image").map((m) => <div key={m.id}><a href={m.url} target="_blank">📎 {m.original_name}</a></div>)}
          </div>
        </>
      )}

      {tab === "trust" && (
        <>
          <div className="row spread"><p className="muted">Шалгалтыг Gemini-ээр гүнзгийрүүлж болно (утгын давхардал, тоон мэдэгдэл ялгах, AI хяналт).</p>
            <button className="btn secondary sm" onClick={aiCheck} disabled={aiBusy}>{aiBusy ? "Шалгаж байна…" : "✨ AI-аар гүнзгий шалгах"}</button></div>
          {c.verification ? <TrustCard v={c.verification} detailed /> : <Alert tone="info">Шалгалтын үр дүн алга. «AI-аар шалгах» дарна уу.</Alert>}
          {mismatch.length > 0 && (
            <div className="card"><h3>Албан ёсны статистиктай зөрүүтэй тоо</h3>
              <div className="table-wrap"><table><thead><tr><th>Үзүүлэлт</th><th>Мэдээнд</th><th>Албан ёсны</th><th>Зөрүү</th><th>Ишлэл</th></tr></thead><tbody>
                {mismatch.map((m, i) => <tr key={i}><td>{m.indicator}</td><td>{m.claimed} {m.unit}</td><td>{m.official} ({m.year}) · {m.source}</td><td className="error">{m.deviation_pct}%</td><td className="muted">“{m.quote}”</td></tr>)}</tbody></table></div></div>
          )}
          <div className="card"><h3>Давхардал / хуулбар ({dups.length})</h3>
            {dups.length ? dups.map((d: any) => <Alert key={d.id}>{who === "pulse" ? <a href={`/editor/${d.id}`}>#{d.id} {d.title}</a> : <b>#{d.id} {d.title}</b>} — {d.reason} {d.similarity ? `(${Math.round(d.similarity * 100)}%)` : ""}</Alert>) : <p className="muted">Давхардал олдсонгүй ✓</p>}</div>
          {(c.verification?.related_pledges?.length ?? 0) > 0 && <div className="card"><h3>Холбогдож болох амлалт (санал)</h3>{c.verification!.related_pledges!.map((p) => <div key={p.id}>{p.politician}: {p.text}</div>)}</div>}
          {c.ai_review && <div className="card ai"><h3>AI дүгнэлт</h3><p>{c.ai_review.summary}</p><ul>{c.ai_review.issues.map((i) => <li key={i}>{i}</li>)}</ul></div>}
        </>
      )}

      {tab === "versions" && (
        <div className="card">
          {!c.versions?.length && <p className="muted">Хувилбар алга.</p>}
          {c.versions?.map((v) => <div key={v.id} className="muted">v{v.number} · {fmtDate(v.created_at)} · {v.title}</div>)}
          {diff ? (<><h3 style={{ marginTop: 12 }}>Өмнөх хувилбартай харьцуулалт (сүүлийн засвар)</h3>
            <div className="prose">{diff.map((d, i) => <span key={i} className={d.k === "add" ? "diff-add" : d.k === "del" ? "diff-del" : ""}>{d.t}</span>)}</div></>)
            : <p className="muted">Харьцуулахад хоёр хувилбар хэрэгтэй (засвар хийгдсэний дараа гарна).</p>}
        </div>
      )}

      {done && <Alert tone="ok">{done}</Alert>}
      {err && <Alert>{err}</Alert>}
      {c.status === "under_review" && !open && <Alert tone="info">Энэ мэдээг {who === "newsroom" ? "Pulse.mn-ийн редактор" : "редакц өөрөө"} шалгаж шийдвэр гаргана.</Alert>}
      {open ? (
        <div className="card">
          <h3>Шалгах жагсаалт</h3>
          {c.checklist_items?.map((k) => (
            <label key={k.key} className="check-row"><input type="checkbox" checked={!!checks[k.key]} onChange={(e) => setChecks({ ...checks, [k.key]: e.target.checked })} /> {k.label} {k.required && <small className="muted">(заавал)</small>}</label>))}
          <h3 style={{ marginTop: 16 }}>Шийдвэр</h3>
          <div className="row">{DECISIONS.map(([k, l, tone]) => <button key={k} className={`btn sm ${decision === k ? tone : "secondary"}`} onClick={() => setDecision(k)}>{l}</button>)}</div>
          <div className="field" style={{ marginTop: 12 }}>
            <span>Шалтгаан {decision === "approve" ? "(заавал биш)" : "(заавал)"}</span>
            <textarea style={{ minHeight: 90 }} value={reason} onChange={(e) => setReason(e.target.value)} placeholder="Яг юуг засах, эсвэл яагаад татгалзсаныг тодорхой бичнэ үү" />
          </div>
          <button className="btn" onClick={submit} disabled={busy}>Шийдвэр баталгаажуулах</button>
        </div>
      ) : c.review_reason && <div className="card"><b>Шийдвэрийн шалтгаан:</b> {c.review_reason}</div>}
      {c.status === "published" && (c.can_decide ?? true) && <FeatureControl c={c} url={`${base}/${c.id}/feature/`} mode="decide" onDone={() => load()} />}
      {c.status === "published" && (c.can_decide ?? true) && <CorrectionForm base={base} id={c.id} items={c.corrections ?? []} onDone={load} />}
    </RequireRole>
  );
}

/** Нийтлэгдсэн мэдээнд залруулга / хариу тайлбар / шинэчлэл нэмэх (нийтэд ил харагдана). */
function CorrectionForm({ base, id, items, onDone }: { base: string; id: number; items: Correction[]; onDone: () => void }) {
  const [kind, setKind] = useState("correction"); const [text, setText] = useState(""); const [err, setErr] = useState("");
  async function send() {
    setErr("");
    try { await api(`${base}/${id}/corrections/`, { method: "POST", body: { kind, text } }); setText(""); onDone(); }
    catch (x) { setErr(x instanceof ApiError ? x.message : "Нийтэлж чадсангүй."); }
  }
  return (
    <div className="card">
      <h3>✏️ Залруулга, хариу тайлбар</h3>
      <p className="muted" style={{ marginTop: 0 }}>Алдаа илэрсэн, эсвэл шүүмжлэгдсэн этгээд хариу тайлбар өгөх эрхээ эдэлсэн үед мэдээн дээр ил нийтэлнэ. Сэтгүүлчид мэдэгдэл очно.</p>
      {items.map((x) => <div key={x.id} className="muted">• {x.kind_label} ({fmtDate(x.created_at)}): {x.text}</div>)}
      <div className="row" style={{ marginTop: 10 }}>
        <select value={kind} onChange={(e) => setKind(e.target.value)}><option value="correction">Залруулга</option><option value="reply">Хариу тайлбар</option><option value="update">Шинэчлэл</option></select>
        <input style={{ flex: 1, minWidth: 200 }} placeholder="Юуг залруулсан, хэн ямар тайлбар өгсөн…" value={text} onChange={(e) => setText(e.target.value)} />
        <button className="btn sm" disabled={text.trim().length < 10} onClick={send}>Нийтлэх</button>
      </div>
      {err && <Alert>{err}</Alert>}
    </div>
  );
}
