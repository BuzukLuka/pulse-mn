"""Persona бүрийн эрх, хууль эрх зүйн шаардлага, төлбөр, дэлхийн мэдээний иж бүрэн тест."""
from datetime import date, timedelta
from unittest import mock

from django.core.management import call_command
from django.test import override_settings
from django.utils import timezone
from rest_framework.test import APITestCase

from apps.accounts.models import Role, User
from apps.audit.models import AuditLog
from apps.catalog.models import Category, Province
from apps.complaints.models import Complaint
from apps.content.models import Content, Correction
from apps.content.services import CHECKLIST, REQUIRED_CHECKS
from apps.newsroom.models import Purchase
from apps.newsroom.payments import breakdown
from apps.notifications.models import Notification

PW = "Pulse12345!"
BODY = "Дорноговь аймагт малчдын бэлчээрийн даацыг тооцож, ган зудын эрсдэлийг бууруулах ажил эхэллээ. " * 2
OK = {"facts_verified": True, "no_defamation": True, "personal_data": "none"}
ALL_CHECKS = {k: True for k, _, _ in CHECKLIST}


class Base(APITestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed", "--no-users", verbosity=0)
        mk = User.objects.create_user
        cls.admin = mk("admin@t.mn", PW, role=Role.ADMIN, full_name="Админ")
        cls.editor = mk("editor@t.mn", PW, role=Role.EDITOR, full_name="Редактор")
        cls.j = mk("j@t.mn", PW, role=Role.JOURNALIST, full_name="Сэтгүүлч", is_verified=True, press_card_no="MN-1")
        cls.j2 = mk("j2@t.mn", PW, role=Role.JOURNALIST, full_name="Сэтгүүлч 2", is_verified=True)
        cls.nr = mk("nr@t.mn", PW, role=Role.NEWSROOM, full_name="Редакц", legal_name="Редакц ХХК",
                    registry_no="1234567", responsible_editor="Б. Бат", is_verified=True)
        cls.nr2 = mk("nr2@t.mn", PW, role=Role.NEWSROOM, full_name="Редакц 2", is_verified=True)
        cls.citizen = mk("c@t.mn", PW, role=Role.CITIZEN, full_name="Иргэн")

    def login(self, user):
        if user is None:
            self.client.credentials()
            return
        r = self.client.post("/api/v1/auth/login/", {"email": user.email, "password": PW}, format="json")
        self.assertEqual(r.status_code, 200, r.content)
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + r.data["access"])

    def payload(self, **kw):
        return {"title": "Бэлчээрийн даац тооцоолол", "body": BODY, "category": Category.objects.get(slug="agriculture").pk,
                "province": Province.objects.get(name="Дорноговь").pk, "event_date": date.today().isoformat(),
                "source": "Аймгийн ХАА газар", "copyright_declared": True, "compliance": dict(OK), **kw}

    def published(self, author=None, **kw):
        d = dict(author=author or self.j, title="Нийтлэгдсэн мэдээ", body=BODY, status="published",
                 published_at=timezone.now(), category=Category.objects.get(slug="economy"),
                 province=Province.objects.get(name="Дорноговь"), compliance=dict(OK))
        d.update(kw)
        return Content.objects.create(**d)


# ---------- Бүртгэл, зөвшөөрөл (persona бүр) ----------
class RegistrationConsentTests(Base):
    def reg(self, **kw):
        d = {"email": "new@t.mn", "password": PW, "full_name": "Шинэ", "accept_terms": True, "accept_privacy": True, **kw}
        return self.client.post("/api/v1/auth/register/", d, format="json")

    def test_terms_and_privacy_required_for_everyone(self):
        r = self.reg(role="citizen", accept_terms=False, accept_privacy=False)
        self.assertEqual(r.status_code, 400)
        self.assertIn("accept_terms", r.data)
        self.assertIn("accept_privacy", r.data)

    def test_citizen_registers_with_consent_timestamps(self):
        r = self.reg(role="citizen")
        self.assertEqual(r.status_code, 201, r.content)
        u = User.objects.get(email="new@t.mn")
        self.assertIsNotNone(u.terms_accepted_at)
        self.assertIsNotNone(u.privacy_consent_at)
        self.assertIsNone(u.ethics_accepted_at)

    def test_journalist_must_accept_code_of_ethics(self):
        self.assertIn("accept_ethics", self.reg(role="journalist").data)
        r = self.reg(role="journalist", accept_ethics=True, press_card_no="MN-77")
        self.assertEqual(r.status_code, 201)
        u = User.objects.get(email="new@t.mn")
        self.assertIsNotNone(u.ethics_accepted_at)
        self.assertEqual(u.press_card_no, "MN-77")

    def test_newsroom_needs_legal_entity_details(self):
        r = self.reg(role="newsroom")
        self.assertEqual(set(r.data) & {"legal_name", "registry_no", "responsible_editor"},
                         {"legal_name", "registry_no", "responsible_editor"})
        r = self.reg(role="newsroom", legal_name="Мэдээ ХХК", registry_no="12AB", responsible_editor="Д. Дорж")
        self.assertIn("registry_no", r.data)
        r = self.reg(role="newsroom", legal_name="Мэдээ ХХК", registry_no="7654321", responsible_editor="Д. Дорж")
        self.assertEqual(r.status_code, 201, r.content)
        self.assertEqual(User.objects.get(email="new@t.mn").registry_no, "7654321")

    def test_admin_and_editor_roles_cannot_self_register(self):
        for role in ("admin", "editor"):
            self.assertEqual(self.reg(role=role).status_code, 400)

    def test_verification_prerequisites_per_persona(self):
        self.login(self.j2)  # үнэмлэх, байгууллагагүй
        User.objects.filter(pk=self.j2.pk).update(is_verified=False)
        r = self.client.post("/api/v1/auth/request-verification/")
        self.assertEqual(r.status_code, 422)
        self.login(self.nr2)  # регистргүй редакц
        User.objects.filter(pk=self.nr2.pk).update(is_verified=False)
        self.assertEqual(self.client.post("/api/v1/auth/request-verification/").status_code, 422)
        self.client.patch("/api/v1/auth/me/", {"legal_name": "Р2 ХХК", "registry_no": "1111111",
                                               "responsible_editor": "Э. Эрдэнэ"}, format="json")
        self.assertEqual(self.client.post("/api/v1/auth/request-verification/").status_code, 200)
        self.assertEqual(self.client.patch("/api/v1/auth/me/", {"registry_no": "abc"}, format="json").status_code, 400)


