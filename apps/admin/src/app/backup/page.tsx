"use client";
import { Alert, download, RequireRole } from "@pulse/shared";
import { useState } from "react";

export default function Backup() {
  const [msg, setMsg] = useState(""); const [err, setErr] = useState(""); const [busy, setBusy] = useState(false);
  async function run() {
    setBusy(true); setErr(""); setMsg("");
    try { await download("/admin/backup/", `pulse-backup-${new Date().toISOString().slice(0, 10)}.json`); setMsg("Нөөц хуулбар татагдлаа."); }
    catch { setErr("Нөөцлөх үед алдаа гарлаа."); } finally { setBusy(false); }
  }
  return (
    <RequireRole roles={["admin"]}>
      <h1>Нөөцлөлт ба сэргээлт</h1>
      {msg && <Alert tone="ok">{msg}</Alert>}{err && <Alert>{err}</Alert>}
      <div className="card"><h3>Нөөц хуулбар татах</h3>
        <p className="muted">Контент, амлалт, статистик, гомдол, аудит, ангилал зэргийг JSON-оор татна. Нууц үг, токен ороогүй. Мэдээний зураг/видео файл тусдаа хадгалагдана.</p>
        <button className="btn" disabled={busy} onClick={run}>{busy ? "Бэлтгэж байна…" : "⬇ Нөөцлөх"}</button></div>
      <div className="card"><h3>Сэргээх</h3>
        <p className="muted">Сэргээлт нь өгөгдлийг бүхэлд нь дарж бичдэг аюултай үйлдэл тул вэбээс биш сервер дээр гараар хийнэ:</p>
        <pre className="card" style={{ overflowX: "auto" }}>{`cd backend\npython manage.py loaddata pulse-backup-YYYY-MM-DD.json`}</pre>
        <p className="muted">Сэргээхээс өмнө одоогийн өгөгдлийг заавал нөөцөлнө. Docker ашиглаж байвал: <code>docker compose exec backend python manage.py loaddata /tmp/backup.json</code></p></div>
    </RequireRole>
  );
}
