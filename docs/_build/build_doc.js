// Pulse.mn — нэгдсэн баримт бичиг (.docx) үүсгэгч.  node build_doc.js
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, ImageRun, HeadingLevel, AlignmentType,
  WidthType, ShadingType, BorderStyle, PageBreak, LevelFormat, Footer, Header, PageNumber, ExternalHyperlink,
} = require("docx");
const { FR, NFR, LR, WF, BENCH, PERF } = require("./data");

const ROOT = path.resolve(__dirname, "..", "..");
const FONT = "Arial";
const W = 9026; // A4, 1" зай
const C = { ink: "0C2430", teal: "0F6F7C", tealSoft: "E2F0F2", line: "D3CFC5", muted: "627080", head: "F4F2EE" };
const TONE = {
  "Хэрэгжсэн": "E4F2EA", "Хэсэгчлэн": "FFF3DC", "ДЕМО": "E5EEF8", "Хэрэгжээгүй": "F7E8EE", "Тэнцээгүй": "F7E8EE",
  "Өөрчлөгдсөн": "EEEBFA", "✅": "E4F2EA",
};

// ---------- туслахууд ----------
const t = (text, o = {}) => new TextRun({ text, font: FONT, ...o });
const P = (children, o = {}) => new Paragraph({ children: Array.isArray(children) ? children : [t(children)], spacing: { after: 120, line: 276 }, ...o });
const H1 = (text) => new Paragraph({ heading: HeadingLevel.HEADING_1, children: [t(text)], pageBreakBefore: true });
const H2 = (text) => new Paragraph({ heading: HeadingLevel.HEADING_2, children: [t(text)] });
const H3 = (text) => new Paragraph({ heading: HeadingLevel.HEADING_3, children: [t(text)] });
const bullet = (children) => new Paragraph({ numbering: { reference: "b", level: 0 }, children: Array.isArray(children) ? children : [t(children)], spacing: { after: 60 } });
const caption = (text) => new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 60, after: 240 }, children: [t(text, { italics: true, size: 18, color: C.muted })] });
const border = { style: BorderStyle.SINGLE, size: 4, color: C.line };
const borders = { top: border, bottom: border, left: border, right: border };

function cell(content, width, o = {}) {
  const runs = (Array.isArray(content) ? content : [content]).map((x) => (typeof x === "string" ? t(x, { size: o.size || 17, bold: o.bold, color: o.color }) : x));
  return new TableCell({
    borders, width: { size: width, type: WidthType.DXA },
    shading: o.fill ? { fill: o.fill, type: ShadingType.CLEAR, color: "auto" } : undefined,
    margins: { top: 50, bottom: 50, left: 90, right: 90 },
    children: [new Paragraph({ children: runs, alignment: o.align })],
  });
}

function table(widths, head, rows, o = {}) {
  const sum = widths.reduce((a, b) => a + b, 0);
  if (sum !== W) throw new Error("table width " + sum);
  return new Table({
    width: { size: W, type: WidthType.DXA }, columnWidths: widths,
    rows: [
      new TableRow({ tableHeader: true, children: head.map((h, i) => cell(h, widths[i], { bold: true, fill: C.tealSoft, color: C.ink, size: 17 })) }),
      ...rows.map((r) => new TableRow({ cantSplit: true, children: r.map((v, i) => {
        const fill = o.toneCol === i ? TONE[v] : (o.toneCol2 === i ? TONE[v] : undefined);
        return cell(v, widths[i], { fill, size: o.size, align: o.center && o.center.includes(i) ? AlignmentType.CENTER : undefined });
      }) })),
    ],
  });
}

function pngSize(file) {
  const b = fs.readFileSync(file);
  return { w: b.readUInt32BE(16), h: b.readUInt32BE(20) };
}
function image(file, maxW = 600, maxH = 800) {
  const { w, h } = pngSize(file);
  let s = Math.min(maxW / w, maxH / h, 1);
  if (w * s < 120) s = Math.min(maxW / w, maxH / h);
  return new Paragraph({ alignment: AlignmentType.CENTER, keepNext: true, children: [new ImageRun({ type: "png", data: fs.readFileSync(file),
    transformation: { width: Math.round(w * s), height: Math.round(h * s) } })] });
}

