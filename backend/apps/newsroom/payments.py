"""Төлбөрийн үйлчилгээ үзүүлэгч (provider) — шлюзийн API холбогдох хүртэл ДЕМО горимд ажиллана.

PAYMENT_PROVIDER=demo (анхдагч): нэхэмжлэх үүсгэж, худалдан авагч гараар баталгаажуулна; мөнгө шилжихгүй.
PAYMENT_PROVIDER=qpay: QPay гэрээ, merchant мэдээлэл (QPAY_USERNAME, QPAY_PASSWORD, QPAY_INVOICE_CODE) авсны дараа
QPayProvider-ийг хэрэгжүүлнэ. Интерфейс ижил тул бусад кодыг өөрчлөх шаардлагагүй.

Татвар: үнэ нь НӨАТ (10%) шингэсэн дүн. И-баримт (ebarimt.mn) холболт хийгдэх хүртэл баримтын дугаар ДЕМО.
"""
import os
import secrets

from apps.common.exceptions import Unprocessable

VAT_RATE = 0.10
PLATFORM_FEE_PCT = int(os.getenv("PLATFORM_FEE_PCT", "10"))
LICENSES = {"standard": ("Энгийн лиценз (давхар зарагдана)", 1), "exclusive": ("Онцгой эрх (зөвхөн нэг редакц)", 3)}


def breakdown(gross):
    """НӨАТ шингэсэн нийт дүнгээс татвар, платформын шимтгэл, сэтгүүлчид очих цэвэр дүнг салгана."""
    vat = round(gross * VAT_RATE / (1 + VAT_RATE))
    fee = round((gross - vat) * PLATFORM_FEE_PCT / 100)
    return {"amount": gross, "vat_amount": vat, "platform_fee": fee, "author_net": gross - vat - fee}


class DemoProvider:
    name = "demo"
    live = False

    def create_invoice(self, purchase):
        return {"provider_ref": f"DEMO-{secrets.token_hex(5).upper()}",
                "qr_text": f"PULSE-DEMO|{purchase.invoice_code}|{purchase.amount}",
                "instructions": "ДЕМО горим: бодит төлбөр хийгдэхгүй. «Төлбөр төлсөн» товчоор баталгаажуулна."}

    def check_paid(self, purchase):
        return None  # гараар баталгаажуулна

    def issue_receipt(self, purchase):
        return f"DEMO-EB-{secrets.token_hex(4).upper()}"


class QPayProvider(DemoProvider):
    """QPay merchant API холбогдоогүй. Гэрээ байгуулсны дараа токен авах, нэхэмжлэх үүсгэх, төлөлт шалгах
    (`/v2/auth/token`, `/v2/invoice`, `/v2/payment/check`) дуудлагуудыг энд хэрэгжүүлнэ."""
    name = "qpay"

    def create_invoice(self, purchase):
        raise Unprocessable("QPay холбогдоогүй байна. PAYMENT_PROVIDER=demo ашиглана уу.")


def get_provider():
    return {"demo": DemoProvider, "qpay": QPayProvider}.get(os.getenv("PAYMENT_PROVIDER", "demo"), DemoProvider)()
