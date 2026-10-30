from django.conf import settings
from django.db import models


class DataSource(models.Model):
    KINDS = [("official", "Албан ёсны (импорт)"), ("manual", "Гараар оруулсан"), ("api_csv", "CSV холбоос")]
    FREQ = [("daily", "Өдөр бүр"), ("monthly", "Сар бүр"), ("quarterly", "Улирал бүр"), ("yearly", "Жил бүр")]
    name = models.CharField(max_length=200, unique=True)
    kind = models.CharField(max_length=10, choices=KINDS, default="manual")
    url = models.URLField(blank=True)
    frequency = models.CharField(max_length=10, choices=FREQ, default="yearly")
    last_synced_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=10, default="never")  # never | ok | error
    last_error = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Indicator(models.Model):
    name = models.CharField(max_length=200, unique=True)
    aliases = models.CharField(max_length=300, blank=True, help_text="Мэдээнээс таних өөр нэрс, таслалаар")
    unit = models.CharField(max_length=40)
    category = models.ForeignKey("catalog.Category", on_delete=models.PROTECT, related_name="+")
    source = models.ForeignKey(DataSource, on_delete=models.PROTECT, related_name="indicators")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["category_id", "name"]

    def __str__(self):
        return self.name


class IndicatorValue(models.Model):
    indicator = models.ForeignKey(Indicator, on_delete=models.CASCADE, related_name="values")
    province = models.ForeignKey("catalog.Province", null=True, blank=True, on_delete=models.CASCADE, related_name="+")
    district = models.ForeignKey("catalog.District", null=True, blank=True, on_delete=models.CASCADE, related_name="+")
    year = models.PositiveSmallIntegerField()
    value = models.DecimalField(max_digits=22, decimal_places=4)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-year"]
        constraints = [models.UniqueConstraint(fields=["indicator", "province", "district", "year"],
                                               name="uniq_indicator_value")]


class IndicatorValueHistory(models.Model):
    value_ref = models.ForeignKey(IndicatorValue, on_delete=models.CASCADE, related_name="history")
    old_value = models.DecimalField(max_digits=22, decimal_places=4, null=True)
    new_value = models.DecimalField(max_digits=22, decimal_places=4)
    reason = models.TextField()
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="+")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]
