"use client";
import { useEffect, useState, type CSSProperties, type ReactNode } from "react";
import { CHECK_ICON, fmtNum, PLEDGE_LABEL, PLEDGE_TONE, STATUS_LABEL, STATUS_TONE } from "./labels";
import type { ContentStatus, PledgeStats, PledgeStatus, PublicTrust, Verification } from "./types";

export const StatusBadge = ({ status }: { status: ContentStatus }) =>
  <span className={`badge ${STATUS_TONE[status]}`}>{STATUS_LABEL[status]}</span>;

export function Field({ label, error, children }: { label: string; error?: string; children: ReactNode }) {
  return (
    <label className={`field ${error ? "has-error" : ""}`}>
      <span>{label}</span>
      {children}
      {error && <small className="err">{error}</small>}
    </label>
  );
}

export const Alert = ({ tone = "error", children }: { tone?: "error" | "ok" | "info"; children: ReactNode }) =>
  <div className={`alert ${tone}`}>{children}</div>;

/** Зүрхний цохилтын шугам — брэндийн гол дүрс. */
export const PulseMark = ({ size = 20, color = "#fff" }: { size?: number; color?: string }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
    <path d="M2 12h4l2.5-6 4 12 3-9 2 3H22" />
  </svg>
);

export const Logo = ({ tag }: { tag?: string }) => (
  <a className="brand" href="/">
    <span className="mark"><PulseMark /></span>
    <span>Pulse<span className="dotmn">.mn</span></span>
    {tag && <small>{tag}</small>}
  </a>
);

type NavItem = { href: string; label: string };

/** Одоогийн замд тохирох цэсийг тодруулна ("/" зөвхөн яг таарвал). */
function useActive(nav: NavItem[]) {
  const [path, setPath] = useState("");
  useEffect(() => setPath(window.location.pathname), []);
  const best = nav.filter((n) => n.href === "/" ? path === "/" : path === n.href || path.startsWith(n.href + "/"))
    .sort((a, b) => b.href.length - a.href.length)[0];
  return best?.href;
}

const MenuButton = ({ open, onClick }: { open: boolean; onClick: () => void }) =>
  <button className="menu-btn" aria-label={open ? "Цэс хаах" : "Цэс нээх"} aria-expanded={open} onClick={onClick}><span /></button>;

export function Shell({ brand, nav, right, children, variant = "site", footer = true }:
  { brand?: string; nav: NavItem[]; right?: ReactNode; children: ReactNode; variant?: "site" | "app"; footer?: boolean }) {
  const [open, setOpen] = useState(false);
  const active = useActive(nav);
  const links = nav.map((n) => <a key={n.href} href={n.href} className={n.href === active ? "on" : ""}>{n.label}</a>);

  if (variant === "app") {
    return (
      <div className={`app ${open ? "open" : ""}`}>
        <aside className="side">
          <Logo tag={brand} />
          <nav>{links}</nav>
          {right && <div className="right">{right}</div>}
        </aside>
        <div className="scrim" onClick={() => setOpen(false)} />
        <div className="app-main">
          <header className="app-top"><Logo tag={brand} /><MenuButton open={open} onClick={() => setOpen(!open)} /></header>
          <main className="container">{children}</main>
        </div>
      </div>
    );
  }
  return (
    <>
      <header className={`topbar ${open ? "open" : ""}`}>
        <Logo tag={brand} />
        <MenuButton open={open} onClick={() => setOpen(!open)} />
        <nav>{links}</nav>
        <div className="right">{right}</div>
      </header>
      <main className="container">{children}</main>
      {footer && <footer className="footer">
        <div className="footer-grid">
          <div>
            <Logo />
            <p style={{ maxWidth: "38ch", marginTop: 14 }}>Сэтгүүлч оруулж, редактор AI-ийн тусламжтай шалгаж баталгаажуулсан орон нутгийн мэдээ, мэдээлэл.</p>
          </div>
          <div><h4>Үзэх</h4><a href="/">Мэдээ</a><a href="/stats">Статистик</a><a href="/pledges">Амлалтын хяналт</a><a href="/journalists">Сэтгүүлчид</a></div>
          <div><h4>Оролцох</h4><a href="/register">Сэтгүүлчээр бүртгүүлэх</a><a href="/login">Нэвтрэх</a><a href="/complaints">Гомдол, санал</a></div>
          <div><h4>Эрх зүй</h4><a href="/legal/terms">Үйлчилгээний нөхцөл</a><a href="/legal/privacy">Хувийн мэдээлэл</a>
            <a href="/legal/ethics">Ёс зүйн дүрэм</a><a href="/legal">Бүх баримт бичиг</a></div>
        </div>
        <div className="fine"><span>© {new Date().getFullYear()} Pulse.mn</span><span>Баримтад суурилсан орон нутгийн мэдээлэл</span></div>
      </footer>}
    </>
  );
}

