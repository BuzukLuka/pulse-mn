"""Vercel Blob storage (serverless дээр диск зөвхөн уншигддаг тул медиа файлыг Blob-д хадгална).

BLOB_READ_WRITE_TOKEN тохируулсан үед settings.STORAGES энэ классыг ашиглана. REST протокол нь
@vercel/blob SDK-тай ижил: PUT https://vercel.com/api/blob/?pathname=<нэр>.
"""
import mimetypes
import os
import uuid

import requests
from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible

API_URL = "https://vercel.com/api/blob"
API_VERSION = "13"


@deconstructible
class VercelBlobStorage(Storage):
    def __init__(self):
        self.token = os.getenv("BLOB_READ_WRITE_TOKEN", "")
        # vercel_blob_rw_<storeId>_<secret> — эсвэл BLOB_STORE_ID-ээр шууд заана
        store = os.getenv("BLOB_STORE_ID") or (self.token.split("_")[3] if self.token.count("_") >= 4 else "")
        self.store_id = store.removeprefix("store_").lower()

    def _headers(self, **extra):
        return {"authorization": f"Bearer {self.token}", "x-api-version": API_VERSION,
                "x-vercel-blob-store-id": self.store_id, **extra}

    def _save(self, name, content):
        # Давхцахгүй нэр өөрсдөө өгнө (FileField-ийн 100 тэмдэгтийн хязгаарт багтаана)
        head, tail = os.path.split(name)
        name = f"{head}/{uuid.uuid4().hex[:10]}-{tail[-60:]}".lstrip("/")
        content.seek(0)
        r = requests.put(f"{API_URL}/", params={"pathname": name}, data=content.read(), timeout=60,
                         headers=self._headers(**{
                             "x-vercel-blob-access": "public", "x-add-random-suffix": "0",
                             "x-content-type": mimetypes.guess_type(name)[0] or "application/octet-stream"}))
        if r.status_code >= 400:
            raise OSError(f"Vercel Blob upload failed ({r.status_code}): {r.text[:200]}")
        return r.json().get("pathname", name)

    def url(self, name):
        return f"https://{self.store_id}.public.blob.vercel-storage.com/{name}"

    def exists(self, name):
        return False  # _save нэр бүрийг давхцахгүй болгодог

    def delete(self, name):
        requests.post(f"{API_URL}/delete", json={"urls": [self.url(name)]}, headers=self._headers(), timeout=30)

    def size(self, name):
        r = requests.head(self.url(name), timeout=15)
        return int(r.headers.get("content-length", 0))