# ---------- Эрхийн матриц ----------
class PermissionMatrixTests(Base):
    """Endpoint бүрт аль persona хандах ёстойг шалгана (401/403 эсвэл амжилттай)."""
    MATRIX = [
        ("get", "/api/v1/news/", {"anon", "citizen", "journalist", "newsroom", "editor", "admin"}),
        ("get", "/api/v1/content/", {"journalist"}),
        ("get", "/api/v1/review/", {"editor", "admin"}),
        ("get", "/api/v1/newsroom/summary/", {"newsroom"}),
        ("get", "/api/v1/newsroom/content/", {"newsroom"}),
        ("get", "/api/v1/memberships/", {"journalist"}),
        ("get", "/api/v1/purchases/", {"newsroom", "journalist"}),
        ("get", "/api/v1/admin/users/", {"admin"}),
        ("get", "/api/v1/admin/purchases/", {"admin"}),
        ("get", "/api/v1/admin/complaints/", {"admin"}),
        ("get", "/api/v1/admin/audit/", {"admin"}),
        ("get", "/api/v1/auth/me/export/", {"citizen", "journalist", "newsroom", "editor", "admin"}),
        ("get", "/api/v1/notifications/", {"citizen", "journalist", "newsroom", "editor", "admin"}),
        ("get", "/api/v1/newsrooms/", {"anon", "citizen", "journalist", "newsroom", "editor", "admin"}),
    ]

    def test_matrix(self):
        users = {"anon": None, "citizen": self.citizen, "journalist": self.j, "newsroom": self.nr,
                 "editor": self.editor, "admin": self.admin}
        for persona, user in users.items():
            self.login(user)
            for method, url, allowed in self.MATRIX:
                code = getattr(self.client, method)(url).status_code
                if persona in allowed:
                    self.assertLess(code, 400, f"{persona} {url} → {code}")
                else:
                    self.assertIn(code, (401, 403), f"{persona} {url} → {code}")

    def test_visibility_of_content_by_persona(self):
        draft = Content.objects.create(author=self.j, title="Ноорог", body=BODY)
        pub = self.published()
        self.login(None)
        self.assertEqual(self.client.get(f"/api/v1/news/{draft.pk}/").status_code, 404)
        self.assertEqual(self.client.get(f"/api/v1/news/{pub.pk}/").status_code, 200)
        self.login(self.j2)  # өөр сэтгүүлчийн контентыг харахгүй
        self.assertEqual(self.client.get(f"/api/v1/content/{draft.pk}/").status_code, 404)
        self.login(self.editor)  # редактор ноорог харахгүй
        self.assertEqual(self.client.get(f"/api/v1/review/{draft.pk}/").status_code, 404)


# ---------- Сэтгүүлчийн хууль ёсны мэдэгдэл ----------
class ComplianceTests(Base):
    def submit(self, **kw):
        self.login(self.j)
        cid = self.client.post("/api/v1/content/", self.payload(**kw), format="json").data["id"]
        return cid, self.client.post(f"/api/v1/content/{cid}/submit/")

    def test_compliance_declarations_required(self):
        _, r = self.submit(compliance={})
        self.assertEqual(r.status_code, 400)
        self.assertEqual(len(r.data["compliance"]), 3)

    def test_minors_and_sponsor_rules(self):
        _, r = self.submit(compliance={**OK, "minors_involved": True})
        self.assertEqual(r.status_code, 400)
        _, r = self.submit(compliance={**OK, "sponsored": True})
        self.assertEqual(r.status_code, 400)
        _, r = self.submit(compliance={**OK, "political_ad": True, "sponsor_name": "Нам А"})
        self.assertEqual(r.status_code, 200, r.content)

    def test_unknown_compliance_keys_dropped(self):
        self.login(self.j)
        r = self.client.post("/api/v1/content/", self.payload(compliance={**OK, "evil": "x"}), format="json")
        self.assertNotIn("evil", r.data["compliance"])

    def test_public_disclosure_shown_raw_compliance_hidden(self):
        c = self.published(compliance={**OK, "sponsored": True, "sponsor_name": "Компани ХХК",
                                       "conflict_of_interest": "Зохиогч тус компанид ажилладаг"})
        d = self.client.get(f"/api/v1/news/{c.pk}/").data
        self.assertNotIn("compliance", d)
        self.assertEqual(d["disclosure"]["sponsor_name"], "Компани ХХК")
        self.assertTrue(d["disclosure"]["sponsored"])

    def test_editor_must_tick_all_legal_checks(self):
        cid, r = self.submit()
        self.assertEqual(r.status_code, 200)
        self.assertTrue({"privacy", "defamation", "minors"} <= set(REQUIRED_CHECKS))
        self.login(self.editor)
        old = {"facts": True, "source": True, "rights": True}
        self.assertEqual(self.client.post(f"/api/v1/review/{cid}/decide/", {"decision": "approve", "checklist": old},
                                          format="json").status_code, 422)
        r = self.client.post(f"/api/v1/review/{cid}/decide/", {"decision": "approve", "checklist": ALL_CHECKS}, format="json")
        self.assertEqual(r.data["status"], "published")
        items = self.client.get(f"/api/v1/review/{cid}/").data["checklist_items"]
        self.assertTrue(any(i["key"] == "defamation" and i["required"] for i in items))


