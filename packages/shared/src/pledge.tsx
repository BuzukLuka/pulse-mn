"use client";
import { fmtDate } from "./labels";
import { progressColor } from "./map";

/** Явцын мөр (0–100%). */
export function Progress({ value }: { value: number }) {
  return <div className="prog" role="img" aria-label={`Явц ${value}%`}><span style={{ width: `${Math.min(100, value)}%`, background: progressColor(value) }} /></div>;
}

/** Хугацааны шугам: бүртгэсэн өдөр → өнөөдөр → эцсийн хугацаа. */
export function DeadlineLine({ start, deadline, progress }: { start?: string; deadline: string | null; progress: number }) {
  if (!deadline) return <small className="muted">Хэрэгжих хугацаа тогтоогоогүй</small>;
  const a = new Date(start ?? Date.now()).getTime(), b = new Date(deadline).getTime(), now = Date.now();
  const pct = (t: number) => Math.max(0, Math.min(100, ((t - a) / Math.max(1, b - a)) * 100));
  const timePct = pct(now); const late = now > b && progress < 100; const behind = !late && progress + 10 < timePct;
  return (
    <div>
      <div className="tl">
        <div className="line" /><div className="done" style={{ width: `${progress}%` }} />
        <div className="tick" style={{ left: 0 }} /><div className="tick" style={{ left: "calc(100% - 2px)" }} />
        <div className="tick today" style={{ left: `${timePct}%` }} title="Өнөөдөр" />
        <span className="lbl l" style={{ left: 0 }}>{start ? fmtDate(start) : ""}</span>
        <span className="lbl r" style={{ left: "100%" }}>{fmtDate(deadline)}</span>
      </div>
      <small className={late || behind ? "" : "muted"} style={late || behind ? { color: "#b91c1c" } : undefined}>
        {late ? "⚠ Хугацаа хэтэрсэн" : behind ? `⚠ Хоцорч байна: хугацааны ${Math.round(timePct)}% өнгөрсөн, явц ${progress}%`
          : `Хугацааны ${Math.round(timePct)}% өнгөрсөн · явц ${progress}%`}
      </small>
    </div>
  );
}
