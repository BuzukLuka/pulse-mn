import os, sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
from django.core.wsgi import get_wsgi_application
app = application = get_wsgi_application()


def _bootstrap():
    """Cold start: хүлээгдэж буй migration-ыг хэрэгжүүлж, УИХ-ын гишүүд хоосон бол parliament.mn-ээс нэг удаа импортлоно."""
    try:
        from django.core.management import call_command
        from django.db import connection
        from django.db.migrations.executor import MigrationExecutor
        ex = MigrationExecutor(connection)
        if ex.migration_plan(ex.loader.graph.leaf_nodes()):
            call_command("migrate", interactive=False, verbosity=0)
        from apps.pledges.models import Politician
        if not Politician.objects.filter(parliament_id__isnull=False).exists():
            call_command("import_parliament", verbosity=0)
    except Exception as e:  # noqa: BLE001 — ачаалалт унагахгүй, логд үлдээнэ
        print("bootstrap:", e, file=sys.stderr)


if os.getenv("VERCEL"):
    _bootstrap()