# ---------- Залруулга, хариу тайлбар, хууль ёсны нуулт ----------
class CorrectionAndTakedownTests(Base):
    def test_editor_publishes_correction_visible_to_public(self):
        c = self.published()
        self.login(self.citizen)
        self.assertEqual(self.client.post(f"/api/v1/review/{c.pk}/corrections/", {"text": "x" * 20}).status_code, 403)
        self.login(self.editor)
        r = self.client.post(f"/api/v1/review/{c.pk}/corrections/", {"kind": "correction", "text": "Тоог 15 биш 12 гэж залруулав."},
                             format="json")
        self.assertEqual(r.status_code, 201)
        self.assertEqual(self.client.post(f"/api/v1/review/{c.pk}/corrections/", {"kind": "bad", "text": "x" * 20},
                                          format="json").status_code, 422)
        pub = self.client.get(f"/api/v1/news/{c.pk}/").data
        self.assertEqual(pub["corrections"][0]["kind_label"], "Залруулга")
        self.assertTrue(Notification.objects.filter(user=self.j, title__contains="залруулга").exists())

    def test_correction_only_on_published(self):
        c = Content.objects.create(author=self.j, title="Хянагдаж буй", body=BODY, status="under_review")
        self.login(self.editor)
        self.assertEqual(self.client.post(f"/api/v1/review/{c.pk}/corrections/", {"text": "x" * 20},
                                          format="json").status_code, 409)

    def test_right_of_reply_via_complaint(self):
        c = self.published()
        self.login(self.citizen)
        self.client.post("/api/v1/complaints/", {"target_type": "content", "target_id": c.pk, "kind": "reply",
                                                 "text": "Миний байр суурийг тусгаагүй байна."}, format="json")
        comp = Complaint.objects.get()
        self.login(self.admin)
        r = self.client.post(f"/api/v1/admin/complaints/{comp.pk}/resolve/",
                             {"status": "resolved", "resolution": "Хариу тайлбарыг нийтлэв.",
                              "correction": "Иргэн Б: мэдээнд дурдсан хэрэгт оролцоогүй болно."}, format="json")
        self.assertEqual(r.status_code, 200, r.content)
        self.assertEqual(Correction.objects.get(content=c).kind, "reply")

    def test_hide_requires_legal_basis_and_notifies_author(self):
        c = self.published()
        self.login(self.admin)
        r = self.client.post(f"/api/v1/admin/content/{c.pk}/hide/", {"reason": "Шүүхийн шийдвэр №12", "legal_basis": "nope"},
                             format="json")
        self.assertEqual(r.status_code, 422)
        r = self.client.post(f"/api/v1/admin/content/{c.pk}/hide/", {"reason": "Шүүхийн шийдвэр №12", "legal_basis": "court_order"},
                             format="json")
        self.assertEqual(r.data["status"], "hidden")
        log = AuditLog.objects.filter(action="content.hide").latest("id")
        self.assertTrue(log.reason.startswith("[Шүүхийн шийдвэр]"))
        self.assertTrue(Notification.objects.filter(user=self.j, title__contains="нуулаа").exists())
        self.login(None)
        self.assertEqual(self.client.get(f"/api/v1/news/{c.pk}/").status_code, 404)


# ---------- Хувийн мэдээллийн субъектийн эрх ----------
class DataRightsTests(Base):
    def test_export_contains_own_data_only(self):
        self.published(title="Миний мэдээ")
        self.published(author=self.j2, title="Бусдын мэдээ")
        self.login(self.j)
        d = self.client.get("/api/v1/auth/me/export/").data
        self.assertEqual(d["profile"]["email"], "j@t.mn")
        self.assertEqual([c["title"] for c in d["content"]], ["Миний мэдээ"])

    def test_delete_account_anonymizes_and_keeps_published_news(self):
        c = self.published()
        self.login(self.j)
        self.assertEqual(self.client.post("/api/v1/auth/me/delete/", {"password": "wrong"}, format="json").status_code, 422)
        self.assertEqual(self.client.post("/api/v1/auth/me/delete/", {"password": PW}, format="json").status_code, 204)
        u = User.objects.get(pk=self.j.pk)
        self.assertFalse(u.is_active)
        self.assertTrue(u.email.startswith("deleted-"))
        self.assertEqual(u.full_name, "Устгагдсан хэрэглэгч")
        self.assertEqual(self.client.post("/api/v1/auth/login/", {"email": "j@t.mn", "password": PW}, format="json").status_code, 401)
        self.login(None)
        self.assertEqual(self.client.get(f"/api/v1/news/{c.pk}/").data["author_name"], "Устгагдсан хэрэглэгч")

    def test_last_admin_cannot_delete_self(self):
        self.login(self.admin)
        self.assertEqual(self.client.post("/api/v1/auth/me/delete/", {"password": PW}, format="json").status_code, 409)


# ---------- Төлбөр (ДЕМО provider) ----------
class PaymentTests(Base):
    def buy(self, content, user=None, **kw):
        self.login(user or self.nr)
        return self.client.post("/api/v1/purchases/", {"content": content.pk, "accept_terms": True, **kw}, format="json")

    def test_vat_and_fee_breakdown(self):
        b = breakdown(110000)
        self.assertEqual(b["vat_amount"], 10000)          # НӨАТ = 110000 × 10/110
        self.assertEqual(b["platform_fee"], 10000)        # (110000 − 10000) × 10%
        self.assertEqual(b["author_net"], 90000)
        self.assertEqual(sum([b["vat_amount"], b["platform_fee"], b["author_net"]]), b["amount"])

    def test_quote_and_terms_required(self):
        c = self.published(price=33000)
        self.login(self.nr)
        q = self.client.get(f"/api/v1/purchases/quote/?content={c.pk}").data
        self.assertEqual([o["amount"] for o in q["options"]], [33000, 99000])
        self.assertFalse(q["live"])
        r = self.client.post("/api/v1/purchases/", {"content": c.pk}, format="json")
        self.assertEqual(r.status_code, 422)

    def test_standard_purchase_confirm_issues_receipt(self):
        c = self.published(price=22000)
        p = self.buy(c).data
        self.assertEqual((p["amount"], p["vat_amount"], p["license_type"], p["demo"]), (22000, 2000, "standard", True))
        self.assertTrue(p["provider_ref"].startswith("DEMO-"))
        p = self.client.post(f"/api/v1/purchases/{p['id']}/confirm/").data
        self.assertEqual(p["status"], "paid")
        self.assertTrue(p["ebarimt_no"].startswith("DEMO-EB-"))
        self.login(self.j)
        sales = self.client.get("/api/v1/purchases/").data
        self.assertEqual(sales[0]["author_net"], 18000)

    def test_exclusive_license_blocks_other_buyers(self):
        c = self.published(price=10000)
        p = self.buy(c, license_type="exclusive").data
        self.assertEqual(p["amount"], 30000)
        self.client.post(f"/api/v1/purchases/{p['id']}/confirm/")
        self.assertEqual(self.buy(c, self.nr2).status_code, 409)

    def test_exclusive_not_possible_after_standard_sale(self):
        c = self.published(price=10000)
        p = self.buy(c).data
        self.client.post(f"/api/v1/purchases/{p['id']}/confirm/")
        self.assertEqual(self.buy(c, self.nr2, license_type="exclusive").status_code, 409)
        self.assertEqual(self.buy(c, self.nr2).status_code, 201)

    def test_not_for_sale_and_unpublished(self):
        self.assertEqual(self.buy(self.published(price=0)).status_code, 422)
        draft = Content.objects.create(author=self.j, title="Ноорог", body=BODY, price=5000)
        self.assertEqual(self.buy(draft).status_code, 422)

    def test_admin_refund_and_permissions(self):
        c = self.published(price=11000)
        p = self.buy(c).data
        self.client.post(f"/api/v1/purchases/{p['id']}/confirm/")
        self.assertEqual(self.client.post(f"/api/v1/admin/purchases/{p['id']}/refund/", {"reason": "x"}).status_code, 403)
        self.login(self.admin)
        self.assertEqual(self.client.post(f"/api/v1/admin/purchases/{p['id']}/refund/", {"reason": ""},
                                          format="json").status_code, 422)
        r = self.client.post(f"/api/v1/admin/purchases/{p['id']}/refund/", {"reason": "Зохиогчийн эрхийн маргаан"}, format="json")
        self.assertEqual(r.data["status"], "refunded")
        totals = self.client.get("/api/v1/admin/purchases/").data["totals"]
        self.assertEqual(totals["gross"], 0)
        self.assertEqual(Purchase.objects.get().refund_reason, "Зохиогчийн эрхийн маргаан")

    def test_cancel_only_own_pending(self):
        c = self.published(price=5000)
        p = self.buy(c).data
        self.login(self.nr2)
        self.assertEqual(self.client.post(f"/api/v1/purchases/{p['id']}/cancel/").status_code, 409)
        self.login(self.nr)
        self.assertEqual(self.client.post(f"/api/v1/purchases/{p['id']}/cancel/").data["status"], "cancelled")


