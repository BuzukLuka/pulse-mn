from django.db import transaction
from rest_framework.exceptions import ValidationError

from apps.audit import models as audit
from apps.common.exceptions import Unprocessable
from .models import PledgeEvidence, PledgeStatus, PledgeStatusHistory


def percentages(qs):
    """Биелэлтийн хувь. «Мэдээлэл дутуу» амлалтыг үндсэн тооцооноос хасна."""
    counts = {s.value: 0 for s in PledgeStatus}
    for st in qs.values_list("status", flat=True):
        counts[st] += 1
    total = sum(counts.values())
    base = total - counts["insufficient"]
    pct = lambda n: round(100 * n / base, 1) if base else None
    return {"total": total, "counts": counts, "base": base,
            "percent": {k: pct(v) for k, v in counts.items() if k != "insufficient"},
            "method": "Хувь = тухайн төлөвтэй амлалт ÷ (нийт амлалт − «мэдээлэл дутуу»). Баримтгүй амлалтыг тооцоонд оруулаагүй."}


@transaction.atomic
def update_status(pledge, user, status, reason, evidence):
    """Баримтгүйгээр төлөв өөрчлөх боломжгүй. Түүхийг заавал хадгална."""
    if status not in PledgeStatus.values:
        raise ValidationError({"status": ["Буруу төлөв."]})
    if status == pledge.status:
        raise ValidationError({"status": ["Төлөв өөрчлөгдөөгүй байна."]})
    if not reason.strip():
        raise Unprocessable("Шалтгаан заавал бичнэ.")
    ev = evidence or {}
    if not str(ev.get("source", "")).strip() or not ev.get("date"):
        raise Unprocessable("Нотлох баримтын эх сурвалж, огноо заавал (баримтгүйгээр төлөв өөрчлөх боломжгүй).")
    e = PledgeEvidence.objects.create(
        pledge=pledge, kind=ev.get("kind", "document"), source=ev["source"], date=ev["date"],
        url=ev.get("url", ""), note=ev.get("note", ""), added_by=user)
    old = pledge.status
    pledge.status = status
    pledge.save(update_fields=["status", "updated_at"])
    PledgeStatusHistory.objects.create(pledge=pledge, old_status=old, new_status=status, reason=reason,
                                       evidence=e, changed_by=user)
    audit.log(user, "pledge.status", "pledge", pledge.pk, {"status": old}, {"status": status}, reason)
    return pledge
