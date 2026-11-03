from django.db import transaction
from django.utils import timezone
from rest_framework import mixins, serializers, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.audit import models as audit
from apps.common.exceptions import Unprocessable
from apps.common.permissions import roles
from apps.notifications.services import notify
from .models import Complaint


class ComplaintSerializer(serializers.ModelSerializer):
    reporter_email = serializers.CharField(source="reporter.email", read_only=True)
    resolved_by_email = serializers.CharField(source="resolved_by.email", default=None, read_only=True)

    class Meta:
        model = Complaint
        fields = ["id", "target_type", "target_id", "kind", "text", "evidence_url", "status", "resolution",
                  "reporter_email", "resolved_by_email", "resolved_at", "created_at"]
        read_only_fields = ["status", "resolution", "resolved_at"]

    def validate_text(self, v):
        if len(v.strip()) < 10:
            raise serializers.ValidationError("Дор хаяж 10 тэмдэгтээр тайлбарлана уу.")
        return v

    def validate(self, a):
        from apps.content.models import Content
        from apps.pledges.models import Pledge
        from apps.statistics.models import Indicator
        model = {"content": Content, "pledge": Pledge, "indicator": Indicator}[a["target_type"]]
        if not model.objects.filter(pk=a["target_id"]).exists():
            raise serializers.ValidationError({"target_id": "Холбогдох объект олдсонгүй."})
        return a


class MyComplaintViewSet(mixins.CreateModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    """Иргэн/сэтгүүлч гомдол гаргана. Нийтэд шууд харагдахгүй — эхлээд админ шалгана."""
    serializer_class = ComplaintSerializer

    def get_queryset(self):
        return Complaint.objects.filter(reporter=self.request.user)

    def perform_create(self, s):
        c = s.save(reporter=self.request.user)
        audit.log(self.request.user, "complaint.create", "complaint", c.pk, after={"target": f"{c.target_type}#{c.target_id}"})


class AdminComplaintViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    permission_classes = [roles("admin")]
    serializer_class = ComplaintSerializer

    def get_queryset(self):
        qs = Complaint.objects.select_related("reporter", "resolved_by")
        if self.request.query_params.get("status"):
            qs = qs.filter(status=self.request.query_params["status"])
        return qs

    @action(detail=True, methods=["post"])
    @transaction.atomic
    def resolve(self, request, pk=None):
        c = self.get_object()
        st = request.data.get("status")
        if st not in ("resolved", "dismissed"):
            raise serializers.ValidationError({"status": ["resolved эсвэл dismissed."]})
        res = str(request.data.get("resolution", "")).strip()
        if not res:
            raise Unprocessable("Шийдвэрийн тайлбар заавал.")
        before = {"status": c.status}
        c.status, c.resolution, c.resolved_by, c.resolved_at = st, res, request.user, timezone.now()
        c.save()
        audit.log(request.user, "complaint.resolve", "complaint", c.pk, before, {"status": st}, res)
        # Мэдээний гомдлыг үндэслэлтэй гэж үзвэл залруулга / хариу тайлбарыг мэдээн дээр нийтэлнэ
        correction = str(request.data.get("correction", "")).strip()
        if st == "resolved" and correction and c.target_type == "content":
            from apps.content.models import Content
            from apps.content.services import add_correction
            add_correction(Content.objects.get(pk=c.target_id), request.user,
                           "reply" if c.kind == "reply" else "correction", correction)
        notify(c.reporter, "Таны гомдол шийдвэрлэгдлээ", res)
        return Response(self.get_serializer(c).data)
