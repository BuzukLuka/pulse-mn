from datetime import date

from django.core.management import call_command
from rest_framework.test import APITestCase

from apps.accounts.models import Role, User
from apps.catalog.models import Category, Province
from apps.content.models import Content
from apps.newsroom.models import Membership, Purchase
from apps.notifications.models import Notification

PW = "Pulse12345!"
BODY = "Дорноговь аймагт малчдын бэлчээрийн даацыг тооцож, ган зудын эрсдэлийг бууруулах ажил эхэллээ. " * 2


class NewsroomFlowTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed", "--no-users", verbosity=0)
        cls.j = User.objects.create_user("j@t.mn", PW, role=Role.JOURNALIST, full_name="Сэтгүүлч")
        cls.nr = User.objects.create_user("n@t.mn", PW, role=Role.NEWSROOM, full_name="Редакц")
        cls.ed = User.objects.create_user("e@t.mn", PW, role=Role.EDITOR)
        cls.admin = User.objects.create_user("a@t.mn", PW, role=Role.ADMIN)
        cls.citizen = User.objects.create_user("c@t.mn", PW, role=Role.CITIZEN)

    def login(self, email):
        r = self.client.post("/api/v1/auth/login/", {"email": email, "password": PW}, format="json")
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + r.data["access"])

    def draft(self, **kw):
        d = {"title": "Бэлчээрийн даац тооцоолол", "body": BODY, "category": Category.objects.get(slug="agriculture").pk,
             "province": Province.objects.get(name="Дорноговь").pk, "event_date": date.today().isoformat(),
             "source": "Аймгийн ХАА газар", "copyright_declared": True, **kw}
        r = self.client.post("/api/v1/content/", d, format="json")
        self.assertEqual(r.status_code, 201, r.content)
        return r.data["id"]

    def test_unverified_cannot_submit_until_admin_verifies(self):
        self.login("j@t.mn")
        cid = self.draft()
        self.assertEqual(self.client.post(f"/api/v1/content/{cid}/submit/").status_code, 422)
        self.assertEqual(self.client.post("/api/v1/auth/request-verification/").status_code, 200)
        self.assertTrue(Notification.objects.filter(user=self.admin, title__contains="Баталгаажуулалт").exists())
        self.login("a@t.mn")
        r = self.client.get("/api/v1/admin/users/?verification=requested")
        self.assertEqual([u["email"] for u in r.data["results"]], ["j@t.mn"])
        self.client.post(f"/api/v1/admin/users/{self.j.pk}/verify/", {"verified": True, "reason": "Үнэмлэх"}, format="json")
        self.login("j@t.mn")
        self.assertEqual(self.client.post(f"/api/v1/content/{cid}/submit/").status_code, 200)

    def test_membership_newsroom_notified_and_sees_content(self):
        User.objects.filter(pk=self.j.pk).update(is_verified=True)
        self.login("j@t.mn")
        # редакц биш хэрэглэгчийг редакц болгон сонгох боломжгүй
        r = self.client.post("/api/v1/content/", {"title": "Туршилт", "newsroom": self.ed.pk}, format="json")
        self.assertEqual(r.status_code, 400)
        mid = self.client.post("/api/v1/memberships/", {"newsroom": self.nr.pk, "message": "Сайн уу"}, format="json").data["id"]
        self.assertEqual(self.client.post("/api/v1/memberships/", {"newsroom": self.nr.pk}, format="json").status_code, 409)
        self.login("n@t.mn")
        self.assertEqual(self.client.get("/api/v1/newsroom/members/").data[0]["status"], "pending")
        self.client.post(f"/api/v1/newsroom/members/{mid}/decide/", {"approve": True}, format="json")
        self.assertEqual(Membership.objects.get(pk=mid).status, "active")
        self.login("j@t.mn")
        cid = self.draft(newsroom=self.nr.pk)
        self.client.post(f"/api/v1/content/{cid}/submit/")
        self.assertTrue(Notification.objects.filter(user=self.nr, content_id=cid).exists())
        hist = self.client.get(f"/api/v1/content/{cid}/history/").data
        self.assertEqual([h["action"] for h in hist], ["created", "content.submit"])
        self.login("n@t.mn")
        self.assertEqual([c["id"] for c in self.client.get("/api/v1/newsroom/content/").data], [cid])
        # иргэн редакцын самбарт хандахгүй
        self.login("c@t.mn")
        self.assertEqual(self.client.get("/api/v1/newsroom/content/").status_code, 403)

    def test_submit_to_newsroom_without_membership_and_send_later(self):
        User.objects.filter(pk=self.j.pk).update(is_verified=True)
        self.login("j@t.mn")
        cid = self.draft(newsroom=self.nr.pk)  # гишүүнчлэлгүйгээр шууд редакц руу
        self.client.post(f"/api/v1/content/{cid}/submit/")
        self.assertTrue(Notification.objects.filter(user=self.nr, content_id=cid).exists())
        # редакц сонгоогүй илгээсэн мэдээг дараа нь редакц руу явуулна
        cid2 = self.draft(title="Дараа илгээх мэдээ")
        self.client.post(f"/api/v1/content/{cid2}/submit/")
        r = self.client.post(f"/api/v1/content/{cid2}/send-to-newsroom/", {"newsroom": self.nr.pk}, format="json")
        self.assertEqual(r.status_code, 200, r.content)
        self.assertEqual(self.client.post(f"/api/v1/content/{cid2}/send-to-newsroom/", {"newsroom": self.nr.pk}, format="json").status_code, 409)
        self.login("n@t.mn")
        self.assertEqual(sorted(c["id"] for c in self.client.get("/api/v1/newsroom/content/").data), sorted([cid, cid2]))

    def test_demo_purchase_and_ratings(self):
        c = Content.objects.create(author=self.j, title="Худалдах мэдээ", body=BODY, status="published", price=25000)
        self.login("c@t.mn")
        self.assertEqual(self.client.post("/api/v1/purchases/", {"content": c.pk}, format="json").status_code, 403)
        self.login("n@t.mn")
        p = self.client.post("/api/v1/purchases/", {"content": c.pk}, format="json").data
        self.assertEqual((p["status"], p["amount"]), ("pending", 25000))
        self.assertEqual(self.client.post(f"/api/v1/purchases/{p['id']}/confirm/").data["status"], "paid")
        self.assertTrue(Notification.objects.filter(user=self.j, title__contains="худалдан авлаа").exists())
        self.assertEqual(Purchase.objects.get().status, "paid")
        # үнэлгээ: өөрийгөө үнэлэхгүй, нэг хэрэглэгч нэг удаа (засна)
        r = self.client.post("/api/v1/ratings/", {"target": self.j.pk, "score": 4, "comment": "Сайн"}, format="json")
        self.assertEqual(r.data["summary"]["avg"], 4)
        self.client.post("/api/v1/ratings/", {"target": self.j.pk, "score": 5}, format="json")
        self.assertEqual(self.client.get(f"/api/v1/ratings/?target={self.j.pk}").data["summary"]["count"], 1)
        self.assertEqual(self.client.post("/api/v1/ratings/", {"target": self.nr.pk, "score": 5}, format="json").status_code, 422)
        s = self.client.get(f"/api/v1/ratings/suggest/?target={self.j.pk}").data
        self.assertTrue(1 <= s["score"] <= 5 and s["reasons"])
