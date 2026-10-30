"use client";
import { AuthProvider } from "@pulse/shared";
import type { ReactNode } from "react";
import AppShell from "./AppShell";

export default function Providers({ children }: { children: ReactNode }) {
  return <AuthProvider><AppShell>{children}</AppShell></AuthProvider>;
}
