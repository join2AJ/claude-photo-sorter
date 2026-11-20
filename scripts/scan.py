"""Step 1: inventory a folder of photos, videos and documents (any folder, Google Takeout, Apple Photos export...).

  python scripts/scan.py "/path/to/photos"              # everything
  python scripts/scan.py "/path/to/photos" --limit 200  # try a sample first

Records size, sha256, dimensions, video length and (for Google Takeout) the .json sidecar
date/GPS for each file, and makes a 256px square preview in dashboard/data/thumbs/.
Zip files inside the folder are unpacked into inbox/ (once) and their files are included.
Documents (PDF, Word, Excel, text...) get a preview of their first page.
Read-only on your photos.
"""
import argparse, functools, hashlib, json, os, random, re, shutil, subprocess, sys
from concurrent.futures import ThreadPoolExecutor

from PIL import Image, ImageOps
import imagehash

try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
except ImportError:
    pass

sys.path.insert(0, os.path.dirname(__file__))
from common import DATA, INBOX, LABELS, THUMBS, WORK, kind_of, safe_unzip, save

ap = argparse.ArgumentParser()
ap.add_argument("source")
ap.add_argument("--limit", type=int, default=0, help="only scan a random sample of N files")
args = ap.parse_args()
src = os.path.expanduser(args.source)
if not os.path.isdir(src):
    sys.exit(f"Folder not found: {src}")

HAS_FFMPEG = shutil.which("ffmpeg") and shutil.which("ffprobe")
MINI = os.path.join(DATA, "mini")  # 72px copies for the animation, so hundreds can move smoothly
for d in (THUMBS, MINI):
    if os.path.isdir(d):
        shutil.rmtree(d)
    os.makedirs(d)
# a new inventory means new ids: old contact sheets and labels would point at the wrong files
for d in (LABELS, os.path.join(WORK, "sheets")):
    shutil.rmtree(d, ignore_errors=True)
for f in ("labels.json", "dupes.json"):
    if os.path.exists(os.path.join(DATA, f)):
        os.remove(os.path.join(DATA, f))


@functools.lru_cache(maxsize=4096)
def json_files(d):
    return tuple(f for f in os.listdir(d) if f.endswith(".json"))


def sidecar(path):
    """Google Takeout writes '<file>.json' or '<file>.supplemental-metadata.json' (often truncated)."""
    d, name = os.path.split(path)
    m = re.match(r"(.*?)(\(\d+\))(\.\w+)$", name)  # IMG_1(1).JPG -> IMG_1.JPG...(1).json
    for f in json_files(d):
        if m and f.startswith(m.group(1) + m.group(3)) and f.endswith(m.group(2) + ".json"):
            return os.path.join(d, f)
        if not m and f.startswith(name + ".") and not re.search(r"\(\d+\)\.json$", f):
            return os.path.join(d, f)
    return None


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def square(im, size=256):
    im = im.convert("RGB")
    s = min(im.size)
    left, top = (im.width - s) // 2, (im.height - s) // 2
    return im.crop((left, top, left + s, top + s)).resize((size, size))


def video_info(path, thumb):
    if not HAS_FFMPEG:
        return 0, 0, 0.0
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                        "stream=width,height:stream_tags=rotate:format=duration", "-of", "json", path],
                       capture_output=True, text=True)
    j = json.loads(r.stdout or "{}")
    s = (j.get("streams") or [{}])[0]
    w, h = s.get("width", 0), s.get("height", 0)
    if str(s.get("tags", {}).get("rotate", "0")) in ("90", "-90", "270"):
        w, h = h, w
    dur = float(j.get("format", {}).get("duration", 0) or 0)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", "1" if dur > 2 else "0", "-i", path, "-frames:v", "1",
                    "-vf", "scale=256:256:force_original_aspect_ratio=increase,crop=256:256", thumb])
    return w, h, dur


def doc_preview(path, ext, thumb):
    """First page of a PDF; for other documents a paper tile with the file type."""
    if ext == ".pdf":
        try:
            import pypdfium2 as pdfium
            pdf = pdfium.PdfDocument(path)
            page = pdf[0]
            im = page.render(scale=300 / max(page.get_size())).to_pil()
            pdf.close()
            square_top(im).save(thumb, quality=80)
            return
        except Exception:
            pass
    from PIL import ImageDraw, ImageFont
    colors = {".docx": (43, 87, 154), ".doc": (43, 87, 154), ".xlsx": (33, 115, 70), ".xls": (33, 115, 70),
              ".csv": (33, 115, 70), ".ods": (33, 115, 70), ".pptx": (196, 72, 38), ".ppt": (196, 72, 38), ".pdf": (180, 40, 40)}
    im = Image.new("RGB", (256, 256), (236, 233, 226))
    d = ImageDraw.Draw(im)
    d.rectangle((48, 24, 208, 232), fill="white", outline=(200, 196, 188))
    for y in range(70, 200, 18):
        d.line((66, y, 190, y), fill=(220, 217, 210), width=6)
    font = None
    for f in ("/System/Library/Fonts/Helvetica.ttc", "arial.ttf", "DejaVuSans-Bold.ttf", "DejaVuSans.ttf"):
        try:
            font = ImageFont.truetype(f, 30)
            break
        except OSError:
            pass
    d.rounded_rectangle((60, 150, 196, 196), 8, fill=colors.get(ext, (90, 90, 100)))
    d.text((128, 173), ext[1:].upper(), fill="white", font=font or ImageFont.load_default(), anchor="mm")
    im.save(thumb, quality=85)


