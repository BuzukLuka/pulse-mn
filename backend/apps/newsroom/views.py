from django.db.models import Count
from rest_framework import generics, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import Role, User
from apps.common.permissions import roles
from apps.content.models import Content, Status
from apps.content.serializers import ContentSerializer
from . import services
from .models import Membership, Purchase, Rating


def membership_json(m):
    return {"id": m.id, "status": m.status, "status_label": m.get_status_display(), "message": m.message,
            "created_at": m.created_at, "decided_at": m.decided_at,
            "newsroom": {"id": m.newsroom_id, "name": services.display_name(m.newsroom)},
            "journalist": services.journalist_card(m.journalist)}


def purchase_json(p):
    return {"id": p.id, "status": p.status, "status_label": p.get_status_display(), "amount": p.amount,
            "invoice_code": p.invoice_code, "created_at": p.created_at, "paid_at": p.paid_at,
            "license_type": p.license_type, "license_label": p.get_license_type_display(),
            "vat_amount": p.vat_amount, "platform_fee": p.platform_fee, "author_net": p.author_net,
            "provider": p.provider, "provider_ref": p.provider_ref, "ebarimt_no": p.ebarimt_no,
            "refund_reason": p.refund_reason, "demo": p.provider == "demo",
            "content": {"id": p.content_id, "title": p.content.title, "author_name": services.display_name(p.content.author)},
            "buyer": {"id": p.buyer_id, "name": services.display_name(p.buyer)}}


# ---------- Нийтийн: редакцуудын жагсаалт, профайл ----------
class NewsroomListView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        qs = User.objects.filter(role=Role.NEWSROOM, is_active=True).select_related("province").order_by("-is_verified", "full_name")[:100]
        return Response([services.newsroom_card(u) for u in qs])


class NewsroomPublicView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, pk):
        u = generics.get_object_or_404(User, pk=pk, role=Role.NEWSROOM, is_active=True)
        members = Membership.objects.filter(newsroom=u, status="active").select_related("journalist", "journalist__province")
        works = Content.objects.filter(newsroom=u, status=Status.PUBLISHED).select_related("province").order_by("-published_at")[:20]
        return Response({**services.newsroom_card(u),
                         "journalists": [services.journalist_card(m.journalist) for m in members],
                         "works": [{"id": c.id, "title": c.title, "published_at": c.published_at,
                                    "author_name": services.display_name(c.author),
                                    "province_name": c.province.name if c.province_id else None} for c in works]})


# ---------- Сэтгүүлч: гишүүнчлэл, баталгаажуулалт ----------
class MyMembershipsView(APIView):
    permission_classes = [roles("journalist")]

    def get(self, request):
        qs = Membership.objects.filter(journalist=request.user).select_related("newsroom", "journalist")
        return Response([membership_json(m) for m in qs])

    def post(self, request):
        m = services.request_membership(request.user, request.data.get("newsroom"), str(request.data.get("message", "")))
        return Response(membership_json(m), status=201)


class MembershipEndView(APIView):
    permission_classes = [roles("journalist", "newsroom")]

    def post(self, request, pk):
        m = generics.get_object_or_404(Membership, pk=pk)
        return Response(membership_json(services.end_membership(request.user, m)))


class RequestVerificationView(APIView):
    permission_classes = [roles("journalist", "newsroom")]

    def post(self, request):
        u = services.request_verification(request.user)
        return Response({"verification_requested_at": u.verification_requested_at})


# ---------- Редакцын самбар ----------
class NewsroomDashboardViewSet(viewsets.ViewSet):
    permission_classes = [roles("newsroom")]

    @action(detail=False, methods=["get"])
    def summary(self, request):
        rows = dict(Content.objects.filter(newsroom=request.user).exclude(status=Status.DRAFT)
                    .values_list("status").annotate(n=Count("id")))
        return Response({"content": rows, "content_total": sum(rows.values()),
                         "members": Membership.objects.filter(newsroom=request.user, status="active").count(),
                         "pending": Membership.objects.filter(newsroom=request.user, status="pending").count(),
                         "purchases": Purchase.objects.filter(buyer=request.user, status="paid").count(),
                         "rating": services.rating_summary(request.user)})

    @action(detail=False, methods=["get"])
    def members(self, request):
        return Response([membership_json(m) for m in services.visible_members(request.user).select_related("newsroom")])

    @action(detail=False, methods=["post"], url_path=r"members/(?P<mid>\d+)/decide")
    def decide(self, request, mid=None):
        m = generics.get_object_or_404(Membership, pk=mid, newsroom=request.user)
        return Response(membership_json(services.decide_membership(request.user, m, bool(request.data.get("approve")))))

    @action(detail=False, methods=["get"])
    def content(self, request):
        """Харьяа сэтгүүлчдийн редакцаар дамжуулж илгээсэн мэдээ (ноорог харагдахгүй)."""
        qs = Content.objects.filter(newsroom=request.user).exclude(status=Status.DRAFT).select_related(
            "category", "province", "district", "author").prefetch_related("media").order_by("-submitted_at")
        if request.query_params.get("status"):
            qs = qs.filter(status=request.query_params["status"])
        return Response(ContentSerializer(qs[:100], many=True, context={"request": request}).data)


