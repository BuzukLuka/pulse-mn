"""Олон тооны ТУРШИЛТЫН (зохиомол) өгөгдөл: хэрэглэгч, мэдээ (бүх төлөв), амлалт, статистик, гомдол.

Бодит хүн, байгууллага, тоо БИШ. Бизнес логикийг (submit/decide/update_status) дамжуулж үүсгэдэг тул
Pulse Trust шалгалт, аудит, мэдэгдэл бүгд бодитоор бүрдэнэ. Дахин ажиллуулахад давхардуулахгүй.
    python manage.py seed_test --news 120
"""
import random
from datetime import timedelta

from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.accounts.models import Experience, PortfolioItem, Role, User
from apps.catalog.models import Category, District, Province
from apps.complaints.models import Complaint
from apps.content import services as cs
from apps.content.models import Content, ContentType, License
from apps.newsroom.models import Membership, Purchase, Rating
from apps.pledges.models import Pledge, PledgeStatus, Politician
from apps.pledges.services import update_status
from apps.statistics import services as st
from apps.statistics.models import DataSource, Indicator

SURNAMES = ["Бат", "Болд", "Ганбаатар", "Дорж", "Энх", "Мөнх", "Цэрэн", "Пүрэв", "Даваа", "Сүх", "Отгон", "Нямаа"]
NAMES = ["Сараа", "Тэмүүлэн", "Номин", "Ану", "Билгүүн", "Хулан", "Эрдэнэ", "Мишээл", "Түвшин", "Ундрал",
         "Гэрэл", "Хонгор", "Солонго", "Мөнхзул", "Төгөлдөр", "Оюун", "Ариунаа", "Батзориг", "Наран", "Золбоо"]
ORGS = ["Орон нутгийн мэдээ ТВ", "Говийн дуу сонин", "Хангай FM", "Баруун бүсийн мэдээ", "Чөлөөт сэтгүүлч",
        "Тал нутгийн хэвлэл", "Эко мэдээ сайт"]

