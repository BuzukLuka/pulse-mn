"""Туршилтын (зохиомол) өгөгдөл: албан ёсны үзүүлэлт, улс төрч, амлалт. Бодит тоо БИШ."""
from django.core.management import call_command
from django.core.management.base import BaseCommand

from apps.accounts.models import Role, User
from apps.catalog.models import Category, Province
from apps.pledges.models import Pledge, Politician
from apps.pledges.services import update_status
from apps.statistics import services as st
from apps.statistics.models import DataSource, Indicator


class Command(BaseCommand):
    help = "Demo өгөгдөл (зохиомол) үүсгэнэ. Урьдчилан `seed` ажилласан байх ёстой."

    def handle(self, *a, **o):
        call_command("seed", verbosity=0)
        admin = User.objects.filter(role=Role.ADMIN).first()
        cat = lambda s: Category.objects.get(slug=s)
        src, _ = DataSource.objects.get_or_create(name="Үндэсний статистикийн хороо (ЗОХИОМОЛ ДЕМО)",
                                                  defaults={"kind": "manual", "frequency": "yearly"})
        rows = [("Хүн амын тоо", "хүн ам", "хүн", "population", {"Дорноговь": 75000, "Дундговь": 46000}),
                ("Малын тоо", "мал сүрэг", "толгой", "agriculture", {"Дорноговь": 2100000, "Дундговь": 2600000}),
                ("Сургуулийн тоо", "ерөнхий боловсролын сургууль", "сургууль", "education", {"Дорноговь": 28, "Дундговь": 22})]
        for name, aliases, unit, c, vals in rows:
            ind, _ = Indicator.objects.get_or_create(name=name, defaults={
                "aliases": aliases, "unit": unit, "category": cat(c), "source": src})
            for prov, v in vals.items():
                for y, k in ((2023, 0.97), (2024, 1.0)):
                    if not ind.values.filter(province__name=prov, year=y).exists():
                        st.set_value(admin, ind, Province.objects.get(name=prov), y, round(v * k), "Demo өгөгдөл")
            for y, k in ((2023, 0.97), (2024, 1.0)):   # улсын дүн (зохиомол)
                if not ind.values.filter(province__isnull=True, year=y).exists():
                    st.set_value(admin, ind, None, y, round(sum(vals.values()) * 8 * k), "Demo өгөгдөл (улсын)")
        pol, _ = Politician.objects.get_or_create(
            name="Б. Демо (зохиомол)", position="Аймгийн засаг дарга", term_year=2024,
            defaults={"party": "Бие даагч", "province": Province.objects.get(name="Дорноговь")})
        for text, status in [("Аймгийн төвийн 10 км замыг 2026 онд асфальтжуулна.", "in_progress"),
                             ("Сум бүрт цэцэрлэг шинээр барина.", "insufficient"),
                             ("Малчдын бэлчээрийн даацыг тооцож, зургийн сан үүсгэнэ.", "fulfilled")]:
            p, made = Pledge.objects.get_or_create(politician=pol, text=text, defaults={
                "category": cat("infrastructure"), "source": "Сонгуулийн мөрийн хөтөлбөр (демо)"})
            if made and status != "insufficient":
                update_status(p, admin, status, "Demo анхны төлөв", {"source": "Аймгийн ТЗГ-ын тайлан (демо)", "date": "2025-12-01"})
        self.stdout.write("seed_demo дууслаа (зохиомол өгөгдөл)")
