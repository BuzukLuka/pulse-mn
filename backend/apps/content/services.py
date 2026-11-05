import hashlib
import re
from difflib import SequenceMatcher
from pathlib import Path

from django.conf import settings
from django.db import transaction
from django.db.models import Q
from datetime import timedelta

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
    problems = compliance_problems(content.compliance or {})
    if problems:
        errors["compliance"] = problems
    return errors


# Сэтгүүлчийн хууль ёсны мэдэгдэл. Үндэслэл: Хэвлэлийн эрх чөлөөний тухай хууль, Зөрчлийн тухай хууль (гүтгэх),
# Хувийн мэдээлэл хамгаалах тухай хууль, Хүүхдийн эрхийн тухай хууль, Зар сурталчилгааны тухай хууль, Сонгуулийн хууль.
PERSONAL_DATA = {"none": "Хувь хүний мэдээлэл агуулаагүй", "consent": "Холбогдох хүний зөвшөөрөлтэй",
                 "public_interest": "Олон нийтийн ашиг сонирхолд (албан тушаалтан, нийтийн үйл ажиллагаа)"}


def compliance_problems(c):
    out = []
    if not c.get("facts_verified"):
        out.append("Баримтыг шалгасан, санаатай худал мэдээлэл агуулаагүй гэдгээ баталгаажуулна уу.")
    if not c.get("no_defamation"):
        out.append("Гүтгэлэг, доромжлол, үзэн ядалт өдөөсөн агуулгагүй гэдгээ баталгаажуулна уу.")
    if c.get("personal_data") not in PERSONAL_DATA:
        out.append("Хувь хүний мэдээллийн талаар сонголт хийнэ үү.")
    if c.get("minors_involved") and not c.get("minors_protected"):
        out.append("Хүүхдийн нэр, нүүр, хаягийг нууцалсан эсвэл асран хамгаалагчийн зөвшөөрөлтэй гэдгээ баталгаажуулна уу.")
    if (c.get("sponsored") or c.get("political_ad")) and not str(c.get("sponsor_name", "")).strip():
        out.append("Ивээн тэтгэсэн / улс төрийн сурталчилгааны захиалагчийг заана уу.")
    return out


@transaction.atomic
def submit(content, actor):
    if not content.can_transition(Status.UNDER_REVIEW):
        raise Conflict(f"'{content.get_status_display()}' төлөвтэй контентыг илгээх боломжгүй.")
    content.review_by = review_route(content)
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
    content.save(update_fields=["status", "submitted_at", "verification", "review_by", "updated_at"])
    number = (content.versions.order_by("-number").values_list("number", flat=True).first() or 0) + 1
    ContentVersion.objects.create(content=content, number=number, title=content.title, body=content.body,
                                  source=content.source, tags=content.tags)
    audit.log(actor, "content.submit", "content", content.pk, {"status": before},
              {"status": content.status})
    if content.review_by == "newsroom":
        for u in [content.newsroom, *content.newsroom.staff.filter(role="editor", is_active=True)]:
            notify(u, "Шалгах мэдээ ирлээ — танай редакц шийдвэр гаргана",
                   f"{content.author.full_name or content.author.email}: {content.title}", content.pk)
    else:
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


CHECKLIST = [("facts", "Баримт, тоо нотолгоотой", True), ("source", "Эх сурвалж найдвартай", True),
             ("rights", "Зохиогчийн эрх, зөвшөөрөл зөв", True),
             ("privacy", "Хувийн мэдээлэл хууль ёсны (зөвшөөрөл эсвэл нийтийн ашиг сонирхол)", True),
             ("defamation", "Гүтгэлэг, доромжлол, үзэн ядалт өдөөсөн агуулгагүй", True),
             ("minors", "Хүүхдийн нэр, нүүр, хаяг хамгаалагдсан (хамааралгүй бол тэмдэглэнэ)", True),
             ("ads", "Ивээн тэтгэсэн / улс төрийн сурталчилгааг тэмдэглэсэн", False),
             ("tone", "Хэл найруулга, ёс зүй", False)]
