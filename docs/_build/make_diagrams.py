"""Pulse.mn UML диаграмуудыг (Mermaid) бодит кодоос үүсгэж PNG болгоно.

Класс диаграм нь models.json (Django моделиос introspect хийсэн) дээр суурилна — систем өөрчлөгдвөл
дахин ажиллуулахад таарна. Бусад диаграм нь хэрэгжсэн урсгал (services.py, views.py)-ыг дагана.
"""
import json
import os
import subprocess

from PIL import Image, ImageChops

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "uml")
os.makedirs(OUT, exist_ok=True)
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

D = {}

# ---------------------------------------------------------------- Use case

def uc(title, actors, ucs, secondary=()):
    """Оролцогч зүүн талд, use case системийн хүрээнд, туслах систем баруун талд — огтлолцолгүй од хэлбэр."""
    L = ["flowchart LR",
         "  classDef actor fill:#fff,stroke:#0c2430,stroke-width:2px,color:#0c2430,font-weight:bold",
         "  classDef uc fill:#e2f0f2,stroke:#0f6f7c,color:#0c2430",
         "  classDef ext fill:#eeebfa,stroke:#5b4bb7,color:#0c2430"]
    for i, a in enumerate(actors):
        L.append(f"  A{i}([\"{a}\"]):::actor")
    L.append("  subgraph S[Pulse.mn]")
    L.append("    direction TB")
    for i, (u, _, _) in enumerate(ucs):
        L.append(f"    U{i}(\"{u}\"):::uc")
    L.append("  end")
    for i, s in enumerate(secondary):
        L.append(f"  X{i}[\"{s}\"]:::ext")
    for i, (u, who, ext) in enumerate(ucs):
        for a in who:
            L.append(f"  A{actors.index(a)} --- U{i}")
        for e in ext:
            L.append(f"  U{i} -.-> X{secondary.index(e)}")
    return (title, "\n".join(L))


D["uc_journalist"] = uc("Use case — Сэтгүүлч", ["Сэтгүүлч"], [
    ("Бүртгүүлэх, нэвтрэх — нөхцөл, ёс зүй зөвшөөрөх", ["Сэтгүүлч"], []),
    ("Профайл, туршлага, портфолио, гол сэдэв", ["Сэтгүүлч"], []),
    ("Баталгаажуулалт хүсэх", ["Сэтгүүлч"], []),
    ("Контент байршуулах, медиа хавсаргах", ["Сэтгүүлч"], ["AI: Gemini / дүрэм"]),
    ("Урьдчилан шалгах, хууль ёсны мэдэгдэл", ["Сэтгүүлч"], ["AI: Gemini / дүрэм"]),
    ("Шалгалтад илгээх — бүгдийг сонгож олноор", ["Сэтгүүлч"], []),
    ("Төлвийн түүх, редакторын тайлбар харах", ["Сэтгүүлч"], []),
    ("Редакцад нэгдэх / гарах", ["Сэтгүүлч"], []),
    ("Топ мэдээ болгох хүсэлт", ["Сэтгүүлч"], []),
    ("Хандалт, борлуулалт (ДЕМО) харах", ["Сэтгүүлч"], []),
    ("Мэдэгдэл — бүгдийг сонгох", ["Сэтгүүлч"], []),
], ["AI: Gemini / дүрэм"])

D["uc_newsroom"] = uc("Use case — Редакц ба редакторууд", ["Редакц", "Редакцын редактор", "Pulse.mn редактор"], [
    ("Хуулийн этгээдээр бүртгүүлэх", ["Редакц"], []),
    ("Сэтгүүлчийн гишүүнчлэл батлах", ["Редакц"], []),
    ("Редакцын редактор нэмэх / идэвхгүй болгох", ["Редакц"], []),
    ("Контент шалгаж шийдвэр гаргах", ["Редакц", "Редакцын редактор", "Pulse.mn редактор"], ["AI: Gemini / дүрэм"]),
    ("Залруулга, хариу тайлбар нийтлэх", ["Редакцын редактор", "Pulse.mn редактор"], []),
    ("Топ мэдээ тавих — хугацаатай", ["Редакц", "Редакцын редактор", "Pulse.mn редактор"], []),
    ("Мэдээ лицензлэх — худалдан авах", ["Редакц"], ["Төлбөр — ДЕМО"]),
    ("Сэтгүүлчид үнэлгээ өгөх", ["Редакц"], ["AI: Gemini / дүрэм"]),
    ("Амлалтын төлөв — нотолгоотой", ["Pulse.mn редактор"], []),
], ["AI: Gemini / дүрэм", "Төлбөр — ДЕМО"])

