# Pulse.mn

Орон нутгийн баталгаатай мэдээллийн платформ. **Төлбөр/маркетплейс хэсэг хасагдсан**;
сэтгүүлч мэдээ оруулна → редактор (Gemini AI-ийн тусламжтай) шалгаж нийтэлнэ → нийтийн сайтад гарна →
админ хэрэглэгч, эрх, аудитыг удирдана.

```
pulse-mn/
├─ backend/                 Django 5 + DRF + PostgreSQL  (Vercel project #1: API)
│  ├─ config/               settings, urls
│  ├─ api/index.py          Vercel serverless entry
│  └─ apps/
│     ├─ accounts/          User, JWT, эрх удирдлага (UC-03)
│     ├─ catalog/           Аймаг, сум, ангилал + `seed`
│     ├─ content/           Контент, медиа, state machine (UC-01)
│     ├─ review/            Редакторын шалгалт (UC-02)
│     ├─ ai/                Gemini клиент + дүрмийн fallback
│     ├─ audit/             Аудит лог
│     └─ notifications/     Мэдэгдэл
├─ apps/
│  ├─ platform/             Next.js 14 + TS: нийтийн сайт, сэтгүүлч, редактор (Vercel #2)
│  └─ admin/                Next.js 14 + TS: админ самбар (Vercel #3)
├─ packages/shared/         Хуваалцсан TS: API client, auth, төрөл, UI, CSS
├─ infra/pgadmin/           pgAdmin серверийн тохиргоо
├─ docs/SCOPE.md            Шаардлагын уялдаа
└─ docker-compose.yml       Postgres + pgAdmin + backend
```

## Локал ажиллуулах

```bash
# 1) Postgres + pgAdmin + Django
cp backend/.env.example backend/.env        # GEMINI_API_KEY-ээ энд бичнэ
docker compose up --build                   # API http://localhost:8000 · pgAdmin http://localhost:5050
#   pgAdmin нэвтрэх: admin@pulse.mn / admin  (сервер "Pulse.mn (local)" автоматаар бүртгэгдсэн, нууц үг: pulse)

# 2) Frontend
npm install
cp apps/platform/.env.example apps/platform/.env.local
cp apps/admin/.env.example    apps/admin/.env.local
npm run dev:platform     # http://localhost:3000
npm run dev:admin        # http://localhost:3001
```

Docker-гүйгээр: `cd backend && pip install -r requirements.txt && python manage.py migrate && python manage.py seed && python manage.py seed_demo && python manage.py runserver`
(`DATABASE_URL` хоосон бол SQLite). Тест: `python manage.py test` (9 тест).

**Туршилтын хэрэглэгч** (`seed`, нууц үг `Pulse12345!` — production дээр заавал солих/устгах):
`journalist@pulse.mn`, `editor@pulse.mn`, `admin@pulse.mn`.

## Gemini API
`GEMINI_API_KEY` (https://aistudio.google.com/apikey) тохируулбал:
- сэтгүүлч «✨ Ангилал, түлхүүр үг санал болгох» дарахад ангилал, шошго, хураангуй гарна;
- редактор «✨ AI-аар шалгуулах» дарахад баримт/чанарын урьдчилсан дүгнэлт (verdict, оноо, асуудлууд) гарна.
Түлхүүр байхгүй эсвэл дуудлага алдаатай бол дүрэмд суурилсан хувилбар автоматаар ажиллана.
AI нь зөвхөн санал өгнө — **эцсийн шийдвэрийг редактор гаргана**. Модель: `GEMINI_MODEL` (default `gemini-2.5-flash`).

## Vercel дээр байршуулах (3 project, нэг repo)
Repo-г GitHub-д push хийгээд Vercel дээр **Add New → Project** гурван удаа, тус бүр дээр **Root Directory**-г заана:

| Project | Root Directory | Env |
|---|---|---|
| `pulse-mn-api` | `backend` | `DATABASE_URL`, `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=0`, `GEMINI_API_KEY`, `CORS_ALLOWED_ORIGINS`, `CSRF_TRUSTED_ORIGINS` |
| `pulse-mn-platform` | `apps/platform` | `NEXT_PUBLIC_API_URL=https://<api>.vercel.app/api/v1` |
| `pulse-mn-admin` | `apps/admin` | `NEXT_PUBLIC_API_URL=…`, `NEXT_PUBLIC_PLATFORM_URL=https://<platform>.vercel.app` |

Frontend project дээр *Settings → General → "Include source files outside of the Root Directory"* **асаалттай** байх ёстой (shared багц).

Мэдээллийн сан: Vercel Marketplace-ээс **Neon** эсвэл **Supabase** Postgres холбоод `DATABASE_URL`-ийг API project-д өгнө.
Эхний migrate/seed-ийг локалаас ажиллуулна:
```bash
cd backend
DATABASE_URL="postgres://…" python manage.py migrate
DATABASE_URL="postgres://…" python manage.py seed --password '<хүчтэй-нууц-үг>'
```
pgAdmin-д ижил хост/порт/хэрэглэгчээр шинэ сервер нэмж холбоно.

> ⚠️ **Файл хадгалалт:** Vercel serverless дээр файлын систем түр зуурынх тул зураг/видео upload production-д
> хадгалагдахгүй. Production-д `django-storages` (S3/Supabase Storage/Cloudflare R2) эсвэл Vercel Blob холбоно
> (`content.Media.file` талбар storage backend-ээр солигдоход хангалттай).

## API товч
`POST /auth/register|login|refresh` · `GET /auth/me` · `GET /catalog/{provinces,districts,categories}` ·
`GET|POST /content/`, `POST /content/{id}/submit|media`, `POST /content/suggest-tags/` ·
`GET /news/` (нийтийн) · `GET /review/`, `POST /review/{id}/decide|ai-check` ·
`GET|PATCH /admin/users/` · `GET /admin/content/`, `POST …/hide|restore` · `GET /admin/audit|stats/` · `GET /notifications/`

## v2: нэмэгдсэн боломжууд
Профайл/портфолио, амлалтын хяналт, статистикийн самбар + эх сурвалжийн удирдлага, гомдол, нөөцлөлт, хувилбар/checklist
болон **Pulse Trust AI давхарга** (давхардал, төстэй зураг, тоон баримтын тулгалт, хувийн мэдээлэл).
Дэлгэрэнгүй: [`docs/SCOPE.md`](docs/SCOPE.md), [`docs/INNOVATION.md`](docs/INNOVATION.md).

* Зохиомол демо өгөгдөл: `python manage.py seed_demo` (албан ёсны үзүүлэлт, албан тушаалтан, амлалт — **бодит биш**).
* Миграци шинэчлэгдсэн (`0001_initial` дахин үүссэн) — v1-ийн өгөгдлийн санг шинээр үүсгэнэ үү.
* Тест: `cd backend && python manage.py test` (18 тест).
