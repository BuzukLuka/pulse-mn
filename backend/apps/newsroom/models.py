from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Membership(models.Model):
    """Сэтгүүлч ↔ редакц: сэтгүүлч хүсэлт илгээж, редакц баталснаар «редакцын сэтгүүлч» болно."""
    STATUSES = [("pending", "Хүлээгдэж буй"), ("active", "Идэвхтэй"), ("rejected", "Татгалзсан"), ("left", "Гарсан")]
    newsroom = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="newsroom_members")
    journalist = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="memberships")
    status = models.CharField(max_length=10, choices=STATUSES, default="pending", db_index=True)
    message = models.CharField(max_length=300, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    decided_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [models.UniqueConstraint(fields=["newsroom", "journalist"], name="uniq_membership")]


class Purchase(models.Model):
    """Редакц нийтлэгдсэн мэдээг худалдан авах (ДЕМО төлбөр — бодит төлбөрийн систем холбогдоогүй)."""
    STATUSES = [("pending", "Төлбөр хүлээгдэж буй"), ("paid", "Төлөгдсөн"), ("cancelled", "Цуцалсан")]
    content = models.ForeignKey("content.Content", on_delete=models.CASCADE, related_name="purchases")
    buyer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="purchases")
    amount = models.PositiveIntegerField()
    invoice_code = models.CharField(max_length=20, unique=True)
    status = models.CharField(max_length=10, choices=STATUSES, default="pending", db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]


class Rating(models.Model):
    """Сэтгүүлч эсвэл редакцад өгөх үнэлгээ (1–5). Нэг хэрэглэгч нэг объектод нэг үнэлгээ (засаж болно)."""
    rater = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="ratings_given")
    target = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="ratings_received")
    content = models.ForeignKey("content.Content", null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    score = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        constraints = [models.UniqueConstraint(fields=["rater", "target"], name="uniq_rating")]
