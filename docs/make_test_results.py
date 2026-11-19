"""Тестийн үр дүнгийн тайлан (docs/TEST_RESULTS.md) үүсгэнэ.

    cd backend && python manage.py test apps -v 2 > ../docs/testlog.txt 2>&1
    python docs/make_test_results.py docs/testlog.txt
Тест бүрийн нэр, хамаарах модуль, тайлбар (docstring), үр дүнг хүснэгтээр гаргана.
"""
import datetime
import importlib
import os
import re
import sys
from collections import OrderedDict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
log = open(sys.argv[1], encoding="utf8", errors="replace").read()
# "test_x (apps.mod.tests.Class.test_x)\n[docstring]\n ... ok" эсвэл нэг мөрөнд
rows, lines = [], log.splitlines()
head = re.compile(r"^(test\w+) \(([\w.]+)\)(.*)$")
for i, ln in enumerate(lines):
    m = head.match(ln)
    if not m:
        continue
    doc, res = "", "?"
    # Тестийн дотоод лог дундуур орж ирвэл үр дүнг («... ok» эсвэл дан «ok») доороос хайна
    for j in range(i, min(i + 40, len(lines))):
        t = (m.group(3) if j == i else lines[j]).rstrip()
        if j > i and head.match(t):
            break
        if j == i + 1 and not t.startswith(("C:", "/", " ")) and " ... " in t:
            doc = t.split(" ... ")[0]
        r = re.search(r"(?:\.\.\. |^)(ok|FAIL|ERROR|skipped.*)$", t)
        if r:
            res = r.group(1)
            break
    rows.append((m.group(1), m.group(2), doc, res))
ran = re.search(r"Ran (\d+) tests in ([\d.]+)s", log)
status = "OK" if re.search(r"^OK", log, re.M) else "FAILED"

sys.path.insert(0, os.path.join(ROOT, "backend"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
docs = {}
try:
    import django
    django.setup()
    for name, path, _, _ in rows:
        mod, cls = path.rsplit(".", 2)[0], path.rsplit(".", 2)[1]
        try:
            k = getattr(importlib.import_module(mod), cls)
            docs[(cls, "")] = (k.__doc__ or "").strip().splitlines()[0] if k.__doc__ else ""
            f = getattr(k, name, None)
            docs[(cls, name)] = (f.__doc__ or "").strip().splitlines()[0] if f and f.__doc__ else ""
        except Exception:  # noqa: BLE001
            pass
except Exception:  # noqa: BLE001
    pass

groups = OrderedDict()
for name, path, doc, res in rows:
    cls = path.rsplit(".", 2)[1]
    groups.setdefault((path.rsplit(".", 2)[0], cls), []).append((name, (doc or docs.get((cls, name)) or "").strip(), res))

human = lambda n: n.removeprefix("test_").replace("_", " ")
icon = lambda r: "✅ Тэнцсэн" if r == "ok" else ("⏭ Алгассан" if r.startswith("skip") else f"❌ {r}")
passed = sum(1 for *_, r in rows if r == "ok")
out = [
    "# Pulse.mn — Тестийн үр дүнгийн тайлан", "",
    f"- **Огноо:** {datetime.datetime.now():%Y.%m.%d %H:%M} (Улаанбаатар)",
    f"- **Орчин:** Django {getattr(sys.modules.get('django'), '__version__', '5')} · Python {sys.version.split()[0]} · SQLite (тестийн DB)",
    f"- **Нийт:** {ran.group(1) if ran else len(rows)} тест · {ran.group(2) if ran else '?'} сек · **{status}**",
    f"- **Тэнцсэн:** {passed} · **Унасан:** {len(rows) - passed}", "",
    "Дахин үүсгэх: `cd backend && python manage.py test apps -v 2 > ../docs/testlog.txt 2>&1 && cd .. && python docs/make_test_results.py docs/testlog.txt`", "",
    "## Хураангуй (модуль бүрээр)", "", "| Модуль / анги | Тест | Тэнцсэн | Үр дүн |", "|---|---:|---:|---|",
]
for (mod, cls), items in groups.items():
    ok = sum(1 for *_, r in items if r == "ok")
    out.append(f"| `{mod.split('.')[1]}` · {cls} | {len(items)} | {ok} | {'✅' if ok == len(items) else '❌'} |")
n = 0
for (mod, cls), items in groups.items():
    out += ["", f"## {cls} — `{mod}`"]
    if docs.get((cls, "")):
        out += ["", f"_{docs[(cls, '')]}_"]
    out += ["", "| # | Test case | Тайлбар | Үр дүн |", "|---:|---|---|---|"]
    for name, doc, res in items:
        n += 1
        out.append(f"| TC-{n:03d} | `{name}` | {(doc or human(name)).replace('|', '/')} | {icon(res)} |")
dest = os.path.join(ROOT, "docs", "TEST_RESULTS.md")
open(dest, "w", encoding="utf8").write("\n".join(out) + "\n")
print(dest, len(rows), "tests", status)
