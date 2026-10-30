from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                              on_delete=models.SET_NULL, related_name="audit_entries")
    action = models.CharField(max_length=60, db_index=True)
    entity_type = models.CharField(max_length=40, db_index=True)
    entity_id = models.CharField(max_length=40)
    before = models.JSONField(null=True, blank=True)
    after = models.JSONField(null=True, blank=True)
    reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at", "-id"]


def log(actor, action, entity_type, entity_id, before=None, after=None, reason=""):
    """Хэн, хэзээ, юу өөрчилсөнийг хадгална (FR-071, NFR-010)."""
    return AuditLog.objects.create(
        actor=actor, action=action, entity_type=entity_type, entity_id=str(entity_id),
        before=before, after=after, reason=reason or "",
    )
