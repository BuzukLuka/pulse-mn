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
    # parliament.mn-ээс импортолсон (УИХ-ын гишүүн): тойрог, сонгуулийн тогтолцоо, зураг
    parliament_id = models.PositiveIntegerField(null=True, blank=True, unique=True)
    photo_url = models.URLField(max_length=400, blank=True)
    profile_url = models.URLField(max_length=400, blank=True)
    constituency_number = models.PositiveSmallIntegerField(null=True, blank=True, db_index=True)
    constituency_name = models.CharField(max_length=120, blank=True)
    election_system = models.CharField(max_length=20, blank=True)  # MAJORITARIAN | PROPORTIONAL
    votes = models.PositiveIntegerField(null=True, blank=True)

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
    # Admin тохируулна: хэрэгжих хугацаа, явцын хувь, байршил (газрын зураг дээр)
    deadline = models.DateField(null=True, blank=True)
    progress = models.PositiveSmallIntegerField(default=0)
    lat = models.FloatField(null=True, blank=True)
    lng = models.FloatField(null=True, blank=True)
    location_name = models.CharField(max_length=200, blank=True)
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


class PledgeUpdate(models.Model):
    """Иргэний оруулсан явцын мэдээ (зураг, байршил). AI урьдчилан шалгаж, админ баталгаажуулна."""
    STATUSES = [("pending", "Шалгаж буй"), ("verified", "Баталгаажсан"), ("rejected", "Татгалзсан")]
    pledge = models.ForeignKey(Pledge, on_delete=models.CASCADE, related_name="updates")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="pledge_updates")
    text = models.TextField(max_length=1500)
    photo = models.FileField(upload_to="pledges/%Y/%m/", blank=True)
    photo_sha256 = models.CharField(max_length=64, blank=True, db_index=True)
    photo_phash = models.CharField(max_length=16, blank=True)
    lat = models.FloatField(null=True, blank=True)
    lng = models.FloatField(null=True, blank=True)
    progress_claim = models.PositiveSmallIntegerField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUSES, default="pending", db_index=True)
    ai_check = models.JSONField(default=dict, blank=True)
    review_note = models.CharField(max_length=500, blank=True)
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