# ---------- Дэлхийн мэдээний AI функц ----------
RSS = b"""<?xml version="1.0"?><rss><channel>
<item><title>Mongolia approves new mining law</title><link>https://ex.com/a</link>
<description>&lt;p&gt;Parliament in Ulaanbaatar passed the bill on copper investment.&lt;/p&gt;</description>
<pubDate>Mon, 02 Nov 2026 08:00:00 GMT</pubDate></item>
<item><title>Inner Mongolia tourism grows</title><link>https://ex.com/b</link><description>Inner Mongolia region of China</description></item>
<item><title>Japan elects new leader</title><link>https://ex.com/c</link><description>Tokyo politics</description></item>
<item><title>No link item</title></item>
</channel></rss>"""


class WorldNewsTests(Base):
    def setUp(self):
        from apps.worldnews import services
        p = mock.patch.object(services, "og_image", return_value="")  # тестэд гадны сайт руу хандахгүй
        p.start()
        self.addCleanup(p.stop)

    def test_rss_image_sources(self):
        from apps.worldnews.services import parse_rss
        xml = b"""<rss xmlns:media="http://search.yahoo.com/mrss/"><channel>
<item><title>A</title><link>https://ex.com/1</link><media:content medium="image" url="https://img.ex.com/1.jpg"/></item>
<item><title>B</title><link>https://ex.com/2</link><media:thumbnail url="https://img.ex.com/2.jpg"/></item>
<item><title>C</title><link>https://ex.com/3</link><enclosure type="image/jpeg" url="https://img.ex.com/3.jpg"/></item>
<item><title>D</title><link>https://ex.com/4</link><description>&lt;img src="https://img.ex.com/4.jpg"&gt; text</description></item>
<item><title>E</title><link>https://ex.com/5</link><description>no image</description></item>
</channel></rss>"""
        self.assertEqual([i["image"] for i in parse_rss(xml)],
                         ["https://img.ex.com/1.jpg", "https://img.ex.com/2.jpg", "https://img.ex.com/3.jpg", "https://img.ex.com/4.jpg", ""])

    def test_og_image_respects_robots_and_parses_meta(self):
        from apps.worldnews import services
        page = b'<html><head><meta property="og:image" content="/img/cover.jpg"></head></html>'
        resp = mock.Mock(status_code=200, raw=mock.Mock(read=mock.Mock(return_value=page)), raise_for_status=mock.Mock())
        mock.patch.stopall()  # setUp-ийн mock-ийг энэ тестэд хасна
        with mock.patch.object(services, "robots_allowed", return_value=True),                 mock.patch.object(services.requests, "get", return_value=resp):
            self.assertEqual(services.og_image("https://site.mn/n/1"), "https://site.mn/img/cover.jpg")
        with mock.patch.object(services, "robots_allowed", return_value=False):
            self.assertEqual(services.og_image("https://site.mn/n/1"), "")
        self.assertEqual(services.og_image("https://news.google.com/rss/articles/x"), "")

    def test_fill_images_once(self):
        from apps.worldnews import services
        from apps.worldnews.models import ExternalArticle
        a = ExternalArticle.objects.create(source="ikon", url="https://ikon.mn/n/1", title="x", relevance=1)
        g = ExternalArticle.objects.create(source="google_en", url="https://news.google.com/a", title="y", relevance=1)
        with mock.patch.object(services, "og_image", return_value="https://content.ikon.mn/a.jpg") as og:
            self.assertEqual(services.fill_images(), 1)
            self.assertEqual(services.fill_images(), 0)      # дахин оролдохгүй
            self.assertEqual(og.call_count, 1)
        a.refresh_from_db(); g.refresh_from_db()
        self.assertEqual((a.image_url, a.image_checked, g.image_checked), ("https://content.ikon.mn/a.jpg", True, False))
    def test_parse_rss_strips_html_and_skips_bad_items(self):
        from apps.worldnews.services import parse_rss
        items = parse_rss(RSS)
        self.assertEqual(len(items), 3)
        self.assertEqual(items[0]["snippet"], "Parliament in Ulaanbaatar passed the bill on copper investment.")
        self.assertEqual(items[0]["published_at"].year, 2026)

    def test_rules_relevance_category_and_language(self):
        from apps.worldnews.services import detect_lang, parse_rss, rules_enrich
        a, b, c = parse_rss(RSS)
        src = {"lang": "en"}
        e = rules_enrich(a, src)
        self.assertGreaterEqual(e["relevance"], 0.5)
        self.assertEqual(e["category"], "economy")
        self.assertLess(rules_enrich(b, src)["relevance"], 0.5)   # Өвөр Монгол
        self.assertEqual(rules_enrich(c, src)["relevance"], 0.0)
        self.assertEqual(detect_lang("Монгол Улсын Их Хурал", "mn"), "mn")
        self.assertEqual(detect_lang("Новости Монголии и Бурятии", "mn"), "ru")
        self.assertEqual(detect_lang("Mongolia news", "mn"), "en")

    def test_refresh_stores_only_relevant_and_respects_staleness(self):
        from apps.worldnews import services
        from apps.worldnews.models import ExternalArticle, FetchRun
        feed = lambda k: services.parse_rss(RSS) if k == "google_en" else []  # noqa: E731
        with mock.patch.object(services, "fetch_source", side_effect=feed), \
                mock.patch.object(services.gemini, "is_configured", return_value=False):
            run = services.refresh(force=True)
            self.assertEqual(ExternalArticle.objects.count(), 1)
            self.assertEqual(ExternalArticle.objects.get().category.slug, "economy")
            self.assertTrue(all(v["ok"] for v in run.report.values()))
            self.assertEqual(services.refresh().pk, run.pk)          # 3 цагийн дотор дахин татахгүй
            self.assertEqual(FetchRun.objects.count(), 1)

    def test_failing_source_does_not_break_others(self):
        from apps.worldnews import services
        def fetch(k):
            if k == "bbc":
                raise ConnectionError("down")
            return services.parse_rss(RSS)
        with mock.patch.object(services, "fetch_source", side_effect=fetch), \
                mock.patch.object(services.gemini, "is_configured", return_value=False):
            run = services.refresh(force=True)
        self.assertFalse(run.report["bbc"]["ok"])
        self.assertTrue(run.report["google_en"]["ok"])

    def test_gemini_enrichment_used_when_configured(self):
        from apps.worldnews import services
        from apps.worldnews.models import ExternalArticle
        ai = [{"i": i, "relevance": 0.9, "category": "politics", "title_mn": "Монгол гарчиг", "summary_mn": "Хураангуй"}
              for i in range(40)]
        with mock.patch.object(services, "fetch_source", side_effect=lambda k: services.parse_rss(RSS)[:1]), \
                mock.patch.object(services.gemini, "is_configured", return_value=True), \
                mock.patch.object(services.gemini, "generate_json", return_value=ai):
            services.refresh(force=True)
        a = ExternalArticle.objects.get()
        self.assertEqual((a.ai_source, a.title_mn, a.category.slug), ("gemini", "Монгол гарчиг", "politics"))

    def test_nso_api_disabled_without_permission(self):
        from apps.worldnews.sources import enabled_sources
        self.assertNotIn("nso", enabled_sources())
        with mock.patch.dict("os.environ", {"NSO_API_ENABLED": "1"}):
            self.assertIn("nso", enabled_sources())

    def test_public_list_and_refresh_permissions(self):
        from apps.worldnews.models import ExternalArticle, FetchRun
        FetchRun.objects.create()  # шинэ гэж тооцогдоно — хүсэлтийн үеэр татахгүй
        ExternalArticle.objects.create(source="google_en", url="https://ex.com/z", title="Mongolia news",
                                       relevance=0.9, published_at=timezone.now() - timedelta(hours=1))
        r = self.client.get("/api/v1/world-news/")
        self.assertEqual(r.data["count"], 1)
        self.assertEqual(r.data["results"][0]["source_name"], "Google News · Mongolia")
        self.assertEqual(self.client.get("/api/v1/world-news/refresh/").status_code, 403)
        self.login(self.citizen)
        self.assertEqual(self.client.get("/api/v1/world-news/refresh/").status_code, 403)
        from apps.worldnews import services
        with mock.patch.object(services, "refresh", return_value=FetchRun.objects.first()):
            self.login(None)
            with mock.patch.dict("os.environ", {"CRON_SECRET": "s3cret"}):
                self.assertEqual(self.client.get("/api/v1/world-news/refresh/", HTTP_AUTHORIZATION="Bearer s3cret").status_code, 200)
                self.assertEqual(self.client.get("/api/v1/world-news/refresh/", HTTP_AUTHORIZATION="Bearer bad").status_code, 403)
            self.login(self.admin)
            self.assertEqual(self.client.post("/api/v1/world-news/refresh/").status_code, 200)
        self.assertEqual(len(self.client.get("/api/v1/world-news/sources/").data["sources"]), 8)


