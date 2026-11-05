from rest_framework import serializers
from .models import Pledge, PledgeEvidence, PledgeStatusHistory, PledgeUpdate, Politician


class EvidenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = PledgeEvidence
        fields = ["id", "kind", "source", "date", "url", "note", "created_at"]


class HistorySerializer(serializers.ModelSerializer):
    evidence = EvidenceSerializer(read_only=True)
    changed_by_name = serializers.SerializerMethodField()

    class Meta:
        model = PledgeStatusHistory
        fields = ["id", "old_status", "new_status", "reason", "evidence", "changed_by_name", "created_at"]

    def get_changed_by_name(self, o):
        return (o.changed_by.full_name or o.changed_by.email.split("@")[0]) if o.changed_by else "систем"


class PledgeSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)
    status_label = serializers.CharField(source="get_status_display", read_only=True)
    politician_name = serializers.CharField(source="politician.name", read_only=True)
    evidence_count = serializers.IntegerField(source="evidence.count", read_only=True)
    updates_count = serializers.SerializerMethodField()

    def get_updates_count(self, o):
        return o.updates.filter(status="verified").count()

    def validate_progress(self, v):
        if not 0 <= v <= 100:
            raise serializers.ValidationError("0–100.")
        return v

    class Meta:
        model = Pledge
        fields = ["id", "politician", "politician_name", "text", "category", "category_name", "source",
                  "source_url", "status", "status_label", "evidence_count", "created_at", "updated_at",
                  "deadline", "progress", "lat", "lng", "location_name", "updates_count"]
        read_only_fields = ["status"]


class PledgeDetailSerializer(PledgeSerializer):
    evidence = EvidenceSerializer(many=True, read_only=True)
    history = HistorySerializer(many=True, read_only=True)

    class Meta(PledgeSerializer.Meta):
        fields = PledgeSerializer.Meta.fields + ["evidence", "history"]


class PoliticianSerializer(serializers.ModelSerializer):
    province_name = serializers.CharField(source="province.name", default=None, read_only=True)
    district_name = serializers.CharField(source="district.name", default=None, read_only=True)

    class Meta:
        model = Politician
        fields = ["id", "name", "position", "party", "province", "province_name", "district",
                  "district_name", "term_year", "parliament_id", "photo_url", "profile_url", "constituency_number",
                  "constituency_name", "election_system", "votes"]
        read_only_fields = ["parliament_id"]
        validators = []

    def validate(self, a):
        qs = Politician.objects.filter(name__iexact=a["name"].strip(), position__iexact=a["position"].strip(),
                                       term_year=a["term_year"])
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError({"name": "Ийм улс төрч (нэр, албан тушаал, он) аль хэдийн бүртгэлтэй."})
        return a


class PledgeUpdateSerializer(serializers.ModelSerializer):
    photo_url = serializers.SerializerMethodField()
    author_name = serializers.SerializerMethodField()
    pledge_text = serializers.CharField(source="pledge.text", read_only=True)
    politician_name = serializers.CharField(source="pledge.politician.name", read_only=True)

    class Meta:
        model = PledgeUpdate
        fields = ["id", "pledge", "pledge_text", "politician_name", "text", "photo_url", "lat", "lng", "progress_claim",
                  "status", "ai_check", "review_note", "author_name", "created_at"]

    def get_photo_url(self, o):
        return o.photo.url if o.photo else ""

    def get_author_name(self, o):
        return o.author.full_name or "Иргэн"