D["uc_citizen"] = uc("Use case — Иргэн", ["Иргэн"], [
    ("Мэдээ хайх, ангилал, Шуурхай", ["Иргэн"], []),
    ("Pulse Trust карт, залруулга харах", ["Иргэн"], []),
    ("Сэтгэгдэл — нэрээ нууцлах", ["Иргэн"], []),
    ("Статистикийн самбар, аймаг харьцуулах", ["Иргэн"], []),
    ("Амлалт: тойрог, 3D газрын зураг, хугацаа", ["Иргэн"], ["parliament.mn"]),
    ("Амлалтын явцын зураг оруулах", ["Иргэн"], ["AI: Gemini / дүрэм"]),
    ("Дэлхийн мэдээ үзэх", ["Иргэн"], ["RSS эх сурвалж"]),
    ("Гомдол гаргах", ["Иргэн"], []),
    ("Үнэлгээ өгөх", ["Иргэн"], []),
    ("Хувийн мэдээлэл татах / бүртгэл устгах", ["Иргэн"], []),
], ["AI: Gemini / дүрэм", "parliament.mn", "RSS эх сурвалж"])

D["uc_admin"] = uc("Use case — Админ", ["Админ"], [
    ("Хэрэглэгч, эрх, баталгаажуулалт", ["Админ"], []),
    ("Контент хянах, нуух — хууль зүйн үндэслэл", ["Админ"], []),
    ("Гомдол шийдвэрлэх", ["Админ"], []),
    ("Төлбөр хянах, буцаах", ["Админ"], ["Төлбөр — ДЕМО"]),
    ("Амлалт: хугацаа, явц, байршил, урьдчилан баталгаажсан зураг", ["Админ"], []),
    ("Иргэний явцын мэдээ шалгах", ["Админ"], []),
    ("УИХ-ын гишүүд импортлох", ["Админ"], ["parliament.mn"]),
    ("Статистик: эх сурвалж, үзүүлэлт, түүх сэргээх", ["Админ"], []),
    ("Нөөцлөлт, аудит лог", ["Админ"], []),
], ["Төлбөр — ДЕМО", "parliament.mn"])

# ---------------------------------------------------------------- Activity
D["act_review"] = ("Activity — Шалгалтад илгээх ба чиглүүлэлт", """flowchart TD
  s((●)) --> a1[Сэтгүүлч «Шалгалтад илгээх»]
  a1 --> d1{Баталгаажсан<br/>сэтгүүлч үү?}
  d1 -- үгүй --> f1([Татгалзана: баталгаажуулалт хүсэх])
  d1 -- тийм --> d2{Мэдэгдэл, талбар<br/>бүрэн үү?}
  d2 -- үгүй --> f2([400: алдааны жагсаалт])
  d2 -- тийм --> a2[AI урьдчилсан шалгалт:<br/>давхардал, зураг, тоо, хувийн мэдээлэл]
  a2 --> a3[Хувилбар хадгалах v1, v2 …]
  a3 --> d3{Редакцын гишүүн,<br/>редакцаа сонгосон уу?}
  d3 -- тийм --> r1[review_by = редакц → редакц, редакторуудад мэдэгдэл]
  d3 -- үгүй --> r2[review_by = Pulse.mn → Pulse.mn редакторт мэдэгдэл]
  r1 --> e1[Редактор шалгах жагсаалт бөглөнө, AI гүнзгий шалгалт]
  r2 --> e1
  e1 --> d4{Шийдвэр}
  d4 -- Зөвшөөрөх --> p1([Нийтлэгдсэн — Pulse Trust карт])
  d4 -- Засварт буцаах --> p2[Засвар шаардлагатай + тайлбар] --> a1
  d4 -- Татгалзах --> p3([Татгалзсан + шалтгаан])""")

