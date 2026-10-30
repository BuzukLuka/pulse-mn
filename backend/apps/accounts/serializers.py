from django.contrib.auth.password_validation import validate_password
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
                  "created_at", "experiences", "portfolio"]
        read_only_fields = ["id", "email", "role", "is_active", "is_verified", "created_at"]


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    role = serializers.ChoiceField(choices=[(r.value, r.label) for r in PUBLIC_ROLES], default=Role.JOURNALIST)

    class Meta:
        model = User
        fields = ["email", "password", "full_name", "phone", "organization", "role"]

    def validate_password(self, value):
        validate_password(value)
        return value

    def create(self, data):
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
                  "is_verified", "created_at", "last_login"]
        read_only_fields = ["id", "email", "full_name", "phone", "organization", "is_verified",
                            "created_at", "last_login"]
