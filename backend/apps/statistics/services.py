import csv
import io
import ipaddress
import socket
from decimal import Decimal, InvalidOperation
from urllib.parse import urlparse

import requests
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.audit import models as audit
from apps.catalog.models import Province
from apps.common.exceptions import Unprocessable
from .models import Indicator, IndicatorValue, IndicatorValueHistory

MAX_CSV_BYTES = 5 * 1024 * 1024


def safe_fetch(url):
    """SSRF хамгаалалттай татаж авалт: зөвхөн http(s), дотоод/loopback хаяг хориотой."""
    u = urlparse(url)
    if u.scheme not in ("http", "https") or not u.hostname:
        raise ValidationError({"url": ["Зөвхөн http/https холбоос зөвшөөрнө."]})
    try:
        for info in socket.getaddrinfo(u.hostname, None):
            ip = ipaddress.ip_address(info[4][0])
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
                raise ValidationError({"url": ["Дотоод сүлжээний хаяг руу холбогдохыг хориглоно."]})
    except socket.gaierror:
        raise ValidationError({"url": ["Хаяг олдсонгүй."]})
    r = requests.get(url, timeout=15, stream=True, allow_redirects=False)
    r.raise_for_status()
    data = r.raw.read(MAX_CSV_BYTES + 1, decode_content=True)
    if len(data) > MAX_CSV_BYTES:
        raise ValidationError({"url": ["Файл 5MB-аас хэтэрсэн."]})
    return data


@transaction.atomic
def set_value(user, indicator, province, year, value, reason, district=None):
    """Утга нэмэх/засах. Засахад өмнөх утгыг түүхэд хадгална (өмнөх хувилбар)."""
    if not reason.strip():
        raise Unprocessable("Өөрчлөлтийн шалтгаан заавал.")
    try:
        value = Decimal(str(value))
    except InvalidOperation:
        raise ValidationError({"value": ["Тоон утга оруулна уу."]})
    obj, created = IndicatorValue.objects.get_or_create(
        indicator=indicator, province=province, district=district, year=year, defaults={"value": value})
    old = None if created else obj.value
    if not created:
        obj.value = value
        obj.save(update_fields=["value", "updated_at"])
    IndicatorValueHistory.objects.create(value_ref=obj, old_value=old, new_value=value, reason=reason, changed_by=user)
    audit.log(user, "indicator.value", "indicator_value", obj.pk,
              {"value": str(old) if old is not None else None}, {"value": str(value)}, reason)
    return obj


@transaction.atomic
def restore(user, history, reason):
    return set_value(user, history.value_ref.indicator, history.value_ref.province, history.value_ref.year,
                     history.old_value if history.old_value is not None else history.new_value,
                     reason or f"Түүхээс сэргээв #{history.pk}", history.value_ref.district)


def import_csv(user, source, raw: bytes):
    """CSV: indicator,province,year,value. Алдаатай мөрийг алгасаж, байгаа зөв утгыг устгахгүй."""
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        source.status, source.last_error = "error", "UTF-8 кодчилолтой CSV байх ёстой."
        source.save(update_fields=["status", "last_error"])
        raise ValidationError({"file": [source.last_error]})
    provinces = {p.name.lower(): p for p in Province.objects.all()}
    inds = {i.name.lower(): i for i in Indicator.objects.filter(source=source)}
    ok, errors = 0, []
    for n, row in enumerate(csv.DictReader(io.StringIO(text)), start=2):
        try:
            ind = inds[row["indicator"].strip().lower()]
            prov = provinces[row["province"].strip().lower()] if row.get("province", "").strip() else None
            set_value(user, ind, prov, int(row["year"]), row["value"].replace(" ", ""), f"CSV импорт: {source.name}")
            ok += 1
        except (KeyError, ValueError, ValidationError, Unprocessable) as e:
            errors.append(f"Мөр {n}: {e}")
    source.last_synced_at = timezone.now()
    source.status = "ok" if not errors or ok else "error"
    source.last_error = "\n".join(errors[:20])
    source.save(update_fields=["last_synced_at", "status", "last_error"])
    return {"imported": ok, "errors": errors[:20]}
