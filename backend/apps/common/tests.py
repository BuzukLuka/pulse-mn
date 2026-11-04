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