/** Зураггүй мэдээнд ангиллаар нь өнгөт хавтас үүсгэнэ. */
const COVERS = [
  ["#e8432a", "#ff9a5a"], ["#1d5bd8", "#6aa8ff"], ["#0f7a52", "#52d6a0"], ["#6a3fd1", "#b39bff"],
  ["#a85a00", "#ffc35a"], ["#0e1220", "#3b4566"], ["#c0287a", "#ff8ac4"],
];
export function Cover({ image, seed, label, chip, trust }:
  { image?: string; seed?: string | number | null; label?: string | null; chip?: string | null; trust?: number | null }) {
  const s = String(seed ?? label ?? "");
  const [a, b] = COVERS[[...s].reduce((h, ch) => h + ch.charCodeAt(0), 0) % COVERS.length];
  return (
    <div className={`cover ${image ? "" : "gen"}`} style={image ? undefined : { background: `linear-gradient(135deg, ${a}, ${b})` }}>
      {chip && image && <span className="chip">{chip}</span>}
      {trust != null && <span className="chip trust-chip">✓ {trust}</span>}
      {image
        // eslint-disable-next-line @next/next/no-img-element
        ? <img src={image} alt="" loading="lazy" />
        : <>
            <svg viewBox="0 0 200 40" preserveAspectRatio="none" aria-hidden><path d="M0 20h60l8-14 12 28 10-22 6 8h104" fill="none" stroke="#fff" strokeWidth="2" /></svg>
            <span style={{ position: "relative" }}>{label}</span>
          </>}
    </div>
  );
}

export function Empty({ title, children, action }: { title: string; children?: ReactNode; action?: ReactNode }) {
  return (
    <div className="empty">
      <svg width="56" height="56" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden><path d="M2 12h4l2.5-6 4 12 3-9 2 3H22" /></svg>
      <h3>{title}</h3>
      {children && <p>{children}</p>}
      {action}
    </div>
  );
}

/** Нэвтрэх/бүртгүүлэх хуудасны хоёр баганат хүрээ. */
export function AuthFrame({ title, text, points, children }: { title: string; text: string; points: [string, string][]; children: ReactNode }) {
  return (
    <div className="auth">
      <div className="auth-art">
        <div><div className="eyebrow" style={{ color: "#ffb4a5" }}><span className="live" /> Pulse.mn</div><h2>{title}</h2><p>{text}</p></div>
        <ul>{points.map(([i, t]) => <li key={t}><i>{i}</i><span>{t}</span></li>)}</ul>
        <svg viewBox="0 0 300 60" fill="none" aria-hidden style={{ width: "100%" }}><path d="M0 34h90l12-26 18 48 14-36 10 14h156" stroke="#e8432a" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" /></svg>
      </div>
      {children}
    </div>
  );
}

export const initials =(name?: string | null) =>
  (name || "?").split(/\s+/).filter(Boolean).slice(0, 2).map((w) => w[0]).join("").toUpperCase();

export const PledgeBadge = ({ status }: { status: PledgeStatus }) =>
  <span className={`badge ${PLEDGE_TONE[status]}`}>{PLEDGE_LABEL[status]}</span>;

/** Амлалтын биелэлтийн хувь — олон өнгийн зурвас + тайлбар. */
export function PledgeBar({ stats }: { stats: PledgeStats }) {
  const order: PledgeStatus[] = ["fulfilled", "in_progress", "not_fulfilled"];
  return (
    <div>
      <div className="bar" role="img" aria-label="Амлалтын биелэлт">
        {order.map((k) => stats.percent[k] ? <span key={k} className={`seg ${PLEDGE_TONE[k]}`} style={{ width: `${stats.percent[k]}%` }} /> : null)}
      </div>
      <div className="row muted" style={{ gap: 12, marginTop: 4 }}>
        {order.map((k) => <span key={k}><i className={`dot ${PLEDGE_TONE[k]}`} /> {PLEDGE_LABEL[k]} {stats.percent[k] ?? "—"}%</span>)}
        <span><i className="dot gray" /> Мэдээлэл дутуу: {stats.counts.insufficient}</span>
      </div>
    </div>
  );
}

