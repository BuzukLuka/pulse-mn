"""parliament.mn-ийн нийтийн API-гаас УИХ-ын 126 гишүүн, тойрог, сонгуулийн үр дүнг импортолно.

    python manage.py import_parliament
Мөрийн хөтөлбөр (амлалт) тэнд байхгүй тул admin-аас эх сурвалжтайгаар оруулна.
"""
from concurrent.futures import ThreadPoolExecutor

import requests
from django.core.management.base import BaseCommand

from apps.pledges.models import Politician

API = "https://parliament.mn/api"
UA = {"User-Agent": "PulseMN/1.0 (+https://pulse-mn-platform.vercel.app)"}


def detail(mid):
    r = requests.get(f"{API}/parliament_member/detail/{mid}/", headers=UA, timeout=15)
    r.raise_for_status()
    return r.json()


class Command(BaseCommand):
    help = "parliament.mn-ээс УИХ-ын гишүүдийг импортолно"

    def handle(self, *a, **o):
        members = requests.get(f"{API}/parliament_members_list/", headers=UA, timeout=20).json()["members"]
        with ThreadPoolExecutor(max_workers=8) as pool:
            details = list(pool.map(lambda m: (m, _safe(m["id"])), members))
        made = updated = 0
        for m, d in details:
            er = next(iter((d or {}).get("election_results") or []), {})
            name = (d or {}).get("short_name") or f"{m['last_name'][:1]}.{m['first_name']}"
            defaults = {
                "name": name, "position": "УИХ-ын гишүүн", "party": m["party"]["name"], "term_year": 2024,
                "photo_url": m.get("profile_image") or "", "profile_url": f"https://parliament.mn/member/{m['id']}",
                "constituency_number": er.get("constituency_number"), "constituency_name": er.get("constituency_name") or "",
                "election_system": er.get("election_system") or "", "votes": er.get("votes_received"),
            }
            obj = Politician.objects.filter(parliament_id=m["id"]).first() or \
                Politician.objects.filter(name=name, position="УИХ-ын гишүүн", term_year=2024).first()
            if obj:
                for k, v in defaults.items():
                    setattr(obj, k, v)
                obj.parliament_id = m["id"]
                obj.save()
                updated += 1
            else:
                Politician.objects.create(parliament_id=m["id"], **defaults)
                made += 1
        self.stdout.write(self.style.SUCCESS(f"parliament.mn: {len(members)} гишүүн (шинэ {made}, шинэчилсэн {updated})"))


def _safe(mid):
    try:
        return detail(mid)
    except Exception:  # noqa: BLE001 — нэг гишүүн унавал жагсаалтын мэдээллээр үлдээнэ
        return None
