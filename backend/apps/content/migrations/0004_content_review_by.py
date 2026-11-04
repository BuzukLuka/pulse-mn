from django.db import migrations, models


def route_pending(apps, schema_editor):
    """Шалгалтад байгаа мэдээнээс баталгаажсан редакцын идэвхтэй гишүүнийх нь редакц руу шилжинэ."""
    Content = apps.get_model("content", "Content")
    Membership = apps.get_model("newsroom", "Membership")
    for c in Content.objects.filter(status__in=["under_review", "changes_requested"], newsroom__isnull=False,
                                    newsroom__is_verified=True, newsroom__is_active=True):
        if Membership.objects.filter(newsroom_id=c.newsroom_id, journalist_id=c.author_id, status="active").exists():
            Content.objects.filter(pk=c.pk).update(review_by="newsroom")


class Migration(migrations.Migration):

    dependencies = [
        ("content", "0003_content_compliance_correction"),
        ("newsroom", "0003_backfill_purchase_breakdown"),
    ]

    operations = [
        migrations.AddField(
            model_name="content",
            name="review_by",
            field=models.CharField(db_index=True, default="pulse", max_length=10),
        ),
        migrations.RunPython(route_pending, migrations.RunPython.noop),
    ]
