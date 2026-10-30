import "@pulse/shared/styles.css";
import type { Metadata, Viewport } from "next";
import { Manrope, Unbounded } from "next/font/google";
import type { ReactNode } from "react";
import Providers from "@/components/Providers";

const body = Manrope({ subsets: ["latin", "cyrillic"], variable: "--font-manrope", display: "swap" });
const display = Unbounded({ subsets: ["latin", "cyrillic"], variable: "--font-unbounded", display: "swap" });

export const metadata: Metadata = { title: "Pulse.mn — Админ самбар", robots: { index: false, follow: false } };
export const viewport: Viewport = { width: "device-width", initialScale: 1, themeColor: "#0e1220" };

export default function RootLayout({ children }: { children: ReactNode }) {
  return <html lang="mn" className={`${body.variable} ${display.variable}`}><body><Providers>{children}</Providers></body></html>;
}
