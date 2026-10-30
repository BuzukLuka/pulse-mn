from django.db import transaction
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
    target.save(update_fields=["is_verified"])
    audit.log(actor, "user.verify", "user", target.pk, before, {"is_verified": verified}, reason)
