from rest_framework import serializers
from .models import Content, ContentVersion, Media


class MediaSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()

    class Meta:
        model = Media
        fields = ["id", "kind", "original_name", "size", "sha256", "phash", "url", "created_at"]

    def get_url(self, obj):
        request = self.context.get("request")
        return request.build_absolute_uri(obj.file.url) if request else obj.file.url


class ContentSerializer(serializers.ModelSerializer):
    media = MediaSerializer(many=True, read_only=True)
    author_name = serializers.SerializerMethodField()
    category_name = serializers.CharField(source="category.name", default=None, read_only=True)
    category_slug = serializers.CharField(source="category.slug", default=None, read_only=True)
    province_name = serializers.CharField(source="province.name", default=None, read_only=True)
    district_name = serializers.CharField(source="district.name", default=None, read_only=True)
    pledge_items = serializers.SerializerMethodField()
    status_label = serializers.CharField(source="get_status_display", read_only=True)
    newsroom_name = serializers.SerializerMethodField()

    class Meta:
        model = Content
        fields = [
            "id", "title", "body", "category", "category_name", "category_slug",
            "province", "province_name", "district", "district_name", "event_date", "source",
            "tags", "ai_summary", "ai_suggestion", "ai_review", "status", "status_label",
            "review_reason", "reviewed_at", "submitted_at", "published_at", "created_at",
            "updated_at", "author", "author_name", "media", "content_type", "event_time",
            "location_detail", "license", "copyright_declared", "verification", "review_checklist",
            "pledges", "pledge_items", "newsroom", "newsroom_name", "price",
        ]
        read_only_fields = ["status", "review_reason", "reviewed_at", "submitted_at", "published_at",
                            "ai_summary", "ai_suggestion", "ai_review", "author", "verification",
                            "review_checklist"]

    def get_pledge_items(self, obj):
        return [{"id": p.pk, "text": p.text[:140], "politician": p.politician.name, "politician_id": p.politician_id}
                for p in obj.pledges.select_related("politician")]

    def get_newsroom_name(self, obj):
        n = obj.newsroom
        return (n.full_name or n.organization or n.email.split("@")[0]) if n else None

    def validate_newsroom(self, value):
        """Зөвхөн идэвхтэй гишүүнчлэлтэй редакцаараа дамжуулж оруулна."""
        if value is None:
            return value
        from apps.newsroom.services import active_newsroom_ids
        request = self.context.get("request")
        if not request or value.pk not in active_newsroom_ids(request.user):
            raise serializers.ValidationError("Та энэ редакцын идэвхтэй сэтгүүлч биш байна.")
        return value

    def get_author_name(self, obj):
        return obj.author.full_name or obj.author.email.split("@")[0]

    def validate_title(self, value):
        if not value.strip():
            raise serializers.ValidationError("Гарчиг заавал.")
        return value

    def validate_tags(self, value):
        if not isinstance(value, list) or any(not isinstance(t, str) for t in value):
            raise serializers.ValidationError("Шошго нь текстийн жагсаалт байх ёстой.")
        return [t.strip()[:40] for t in value if t.strip()][:12]

    def validate(self, attrs):
        district, province = attrs.get("district"), attrs.get("province")
        if district and province and district.province_id != province.id:
            raise serializers.ValidationError({"district": "Сум сонгосон аймагт харьяалагдахгүй байна."})
        return attrs


class PublicContentSerializer(ContentSerializer):
    """Нийтэд харагдах хувилбар: баталгаажуулалтын дотоод талбаргүй."""
    class Meta(ContentSerializer.Meta):
        fields = [f for f in ContentSerializer.Meta.fields
                  if f not in ("ai_suggestion", "ai_review", "review_reason", "author", "submitted_at",
                               "verification", "review_checklist", "copyright_declared", "embedding")]
        fields += ["trust"]

    trust = serializers.SerializerMethodField()

    def get_trust(self, obj):
        """Нийтэд харагдах «Pulse Trust» карт — дотоод алдааны мэдээлэлгүй."""
        v = obj.verification or {}
        return {"editor_verified": bool(v.get("editor_verified")), "score": v.get("score"),
                "level": v.get("level"), "ai_used": v.get("ai_used", False),
                "checks": [{"label": c["label"], "status": c["status"]} for c in v.get("checks", [])
                           if c["key"] in ("source", "media", "duplicate", "claims")],
                "claims": next(([{k: i[k] for k in ("indicator", "unit", "claimed", "official", "year", "source", "mismatch")}
                                 for i in c.get("items", [])] for c in v.get("checks", []) if c["key"] == "claims"), []),
                "verified_at": v.get("verified_at")}


class VersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContentVersion
        fields = ["id", "number", "title", "body", "source", "tags", "created_at"]
