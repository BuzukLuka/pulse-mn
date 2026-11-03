from django.db import transaction
from django.utils import timezone
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken

from apps.audit import models as audit
from apps.common.exceptions import Conflict, Unprocessable
from .models import Role, User


def revoke_sessions(user):
    """Хэрэглэгчийн бүх refresh token-ыг хүчингүй болгоно (UC-03)."""
    for t in OutstandingToken.objects.filter(user=user):
        BlacklistedToken.objects.get_or_create(token=t)


@transaction.atomic
def update_access(actor, target, role=None, is_active=None, reason=""):
    """UC-03 updateAccess(userId, role | status, шалтгаан)."""
    if role is None and is_active is None:
        raise Unprocessable("Шинэ эрх эсвэл төлөв заавал.")
    if not reason.strip():
        raise Unprocessable("Шалтгаан заавал бичнэ.")
    new_role = role if role is not None else target.role
    new_active = is_active if is_active is not None else target.is_active

    loses_admin = target.role == Role.ADMIN and target.is_active and (
        new_role != Role.ADMIN or not new_active)
    if loses_admin:
        active_admins = User.objects.filter(role=Role.ADMIN, is_active=True).count()
        if active_admins <= 1:
            raise Conflict("Сүүлчийн админы эрхийг хасах боломжгүй.")

    before = {"role": target.role, "is_active": target.is_active}
    target.role, target.is_active = new_role, new_active
    target.save(update_fields=["role", "is_active"])
    revoke_sessions(target)
    audit.log(actor, "user.update_access", "user", target.pk, before,
              {"role": target.role, "is_active": target.is_active}, reason)
    from apps.notifications.services import notify
    notify(target, "Таны эрх өөрчлөгдлөө", reason)
    return target


@transaction.atomic
def set_verified(actor, target, verified, reason=""):
    """«Баталгаажсан сэтгүүлч» тэмдэг олгох / авах (аудитад бүртгэнэ)."""
    if not reason.strip():
        raise Unprocessable("Шалтгаан заавал бичнэ.")
    before = {"is_verified": target.is_verified}
    target.is_verified = verified
    target.verification_requested_at = None
    target.save(update_fields=["is_verified", "verification_requested_at"])
    audit.log(actor, "user.verify", "user", target.pk, before, {"is_verified": verified}, reason)
    from apps.notifications.services import notify
    notify(target, "Таны бүртгэл баталгаажлаа" if verified else "Баталгаажуулалт цуцлагдлаа", reason)


# ---------- Хувийн мэдээллийн субъектийн эрх (Хувийн мэдээлэл хамгаалах тухай хууль) ----------
def export_personal_data(user):
    """Хэрэглэгч өөрийн тухай хадгалсан бүх мэдээллийг авах эрх."""
    from apps.complaints.models import Complaint
    from apps.content.models import Content
    from apps.newsroom.models import Membership, Purchase, Rating
    from apps.notifications.models import Notification
    from .serializers import UserSerializer
    return {
        "exported_at": timezone.now().isoformat(),
        "profile": UserSerializer(user).data,
        "content": list(Content.objects.filter(author=user).values("id", "title", "status", "created_at", "published_at")),
        "complaints": list(Complaint.objects.filter(reporter=user).values("id", "target_type", "target_id", "kind", "text", "status", "created_at")),
        "ratings_given": list(Rating.objects.filter(rater=user).values("target_id", "score", "comment", "updated_at")),
        "memberships": list(Membership.objects.filter(journalist=user).values("newsroom_id", "status", "created_at")),
        "purchases": list(Purchase.objects.filter(buyer=user).values("id", "content_id", "amount", "status", "created_at")),
        "notifications": list(Notification.objects.filter(user=user).values("title", "body", "created_at")[:500]),
        "audit": list(audit.AuditLog.objects.filter(actor=user).values("action", "entity_type", "entity_id", "created_at")[:500]),
    }


@transaction.atomic
def delete_account(user, password, reason=""):
    """Бүртгэл устгах: хувийн мэдээллийг нууцлан (anonymize) идэвхгүй болгоно.
    Нийтлэгдсэн мэдээ олон нийтийн ашиг сонирхол, аудитын шаардлагаар «Устгагдсан хэрэглэгч» нэрээр үлдэнэ."""
    if not user.check_password(password):
        raise Unprocessable("Нууц үг буруу.")
    if user.role == Role.ADMIN and User.objects.filter(role=Role.ADMIN, is_active=True).count() <= 1:
        raise Conflict("Сүүлчийн админы бүртгэлийг устгах боломжгүй.")
    from apps.newsroom.models import Membership, Rating
    from apps.notifications.models import Notification
    revoke_sessions(user)
    Membership.objects.filter(journalist=user).delete()
    Rating.objects.filter(rater=user).delete()
    Notification.objects.filter(user=user).delete()
    user.experiences.all().delete(); user.portfolio.all().delete()
    user.email = f"deleted-{user.pk}@deleted.pulse.mn"
    user.full_name, user.phone, user.bio, user.press_card_no = "Устгагдсан хэрэглэгч", "", "", ""
    user.show_email = user.show_phone = False
    user.is_active, user.anonymized_at = False, timezone.now()
    user.set_unusable_password()
    user.save()
    audit.log(None, "user.delete", "user", user.pk, None, {"anonymized": True}, reason or "Хэрэглэгч өөрөө устгасан")
    return user


def verification_missing(user):
    """Баталгаажуулалт хүсэхээс өмнө бөглөх ёстой хууль ёсны мэдээлэл."""
    if user.role == Role.JOURNALIST and not (user.press_card_no.strip() or user.organization.strip()):
        return "Сэтгүүлчийн үнэмлэхийн дугаар эсвэл ажилладаг байгууллагаа профайлдаа оруулна уу."
    if user.role == Role.NEWSROOM and not (user.registry_no and user.legal_name and user.responsible_editor):
        return "Хуулийн этгээдийн нэр, регистрийн дугаар, хариуцлагатай эрхлэгчийг профайлдаа оруулна уу."
    return None
