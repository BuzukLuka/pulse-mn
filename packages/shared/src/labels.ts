import type { CheckStatus, ContentStatus, PledgeStatus, Role } from "./types";

export const STATUS_LABEL: Record<ContentStatus, string> = {
  draft: "Ноорог", under_review: "Хянагдаж буй", changes_requested: "Засвар шаардлагатай",
  published: "Нийтлэгдсэн", rejected: "Татгалзсан", hidden: "Түр нуусан",
};
export const STATUS_TONE: Record<ContentStatus, string> = {
  draft: "gray", under_review: "blue", changes_requested: "amber",
  published: "green", rejected: "red", hidden: "gray",
};
export const ROLE_LABEL: Record<Role, string> = {
  journalist: "Сэтгүүлч", editor: "Редактор", newsroom: "Редакци / байгууллага",
  citizen: "Иргэн", admin: "Администратор",
};
export const VERDICT_LABEL = { ok: "Хэвийн", needs_attention: "Анхаарах зүйлтэй", risky: "Эрсдэлтэй" } as const;
/** Бүх огноо, цагийг Улаанбаатарын цагаар (UTC+8), «2026.11.19 14:05» хэлбэрээр. */
export const TZ = "Asia/Ulaanbaatar";
const parts = (s: string, time: boolean) => {
  const d = /^\d{4}-\d{2}-\d{2}$/.test(s) ? new Date(`${s}T12:00:00+08:00`) : new Date(s);
  if (isNaN(d.getTime())) return null;
  const o = Object.fromEntries(new Intl.DateTimeFormat("en-GB", { timeZone: TZ, year: "numeric", month: "2-digit", day: "2-digit",
    ...(time ? { hour: "2-digit", minute: "2-digit", hour12: false } : {}) }).formatToParts(d).map((p) => [p.type, p.value]));
  return `${o.year}.${o.month}.${o.day}${time ? ` ${o.hour === "24" ? "00" : o.hour}:${o.minute}` : ""}`;
};
export const fmtDate = (s?: string | null) => (s ? parts(s, false) ?? "—" : "—");
export const fmtDateTime = (s?: string | null) => (s ? parts(s, true) ?? "—" : "—");
/** «5 минутын өмнө» маягийн харьцангуй хугацаа. */
export const fmtAgo = (s?: string | null) => {
  if (!s) return "—";
  const m = Math.round((Date.now() - new Date(s).getTime()) / 60000);
  if (m < 1) return "Саяхан";
  if (m < 60) return `${m} минутын өмнө`;
  if (m < 24 * 60) return `${Math.round(m / 60)} цагийн өмнө`;
  return fmtDateTime(s);
};

export const PLEDGE_LABEL: Record<PledgeStatus, string> = {
  fulfilled: "Биелсэн", in_progress: "Хэрэгжиж байгаа", not_fulfilled: "Биелээгүй", insufficient: "Мэдээлэл дутуу",
};
export const PLEDGE_TONE: Record<PledgeStatus, string> = {
  fulfilled: "green", in_progress: "blue", not_fulfilled: "red", insufficient: "gray",
};
export const CHECK_ICON: Record<CheckStatus, string> = { ok: "✓", warn: "!", fail: "✕", info: "i" };
export const CONTENT_TYPES: [string, string][] = [
  ["news", "Мэдээ"], ["article", "Нийтлэл"], ["photo", "Зураг"], ["video", "Видео"], ["document", "Баримт бичиг"],
];
export const LICENSES: [string, string][] = [
  ["attribution", "Эх сурвалж дурдан чөлөөтэй ашиглах"], ["platform_only", "Зөвхөн Pulse.mn дээр нийтлэх"],
  ["permission", "Зөвшөөрөлтэйгээр ашиглах"],
];
export const COMPLAINT_KINDS: [string, string][] = [
  ["wrong", "Буруу мэдээлэл"], ["duplicate", "Хуулбар"], ["copyright", "Зохиогчийн эрх"],
  ["privacy", "Хувийн мэдээлэл"], ["defamation", "Гүтгэлэг, нэр төр"], ["minor", "Хүүхдийн эрх"],
  ["reply", "Хариу тайлбар өгөх хүсэлт"], ["other", "Бусад"],
];
export const LEGAL_BASES: [string, string][] = [
  ["court_order", "Шүүхийн шийдвэр"], ["privacy", "Хувийн мэдээлэл хамгаалах"], ["copyright", "Зохиогчийн эрх"],
  ["defamation", "Гүтгэлэг, нэр төр"], ["minor", "Хүүхдийн эрх"], ["election", "Сонгуулийн хууль"],
  ["ethics", "Ёс зүйн зөрчил"], ["other", "Бусад"],
];
export const PERSONAL_DATA: [string, string][] = [
  ["none", "Хувь хүний мэдээлэл агуулаагүй"], ["consent", "Холбогдох хүний зөвшөөрөлтэй"],
  ["public_interest", "Олон нийтийн ашиг сонирхолд (албан тушаалтан, нийтийн үйл ажиллагаа)"],
];
export const COMPLAINT_STATUS: Record<string, string> = { open: "Нээлттэй", resolved: "Шийдвэрлэсэн", dismissed: "Хүлээн аваагүй" };
export const fmtNum = (n: number | string | null | undefined) =>
  n === null || n === undefined ? "—" : new Intl.NumberFormat("mn-MN", { maximumFractionDigits: 2 }).format(Number(n));
export const MEMBERSHIP_TONE: Record<string, string> = { pending: "amber", active: "green", rejected: "red", left: "gray" };
export const PURCHASE_TONE: Record<string, string> = { pending: "amber", paid: "green", cancelled: "gray", refunded: "red" };
export const fmtMoney = (n: number) => `${new Intl.NumberFormat("mn-MN").format(n)}₮`;
