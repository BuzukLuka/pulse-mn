from django.urls import path
from .views import CategoryList, DistrictList, ProvinceList

urlpatterns = [
    path("catalog/provinces/", ProvinceList.as_view()),
    path("catalog/districts/", DistrictList.as_view()),
    path("catalog/categories/", CategoryList.as_view()),
]
