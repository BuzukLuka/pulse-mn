"use client";
import ReviewPanel from "@/components/ReviewPanel";

export default function EditorReview() {
  return <ReviewPanel base="/review" back="/editor" roles={["editor", "admin"]} who="pulse" />;
}
