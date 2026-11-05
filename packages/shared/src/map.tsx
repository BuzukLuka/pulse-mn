"use client";
import { useEffect, useRef } from "react";

/** MapLibre GL (CDN-ээс ачаална) + OpenFreeMap «liberty» загвар — OSM-ийн 3D барилгатай газрын зураг.
 *  Албан ёсны кадастрын өгөгдөл нээлттэй биш тул OpenStreetMap-ийн барилгын давхаргыг ашиглана. */
const VER = "4.7.1";
const STYLE = "https://tiles.openfreemap.org/styles/liberty";
let loading: Promise<any> | null = null;

function loadLib(): Promise<any> {
  const w = window as any;
  if (w.maplibregl) return Promise.resolve(w.maplibregl);
  if (loading) return loading;
  loading = new Promise((ok, fail) => {
    const css = document.createElement("link");
    css.rel = "stylesheet"; css.href = `https://unpkg.com/maplibre-gl@${VER}/dist/maplibre-gl.css`;
    document.head.appendChild(css);
    const s = document.createElement("script");
    s.src = `https://unpkg.com/maplibre-gl@${VER}/dist/maplibre-gl.js`;
    s.onload = () => ok(w.maplibregl); s.onerror = () => { loading = null; fail(new Error("map")); };
    document.head.appendChild(s);
  });
  return loading;
}

export interface MapPoint { id: number; lat: number; lng: number; title: string; subtitle?: string; progress?: number; href?: string }

export const progressColor = (p = 0) => (p >= 100 ? "#16a34a" : p >= 50 ? "#2563eb" : p > 0 ? "#d97706" : "#9ca3af");

const esc = (s: string) => s.replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]!));

/** points — амлалтын байршлууд; onPick өгвөл газрын зураг дээр дарж байршил сонгоно (admin / иргэн). */
export function PledgeMap({ points, height = 420, onPick, picked }: {
  points: MapPoint[]; height?: number; onPick?: (lat: number, lng: number) => void; picked?: { lat: number; lng: number } | null;
}) {
  const el = useRef<HTMLDivElement>(null); const map = useRef<any>(null); const marks = useRef<any[]>([]);
  const pickRef = useRef(onPick); pickRef.current = onPick;

  useEffect(() => {
    let dead = false;
    loadLib().then((ml) => {
      if (dead || !el.current) return;
      map.current = new ml.Map({ container: el.current, style: STYLE, center: [106.917, 47.918], zoom: 11, pitch: 55, bearing: -17, attributionControl: { compact: true } });
      map.current.addControl(new ml.NavigationControl({ visualizePitch: true }), "top-right");
      map.current.on("click", (e: any) => pickRef.current?.(+e.lngLat.lat.toFixed(6), +e.lngLat.lng.toFixed(6)));
      map.current.on("load", () => draw());
    }).catch(() => { if (el.current) el.current.innerHTML = '<p class="muted" style="padding:16px">Газрын зураг ачаалсангүй.</p>'; });
    return () => { dead = true; map.current?.remove(); map.current = null; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function draw() {
    const ml = (window as any).maplibregl; const m = map.current;
    if (!ml || !m) return;
    marks.current.forEach((x) => x.remove()); marks.current = [];
    const all = [...points];
    for (const p of all) {
      const dot = document.createElement("div");
      dot.className = "map-pin"; dot.style.background = progressColor(p.progress); dot.textContent = p.progress != null ? String(p.progress) : "";
      const html = `<b>${esc(p.title)}</b>${p.subtitle ? `<div class="muted">${esc(p.subtitle)}</div>` : ""}` +
        (p.progress != null ? `<div>Явц: <b>${p.progress}%</b></div>` : "") + (p.href ? `<a href="${esc(p.href)}">Дэлгэрэнгүй →</a>` : "");
      marks.current.push(new ml.Marker({ element: dot }).setLngLat([p.lng, p.lat]).setPopup(new ml.Popup({ offset: 16 }).setHTML(html)).addTo(m));
    }
    if (picked) marks.current.push(new ml.Marker({ color: "#e11d48" }).setLngLat([picked.lng, picked.lat]).addTo(m));
    const pts = picked ? [...all, picked] : all;
    if (pts.length === 1) m.easeTo({ center: [pts[0].lng, pts[0].lat], zoom: 15.5, pitch: 60 });
    else if (pts.length > 1) {
      const b = new ml.LngLatBounds(); pts.forEach((p) => b.extend([p.lng, p.lat]));
      m.fitBounds(b, { padding: 60, maxZoom: 15.5, pitch: 55 });
    }
  }

  const key = JSON.stringify([points.map((p) => [p.id, p.lat, p.lng, p.progress]), picked]);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => { if (map.current?.loaded()) draw(); }, [key]);
  return <div ref={el} className="pledge-map" style={{ height }} />;
}
