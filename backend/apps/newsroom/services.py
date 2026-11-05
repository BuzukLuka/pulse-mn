"""Редакц ↔ сэтгүүлчийн харилцаа, ДЕМО төлбөр, үнэлгээ ба AI-ийн үнэлгээний санал."""
import logging
import secrets

from django.db import transaction
from django.db.models import Avg, Count
from django.utils import timezone

from apps.accounts.models import Role, User
from apps.ai import gemini
from apps.audit import models as audit
from apps.common.exceptions import Conflict, Unprocessable
from apps.notifications.services import notify
from .models import Membership, Purchase, Rating

log = logging.getLogger(__name__)


def display_name(u):
    return u.full_name or u.organization or u.email.split("@")[0]


# ---------- Редакц ↔ сэтгүүлч ----------
@transaction.atomic
def request_membership(journalist, newsroom_id, message=""):
    newsroom = User.objects.filter(pk=newsroom_id, role=Role.NEWSROOM, is_active=True).first()
    if not newsroom:
        raise Unprocessable("Редакц олдсонгүй.")
    m, created = Membership.objects.get_or_create(newsroom=newsroom, journalist=journalist,
                                                  defaults={"message": message[:300]})
    if not created:
        if m.status in ("pending", "active"):
            raise Conflict("Энэ редакцад хүсэлт илгээсэн эсвэл аль хэдийн гишүүн байна.")
        m.status, m.message, m.decided_at = "pending", message[:300], None
        m.save(update_fields=["status", "message", "decided_at"])
    audit.log(journalist, "membership.request", "membership", m.pk, None, {"newsroom": newsroom.pk})
    notify(newsroom, "Шинэ сэтгүүлч нэгдэх хүсэлт илгээлээ",
           f"{display_name(journalist)}: {message or 'Редакцын сэтгүүлчээр бүртгүүлэх хүсэлт'}")
    return m


@transaction.atomic
def decide_membership(newsroom, membership, approve):
    if membership.newsroom_id != newsroom.pk:
        raise Unprocessable("Энэ хүсэлт таны редакцынх биш.")
    if membership.status != "pending":
        raise Conflict("Зөвхөн хүлээгдэж буй хүсэлтэд шийдвэр гаргана.")
    membership.status = "active" if approve else "rejected"
    membership.decided_at = timezone.now()
    membership.save(update_fields=["status", "decided_at"])
    audit.log(newsroom, "membership.approve" if approve else "membership.reject", "membership", membership.pk,
              {"status": "pending"}, {"status": membership.status})
    notify(membership.journalist, f"{display_name(newsroom)}: " + (
        "та редакцын сэтгүүлчээр бүртгэгдлээ" if approve else "нэгдэх хүсэлтийг хүлээж аваагүй"))
    return membership


@transaction.atomic
def end_membership(actor, membership):
    if actor.pk not in (membership.newsroom_id, membership.journalist_id):
        raise Unprocessable("Энэ гишүүнчлэлд хамааралгүй.")
    if membership.status not in ("active", "pending"):
        raise Conflict("Гишүүнчлэл аль хэдийн дууссан.")
    membership.status, membership.decided_at = "left", timezone.now()
    membership.save(update_fields=["status", "decided_at"])
    audit.log(actor, "membership.end", "membership", membership.pk, None, {"status": "left"})
    other = membership.journalist if actor.pk == membership.newsroom_id else membership.newsroom
    notify(other, f"{display_name(actor)} редакцын гишүүнчлэлийг цуцаллаа")
    return membership


def active_newsroom_ids(journalist):
    return set(Membership.objects.filter(journalist=journalist, status="active").values_list("newsroom_id", flat=True))