# ---------- Редакц өөрөө шалгаж нийтлэх ----------
class NewsroomReviewTests(Base):
    def setUp(self):
        from apps.newsroom.models import Membership
        Membership.objects.create(newsroom=self.nr, journalist=self.j, status="active")

    def send(self, author, newsroom):
        self.login(author)
        cid = self.client.post("/api/v1/content/", self.payload(newsroom=newsroom.pk if newsroom else None), format="json").data["id"]
        self.assertEqual(self.client.post(f"/api/v1/content/{cid}/submit/").status_code, 200)
        return Content.objects.get(pk=cid)

    def test_member_news_routed_to_verified_newsroom(self):
        c = self.send(self.j, self.nr)
        self.assertEqual(c.review_by, "newsroom")
        self.assertTrue(Notification.objects.filter(user=self.nr, title__contains="шийдвэр гаргана").exists())
        self.assertFalse(Notification.objects.filter(user=self.editor, content_id=c.pk).exists())
        # Pulse-ийн редакторын жагсаалтад харагдахгүй, шийдвэр гаргах боломжгүй
        self.login(self.editor)
        self.assertNotIn(c.pk, [x["id"] for x in self.client.get("/api/v1/review/").data["results"]])
        self.assertEqual(self.client.get(f"/api/v1/review/{c.pk}/").status_code, 404)
        self.login(self.admin)  # админ хяналтаар харна, гэхдээ шийдвэр редакцынх
        self.assertEqual(self.client.get(f"/api/v1/review/{c.pk}/").status_code, 200)
        self.assertEqual(self.client.post(f"/api/v1/review/{c.pk}/decide/", {"decision": "approve", "checklist": ALL_CHECKS},
                                          format="json").status_code, 409)

    def test_newsroom_decides_with_legal_checklist(self):
        c = self.send(self.j, self.nr)
        self.login(self.nr)
        d = self.client.get(f"/api/v1/newsroom/content/{c.pk}/").data
        self.assertTrue(d["can_decide"])
        self.assertTrue(any(i["key"] == "defamation" for i in d["checklist_items"]))
        url = f"/api/v1/newsroom/content/{c.pk}/decide/"
        self.assertEqual(self.client.post(url, {"decision": "approve", "checklist": {"facts": True}}, format="json").status_code, 422)
        r = self.client.post(url, {"decision": "approve", "checklist": ALL_CHECKS}, format="json")
        self.assertEqual(r.data["status"], "published")
        self.assertTrue(Notification.objects.filter(user=self.j, content_id=c.pk, title__contains="Нийтлэгдсэн").exists())
        trust = self.client.get(f"/api/v1/news/{c.pk}/").data["trust"]
        self.assertTrue(trust["editor_verified"] and trust["verified_by_newsroom"])
        self.assertEqual(trust["verified_by"], "Редакц")
        r = self.client.post(f"/api/v1/newsroom/content/{c.pk}/corrections/", {"kind": "update", "text": "Шинэ мэдээлэл нэмэгдлээ."},
                             format="json")
        self.assertEqual(r.status_code, 201)

    def test_return_and_resubmit_stays_with_newsroom(self):
        c = self.send(self.j, self.nr)
        self.login(self.nr)
        self.client.post(f"/api/v1/newsroom/content/{c.pk}/decide/", {"decision": "return", "reason": "Эх сурвалж нэм"}, format="json")
        self.login(self.j)
        self.assertEqual(self.client.post(f"/api/v1/content/{c.pk}/submit/").status_code, 200)
        self.assertEqual(Content.objects.get(pk=c.pk).review_by, "newsroom")

    def test_non_member_or_unverified_newsroom_goes_to_pulse(self):
        c = self.send(self.j2, self.nr)                 # гишүүн бус
        self.assertEqual(c.review_by, "pulse")
        User.objects.filter(pk=self.nr.pk).update(is_verified=False)
        c2 = self.send(self.j, self.nr)                 # баталгаажаагүй редакц
        self.assertEqual(c2.review_by, "pulse")
        c3 = self.send(self.j, None)                    # бие даасан
        self.assertEqual(c3.review_by, "pulse")
        self.login(self.nr)
        self.assertEqual(self.client.post(f"/api/v1/newsroom/content/{c.pk}/decide/", {"decision": "approve", "checklist": ALL_CHECKS},
                                          format="json").status_code, 409)
        self.assertFalse(self.client.get(f"/api/v1/newsroom/content/{c.pk}/").data["can_decide"])

    def test_other_newsroom_cannot_access(self):
        c = self.send(self.j, self.nr)
        self.login(self.nr2)
        self.assertEqual(self.client.get(f"/api/v1/newsroom/content/{c.pk}/").status_code, 404)
        self.assertEqual(self.client.post(f"/api/v1/newsroom/content/{c.pk}/decide/", {"decision": "reject", "reason": "x"},
                                          format="json").status_code, 404)
        self.login(self.j)
        self.assertEqual(self.client.get(f"/api/v1/newsroom/content/{c.pk}/").status_code, 403)


