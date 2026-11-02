from datetime import date

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from rest_framework.test import APITestCase

from apps.accounts.models import Role, User
from apps.catalog.models import Category, Province
from apps.content.models import Content, Status
from apps.pledges.models import Pledge

PW = "Pulse12345!"
BODY = ("Дорноговь аймагт малын тоо 3 сая толгой боллоо гэж албаны хүн мэдэгдлээ. Бэлчээрийн даацыг "
        "тооцож, малчдад дэмжлэг үзүүлэх ажил эхэллээ. Холбоо барих утас 99112233.")


class TrustTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_demo", verbosity=0)
        cls.j = User.objects.create_user("j@t.mn", PW, role=Role.JOURNALIST, is_verified=True)
        cls.e = User.objects.create_user("e@t.mn", PW, role=Role.EDITOR)

    def login(self, email):
        r = self.client.post("/api/v1/auth/login/", {"email": email, "password": PW}, format="json")
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + r.data["access"])

    def mk(self, **kw):
        d = dict(author=self.j, title="Малын тоо нэмэгдлээ", body=BODY, source="Аймгийн ХАА газар",
                 category=Category.objects.get(slug="agriculture"), province=Province.objects.get(name="Дорноговь"),
                 event_date=date.today(), copyright_declared=True)
        d.update(kw)
        return Content.objects.create(**d)

    def test_claim_mismatch_and_pii(self):
        from apps.ai.checks import run_checks
        res = run_checks(self.mk())
        by = {c["key"]: c for c in res["checks"]}
        self.assertEqual(by["claims"]["status"], "warn")      # 3 сая vs 2.1 сая
        self.assertTrue(by["claims"]["items"][0]["mismatch"])
        self.assertEqual(by["pii"]["status"], "warn")
        self.assertLess(res["score"], 100)

    def test_text_duplicate_flagged(self):
        from apps.ai.checks import duplicate_items
        self.mk(status=Status.PUBLISHED)
        d = self.mk()
        items = duplicate_items(d)
        self.assertTrue(items and items[0]["similarity"] >= 0.85)

    def test_image_phash_duplicate(self):
        import io
        from PIL import Image
        from apps.content.services import save_media
        from apps.ai.checks import media_duplicates

        base = Image.new("RGB", (64, 48))
        base.putdata([((x % 64) * 4 if (x // 64) % 16 < 8 else 255 - (x % 64) * 4, (x // 64) * 5, 90)
                      for x in range(64 * 48)])

        def png(size):
            b = io.BytesIO(); base.resize(size).save(b, "PNG")
            return SimpleUploadedFile("a.png", b.getvalue(), "image/png")
        a, b = self.mk(status=Status.PUBLISHED), self.mk()
        save_media(a, png((120, 90))); save_media(b, png((240, 180)))   # өөр хэмжээтэй ч төстэй
        self.assertTrue(media_duplicates(b))

    def test_submit_stores_verification_and_version(self):
        self.login("j@t.mn")
        c = self.mk()
        r = self.client.post(f"/api/v1/content/{c.pk}/submit/")
        self.assertEqual(r.status_code, 200, r.content)
        self.assertIn("score", r.data["verification"])
        self.assertEqual(c.versions.count(), 1)

    def test_publish_requires_checklist_and_public_trust(self):
        c = self.mk(status=Status.UNDER_REVIEW)
        self.login("e@t.mn")
        r = self.client.post(f"/api/v1/review/{c.pk}/decide/",
                             {"decision": "approve", "checklist": {"facts": True}}, format="json")
        self.assertEqual(r.status_code, 422)
        r = self.client.post(f"/api/v1/review/{c.pk}/decide/",
                             {"decision": "approve", "checklist": {"facts": True, "source": True, "rights": True}}, format="json")
        self.assertEqual(r.status_code, 200, r.content)
        self.client.credentials()
        r = self.client.get(f"/api/v1/news/{c.pk}/")
        self.assertIn("trust", r.data); self.assertNotIn("verification", r.data)
