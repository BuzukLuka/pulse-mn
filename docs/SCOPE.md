# Хамрах хүрээ ба шаардлагын уялдаа

Эх сурвалж: `Pulse_mn - System Requirements (FR-NFR).xlsx`, `General_requirement.xlsx`,
`Pulse_mn_ajliin_tuluvlugu.xlsx`, `pulse_mn.feap` (UC-01/02/03 + Sequence/Activity диаграм).

## Төлбөрийн хэсгийг хассан
Дараах шаардлагууд **хэрэгжүүлээгүй** (хүсэлтийн дагуу): FR-006, FR-007 (үнэ тогтоох),
FR-030…FR-034, FR-037 (худалдан авалт, төлбөр, эх файл нээх), FR-076 (төлбөрийн хяналт),
General requirement-ийн «Захиалга / Төлбөр тооцоо / Захиалгын төлөв».
Контентод үнэ, захиалга, invoice байхгүй — нийтлэгдсэн мэдээ бүгдэд нээлттэй.

## Хэрэгжсэн
| Use case / шаардлага | Backend | Frontend |
|---|---|---|
| FR-001/002 Бүртгэл, нэвтрэлт, профайл | `accounts` (JWT, role) | platform `/login`, `/register` |
| UC-01 / FR-003…005, 010 Контент оруулах, медиа, засаж дахин илгээх | `content` (CRUD, `/submit`, `/media`, 400 валидаци) | platform `/journalist/*` |
| AI шошго (T032) | `ai` → Gemini, fallback дүрэм; `POST /content/suggest-tags/` | `ContentForm` «AI шошго» |
| UC-02 / FR-011…018, 024, 025 Шалгах, шийдвэр, давхардал | `review` (`/decide` 422, state machine, media sha256 + гарчиг) | platform `/editor/*` |
| **Gemini-аар мэдээ хянах** | `POST /review/{id}/ai-check/` | редакторын хуудас «AI-аар шалгуулах» |
| FR-017, 027, 028, 058 Нийтэд харагдах, хайлт, шүүлтүүр | `news` (зөвхөн `published`) | platform `/`, `/news/[id]` |
| UC-03 / FR-060…062, 072 Эрх удирдлага, 409 сүүлчийн админ, сесс цуцлах | `accounts.services.update_access` | admin `/users` |
| FR-062 Нийтлэгдсэн мэдээг түр нуух/сэргээх | `admin/content/{id}/hide|restore` | admin `/content` |
| FR-071, NFR-010 Аудит | `audit.AuditLog` (бүх шийдвэр, эрх, илгээлт) | admin `/audit` |
| FR-025, 037(мэдэгдэл хэсэг) Мэдэгдэл | `notifications` | platform 🔔 |
| NFR-003/004/013 Нууц үг hash, role-based хамгаалалт | Django hasher, `roles()` permission | `RequireRole` |

## v2-д нэмэгдсэн (wireframe + use-case диаграмын бүх дэлгэц, төлбөрөөс бусад)
| Хэсэг | Backend | Frontend |
|---|---|---|
| Сэтгүүлчийн профайл, туршлага, портфолио, нууцлалын сонголт, баталгаажуулалт (admin) | `accounts` (`/profile/*`, `/journalists/*`, `/admin/users/{id}/verify/`) | platform `/profile`, `/journalists`, `/journalists/[id]`; admin `/users` |
| Контентын төрөл (мэдээ/нийтлэл/зураг/видео/баримт), цаг, байршил, лиценз, зохиогчийн эрхийн мэдэгдэл | `content` | `ContentForm` |
| Сэтгүүлчийн самбар (төлвөөр тоо/шүүлт) | `GET /content/summary/` | `/journalist` |
| Хувилбар хадгалах, өмнөх хувилбартай харьцуулах, шалгах жагсаалт (checklist) | `ContentVersion`, `/review/{id}/` | `/editor/[id]` |
| Амлалтын хяналт: албан тушаалтан, амлалт, нотлох баримт, төлвийн түүх, биелэлтийн %, харьцуулалт | `pledges` | platform `/pledges`, `/pledges/[id]`; admin `/pledges` |
| Статистикийн самбар: үзүүлэлт, динамик, аймгийн харьцуулалт, эх сурвалж, шинэчлэгдсэн огноо | `statistics` (`/stats/*`) | platform `/stats` |
| Эх сурвалж/өгөгдлийн удирдлага: CSV импорт, холбоосоос татах (SSRF хамгаалалттай), утга засах, түүх, сэргээх | `/admin/stats/*` | admin `/stats` |
| Гомдол, санал (мэдээ/амлалт/үзүүлэлт) + админ шийдвэрлэх, мэдэгдэх | `complaints` | platform `/complaints`, `ComplaintForm`; admin `/complaints` |
| Нөөцлөлт (JSON dump; сэргээх `loaddata`) | `GET /admin/backup/` | admin `/backup` |
| **Pulse Trust AI давхарга** | `ai/checks.py` | `TrustCard` (platform, editor, journalist) — `docs/INNOVATION.md` |

## Хийгээгүй / санаатайгаар хассан
* **Төлбөр, захиалга, худалдан авалт, «Мэдээний зах» (wireframe 12–14)** — хүсэлтийн дагуу.
* Нөөцийг вэбээс «сэргээх» товч — өгөгдлийг бүхэлд нь дарж бичих аюултай тул `manage.py loaddata`-аар гараар (admin `/backup` дээр заавар бий).
* Файл хадгалалт: Vercel-ийн серверлесс дээр диск байхгүй тул production-д S3/R2/Supabase Storage-д шилжүүлэх шаардлагатай (README).
* Мэдээллийн сангийн бүх демо өгөгдөл (`seed_demo`) **зохиомол**, бодит тоо биш.
