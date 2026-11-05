# Pulse.mn API

Суурь хаяг: `https://pulse-mn-api.vercel.app/api/v1` · Нэвтрэлт: `Authorization: Bearer <JWT access>`
(30 мин; `/auth/refresh/`-ээр шинэчилнэ, 7 хоногийн refresh token эргэлддэг, хаагдвал хүчингүй болно).

## Хэрхэн хийгдсэн бэ
- **Backend:** Django 5 + Django REST Framework. App бүр (`accounts`, `content`, `review`, `newsroom`, `worldnews` …) өөрийн `urls.py`, `views.py` (ViewSet / APIView), `services.py` (бизнес логик, аудит, мэдэгдэл) гэсэн бүтэцтэй. View нь зөвхөн эрх шалгаж, сервис дуудаж, serializer-ээр хариу буцаана.
- **Эрх:** `common.permissions.roles("journalist", …)` — үүрэгт суурилсан; объектын түвшинд queryset-ээр хязгаарлана (жишээ нь редакцын редактор зөвхөн өөрийн редакцын мэдээ).
- **Алдааны код:** 400 талбарын алдаа · 401 нэвтрээгүй · 403 эрхгүй · 404 олдоогүй / харагдахгүй · 409 төлвийн зөрчил · 422 бизнесийн дүрэм (шалтгаан заавал, хууль ёсны мэдэгдэл дутуу г.м.).
- **Хуудаслалт:** жагсаалт `?page=` (12 мөр) → `{count, next, previous, results}`.
- **Тест:** `backend/apps/*/tests.py` — 70 тест (эрхийн матриц, хууль эрх зүй, төлбөр, дэлхийн мэдээ).

## Endpoint-ууд (үүргээр)
| Хэсэг | Endpoint | Хэн |
|---|---|---|
| Нэвтрэлт | `POST auth/register/` (зөвшөөрөл заавал), `POST auth/login/`, `POST auth/refresh/`, `GET/PATCH auth/me/` | Бүгд |
| Хувийн мэдээллийн эрх | `GET auth/me/export/`, `POST auth/me/delete/` | Нэвтэрсэн |
| Баталгаажуулалт | `POST auth/request-verification/` | Сэтгүүлч, редакц |
| Профайл | `PUT profile/experiences/`, `PUT profile/portfolio/` | Сэтгүүлч |
| Каталог | `GET catalog/provinces/ · districts/ · categories/` | Нийтэд |
| Нийтийн мэдээ | `GET news/`, `GET news/{id}/` (зөвхөн нийтлэгдсэн; `disclosure`, `corrections`, `trust`) | Нийтэд |
| Сэтгүүлчийн контент | `content/` CRUD, `{id}/submit/`, `{id}/media/`, `{id}/precheck/`, `{id}/history/`, `{id}/versions/`, `{id}/send-to-newsroom/`, `suggest-tags/`, `summary/` | Сэтгүүлч |
| Шалгалт | `review/`, `review/{id}/`, `{id}/decide/`, `{id}/ai-check/`, `{id}/corrections/` | Pulse.mn редактор, редакцын редактор, админ |
| Редакцын самбар | `newsroom/summary/ · members/ · members/{id}/decide/ · content/ · content/{id}/ · content/{id}/decide/ · ai-check/ · corrections/ · editors/ · editors/{id}/active/` | Редакц |
| Гишүүнчлэл | `GET/POST memberships/`, `POST memberships/{id}/end/` | Сэтгүүлч / редакц |
| Сэтгүүлч, редакц | `GET journalists/`, `journalists/{id}/` (гол сэдэв, үнэлгээ), `GET newsrooms/`, `newsrooms/{id}/` | Нийтэд |
| Үнэлгээ | `GET/POST ratings/`, `GET ratings/suggest/` (AI санал) | Нийтэд / нэвтэрсэн |
| Төлбөр (ДЕМО) | `GET purchases/quote/`, `POST purchases/` (лицензийн нөхцөл), `{id}/confirm/`, `{id}/cancel/` | Редакц (жагсаалтыг сэтгүүлч ч хардаг) |
| Амлалт | `pledges/`, `pledges/politicians/`, `politicians/compare/`, `{id}/update-status/`, `summary/` | Нийтэд / админ |
| Статистик | `stats/indicators/`, `indicators/{id}/series/`, `stats/compare/` | Нийтэд |
| Гомдол | `GET/POST complaints/` | Нэвтэрсэн |
| Мэдэгдэл | `notifications/`, `{id}/read/`, `unread_count/` | Нэвтэрсэн |
| Дэлхийн мэдээ | `GET world-news/`, `GET world-news/sources/`, `GET/POST world-news/refresh/` (Cron эсвэл админ) | Нийтэд |
| Админ | `admin/users/` (+ `{id}/verify/`), `admin/content/` (+ `hide/` хууль зүйн үндэслэлтэй, `restore/`), `admin/complaints/` (+ `resolve/` залруулгатай), `admin/purchases/` (+ `refund/`), `admin/stats/*`, `admin/audit/`, `admin/backup/` | Админ |

## Гадны API, үйлчилгээ
| Үйлчилгээ | Юунд | Холболт |
|---|---|---|
| **Gemini API** (`gemini-2.5-flash`) | AI шошго, мэдээ хянах, үнэлгээний санал, дэлхийн мэдээний орчуулга/ангилал | `ai/gemini.py` — REST, `GEMINI_API_KEY`; түлхүүргүй бол дүрмийн fallback |
| **Neon Postgres** | Мэдээллийн сан | `DATABASE_URL` (Vercel Marketplace) |
| **Vercel Blob** | Зураг, видео, баримт | `common/storage.py` — `PUT https://vercel.com/api/blob`, `BLOB_READ_WRITE_TOKEN` |
| **Vercel Cron** | Дэлхийн мэдээг өдөр бүр шинэчлэх | `vercel.json` → `Authorization: Bearer CRON_SECRET` |
| **RSS** (Google News, BBC, The Diplomat, ikon.mn, Al Jazeera) | Монголын тухай мэдээ | `worldnews/sources.py` — тогтмол жагсаалт; og:image зөвхөн robots.txt зөвшөөрвөл |
| **1212.mn** (ҮСХ) | Албан ёсны мэдээ | `/api/articles` нь robots.txt-ээр хориотой → ҮСХ-ны зөвшөөрлөөр `NSO_API_ENABLED=1` |
| **QPay / И-баримт** | Төлбөр, баримт | Холбогдоогүй — `newsroom/payments.py` ДЕМО provider; `PAYMENT_PROVIDER=qpay` болгож хэрэгжүүлнэ |
