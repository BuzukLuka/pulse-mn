import hmac
import os

from django.db.models import Count, Q
from rest_framework import permissions, serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from . import services
from .models import ExternalArticle, FetchRun
from .sources import SOURCES, enabled_sources


class ArticleSerializer(serializers.ModelSerializer):
    source_name = serializers.SerializerMethodField()
    category_name = serializers.CharField(source="category.name", default=None)

    class Meta:
        model = ExternalArticle
        fields = ["id", "source", "source_name", "url", "title", "title_mn", "snippet", "summary_mn", "language",
                  "published_at", "category", "category_name", "relevance", "ai_source"]

    def get_source_name(self, obj):
        return SOURCES.get(obj.source, {}).get("name", obj.source)


class WorldNewsView(ListAPIView):
    """Дэлхийн мэдээн дэх Монголын тухай мэдээ. Хуучирсан бол (3 цаг) хүсэлтийн үеэр шинэчилнэ."""
    permission_classes = [permissions.AllowAny]
    serializer_class = ArticleSerializer

    def get_queryset(self):
        try:
            services.refresh()
        except Exception:  # noqa: BLE001 — эх сурвалж унасан ч хадгалсан мэдээг харуулна
            pass
        qs = ExternalArticle.objects.select_related("category")
        p = self.request.query_params
        if p.get("source"):
            qs = qs.filter(source=p["source"])
        if p.get("category"):
            qs = qs.filter(category_id=p["category"])
        if p.get("q"):
            qs = qs.filter(Q(title__icontains=p["q"]) | Q(title_mn__icontains=p["q"]) | Q(summary_mn__icontains=p["q"]))
        return qs


class WorldNewsSourcesView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        counts = dict(ExternalArticle.objects.values_list("source").annotate(n=Count("id")))
        run = FetchRun.objects.first()
        on = enabled_sources()
        return Response({
            "sources": [{"key": k, "name": s["name"], "home": s["home"], "enabled": k in on, "count": counts.get(k, 0)}
                        for k, s in SOURCES.items()],
            "last_run": {"at": run.started_at, "added": run.added, "report": run.report} if run else None,
        })


class OptionalJWT(JWTAuthentication):
    """Vercel Cron-ын «Bearer CRON_SECRET» толгойг JWT биш гэж 401 буцаахгүйн тулд алдаатай токеныг үл тооно."""
    def authenticate(self, request):
        try:
            return super().authenticate(request)
        except (InvalidToken, AuthenticationFailed):
            return None


class WorldNewsRefreshView(APIView):
    """Vercel Cron (Authorization: Bearer CRON_SECRET) эсвэл админ гараар шинэчилнэ."""
    permission_classes = [permissions.AllowAny]
    authentication_classes = [OptionalJWT]

    def _allowed(self, request):
        secret = os.getenv("CRON_SECRET", "")
        header = request.headers.get("Authorization", "")
        if secret and hmac.compare_digest(header, f"Bearer {secret}"):
            return True
        u = request.user
        return bool(u and u.is_authenticated and u.role == "admin")

    def get(self, request):
        if not self._allowed(request):
            return Response({"detail": "Эрхгүй."}, status=403)
        run = services.refresh(force=True)
        return Response({"added": run.added, "report": run.report})

    post = get
