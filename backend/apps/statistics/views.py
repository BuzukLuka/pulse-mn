from decimal import Decimal

from django.http import HttpResponse
from rest_framework import permissions, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.catalog.models import Province
from apps.common.permissions import roles
from . import services
from .models import DataSource, Indicator, IndicatorValue, IndicatorValueHistory
from .serializers import DataSourceSerializer, IndicatorSerializer, ValueSerializer

ADMIN = roles("admin")


def _val(v):
    return float(v) if v is not None else None


class PublicIndicators(APIView):
    """Мэдээллийн самбар: шүүлтүүрт тохирох сүүлийн утга, өөрчлөлт %, эх сурвалж, шинэчлэгдсэн огноо."""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        p = request.query_params
        qs = Indicator.objects.filter(is_active=True).select_related("category", "source")
        if p.get("category"):
            qs = qs.filter(category_id=p["category"])
        province = p.get("province") or None
        out = []
        for ind in qs:
            vals = ind.values.filter(district__isnull=True, province_id=province)
            if p.get("year"):
                vals = vals.filter(year__lte=p["year"])
            cur = vals.first()
            if not cur:
                continue
            prev = ind.values.filter(district__isnull=True, province_id=province, year__lt=cur.year).first()
            change = None
            if prev and prev.value:
                change = round(float((cur.value - prev.value) / prev.value * 100), 2)
            out.append({**IndicatorSerializer(ind).data, "value": _val(cur.value), "year": cur.year,
                        "change_pct": change, "updated_at": cur.updated_at})
        return Response(out)


class PublicSeries(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, pk):
        ind = Indicator.objects.select_related("source", "category").get(pk=pk, is_active=True)
        prov = request.query_params.get("province") or None
        vals = ind.values.filter(district__isnull=True, province_id=prov).order_by("year")
        return Response({"indicator": IndicatorSerializer(ind).data,
                         "series": [{"year": v.year, "value": _val(v.value)} for v in vals]})


class PublicCompare(APIView):
    """Аймгуудыг нэг үзүүлэлт, нэг жилээр харьцуулах (нэгж, хугацаа ижил)."""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        ind = Indicator.objects.select_related("source").get(pk=request.query_params.get("indicator"), is_active=True)
        year = request.query_params.get("year")
        ids = [int(i) for i in request.query_params.get("provinces", "").split(",") if i.isdigit()]
        qs = ind.values.filter(district__isnull=True, province__isnull=False)
        if ids:
            qs = qs.filter(province_id__in=ids)
        if year:
            qs = qs.filter(year=year)
        else:
            latest = qs.order_by("-year").values_list("year", flat=True).first()
            qs = qs.filter(year=latest) if latest else qs.none()
        return Response({"indicator": IndicatorSerializer(ind).data,
                         "rows": [{"province": v.province.name, "year": v.year, "value": _val(v.value)}
                                  for v in qs.select_related("province").order_by("-value")]})


class SourceViewSet(viewsets.ModelViewSet):
    permission_classes = [ADMIN]
    queryset = DataSource.objects.all().order_by("name")
    serializer_class = DataSourceSerializer
    pagination_class = None

    @action(detail=True, methods=["post"], url_path="import")
    def import_data(self, request, pk=None):
        src = self.get_object()
        f = request.FILES.get("file")
        if f:
            if f.size > services.MAX_CSV_BYTES:
                raise ValidationError({"file": ["Файл 5MB-аас хэтэрсэн."]})
            raw = f.read()
        elif src.url:
            try:
                raw = services.safe_fetch(src.url)
            except ValidationError:
                raise
            except Exception as e:  # холболт тасрахад өмнөх зөв утгыг устгахгүй
                src.status, src.last_error = "error", str(e)[:500]
                src.save(update_fields=["status", "last_error"])
                return Response({"imported": 0, "errors": [src.last_error]}, status=502)
        else:
            raise ValidationError({"file": ["CSV файл сонгох эсвэл холбоос тохируулна уу."]})
        return Response(services.import_csv(request.user, src, raw))


class IndicatorViewSet(viewsets.ModelViewSet):
    permission_classes = [ADMIN]
    queryset = Indicator.objects.select_related("category", "source")
    serializer_class = IndicatorSerializer
    pagination_class = None

    @action(detail=True, methods=["get", "post"])
    def values(self, request, pk=None):
        ind = self.get_object()
        if request.method == "POST":
            d = request.data
            prov = Province.objects.filter(pk=d.get("province")).first() if d.get("province") else None
            if not d.get("year") or d.get("value") in (None, ""):
                raise ValidationError({"value": ["Он, утга заавал."]})
            v = services.set_value(request.user, ind, prov, int(d["year"]), d["value"], str(d.get("reason", "")))
            return Response(ValueSerializer(v).data, status=201)
        qs = ind.values.select_related("province").prefetch_related("history__changed_by").order_by("-year", "province__name")
        return Response(ValueSerializer(qs, many=True).data)


@api_view(["POST"])
@permission_classes([ADMIN])
def restore_value(request, history_id):
    h = IndicatorValueHistory.objects.select_related("value_ref").get(pk=history_id)
    v = services.restore(request.user, h, str(request.data.get("reason", "")))
    return Response(ValueSerializer(v).data)


@api_view(["GET"])
@permission_classes([ADMIN])
def backup(request):
    """Нөөц хуулбар (JSON). Хэрэглэгчийн нууц үг, токен ороогүй. Сэргээх: `manage.py loaddata <файл>`."""
    from io import StringIO
    from django.core.management import call_command
    buf = StringIO()
    call_command("dumpdata", "catalog", "content", "pledges", "statistics", "complaints", "audit",
                 "notifications", indent=1, stdout=buf)
    resp = HttpResponse(buf.getvalue(), content_type="application/json")
    from django.utils import timezone
    resp["Content-Disposition"] = f'attachment; filename="pulse-backup-{timezone.localdate()}.json"'
    from apps.audit import models as audit
    audit.log(request.user, "system.backup", "system", "0", reason="Нөөц хуулбар татав")
    return resp