# ---------- Редакцын редакторууд ----------
@transaction.atomic
def create_staff_editor(newsroom, email, full_name, password):
    from django.contrib.auth.password_validation import validate_password
    from django.core.exceptions import ValidationError as DjangoValidationError
    from django.utils import timezone as tz
    email = (email or "").strip().lower()
    if not email or "@" not in email or not (full_name or "").strip():
        raise Unprocessable("Имэйл, нэр заавал.")
    if User.objects.filter(email__iexact=email).exists():
        raise Conflict("Энэ имэйлээр бүртгэл аль хэдийн байна.")
    try:
        validate_password(password or "")
    except DjangoValidationError as e:
        raise Unprocessable(" ".join(e.messages))
    now = tz.now()
    u = User.objects.create_user(email, password, role=Role.EDITOR, full_name=full_name.strip(), newsroom_org=newsroom,
                                 organization=newsroom.legal_name or newsroom.full_name, is_verified=True,
                                 terms_accepted_at=now, privacy_consent_at=now, ethics_accepted_at=now)
    audit.log(newsroom, "staff.create", "user", u.pk, None, {"role": "editor", "newsroom": newsroom.pk})
    notify(u, f"Та «{display_name(newsroom)}» редакцын редактороор бүртгэгдлээ", "Шалгах жагсаалтаас мэдээ шалгана.")
    return u


@transaction.atomic
def set_staff_active(newsroom, staff, active):
    from apps.accounts.services import revoke_sessions
    if staff.newsroom_org_id != newsroom.pk:
        raise Unprocessable("Энэ редактор танай редакцынх биш.")
    staff.is_active = bool(active)
    staff.save(update_fields=["is_active"])
    if not staff.is_active:
        revoke_sessions(staff)
    audit.log(newsroom, "staff.activate" if active else "staff.deactivate", "user", staff.pk)
    return staff


# ---------- Баталгаажуулалтын хүсэлт ----------
def request_verification(user):
    if user.is_verified:
        raise Conflict("Таны бүртгэл аль хэдийн баталгаажсан.")
    from apps.accounts.services import verification_missing
    missing = verification_missing(user)
    if missing:
        raise Unprocessable(missing)
    user.verification_requested_at = timezone.now()
    user.save(update_fields=["verification_requested_at"])
    audit.log(user, "user.verification_request", "user", user.pk)
    for admin in User.objects.filter(role=Role.ADMIN, is_active=True):
        notify(admin, "Баталгаажуулалтын шинэ хүсэлт", f"{display_name(user)} ({user.email})")
    return user


# ---------- ДЕМО төлбөр ----------
@transaction.atomic
def create_purchase(buyer, content, license_type="standard", accept_terms=False):
    from .payments import LICENSES, breakdown, get_provider
    if content.status != "published":
        raise Unprocessable("Зөвхөн нийтлэгдсэн мэдээг худалдан авна.")
    if not content.price:
        raise Unprocessable("Энэ мэдээ худалдаанд гараагүй.")
    if license_type not in LICENSES:
        raise Unprocessable("Лицензийн төрөл буруу.")
    if not accept_terms:
        raise Unprocessable("Лицензийн нөхцөл (зохиогчийн эрх, эх сурвалж заах) зөвшөөрнө үү.")
    if Purchase.objects.filter(content=content, license_type="exclusive", status="paid").exists():
        raise Conflict("Энэ мэдээний онцгой эрхийг өөр редакц авсан тул худалдаалах боломжгүй.")
    if license_type == "exclusive" and Purchase.objects.filter(content=content, status="paid").exclude(buyer=buyer).exists():
        raise Conflict("Энэ мэдээг өөр редакц аль хэдийн авсан тул онцгой эрх олгох боломжгүй.")
    existing = Purchase.objects.filter(buyer=buyer, content=content).exclude(status__in=["cancelled", "refunded"]).first()
    if existing:
        return existing
    provider = get_provider()
    gross = content.price * LICENSES[license_type][1]
    p = Purchase(buyer=buyer, content=content, license_type=license_type, provider=provider.name,
                 invoice_code=f"PMN-{secrets.token_hex(4).upper()}", terms_accepted_at=timezone.now(), **breakdown(gross))
    p.provider_ref = provider.create_invoice(p)["provider_ref"]
    p.save()
    audit.log(buyer, "purchase.create", "purchase", p.pk, None,
              {"content": content.pk, "amount": p.amount, "license": license_type})
    return p


