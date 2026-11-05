"""Нэг удаагийн тохиргоо (serverless орчинд migrate/seed ажиллуулах).

OPS_TOKEN орчны хувьсагч хоосон бол endpoint 404 буцаана — ажлаа дуусгаад токеныг устгахад л хаагдана.
    POST /ops/run/?step=migrate          (X-Ops-Token: <токен>)
    POST /ops/run/?step=seed&only=news&news=40
"""
import hmac
import io
import os

from django.core.management import call_command
from django.http import Http404, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST


@csrf_exempt
@require_POST
def run(request):
    token = os.getenv("OPS_TOKEN", "")
    if not token or not hmac.compare_digest(request.headers.get("X-Ops-Token", ""), token):
        raise Http404
    out = io.StringIO()
    step = request.GET.get("step")
    if step == "migrate":
        call_command("migrate", interactive=False, stdout=out, verbosity=1)
    elif step == "import_parliament":
        call_command("import_parliament", stdout=out)
    elif step == "seed":
        call_command("seed_test", news=int(request.GET.get("news", 120)), only=request.GET.get("only", ""), stdout=out)
    else:
        return JsonResponse({"error": "step=migrate|seed"}, status=400)
    return JsonResponse({"step": step, "output": out.getvalue()[-4000:]})
