"use client";
import { RequireRole } from "@pulse/shared";
import ContentForm from "@/components/ContentForm";

export default function NewContent() {
  return (
    <RequireRole roles={["journalist"]}>
      <h1>Шинэ контент</h1>
      <ContentForm onDone={(c) => { window.location.href = `/journalist/${c.id}?sent=1`; }} />
    </RequireRole>
  );
}