def square_top(im, size=256):
    """Square crop from the top, so a page preview shows its heading."""
    im = im.convert("RGB")
    s = min(im.size)
    return im.crop(((im.width - s) // 2, 0, (im.width + s) // 2, s)).resize((size, size))


def process(args):
    i, path = args
    ext = os.path.splitext(path)[1].lower()
    kind = kind_of(path)
    rec = {"id": i, "path": path, "name": os.path.basename(path), "ext": ext, "kind": kind,
           "bytes": os.path.getsize(path), "mtime": int(os.path.getmtime(path)), "sha256": sha(path)}
    thumb = os.path.join(THUMBS, f"{i}.jpg")
    real_preview = True  # only real previews get a look-alike fingerprint (grey placeholders all look the same)
    try:
        if kind == "doc":
            doc_preview(path, ext, thumb)
            real_preview = False
        elif kind == "video":
            rec["w"], rec["h"], rec["duration"] = video_info(path, thumb)
            if not os.path.exists(thumb):  # no ffmpeg: grey placeholder so the dashboard still works
                Image.new("RGB", (256, 256), (60, 60, 66)).save(thumb)
                real_preview = False
        else:
            with Image.open(path) as im:
                rec["w"], rec["h"] = im.size
                im.draft("RGB", (512, 512))
                square(ImageOps.exif_transpose(im)).save(thumb, quality=80)
        with Image.open(thumb) as t:
            if real_preview and t.convert("L").getextrema()[1] - t.convert("L").getextrema()[0] > 24:  # skip blank/black frames
                rec["phash"] = str(imagehash.phash(t))
            t.convert("RGB").resize((72, 72)).save(os.path.join(MINI, f"{i}.jpg"), quality=72)
    except Exception as e:  # unreadable file: keep it in the inventory, flag it
        rec["error"] = str(e)[:200]
        Image.new("RGB", (256, 256), (230, 228, 222)).save(thumb)
        Image.new("RGB", (72, 72), (230, 228, 222)).save(os.path.join(MINI, f"{i}.jpg"))
    sc = sidecar(path)
    if sc:
        try:
            j = json.load(open(sc))
            rec["taken"] = int(j.get("photoTakenTime", {}).get("timestamp", 0)) or None
            g = j.get("geoData") or {}
            if g.get("latitude"):
                rec["geo"] = [g["latitude"], g["longitude"]]
        except Exception:
            pass
    return rec


def walk(top):
    for dp, dirs, fs in os.walk(top):
        dirs[:] = [d for d in dirs if not d.startswith(".") and not d.endswith(" (sorted)")]
        for f in fs:
            if not f.startswith("._"):
                yield os.path.join(dp, f)


files, zips = [], []
for p in walk(src):
    (zips if p.lower().endswith(".zip") else files).append(p)
for z in zips:  # Google Takeout and shared folders often come as zips: unpack once, include what's inside
    st = os.stat(z)
    dest = os.path.join(INBOX, "zips", hashlib.sha1(f"{z}|{st.st_size}|{st.st_mtime}".encode()).hexdigest()[:10]
                        + " " + os.path.splitext(os.path.basename(z))[0][:40])
    try:
        print(f"Unpacking {os.path.basename(z)}...", flush=True)
        files += list(walk(safe_unzip(z, dest)))
    except Exception as e:
        print(f"  could not unpack {os.path.basename(z)}: {e}", flush=True)
files = sorted(f for f in files if kind_of(f))
if not files:
    sys.exit("No photos, videos or documents found in that folder.")
if args.limit and args.limit < len(files):
    files = sorted(random.Random(0).sample(files, args.limit))
print(f"Scanning {len(files)} files...", flush=True)
if not HAS_FFMPEG and any(kind_of(f) == "video" for f in files):
    print("  note: ffmpeg not installed, videos will get grey previews (Mac: brew install ffmpeg)")

with ThreadPoolExecutor(8) as ex:
    recs = []
    for n, r in enumerate(ex.map(process, enumerate(files)), 1):
        recs.append(r)
        if n % 20 == 0 or n == len(files):
            print(f"PROGRESS {n} {len(files)}", flush=True)
        if n % 200 == 0:
            print(f"  {n}/{len(files)}", flush=True)

save(os.path.join(DATA, "inventory.json"), recs)
save(os.path.join(DATA, "source.json"), {"source": src, "limit": args.limit})
bad = [r["name"] for r in recs if "error" in r]
print(f"Done: {len(recs)} files ({sum(r['kind'] == 'video' for r in recs)} videos, "
      f"{sum(r['kind'] == 'doc' for r in recs)} documents), "
      f"{sum(r['bytes'] for r in recs) / 1e9:.1f} GB" + (f", {len(bad)} unreadable: {bad[:5]}" if bad else ""))