# ---------- Редакцын өөрийн редакторууд ----------
class NewsroomStaffEditorTests(Base):
    def setUp(self):
        from apps.newsroom.models import Membership
        Membership.objects.create(newsroom=self.nr, journalist=self.j, status="active")
        self.login(self.nr)
        r = self.client.post("/api/v1/newsroom/editors/", {"email": "Staff@T.mn", "full_name": "Редакцын редактор", "password": PW},
                             format="json")
        self.assertEqual(r.status_code, 201, r.content)
        self.staff = User.objects.get(email="staff@t.mn")

    def submit(self, author, newsroom=None):
        self.login(author)
        cid = self.client.post("/api/v1/content/", self.payload(newsroom=newsroom.pk if newsroom else None), format="json").data["id"]
        self.client.post(f"/api/v1/content/{cid}/submit/")
        return cid

    def test_newsroom_creates_editor_account(self):
        self.assertEqual((self.staff.role, self.staff.newsroom_org_id), ("editor", self.nr.pk))
        self.assertEqual(self.client.post("/api/v1/newsroom/editors/", {"email": "staff@t.mn", "full_name": "x", "password": PW},
                                          format="json").status_code, 409)
        self.assertEqual(self.client.post("/api/v1/newsroom/editors/", {"email": "w@t.mn", "full_name": "x", "password": "123"},
                                          format="json").status_code, 422)
        self.assertEqual([e["email"] for e in self.client.get("/api/v1/newsroom/editors/").data], ["staff@t.mn"])
        self.login(self.staff)
        me = self.client.get("/api/v1/auth/me/").data
        self.assertEqual(me["newsroom_org_name"], "Редакц")

    def test_staff_editor_reviews_only_own_newsroom(self):
        mine = self.submit(self.j, self.nr)            # редакц руу
        pulse = self.submit(self.j2)                    # бие даасан → Pulse
        self.assertTrue(Notification.objects.filter(user=self.staff, content_id=mine).exists())
        self.assertFalse(Notification.objects.filter(user=self.staff, content_id=pulse).exists())
        self.assertFalse(Notification.objects.filter(user=self.editor, content_id=mine).exists())
        self.login(self.staff)
        self.assertEqual([c["id"] for c in self.client.get("/api/v1/review/").data["results"]], [mine])
        self.assertEqual(self.client.get(f"/api/v1/review/{pulse}/").status_code, 404)
        r = self.client.post(f"/api/v1/review/{mine}/decide/", {"decision": "approve", "checklist": ALL_CHECKS}, format="json")
        self.assertEqual(r.data["status"], "published")
        self.assertEqual(self.client.get(f"/api/v1/news/{mine}/").data["trust"]["verified_by"], "Редакцын редактор")
        self.login(self.editor)                         # Pulse-ийн редактор
        self.assertEqual([c["id"] for c in self.client.get("/api/v1/review/").data["results"]], [pulse])

    def test_other_newsroom_staff_and_deactivation(self):
        mine = self.submit(self.j, self.nr)
        self.login(self.nr2)
        self.client.post("/api/v1/newsroom/editors/", {"email": "o@t.mn", "full_name": "Өөр", "password": PW}, format="json")
        other = User.objects.get(email="o@t.mn")
        self.assertEqual(self.client.post(f"/api/v1/newsroom/editors/{self.staff.pk}/active/", {"active": False},
                                          format="json").status_code, 404)
        self.login(other)
        self.assertEqual(self.client.get(f"/api/v1/review/{mine}/").status_code, 404)
        self.login(self.nr)
        self.client.post(f"/api/v1/newsroom/editors/{self.staff.pk}/active/", {"active": False}, format="json")
        r = self.client.post("/api/v1/auth/login/", {"email": "staff@t.mn", "password": PW}, format="json")
        self.assertEqual(r.status_code, 401)

    def test_only_newsroom_role_manages_editors(self):
        for u in (self.j, self.editor, self.citizen):
            self.login(u)
            self.assertEqual(self.client.get("/api/v1/newsroom/editors/").status_code, 403)


