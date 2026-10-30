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
export const fmtDate = (s?: string | null) => (s ? new Date(s).toLocaleDateString("mn-MN") : "—");
export const fmtDateTime = (s?: string | null) => (s ? new Date(s).toLocaleString("mn-MN") : "—");

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
  ["privacy", "Хувийн мэдээлэл"], ["other", "Бусад"],
];
export const COMPLAINT_STATUS: Record<string, string> = { open: "Нээлттэй", resolved: "Шийдвэрлэсэн", dismissed: "Хүлээн аваагүй" };
export const fmtNum = (n: number | string | null | undefined) =>
  n === null || n === undefined ? "—" : new Intl.NumberFormat("mn-MN", { maximumFractionDigits: 2 }).format(Number(n));
