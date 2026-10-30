from rest_framework import generics, permissions
from .models import Category, District, Province
from .serializers import CategorySerializer, DistrictSerializer, ProvinceSerializer


class Open(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    pagination_class = None


class ProvinceList(Open):
    queryset = Province.objects.all()
    serializer_class = ProvinceSerializer


class DistrictList(Open):
    serializer_class = DistrictSerializer

    def get_queryset(self):
        qs = District.objects.all()
        if self.request.query_params.get("province"):
            qs = qs.filter(province_id=self.request.query_params["province"])
        return qs


class CategoryList(Open):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