# Ангилал бүрийн мэдээний загвар: (гарчиг, агуулга). {p} — аймаг, {d} — сум, {n} — тоо.
TEMPLATES = {
    "population": [
        ("{p} аймагт шилжин ирэгсдийн тоо {n} хувиар өслөө",
         "{p} аймгийн {d} суманд сүүлийн жилд шилжин ирж бүртгүүлсэн иргэдийн тоо {n} хувиар нэмэгджээ. "
         "Ажлын байр, сургууль цэцэрлэгийн хүртээмж сайжирсан нь гол шалтгаан гэж орон нутгийн удирдлага тайлбарлав."),
        ("{p}: шинэ төрсөн хүүхдийн тоо өмнөх оноос {n}-аар нэмэгдэв",
         "Аймгийн эрүүл мэндийн газрын мэдээллээр {d} суманд энэ онд {n} хүүхэд төржээ. "
         "Төрөх эмнэлгийн ачаалал нэмэгдсэн тул нэмэлт ор, эмч нарын хуваарийг шинэчлэх шаардлагатай байна."),
    ],
    "economy": [
        ("{p} аймагт жижиг дунд үйлдвэрлэлийн {n} төсөл санхүүжилт авлаа",
         "Жижиг дунд үйлдвэрийг хөгжүүлэх сангаас {p} аймгийн {n} аж ахуйн нэгжид хөнгөлөлттэй зээл олгожээ. "
         "Төслүүдийн ихэнх нь ноос ноолуур, сүү боловсруулах, барилгын материалын чиглэлийнх."),
        ("{d} суманд шинэ худалдааны төв ашиглалтад орж, {n} ажлын байр бий болов",
         "{p} аймгийн {d} суманд орон нутгийн хөрөнгө оруулагчдын санхүүжилтээр худалдааны төв нээгдлээ. "
         "Нийт {n} хүн байнгын ажлын байртай болсон бөгөөд ихэнх нь залуучууд аж."),
    ],
    "agriculture": [
        ("{p} аймагт өвс тэжээлийн нөөц {n} тонноор нэмэгдлээ",
         "Өвөлжилтийн бэлтгэл хангах ажлын хүрээнд {p} аймгийн {d} суманд өвс тэжээлийн улсын нөөцийг {n} тонноор нэмжээ. "
         "Малчид бэлчээрийн доройтлоос болж тэжээлийн хэрэгцээ өсч байгааг онцолж байна."),
        ("{d} суманд {n} малчин өрх хоршоо байгуулав",
         "{p} аймгийн {d} сумын {n} малчин өрх нэгдэж, сүү, ноос борлуулах хоршоо байгууллаа. "
         "Хоршоо нь зуучлагчгүйгээр бүтээгдэхүүнээ шууд үйлдвэрт нийлүүлэх зорилготой."),
    ],
    "education": [
        ("{p} аймгийн {n} сургуульд STEM лаборатори байгуулав",
         "Боловсролын яамны хөтөлбөрийн хүрээнд {p} аймгийн {n} ерөнхий боловсролын сургуульд STEM лаборатори байгуулжээ. "
         "Багш нарыг тоног төхөөрөмж ашиглах сургалтад хамруулсан байна."),
        ("{d} суманд {n} хүүхдийн цэцэрлэгийн барилга баригдаж эхэллээ",
         "{p} аймгийн {d} суманд {n} хүүхдийн суудалтай цэцэрлэгийн барилгын шав тавигдлаа. "
         "Одоогоор цэцэрлэгт хамрагдаж чадахгүй байгаа хүүхдийн тоо хамгийн өндөр сумдын нэг юм."),
    ],
    "health": [
        ("{p} аймгийн нэгдсэн эмнэлэгт {n} шинэ эмч томилогдлоо",
         "Эрүүл мэндийн салбарын хүний нөөцийн дутагдлыг шийдэх зорилгоор {p} аймагт {n} залуу эмч томилогдон ажиллаж эхэллээ. "
         "Тэдэнд орон сууцны хөнгөлөлт үзүүлэхээр болжээ."),
        ("{d} суманд урьдчилан сэргийлэх үзлэгт {n} иргэн хамрагдав",
         "{p} аймгийн {d} суманд зохион байгуулсан үнэ төлбөргүй урьдчилан сэргийлэх үзлэгт {n} иргэн хамрагдсан байна. "
         "Үзлэгээр илэрсэн өвчлөлийг эрт эмчлэх төлөвлөгөө гаргажээ."),
    ],
    "environment": [
        ("{p} аймагт {n} га газарт мод тарилаа",
         "«Тэрбум мод» үндэсний хөдөлгөөний хүрээнд {p} аймгийн {d} орчимд {n} га талбайд мод тарьжээ. "
         "Суулгацыг дуслын усалгааны системтэй холбосон нь ургах чадварыг нэмэгдүүлнэ."),
        ("{d} суманд хог ангилан ялгах {n} цэг байршууллаа",
         "{p} аймгийн {d} суманд хуванцар, шил, цаас ангилан ялгах {n} цэгийг байршуулав. "
         "Иргэдэд зориулсан сурталчилгааны ажлыг сургуулиудтай хамтран зохион байгуулж байна."),
    ],
    "infrastructure": [
        ("{p} аймагт {n} км хатуу хучилттай зам ашиглалтад орлоо",
         "{p} аймгийн төвөөс {d} сум хүртэлх {n} км хатуу хучилттай авто замыг ашиглалтад орууллаа. "
         "Зорчих хугацаа бараг хоёр дахин богиносно гэж тооцоолж байна."),
        ("{d} суманд {n} өрхийг төвийн дулаанд холбов",
         "{p} аймгийн {d} суманд дулааны шугам сүлжээг өргөтгөж, нэмэлт {n} өрхийг төвийн дулаанд холболоо. "
         "Ингэснээр агаарын бохирдлыг бууруулахад хувь нэмэр оруулна."),
    ],
    "politics": [
        ("{p} аймгийн ИТХ-ын хуралдаанаар {n} асуудал хэлэлцэв",
         "{p} аймгийн иргэдийн төлөөлөгчдийн хурлын ээлжит хуралдаанаар орон нутгийн төсвийн гүйцэтгэл зэрэг {n} асуудлыг хэлэлцлээ. "
         "Хуралдааныг анх удаа олон нийтэд шууд дамжуулжээ."),
        ("{d} сумын иргэдийн нийтийн хуралд {n} иргэн оролцов",
         "{p} аймгийн {d} сумын иргэдийн нийтийн хурлаар ирэх оны хөрөнгө оруулалтын саналыг хэлэлцлээ. "
         "Нийт {n} иргэн оролцож, зам, худаг, цэцэрлэгийн асуудлыг тэргүүн ээлжинд тавьжээ."),
    ],
}
EXTRA = [
    "Орон нутгийн удирдлагын мэдээлснээр ажлын явцыг улирал тутам олон нийтэд тайлагнана.",
    "Иргэд санал хүсэлтээ сумын Засаг даргын Тамгын газарт гаргах боломжтой.",
    "Мэргэжилтнүүд энэ арга хэмжээг бусад аймагт ч хэрэгжүүлэх нь зүйтэй гэж үзэж байна.",
    "Төслийн дараагийн шат ирэх онд эхэлнэ.",
]
POSITIONS = ["Аймгийн засаг дарга", "Аймгийн ИТХ-ын дарга", "Сумын засаг дарга", "УИХ-ын гишүүн"]
PARTIES = ["Нам А (зохиомол)", "Нам Б (зохиомол)", "Бие даагч"]
PLEDGES = {
    "infrastructure": ["Аймгийн төвд {n} км авто зам шинээр тавина.", "{n} өрхийг төвийн дулаанд холбоно."],
    "education": ["{n} хүүхдийн цэцэрлэг шинээр барина.", "Сургууль бүрийг өндөр хурдны интернэтэд холбоно."],
    "health": ["Сум бүрт түргэн тусламжийн машин нийлүүлнэ.", "Аймгийн эмнэлэгт {n} ортой шинэ тасаг нээнэ."],
    "agriculture": ["{n} инженерийн хийцтэй худаг гаргана.", "Малчдад зориулсан ноосны урамшууллыг нэмэгдүүлнэ."],
    "environment": ["{n} га талбайд ой мод тарина.", "Хог хаягдлын шинэ төвлөрсөн цэг байгуулна."],
}
COMPLAINTS = [("wrong", "Мэдээнд дурдсан тоо албан ёсны мэдээлэлтэй зөрж байна."),
              ("duplicate", "Энэ мэдээ өөр сайтад өмнө нь нийтлэгдсэн байсан."),
              ("privacy", "Зурган дээр хүүхдийн нүүр бүдгэрүүлээгүй байна."),
              ("other", "Гарчиг агуулгаасаа хэт сенсаац хөөсөн байна."),
              ("copyright", "Зургийг зохиогчийн зөвшөөрөлгүй ашигласан.")]