class JournalistTopicsTests(Base):
    def test_top_categories_on_cards_and_profile(self):
        econ, edu = Category.objects.get(slug="economy"), Category.objects.get(slug="education")
        for _ in range(3):
            self.published(category=econ)
        self.published(category=edu)
        Content.objects.create(author=self.j, title="Ноорог", body=BODY, category=edu)  # тооцохгүй
        card = next(x for x in self.client.get("/api/v1/journalists/").data if x["id"] == self.j.pk)
        self.assertEqual([(t["name"], t["count"]) for t in card["topics"]], [("Эдийн засаг", 3), ("Боловсрол", 1)])
        self.assertEqual(card["published"], 4)
        prof = self.client.get(f"/api/v1/journalists/{self.j.pk}/").data
        self.assertEqual(prof["topics"][0]["slug"], "economy")


# ---------- Сэтгэгдэл, нэр нууцлах ----------
class CommentTests(Base):
    def test_anonymous_citizen_comment(self):
        c = self.published()
        self.assertEqual(self.client.post("/api/v1/comments/", {"content": c.pk, "text": "Сайн мэдээ"}, format="json").status_code, 401)
        self.login(self.citizen)
        r = self.client.post("/api/v1/comments/", {"content": c.pk, "text": "Манай сумын асуудал үнэн.", "is_anonymous": True}, format="json")
        self.assertEqual(r.status_code, 201, r.content)
        self.login(None)
        d = self.client.get(f"/api/v1/comments/?content={c.pk}").data["results"][0]
        self.assertEqual(d["author_name"], "Нэргүй иргэн")
        self.assertNotIn("author", d)

    def test_only_citizen_can_be_anonymous_and_published_only(self):
        c = self.published()
        self.login(self.j)
        self.assertEqual(self.client.post("/api/v1/comments/", {"content": c.pk, "text": "x y", "is_anonymous": True}, format="json").status_code, 422)
        self.assertEqual(self.client.post("/api/v1/comments/", {"content": c.pk, "text": "Баярлалаа"}, format="json").data["author_name"], "Сэтгүүлч")
        draft = Content.objects.create(author=self.j, title="Ноорог", body=BODY)
        self.assertEqual(self.client.post("/api/v1/comments/", {"content": draft.pk, "text": "x y"}, format="json").status_code, 400)

    def test_rate_limit_delete_and_admin_hide(self):
        c = self.published()
        self.login(self.citizen)
        ids = [self.client.post("/api/v1/comments/", {"content": c.pk, "text": f"Сэтгэгдэл {i}"}, format="json").data["id"] for i in range(5)]
        self.assertEqual(self.client.post("/api/v1/comments/", {"content": c.pk, "text": "Зургаа дахь"}, format="json").status_code, 422)
        self.login(self.j)
        self.assertEqual(self.client.delete(f"/api/v1/comments/{ids[0]}/").status_code, 403)
        self.login(self.citizen)
        self.assertEqual(self.client.delete(f"/api/v1/comments/{ids[0]}/").status_code, 204)
        self.login(self.admin)
        self.assertEqual(self.client.delete(f"/api/v1/comments/{ids[1]}/").status_code, 204)
        self.assertTrue(AuditLog.objects.filter(action="comment.hide").exists())
        self.assertEqual(self.client.get(f"/api/v1/comments/?content={c.pk}").data["count"], 3)


class NewsFilterTests(Base):
    def test_category_slug_and_fresh(self):
        from datetime import timedelta
        econ = Category.objects.get(slug="economy")
        new = self.published(category=econ)
        old = self.published(category=Category.objects.get(slug="politics"), published_at=timezone.now() - timedelta(days=3))
        ids = lambda q: [x["id"] for x in self.client.get(f"/api/v1/news/{q}").data["results"]]  # noqa: E731
        self.assertEqual(ids("?c=economy"), [new.pk])
        self.assertEqual(ids("?c=politics"), [old.pk])
        self.assertEqual(ids("?fresh=24"), [new.pk])
        self.assertEqual(sorted(ids("?fresh=bad")), [new.pk])


