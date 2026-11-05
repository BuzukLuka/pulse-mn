"""Мэдээний сэтгэгдэл: нийтэд унших, нэвтэрсэн хэрэглэгч бичих, иргэн нэрээ нууцлах, админ нуух."""
from datetime import timedelta

from django.utils import timezone
from rest_framework import permissions, serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from apps.audit import models as audit
from apps.common.exceptions import Unprocessable
from apps.common.permissions import roles
from .models import Comment, Content, Status

RATE_LIMIT = 5  # 10 минутад


class CommentSerializer(serializers.ModelSerializer):
    author_name = serializers.SerializerMethodField()
    mine = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ["id", "content", "text", "is_anonymous", "author_name", "mine", "created_at"]
        read_only_fields = ["author_name", "mine", "created_at"]

    def get_author_name(self, obj):
        if obj.is_anonymous:
            return "Нэргүй иргэн"
        u = obj.author
        return u.full_name or u.email.split("@")[0]

    def get_mine(self, obj):
        u = self.context["request"].user
        return bool(u.is_authenticated and u.pk == obj.author_id)

    def validate_text(self, v):
        if len(v.strip()) < 2:
            raise serializers.ValidationError("Сэтгэгдэл хоосон байна.")
        return v.strip()


class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    http_method_names = ["get", "post", "delete"]

    def get_permissions(self):
        return [permissions.AllowAny()] if self.action in ("list", "retrieve") else [permissions.IsAuthenticated()]

    def get_queryset(self):
        qs = Comment.objects.filter(is_hidden=False, content__status=Status.PUBLISHED).select_related("author")
        if self.action == "destroy" and self.request.user.is_authenticated and self.request.user.role == "admin":
            qs = Comment.objects.all()
        cid = self.request.query_params.get("content")
        return qs.filter(content_id=cid) if cid else qs

    def perform_create(self, s):
        u = self.request.user
        c = s.validated_data["content"]
        if c.status != Status.PUBLISHED:
            raise ValidationError({"content": ["Зөвхөн нийтлэгдсэн мэдээнд сэтгэгдэл бичнэ."]})
        if s.validated_data.get("is_anonymous") and u.role != "citizen":
            raise Unprocessable("Нэрээ нууцлах боломж зөвхөн иргэнд.")
        if Comment.objects.filter(author=u, created_at__gte=timezone.now() - timedelta(minutes=10)).count() >= RATE_LIMIT:
            raise Unprocessable("Хэт олон сэтгэгдэл. Түр хүлээгээд дахин оролдоно уу.")
        s.save(author=u)

    def destroy(self, request, *args, **kwargs):
        obj = self.get_object()
        if request.user.role == "admin" and obj.author_id != request.user.pk:
            obj.is_hidden = True  # админ устгахгүй, нууна (аудит)
            obj.save(update_fields=["is_hidden"])
            audit.log(request.user, "comment.hide", "comment", obj.pk, None, {"content": obj.content_id},
                      str(request.data.get("reason", "")) if hasattr(request, "data") else "")
            return Response(status=status.HTTP_204_NO_CONTENT)
        if obj.author_id != request.user.pk:
            return Response({"detail": "Зөвхөн өөрийн сэтгэгдлийг устгана."}, status=403)
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
