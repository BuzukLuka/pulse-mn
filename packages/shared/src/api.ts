import type { User } from "./types";

export const API_URL = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1").replace(/\/$/, "");
const KEY = "pulse_session";

export interface Session { access: string; refresh: string; user: User }

export class ApiError extends Error {
  constructor(public status: number, public data: any) {
    super(typeof data?.detail === "string" ? data.detail : `HTTP ${status}`);
  }
  /** DRF-ийн талбар тус бүрийн алдаа: {title: ["..."]} → {title: "..."} */
  get fieldErrors(): Record<string, string> {
    const out: Record<string, string> = {};
    if (this.data && typeof this.data === "object") {
      for (const [k, v] of Object.entries(this.data)) {
        if (k !== "detail") out[k] = Array.isArray(v) ? String(v[0]) : String(v);
      }
    }
    return out;
  }
}

export const session = {
  get(): Session | null {
    if (typeof window === "undefined") return null;
    try { return JSON.parse(localStorage.getItem(KEY) ?? "null"); } catch { return null; }
  },
  set(s: Session | null) {
    if (typeof window === "undefined") return;
    s ? localStorage.setItem(KEY, JSON.stringify(s)) : localStorage.removeItem(KEY);
  },
};

async function refreshAccess(): Promise<string | null> {
  const s = session.get();
  if (!s) return null;
  const r = await fetch(`${API_URL}/auth/refresh/`, {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh: s.refresh }),
  });
  if (!r.ok) { session.set(null); return null; }
  const d = await r.json();
  session.set({ ...s, access: d.access, refresh: d.refresh ?? s.refresh });
  return d.access;
}

export async function api<T = any>(path: string, opts: { method?: string; body?: unknown; auth?: boolean } = {}): Promise<T> {
  const { method = "GET", body, auth = true } = opts;
  const isForm = typeof FormData !== "undefined" && body instanceof FormData;
  const send = (token?: string | null) =>
    fetch(`${API_URL}${path}`, {
      method,
      headers: {
        ...(isForm || body === undefined ? {} : { "Content-Type": "application/json" }),
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: body === undefined ? undefined : isForm ? (body as FormData) : JSON.stringify(body),
    });
  let res = await send(auth ? session.get()?.access : null);
  if (res.status === 401 && auth && session.get()) {
    const t = await refreshAccess();
    if (t) res = await send(t);
  }
  if (res.status === 204) return undefined as T;
  const data = await res.json().catch(() => null);
  if (!res.ok) throw new ApiError(res.status, data);
  return data as T;
}

export const qs = (p: Record<string, string | number | undefined | null>) => {
  const u = new URLSearchParams();
  Object.entries(p).forEach(([k, v]) => v !== undefined && v !== null && v !== "" && u.set(k, String(v)));
  const s = u.toString();
  return s ? `?${s}` : "";
};

/** Файл татах (backup гэх мэт) — Authorization толгойтой. */
export async function download(path: string, filename: string) {
  const token = session.get()?.access;
  const r = await fetch(`${API_URL}${path}`, { headers: token ? { Authorization: `Bearer ${token}` } : {} });
  if (!r.ok) throw new ApiError(r.status, await r.json().catch(() => null));
  const url = URL.createObjectURL(await r.blob());
  const el = document.createElement("a"); el.href = url; el.download = filename; el.click();
  URL.revokeObjectURL(url);
}
