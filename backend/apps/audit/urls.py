from django.urls import path
from .views import AuditLogList

urlpatterns = [path("admin/audit/", AuditLogList.as_view())]
