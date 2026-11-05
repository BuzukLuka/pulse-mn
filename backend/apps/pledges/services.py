from django.db import transaction
from rest_framework.exceptions import ValidationError

from apps.audit import models as audit
from apps.common.exceptions import Unprocessable
from .models import PledgeUpdate, PledgeEvidence, PledgeStatus, PledgeStatusHistory


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


# ---------- Иргэний явцын мэдээ: AI урьдчилсан шалгалт, админы баталгаажуулалт ----------
import hashlib  # noqa: E402
import math  # noqa: E402


def _km(a_lat, a_lng, b_lat, b_lng):
    r = 6371.0
    p1, p2 = math.radians(a_lat), math.radians(b_lat)
    dp, dl = p2 - p1, math.radians(b_lng - a_lng)
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(h))


def check_update(upd):
    """Урьдчилсан шалгалт: зураг давхардсан эсэх (яг ижил / төстэй), амлалтын байршлаас зай, тайлбарын хэмжээ."""
    from apps.content.models import Media
    flags, score = [], 100
    if upd.photo_sha256:
        if (PledgeUpdate.objects.filter(photo_sha256=upd.photo_sha256).exclude(pk=upd.pk).exists()
                or Media.objects.filter(sha256=upd.photo_sha256).exists()):
            flags.append("Яг ижил зураг өмнө нь оруулагдсан"); score -= 50
        elif upd.photo_phash:
            from apps.ai.checks import hamming
            for ph in PledgeUpdate.objects.exclude(pk=upd.pk).exclude(photo_phash="").values_list("photo_phash", flat=True)[:500]:
                if hamming(ph, upd.photo_phash) <= 6:
                    flags.append("Төстэй зураг өмнө нь оруулагдсан"); score -= 25
                    break
    else:
        flags.append("Зураг хавсаргаагүй"); score -= 30
    dist = None
    p = upd.pledge
    if None not in (p.lat, p.lng, upd.lat, upd.lng):
        dist = round(_km(p.lat, p.lng, upd.lat, upd.lng), 2)
        if dist > 5:
            flags.append(f"Амлалтын байршлаас {dist} км зайтай"); score -= 25
    if len(upd.text.strip()) < 30:
        flags.append("Тайлбар хэт богино"); score -= 10
    return {"score": max(0, score), "flags": flags, "distance_km": dist, "source": "rules"}


@transaction.atomic
def submit_update(pledge, user, text, photo=None, lat=None, lng=None, progress=None):
    if len((text or "").strip()) < 10:
        raise Unprocessable("Явцын тайлбарыг 10-аас дээш тэмдэгтээр бичнэ үү.")
    upd = PledgeUpdate(pledge=pledge, author=user, text=text.strip(), lat=lat, lng=lng,
                       progress_claim=progress if progress is not None and 0 <= progress <= 100 else None)
    if photo:
        from pathlib import Path
        if Path(photo.name).suffix.lower().lstrip(".") not in {"jpg", "jpeg", "png", "webp"}:
            raise Unprocessable("Зөвхөн jpg, png, webp зураг.")
        if photo.size > 10 * 1024 * 1024:
            raise Unprocessable("Зураг 10MB-аас хэтэрсэн.")
        h = hashlib.sha256()
        for chunk in photo.chunks():
            h.update(chunk)
        photo.seek(0)
        upd.photo_sha256 = h.hexdigest()
        try:
            from apps.ai.checks import dhash
            upd.photo_phash = dhash(photo)
        except Exception:  # noqa: BLE001
            upd.photo_phash = ""
        photo.seek(0)
        upd.photo = photo
    upd.save()
    upd.ai_check = check_update(upd)
    upd.save(update_fields=["ai_check"])
    audit.log(user, "pledge.update_submit", "pledge", pledge.pk, None, {"update": upd.pk, "score": upd.ai_check["score"]})
    return upd


@transaction.atomic
def review_update(admin, upd, approve, note="", progress=None):
    from django.utils import timezone
    from apps.notifications.services import notify
    if upd.status != "pending":
        raise Unprocessable("Энэ мэдээг аль хэдийн шийдсэн.")
    upd.status = "verified" if approve else "rejected"
    upd.review_note, upd.reviewed_by, upd.reviewed_at = note[:500], admin, timezone.now()
    upd.save(update_fields=["status", "review_note", "reviewed_by", "reviewed_at"])
    if approve:
        p = upd.pledge
        if progress is not None and 0 <= progress <= 100:
            p.progress = progress
            p.save(update_fields=["progress", "updated_at"])
        PledgeEvidence.objects.create(pledge=p, kind="photo", source="Иргэний баталгаажсан мэдээ",
                                      date=upd.created_at.date(), url=upd.photo.url if upd.photo else "", note=upd.text[:300],
                                      added_by=admin)
    audit.log(admin, "pledge.update_verify" if approve else "pledge.update_reject", "pledge", upd.pledge_id, None,
              {"update": upd.pk}, note)
    notify(upd.author, "Таны оруулсан явцын мэдээ " + ("баталгаажлаа" if approve else "хүлээн авагдсангүй"), note or upd.pledge.text[:120])
    return upd
