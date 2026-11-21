"""Shared paths and helpers. Everything the tool writes lives inside this repo:
  dashboard/data/   inventory, thumbnails, labels (what the dashboard reads)
  work/             contact sheets, raw labels and library.db (faces, people, details)
  inbox/            zip files unpacked and links downloaded (your copies, safe to delete)
  models/           free open-source models, downloaded once by scripts/models.py
Your original photos are only ever read, never changed.
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "dashboard", "data")
THUMBS = os.path.join(DATA, "thumbs")
WORK = os.path.join(ROOT, "work")
LABELS = os.path.join(WORK, "labels")      # Claude writes one JSON per batch here
JEV_OUT = os.path.join(WORK, "jev.json")   # Jev labels (optional)
CATEGORIES = os.path.join(ROOT, "categories.json")
INBOX = os.path.join(ROOT, "inbox")
MODELS = os.path.join(ROOT, "models")
DB = os.path.join(WORK, "library.db")

IMG = {".jpg", ".jpeg", ".png", ".heic", ".heif", ".webp", ".gif", ".bmp", ".tif", ".tiff"}
VID = {".mov", ".mp4", ".m4v", ".3gp", ".avi", ".mkv", ".webm"}
DOC = {".pdf", ".docx", ".doc", ".xlsx", ".xls", ".csv", ".txt", ".md", ".pptx", ".ppt", ".odt", ".ods", ".rtf"}
ARCHIVE = {".zip"}
KINDS = ("photo", "video", "doc")


def kind_of(path):
    ext = os.path.splitext(path)[1].lower()
    return "photo" if ext in IMG else "video" if ext in VID else "doc" if ext in DOC else None


SETTINGS = os.path.join(WORK, "settings.json")
DEFAULT_SETTINGS = {"estimates": True}  # age, gender and emotion guesses; off = never computed or shown


def settings():
    s = dict(DEFAULT_SETTINGS)
    s.update(load(SETTINGS, {}) or {})
    return s


def load(path, default=None):
    if not os.path.exists(path):
        return default
    with open(path) as f:
        return json.load(f)


def save(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(obj, f, indent=1)


def categories():
    cats = load(CATEGORIES)
    keys = [c["key"] for c in cats]
    assert len(keys) == len(set(keys)), "categories.json has duplicate keys"
    for kind in ("photo", "video"):  # doc folders are optional
        assert any(c["kind"] == kind for c in cats), f"categories.json needs at least one {kind} folder"
    return cats


def safe_unzip(zip_path, dest, depth=0):
    """Unpack a zip into dest, safely: no paths that escape dest, no Mac junk, stops if the disk would fill.
    Zips inside the zip are unpacked too (up to 3 levels). A '.unzipped' marker makes it run only once."""
    import shutil, zipfile
    marker = os.path.join(dest, ".unzipped")
    if os.path.exists(marker):
        return dest
    os.makedirs(dest, exist_ok=True)
    root = os.path.realpath(dest)
    with zipfile.ZipFile(zip_path) as z:
        members = [m for m in z.infolist() if not m.is_dir() and "__MACOSX" not in m.filename
                   and not os.path.basename(m.filename).startswith("._")]
        need = sum(m.file_size for m in members)
        free = shutil.disk_usage(root).free
        if need > free * 0.9:
            raise RuntimeError(f"Not enough disk space to unpack {os.path.basename(zip_path)}: "
                               f"needs {need / 1e9:.1f} GB, {free / 1e9:.1f} GB free.")
        for m in members:
            target = os.path.realpath(os.path.join(root, m.filename))
            if not target.startswith(root + os.sep):
                continue  # a path like ../../x would land outside: skip it
            os.makedirs(os.path.dirname(target), exist_ok=True)
            with z.open(m) as src, open(target, "wb") as out:
                shutil.copyfileobj(src, out, 1 << 20)
            if depth < 3 and target.lower().endswith(".zip"):
                try:
                    safe_unzip(target, os.path.splitext(target)[0], depth + 1)
                    os.remove(target)  # our own copy, already unpacked
                except zipfile.BadZipFile:
                    pass
    open(marker, "w").close()
    return dest