@transaction.atomic
def confirm_purchase(buyer, purchase):
    """ДЕМО: бодит төлбөрийн шлюз (QPay гэх мэт) холбогдох хүртэл төлбөрийг гараар баталгаажуулна."""
    if purchase.buyer_id != buyer.pk:
        raise Unprocessable("Энэ нэхэмжлэх таных биш.")
    if purchase.status != "pending":
        raise Conflict("Нэхэмжлэх аль хэдийн шийдэгдсэн.")
    from .payments import get_provider
    if purchase.license_type == "exclusive" and Purchase.objects.filter(
            content=purchase.content, status="paid").exclude(pk=purchase.pk).exists():
        raise Conflict("Энэ хооронд өөр редакц худалдан авсан тул онцгой эрх олгох боломжгүй.")
    purchase.status, purchase.paid_at = "paid", timezone.now()
    purchase.ebarimt_no = get_provider().issue_receipt(purchase)
    purchase.save(update_fields=["status", "paid_at", "ebarimt_no"])
    audit.log(buyer, "purchase.paid", "purchase", purchase.pk, {"status": "pending"}, {"status": "paid"})
    notify(purchase.content.author, "Таны мэдээг редакц худалдан авлаа",
           f"{display_name(buyer)} · {purchase.content.title} · {purchase.get_license_type_display()} · "
           f"танд {purchase.author_net:,}₮ (НӨАТ, шимтгэл хассан)", purchase.content_id)
    return purchase


@transaction.atomic
def refund_purchase(admin, purchase, reason):
    """Админ төлөгдсөн худалдан авалтыг буцаана (маргаан, зохиогчийн эрхийн зөрчил гэх мэт)."""
    if purchase.status != "paid":
        raise Conflict("Зөвхөн төлөгдсөн худалдан авалтыг буцаана.")
    if not reason.strip():
        raise Unprocessable("Буцаалтын шалтгаан заавал.")
    purchase.status, purchase.refund_reason = "refunded", reason.strip()[:300]
    purchase.save(update_fields=["status", "refund_reason"])
    audit.log(admin, "purchase.refund", "purchase", purchase.pk, {"status": "paid"}, {"status": "refunded"}, reason)
    for u in (purchase.buyer, purchase.content.author):
        notify(u, "Худалдан авалтыг буцаалаа", f"{purchase.content.title} · {reason.strip()[:200]}", purchase.content_id)
    return purchase


@transaction.atomic
def cancel_purchase(buyer, purchase):
    if purchase.buyer_id != buyer.pk or purchase.status != "pending":
        raise Conflict("Зөвхөн төлөгдөөгүй өөрийн нэхэмжлэхийг цуцална.")
    purchase.status = "cancelled"
    purchase.save(update_fields=["status"])
    return purchase


# ---------- Үнэлгээ ----------
def rating_summary(target):
    qs = Rating.objects.filter(target=target)
    agg = qs.aggregate(avg=Avg("score"), n=Count("id"))
    dist = dict(qs.values_list("score").annotate(c=Count("id")))
    return {"avg": round(agg["avg"], 2) if agg["avg"] else None, "count": agg["n"],
            "distribution": {s: dist.get(s, 0) for s in range(1, 6)}}


@transaction.atomic
def rate(rater, target, score, comment="", content=None):
    if rater.pk == target.pk:
        raise Unprocessable("Өөрийгөө үнэлэх боломжгүй.")
    if target.role not in (Role.JOURNALIST, Role.NEWSROOM):
        raise Unprocessable("Зөвхөн сэтгүүлч эсвэл редакцыг үнэлнэ.")
    if not isinstance(score, int) or not 1 <= score <= 5:
        raise Unprocessable("Үнэлгээ 1–5 байна.")
    r, _ = Rating.objects.update_or_create(rater=rater, target=target, defaults={
        "score": score, "comment": comment[:500], "content": content})
    audit.log(rater, "rating.set", "user", target.pk, None, {"score": score})
    return r


def _metrics(target):
    from apps.complaints.models import Complaint
    from apps.content.models import Content
    field = "author" if target.role == Role.JOURNALIST else "newsroom"
    qs = Content.objects.filter(**{field: target}).exclude(status="draft")
    by = dict(qs.values_list("status").annotate(n=Count("id")))
    published = qs.filter(status="published")
    trust = [c.verification.get("score") for c in published.only("verification")[:200]
             if c.verification and c.verification.get("score") is not None]
    complaints = Complaint.objects.filter(target_type="content", target_id__in=qs.values("id"))
    m = {
        "role": target.role, "verified": target.is_verified, "submitted": sum(by.values()),
        "published": by.get("published", 0), "rejected": by.get("rejected", 0),
        "changes_requested": by.get("changes_requested", 0),
        "avg_trust": round(sum(trust) / len(trust), 1) if trust else None,
        "complaints_upheld": complaints.filter(status="resolved").count(),
        "user_avg": rating_summary(target)["avg"],
    }
    if target.role == Role.NEWSROOM:
        m["members"] = Membership.objects.filter(newsroom=target, status="active").count()
        m["purchases_paid"] = Purchase.objects.filter(buyer=target, status="paid").count()
    return m


