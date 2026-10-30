from rest_framework import generics
from apps.common.permissions import roles
from .models import AuditLog
from .serializers import AuditLogSerializer


class AuditLogList(generics.ListAPIView):
    permission_classes = [roles("admin")]
    serializer_class = AuditLogSerializer

    def get_queryset(self):
        qs = AuditLog.objects.select_related("actor")
        p = self.request.query_params
        if p.get("entity_type"):
            qs = qs.filter(entity_type=p["entity_type"])
        if p.get("action"):
            qs = qs.filter(action=p["action"])
        return qs
