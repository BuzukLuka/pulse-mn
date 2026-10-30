from django.core.management.base import BaseCommand

from apps.accounts.models import Role, User
from apps.catalog.models import Category, District, Province

PROVINCES = {
    "Улаанбаатар": ["Баянгол", "Баянзүрх", "Сонгинохайрхан", "Сүхбаатар", "Хан-Уул", "Чингэлтэй"],
    "Архангай": ["Цэцэрлэг"], "Баян-Өлгий": ["Өлгий"], "Баянхонгор": ["Баянхонгор"],
    "Булган": ["Булган"], "Говь-Алтай": ["Алтай"], "Говьсүмбэр": ["Чойр"],
    "Дархан-Уул": ["Дархан"], "Дорноговь": ["Сайншанд"], "Дорнод": ["Хэрлэн"],
    "Дундговь": ["Мандалговь"], "Завхан": ["Улиастай"], "Орхон": ["Баян-Өндөр", "Жаргалант"],
    "Өвөрхангай": ["Арвайхээр"], "Өмнөговь": ["Даланзадгад"], "Сүхбаатар": ["Баруун-Урт"],
    "Сэлэнгэ": ["Сүхбаатар"], "Төв": ["Зуунмод"], "Увс": ["Улаангом"],
    "Ховд": ["Жаргалант"], "Хөвсгөл": ["Мөрөн"], "Хэнтий": ["Чингис"],
}
CATEGORIES = [
    ("population", "Хүн ам"), ("economy", "Эдийн засаг"), ("agriculture", "Хөдөө аж ахуй"),
    ("education", "Боловсрол"), ("health", "Эрүүл мэнд"), ("environment", "Байгаль орчин"),
    ("infrastructure", "Дэд бүтэц"), ("politics", "Улс төр"),
]
DEMO_USERS = [
    ("admin@pulse.mn", "Админ", Role.ADMIN),
    ("editor@pulse.mn", "Редактор Бат", Role.EDITOR),
    ("journalist@pulse.mn", "Сэтгүүлч Сараа", Role.JOURNALIST),
]


class Command(BaseCommand):
    help = "Аймаг, сум, ангилал болон туршилтын хэрэглэгчдийг үүсгэнэ"

    def add_arguments(self, parser):
        parser.add_argument("--password", default="Pulse12345!")
        parser.add_argument("--no-users", action="store_true")

    def handle(self, *args, **opts):
        for name, districts in PROVINCES.items():
            p, _ = Province.objects.get_or_create(name=name)
            for d in districts:
                District.objects.get_or_create(province=p, name=d)
        for slug, name in CATEGORIES:
            Category.objects.get_or_create(slug=slug, defaults={"name": name})
        if not opts["no_users"]:
            for email, name, role in DEMO_USERS:
                if not User.objects.filter(email=email).exists():
                    User.objects.create_user(email, opts["password"], full_name=name, role=role,
                                             is_staff=role == Role.ADMIN)
            self.stdout.write(f"Demo хэрэглэгчид: {[u[0] for u in DEMO_USERS]} / {opts['password']}")
        self.stdout.write(self.style.SUCCESS("Seed дууслаа"))
