from django.core.management import call_command
from rest_framework.test import APITestCase

from apps.accounts.models import Role, User
from apps.pledges.models import Pledge
from apps.pledges.services import percentages

PW = "Pulse12345!"


class PledgeStatsComplaintTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_demo", verbosity=0)
        cls.admin = User.objects.create_user("a@t.mn", PW, role=Role.ADMIN)
        cls.citizen = User.objects.create_user("c@t.mn", PW, role=Role.CITIZEN)

    def login(self, email):
        r = self.client.post("/api/v1/auth/login/", {"email": email, "password": PW}, format="json")
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + r.data["access"])

    def test_percent_excludes_insufficient(self):
        p = percentages(Pledge.objects.all())
        self.assertEqual(p["total"], 3); self.assertEqual(p["base"], 2)
        self.assertEqual(p["percent"]["fulfilled"], 50.0)

    def test_status_change_needs_reason_and_evidence(self):
        self.login("a@t.mn")
        p = Pledge.objects.filter(status="insufficient").first()
        r = self.client.post(f"/api/v1/pledges/{p.pk}/update-status/", {"status": "fulfilled"}, format="json")
        self.assertEqual(r.status_code, 422)
        r = self.client.post(f"/api/v1/pledges/{p.pk}/update-status/", {
            "status": "fulfilled", "reason": "Ажил хүлээн авсан",
            "evidence": {"source": "Акт №1", "date": "2026-01-02"}}, format="json")
        self.assertEqual(r.status_code, 200, r.content)

    def test_public_stats_and_backup_admin_only(self):
        self.assertEqual(self.client.get("/api/v1/stats/indicators/").status_code, 200)
        self.assertIn(self.client.get("/api/v1/admin/backup/").status_code, (401, 403))
        self.login("a@t.mn")
        self.assertEqual(self.client.get("/api/v1/admin/backup/").status_code, 200)

    def test_complaint_flow(self):
        self.login("c@t.mn")
        r = self.client.post("/api/v1/complaints/", {"subject": "Буруу мэдээлэл", "message": "Тоо буруу байна"}, format="json")
        self.assertIn(r.status_code, (201, 400), r.content)
