from django.db.models import Q
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response

from apps.catalog.models import Category
from apps.common.permissions import roles
from . import services
from .models import Pledge, PledgeUpdate, Politician
from .serializers import PledgeDetailSerializer, PledgeSerializer, PledgeUpdateSerializer, PoliticianSerializer

WRITE = roles("editor", "admin")


class PoliticianViewSet(viewsets.ModelViewSet):
    serializer_class = PoliticianSerializer
    pagination_class = None

    def get_permissions(self):
        return [permissions.AllowAny()] if self.action in ("list", "retrieve", "compare", "constituencies") else [WRITE()]

    def get_queryset(self):
        qs = Politician.objects.select_related("province", "district")
        p = self.request.query_params
        if p.get("q"):
            qs = qs.filter(Q(name__icontains=p["q"]) | Q(position__icontains=p["q"]))
        if p.get("province"):
            qs = qs.filter(province_id=p["province"])
        if p.get("district"):
            qs = qs.filter(district_id=p["district"])
        if p.get("term_year"):
            qs = qs.filter(term_year=p["term_year"])
        if p.get("constituency"):
            qs = qs.filter(constituency_number=p["constituency"])
        if p.get("system"):
            qs = qs.filter(election_system=p["system"])
        if p.get("category"):
            qs = qs.filter(pledges__category_id=p["category"]).distinct()
        return qs.order_by("constituency_number", "name")

    @action(detail=False, methods=["get"])
    def constituencies(self, request):
        """Тойргууд (parliament.mn-ийн сонгуулийн үр дүнгээс)."""
        from django.db.models import Count
        rows = (Politician.objects.filter(constituency_number__isnull=False).values("constituency_number", "constituency_name")
                .annotate(members=Count("id")).order_by("constituency_number"))
        return Response(list(rows))

    def _card(self, pol):
        return {**PoliticianSerializer(pol).data, "stats": services.percentages(pol.pledges.all())}

    def list(self, request, *args, **kwargs):
        return Response([self._card(p) for p in self.get_queryset()])

    def retrieve(self, request, *args, **kwargs):
        pol = self.get_object()
        return Response({**self._card(pol), "pledges": PledgeSerializer(pol.pledges.all(), many=True).data})

    @action(detail=False, methods=["get"])
    def compare(self, request):
        """Ижил шалгуур, ижил аргачлалаар харьцуулах."""
        ids = [int(i) for i in request.query_params.get("ids", "").split(",") if i.isdigit()][:4]
        return Response([self._card(p) for p in Politician.objects.filter(pk__in=ids)])


class AdminPledgeUpdateViewSet(viewsets.ReadOnlyModelViewSet):
    """Иргэний явцын мэдээг шалгах дараалал."""
    permission_classes = [WRITE]
    serializer_class = PledgeUpdateSerializer

    def get_queryset(self):
        qs = PledgeUpdate.objects.select_related("pledge", "pledge__politician", "author")
        return qs.filter(status=self.request.query_params.get("status", "pending"))

    @action(detail=True, methods=["post"])
    def review(self, request, pk=None):
        progress = request.data.get("progress")
        upd = services.review_update(request.user, self.get_object(), bool(request.data.get("approve")),
                                     str(request.data.get("note", "")), int(progress) if str(progress or "").isdigit() else None)
        return Response(self.get_serializer(upd).data)


class PledgeViewSet(viewsets.ModelViewSet):
    pagination_class = None

    def get_permissions(self):
        if self.action == "updates":
            return [permissions.AllowAny()] if self.request.method == "GET" else [permissions.IsAuthenticated()]
        return [permissions.AllowAny()] if self.action in ("list", "retrieve", "summary") else [WRITE()]

    def get_serializer_class(self):
        return PledgeDetailSerializer if self.action == "retrieve" else PledgeSerializer

    def get_queryset(self):
        qs = Pledge.objects.select_related("politician", "category").prefetch_related("evidence", "history")
        p = self.request.query_params
        if p.get("politician"):
            qs = qs.filter(politician_id=p["politician"])
        if p.get("category"):
            qs = qs.filter(category_id=p["category"])
        if p.get("status"):
            qs = qs.filter(status=p["status"])
        if p.get("constituency"):
            qs = qs.filter(politician__constituency_number=p["constituency"])
        return qs

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=False, methods=["get"])
    def summary(self, request):
        qs = Pledge.objects.all()
        p = request.query_params
        if p.get("province"):
            qs = qs.filter(politician__province_id=p["province"])
        if p.get("term_year"):
            qs = qs.filter(politician__term_year=p["term_year"])
        by_cat = []
        for c in Category.objects.all():
            sub = qs.filter(category=c)
            if sub.exists():
                by_cat.append({"category": c.name, **services.percentages(sub)})
        return Response({"overall": services.percentages(qs), "by_category": by_cat})

    @action(detail=True, methods=["get", "post"], url_path="updates",
            parser_classes=[MultiPartParser, FormParser, JSONParser])
    def updates(self, request, pk=None):
        """GET: баталгаажсан явцын мэдээ (нийтэд). POST: нэвтэрсэн иргэн зураг, байршилтай мэдээ оруулна."""
        pledge = self.get_object()
        if request.method == "GET":
            qs = pledge.updates.filter(status="verified").select_related("author")
            return Response(PledgeUpdateSerializer(qs, many=True).data)
        d = request.data

        def num(k, cast=float):
            try:
                return cast(d.get(k)) if d.get(k) not in (None, "") else None
            except (TypeError, ValueError):
                return None
        upd = services.submit_update(pledge, request.user, str(d.get("text", "")), request.FILES.get("photo"),
                                     num("lat"), num("lng"), num("progress", int))
        return Response(PledgeUpdateSerializer(upd).data, status=201)

    @action(detail=True, methods=["post"], url_path="update-status")
    def update_status(self, request, pk=None):
        ev = request.data.get("evidence")
        if ev is not None and not isinstance(ev, dict):
            raise ValidationError({"evidence": ["Объект байх ёстой."]})
        pledge = self.get_object()
        services.update_status(pledge, request.user, str(request.data.get("status", "")),
                               str(request.data.get("reason", "")), ev)
        return Response(PledgeDetailSerializer(Pledge.objects.get(pk=pledge.pk)).data)
