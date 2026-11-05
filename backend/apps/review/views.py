from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.ai import services as ai
from apps.common.permissions import roles
from apps.content import services
from apps.content.models import Content, Status
from apps.content.serializers import ContentSerializer, VersionSerializer


class ReviewViewSet(viewsets.ReadOnlyModelViewSet):
    """UC-02: Редактор контент шалгаж шийдвэр гаргах."""
    permission_classes = [roles("editor", "admin")]
    serializer_class = ContentSerializer

    def get_queryset(self):
        qs = Content.objects.exclude(status=Status.DRAFT).select_related(
            "category", "province", "district", "author").prefetch_related("media")
        u = self.request.user
        if u.role == "editor" and u.newsroom_org_id:
            qs = qs.filter(review_by="newsroom", newsroom_id=u.newsroom_org_id)  # зөвхөн өөрийн редакцынх
        elif u.role != "admin":
            qs = qs.exclude(review_by="newsroom")
        if self.action == "list":  # төлвийн шүүлтүүр зөвхөн жагсаалтад
            st = self.request.query_params.get("status", Status.UNDER_REVIEW)
            if st != "all":
                qs = qs.filter(status=st)
        # ирсэн дарааллаар (хамгийн эрт ирсэн нь эхэнд)
        return qs.order_by("submitted_at", "id")

    def retrieve(self, request, *args, **kwargs):
        obj = self.get_object()
        data = self.get_serializer(obj).data
        data["duplicates"] = services.find_duplicates(obj)  # checkDuplicate
        data["checklist_items"] = [{"key": k, "label": l, "required": r} for k, l, r in services.CHECKLIST]
        data["versions"] = VersionSerializer(obj.versions.all(), many=True).data
        return Response(data)

    @action(detail=True, methods=["post"])
    def decide(self, request, pk=None):
        obj = self.get_object()
        if obj.review_by == "newsroom" and request.user.newsroom_org_id != obj.newsroom_id:
            from apps.common.exceptions import Conflict
            raise Conflict("Энэ мэдээг редакц өөрөө шалгаж нийтэлнэ. Pulse.mn нийтэлсний дараах хяналт хийнэ.")
        obj = services.decide(obj, request.user,
                              str(request.data.get("decision", "")),
                              str(request.data.get("reason", "")),
                              request.data.get("checklist"))
        return Response(self.get_serializer(obj).data)

    @action(detail=True, methods=["post"])
    def corrections(self, request, pk=None):
        """Залруулга / хариу тайлбар нийтлэх."""
        from apps.content.serializers import CorrectionSerializer
        c = services.add_correction(self.get_object(), request.user, str(request.data.get("kind", "correction")),
                                    str(request.data.get("text", "")))
        return Response(CorrectionSerializer(c).data, status=201)

    @action(detail=True, methods=["post"], url_path="ai-check")
    def ai_check(self, request, pk=None):
        """Gemini-аар мэдээг хянуулах (редакторт туслах санал, шийдвэр биш)."""
        obj = self.get_object()
        from apps.ai.checks import run_checks
        result = run_checks(obj, use_ai=True)
        obj.verification = {**result, "editor_verified": (obj.verification or {}).get("editor_verified", False)}
        obj.save(update_fields=["verification", "ai_review", "embedding", "updated_at"])
        return Response({**result, **(obj.ai_review or {}), "trust": result})