# ---------- ДЕМО төлбөр ----------
class PurchaseViewSet(viewsets.ViewSet):
    def get_permissions(self):
        return [roles("newsroom")()] if self.action != "list" else [roles("newsroom", "journalist")()]

    def list(self, request):
        """Редакц: өөрийн худалдан авалт. Сэтгүүлч: өөрийн мэдээний борлуулалт."""
        qs = Purchase.objects.select_related("content", "content__author", "buyer")
        qs = qs.filter(content__author=request.user) if request.user.role == Role.JOURNALIST else qs.filter(buyer=request.user)
        if request.query_params.get("content"):
            qs = qs.filter(content_id=request.query_params["content"])
        return Response([purchase_json(p) for p in qs[:100]])

    def create(self, request):
        c = generics.get_object_or_404(Content, pk=request.data.get("content"))
        p = services.create_purchase(request.user, c, str(request.data.get("license_type", "standard")),
                                     bool(request.data.get("accept_terms")))
        return Response(purchase_json(p), status=201)

    @action(detail=False, methods=["get"])
    def quote(self, request):
        """Худалдан авахаас өмнө үнийн задаргаа (НӨАТ, шимтгэл, сэтгүүлчид очих дүн)."""
        from .payments import LICENSES, PLATFORM_FEE_PCT, breakdown, get_provider
        c = generics.get_object_or_404(Content, pk=request.query_params.get("content"), status=Status.PUBLISHED)
        exclusive_sold = Purchase.objects.filter(content=c, license_type="exclusive", status="paid").exists()
        any_sold = Purchase.objects.filter(content=c, status="paid").exists()
        return Response({"provider": get_provider().name, "live": get_provider().live, "fee_pct": PLATFORM_FEE_PCT,
                         "options": [{"license_type": k, "label": label, **breakdown(c.price * mult),
                                      "available": not exclusive_sold and (k != "exclusive" or not any_sold)}
                                     for k, (label, mult) in LICENSES.items()]})

    @action(detail=True, methods=["post"])
    def confirm(self, request, pk=None):
        p = generics.get_object_or_404(Purchase, pk=pk)
        return Response(purchase_json(services.confirm_purchase(request.user, p)))

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        p = generics.get_object_or_404(Purchase, pk=pk)
        return Response(purchase_json(services.cancel_purchase(request.user, p)))


class AdminPurchaseViewSet(viewsets.ViewSet):
    """Админ: бүх төлбөрийн хяналт, буцаалт."""
    permission_classes = [roles("admin")]

    def list(self, request):
        from django.db.models import Sum
        qs = Purchase.objects.select_related("content", "content__author", "buyer")
        if request.query_params.get("status"):
            qs = qs.filter(status=request.query_params["status"])
        paid = Purchase.objects.filter(status="paid").aggregate(
            gross=Sum("amount"), vat=Sum("vat_amount"), fee=Sum("platform_fee"), net=Sum("author_net"))
        return Response({"totals": {k: v or 0 for k, v in paid.items()}, "items": [purchase_json(p) for p in qs[:200]]})

    @action(detail=True, methods=["post"])
    def refund(self, request, pk=None):
        p = generics.get_object_or_404(Purchase, pk=pk)
        return Response(purchase_json(services.refund_purchase(request.user, p, str(request.data.get("reason", "")))))


# ---------- Үнэлгээ ----------
class RatingView(APIView):
    def get_permissions(self):
        return [permissions.AllowAny()] if self.request.method == "GET" else [permissions.IsAuthenticated()]

    def get(self, request):
        target = generics.get_object_or_404(User, pk=request.query_params.get("target"))
        items = Rating.objects.filter(target=target).select_related("rater")[:30]
        mine = Rating.objects.filter(target=target, rater=request.user).first() if request.user.is_authenticated else None
        return Response({"summary": services.rating_summary(target),
                         "items": [{"id": r.id, "score": r.score, "comment": r.comment, "updated_at": r.updated_at,
                                    "rater": services.display_name(r.rater), "rater_role": r.rater.role} for r in items],
                         "mine": {"score": mine.score, "comment": mine.comment} if mine else None})

    def post(self, request):
        target = generics.get_object_or_404(User, pk=request.data.get("target"))
        content = Content.objects.filter(pk=request.data.get("content")).first() if request.data.get("content") else None
        try:
            score = int(request.data.get("score"))
        except (TypeError, ValueError):
            score = 0
        services.rate(request.user, target, score, str(request.data.get("comment", "")), content)
        return Response({"summary": services.rating_summary(target)}, status=201)


class RatingSuggestView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        target = generics.get_object_or_404(User, pk=request.query_params.get("target"),
                                            role__in=[Role.JOURNALIST, Role.NEWSROOM])
        return Response(services.suggest_rating(target))
