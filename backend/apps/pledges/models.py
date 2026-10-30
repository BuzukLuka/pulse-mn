from django.conf import settings
from django.db import models


class PledgeStatus(models.TextChoices):
    FULFILLED = "fulfilled", "Биелсэн"
    IN_PROGRESS = "in_progress", "Хэрэгжиж байгаа"
    NOT_FULFILLED = "not_fulfilled", "Биелээгүй"
    INSUFFICIENT = "insufficient", "Мэдээлэл дутуу"


class Politician(models.Model):
    name = models.CharField(max_length=160)
    position = models.CharField(max_length=160)
    party = models.CharField(max_length=120, blank=True)
    province = models.ForeignKey("catalog.Province", null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    district = models.ForeignKey("catalog.District", null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    term_year = models.PositiveSmallIntegerField(help_text="Сонгуулийн он")

    class Meta:
        ordering = ["name"]
        constraints = [models.UniqueConstraint(fields=["name", "position", "term_year"], name="uniq_politician_term")]

    def __str__(self):
        return f"{self.name} ({self.position}, {self.term_year})"


class Pledge(models.Model):
    politician = models.ForeignKey(Politician, on_delete=models.CASCADE, related_name="pledges")
    text = models.TextField()
    category = models.ForeignKey("catalog.Category", on_delete=models.PROTECT, related_name="+")
    source = models.CharField(max_length=300)
    source_url = models.URLField(blank=True)
    status = models.CharField(max_length=14, choices=PledgeStatus.choices, default=PledgeStatus.INSUFFICIENT, db_index=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="+")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["id"]


class PledgeEvidence(models.Model):
    KINDS = [("document", "Албан бичиг"), ("news", "Мэдээ"), ("statistics", "Статистик"),
             ("photo", "Зураг"), ("video", "Видео"), ("other", "Бусад")]
    pledge = models.ForeignKey(Pledge, on_delete=models.CASCADE, related_name="evidence")
    kind = models.CharField(max_length=12, choices=KINDS, default="document")
    source = models.CharField(max_length=300)
    date = models.DateField()
    url = models.URLField(blank=True)
    note = models.TextField(blank=True)
    added_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="+")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "-id"]


class PledgeStatusHistory(models.Model):
    pledge = models.ForeignKey(Pledge, on_delete=models.CASCADE, related_name="history")
    old_status = models.CharField(max_length=14, choices=PledgeStatus.choices)
    new_status = models.CharField(max_length=14, choices=PledgeStatus.choices)
    reason = models.TextField()
    evidence = models.ForeignKey(PledgeEvidence, null=True, on_delete=models.SET_NULL, related_name="+")
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="+")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]