CHECKLIST = {"facts": True, "source": True, "rights": True, "privacy": True, "tone": True}
PASSWORD = "Pulse12345!"


class Command(BaseCommand):
    help = "Олон тооны туршилтын (зохиомол) өгөгдөл үүсгэнэ."

    def add_arguments(self, parser):
        parser.add_argument("--news", type=int, default=120, help="Үүсгэх мэдээний тоо")
        parser.add_argument("--seed", type=int, default=2026, help="Санамсаргүй тооны үр (давтагдах үр дүн)")
        parser.add_argument("--only", default="", help="Таслалаар: news,pledges,stats,complaints,network (хоосон бол бүгд). "
                                                       "Serverless-д хугацаа хэтрэхээс сэргийлж хэсэгчлэн ажиллуулна.")

    def handle(self, *a, **o):
        parts = set(filter(None, o["only"].split(","))) or {"news", "pledges", "stats", "complaints", "network"}
        if parts & {"pledges", "stats"} or not Province.objects.exists():
            call_command("seed_demo", verbosity=0)  # удаан тул шаардлагатай үед л
        self.rng = random.Random(o["seed"])
        self.provinces = list(Province.objects.prefetch_related("districts"))
        self.cats = {c.slug: c for c in Category.objects.all()}
        self.admin = User.objects.filter(role=Role.ADMIN).first()

        journalists, editors, citizens = self.users()
        made = self.news(journalists, editors, o["news"]) if "news" in parts else 0
        pols = self.pledges() if "pledges" in parts else Politician.objects.count()
        if "stats" in parts:
            self.stats()
        if "complaints" in parts:
            self.complaints(citizens)
        if "network" in parts:
            self.network(journalists, citizens)
        self.stdout.write(self.style.SUCCESS(
            f"seed_test дууслаа: {User.objects.count()} хэрэглэгч, {Content.objects.count()} контент (+{made}), "
            f"{pols} албан тушаалтан, {Complaint.objects.count()} гомдол. Нууц үг: {PASSWORD}"))

    # ---------- Хэрэглэгчид ----------
    def user(self, i, role, prefix):
        email = f"{prefix}{i}@test.pulse.mn"
        u = User.objects.filter(email=email).first()
        if u:
            return u, False
        prov = self.rng.choice(self.provinces)
        return User.objects.create_user(
            email, PASSWORD, role=role, full_name=f"{self.rng.choice(SURNAMES)[0]}. {NAMES[i % len(NAMES)]}",
            phone=f"9{self.rng.randint(1000000, 9999999)}", organization=self.rng.choice(ORGS) if role != Role.CITIZEN else "",
            province=prov, bio="Туршилтын (зохиомол) хэрэглэгч.", is_verified=role == Role.JOURNALIST and i % 3 != 0,
            show_org=True), True

    def users(self):
        journalists, editors, citizens = [], [], []
        for i in range(1, 13):
            u, new = self.user(i, Role.JOURNALIST, "journalist")
            journalists.append(u)
            if new:
                Experience.objects.create(user=u, organization=self.rng.choice(ORGS), position="Сурвалжлагч",
                                          period=f"{2015 + i % 6}–одоо")
                for k in range(self.rng.randint(1, 4)):
                    PortfolioItem.objects.create(user=u, title=f"Сурвалжилга №{k + 1} (демо)", kind=self.rng.choice(
                        ["news", "article", "photo", "video"]), year=2021 + k % 5)
        editors = [self.user(i, Role.EDITOR, "editor")[0] for i in range(1, 5)]
        citizens = [self.user(i, Role.CITIZEN, "citizen")[0] for i in range(1, 21)]
        for i in range(1, 4):
            u, _ = self.user(i, Role.NEWSROOM, "newsroom")
            if u.full_name != ORGS[i]:
                u.full_name, u.organization, u.is_verified = ORGS[i], ORGS[i], True
                u.bio = "Туршилтын (зохиомол) редакц."
                u.save(update_fields=["full_name", "organization", "is_verified", "bio"])
        User.objects.filter(email="journalist@pulse.mn").update(is_verified=True)
        return journalists, editors, citizens

    # ---------- Мэдээ (бүх төлөв) ----------
    def news(self, journalists, editors, total):
        have = Content.objects.filter(author__email__endswith="@test.pulse.mn").count()
        today = timezone.localdate()
        made = 0
        for k in range(have, total):
            slug = self.rng.choice(list(TEMPLATES))
            title_t, body_t = self.rng.choice(TEMPLATES[slug])
            prov = self.rng.choice(self.provinces)
            dist = self.rng.choice(list(prov.districts.all()) or [None])
            n = self.rng.choice([3, 5, 8, 12, 15, 20, 25, 40, 60, 120, 250])
            fmt = {"p": prov.name, "d": dist.name if dist else prov.name, "n": n}
            body = body_t.format(**fmt) + "\n\n" + " ".join(self.rng.sample(EXTRA, 2))
            days_ago = self.rng.randint(1, 120)
            author = self.rng.choice(journalists)
            c = Content.objects.create(
                author=author, title=title_t.format(**fmt)[:250], body=body, category=self.cats[slug], province=prov,
                district=dist, event_date=today - timedelta(days=days_ago), source=f"{self.rng.choice(ORGS)} (демо)",
                tags=["демо", self.cats[slug].name.lower(), prov.name.lower()],
                content_type=self.rng.choice([ContentType.NEWS] * 4 + [ContentType.ARTICLE, ContentType.PHOTO]),
                license=self.rng.choice(list(License.values)), copyright_declared=True,
                location_detail=f"{dist.name if dist else prov.name} төв")
            roll = self.rng.random()
            if roll < 0.06 or not author.is_verified:   # ноорог хэвээр (баталгаажаагүй бол илгээх боломжгүй)
                pass
            else:
                cs.submit(c, author)
                ed = self.rng.choice(editors)
                if roll < 0.16:                   # шалгалт хүлээж буй
                    pass
                elif roll < 0.24:
                    cs.decide(c, ed, "return", "Эх сурвалжийн холбоос, албан ёсны тоог нэмж оруулна уу.", CHECKLIST)
                elif roll < 0.29:
                    cs.decide(c, ed, "reject", "Баримтаар нотлогдоогүй тул нийтлэх боломжгүй.", CHECKLIST)
                else:
                    cs.decide(c, ed, "approve", "", CHECKLIST)
                    if roll > 0.98:
                        cs.set_visibility(c, self.admin, True, "Гомдлын дагуу түр нуусан (демо).")
            # Он сар өдрийг тараана (нүүр хуудсанд бодитой харагдуулах).
            when = timezone.now() - timedelta(days=days_ago - 1, hours=self.rng.randint(0, 23))
            Content.objects.filter(pk=c.pk).update(created_at=when, **(
                {"published_at": when + timedelta(hours=6)} if c.published_at else {}))
            made += 1
        return made

    # ---------- Амлалт ----------
    def pledges(self):
        for i in range(1, 11):
            prov = self.provinces[(i * 3) % len(self.provinces)]
            pol, _ = Politician.objects.get_or_create(
                name=f"{SURNAMES[i % len(SURNAMES)][0]}. {NAMES[(i + 7) % len(NAMES)]} (зохиомол)",
                position=POSITIONS[i % len(POSITIONS)], term_year=2024,
                defaults={"party": PARTIES[i % len(PARTIES)], "province": prov})
            if pol.pledges.exists():
                continue
            for slug in self.rng.sample(list(PLEDGES), 4):
                text = self.rng.choice(PLEDGES[slug]).format(n=self.rng.choice([5, 10, 20, 50, 100]))
                p = Pledge.objects.create(politician=pol, text=text, category=self.cats[slug],
                                          source="Сонгуулийн мөрийн хөтөлбөр (демо)", created_by=self.admin)
                status = self.rng.choice(list(PledgeStatus.values))
                if status != PledgeStatus.INSUFFICIENT:
                    update_status(p, self.admin, status, "Тайлангаар баталгаажсан (демо)",
                                  {"source": f"{prov.name} аймгийн ЗДТГ-ын тайлан (демо)",
                                   "date": f"2025-{self.rng.randint(1, 12):02d}-15"})
        return Politician.objects.count()

    # ---------- Статистик: бүх аймаг, 2020–2024 ----------
    def stats(self):
        src = DataSource.objects.filter(name__contains="ЗОХИОМОЛ").first()
        rows = [("Хүн амын тоо", "хүн", "population", 60000), ("Малын тоо", "толгой", "agriculture", 2000000),
                ("Сургуулийн тоо", "сургууль", "education", 25), ("Ажилгүйдлийн түвшин", "%", "economy", 8),
                ("Эмнэлгийн орны тоо", "ор", "health", 400), ("Хатуу хучилттай зам", "км", "infrastructure", 150)]
        for name, unit, slug, base in rows:
            ind, _ = Indicator.objects.get_or_create(name=name, defaults={
                "aliases": name.lower(), "unit": unit, "category": self.cats[slug], "source": src})
            for prov in self.provinces:
                scale = 18 if prov.name == "Улаанбаатар" and unit not in ("%",) else self.rng.uniform(0.6, 1.5)
                for y in range(2020, 2025):
                    if ind.values.filter(province=prov, year=y).exists():
                        continue
                    v = base * scale * (1 + 0.025 * (y - 2020)) * self.rng.uniform(0.97, 1.03)
                    st.set_value(self.admin, ind, prov, y, round(v, 1) if unit == "%" else round(v), "Туршилтын өгөгдөл")
            for y in range(2020, 2025):
                if not ind.values.filter(province__isnull=True, year=y).exists():
                    vals = [float(x) for x in ind.values.filter(year=y, province__isnull=False).values_list("value", flat=True)]
                    if vals:
                        total = sum(vals) / len(vals) if unit == "%" else sum(vals)
                        st.set_value(self.admin, ind, None, y, round(total, 1), "Туршилтын өгөгдөл (улсын)")

    # ---------- Гомдол ----------
    def complaints(self, citizens):
        if Complaint.objects.filter(reporter__email__endswith="@test.pulse.mn").exists():
            return
        published = list(Content.objects.filter(status="published").values_list("id", flat=True)[:40])
        pledges = list(Pledge.objects.values_list("id", flat=True)[:20])
        for i in range(25):
            kind, text = self.rng.choice(COMPLAINTS)
            target_type, ids = ("pledge", pledges) if i % 5 == 0 and pledges else ("content", published)
            if not ids:
                continue
            status = self.rng.choice(["open", "open", "resolved", "dismissed"])
            Complaint.objects.create(
                reporter=self.rng.choice(citizens), target_type=target_type, target_id=self.rng.choice(ids), kind=kind,
                text=text, status=status, resolution="Шалгаад зассан (демо)." if status == "resolved" else "",
                resolved_by=self.admin if status != "open" else None,
                resolved_at=timezone.now() if status != "open" else None)

    # ---------- Редакц ↔ сэтгүүлч, үнэлгээ, ДЕМО төлбөр ----------
    # Хэсэг бүр өөрөө давхардлаа шалгадаг тул тасарвал дахин ажиллуулахад үргэлжилнэ.
    def network(self, journalists, citizens):
        newsrooms = list(User.objects.filter(role=Role.NEWSROOM, email__endswith="@test.pulse.mn").order_by("email"))
        if not newsrooms:
            return
        demo = User.objects.filter(email="journalist@pulse.mn").first()
        for k, j in enumerate(journalists + ([demo] if demo else [])):
            nr = newsrooms[(k // 2) % len(newsrooms)]  # баталгаажсан/үгүйг редакц бүрт холино
            status = "pending" if k % 5 == 4 else "active"
            m, made = Membership.objects.get_or_create(journalist=j, newsroom=nr, defaults={
                "status": status, "message": "Хамтран ажиллах хүсэлт (демо)",
                "decided_at": timezone.now() if status == "active" else None})
            if not made or status != "active":
                continue
            mine = list(Content.objects.filter(author=j).exclude(status="draft").values_list("pk", "status"))
            Content.objects.filter(pk__in=[pk for pk, _ in mine[::2]]).update(newsroom=nr)
            Content.objects.filter(pk__in=[pk for pk, st in mine if st == "published"][:2]).update(
                price=self.rng.choice([15000, 25000, 40000, 60000]))
        if not Purchase.objects.filter(invoice_code__startswith="PMN-DEMO").exists():
            Purchase.objects.bulk_create([
                Purchase(content=c, buyer=self.rng.choice(newsrooms), amount=c.price, invoice_code=f"PMN-DEMO{c.pk:04d}",
                         status=self.rng.choice(["paid", "paid", "pending"]), paid_at=timezone.now())
                for c in Content.objects.filter(price__gt=0, status="published")[:8]])
        raters = citizens[:10] + newsrooms
        if not Rating.objects.filter(rater__in=raters).exists():
            comments = ["Баримттай, цаг алдалгүй сурвалжилдаг.", "Эх сурвалжаа тодорхой заадаг.",
                        "Зарим мэдээ засвар шаардсан.", "Хамтран ажиллахад найдвартай.", "Сайн, гэхдээ илүү гүнзгий байж болно."]
            Rating.objects.bulk_create([
                Rating(rater=r, target=t, score=self.rng.choice([3, 4, 4, 5, 5]), comment=self.rng.choice(comments))
                for t in journalists + newsrooms for r in self.rng.sample(raters, 4) if r.pk != t.pk], ignore_conflicts=True)
