"use client";
import { Alert, api, fmtDate, fmtDateTime, RequireRole, StatusBadge, TrustCard, type Content } from "@pulse/shared";
import { useParams, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";
import ContentForm from "@/components/ContentForm";

function Inner() {
  const { id } = useParams<{ id: string }>(); const sent = useSearchParams().get("sent");
  const [c, setC] = useState<Content | null>(null); const [err, setErr] = useState("");
  useEffect(() => { api<Content>(`/content/${id}/`).then(setC).catch(() => setErr("Контент олдсонгүй.")); }, [id]);
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
      {c.status === "under_review" && <Alert tone="info">Шалгалтад байна. Илгээсэн: {fmtDateTime(c.submitted_at)}</Alert>}
      {c.status === "published" && <Alert tone="ok">Нийтлэгдсэн ({fmtDate(c.published_at)}). <a href={`/news/${c.id}`}>Харах</a></Alert>}
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