# ---------- Топ мэдээ ----------
class FeaturedTests(Base):
    def test_journalist_requests_newsroom_decides(self):
        from apps.newsroom.models import Membership
        Membership.objects.create(newsroom=self.nr, journalist=self.j, status="active")
        c = self.published(newsroom=self.nr)
        self.login(self.j)
        self.assertEqual(self.client.post(f"/api/v1/content/{c.pk}/feature-request/", {"hours": 5}, format="json").status_code, 422)
        self.assertEqual(self.client.post(f"/api/v1/content/{c.pk}/feature-request/", {"hours": 24}, format="json").data["feature_request_hours"], 24)
        self.assertTrue(Notification.objects.filter(user=self.nr, title__contains="Топ мэдээ болгох хүсэлт").exists())
        self.login(self.nr2)  # өөр редакц
        self.assertEqual(self.client.post(f"/api/v1/newsroom/content/{c.pk}/feature/", {"hours": 24}, format="json").status_code, 404)
        self.login(self.nr)
        r = self.client.post(f"/api/v1/newsroom/content/{c.pk}/feature/", {"hours": 24}, format="json")
        self.assertTrue(r.data["is_featured"])
        self.assertIsNone(r.data["feature_request_hours"])
        self.login(None)
        self.assertEqual([x["id"] for x in self.client.get("/api/v1/news/?featured=1").data["results"]], [c.pk])

    def test_pulse_editor_features_independent_and_expiry(self):
        from datetime import timedelta
        c = self.published()
        self.login(self.citizen)
        self.assertEqual(self.client.post(f"/api/v1/review/{c.pk}/feature/", {"hours": 6}, format="json").status_code, 403)
        self.login(self.editor)
        self.assertTrue(self.client.post(f"/api/v1/review/{c.pk}/feature/", {"hours": 6}, format="json").data["is_featured"])
        Content.objects.filter(pk=c.pk).update(featured_until=timezone.now() - timedelta(minutes=1))  # хугацаа дууссан
        self.assertEqual(self.client.get("/api/v1/news/?featured=1").data["count"], 0)
        self.client.post(f"/api/v1/review/{c.pk}/feature/", {"hours": 12}, format="json")
        self.assertFalse(self.client.post(f"/api/v1/review/{c.pk}/feature/", {"hours": 0}, format="json").data["is_featured"])
        self.assertTrue(Notification.objects.filter(user=self.j, title__contains="топоос буулаа").exists())


# ---------- Амлалт: тойрог, иргэний явцын мэдээ, импорт ----------
class PledgeProgressTests(Base):
    def setUp(self):
        from apps.pledges.models import Pledge, Politician
        self.pol = Politician.objects.create(name="Б.Бат", position="УИХ-ын гишүүн", term_year=2024, parliament_id=99,
                                             constituency_number=12, constituency_name="Хан-Уул", election_system="MAJORITARIAN")
        self.pl = Pledge.objects.create(politician=self.pol, text="120 хүүхдийн цэцэрлэг барина", category=Category.objects.get(slug="education"),
                                        source="Мөрийн хөтөлбөр", lat=47.9, lng=106.9)

    def test_constituency_filter_and_list(self):
        r = self.client.get("/api/v1/pledges/politicians/constituencies/")
        self.assertEqual(r.data[0]["constituency_name"], "Хан-Уул")
        self.assertEqual(len(self.client.get("/api/v1/pledges/politicians/?constituency=12").data), 1)
        self.assertEqual(len(self.client.get("/api/v1/pledges/politicians/?constituency=3").data), 0)

    def test_admin_sets_deadline_progress_location(self):
        self.login(self.citizen)
        self.assertEqual(self.client.patch(f"/api/v1/pledges/{self.pl.pk}/", {"progress": 40}, format="json").status_code, 403)
        self.login(self.admin)
        r = self.client.patch(f"/api/v1/pledges/{self.pl.pk}/", {"deadline": "2027-09-01", "progress": 40, "location_name": "Хан-Уул 15-р хороо"}, format="json")
        self.assertEqual((r.data["deadline"], r.data["progress"]), ("2027-09-01", 40))
        self.assertEqual(self.client.patch(f"/api/v1/pledges/{self.pl.pk}/", {"progress": 140}, format="json").status_code, 400)

    def test_citizen_update_ai_check_and_verify(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        from io import BytesIO
        from PIL import Image
        buf = BytesIO(); Image.new("RGB", (64, 64), (200, 30, 30)).save(buf, "JPEG")
        url = f"/api/v1/pledges/{self.pl.pk}/updates/"
        self.assertEqual(self.client.post(url, {"text": "Барилга эхэлсэн"}, format="multipart").status_code, 401)
        self.login(self.citizen)
        r = self.client.post(url, {"text": "Цэцэрлэгийн барилгын суурь цутгаж, хана өрж эхэлсэн байна.", "lat": "48.5", "lng": "106.9",
                                   "progress": "30", "photo": SimpleUploadedFile("a.jpg", buf.getvalue(), "image/jpeg")}, format="multipart")
        self.assertEqual(r.status_code, 201, r.content)
        self.assertTrue(any("км зайтай" in f for f in r.data["ai_check"]["flags"]))
        uid = r.data["id"]
        # давхар зураг
        r2 = self.client.post(url, {"text": "Дахин ижил зураг оруулж байна шүү дээ.", "photo": SimpleUploadedFile("b.jpg", buf.getvalue(), "image/jpeg")}, format="multipart")
        self.assertIn("Яг ижил зураг өмнө нь оруулагдсан", r2.data["ai_check"]["flags"])
        self.assertEqual(self.client.get(url).data, [])            # баталгаажаагүй нь нийтэд харагдахгүй
        self.login(self.admin)
        self.assertEqual(len(self.client.get("/api/v1/admin/pledge-updates/").data["results"]), 2)
        self.client.post(f"/api/v1/admin/pledge-updates/{uid}/review/", {"approve": True, "note": "Зураг тохирч байна", "progress": 30}, format="json")
        self.login(None)
        self.assertEqual(len(self.client.get(url).data), 1)
        self.assertEqual(self.client.get(f"/api/v1/pledges/{self.pl.pk}/").data["progress"], 30)
        self.assertTrue(Notification.objects.filter(user=self.citizen, title__contains="баталгаажлаа").exists())

    def test_import_parliament(self):
        from apps.pledges.management.commands import import_parliament as imp
        from apps.pledges.models import Politician
        lst = {"members": [{"id": 5, "first_name": "Номин", "last_name": "Бат", "profile_image": "https://parliament.mn/p.jpg",
                            "party": {"name": "Ардчилсан нам"}}]}
        det = {"short_name": "Б.Номин", "election_results": [{"constituency_number": 3, "constituency_name": "Архангай",
               "election_system": "MAJORITARIAN", "votes_received": 12345}]}
        resp = mock.Mock(json=mock.Mock(return_value=lst))
        with mock.patch.object(imp.requests, "get", return_value=resp), mock.patch.object(imp, "detail", return_value=det):
            call_command("import_parliament", verbosity=0)
            call_command("import_parliament", verbosity=0)   # дахин ажиллуулахад давхардахгүй
        p = Politician.objects.get(parliament_id=5)
        self.assertEqual((p.name, p.constituency_name, p.votes, p.profile_url), ("Б.Номин", "Архангай", 12345, "https://parliament.mn/member/5"))
