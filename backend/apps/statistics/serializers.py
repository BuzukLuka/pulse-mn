from rest_framework import serializers
from .models import DataSource, Indicator, IndicatorValue, IndicatorValueHistory


class DataSourceSerializer(serializers.ModelSerializer):
    indicator_count = serializers.IntegerField(source="indicators.count", read_only=True)

    class Meta:
        model = DataSource
        fields = ["id", "name", "kind", "url", "frequency", "last_synced_at", "status", "last_error", "indicator_count"]
        read_only_fields = ["last_synced_at", "status", "last_error"]


class IndicatorSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)
    source_name = serializers.CharField(source="source.name", read_only=True)
    frequency = serializers.CharField(source="source.get_frequency_display", read_only=True)

    class Meta:
        model = Indicator
        fields = ["id", "name", "aliases", "unit", "category", "category_name", "source", "source_name",
                  "frequency", "is_active"]


class HistorySerializer(serializers.ModelSerializer):
    changed_by_name = serializers.SerializerMethodField()

    class Meta:
        model = IndicatorValueHistory
        fields = ["id", "old_value", "new_value", "reason", "changed_by_name", "created_at"]

    def get_changed_by_name(self, o):
        return o.changed_by.email if o.changed_by else "систем"


class ValueSerializer(serializers.ModelSerializer):
    province_name = serializers.CharField(source="province.name", default="Улсын дүн", read_only=True)
    history = HistorySerializer(many=True, read_only=True)

    class Meta:
        model = IndicatorValue
        fields = ["id", "indicator", "province", "province_name", "district", "year", "value", "updated_at", "history"]
