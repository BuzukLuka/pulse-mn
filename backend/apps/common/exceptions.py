from rest_framework.exceptions import APIException


class Unprocessable(APIException):
    """422 — жишээ нь шийдвэрийн шалтгаан заавал (UC-02)."""
    status_code = 422
    default_detail = "Хүсэлтийг боловсруулах боломжгүй."
    default_code = "unprocessable"


class Conflict(APIException):
    """409 — жишээ нь сүүлчийн админы эрхийг хасах (UC-03)."""
    status_code = 409
    default_detail = "Зөрчил үүслээ."
    default_code = "conflict"
