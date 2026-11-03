from django.conf import settings
from django.db import models


class Status(models.TextChoices):
    DRAFT = "draft", "Ноорог"
    UNDER_REVIEW = "under_review", "Хянагдаж буй"
    CHANGES_REQUESTED = "changes_requested", "Засвар шаардлагатай"
    PUBLISHED = "published", "Нийтлэгдсэн"
    REJECTED = "rejected", "Татгалзсан"
    HIDDEN = "hidden", "Түр нуусан"


# State machine (UC-01/02): аль төлвөөс аль төлөв рүү шилжих боломжтой вэ
TRANSITIONS = {
    Status.DRAFT: {Status.UNDER_REVIEW},
    Status.CHANGES_REQUESTED: {Status.UNDER_REVIEW},
    Status.UNDER_REVIEW: {Status.PUBLISHED, Status.CHANGES_REQUESTED, Status.REJECTED},
    Status.PUBLISHED: {Status.HIDDEN},
    Status.HIDDEN: {Status.PUBLISHED},
    Status.REJECTED: set(),
}


class ContentType(models.TextChoices):
    NEWS = "news", "Мэдээ"
    ARTICLE = "article", "Нийтлэл"
    PHOTO = "photo", "Зураг"
    VIDEO = "video", "Видео"
    DOCUMENT = "document", "Баримт бичиг"


class License(models.TextChoices):
    ATTRIBUTION = "attribution", "Эх сурвалж дурдан чөлөөтэй ашиглах"
    PLATFORM_ONLY = "platform_only", "Зөвхөн Pulse.mn дээр нийтлэх"
    PERMISSION = "permission", "Зөвшөөрөлтэйгээр ашиглах"


class Content(models.Model):
    content_type = models.CharField(max_length=10, choices=ContentType.choices, default=ContentType.NEWS)
    event_time = models.TimeField(null=True, blank=True)
    location_detail = models.CharField(max_length=200, blank=True)  # баг / байршил
    license = models.CharField(max_length=14, choices=License.choices, default=License.ATTRIBUTION)
    copyright_declared = models.BooleanField(default=False)
    verification = models.JSONField(null=True, blank=True)       # Pulse Trust шалгалтын үр дүн
    embedding = models.JSONField(null=True, blank=True)
    review_checklist = models.JSONField(null=True, blank=True)
    pledges = models.ManyToManyField("pledges.Pledge", blank=True, related_name="news")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="contents")
    # Сэтгүүлч харьяалагддаг редакцаараа дамжуулж оруулбал редакц мэдэгдэл авч, самбартаа хянана
    newsroom = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
                                 related_name="newsroom_contents")
    price = models.PositiveIntegerField(default=0, help_text="Редакцад худалдах үнэ (₮). 0 бол зарахгүй.")
    # Сэтгүүлчийн хууль ёсны мэдэгдэл (илгээхэд заавал): баримт, гүтгэлэггүй, хувийн мэдээлэл, хүүхэд,
    # ашиг сонирхлын зөрчил, ивээн тэтгэсэн / улс төрийн сурталчилгаа. Шалгалт: services.compliance_problems
    compliance = models.JSONField(default=dict, blank=True)
    title = models.CharField(max_length=250)
    body = models.TextField(blank=True)
    category = models.ForeignKey("catalog.Category", null=True, blank=True, on_delete=models.PROTECT)
    province = models.ForeignKey("catalog.Province", null=True, blank=True, on_delete=models.PROTECT)
    district = models.ForeignKey("catalog.District", null=True, blank=True, on_delete=models.PROTECT)
    event_date = models.DateField(null=True, blank=True)
    source = models.CharField(max_length=300, blank=True)
    tags = models.JSONField(default=list, blank=True)
    ai_summary = models.TextField(blank=True)
    ai_suggestion = models.JSONField(null=True, blank=True)
    ai_review = models.JSONField(null=True, blank=True)

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT, db_index=True)
    review_reason = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                                    on_delete=models.SET_NULL, related_name="reviewed_contents")
    reviewed_at = models.DateTimeField(null=True, blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["status", "published_at"])]

    def __str__(self):
        return self.title

    def can_transition(self, new_status):
        return Status(new_status) in TRANSITIONS[Status(self.status)]


class Media(models.Model):
    class Kind(models.TextChoices):
        IMAGE = "image", "Зураг"
        VIDEO = "video", "Видео"
        DOCUMENT = "document", "Баримт"

    content = models.ForeignKey(Content, on_delete=models.CASCADE, related_name="media")
    file = models.FileField(upload_to="media/%Y/%m/")
    kind = models.CharField(max_length=10, choices=Kind.choices)
    original_name = models.CharField(max_length=255)
    size = models.PositiveBigIntegerField(default=0)
    sha256 = models.CharField(max_length=64, db_index=True)  # яг ижил файл
    phash = models.CharField(max_length=16, blank=True, db_index=True)  # төстэй зураг (dHash)
    created_at = models.DateTimeField(auto_now_add=True)


class Correction(models.Model):
    """Нийтлэгдсэн мэдээний залруулга, хариу тайлбар (хариу өгөх эрх), шинэчлэл — нийтэд ил харагдана."""
    KINDS = [("correction", "Залруулга"), ("reply", "Хариу тайлбар"), ("update", "Шинэчлэл")]
    content = models.ForeignKey(Content, on_delete=models.CASCADE, related_name="corrections")
    kind = models.CharField(max_length=12, choices=KINDS, default="correction")
    text = models.TextField()
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="+")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]


class ContentVersion(models.Model):
    """Шалгалтад илгээх бүрийн агшин — редактор «өмнөх хувилбартай харьцуулах»-д ашиглана."""
    content = models.ForeignKey(Content, on_delete=models.CASCADE, related_name="versions")
    number = models.PositiveIntegerField()
    title = models.CharField(max_length=250)
    body = models.TextField(blank=True)
    source = models.CharField(max_length=300, blank=True)
    tags = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["number"]
        unique_together = [("content", "number")]
