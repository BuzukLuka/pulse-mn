import "@pulse/shared/styles.css";
import type { Metadata, Viewport } from "next";
import { Manrope, Unbounded } from "next/font/google";
import type { ReactNode } from "react";
import Providers from "@/components/Providers";

const body = Manrope({ subsets: ["latin", "cyrillic"], variable: "--font-manrope", display: "swap" });
const display = Unbounded({ subsets: ["latin", "cyrillic"], variable: "--font-unbounded", display: "swap" });

export const metadata: Metadata = {
  title: "Pulse.mn — Орон нутгийн баталгаатай мэдээлэл",
  description: "Шалгагдаж баталгаажсан орон нутгийн мэдээ, мэдээлэл",
};
export const viewport: Viewport = { width: "device-width", initialScale: 1, themeColor: "#e8432a" };

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="mn" className={`${body.variable} ${display.variable}`}>
      <body><Providers>{children}</Providers></body>
    </html>
  );
}
