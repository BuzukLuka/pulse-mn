import hashlib
import re
from difflib import SequenceMatcher
from pathlib import Path

from django.conf import settings
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.audit import models as audit
from apps.common.exceptions import Conflict, Unprocessable
from apps.notifications.services import notify, notify_editors
from .models import Content, ContentVersion, Media, Status

EXT_KIND = {"jpg": "image", "jpeg": "image", "png": "image", "webp": "image",
            "mp4": "video", "mov": "video", "pdf": "document"}


# ---------- UC-01 ----------
def validate_for_submit(content):
    """validate(): заавал талбар, формат, хэмжээ (400 — алдааны жагсаалт)."""
    errors = {}
    if len(content.title.strip()) < 5:
        errors["title"] = ["Гарчиг дор хаяж 5 тэмдэгт байна."]
    if len(content.body.strip()) < 50:
        errors["body"] = ["Агуулга дор хаяж 50 тэмдэгт байна."]
    if not content.category_id:
        errors["category"] = ["Төрөл сонгоно уу."]
    if not content.province_id:
        errors["province"] = ["Аймаг сонгоно уу."]
    if not content.event_date:
        errors["event_date"] = ["Огноо заавал."]
    elif content.event_date > timezone.localdate():
        errors["event_date"] = ["Ирээдүйн огноо байж болохгүй."]
    if not content.source.strip():
        errors["source"] = ["Эх сурвалж заавал."]
    if not content.copyright_declared:
        errors["copyright_declared"] = ["Зохиогчийн эрхийн мэдэгдэл (өөрийн материал эсвэл зөвшөөрөлтэй) заавал."]
    return errors


@transaction.atomic
def submit(content, actor):
    if not content.can_transition(Status.UNDER_REVIEW):
        raise Conflict(f"'{content.get_status_display()}' төлөвтэй контентыг илгээх боломжгүй.")
    if not content.author.is_verified:
        raise Unprocessable("Зөвхөн баталгаажсан сэтгүүлч мэдээ илгээнэ. Профайлаас баталгаажуулалтын хүсэлт илгээнэ үү.")
    errors = validate_for_submit(content)
    if errors:
        raise ValidationError(errors)
    before = content.status
    content.status = Status.UNDER_REVIEW
    content.submitted_at = timezone.now()
    from apps.ai.checks import run_checks
    try:
        content.verification = run_checks(content, use_ai=False)  # хурдан, AI-гүй урьдчилсан шалгалт
    except Exception:  # noqa: BLE001 — шалгалт унавал илгээлтийг хаахгүй
        import logging
        logging.getLogger(__name__).exception("precheck failed")
    content.save(update_fields=["status", "submitted_at", "verification", "updated_at"])
    number = (content.versions.order_by("-number").values_list("number", flat=True).first() or 0) + 1
    ContentVersion.objects.create(content=content, number=number, title=content.title, body=content.body,
                                  source=content.source, tags=content.tags)
    audit.log(actor, "content.submit", "content", content.pk, {"status": before},
              {"status": content.status})
    notify_editors("Шинэ контент шалгалтад ирлээ", content.title, content.pk)
    if content.newsroom_id:
        notify(content.newsroom, "Танай сэтгүүлч шинэ мэдээ илгээлээ",
               f"{content.author.full_name or content.author.email}: {content.title}", content.pk)
    return content


def save_media(content, upload):
    ext = Path(upload.name).suffix.lower().lstrip(".")
    if ext not in settings.ALLOWED_UPLOAD_EXT:
        raise ValidationError({"file": [f"'.{ext}' формат дэмжигдэхгүй. Зөвшөөрөгдсөн: "
                                        + ", ".join(sorted(settings.ALLOWED_UPLOAD_EXT))]})
    if upload.size > settings.MAX_UPLOAD_MB * 1024 * 1024:
        raise ValidationError({"file": [f"Файл {settings.MAX_UPLOAD_MB}MB-аас хэтэрсэн."]})
    h = hashlib.sha256()
    for chunk in upload.chunks():
        h.update(chunk)
    upload.seek(0)
    phash = ""
    if EXT_KIND[ext] == "image":
        try:
            from apps.ai.checks import dhash
            phash = dhash(upload)
        except Exception:  # noqa: BLE001
            phash = ""
        upload.seek(0)
    return Media.objects.create(content=content, file=upload, kind=EXT_KIND[ext],
                                original_name=upload.name[:255], size=upload.size,
                                sha256=h.hexdigest(), phash=phash)


# ---------- UC-02 ----------
def _norm(s):
    return re.sub(r"\W+", " ", s.lower()).strip()


