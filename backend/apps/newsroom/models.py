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
    STATUSES = [("pending", "Төлбөр хүлээгдэж буй"), ("paid", "Төлөгдсөн"), ("cancelled", "Цуцалсан"),
                ("refunded", "Буцаан олгосон")]
    LICENSES = [("standard", "Энгийн лиценз"), ("exclusive", "Онцгой эрх")]
    content = models.ForeignKey("content.Content", on_delete=models.CASCADE, related_name="purchases")
    buyer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="purchases")
    license_type = models.CharField(max_length=10, choices=LICENSES, default="standard")
    amount = models.PositiveIntegerField()                       # НӨАТ шингэсэн нийт дүн
    vat_amount = models.PositiveIntegerField(default=0)
    platform_fee = models.PositiveIntegerField(default=0)
    author_net = models.PositiveIntegerField(default=0)          # сэтгүүлчид шилжүүлэх дүн
    provider = models.CharField(max_length=20, default="demo")
    provider_ref = models.CharField(max_length=60, blank=True)
    ebarimt_no = models.CharField(max_length=40, blank=True)     # И-баримтын дугаар (ДЕМО)
    terms_accepted_at = models.DateTimeField(null=True, blank=True)
    refund_reason = models.CharField(max_length=300, blank=True)
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
