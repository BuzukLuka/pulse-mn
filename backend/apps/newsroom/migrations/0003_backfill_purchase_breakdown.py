from django.db import migrations


def backfill(apps, schema_editor):
    """Задаргаагүй (0003-аас өмнөх) худалдан авалтад НӨАТ, шимтгэл, сэтгүүлчийн дүнг тооцоолж бөглөнө."""
    from apps.newsroom.payments import breakdown
    Purchase = apps.get_model("newsroom", "Purchase")
    for p in Purchase.objects.filter(vat_amount=0, amount__gt=0):
        b = breakdown(p.amount)
        Purchase.objects.filter(pk=p.pk).update(vat_amount=b["vat_amount"], platform_fee=b["platform_fee"],
                                                author_net=b["author_net"])


class Migration(migrations.Migration):
    dependencies = [("newsroom", "0002_purchase_author_net_purchase_ebarimt_no_and_more")]
    operations = [migrations.RunPython(backfill, migrations.RunPython.noop)]