// ---------- тестүүд (TEST_RESULTS.md-ээс) ----------
const tests = [];
let curClass = "";
for (const line of fs.readFileSync(path.join(ROOT, "docs", "TEST_RESULTS.md"), "utf8").split(/\r?\n/)) {
  const h = line.match(/^## (\w+) — `([\w.]+)`/);
  if (h) curClass = h[1];
  const m = line.match(/^\| (TC-\d+) \| `([^`]+)` \| (.*?) \| (.*?) \|$/);
  if (m) tests.push({ id: m[1], name: m[2], cls: curClass, desc: m[3], ok: m[4].includes("✅") });
}
const passed = tests.filter((x) => x.ok).length;

// Тест бүр аль шаардлагыг хамарсныг урвуу индекс
const testReqs = {};
for (const r of [...FR, ...NFR]) for (const tc of r[r.length - 1]) (testReqs[tc] = testReqs[tc] || []).push(r[0]);
for (const r of LR) for (const tc of r[4]) (testReqs[tc] = testReqs[tc] || []).push(r[0]);

const count = (arr, idx, val) => arr.filter((r) => r[idx] === val).length;
const frOrig = FR.filter((r) => +r[0].slice(3) <= 79), frNew = FR.filter((r) => +r[0].slice(3) > 79);
const STATUSES = ["Хэрэгжсэн", "Хэсэгчлэн", "ДЕМО", "Хэрэгжээгүй"];
const covered = (arr, i) => arr.filter((r) => r[i].length > 0).length;
const pct = (a, b) => (b ? Math.round((a / b) * 1000) / 10 : 0) + "%";

const uml = JSON.parse(fs.readFileSync(path.join(__dirname, "uml", "index.json"), "utf8"));
const U = (k) => uml.find((x) => x.key === k);

// ---------- агуулга ----------
const body = [];

// Нүүр хуудас
body.push(
  new Paragraph({ spacing: { before: 2600, after: 200 }, children: [t("Pulse.mn", { size: 64, bold: true, color: C.teal })] }),
  new Paragraph({ spacing: { after: 120 }, children: [t("Системийн нэгдсэн баримт бичиг", { size: 40, bold: true, color: C.ink })] }),
  new Paragraph({ spacing: { after: 600 }, children: [t("Бенчмарк судалгаа · Системийн шаардлага · UML · Wireframe · Тест ба шаардлагын харьцуулалт", { size: 22, color: C.muted })] }),
  table([2600, 6426], ["Талбар", "Утга"], [
    ["Хувилбар", "2.0 — хэрэгжсэн платформтой тулгасан"],
    ["Огноо", "2026.11.19"],
    ["Код", "github.com/BuzukLuka/pulse-mn (main, eeb05ec)"],
    ["Ажиллаж буй хаяг", "pulse-mn-platform.vercel.app · pulse-mn-api.vercel.app"],
    ["Эх сурвалж баримтууд", "System Requirements (FR-NFR).xlsx v1.0 · docs/requirements.csv · pulse.mn.v2.feap · Wireframes.html (Claude Design) · TEST_RESULTS.md"],
  ]),
  new Paragraph({ spacing: { before: 400 }, children: [t("Энэ баримт өмнөх тусдаа баримтуудыг нэгтгэж, шаардлага бүрийг ажиллаж буй кодтой нэг бүрчлэн тулгав. Байхгүй функцийг «хэрэгжсэн» гэж бичээгүй; дутуу, ДЕМО, хэрэгжээгүйг тодорхой тэмдэглэв.", { size: 20, color: C.muted })] }),
);

// Агуулга
body.push(H1("Агуулга"));
[
  "Гүйцэтгэх хураангуй", "1. Танилцуулга", "2. Бенчмарк судалгаа", "3. Системийн шаардлага (FR, NFR, хууль эрх зүй)", "4. Өмнөх баримттай зөрүү ба засвар",
  "5. UML диаграм", "6. Wireframe ба хэрэгжсэн дэлгэц", "7. Тестийн судалгаа: шаардлагатай харьцуулалт", "8. Дүгнэлт ба зөвлөмж", "9. Хавсралт: технологи, API",
].forEach((x) => body.push(P([t(x, { size: 22 })], { spacing: { after: 100 } })));

// Гүйцэтгэх хураангуй
const implOrig = count(frOrig, 4, "Хэрэгжсэн");
const kpi = (label, value, note) => [label, value, note];
body.push(H1("Гүйцэтгэх хураангуй"));
body.push(P("Pulse.mn нь Монголын орон нутгийн мэдээг нийтлэхээс өмнө баталгаажуулж, албан ёсны статистик ба УИХ-ын гишүүдийн амлалтын хяналттай нэг дор нэгтгэсэн, ажиллаж буй (production) платформ. Энэ тайлан нь бенчмарк судалгаа, системийн шаардлага, UML загвар, wireframe болон тестийн үр дүнг нэг баримтад нэгтгэж, бүгдийг бодит кодтой тулгасан."));
body.push(table([3600, 1700, 3726], ["Үзүүлэлт", "Үр дүн", "Тайлбар"], [
  kpi("Анхны SRS-ийн шаардлага бүрэн хэрэгжсэн", `${implOrig} / 79 (${pct(implOrig, 79)})`, `Хэсэгчлэн ${count(frOrig, 4, "Хэсэгчлэн")}, ДЕМО ${count(frOrig, 4, "ДЕМО")}, хэрэгжээгүй ${count(frOrig, 4, "Хэрэгжээгүй")}`),
  kpi("Нэмэлтээр хэрэгжүүлсэн функц", `${frNew.length}`, "Редакцын урсгал, AI шалгалт, дэлхийн мэдээ, 3D газрын зураг, parliament.mn …"),
  kpi("Хууль эрх зүйн шаардлага", `${count(LR, 3, "Хэрэгжсэн")} / ${LR.length}`, "Төлбөрийн хэсэг ДЕМО"),
  kpi("Автомат тест", `${passed} / ${tests.length} тэнцсэн`, "Backend APITestCase + frontend typecheck, build"),
  kpi("Шаардлагын тестийн хамралт (FR)", `${pct(covered(FR, 6), FR.length)}`, "Тест бүр шаардлагын ID-тай холбогдсон"),
  kpi("API хурд (засварын дараа)", PERF.after.headline, PERF.after.note),
  kpi("UML / wireframe", "15 диаграм · 20 дэлгэц", "Диаграмыг кодоос үүсгэсэн; wireframe бүрийг хуудастай тулгасан"),
], { size: 17 }));
body.push(H2("Гол дүгнэлт"));
[
  "Бенчмарк: олон улсын платформууд нэг чиглэлд (эх сурвалжийн харьцуулалт, амлалт, AI баримт шалгалт, лиценз) төвлөрдөг; Монголд нийтлэхээс өмнөх баталгаажуулалт, амлалтын тасралтгүй хяналттай платформ олдсонгүй — Pulse.mn энэ хоосон зайг нөхнө.",
  `Хэрэгжилт: анхны 79 шаардлагын ${pct(implOrig, 79)} бүрэн; дутуу нь эх файлын төлбөрийн хаалт, хуваалцах товч, ажлын хуваарилалт, шүүлттэй тайлан.`,
  "Гүйцэтгэл: шалгалтаар API удаан (13–34 сек) байсныг илрүүлж, шалтгааныг (сервер Сингапурт, ДБ Вашингтонд + N+1 query) засав — " + PERF.after.headline + ".",
  "Эрсдэл: төлбөр ДЕМО (QPay, сэтгүүлчид орлого шилжүүлэх гэрээ шаардлагатай), Gemini түлхүүргүй үед AI дүрмээр ажиллана, мөрийн хөтөлбөрийн бүтэцтэй нээлттэй өгөгдөл байхгүй тул амлалтыг гараар оруулна.",
].forEach((x) => body.push(bullet(x)));

// 1. Танилцуулга
body.push(H1("1. Танилцуулга"));
body.push(H2("1.1 Зорилго"));
body.push(P("Pulse.mn нь орон нутгийн баталгаажсан мэдээ, албан ёсны тоон мэдээлэл, улс төрчдийн амлалтын хяналтыг нэг дор нэгтгэсэн платформ. Сэтгүүлч мэдээ байршуулж, редактор (Pulse.mn эсвэл баталгаажсан редакц) нотолгоонд суурилан шалгаж нийтэлнэ; редакц мэдээг лицензлэн худалдан авна; иргэн баталгаажсан мэдээ, статистик, амлалтын явцыг харж, өөрөө зургаар явц баталгаажуулна."));
body.push(H2("1.2 Хамрах хүрээ"));
[
  "Мэдээ: байршуулах → AI урьдчилсан шалгалт → редакторын шийдвэр → нийтлэх, залруулга, нуулт.",
  "Редакц: хуулийн этгээдээр бүртгүүлэх, сэтгүүлчийн гишүүнчлэл, өөрийн редактор, өөрийн гишүүдийн мэдээг шалгах.",
  "Худалдаа: энгийн / онцгой лиценз, НӨАТ ба шимтгэлийн задаргаа — төлбөр ДЕМО горимд (бодит мөнгө шилжихгүй).",
  "Амлалт: parliament.mn-ийн 126 гишүүн, тойрог; хугацаа, явц, 3D газрын зураг; иргэний зурагт мэдээ.",
  "Статистик: аймаг, сумын үзүүлэлт, харьцуулалт, түүх; дэлхийн мэдээний AI шүүлт.",
  "Хамаарахгүй: бодит төлбөрийн шлюз (QPay), сэтгүүлчид орлого шилжүүлэх, 1212.mn API (зөвшөөрөл хүлээж буй).",
].forEach((x) => body.push(bullet(x)));
body.push(H2("1.3 Оролцогчид (persona)"));
body.push(table([2000, 7026], ["Оролцогч", "Үүрэг"], [
  ["Сэтгүүлч", "Мэдээ байршуулах, шалгуулах, редакцад нэгдэх, топ хүсэх, хандалт / борлуулалт харах"],
  ["Редакц (байгууллага)", "Гишүүнчлэл батлах, редактор нэмэх, өөрийн гишүүдийн мэдээг шалгах, мэдээ лицензлэх"],
  ["Редакцын редактор", "Зөвхөн өөрийн редакцын мэдээг шалгах, залруулга, топ тавих"],
  ["Pulse.mn редактор", "Редакцгүй мэдээг шалгах, амлалтын төлөв, залруулга"],
  ["Иргэн", "Мэдээ, статистик, амлалт үзэх; нэрээ нууцалж сэтгэгдэл; амлалтын явцын зураг; гомдол"],
  ["Админ", "Хэрэглэгч, эрх, гомдол, төлбөр, амлалт, статистик, нөөцлөлт, аудит"],
]));
body.push(H2("1.4 Төлвийн тэмдэглэгээ"));
body.push(table([2000, 7026], ["Төлөв", "Утга"], [
  ["Хэрэгжсэн", "Ажиллаж буй системд бүрэн байгаа, кодоор шалгасан"],
  ["Хэсэгчлэн", "Гол хэсэг нь байгаа, тэмдэглэсэн дутуу зүйлтэй"],
  ["ДЕМО", "Урсгал бүрэн, гэхдээ бодит гадаад үйлчилгээ (төлбөр) холбогдоогүй"],
  ["Хэрэгжээгүй", "Системд байхгүй"],
], { toneCol: 0 }));

// 2. Бенчмарк
body.push(H1("2. Бенчмарк судалгаа"));
body.push(P("Pulse.mn-ийн гурван чиглэл (баталгаажсан мэдээ, амлалтын хяналт, мэдээний лицензийн зах)-ээр олон улсын болон Монголын ижил төстэй 7 платформыг харьцуулав. Мэдээллийг 2026.11.19-нд нийтийн эх сурвалжаас цуглуулсан; компаниудын өөрсдийн мэдээлсэн тоог тэмдэглэв."));
body.push(H2("2.1 Платформууд"));
body.push(table([1700, 1500, 3200, 2626], BENCH.cols, BENCH.rows));
body.push(H2("2.2 Чадварын харьцуулалт"));
body.push(P([t("✓ бүрэн · ◐ хэсэгчлэн · — байхгүй. ", { size: 18, color: C.muted })]));
body.push(table([2426, 900, 900, 900, 1000, 950, 1000, 950], BENCH.matrix.cols, BENCH.matrix.rows, { center: [1, 2, 3, 4, 5, 6, 7] }));
body.push(H2("2.3 Дүгнэлт"));
[
  "Олон улсын платформууд нэг чиглэлд төвлөрдөг: Ground News — эх сурвалжийн харьцуулалт, PolitiFact — амлалт, Full Fact — AI баримт шалгалт, Reuters Connect / Newsflare — лицензийн зах.",
  "Монголд IFCN-ийн гэрчилгээтэй баримт шалгах төв (MFCC) байгаа ч мэдээний сайтуудад нийтлэхээс өмнөх баталгаажуулалтын урсгал, амлалтын тасралтгүй хяналт олдсонгүй.",
  "Pulse.mn-ийн ялгарал: баталгаажуулалт + амлалт + албан статистик + лицензийг нэг Монгол платформд; иргэний зургийг AI-аар урьдчилан шалгаж газрын зураг дээр явц харуулах.",
  "Сул тал (бенчмаркаас): Reuters, Newsflare сэтгүүлч / зохиогчид орлогыг шууд шилжүүлдэг — Pulse.mn-д бодит төлбөр, payout хараахан байхгүй (ДЕМО).",
  "Full Fact-ийн зарчмыг баримталсан: AI «үнэн эсэх»-ийг шийдэхгүй, зөвхөн санал, анхааруулга өгнө; шийдвэрийг хүн гаргана.",
].forEach((x) => body.push(bullet(x)));
body.push(H3("Эх сурвалж"));
BENCH.sources.forEach(([n, u]) => body.push(bullet([t(n + " — ", { size: 18 }), new ExternalHyperlink({ link: u, children: [t(u, { size: 18, color: C.teal, underline: {} })] })])));

// 3. Шаардлага
body.push(H1("3. Системийн шаардлага"));
body.push(P(`Анхны SRS (FR-001…FR-079, NFR-001…NFR-015) дээр хэрэгжүүлэх явцад нэмэгдсэн ${frNew.length} функциональ (FR-080…FR-${FR[FR.length - 1][0].slice(3)}) болон ${LR.length} хууль эрх зүйн шаардлагыг нэгтгэв. Шаардлага бүрийг код, дэлгэц, тесттэй тулгасан.`));
body.push(H2("3.1 Хураангуй"));
const sumRow = (label, arr, i) => [label, String(arr.length), ...STATUSES.map((s) => String(count(arr, i, s)))];
body.push(table([2626, 1000, 1400, 1300, 1300, 1400], ["Бүлэг", "Нийт", ...STATUSES], [
  sumRow("FR — анхны SRS", frOrig, 4), sumRow("FR — нэмэгдсэн", frNew, 4), sumRow("Хууль эрх зүй (LR)", LR, 3),
  ["NFR", String(NFR.length), String(count(NFR, 3, "Хэрэгжсэн")), String(count(NFR, 3, "Хэсэгчлэн")), "0", String(count(NFR, 3, "Тэнцээгүй"))],
], { center: [1, 2, 3, 4, 5] }));
body.push(P([t(`Анхны 79 FR-ийн ${count(frOrig, 4, "Хэрэгжсэн")} нь (${pct(count(frOrig, 4, "Хэрэгжсэн"), 79)}) бүрэн, ${count(frOrig, 4, "Хэсэгчлэн")} хэсэгчлэн, ${count(frOrig, 4, "ДЕМО")} ДЕМО, ${count(frOrig, 4, "Хэрэгжээгүй")} хэрэгжээгүй.`, { size: 20 })], { spacing: { before: 120 } }));
body.push(H2("3.2 Функциональ шаардлага (FR)"));
body.push(table([820, 3100, 1120, 2786, 1200], ["ID", "Шаардлага (модуль · оролцогч)", "Төлөв", "Хэрэгжилт / тайлбар", "Тест"],
  FR.map((r) => [r[0], [t(r[3], { size: 17 }), t(`  ${r[1]} · ${r[2]}`, { size: 15, color: C.muted })], r[4], r[5], r[6].join(", ") || "—"]), { toneCol: 2, size: 16 }));
body.push(H2("3.3 Функциональ бус шаардлага (NFR)"));
body.push(table([900, 1500, 2100, 1100, 2526, 900], ["ID", "Ангилал", "Шаардлага", "Төлөв", "Нотолгоо / хэмжилт", "Тест"],
  NFR.map((r) => [r[0], r[1], r[2], r[3], r[4], r[5].join(", ") || "—"]), { toneCol: 3, size: 16 }));
body.push(H2("3.4 Хууль эрх зүйн шаардлага (LR)"));
body.push(table([800, 3300, 2726, 1100, 1100], ["ID", "Шаардлага", "Хууль / дүрэм", "Төлөв", "Тест"],
  LR.map((r) => [r[0], r[1], r[2], r[3], r[4].join(", ")]), { toneCol: 3, size: 16 }));

// 4. Зөрүү
body.push(H1("4. Өмнөх баримттай зөрүү ба засвар"));
body.push(P("Өмнөх баримтуудад (SRS v1.0, requirements.csv v3, .feap v2) байсан боловч системд байхгүй, эсвэл системд байгаа боловч баримтад ороогүй зүйлсийг энд засав."));
body.push(H2("4.1 Баримтад «хэрэгжсэн / төлөвлөгөө» гэж буруу бичигдсэн"));
body.push(table([2600, 3213, 3213], ["Зүйл", "Өмнөх баримтад", "Бодит байдал (2026.11.19)"], [
  ["Газрын зураг (csv №15)", "«Төлөвлөгөө»", "Хэрэгжсэн — амлалтын 3D газрын зураг (MapLibre + OSM)"],
  ["Иргэдийн мэдээлэл (csv №14)", "«Хэсэгчлэн», маягт төлөвлөгөөнд", "Хэрэгжсэн — иргэний амлалтын явцын зураг + AI шалгалт"],
  ["Эх файлын хамгаалалт (FR-032)", "Тусгаагүй", "Хэрэгжээгүй — медиа төлбөрөөс өмнө харагдана"],
  ["Хуваалцах (FR-059)", "Тусгаагүй", "Хэрэгжээгүй"],
  ["Ажлын хуваарилалт (FR-024)", "Тусгаагүй", "Хэсэгчлэн — хуваарилалт, яаралтай тэмдэг байхгүй"],
  ["Тайлан шүүлт (FR-079)", "Тусгаагүй", "Хэсэгчлэн — зөвхөн KPI самбар"],
  ["Хурд (NFR-001, 015)", "Хэмжээгүй", "Засагдсан — 13–34 сек байсныг 0.6–0.9 сек болгов (7.4)"],
  ["Төлбөр (FR-031, csv №38)", "ДЕМО", "ДЕМО хэвээр — QPay, payout холбогдоогүй"],
], { size: 16 }));
body.push(H2("4.2 Системд байгаа боловч өмнөх баримтад дутуу байсан"));
frNew.filter((r) => +r[0].slice(3) >= 89).forEach((r) => body.push(bullet(`${r[0]} — ${r[3]}`)));
body.push(H2("4.3 UML загварын засвар"));
[
  ".feap v2 (2026.11.05)-ийн класс диаграмд PledgeUpdate, Comment, Politician-ы тойргийн талбар, Content.views, featured_until байгаагүй — 5-р бүлгийн класс диаграмыг Django моделиос шууд үүсгэсэн (29 модель).",
  "Use case-д «Амлалтын явцын зураг оруулах», «УИХ-ын гишүүд импортлох», «Сэтгэгдэл — нэр нууцлах», «Топ мэдээ», «Бүгдийг сонгох» нэмэгдэв.",
  "Activity-д «Иргэний амлалтын явцын мэдээ», State-д контентын 6 төлөв (кодын TRANSITIONS) нэмэгдэв.",
].forEach((x) => body.push(bullet(x)));

// 5. UML
body.push(H1("5. UML диаграм"));
body.push(P("Диаграмуудыг хэрэгжсэн кодоос (Django модель, services.py, views.py) үүсгэв: docs/_build/make_diagrams.py. Систем өөрчлөгдвөл дахин ажиллуулахад шинэчлэгдэнэ."));
const sec = [
  ["5.1 Use case диаграм", ["uc_journalist", "uc_newsroom", "uc_citizen", "uc_admin"]],
  ["5.2 Activity диаграм", ["act_review", "act_license", "act_world", "act_pledge"]],
  ["5.3 State диаграм", ["state_content"]],
  ["5.4 Sequence диаграм", ["seq_submit", "seq_purchase", "seq_pledge"]],
  ["5.5 Class диаграм", ["cls_content", "cls_market", "cls_civic"]],
  ["5.6 Deployment диаграм", ["deploy"]],
];
let fig = 0;
for (const [title, keys] of sec) {
  body.push(H2(title));
  for (const k of keys) {
    const d = U(k);
    body.push(image(d.png, 600, 820));
    body.push(caption(`Зураг ${++fig}. ${d.title}`));
  }
}

// 6. Wireframe
body.push(H1("6. Wireframe ба хэрэгжсэн дэлгэц"));
body.push(P("Wireframe: Claude Design-д бэлтгэсэн «Pulse.mn — Wireframes» (2026.11.05, 20 дэлгэц). Дэлгэц бүрийг хэрэгжсэн хуудастай тулгав."));
body.push(table([500, 2300, 2100, 1300, 2826], ["#", "Wireframe", "Хэрэгжсэн хуудас", "Төлөв", "Тайлбар"],
  WF.map((r) => [r[0], r[1], r[2], r[3], r[4]]), { toneCol: 3, size: 16 }));
WF.forEach((r) => {
  const f = path.join(__dirname, "wf", `${r[0]}.png`);
  if (!fs.existsSync(f)) return;
  const mobile = +r[0] >= 18;
  body.push(new Paragraph({ children: [new PageBreak()] }));
  body.push(H3(`${r[0]}. ${r[1]} → ${r[2]} (${r[3]})`));
  body.push(image(f, mobile ? 300 : 600, 760));
  body.push(caption(`Зураг ${++fig}. Wireframe ${r[0]} — ${r[1]}`));
});

// 7. Тест
body.push(H1("7. Тестийн судалгаа: шаардлагатай харьцуулалт"));
body.push(H2("7.1 Арга зүй"));
[
  "Backend: Django APITestCase — бодит HTTP endpoint-оор, үүрэг бүрийн JWT-ээр (сэтгүүлч, редакц, редактор, иргэн, админ) дуудна; гадаад үйлчилгээг (Gemini, RSS, parliament.mn) mock-оор орлуулна.",
  "Frontend: TypeScript typecheck (platform, admin, shared), Next.js production build.",
  "Гүйцэтгэл: production API дээр latency хэмжилт ба 100 хүсэлт / 10 зэрэг ачааллын туршилт (2026.11.19).",
  "Ул мөр (traceability): тест бүрийг шаардлагын ID-тай холбов (3-р бүлгийн «Тест» багана).",
].forEach((x) => body.push(bullet(x)));
body.push(H2("7.2 Үр дүн"));
const allFR = FR.length, frCov = covered(FR, 6), origCov = covered(frOrig, 6), nfrCov = covered(NFR, 5);
const implFR = FR.filter((r) => r[4] === "Хэрэгжсэн"), implCov = covered(implFR, 6);
body.push(table([5026, 2000, 2000], ["Үзүүлэлт", "Утга", "Хувь"], [
  ["Нийт автомат тест (backend)", `${tests.length}`, ""],
  ["Тэнцсэн", `${passed} / ${tests.length}`, pct(passed, tests.length)],
  ["Frontend typecheck + build (platform, admin)", "Алдаагүй", "100%"],
  ["FR — тестээр хамрагдсан (бүгд)", `${frCov} / ${allFR}`, pct(frCov, allFR)],
  ["FR — анхны SRS (79)", `${origCov} / 79`, pct(origCov, 79)],
  ["FR — «Хэрэгжсэн» төлөвтэйгөөс тесттэй", `${implCov} / ${implFR.length}`, pct(implCov, implFR.length)],
  ["Хууль эрх зүй (LR)", `${covered(LR, 4)} / ${LR.length}`, pct(covered(LR, 4), LR.length)],
  ["NFR — автомат тесттэй", `${nfrCov} / ${NFR.length}`, pct(nfrCov, NFR.length)],
], { center: [1, 2] }));
body.push(H2("7.3 Модуль бүрээр хамралт"));
const mods = {};
FR.forEach((r) => { const m = r[1]; mods[m] = mods[m] || [0, 0, 0]; mods[m][0]++; if (r[6].length) mods[m][1]++; if (r[4] === "Хэрэгжсэн") mods[m][2]++; });
body.push(table([3426, 1400, 1400, 1400, 1400], ["Модуль", "FR", "Хэрэгжсэн", "Тесттэй", "Хамралт"],
  Object.entries(mods).sort((a, b) => b[1][0] - a[1][0]).map(([m, v]) => [m, String(v[0]), String(v[2]), String(v[1]), pct(v[1], v[0])]), { center: [1, 2, 3, 4], size: 16 }));
body.push(H2("7.4 Гүйцэтгэлийн тест (production): засварын өмнө ба дараа"));
body.push(P("Хэмжилтийг production API дээр curl-ээр хийсэн. Засварын өмнө /health 0.4 сек байхад ДБ-тэй endpoint 13–34 сек байсан нь сервер биш, өгөгдлийн сантай харилцах хэсэг удааныг харуулав."));
body.push(table([2626, 1500, 1500, 1700, 1700], ["Endpoint", "Query: өмнө", "Query: дараа", "Хугацаа: өмнө", "Хугацаа: дараа"],
  PERF.rows, { size: 16, center: [1, 2, 3, 4] }));
body.push(H3("Шалтгаан ба засвар"));
[
  "Байршил: Vercel функц sin1 (Сингапур), Neon ДБ iad1 (Вашингтон) — query бүр ~230 мс далай дамнасан. Функцийг iad1 руу шилжүүлэв (eeb05ec).",
  "N+1 query: гишүүн бүрийн статистикийг тусад нь тоолж байсныг нэг GROUP BY болгов (137 → 2); амлалтын тоог annotate (46 → 1); мэдээний редакц, залруулга, амлалтыг prefetch (45 → 5).",
  "Регресс хамгаалалт: QueryCountTests — жагсаалтын query тоо өсвөл тест унана.",
].forEach((x) => body.push(bullet(x)));
body.push(H3("Ачааллын туршилт (/news, 100 хүсэлт, 10 зэрэг)"));
body.push(table([3026, 3000, 3000], ["Үзүүлэлт", "Өмнө", "Дараа"], PERF.load, { center: [1, 2], size: 17 }));
body.push(H2("7.5 Тестээр хамрагдаагүй шаардлага"));
body.push(table([1000, 4426, 1400, 2200], ["ID", "Шаардлага", "Төлөв", "Шалгах арга"],
  [...FR.filter((r) => !r[6].length).map((r) => [r[0], r[3], r[4], r[4] === "Хэрэгжсэн" ? "Гараар шалгасан; автомат тест нэмэх" : "Хэрэгжүүлсний дараа тест"]),
   ...NFR.filter((r) => !r[5].length).map((r) => [r[0], r[2], r[3], r[0] === "NFR-015" ? "Ачааллын туршилт (7.4)" : "Гараар / код хянах"])],
  { toneCol: 2, size: 16 }));
body.push(H2("7.6 Test case-ууд"));
body.push(table([900, 2000, 3226, 1700, 1200], ["TC", "Анги", "Test case", "Шаардлага", "Үр дүн"],
  tests.map((x) => [x.id, x.cls, x.name.replace(/^test_/, "").replace(/_/g, " "), (testReqs[x.id] || []).join(", ") || "—", x.ok ? "✅ Тэнцсэн" : "❌"]),
  { toneCol: 4, size: 15 }));

// 8. Дүгнэлт ба зөвлөмж
body.push(H1("8. Дүгнэлт ба зөвлөмж"));
body.push(H2("8.1 Дүгнэлт"));
[
  `Платформ ажиллаж байна: анхны шаардлагын ${pct(implOrig, 79)} бүрэн, ${frNew.length} нэмэлт функц, ${passed}/${tests.length} автомат тест тэнцсэн.`,
  "Pulse.mn-ийн өрсөлдөх давуу тал — нийтлэхээс өмнөх редакторын баталгаажуулалт + AI шалгалт + амлалт + статистик нэг дор, Монгол хэл дээр.",
  "Гүйцэтгэлийн гол асуудлыг хэмжилтээр илрүүлж зассан; цаашид query тооны тест хамгаална.",
].forEach((x) => body.push(bullet(x)));
body.push(H2("8.2 Зөвлөмж ба дараагийн алхам"));
body.push(table([700, 4026, 1500, 2800], ["#", "Ажил", "Ач холбогдол", "Холбогдох шаардлага"], [
  ["1", "QPay merchant гэрээ, бодит төлбөр; сэтгүүлчийн данс, payout (гараар → банкны API)", "Өндөр", "FR-031, FR-076, LR-12"],
  ["2", "Худалдан авалтаас өмнө эх зураг, видеог хаах (watermark / preview)", "Өндөр", "FR-029, FR-032"],
  ["3", "GEMINI_API_KEY тохируулж AI гүнзгий шалгалт, embedding давхардлыг идэвхжүүлэх", "Дунд", "FR-018, FR-085"],
  ["4", "Хуваалцах товч (Open Graph зураг, эх сурвалж, огноотой)", "Дунд", "FR-059"],
  ["5", "Шалгах ажлыг редакторт хуваарилах, «яаралтай» тэмдэг", "Дунд", "FR-024"],
  ["6", "Хугацаа, аймгаар шүүх тайлан; ангилал, аймгийг админ самбараас удирдах", "Дунд", "FR-070, FR-077, FR-079"],
  ["7", "1212.mn API зөвшөөрөл авч статистик автоматаар татах; автомат нөөцлөлт", "Дунд", "FR-064, FR-073"],
  ["8", "Мөрийн хөтөлбөрийг эх сурвалжтайгаар бүртгэх (нам, ТЕГ-ийн баримт)", "Өндөр", "FR-019, FR-049"],
], { size: 16 }));

// 9. Хавсралт
body.push(H1("9. Хавсралт: технологи, API"));
body.push(table([2600, 6426], ["Давхарга", "Технологи"], [
  ["Frontend", "Next.js 14 (platform, admin), TypeScript, shared дизайн систем, MapLibre GL + OpenFreeMap"],
  ["Backend", "Django 5 + DRF, SimpleJWT, 14 app (accounts, content, review, newsroom, pledges, statistics, worldnews, ai, audit …)"],
  ["Өгөгдөл", "Neon Postgres, Vercel Blob (медиа)"],
  ["AI", "Gemini (сонголттой; түлхүүргүй бол дүрмийн fallback), sha256 + dHash, shingle Jaccard"],
  ["Гадаад өгөгдөл", "parliament.mn нийтийн API, RSS (Google News, BBC, The Diplomat, ikon.mn, Al Jazeera), 1212.mn (зөвшөөрөл хүлээж буй)"],
  ["Байршуулалт", "Vercel (3 төсөл), Vercel Cron, GitHub (branch protection, CODEOWNERS)"],
  ["Тест", `Django APITestCase — ${tests.length} test case; tsc, next build`],
]));
body.push(H2("API (үндсэн)"));
[
  "Нэвтрэлт: /auth/register, /auth/login, /auth/me, /auth/me/export, /auth/me/delete, /auth/request-verification",
  "Контент: /content (CRUD), /content/{id}/media, /submit, /history, /versions, /send-to-newsroom, /feature-request, /summary, /suggest-tags",
  "Шалгалт: /review, /review/{id}/decide, /ai-check, /corrections, /feature; редакц: /newsroom/content/…",
  "Нийтийн: /news, /news/{id}, /comments, /world-news, /stats/indicators, /stats/compare, /journalists, /newsrooms",
  "Худалдаа: /purchases, /purchases/quote, /confirm, /cancel, /ratings, /ratings/suggest",
  "Амлалт: /pledges, /pledges/{id}/updates, /update-status, /summary, /pledges/politicians, /compare, /constituencies",
  "Админ: /admin/users, /admin/content, /admin/complaints, /admin/purchases, /admin/pledge-updates, /admin/stats, /admin/backup, /admin/audit",
].forEach((x) => body.push(bullet(x)));

const doc = new Document({
  creator: "Pulse.mn", title: "Pulse.mn — Системийн нэгдсэн баримт бичиг",
  styles: {
    default: { document: { run: { font: FONT, size: 21 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: FONT, size: 34, bold: true, color: C.ink }, paragraph: { spacing: { before: 0, after: 240 }, keepNext: true, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: FONT, size: 26, bold: true, color: C.teal }, paragraph: { spacing: { before: 320, after: 140 }, keepNext: true, outlineLevel: 1 } },
      { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: FONT, size: 22, bold: true, color: C.ink }, paragraph: { spacing: { before: 200, after: 100 }, keepNext: true, outlineLevel: 2 } },
    ],
  },
  numbering: { config: [{ reference: "b", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT,
    style: { paragraph: { indent: { left: 540, hanging: 270 } } } }] }] },
  sections: [{
    properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 } } },
    headers: { default: new Header({ children: [new Paragraph({ alignment: AlignmentType.RIGHT, children: [t("Pulse.mn — Системийн нэгдсэн баримт бичиг v2.0", { size: 16, color: C.muted })] })] }) },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [t("", { size: 16 }), new TextRun({ children: [PageNumber.CURRENT], font: FONT, size: 16, color: C.muted })] })] }) },
    children: body,
  }],
});

const out = path.join(ROOT, "docs", "Pulse.mn — Нэгдсэн баримт бичиг.docx");
Packer.toBuffer(doc).then((b) => { fs.writeFileSync(out, b); console.log(out, (b.length / 1048576).toFixed(1) + " MB", "tests", tests.length, "FR", FR.length); });
