from rest_framework import serializers
from .models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    actor_email = serializers.CharField(source="actor.email", default=None, read_only=True)

    class Meta:
        model = AuditLog
        fields = ["id", "actor", "actor_email", "action", "entity_type", "entity_id",
                  "before", "after", "reason", "created_at"]