D["act_license"] = ("Activity — Мэдээ лицензлэх (ДЕМО төлбөр)", """flowchart TD
  s((●)) --> a1[Редакц нийтлэгдсэн мэдээн дээр лиценз сонгоно: энгийн ×1 / онцгой ×3]
  a1 --> a2[Үнийн задаргаа: НӨАТ 10/110, Pulse.mn шимтгэл 10%, сэтгүүлчийн цэвэр дүн]
  a2 --> d1{Нөхцөл зөвшөөрсөн,<br/>эрх чөлөөтэй юу?}
  d1 -- үгүй --> f1([Татгалзана])
  d1 -- тийм --> a3[Нэхэмжлэх PMN-XXXX — provider: demo]
  a3 --> d2{Төлбөр<br/>баталгаажсан уу?}
  d2 -- цуцалсан --> f2([Цуцлагдсан])
  d2 -- тийм --> a4[Төлөгдсөн; И-баримт ДЕМО; сэтгүүлчид мэдэгдэл]
  a4 --> d3{Маргаан<br/>гарсан уу?}
  d3 -- тийм --> a5([Админ шалтгаантай буцаана])
  d3 -- үгүй --> f3([Төгсгөл])""")

D["act_world"] = ("Activity — Дэлхийн мэдээний AI шүүлт", """flowchart TD
  s((●)) --> a1[Vercel Cron өдөр бүр / кэш 3 цагаас хуучирсан]
  a1 --> a2[RSS эх сурвалж бүрийг зэрэг татна — нэг нь унахад бусад нь үргэлжилнэ]
  a2 --> a3[Давхардал хасах, хэл таних]
  a3 --> d1{Gemini<br/>тохируулсан уу?}
  d1 -- тийм --> g[Gemini: Монголтой холбоо, ангилал, Монгол гарчиг, хураангуй]
  d1 -- үгүй --> r[Дүрэм: түлхүүр үг, Өвөр Монголыг хасах, ангилал]
  g --> a4[Холбоо ≥ 0.5-ийг хадгална]
  r --> a4
  a4 --> a5[robots.txt зөвшөөрвөл og:image зураг]
  a5 --> f([Төгсгөл])""")

D["act_pledge"] = ("Activity — Иргэний амлалтын явцын мэдээ", """flowchart TD
  s((●)) --> a1[Нэвтэрсэн иргэн амлалт сонгоно]
  a1 --> a2[Тайлбар, зураг jpg/png/webp ≤10MB, байршил, явцын үнэлгээ]
  a2 --> a3[sha256 + dHash тооцоолох]
  a3 --> a4[AI урьдчилсан шалгалт:<br/>давхар зураг, байршлаас >5 км,<br/>богино тайлбар → оноо 0–100]
  a4 --> a5[Шалгаж буй төлөвтэй хадгална — нийтэд харагдахгүй]
  a5 --> d1{Админ / редактор<br/>шийдвэр}
  d1 -- Баталгаажуулах --> b1[Амлалтын явц % шинэчлэх; нотлох баримт PledgeEvidence үүсгэх]
  b1 --> b2([Нийтэд харагдана; иргэнд мэдэгдэл])
  d1 -- Татгалзах --> c1([Татгалзсан; иргэнд мэдэгдэл])""")

# ---------------------------------------------------------------- State
D["state_content"] = ("State — Контентын төлөв", """stateDiagram-v2
  [*] --> draft: Үүсгэх
  draft --> under_review: Шалгалтад илгээх
  changes_requested --> under_review: Засаад дахин илгээх
  under_review --> published: Зөвшөөрөх
  under_review --> changes_requested: Засварт буцаах
  under_review --> rejected: Татгалзах
  published --> hidden: Нуух (хууль зүйн үндэслэл)
  hidden --> published: Сэргээх
  rejected --> [*]
  draft: Ноорог
  under_review: Хянагдаж буй
  changes_requested: Засвар шаардлагатай
  published: Нийтлэгдсэн
  rejected: Татгалзсан
  hidden: Түр нуусан""")

