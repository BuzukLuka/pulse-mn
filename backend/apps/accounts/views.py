from django.db.models import Count, Q
from rest_framework import generics, permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from apps.common.permissions import roles
from apps.content.models import Content
from .models import Experience, PortfolioItem, Role, User
from .serializers import (AdminUserSerializer, ExperienceSerializer, LoginSerializer, PortfolioSerializer,
                          RegisterSerializer, UserSerializer)
from .services import delete_account, export_personal_data, set_verified, update_access


class RegisterView(generics.CreateAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        user = ser.save()
        refresh = RefreshToken.for_user(user)
        refresh["role"] = user.role
        return Response({"user": UserSerializer(user).data, "refresh": str(refresh),
                         "access": str(refresh.access_token)}, status=status.HTTP_201_CREATED)


class LoginView(TokenObtainPairView):
    serializer_class = LoginSerializer
    permission_classes = [permissions.AllowAny]


class MeView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user


class MeExportView(APIView):
    """Өөрийн мэдээллийг JSON-оор татах (мэдээлэл авах эрх)."""
    def get(self, request):
        return Response(export_personal_data(request.user))


class MeDeleteView(APIView):
    """Бүртгэлээ устгах (мэдээллээ устгуулах эрх) — нууц үгээр баталгаажуулна."""
    def post(self, request):
        delete_account(request.user, str(request.data.get("password", "")), str(request.data.get("reason", "")))
        return Response(status=status.HTTP_204_NO_CONTENT)


class ReplaceListView(APIView):
    """PUT: өөрийн туршлага / портфолиог бүхэлд нь солих."""
    model = None
    serializer = None
    limit = 30

    def put(self, request):
        data = request.data if isinstance(request.data, list) else request.data.get("items", [])
        if len(data) > self.limit:
            return Response({"detail": f"Хамгийн ихдээ {self.limit} мөр."}, status=400)
        ser = self.serializer(data=data, many=True)
        ser.is_valid(raise_exception=True)
        self.model.objects.filter(user=request.user).delete()
        self.model.objects.bulk_create([self.model(user=request.user, **d) for d in ser.validated_data])
        return Response(UserSerializer(request.user).data)


class ExperienceView(ReplaceListView):
    model, serializer = Experience, ExperienceSerializer


class PortfolioView(ReplaceListView):
    model, serializer = PortfolioItem, PortfolioSerializer


class JournalistListView(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    pagination_class = None

    def list(self, request, *args, **kwargs):
        from apps.newsroom.services import rating_summary
        qs = User.objects.filter(role=Role.JOURNALIST, is_active=True).select_related("province")             .order_by("-is_verified", "full_name")[:100]
        return Response([{"id": u.id, "full_name": u.full_name or u.email.split("@")[0],
                          "is_verified": u.is_verified, "province": u.province.name if u.province else None,
                          "rating": rating_summary(u)}
                         for u in qs])


class JournalistPublicView(APIView):
    """Нийтийн профайл: зөвхөн хэрэглэгчийн зөвшөөрсөн талбарууд (NFR-013)."""
    permission_classes = [permissions.AllowAny]

    def get(self, request, pk):
        u = generics.get_object_or_404(User, pk=pk, role=Role.JOURNALIST, is_active=True)
        works = Content.objects.filter(author=u, status="published").select_related("province").order_by("-published_at")[:20]
        return Response({
            "id": u.id, "full_name": u.full_name or u.email.split("@")[0], "bio": u.bio,
            "is_verified": u.is_verified, "province": u.province.name if u.province else None,
            "organization": u.organization if u.show_org else None,
            "email": u.email if u.show_email else None, "phone": u.phone if u.show_phone else None,
            "experiences": ExperienceSerializer(u.experiences.all(), many=True).data if u.show_org else [],
            "portfolio": PortfolioSerializer(u.portfolio.all(), many=True).data,
            "works": [{"id": c.id, "title": c.title, "published_at": c.published_at,
                       "province_name": c.province.name if c.province else None} for c in works],
            "newsrooms": [{"id": m.newsroom_id, "name": m.newsroom.full_name or m.newsroom.organization}
                          for m in u.memberships.filter(status="active").select_related("newsroom")],
        })


class AdminUserViewSet(viewsets.ReadOnlyModelViewSet):
    """UC-03: хэрэглэгчийн жагсаалт, эрх өөрчлөх / түр хаах."""
    permission_classes = [roles("admin")]
    serializer_class = AdminUserSerializer

    def get_queryset(self):
        qs = User.objects.order_by("-created_at")
        p = self.request.query_params
        if p.get("q"):
            qs = qs.filter(Q(email__icontains=p["q"]) | Q(full_name__icontains=p["q"]))
        if p.get("role"):
            qs = qs.filter(role=p["role"])
        if p.get("is_active") in ("true", "false"):
            qs = qs.filter(is_active=p["is_active"] == "true")
        if p.get("verification") == "requested":
            qs = qs.filter(verification_requested_at__isnull=False, is_verified=False)
        return qs

    def partial_update(self, request, *args, **kwargs):
        target = self.get_object()
        role = request.data.get("role")
        if role is not None and role not in Role.values:
            return Response({"role": ["Буруу үүрэг."]}, status=400)
        is_active = request.data.get("is_active")
        update_access(request.user, target, role=role, is_active=is_active,
                      reason=str(request.data.get("reason", "")))
        return Response(self.get_serializer(target).data)


class AdminVerifyView(APIView):
    permission_classes = [roles("admin")]

    def post(self, request, pk):
        target = generics.get_object_or_404(User, pk=pk)
        set_verified(request.user, target, bool(request.data.get("verified", True)),
                     str(request.data.get("reason", "")))
        return Response(AdminUserSerializer(target).data)


class AdminStatsView(APIView):
    permission_classes = [roles("admin")]

    def get(self, request):
        by_status = dict(Content.objects.values_list("status").annotate(n=Count("id")))
        by_role = dict(User.objects.values_list("role").annotate(n=Count("id")))
        return Response({"content_by_status": by_status, "users_by_role": by_role,
                         "users_total": User.objects.count(),
                         "content_total": Content.objects.count()})