def _rules_score(m):
    """Тайлбарлах боломжтой энгийн жин: батлагдсан хувь, Pulse Trust, гомдол, баталгаажуулалт."""
    reasons, score = [], 3.0
    if m["submitted"]:
        ratio = m["published"] / m["submitted"]
        score += (ratio - 0.6) * 2.5
        reasons.append(f"Илгээсэн {m['submitted']} мэдээний {round(ratio * 100)}% нь нийтлэгдсэн.")
    else:
        reasons.append("Шалгалтад илгээсэн мэдээ алга — үнэлгээ урьдчилсан.")
    if m["avg_trust"] is not None:
        score += (m["avg_trust"] - 70) / 30
        reasons.append(f"Нийтлэгдсэн мэдээний Pulse Trust дундаж {m['avg_trust']}.")
    if m["rejected"]:
        score -= min(1.0, m["rejected"] * 0.15)
        reasons.append(f"{m['rejected']} мэдээ татгалзагдсан.")
    if m["complaints_upheld"]:
        score -= min(1.0, m["complaints_upheld"] * 0.3)
        reasons.append(f"{m['complaints_upheld']} гомдол үндэслэлтэй гэж шийдэгдсэн.")
    if m["verified"]:
        score += 0.3
        reasons.append("Баталгаажсан бүртгэлтэй.")
    if m.get("members"):
        reasons.append(f"{m['members']} идэвхтэй сэтгүүлчтэй.")
    return max(1.0, min(5.0, round(score, 1))), reasons


def suggest_rating(target):
    """AI-ийн үнэлгээний санал: үзүүлэлтээс тооцоолж, Gemini байвал тайлбарыг сайжруулна. Шийдвэр — хэрэглэгчийнх."""
    m = _metrics(target)
    score, reasons = _rules_score(m)
    out = {"score": score, "reasons": reasons, "metrics": m, "source": "rules"}
    if gemini.is_configured() and m["submitted"]:
        prompt = (
            "Чи мэдээний платформын чанарын шинжээч. Доорх үзүүлэлтээр "
            f"{'сэтгүүлч' if m['role'] == 'journalist' else 'редакц'}-ийг 1-5 онооны хооронд үнэл. "
            "Зөвхөн өгөгдсөн тоонд тулгуурла, таамаглал бүү нэм.\n"
            f"Үзүүлэлт (JSON): {m}\nДүрэмд суурилсан урьдчилсан оноо: {score}\n"
            'JSON буцаа: {"score": 1.0-5.0, "reasons": ["Монголоор 2-4 богино шалтгаан"]}'
        )
        try:
            d = gemini.generate_json(prompt)
            s = float(d.get("score", score))
            out.update(score=max(1.0, min(5.0, round(s, 1))),
                       reasons=[str(r)[:200] for r in d.get("reasons", [])][:4] or reasons, source="gemini")
        except Exception:  # noqa: BLE001 — AI унавал дүрмийн санал хэвээр
            log.exception("Gemini rating suggestion failed")
    return out


def newsroom_card(u):
    return {"id": u.id, "name": display_name(u), "organization": u.organization, "is_verified": u.is_verified,
            "province": u.province.name if u.province_id else None, "bio": u.bio,
            "members": Membership.objects.filter(newsroom=u, status="active").count(),
            "rating": rating_summary(u)}


def visible_members(newsroom):
    return Membership.objects.filter(newsroom=newsroom).select_related("journalist", "journalist__province")


def journalist_card(u):
    return {"id": u.id, "name": display_name(u), "is_verified": u.is_verified, "email": u.email,
            "province": u.province.name if u.province_id else None, "rating": rating_summary(u),
            "published": u.contents.filter(status="published").count()}