# ---------------------------------------------------------------- Sequence
D["seq_submit"] = ("Sequence — Контент байршуулж шалгуулах", """sequenceDiagram
  autonumber
  actor J as Сэтгүүлч
  participant W as Platform (Next.js)
  participant API as API (Django)
  participant AI as AI шалгалт
  participant DB as Neon Postgres
  actor E as Редактор
  J->>W: Маягт бөглөж, медиа хавсаргана
  W->>API: POST /content/ (JWT)
  API->>DB: Content(draft)
  W->>API: POST /content/{id}/media/
  API->>API: төрөл, хэмжээ, sha256, dHash
  J->>W: «Шалгалтад илгээх»
  W->>API: POST /content/{id}/submit/
  API->>AI: run_checks (давхардал, тоо, хувийн мэдээлэл)
  AI-->>API: verification + trust оноо
  API->>DB: under_review, review_by, ContentVersion
  API-->>E: Мэдэгдэл
  E->>W: Шалгах жагсаалт, шийдвэр
  W->>API: POST /review/{id}/decide/
  API->>DB: published / changes_requested / rejected + AuditLog
  API-->>J: Мэдэгдэл (шалтгаантай)""")

D["seq_purchase"] = ("Sequence — Мэдээ худалдан авах (ДЕМО)", """sequenceDiagram
  autonumber
  actor N as Редакц
  participant W as Platform
  participant API as API
  participant P as PaymentProvider (demo)
  actor J as Сэтгүүлч
  N->>W: Лиценз сонгох
  W->>API: GET /purchases/quote/
  API-->>W: НӨАТ, шимтгэл, сэтгүүлчийн дүн
  N->>W: Нөхцөл зөвшөөрөх
  W->>API: POST /purchases/
  API->>P: create_invoice
  P-->>API: provider_ref
  N->>W: «Төлбөр төлсөн»
  W->>API: POST /purchases/{id}/confirm/
  API->>P: issue_receipt (И-баримт ДЕМО)
  API-->>J: «Таны мэдээг худалдан авлаа · цэвэр дүн»""")

D["seq_pledge"] = ("Sequence — Амлалтын явц баталгаажуулах", """sequenceDiagram
  autonumber
  actor C as Иргэн
  participant W as Platform
  participant API as API
  participant B as Vercel Blob
  actor A as Админ
  C->>W: Зураг, байршил, тайлбар
  W->>API: POST /pledges/{id}/updates/ (multipart)
  API->>API: check_update: давхардал, зай, тайлбар
  API->>B: зураг хадгалах
  API-->>W: AI оноо, анхааруулга
  A->>W: Шалгах дараалал
  W->>API: POST /admin/pledge-updates/{id}/review/
  API->>API: progress шинэчлэх, PledgeEvidence
  API-->>C: Мэдэгдэл""")

# ---------------------------------------------------------------- Deployment
D["deploy"] = ("Deployment — Байршуулалт", """flowchart LR
  classDef n fill:#fff,stroke:#0c2430,stroke-width:1.5px,color:#0c2430
  classDef ext fill:#eeebfa,stroke:#5b4bb7,color:#0c2430
  U[Хэрэглэгчийн хөтөч / гар утас]:::n
  P[Vercel · pulse-mn-platform<br/>Next.js 14]:::n
  AD[Vercel · pulse-mn-admin<br/>Next.js 14]:::n
  API[Vercel · pulse-mn-api<br/>Django 5 + DRF, sin1]:::n
  DB[(Neon Postgres)]:::n
  BL[(Vercel Blob — медиа)]:::n
  CR[Vercel Cron — өдөр бүр]:::n
  G[Gemini API — сонголттой]:::ext
  R[RSS эх сурвалжууд]:::ext
  PM[parliament.mn API]:::ext
  OSM[OpenFreeMap / OSM 3D tiles]:::ext
  GH[GitHub · BuzukLuka/pulse-mn]:::ext
  U -- HTTPS --> P
  U -- HTTPS --> AD
  U -- vector tiles --> OSM
  P -- REST /api/v1 JWT --> API
  AD -- REST /api/v1 JWT --> API
  API -- SQL --> DB
  API -- PUT --> BL
  CR -- /world-news/refresh --> API
  API -.-> G
  API -.-> R
  API -.-> PM
  GH -- push → deploy --> P & AD & API""")

# ---------------------------------------------------------------- Class (models.json-оос)
models = {m["name"]: m for m in json.load(open(os.path.join(HERE, "models.json"), encoding="utf8"))}
SKIP_F = {"id", "password", "groups", "user_permissions", "last_login", "is_superuser", "is_staff"}
TYPE = {"CharField": "str", "TextField": "text", "BooleanField": "bool", "DateTimeField": "datetime", "DateField": "date",
        "PositiveIntegerField": "int", "PositiveSmallIntegerField": "int", "IntegerField": "int", "FloatField": "float",
        "JSONField": "json", "FileField": "file", "URLField": "url", "EmailField": "email", "DecimalField": "decimal",
        "BigAutoField": "id", "TimeField": "time", "SlugField": "slug", "BigIntegerField": "int"}


