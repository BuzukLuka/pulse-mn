"use client";
import ReviewPanel from "@/components/ReviewPanel";

/** Баталгаажсан редакц өөрийн гишүүн сэтгүүлчийн мэдээг шалгаж нийтэлнэ. */
export default function NewsroomReview() {
  return <ReviewPanel base="/newsroom/content" back="/newsroom" roles={["newsroom"]} who="newsroom" />;
}
