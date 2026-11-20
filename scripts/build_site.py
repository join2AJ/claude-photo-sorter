"""Build the public demo website into site/ (plain files, no server needed). Host it on Netlify.

  python scripts/build_site.py

It uses only the drawn demo library from demo.py: no real photos, people, phone numbers or payments.
The sorting animation, the Details page (people, faces, screenshots, money, documents) and the
sample Excel download all work. Sorting your own photos needs the app on your computer.
"""
import os, shutil, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DASH, SITE = os.path.join(ROOT, "dashboard"), os.path.join(ROOT, "site")
FLAG = '<script>window.STATIC_DEMO = true;</script>\n'

subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "demo.py")], check=True)
if os.path.isdir(SITE):
    shutil.rmtree(SITE)
os.makedirs(SITE)
for f in os.listdir(DASH):
    if f.endswith((".html", ".css", ".js")):
        shutil.copy(os.path.join(DASH, f), SITE)
shutil.copytree(os.path.join(DASH, "demo"), os.path.join(SITE, "demo"))
for page in ("index.html", "details.html", "share.html"):
    p = os.path.join(SITE, page)
    html = open(p).read()
    i = html.index("<script src=")
    html = html[:i] + FLAG + html[i:]
    html = html.replace("<head>", '<head>\n<meta name="robots" content="noindex">', 1) if "--noindex" in sys.argv else html
    open(p, "w").write(html)
with open(os.path.join(SITE, "netlify.toml"), "w") as f:
    f.write('''# Public demo website: plain files, nothing to build.
[build]
  publish = "."
  command = "echo 'Static demo: nothing to build'"

[[headers]]
  for = "/*"
  [headers.values]
    X-Frame-Options = "DENY"
    X-Content-Type-Options = "nosniff"
    Referrer-Policy = "strict-origin-when-cross-origin"
    Permissions-Policy = "camera=(), microphone=(), geolocation=()"

[[headers]]
  for = "/demo/*"
  [headers.values]
    Cache-Control = "public, max-age=86400"
''')
size = sum(os.path.getsize(os.path.join(d, f)) for d, _, fs in os.walk(SITE) for f in fs)
print(f"Website ready in site/ ({size / 1e6:.0f} MB). Netlify: connect the repo (netlify.toml points to site/), "
      f"or drag the site folder onto app.netlify.com/drop.")