def cls_diagram(names, title, maxf=11):
    lines = ["classDiagram", "  direction LR"]
    for n in names:
        m = models[n]
        attrs = [f for f in m["fields"] if not f[2] and f[0] not in SKIP_F]
        lines.append(f"  class {n} {{")
        for f in attrs[:maxf]:
            lines.append(f"    +{TYPE.get(f[1], f[1])} {f[0]}")
        if len(attrs) > maxf:
            lines.append(f"    +… {len(attrs) - maxf} талбар")
        lines.append("  }")
    for n in names:
        for f in models[n]["fields"]:
            if f[2] in names and f[0] not in SKIP_F:
                card = '"*" --> "0..*"' if f[3] == "many" else ('"0..*" --> "1"' if f[3] == "fk" else '"1" --> "1"')
                lines.append(f"  {n} {card} {f[2]} : {f[0]}")
    return (title, "\n".join(lines))


D["cls_content"] = cls_diagram(["User", "Experience", "PortfolioItem", "Content", "Media", "ContentVersion", "Correction",
                                "Comment", "Category", "Province", "District", "Notification", "AuditLog"],
                               "Class — Хэрэглэгч, контент")
D["cls_market"] = cls_diagram(["User", "Content", "Membership", "Purchase", "Rating", "Complaint", "ExternalArticle", "FetchRun",
                               "Category"], "Class — Редакц, худалдаа, гомдол, дэлхийн мэдээ")
D["cls_civic"] = cls_diagram(["Politician", "Pledge", "PledgeEvidence", "PledgeStatusHistory", "PledgeUpdate", "Category",
                              "Province", "District", "DataSource", "Indicator", "IndicatorValue", "IndicatorValueHistory", "User"],
                             "Class — Амлалт, статистик")

HTML = """<!doctype html><html><head><meta charset="utf-8">
<script src="https://cdn.jsdelivr.net/npm/mermaid@10.9.1/dist/mermaid.min.js"></script>
<style>body{margin:0;background:#fff;font-family:'Segoe UI',Arial,sans-serif}.mermaid{padding:24px;display:inline-block}</style></head>
<body><pre class="mermaid">%s</pre><script>mermaid.initialize({startOnLoad:true,theme:'base',
themeVariables:{fontFamily:'Segoe UI, Arial, sans-serif',fontSize:'15px',primaryColor:'#e2f0f2',primaryBorderColor:'#0f6f7c',
lineColor:'#3b4a56',primaryTextColor:'#0c2430',secondaryColor:'#f4f2ee',tertiaryColor:'#fbfaf8'},
flowchart:{htmlLabels:true,curve:'basis',useMaxWidth:false},sequence:{mirrorActors:false,useMaxWidth:false},
class:{useMaxWidth:false},state:{useMaxWidth:false},maxTextSize:200000});</script></body></html>"""


def trim(p):
    im = Image.open(p).convert("RGB")
    bg = Image.new("RGB", im.size, (255, 255, 255))
    box = ImageChops.difference(im, bg).getbbox()
    if box:
        pad = 24
        im = im.crop((max(0, box[0] - pad), max(0, box[1] - pad), min(im.width, box[2] + pad), min(im.height, box[3] + pad)))
    im.save(p)
    return im.size


index = []
for key, (title, src) in D.items():
    html = os.path.join(OUT, key + ".html")
    open(html, "w", encoding="utf8").write(HTML % src.replace("<", "&lt;").replace("&lt;br/>", "<br/>"))
    png = os.path.join(OUT, key + ".png")
    subprocess.run([EDGE, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=2",
                    "--virtual-time-budget=15000", "--window-size=2400,2400", f"--screenshot={png}",
                    "file:///" + html.replace(os.sep, "/")], capture_output=True, timeout=180)
    size = trim(png) if os.path.exists(png) else None
    os.remove(html)
    index.append({"key": key, "title": title, "png": png, "size": size, "mermaid": src})
    print(key, size)
json.dump(index, open(os.path.join(OUT, "index.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1)
