from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models


class Role(models.TextChoices):
    JOURNALIST = "journalist", "Сэтгүүлч"
    EDITOR = "editor", "Редактор"
    NEWSROOM = "newsroom", "Редакци / байгууллага"
    CITIZEN = "citizen", "Иргэн"
    ADMIN = "admin", "Администратор"


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra):
        if not email:
            raise ValueError("Имэйл заавал")
        user = self.model(email=self.normalize_email(email), **extra)
        user.set_password(password)  # нууц үг hash-лагдана (NFR-003)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra):
        extra.update(role=Role.ADMIN, is_staff=True, is_superuser=True)
        return self.create_user(email, password, **extra)


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=120, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    organization = models.CharField(max_length=160, blank=True)
    bio = models.TextField(blank=True)
    province = models.ForeignKey("catalog.Province", null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    district = models.ForeignKey("catalog.District", null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.CITIZEN, db_index=True)
    is_verified = models.BooleanField(default=False)  # «Баталгаажсан» тэмдэг (админ олгоно)
    verification_requested_at = models.DateTimeField(null=True, blank=True)  # хэрэглэгч хүсэлт илгээсэн
    # Хууль эрх зүйн зөвшөөрөл (Хувийн мэдээлэл хамгаалах тухай хууль, үйлчилгээний нөхцөл, ёс зүйн дүрэм)
    terms_accepted_at = models.DateTimeField(null=True, blank=True)
    privacy_consent_at = models.DateTimeField(null=True, blank=True)
    ethics_accepted_at = models.DateTimeField(null=True, blank=True)  # сэтгүүлч: ёс зүйн дүрэм
    press_card_no = models.CharField(max_length=40, blank=True)       # сэтгүүлчийн үнэмлэхийн дугаар
    # Редакц: хуулийн этгээдийн мэдээлэл (Хэвлэлийн эрх чөлөөний тухай хууль — хариуцлага хүлээх этгээд)
    legal_name = models.CharField(max_length=200, blank=True)
    registry_no = models.CharField(max_length=20, blank=True)         # хуулийн этгээдийн регистрийн дугаар
    responsible_editor = models.CharField(max_length=120, blank=True) # хариуцлагатай эрхлэгч
    anonymized_at = models.DateTimeField(null=True, blank=True)       # бүртгэл устгасан (мэдээлэл нууцалсан)
    show_email = models.BooleanField(default=False)   # профайлын нууцлалын тохиргоо
    show_phone = models.BooleanField(default=False)
    show_org = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = "email"
    objects = UserManager()

    def __str__(self):
        return self.email


class Experience(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="experiences")
    organization = models.CharField(max_length=160)
    position = models.CharField(max_length=160, blank=True)
    period = models.CharField(max_length=60, blank=True)

    class Meta:
        ordering = ["id"]


class PortfolioItem(models.Model):
    KINDS = [("news", "Мэдээ"), ("article", "Нийтлэл"), ("photo", "Зураг"), ("video", "Видео"), ("document", "Баримт")]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="portfolio")
    title = models.CharField(max_length=200)
    kind = models.CharField(max_length=10, choices=KINDS, default="news")
    year = models.PositiveSmallIntegerField(null=True, blank=True)
    url = models.URLField(blank=True)

    class Meta:
        ordering = ["-year", "id"]
