from django.db import models


class ExternalArticle(models.Model):
    """Гадны эх сурвалжаас (RSS / зөвшөөрөгдсөн API) татсан Монголын тухай мэдээ.

    Зохиогчийн эрх: зөвхөн гарчиг, богино хэсэг, AI хураангуй, эх холбоосыг хадгална — бүтэн текст хуулахгүй.
    """
    source = models.CharField(max_length=40, db_index=True)        # sources.SOURCES түлхүүр
    url = models.URLField(max_length=600, unique=True)
    title = models.CharField(max_length=400)
    title_mn = models.CharField(max_length=400, blank=True)        # AI орчуулга (англи эх сурвалжид)
    snippet = models.TextField(blank=True)
    summary_mn = models.TextField(blank=True)                      # AI хураангуй (Монголоор)
    language = models.CharField(max_length=5, default="en")
    published_at = models.DateTimeField(null=True, blank=True, db_index=True)
    category = models.ForeignKey("catalog.Category", null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    relevance = models.FloatField(default=0)                       # 0–1: Монголтой хэр холбоотой
    ai_source = models.CharField(max_length=10, default="rules")   # gemini | rules
    fetched_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-published_at", "-id"]


class FetchRun(models.Model):
    """Татах ажиллагааны бүртгэл (сүүлд хэзээ шинэчилсэн, эх сурвалж бүрийн үр дүн)."""
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    added = models.PositiveIntegerField(default=0)
    report = models.JSONField(default=dict)

    class Meta:
        ordering = ["-started_at"]