def find_duplicates(content, use_ai=False):
    """checkDuplicate: текст + яг ижил медиа + төстэй зураг (+ Gemini semantic)."""
    from apps.ai.checks import duplicate_items
    return [{**d, "reason": d["reason"]} for d in duplicate_items(content, use_ai=use_ai)]


REQUIRED_CHECKS = ["facts", "source", "rights"]
CHECKLIST = [("facts", "Баримт, тоо нотолгоотой", True), ("source", "Эх сурвалж найдвартай", True),
             ("rights", "Зохиогчийн эрх, зөвшөөрөл зөв", True), ("privacy", "Хувийн мэдээлэл хамгаалагдсан", False),
             ("tone", "Хэл найруулга, ёс зүй", False)]

DECISIONS = {
    "approve": Status.PUBLISHED,
    "return": Status.CHANGES_REQUESTED,
    "reject": Status.REJECTED,
}


@transaction.atomic
def decide(content, editor, decision, reason="", checklist=None):
    """decide(id, төрөл, шалтгаан) — Зөвшөөрөх / Засварт буцаах / Татгалзах."""
    if decision not in DECISIONS:
        raise ValidationError({"decision": ["approve, return, reject-ийн аль нэг байна."]})
    if decision != "approve" and not reason.strip():
        raise Unprocessable("Шалтгаан заавал бичнэ.")
    new_status = DECISIONS[decision]
    if checklist is not None:
        if not isinstance(checklist, dict):
            raise ValidationError({"checklist": ["Checklist объект байх ёстой."]})
        content.review_checklist = {k: bool(v) for k, v in checklist.items()}
        if decision == "approve" and not all(content.review_checklist.get(k) for k in REQUIRED_CHECKS):
            raise Unprocessable("Нийтлэхийн өмнө шалгах жагсаалтын заавал хэсгүүдийг баталгаажуулна уу.")
    if not content.can_transition(new_status):
        raise Conflict(f"'{content.get_status_display()}' төлөвөөс шийдвэр гаргах боломжгүй.")
    before = content.status
    content.status = new_status
    content.review_reason = reason.strip()
    content.reviewed_by = editor
    content.reviewed_at = timezone.now()
    if new_status == Status.PUBLISHED:
        content.published_at = timezone.now()
        if not content.ai_summary:
            from apps.ai.services import rules_suggest
            content.ai_summary = (content.ai_suggestion or {}).get("summary") or rules_suggest(
                content.title, content.body)["summary"]
    if new_status == Status.PUBLISHED and content.verification:
        content.verification = {**content.verification, "editor_verified": True,
                                "verified_at": timezone.now().isoformat()}
    content.save()
    audit.log(editor, f"content.{decision}", "content", content.pk, {"status": before},
              {"status": new_status}, reason)
    notify(content.author, f"Таны контент: {content.get_status_display()}",
           reason or content.title, content.pk)
    if content.newsroom_id:
        notify(content.newsroom, f"Редакторын шийдвэр: {content.get_status_display()}", content.title, content.pk)
    return content


HISTORY_LABELS = {
    "content.submit": "Шалгалтад илгээсэн", "content.approve": "Нийтлэгдсэн", "content.return": "Засварт буцаасан",
    "content.reject": "Татгалзсан", "content.hide": "Түр нуусан", "content.restore": "Сэргээсэн",
}


def status_history(content):
    rows = audit.AuditLog.objects.filter(entity_type="content", entity_id=str(content.pk),
                                         action__in=HISTORY_LABELS).select_related("actor").order_by("created_at")
    out = [{"action": "created", "label": "Ноорог үүсгэсэн", "at": content.created_at, "actor": None, "reason": ""}]
    for r in rows:
        out.append({"action": r.action, "label": HISTORY_LABELS[r.action], "at": r.created_at, "reason": r.reason,
                    "actor": (r.actor.full_name or r.actor.email) if r.actor else None,
                    "to": (r.after or {}).get("status")})
    return out


@transaction.atomic
def set_visibility(content, admin_user, hide, reason):
    """FR-062: зөрчилтэй нийтлэгдсэн мэдээг түр нуух / сэргээх."""
    if not reason.strip():
        raise Unprocessable("Шалтгаан заавал бичнэ.")
    target = Status.HIDDEN if hide else Status.PUBLISHED
    if not content.can_transition(target):
        raise Conflict("Энэ төлөвт үйлдэл хийх боломжгүй.")
    before = content.status
    content.status = target
    content.save(update_fields=["status", "updated_at"])
    audit.log(admin_user, "content.hide" if hide else "content.restore", "content", content.pk,
              {"status": before}, {"status": target}, reason)
    return content
