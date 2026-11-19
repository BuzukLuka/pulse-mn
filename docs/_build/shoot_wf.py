import os
import re
import subprocess

os.chdir(os.path.dirname(os.path.abspath(__file__)))
src = open("wireframes.html", encoding="utf8").read()
sizes = re.findall(r'title="([^"]*)" width="(\d+)" height="(\d+)"', open("sizes.txt", encoding="utf8").read())
E = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
os.makedirs("wf", exist_ok=True)
for i, (t, w, h) in enumerate(sizes, 1):
    css = ("html,body{background:#fff!important}body{padding:0!important;gap:0!important}"
           ".board h2{display:none!important}.board iframe{box-shadow:none!important}"
           f"section.board:not(:nth-of-type({i})){{display:none!important}}")
    # Bundle баримтыг дахин бичдэг тул загварыг рендерийн дараа тасралтгүй нэмнэ
    js = ("<script>setInterval(function(){if(document.head&&!document.getElementById('__wf')){"
          "var s=document.createElement('style');s.id='__wf';s.textContent=" + repr(css).replace("'", '"') +
          ";document.head.appendChild(s);}},50);</script>")
    v = js + src
    fn = os.path.abspath(f"v{i}.html")
    open(fn, "w", encoding="utf8").write(v)
    out = os.path.abspath(f"wf/{i:02d}.png")
    url = "file:///" + fn.replace(os.sep, "/")
    subprocess.run([E, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--virtual-time-budget=12000",
                    f"--window-size={w},{h}", f"--screenshot={out}", url], capture_output=True, timeout=120)
    os.remove(fn)
    print(i, t, os.path.getsize(out) if os.path.exists(out) else "MISSING")