REQUIRED_CHECKS = [k for k, _, req in CHECKLIST if req]

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
                                "verified_at": timezone.now().isoformat(),
                                "verified_by": editor.full_name or editor.organization or "Pulse.mn редактор",
                                "verified_by_newsroom": content.review_by == "newsroom"}
    content.save()
    audit.log(editor, f"content.{decision}", "content", content.pk, {"status": before},
              {"status": new_status}, reason)
    notify(content.author, f"Таны контент: {content.get_status_display()}",
           reason or content.title, content.pk)
    if content.newsroom_id and content.newsroom_id != editor.pk:
        notify(content.newsroom, f"Редакторын шийдвэр: {content.get_status_display()}", content.title, content.pk)
    return content


def review_route(content):
    """Баталгаажсан редакцын идэвхтэй гишүүн тухайн редакцаараа илгээсэн бол редакц өөрөө шалгана."""
    from apps.newsroom.models import Membership
    nr = content.newsroom
    if nr and nr.is_verified and nr.is_active and Membership.objects.filter(
            newsroom=nr, journalist_id=content.author_id, status="active").exists():
        return "newsroom"
    return "pulse"


@transaction.atomic
def send_to_newsroom(content, actor, newsroom):
    """Илгээсэн / нийтлэгдсэн мэдээг дараа нь редакц руу явуулах (редакц сонгоогүй байсан бол)."""
    from apps.accounts.models import Role, User
    if content.status == Status.DRAFT:
        raise Conflict("Ноорогт редакцаа маягт дээрээс сонгоно уу.")
    if content.newsroom_id:
        raise Conflict("Энэ мэдээ аль хэдийн редакцад илгээгдсэн.")
    nr = User.objects.filter(pk=newsroom, role=Role.NEWSROOM, is_active=True).first() if newsroom else None
    if not nr:
        raise Unprocessable("Редакц олдсонгүй.")
    content.newsroom = nr
    content.save(update_fields=["newsroom", "updated_at"])
    audit.log(actor, "content.send_newsroom", "content", content.pk, None, {"newsroom": nr.pk})
    notify(nr, "Сэтгүүлч танай редакцад мэдээ илгээлээ",
           f"{content.author.full_name or content.author.email}: {content.title} ({content.get_status_display()})", content.pk)
    return content


FEATURE_HOURS = (6, 12, 24, 48, 72)


def can_feature(user, content):
    """Топ болгох эрх: редакц өөрийн редакцын мэдээнд, редакцын редактор мөн, Pulse.mn редактор ба админ бүх мэдээнд."""
    if user.role == "admin" or (user.role == "editor" and not user.newsroom_org_id):
        return True
    if user.role == "newsroom":
        return content.newsroom_id == user.pk
    return user.role == "editor" and content.newsroom_id == user.newsroom_org_id


@transaction.atomic
def request_feature(content, journalist, hours):
    if content.status != Status.PUBLISHED:
        raise Conflict("Зөвхөн нийтлэгдсэн мэдээг топ болгох хүсэлт илгээнэ.")
    if hours not in FEATURE_HOURS:
        raise Unprocessable("Хугацаа: 6, 12, 24, 48, 72 цагийн аль нэг.")
    content.feature_request_hours = hours
    content.save(update_fields=["feature_request_hours", "updated_at"])
    audit.log(journalist, "content.feature_request", "content", content.pk, None, {"hours": hours})
    title = f"Топ мэдээ болгох хүсэлт ({hours} цаг)"
    if content.newsroom_id:
        for u in [content.newsroom, *content.newsroom.staff.filter(role="editor", is_active=True)]:
            notify(u, title, content.title, content.pk)
    else:
        notify_editors(title, content.title, content.pk)
    return content


