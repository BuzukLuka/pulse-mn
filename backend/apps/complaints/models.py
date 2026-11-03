from django.conf import settings
from django.db import models


class Complaint(models.Model):
    TARGETS = [("content", "Мэдээ"), ("pledge", "Амлалт"), ("indicator", "Статистик үзүүлэлт")]
    KINDS = [("wrong", "Буруу мэдээлэл"), ("duplicate", "Хуулбар"), ("copyright", "Зохиогчийн эрх"),
             ("privacy", "Хувийн мэдээлэл"), ("defamation", "Гүтгэлэг, нэр төр"), ("minor", "Хүүхдийн эрх"),
             ("reply", "Хариу тайлбар өгөх хүсэлт"), ("other", "Бусад")]
    STATUSES = [("open", "Нээлттэй"), ("resolved", "Шийдвэрлэсэн"), ("dismissed", "Хүлээн аваагүй")]
    reporter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="complaints")
    target_type = models.CharField(max_length=10, choices=TARGETS)
    target_id = models.PositiveIntegerField()
    kind = models.CharField(max_length=10, choices=KINDS, default="wrong")
    text = models.TextField()
    evidence_url = models.URLField(blank=True)
    status = models.CharField(max_length=10, choices=STATUSES, default="open", db_index=True)
    resolution = models.TextField(blank=True)
    resolved_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    resolved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
