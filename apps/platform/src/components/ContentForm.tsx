"use client";
import {
  api, ApiError, Alert, Field, TrustCard, CONTENT_TYPES, LICENSES, PERSONAL_DATA, type AiSuggestion, type Category, type Compliance, type Content,
  type District, type Membership, type Option, type PersonCard, type Pledge, type Verification, useAuth,
} from "@pulse/shared";
import { useEffect, useState, type FormEvent } from "react";

/** UC-01: контент маягт → медиа upload → AI шошго санал → батлах → шалгалтад илгээх */
export default function ContentForm({ initial, onDone }: { initial?: Content; onDone: (c: Content) => void }) {
  const [id, setId] = useState<number | undefined>(initial?.id);
  const [f, setF] = useState({
    title: initial?.title ?? "", body: initial?.body ?? "", category: String(initial?.category ?? ""),
    province: String(initial?.province ?? ""), district: String(initial?.district ?? ""),
    event_date: initial?.event_date ?? "", source: initial?.source ?? "",
    content_type: initial?.content_type ?? "news", event_time: initial?.event_time?.slice(0, 5) ?? "",
    location_detail: initial?.location_detail ?? "", license: initial?.license ?? "attribution",
    newsroom: String(initial?.newsroom ?? ""), price: String(initial?.price ?? 0),
  });
  const { user } = useAuth();
  const [newsrooms, setNewsrooms] = useState<PersonCard[]>([]); const [mineIds, setMineIds] = useState<Set<number>>(new Set());
  const [copyright, setCopyright] = useState(!!initial?.copyright_declared);
  const [comp, setComp] = useState<Compliance>(initial?.compliance ?? {});
  const tick = (k: keyof Compliance) => (e: { target: { checked: boolean } }) => setComp({ ...comp, [k]: e.target.checked });
  const [pledgeIds, setPledgeIds] = useState<number[]>(initial?.pledges ?? []);
  const [allPledges, setAllPledges] = useState<Pledge[]>([]);
  const [trust, setTrust] = useState<Verification | null>(initial?.verification ?? null);
  const [tags, setTags] = useState<string[]>(initial?.tags ?? []);
  const [media, setMedia] = useState(initial?.media ?? []);
  const [files, setFiles] = useState<File[]>([]);
  const [provinces, setProvinces] = useState<Option[]>([]); const [districts, setDistricts] = useState<District[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [errs, setErrs] = useState<Record<string, string>>({}); const [msg, setMsg] = useState("");
  const [busy, setBusy] = useState(false); const [ai, setAi] = useState<AiSuggestion | null>(null); const [newTag, setNewTag] = useState("");

  useEffect(() => {
    api<Option[]>("/catalog/provinces/", { auth: false }).then(setProvinces);
    api<Category[]>("/catalog/categories/", { auth: false }).then(setCategories);
    api<Pledge[]>("/pledges/", { auth: false }).then(setAllPledges).catch(() => {});
    api<PersonCard[]>("/newsrooms/", { auth: false }).then(setNewsrooms).catch(() => {});
    api<Membership[]>("/memberships/").then((m) => setMineIds(new Set(m.filter((x) => x.status === "active").map((x) => x.newsroom.id)))).catch(() => {});
  }, []);
  useEffect(() => {
    if (!f.province) { setDistricts([]); return; }
    api<District[]>(`/catalog/districts/?province=${f.province}`, { auth: false }).then(setDistricts);
  }, [f.province]);

  const set = (k: keyof typeof f) => (e: { target: { value: string } }) => setF({ ...f, [k]: e.target.value });
  const payload = () => ({
    title: f.title, body: f.body, tags, source: f.source, event_date: f.event_date || null,
    category: f.category ? Number(f.category) : null, province: f.province ? Number(f.province) : null,
    district: f.district ? Number(f.district) : null,
    content_type: f.content_type, event_time: f.event_time || null, location_detail: f.location_detail,
    license: f.license, copyright_declared: copyright, pledges: pledgeIds,
    newsroom: f.newsroom ? Number(f.newsroom) : null, price: Math.max(0, Number(f.price) || 0), compliance: comp,
  });

  async function suggest() {
    setMsg(""); setErrs({});
    try {
      const r = await api<AiSuggestion>("/content/suggest-tags/", { method: "POST", body: { title: f.title, body: f.body, content_id: id } });
      setAi(r);
    } catch (x) { setErrs(x instanceof ApiError ? x.fieldErrors : {}); }
  }
  function applyAi() {
    if (!ai) return;
    setF({ ...f, category: ai.category_id ? String(ai.category_id) : f.category });
    setTags(Array.from(new Set([...tags, ...ai.tags])));
    setAi(null); setMsg("Санал болгосон шошгыг баталлаа. Хүсвэл засаж болно.");
  }

  async function save(submit: boolean) {
    setBusy(true); setErrs({}); setMsg("");
    try {
      let saved = id ? await api<Content>(`/content/${id}/`, { method: "PATCH", body: payload() })
                     : await api<Content>("/content/", { method: "POST", body: payload() });
      setId(saved.id);
      if (files.length) {
        const fd = new FormData(); files.forEach((x) => fd.append("file", x));
        const up = await api<typeof media>(`/content/${saved.id}/media/`, { method: "POST", body: fd });
        setMedia([...media, ...up]); setFiles([]);
      }
      if (submit) saved = await api<Content>(`/content/${saved.id}/submit/`, { method: "POST" });
      else setMsg("Ноорог хадгалагдлаа.");
      if (submit) onDone(saved);
    } catch (x) {
      if (x instanceof ApiError) setErrs(x.status === 400 ? x.fieldErrors : { form: x.message });
      else setErrs({ form: "Алдаа гарлаа." });
    } finally { setBusy(false); }
  }

  async function precheck() {
    setBusy(true); setErrs({}); setMsg("");
    try {
      const saved = id ? await api<Content>(`/content/${id}/`, { method: "PATCH", body: payload() })
                       : await api<Content>("/content/", { method: "POST", body: payload() });
      setId(saved.id);
      if (files.length) {
        const fd = new FormData(); files.forEach((x) => fd.append("file", x));
        const up = await api<typeof media>(`/content/${saved.id}/media/`, { method: "POST", body: fd });
        setMedia([...media, ...up]); setFiles([]);
      }
      setTrust(await api<Verification>(`/content/${saved.id}/precheck/`, { method: "POST" }));
    } catch (x) { setErrs(x instanceof ApiError ? (x.status === 400 ? x.fieldErrors : { form: x.message }) : { form: "Алдаа гарлаа." }); }
    finally { setBusy(false); }
  }

  async function removeMedia(mid: number) {
    if (!id) return;
    await api(`/content/${id}/media/${mid}/`, { method: "DELETE" });
    setMedia(media.filter((m) => m.id !== mid));
  }

  return (
    <form onSubmit={(e: FormEvent) => { e.preventDefault(); save(true); }}>
      {errs.form && <Alert>{errs.form}</Alert>}
      {errs.detail && <Alert>{errs.detail}</Alert>}
      {msg && <Alert tone="ok">{msg}</Alert>}
      <div className="card">
        <Field label="Гарчиг" error={errs.title}><input value={f.title} onChange={set("title")} /></Field>
        <Field label="Агуулга" error={errs.body}><textarea value={f.body} onChange={set("body")} /></Field>
        <div className="two">
          <Field label="Контентын төрөл" error={errs.content_type}>
            <select value={f.content_type} onChange={set("content_type")}>{CONTENT_TYPES.map(([k, l]) => <option key={k} value={k}>{l}</option>)}</select>
          </Field>
          <Field label="Үйл явдал болсон цаг" error={errs.event_time}><input type="time" value={f.event_time} onChange={set("event_time")} /></Field>
          <Field label="Аймаг" error={errs.province}>
            <select value={f.province} onChange={(e) => setF({ ...f, province: e.target.value, district: "" })}>
              <option value="">— сонгох —</option>{provinces.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
            </select>
          </Field>
          <Field label="Сум / дүүрэг" error={errs.district}>
            <select value={f.district} onChange={set("district")} disabled={!districts.length}>
              <option value="">— сонгох —</option>{districts.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
            </select>
          </Field>
          <Field label="Төрөл" error={errs.category}>
            <select value={f.category} onChange={set("category")}>
              <option value="">— сонгох —</option>{categories.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
            </select>
          </Field>
          <Field label="Үйл явдал болсон огноо" error={errs.event_date}><input type="date" value={f.event_date} onChange={set("event_date")} /></Field>
        </div>
        <Field label="Байршил (баг, хороо, газрын нэр)" error={errs.location_detail}><input value={f.location_detail} onChange={set("location_detail")} /></Field>
        <Field label="Эх сурвалж" error={errs.source}><input value={f.source} onChange={set("source")} placeholder="Жишээ: Аймгийн ХАА-н газар, албан тоот №…" /></Field>
      </div>

      <div className="card">
        <h3>Зураг / видео / баримт</h3>
        <Field label="Файл нэмэх (jpg, png, webp, mp4, mov, pdf · 50MB хүртэл)" error={errs.file}>
          <input type="file" multiple accept=".jpg,.jpeg,.png,.webp,.mp4,.mov,.pdf" onChange={(e) => setFiles(Array.from(e.target.files ?? []))} />
        </Field>
        {files.map((x) => <div className="muted" key={x.name}>📎 {x.name} (шинэ)</div>)}
        {media.map((m) => (
          <div key={m.id} className="row muted">📎 {m.original_name} <button type="button" className="btn secondary sm" onClick={() => removeMedia(m.id)}>Устгах</button></div>
        ))}
      </div>

      <div className="card">
        <h3>Редакц, худалдаа</h3>
        <div className="two">
          <Field label="Аль редакц руу илгээх вэ?" error={errs.newsroom}>
            <select value={f.newsroom} onChange={set("newsroom")}>
              <option value="">— Редакцгүй (зөвхөн Pulse.mn) —</option>
              {[...newsrooms].sort((a, b) => Number(mineIds.has(b.id)) - Number(mineIds.has(a.id))).map((n) =>
                <option key={n.id} value={n.id}>{n.name}{mineIds.has(n.id) ? " — миний редакц" : ""}{n.is_verified ? " ✓" : ""}</option>)}
            </select>
          </Field>
          <Field label="Редакцад худалдах үнэ (₮, 0 = зарахгүй)" error={errs.price}>
            <input type="number" min={0} step={1000} value={f.price} onChange={set("price")} />
          </Field>
        </div>
        <small className="muted">Редакц сонговол «Шалгалтад илгээх» дарахад тэр редакцад мэдэгдэл очиж, мэдээ нь редакцын самбарт гарна;
          редакторын шийдвэр бүрийг ч редакц мэдэж байна. Үнэ тавибал нийтлэгдсэний дараа редакцууд худалдан авч болно.</small>
      </div>

      <div className="card">
        <h3>Зохиогчийн эрх, лиценз</h3>
        <Field label="Хэрэглээний нөхцөл" error={errs.license}>
          <select value={f.license} onChange={set("license")}>{LICENSES.map(([k, l]) => <option key={k} value={k}>{l}</option>)}</select>
        </Field>
        <label className="check-row"><input type="checkbox" checked={copyright} onChange={(e) => setCopyright(e.target.checked)} />
          Энэ материал миний бүтээл, эсвэл ашиглах зөвшөөрөлтэй гэдгээ баталж байна.</label>
        {errs.copyright_declared && <small className="err">{errs.copyright_declared}</small>}
      </div>

      <div className="card">
        <h3>⚖️ Хууль, ёс зүйн мэдэгдэл (илгээхэд заавал)</h3>
        <p className="muted" style={{ marginTop: 0 }}>Үндэслэл: <a href="/legal/journalists" target="_blank">сэтгүүлчид мөрдөх шаардлага</a>. Ивээн тэтгэсэн, ашиг сонирхлын мэдэгдэл уншигчид ил харагдана.</p>
        {errs.compliance && <Alert>{errs.compliance}</Alert>}
        <label className="check-row consent"><input type="checkbox" checked={!!comp.facts_verified} onChange={tick("facts_verified")} />
          <span>Баримтыг шалгасан; санаатай худал, төөрөгдүүлсэн мэдээлэл агуулаагүй.</span></label>
        <label className="check-row consent"><input type="checkbox" checked={!!comp.no_defamation} onChange={tick("no_defamation")} />
          <span>Хэн нэгнийг гүтгэсэн, доромжилсон, үзэн ядалт өдөөсөн агуулгагүй.</span></label>
        <Field label="Хувь хүний мэдээлэл">
          <select value={comp.personal_data ?? ""} onChange={(e) => setComp({ ...comp, personal_data: e.target.value as Compliance["personal_data"] })}>
            <option value="">— сонгох —</option>{PERSONAL_DATA.map(([k, l]) => <option key={k} value={k}>{l}</option>)}</select>
        </Field>
        <label className="check-row consent"><input type="checkbox" checked={!!comp.minors_involved} onChange={tick("minors_involved")} /> <span>Мэдээнд хүүхэд (18 хүртэлх) оролцсон</span></label>
        {comp.minors_involved && <label className="check-row consent" style={{ marginLeft: 26 }}><input type="checkbox" checked={!!comp.minors_protected} onChange={tick("minors_protected")} />
          <span>Хүүхдийн нэр, нүүр, хаяг, сургуулийг нууцалсан эсвэл асран хамгаалагчийн зөвшөөрөлтэй.</span></label>}
        <div className="two">
          <label className="check-row consent"><input type="checkbox" checked={!!comp.sponsored} onChange={tick("sponsored")} /> <span>Ивээн тэтгэсэн / захиалгат материал</span></label>
          <label className="check-row consent"><input type="checkbox" checked={!!comp.political_ad} onChange={tick("political_ad")} /> <span>Улс төрийн сурталчилгаа (нам, нэр дэвшигч)</span></label>
        </div>
        {(comp.sponsored || comp.political_ad) && <Field label="Захиалагч (уншигчид харагдана)"><input value={comp.sponsor_name ?? ""} onChange={(e) => setComp({ ...comp, sponsor_name: e.target.value })} /></Field>}
        <Field label="Ашиг сонирхлын зөрчил (байвал бичнэ — уншигчид харагдана)">
          <input value={comp.conflict_of_interest ?? ""} placeholder="Жишээ: Зохиогч тус байгууллагад өмнө ажиллаж байсан" onChange={(e) => setComp({ ...comp, conflict_of_interest: e.target.value })} /></Field>
      </div>

      {allPledges.length > 0 && (
        <div className="card">
          <h3>Холбогдох амлалт (заавал биш)</h3>
          <select multiple style={{ width: "100%", minHeight: 100 }} value={pledgeIds.map(String)}
            onChange={(e) => setPledgeIds(Array.from(e.target.selectedOptions).map((o) => Number(o.value)))}>
            {allPledges.map((p) => <option key={p.id} value={p.id}>{p.politician_name}: {p.text.slice(0, 70)}</option>)}
          </select>
          <small className="muted">Ctrl/⌘ дарж олныг сонгоно. Мэдээ нийтлэгдвэл амлалтын хуудсанд нотолгоо болж холбогдоно.</small>
        </div>
      )}

      <div className="card ai">
        <div className="row spread"><h3>AI шошго (Gemini)</h3>
          <button type="button" className="btn secondary sm" onClick={suggest}>✨ Ангилал, түлхүүр үг санал болгох</button></div>
        {ai && (
          <div className="alert info">
            <div>Санал болгосон төрөл: <b>{categories.find((c) => c.id === ai.category_id)?.name ?? "—"}</b> <small>({ai.source === "gemini" ? "Gemini" : "дүрмийн"})</small></div>
            <div>{ai.tags.map((t) => <span className="tag" key={t}>#{t}</span>)}</div>
            {ai.summary && <div className="muted">Хураангуй: {ai.summary}</div>}
            <button type="button" className="btn sm" onClick={applyAi}>Батлах</button>
          </div>
        )}
        <p className="muted" style={{ marginTop: 0 }}>Шошго нь мэдээг <b>хайлт, шүүлтүүрт</b> олдуулах, <b>давхардсан мэдээ</b> илрүүлэх,
          холбогдох <b>статистик үзүүлэлт, амлалттай</b> автоматаар тулгахад ашиглагдана. AI зөвхөн санал болгоно — та батлах, засах эрхтэй.</p>
        <div>{tags.map((t) => <span className="tag" key={t}>#{t}<button type="button" onClick={() => setTags(tags.filter((x) => x !== t))}>×</button></span>)}</div>
        <div className="row">
          <input placeholder="Шошго нэмэх" value={newTag} onChange={(e) => setNewTag(e.target.value)}
            onKeyDown={(e) => { if (e.key === "Enter") { e.preventDefault(); if (newTag.trim()) { setTags([...tags, newTag.trim()]); setNewTag(""); } } }} />
        </div>
      </div>

      <div className="card ai">
        <div className="row spread"><h3>Pulse Trust · илгээхээс өмнө өөрөө шалгах</h3>
          <button type="button" className="btn secondary sm" disabled={busy} onClick={precheck}>🛡 Шалгах</button></div>
        <p className="muted">Давхардал, төстэй зураг, эх сурвалж, хувийн мэдээлэл, албан ёсны статистиктай тулгалтыг шалгана. Алдаагаа илгээхээс өмнө засвал батлагдах магадлал өснө.</p>
        {trust && <TrustCard v={trust} detailed />}
      </div>

      {user && !user.is_verified && <Alert tone="info">Баталгаажаагүй бүртгэлээр шалгалтад илгээх боломжгүй — ноорог хадгалаад, баталгаажуулалт хүснэ үү.</Alert>}
      <div className="row">
        <button type="submit" className="btn" disabled={busy || (!!user && !user.is_verified)}>Шалгалтад илгээх</button>
        <button type="button" className="btn secondary" disabled={busy} onClick={() => save(false)}>Ноорог хадгалах</button>
      </div>
    </form>
  );
}
