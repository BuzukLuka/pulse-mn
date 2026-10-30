from django.db.models import Q
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response

from apps.ai import services as ai
from apps.catalog.models import Category
from apps.common.exceptions import Conflict
from apps.common.permissions import roles
from . import services
from .models import Content, Media, Status
from .serializers import ContentSerializer, MediaSerializer, PublicContentSerializer, VersionSerializer

EDITABLE = {Status.DRAFT, Status.CHANGES_REQUESTED}


class MyContentViewSet(viewsets.ModelViewSet):
    """UC-01: Сэтгүүлч контент оруулах, засах, шалгалтад илгээх."""
    permission_classes = [roles("journalist")]
    serializer_class = ContentSerializer
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get_queryset(self):
        qs = Content.objects.filter(author=self.request.user).select_related(
            "category", "province", "district", "author").prefetch_related("media")
        if self.request.query_params.get("status"):
            qs = qs.filter(status=self.request.query_params["status"])
        return qs

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def _ensure_editable(self, obj):
        if obj.status not in EDITABLE:
            raise Conflict("Энэ төлөвт контентыг засах боломжгүй.")

    def update(self, request, *args, **kwargs):
        self._ensure_editable(self.get_object())
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.status != Status.DRAFT:
            raise Conflict("Зөвхөн ноорог контентыг устгана.")
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=["post"])
    def submit(self, request, pk=None):
        obj = services.submit(self.get_object(), request.user)
        return Response(self.get_serializer(obj).data)

    @action(detail=True, methods=["post"], url_path="media")
    def add_media(self, request, pk=None):
        obj = self.get_object()
        self._ensure_editable(obj)
        files = request.FILES.getlist("file")
        if not files:
            raise ValidationError({"file": ["Файл сонгоно уу."]})
        created = [services.save_media(obj, f) for f in files]
        return Response(MediaSerializer(created, many=True, context={"request": request}).data,
                        status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["delete"], url_path=r"media/(?P<media_id>\d+)")
    def remove_media(self, request, pk=None, media_id=None):
        obj = self.get_object()
        self._ensure_editable(obj)
        Media.objects.filter(content=obj, pk=media_id).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["post"], url_path="precheck")
    def precheck(self, request, pk=None):
        """Илгээхээс өмнө өөрөө шалгах (Pulse Trust, AI-гүй хурдан шалгалт)."""
        from apps.ai.checks import run_checks
        obj = self.get_object()
        result = run_checks(obj, use_ai=False)
        Content.objects.filter(pk=obj.pk).update(verification=result)
        return Response(result)

    @action(detail=True, methods=["get"])
    def versions(self, request, pk=None):
        return Response(VersionSerializer(self.get_object().versions.all(), many=True).data)

    @action(detail=False, methods=["get"])
    def summary(self, request):
        """Сэтгүүлчийн хяналтын самбар: төлөв тус бүрийн тоо."""
        from django.db.models import Count
        rows = Content.objects.filter(author=request.user).values("status").annotate(n=Count("id"))
        out = {s.value: 0 for s in Status}
        out.update({r["status"]: r["n"] for r in rows})
        out["total"] = sum(out.values())
        return Response(out)

    @action(detail=False, methods=["post"], url_path="suggest-tags")
    def suggest_tags(self, request):
        """AI-аар ангилал, түлхүүр үг санал болгох (Gemini → rules fallback)."""
        title = str(request.data.get("title", "")).strip()
        body = str(request.data.get("body", "")).strip()
        if len(title) + len(body) < 20:
            raise ValidationError({"body": ["Санал болгохын тулд гарчиг, агуулгаа бөглөнө үү."]})
        cats = list(Category.objects.values_list("slug", "name"))
        result = ai.suggest_tags(title, body, cats)
        cat = Category.objects.filter(slug=result["category"]).first()
        result["category_id"] = cat.pk if cat else None
        pk = request.data.get("content_id")
        if pk:
            Content.objects.filter(pk=pk, author=request.user).update(ai_suggestion=result)
        return Response(result)


class PublicNewsViewSet(viewsets.ReadOnlyModelViewSet):
    """Нийтэд харагдах, зөвхөн шалгагдаж нийтлэгдсэн мэдээ (FR-017)."""
    permission_classes = [permissions.AllowAny]
    serializer_class = PublicContentSerializer

    def get_queryset(self):
        qs = Content.objects.filter(status=Status.PUBLISHED).select_related(
            "category", "province", "district", "author").prefetch_related("media")
        p = self.request.query_params
        if p.get("q"):
            qs = qs.filter(Q(title__icontains=p["q"]) | Q(body__icontains=p["q"])
                           | Q(tags__icontains=p["q"]))
        for key in ("province", "district", "category"):
            if p.get(key):
                qs = qs.filter(**{f"{key}_id": p[key]})
        if p.get("date_from"):
            qs = qs.filter(event_date__gte=p["date_from"])
        if p.get("date_to"):
            qs = qs.filter(event_date__lte=p["date_to"])
        return qs.order_by("-published_at")


class AdminContentViewSet(viewsets.ReadOnlyModelViewSet):
    """FR-062: Админ бүх контентыг хянаж, зөрчилтэйг түр нууна."""
    permission_classes = [roles("admin")]
    serializer_class = ContentSerializer

    def get_queryset(self):
        qs = Content.objects.select_related("category", "province", "district", "author") \
            .prefetch_related("media")
        p = self.request.query_params
        if p.get("status"):
            qs = qs.filter(status=p["status"])
        if p.get("q"):
            qs = qs.filter(title__icontains=p["q"])
        return qs

    @action(detail=True, methods=["post"])
    def hide(self, request, pk=None):
        c = services.set_visibility(self.get_object(), request.user, True, str(request.data.get("reason", "")))
        return Response(self.get_serializer(c).data)

    @action(detail=True, methods=["post"])
    def restore(self, request, pk=None):
        c = services.set_visibility(self.get_object(), request.user, False, str(request.data.get("reason", "")))
        return Response(self.get_serializer(c).data)
