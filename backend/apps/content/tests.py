from datetime import date

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from rest_framework.test import APITestCase

from apps.accounts.models import Role, User
from apps.audit.models import AuditLog
from apps.catalog.models import Category, Province
from apps.content.models import Content, Status
from apps.notifications.models import Notification

PW = "Pulse12345!"
BODY = "Дорноговь аймагт малчдын бэлчээрийн даацыг тооцож, ган зудын эрсдэлийг бууруулах ажил эхэллээ. " * 2


class WorkflowTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed", "--no-users", verbosity=0)
        cls.journalist = User.objects.create_user("j@t.mn", PW, role=Role.JOURNALIST, full_name="Ж", is_verified=True)
        cls.editor = User.objects.create_user("e@t.mn", PW, role=Role.EDITOR)
        cls.admin = User.objects.create_user("a@t.mn", PW, role=Role.ADMIN)

    def login(self, email):
        r = self.client.post("/api/v1/auth/login/", {"email": email, "password": PW}, format="json")
        self.assertEqual(r.status_code, 200, r.content)
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + r.data["access"])

    def payload(self, **kw):
        d = {"title": "Бэлчээрийн даац тооцоолол", "body": BODY,
             "category": Category.objects.get(slug="agriculture").pk,
             "province": Province.objects.get(name="Дорноговь").pk,
             "event_date": date.today().isoformat(), "source": "Аймгийн ХАА газар", "copyright_declared": True}
        d.update(kw)
        return d

    def test_uc01_validation_400_then_submit(self):
        self.login("j@t.mn")
        r = self.client.post("/api/v1/content/", {"title": "Ноорог гарчиг"}, format="json")
        self.assertEqual(r.status_code, 201)
        cid = r.data["id"]
        r = self.client.post(f"/api/v1/content/{cid}/submit/")
        self.assertEqual(r.status_code, 400)
        self.assertIn("body", r.data); self.assertIn("source", r.data)
        self.client.patch(f"/api/v1/content/{cid}/", self.payload(), format="json")
        r = self.client.post(f"/api/v1/content/{cid}/submit/")
        self.assertEqual(r.status_code, 200, r.content)
        self.assertEqual(r.data["status"], Status.UNDER_REVIEW)
        self.assertTrue(AuditLog.objects.filter(action="content.submit").exists())
        self.assertEqual(Notification.objects.filter(user=self.editor).count(), 1)
        # илгээсний дараа засах боломжгүй (409)
        r = self.client.patch(f"/api/v1/content/{cid}/", {"title": "Өөр гарчиг"}, format="json")
        self.assertEqual(r.status_code, 409)

    def test_media_upload_and_duplicate_detection(self):
        self.login("j@t.mn")
        ids = []
        for title in ("Нэгдүгээр мэдээ", "Хоёрдугаар мэдээ гэж өөр"):
            cid = self.client.post("/api/v1/content/", self.payload(title=title), format="json").data["id"]
            f = SimpleUploadedFile("a.jpg", b"same-bytes", content_type="image/jpeg")
            r = self.client.post(f"/api/v1/content/{cid}/media/", {"file": f}, format="multipart")
            self.assertEqual(r.status_code, 201, r.content)
            self.client.post(f"/api/v1/content/{cid}/submit/")
            ids.append(cid)
        bad = SimpleUploadedFile("x.exe", b"MZ")
        r = self.client.post(f"/api/v1/content/{ids[0]}/media/", {"file": bad}, format="multipart")
        self.assertEqual(r.status_code, 409)  # илгээсэн тул засах боломжгүй
        self.login("e@t.mn")
        r = self.client.get(f"/api/v1/review/{ids[1]}/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["duplicates"][0]["id"], ids[0])
        self.assertEqual([c["id"] for c in self.client.get("/api/v1/review/").data["results"]], ids)

    def _submitted(self):
        self.login("j@t.mn")
        cid = self.client.post("/api/v1/content/", self.payload(), format="json").data["id"]
        self.client.post(f"/api/v1/content/{cid}/submit/")
        return cid

    def test_uc02_decide_rules(self):
        cid = self._submitted()
        self.login("j@t.mn")  # сэтгүүлч шийдвэр гаргаж чадахгүй
        self.assertEqual(self.client.post(f"/api/v1/review/{cid}/decide/", {"decision": "approve"}).status_code, 403)
        self.login("e@t.mn")
        r = self.client.post(f"/api/v1/review/{cid}/decide/", {"decision": "reject", "reason": " "}, format="json")
        self.assertEqual(r.status_code, 422)  # шалтгаан заавал
        r = self.client.post(f"/api/v1/review/{cid}/decide/", {"decision": "return", "reason": "Эх сурвалж тодруулна уу"}, format="json")
        self.assertEqual(r.data["status"], Status.CHANGES_REQUESTED)
        # сэтгүүлч засаад дахин илгээнэ
        self.login("j@t.mn")
        self.assertEqual(self.client.get(f"/api/v1/content/{cid}/").data["review_reason"], "Эх сурвалж тодруулна уу")
        self.assertEqual(self.client.post(f"/api/v1/content/{cid}/submit/").status_code, 200)
        self.login("e@t.mn")
        r = self.client.post(f"/api/v1/review/{cid}/decide/", {"decision": "approve"}, format="json")
        self.assertEqual(r.data["status"], Status.PUBLISHED)
        self.assertEqual(self.client.post(f"/api/v1/review/{cid}/decide/", {"decision": "approve"}, format="json").status_code, 409)
        self.assertEqual(AuditLog.objects.filter(entity_type="content", entity_id=str(cid)).count(), 4)
        # нийтэд харагдана, дотоод талбаргүй
        self.client.credentials()
        pub = self.client.get("/api/v1/news/").data["results"]
        self.assertEqual(len(pub), 1)
        self.assertNotIn("ai_review", pub[0])
        self.assertEqual(len(self.client.get("/api/v1/news/?q=бэлчээр").data["results"]), 1)

    def test_ai_fallback_rules(self):
        cid = self._submitted()
        self.login("e@t.mn")
        r = self.client.post(f"/api/v1/review/{cid}/ai-check/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["source"], "rules")  # GEMINI_API_KEY тохируулаагүй
        self.login("j@t.mn")
        r = self.client.post("/api/v1/content/suggest-tags/", {"title": "Зам барилга", "body": "Шинэ зам, гүүр барилгын ажил эхэллээ дэд бүтэц"}, format="json")
        self.assertEqual(r.data["category"], "infrastructure")


class AdminTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed", "--no-users", verbosity=0)
        cls.admin = User.objects.create_user("a@t.mn", PW, role=Role.ADMIN)
        cls.j = User.objects.create_user("j@t.mn", PW, role=Role.JOURNALIST, is_verified=True)

    def login(self, email):
        r = self.client.post("/api/v1/auth/login/", {"email": email, "password": PW}, format="json")
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + r.data["access"])
        return r.data

    def test_uc03_access_change(self):
        self.login("a@t.mn")
        url = f"/api/v1/admin/users/{self.j.pk}/"
        self.assertEqual(self.client.patch(url, {"role": "editor"}, format="json").status_code, 422)
        r = self.client.patch(url, {"role": "editor", "reason": "Дэвшүүлсэн"}, format="json")
        self.assertEqual(r.status_code, 200); self.assertEqual(r.data["role"], "editor")
        log = AuditLog.objects.get(action="user.update_access")
        self.assertEqual((log.before["role"], log.after["role"]), ("journalist", "editor"))

    def test_last_admin_protected_409(self):
        self.login("a@t.mn")
        url = f"/api/v1/admin/users/{self.admin.pk}/"
        r = self.client.patch(url, {"role": "citizen", "reason": "тест"}, format="json")
        self.assertEqual(r.status_code, 409)
        r = self.client.patch(url, {"is_active": False, "reason": "тест"}, format="json")
        self.assertEqual(r.status_code, 409)

    def test_deactivated_user_cannot_login_and_sessions_revoked(self):
        tokens = self.login("j@t.mn")
        self.login("a@t.mn")
        self.client.patch(f"/api/v1/admin/users/{self.j.pk}/", {"is_active": False, "reason": "Зөрчил"}, format="json")
        self.client.credentials()
        self.assertEqual(self.client.post("/api/v1/auth/refresh/", {"refresh": tokens["refresh"]}, format="json").status_code, 401)
        self.assertEqual(self.client.post("/api/v1/auth/login/", {"email": "j@t.mn", "password": PW}, format="json").status_code, 401)

    def test_non_admin_forbidden(self):
        self.login("j@t.mn")
        self.assertEqual(self.client.get("/api/v1/admin/users/").status_code, 403)
        self.assertEqual(self.client.get("/api/v1/admin/audit/").status_code, 403)

    def test_register_cannot_pick_admin_role(self):
        r = self.client.post("/api/v1/auth/register/", {"email": "n@t.mn", "password": PW, "role": "admin"}, format="json")
        self.assertEqual(r.status_code, 400)
        r = self.client.post("/api/v1/auth/register/", {"email": "n@t.mn", "password": PW, "role": "journalist"}, format="json")
        self.assertEqual(r.status_code, 201)
