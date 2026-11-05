"use client";
import { Alert, api, ApiError, fmtDate, fmtDateTime, RequireRole, StatusBadge, Timeline, TrustCard, type Content, type HistoryItem, type PersonCard } from "@pulse/shared";
import { useParams, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";
import ContentForm from "@/components/ContentForm";
import FeatureControl from "@/components/FeatureControl";

function Inner() {
  const { id } = useParams<{ id: string }>(); const sent = useSearchParams().get("sent");
  const [c, setC] = useState<Content | null>(null); const [err, setErr] = useState("");
  const [hist, setHist] = useState<HistoryItem[]>([]);
  const [newsrooms, setNewsrooms] = useState<PersonCard[]>([]); const [pick, setPick] = useState(""); const [sendErr, setSendErr] = useState("");
  const loadHist = () => api<HistoryItem[]>(`/content/${id}/history/`).then(setHist).catch(() => {});
  useEffect(() => {
    api<Content>(`/content/${id}/`).then(setC).catch(() => setErr("Контент олдсонгүй."));
    loadHist();
    api<PersonCard[]>("/newsrooms/", { auth: false }).then(setNewsrooms).catch(() => {});
  }, [id]); // eslint-disable-line react-hooks/exhaustive-deps
  async function sendToNewsroom() {
    setSendErr("");
    try { setC(await api<Content>(`/content/${id}/send-to-newsroom/`, { method: "POST", body: { newsroom: Number(pick) } })); loadHist(); }
    catch (x) { setSendErr(x instanceof ApiError ? x.message : "Илгээж чадсангүй."); }
  }
  if (err) return <Alert>{err}</Alert>;
  if (!c) return <p className="muted">Ачаалж байна…</p>;
  const editable = c.status === "draft" || c.status === "changes_requested";
  return (
    <>
      <a href="/journalist">← Миний контент</a>
      <div className="row spread" style={{ marginTop: 8 }}><h1>{c.title}</h1><StatusBadge status={c.status} /></div>
      {sent && <Alert tone="ok">Амжилттай илгээгдлээ. Таны контент редакторын шалгалтад орлоо.</Alert>}
      {c.status === "changes_requested" && <Alert>Редакторын тайлбар: <b>{c.review_reason}</b> — засаад дахин илгээнэ үү.</Alert>}
      {c.status === "rejected" && <Alert>Татгалзсан. Шалтгаан: <b>{c.review_reason}</b></Alert>}
      {c.status === "under_review" && <Alert tone="info">Шалгалтад байна. Илгээсэн: {fmtDateTime(c.submitted_at)} ·
        Шалгагч: <b>{c.review_by === "newsroom" ? `«${c.newsroom_name}» редакц` : "Pulse.mn редактор"}</b></Alert>}
      {c.status === "published" && <Alert tone="ok">Нийтлэгдсэн ({fmtDate(c.published_at)}). <a href={`/news/${c.id}`}>Харах</a></Alert>}
      {c.newsroom_name && <p className="muted">🏢 Редакц: <b>{c.newsroom_name}</b> — шинэ төлөв бүрийн мэдэгдэл редакцад очно.</p>}
      {!editable && !c.newsroom && (
        <div className="card"><h3>🏢 Редакцад илгээх</h3>
          <p className="muted" style={{ marginTop: 0 }}>Энэ мэдээг редакц сонгоогүй илгээсэн байна. Редакц сонговол тэдэнд мэдэгдэл очиж, самбарт нь гарна.</p>
          <div className="row"><select value={pick} onChange={(e) => setPick(e.target.value)} style={{ flex: 1, minWidth: 180 }}>
            <option value="">Редакц сонгох…</option>{newsrooms.map((n) => <option key={n.id} value={n.id}>{n.name}{n.is_verified ? " ✓" : ""}</option>)}</select>
            <button className="btn sm" disabled={!pick} onClick={sendToNewsroom}>Редакцад илгээх</button></div>
          {sendErr && <Alert>{sendErr}</Alert>}
        </div>
      )}
      {c.status === "published" && <FeatureControl c={c} url={`/content/${c.id}/feature-request/`} mode="request" onDone={setC} />}
      {hist.length > 0 && <div className="card"><h3>Төлвийн түүх</h3><Timeline items={hist} /></div>}
      {!editable && c.verification && <TrustCard v={c.verification} detailed />}
      {editable ? (
        <ContentForm initial={c} onDone={(x) => { window.location.href = `/journalist/${x.id}?sent=1`; }} />
      ) : (
        <div className="card"><div className="prose">{c.body}</div><p className="muted">Эх сурвалж: {c.source}</p></div>
      )}
    </>
  );
}
export default function Page() {
  return <RequireRole roles={["journalist"]}><Suspense><Inner /></Suspense></RequireRole>;
}
