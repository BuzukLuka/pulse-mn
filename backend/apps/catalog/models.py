from django.db import models


class Province(models.Model):
    name = models.CharField(max_length=80, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class District(models.Model):
    province = models.ForeignKey(Province, on_delete=models.CASCADE, related_name="districts")
    name = models.CharField(max_length=80)

    class Meta:
        ordering = ["name"]
        unique_together = [("province", "name")]

    def __str__(self):
        return f"{self.province} / {self.name}"


class Category(models.Model):
    slug = models.SlugField(unique=True)
    name = models.CharField(max_length=80)

    class Meta:
        ordering = ["id"]
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name
