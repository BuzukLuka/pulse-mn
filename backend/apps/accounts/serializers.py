import re

from django.contrib.auth.password_validation import validate_password
from django.utils import timezone
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import Experience, PortfolioItem, Role, User

PUBLIC_ROLES = [Role.JOURNALIST, Role.NEWSROOM, Role.CITIZEN]


class ExperienceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Experience
        fields = ["id", "organization", "position", "period"]


class PortfolioSerializer(serializers.ModelSerializer):
    class Meta:
        model = PortfolioItem
        fields = ["id", "title", "kind", "year", "url"]


class UserSerializer(serializers.ModelSerializer):
    experiences = ExperienceSerializer(many=True, read_only=True)
    portfolio = PortfolioSerializer(many=True, read_only=True)
    province_name = serializers.CharField(source="province.name", default=None, read_only=True)

    class Meta:
        model = User
        fields = ["id", "email", "full_name", "phone", "organization", "bio", "province", "province_name",
                  "district", "show_email", "show_phone", "show_org", "role", "is_active", "is_verified",
                  "verification_requested_at", "created_at", "experiences", "portfolio",
                  "press_card_no", "legal_name", "registry_no", "responsible_editor",
                  "terms_accepted_at", "privacy_consent_at", "ethics_accepted_at"]
        read_only_fields = ["id", "email", "role", "is_active", "is_verified", "verification_requested_at", "created_at",
                            "terms_accepted_at", "privacy_consent_at", "ethics_accepted_at"]

    def validate_registry_no(self, v):
        return validate_registry(v)


def validate_registry(v):
    """Монголын хуулийн этгээдийн регистр 7 оронтой тоо."""
    v = (v or "").strip()
    if v and not re.fullmatch(r"\d{7}", v):
        raise serializers.ValidationError("Хуулийн этгээдийн регистрийн дугаар 7 оронтой тоо байна.")
    return v


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    role = serializers.ChoiceField(choices=[(r.value, r.label) for r in PUBLIC_ROLES], default=Role.JOURNALIST)
    accept_terms = serializers.BooleanField(write_only=True, default=False)
    accept_privacy = serializers.BooleanField(write_only=True, default=False)
    accept_ethics = serializers.BooleanField(write_only=True, default=False)

    class Meta:
        model = User
        fields = ["email", "password", "full_name", "phone", "organization", "role", "accept_terms", "accept_privacy",
                  "accept_ethics", "legal_name", "registry_no", "responsible_editor", "press_card_no"]

    def validate_password(self, value):
        validate_password(value)
        return value

    def validate_registry_no(self, v):
        return validate_registry(v)

    def validate(self, a):
        err = {}
        if not a.get("accept_terms"):
            err["accept_terms"] = "Үйлчилгээний нөхцөлийг зөвшөөрнө үү."
        if not a.get("accept_privacy"):
            err["accept_privacy"] = "Хувийн мэдээлэл боловсруулах зөвшөөрөл заавал (Хувийн мэдээлэл хамгаалах тухай хууль)."
        if a.get("role") == Role.JOURNALIST and not a.get("accept_ethics"):
            err["accept_ethics"] = "Сэтгүүлчийн ёс зүйн дүрмийг хүлээн зөвшөөрнө үү."
        if a.get("role") == Role.NEWSROOM:
            for f, msg in (("legal_name", "Хуулийн этгээдийн нэр заавал."), ("registry_no", "Регистрийн дугаар заавал."),
                           ("responsible_editor", "Хариуцлагатай эрхлэгчийн нэр заавал.")):
                if not str(a.get(f, "")).strip():
                    err[f] = msg
        if err:
            raise serializers.ValidationError(err)
        return a

    def create(self, data):
        now = timezone.now()
        data.pop("accept_terms"); data.pop("accept_privacy")
        ethics = data.pop("accept_ethics")
        data.update(terms_accepted_at=now, privacy_consent_at=now,
                    ethics_accepted_at=now if ethics and data.get("role") == Role.JOURNALIST else None)
        return User.objects.create_user(**data)


class LoginSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["role"] = user.role
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data["user"] = UserSerializer(self.user).data
        return data


class AdminUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "full_name", "phone", "organization", "role", "is_active",
                  "is_verified", "verification_requested_at", "created_at", "last_login",
                  "press_card_no", "legal_name", "registry_no", "responsible_editor", "anonymized_at"]
        read_only_fields = ["id", "email", "full_name", "phone", "organization", "is_verified",
                            "verification_requested_at", "created_at", "last_login",
                            "press_card_no", "legal_name", "registry_no", "responsible_editor", "anonymized_at"]