@transaction.atomic
def set_featured(content, actor, hours):
    """hours=0 бол топоос буулгана."""
    if not can_feature(actor, content):
        raise Unprocessable("Энэ мэдээг топ болгох эрхгүй.")
    if content.status != Status.PUBLISHED:
        raise Conflict("Зөвхөн нийтлэгдсэн мэдээ топ болно.")
    if hours and hours not in FEATURE_HOURS:
        raise Unprocessable("Хугацаа: 6, 12, 24, 48, 72 цагийн аль нэг.")
    before = content.featured_until.isoformat() if content.featured_until else None
    content.featured_until = timezone.now() + timedelta(hours=hours) if hours else None
    content.featured_by = actor if hours else None
    content.feature_request_hours = None
    content.save(update_fields=["featured_until", "featured_by", "feature_request_hours", "updated_at"])
    audit.log(actor, "content.feature" if hours else "content.unfeature", "content", content.pk,
              {"featured_until": before}, {"hours": hours})
    notify(content.author, f"Таны мэдээ {hours} цаг топ мэдээ боллоо" if hours else "Таны мэдээ топоос буулаа",
           content.title, content.pk)
    return content


HISTORY_LABELS = {
    "content.feature": "Топ мэдээ болсон", "content.unfeature": "Топоос буулгасан", "content.feature_request": "Топ хүсэлт илгээсэн",
    "content.send_newsroom": "Редакцад илгээсэн", "content.correction": "Залруулга нэмсэн",
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


LEGAL_BASES = {"court_order": "Шүүхийн шийдвэр", "privacy": "Хувийн мэдээлэл хамгаалах", "copyright": "Зохиогчийн эрх",
               "defamation": "Гүтгэлэг, нэр төр", "minor": "Хүүхдийн эрх", "election": "Сонгуулийн хууль",
               "ethics": "Ёс зүйн зөрчил", "other": "Бусад"}


@transaction.atomic
def add_correction(content, actor, kind, text):
    """Залруулга / хариу тайлбар нийтлэх (зөвхөн нийтлэгдсэн мэдээнд)."""
    from .models import Correction
    if content.status != Status.PUBLISHED:
        raise Conflict("Зөвхөн нийтлэгдсэн мэдээнд залруулга нэмнэ.")
    if kind not in dict(Correction.KINDS) or len(text.strip()) < 10:
        raise Unprocessable("Төрөл болон 10-аас дээш тэмдэгттэй тайлбар заавал.")
    c = Correction.objects.create(content=content, kind=kind, text=text.strip(), created_by=actor)
    audit.log(actor, "content.correction", "content", content.pk, None, {"kind": kind}, text.strip()[:200])
    notify(content.author, f"Таны мэдээнд {c.get_kind_display().lower()} нэмэгдлээ", text.strip()[:200], content.pk)
    return c


@transaction.atomic
def set_visibility(content, admin_user, hide, reason, legal_basis="other"):
    """FR-062: зөрчилтэй нийтлэгдсэн мэдээг түр нуух / сэргээх (нуухад хууль зүйн үндэслэл заана)."""
    if not reason.strip():
        raise Unprocessable("Шалтгаан заавал бичнэ.")
    if hide:
        if legal_basis not in LEGAL_BASES:
            raise Unprocessable("Хууль зүйн үндэслэл буруу.")
        reason = f"[{LEGAL_BASES[legal_basis]}] {reason.strip()}"
    target = Status.HIDDEN if hide else Status.PUBLISHED
    if not content.can_transition(target):
        raise Conflict("Энэ төлөвт үйлдэл хийх боломжгүй.")
    before = content.status
    content.status = target
    content.save(update_fields=["status", "updated_at"])
    audit.log(admin_user, "content.hide" if hide else "content.restore", "content", content.pk,
              {"status": before}, {"status": target}, reason)
    notify(content.author, "Таны мэдээг түр нуулаа" if hide else "Таны мэдээг сэргээлээ", reason, content.pk)
    return content