/** Pulse Trust — шалгалтын үр дүн. detailed=true бол редактор/сэтгүүлчид бүх дэлгэрэнгүйг үзүүлнэ. */
export function TrustCard({ v, pub, detailed }: { v?: Verification | null; pub?: PublicTrust; detailed?: boolean }) {
  const score = v?.score ?? pub?.score ?? null;
  const level = v?.level ?? pub?.level ?? "medium";
  const verified = v?.editor_verified ?? pub?.editor_verified;
  const checks = (v?.checks ?? pub?.checks ?? []) as { key?: string; label: string; status: keyof typeof CHECK_ICON; detail?: string; items?: any[] }[];
  if (score === null && !checks.length) return null;
  return (
    <div className="card trust">
      <div className="row spread">
        <div className="row">
          <div className={`score ${level}`} style={{ "--p": score ?? 0 } as CSSProperties}>{score ?? "—"}</div>
          <div><b>Pulse Trust</b><div className="muted">{verified ? "Редактор баталгаажуулсан ✓" : "Урьдчилсан шалгалт"}{(v?.ai_used ?? pub?.ai_used) ? " · Gemini AI ашигласан" : ""}</div></div>
        </div>
        {verified && <span className="badge green">Баталгаажсан</span>}
      </div>
      <ul className="checks">
        {checks.map((c) => (
          <li key={c.label} className={c.status}>
            <span className="ico">{CHECK_ICON[c.status]}</span>
            <div><b>{c.label}</b>{detailed && c.detail && <div className="muted">{c.detail}</div>}</div>
          </li>
        ))}
      </ul>
      {pub && pub.claims.length > 0 && (
        <div className="table-wrap"><table><thead><tr><th>Үзүүлэлт</th><th>Мэдээнд</th><th>Албан ёсны</th><th>Эх сурвалж</th></tr></thead>
          <tbody>{pub.claims.map((c, i) => (
            <tr key={i}><td>{c.indicator}</td><td>{fmtNum(c.claimed)} {c.unit}</td>
              <td>{fmtNum(c.official)} ({c.year}) {c.mismatch && <span className="badge amber">зөрүүтэй</span>}</td><td>{c.source}</td></tr>))}
          </tbody></table></div>
      )}
      <small className="muted">AI-ийн шалгалт нь туслах мэдээлэл. Эцсийн шийдвэрийг редактор гаргадаг.</small>
    </div>
  );
}

/** Энгийн шугаман график (SVG, гадны сан ашиглаагүй). */
export function LineChart({ points, unit }: { points: { year: number; value: number }[]; unit?: string }) {
  if (points.length < 2) return <p className="muted">График зурахад дор хаяж 2 жилийн утга хэрэгтэй.</p>;
  const W = 560, H = 200, P = 36;
  const xs = points.map((p) => p.year), ys = points.map((p) => p.value);
  const x0 = Math.min(...xs), x1 = Math.max(...xs), y0 = Math.min(...ys), y1 = Math.max(...ys);
  const sx = (x: number) => P + ((x - x0) / (x1 - x0 || 1)) * (W - 2 * P);
  const sy = (y: number) => H - P - ((y - y0) / (y1 - y0 || 1)) * (H - 2 * P);
  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="chart" role="img" aria-label={`Динамик ${unit ?? ""}`}>
      <polyline fill="none" stroke="var(--brand)" strokeWidth="2.5" points={points.map((p) => `${sx(p.year)},${sy(p.value)}`).join(" ")} />
      {points.map((p) => (
        <g key={p.year}>
          <circle cx={sx(p.year)} cy={sy(p.value)} r="4" fill="var(--brand)" />
          <text x={sx(p.year)} y={H - 10} textAnchor="middle" fontSize="11" fill="var(--muted)">{p.year}</text>
          <text x={sx(p.year)} y={sy(p.value) - 9} textAnchor="middle" fontSize="11" fill="var(--text)">{fmtNum(p.value)}</text>
        </g>
      ))}
    </svg>
  );
}

export function Tabs({ tabs, value, onChange }: { tabs: [string, string][]; value: string; onChange: (v: string) => void }) {
  return <div className="tabs">{tabs.map(([k, l]) => <button key={k} className={k === value ? "on" : ""} onClick={() => onChange(k)}>{l}</button>)}</div>;
}
