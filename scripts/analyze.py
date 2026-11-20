"""Step 2b: look inside every file, on this computer, with free open-source models.

  python scripts/analyze.py            # new files only (results are kept per file, by content)
  python scripts/analyze.py --again    # redo everything

Photos:    date, camera, GPS, faces (who, estimated age / gender / emotion), main things in it,
           and for screenshots the text, company/app, what kind of screen, amounts and transaction ids.
Videos:    date, camera, GPS, length, and faces from frames every few seconds.
Documents: text, type (bill, bank statement, ID, ticket...), company, amounts.
Faces of the same person get the same person number (P0001...). Name people on the Details page.
Writes work/library.db and face pictures in dashboard/data/faces/. Your files are only read.
"""
import os, re, sqlite3, subprocess, sys, tempfile, time
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime, timezone

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
from common import DATA, DB, load

VERSION = 1
FACES_DIR = os.path.join(DATA, "faces")

SCHEMA = """
CREATE TABLE IF NOT EXISTS files (
  sha256 TEXT PRIMARY KEY, version INT, name TEXT, ext TEXT, kind TEXT, bytes INT, width INT, height INT,
  duration REAL, taken TEXT, camera TEXT, lens TEXT, lat REAL, lon REAL, is_screenshot INT, tags TEXT,
  text TEXT, company TEXT, sector TEXT, content TEXT, amount REAL, currency TEXT, direction TEXT,
  txn_ids TEXT, face_count INT, error TEXT, analysed_at TEXT);
CREATE TABLE IF NOT EXISTS people (
  person_id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, mobile TEXT, mobile_verified INT DEFAULT 0,
  consent TEXT DEFAULT 'pending', consent_at TEXT, share_with TEXT DEFAULT '', hide_from TEXT DEFAULT '',
  centroid BLOB, n INT DEFAULT 0, created_at TEXT, notes TEXT);
CREATE TABLE IF NOT EXISTS faces (
  face_id INTEGER PRIMARY KEY AUTOINCREMENT, sha256 TEXT, frame_s REAL, x INT, y INT, w INT, h INT,
  img_w INT, img_h INT, score REAL, embedding BLOB, age TEXT, age_years INT, gender TEXT, gender_conf REAL,
  emotion TEXT, emotion_conf REAL, person_id INT, manual INT DEFAULT 0);
CREATE INDEX IF NOT EXISTS faces_sha ON faces(sha256);
CREATE INDEX IF NOT EXISTS faces_person ON faces(person_id);
CREATE TABLE IF NOT EXISTS consent_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT, person_id INT, action TEXT, detail TEXT, at TEXT);
"""


def connect():
    os.makedirs(os.path.dirname(DB), exist_ok=True)
    db = sqlite3.connect(DB, timeout=30)
    db.row_factory = sqlite3.Row
    db.executescript(SCHEMA)
    return db


def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ---------- metadata ----------

def _ratio(v):
    try:
        return float(v)
    except Exception:
        return float(v[0]) / float(v[1]) if isinstance(v, tuple) and v[1] else 0.0


def photo_meta(path):
    from PIL import Image
    try:
        from pillow_heif import register_heif_opener
        register_heif_opener()
    except ImportError:
        pass
    out = {}
    with Image.open(path) as im:
        ex = im.getexif()
        sub = ex.get_ifd(0x8769)
        dt = sub.get(0x9003) or sub.get(0x9004) or ex.get(0x0132)
        if dt:
            try:
                out["taken"] = datetime.strptime(str(dt).strip()[:19], "%Y:%m:%d %H:%M:%S").strftime("%Y-%m-%d %H:%M")
            except ValueError:
                pass
        make, model = str(ex.get(0x010F) or "").strip(" \x00"), str(ex.get(0x0110) or "").strip(" \x00")
        if model:
            out["camera"] = model if make.split(" ")[0].lower() in model.lower() else f"{make} {model}".strip()
        if sub.get(0xA434):
            out["lens"] = str(sub.get(0xA434)).strip(" \x00")
        gps = ex.get_ifd(0x8825)
        if gps.get(2) and gps.get(4):
            dms = lambda v: _ratio(v[0]) + _ratio(v[1]) / 60 + _ratio(v[2]) / 3600
            lat, lon = dms(gps[2]), dms(gps[4])
            if str(gps.get(1, "N")).upper().startswith("S"):
                lat = -lat
            if str(gps.get(3, "E")).upper().startswith("W"):
                lon = -lon
            if lat or lon:
                out["lat"], out["lon"] = round(lat, 6), round(lon, 6)
        software = str(ex.get(0x0131) or "")
        out["_has_camera"] = bool(make or model or sub.get(0x829A))  # exposure time = a real camera
        out["_software"] = software
    return out


def video_meta(path):
    import json
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration:format_tags:stream=width,height:stream_tags",
                        "-of", "json", path], capture_output=True, text=True)
    j = json.loads(r.stdout or "{}")
    tags = {k.lower(): v for k, v in (j.get("format", {}).get("tags") or {}).items()}
    for s in j.get("streams", []):
        for k, v in (s.get("tags") or {}).items():
            tags.setdefault(k.lower(), v)
    out = {"duration": float(j.get("format", {}).get("duration") or 0)}
    ct = tags.get("com.apple.quicktime.creationdate") or tags.get("creation_time")
    if ct:
        try:
            d = datetime.fromisoformat(ct.replace("Z", "+00:00"))
            out["taken"] = (d.astimezone() if d.tzinfo else d).strftime("%Y-%m-%d %H:%M")
        except ValueError:
            pass
    model = tags.get("com.apple.quicktime.model") or tags.get("model") or tags.get("com.android.model")
    make = tags.get("com.apple.quicktime.make") or tags.get("make") or tags.get("com.android.manufacturer")
    if model:
        out["camera"] = model if make and make.lower() in model.lower() else f"{make or ''} {model}".strip()
    loc = tags.get("com.apple.quicktime.location.iso6709") or tags.get("location")
    m = re.match(r"([+-]\d+\.\d+)([+-]\d+\.\d+)", loc or "")
    if m:
        out["lat"], out["lon"] = float(m.group(1)), float(m.group(2))
    return out


def doc_text(path, ext):
    try:
        if ext == ".pdf":
            from pypdf import PdfReader
            r = PdfReader(path)
            text = "\n".join((p.extract_text() or "") for p in r.pages[:20])
            if len(text.strip()) < 20:  # a scanned PDF: read the first pages as pictures
                import pypdfium2 as pdfium
                from vision import read_text
                import cv2
                pdf = pdfium.PdfDocument(path)
                parts = []
                for i in range(min(3, len(pdf))):
                    im = np.asarray(pdf[i].render(scale=2).to_pil().convert("RGB"))
                    parts.append(read_text(cv2.cvtColor(im, cv2.COLOR_RGB2BGR)))
                pdf.close()
                text = "\n".join(parts)
            return text
        if ext == ".docx":
            import docx
            d = docx.Document(path)
            return "\n".join([p.text for p in d.paragraphs] + [c.text for t in d.tables for row in t.rows for c in row.cells])
        if ext in (".xlsx",):
            import openpyxl
            wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
            rows = []
            for ws in wb.worksheets[:5]:
                for row in ws.iter_rows(max_row=300, values_only=True):
                    rows.append(" ".join(str(v) for v in row if v is not None))
            return "\n".join(rows)
        if ext in (".pptx", ".odt", ".ods"):
            import zipfile
            with zipfile.ZipFile(path) as z:
                xml = " ".join(z.read(n).decode("utf8", "ignore") for n in z.namelist()
                               if n.endswith(".xml") and ("slide" in n or n == "content.xml"))
            return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", xml))
        if ext in (".txt", ".md", ".csv", ".rtf"):
            with open(path, errors="ignore") as f:
                return f.read(200_000)
    except Exception as e:
        return f"[could not read: {str(e)[:80]}]"
    return ""


# ---------- one file (runs in a worker process) ----------

SCREEN_SIZES = {(1170, 2532), (1179, 2556), (1284, 2778), (1290, 2796), (1125, 2436), (1242, 2688), (828, 1792),
                (750, 1334), (1080, 1920), (1080, 2400), (1080, 2340), (1080, 2316), (1440, 3200), (1440, 3120),
                (1920, 1080), (2560, 1440), (1366, 768), (1440, 900), (2880, 1800), (3024, 1964), (2560, 1600),
                (1280, 800), (1536, 864), (3840, 2160), (720, 1600), (1080, 2408), (1220, 2712), (1260, 2800)}
DOCLIKE = {"menu", "web site", "envelope", "book jacket", "comic book", "crossword puzzle", "monitor", "screen",
           "notebook", "binder", "packet", "carton", "scoreboard", "street sign", "slide rule", "desktop computer"}


def is_screenshot(rec, meta):
    name = rec["name"].lower()
    if "screenshot" in name or "screen shot" in name or name.startswith(("scr_", "screenrecord")):
        return True
    if meta.get("_has_camera"):
        return False
    w, h = rec.get("w") or 0, rec.get("h") or 0
    return rec["ext"] == ".png" or (w, h) in SCREEN_SIZES or (h, w) in SCREEN_SIZES


def video_frames(path, duration, folder):
    """Up to 16 frames, one every few seconds."""
    if not duration:
        duration = 1
    n = int(min(16, max(1, duration // 3)))
    times = [duration * (i + 0.5) / n for i in range(n)]
    out = []
    for i, t in enumerate(times):
        f = os.path.join(folder, f"{i}.jpg")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.2f}", "-i", path, "-frames:v", "1",
                        "-vf", "scale='min(1280,iw)':-2", f], capture_output=True)
        if os.path.exists(f):
            out.append((t, f))
    return out


def work(rec):
    """Everything for one file. Returns a row for `files` and a list of faces (with face pictures as JPEG bytes)."""
    import cv2
    import textinfo, vision
    row = {"sha256": rec["sha256"], "name": rec["name"], "ext": rec["ext"], "kind": rec["kind"], "bytes": rec["bytes"],
           "width": rec.get("w"), "height": rec.get("h"), "duration": rec.get("duration")}
    faces = []
    try:
        if rec.get("taken"):
            row["taken"] = datetime.fromtimestamp(rec["taken"]).strftime("%Y-%m-%d %H:%M")
        if rec.get("geo"):
            row["lat"], row["lon"] = rec["geo"]
        m = re.search(r"(20\d\d|19\d\d)[-_]?([01]\d)[-_]?([0-3]\d)(?:[-_ ]?([0-2]\d)[-_.]?([0-5]\d)[-_.]?([0-5]\d))?", rec["name"])
        if m and 1 <= int(m.group(2)) <= 12 and 1 <= int(m.group(3)) <= 31:  # Screenshot_20240315-104210, IMG-20240315-WA0001
            row["filename_date"] = f"{m.group(1)}-{m.group(2)}-{m.group(3)}" + (f" {m.group(4)}:{m.group(5)}" if m.group(4) else "")
        text = ""
        if rec["kind"] == "photo":
            meta = photo_meta(rec["path"])
            img = vision.load(rec["path"])
            shot = is_screenshot(rec, meta)
            found = vision.faces(img)
            tags = vision.tags(img)
            names = [t[1] for t in tags]
            if shot or (not found and DOCLIKE & set(names)):
                text = vision.read_text(img)
            for f in found:
                f["thumb"] = cv2.imencode(".jpg", vision.face_thumb(img, f["box"]), [cv2.IMWRITE_JPEG_QUALITY, 85])[1].tobytes()
                f["img_w"], f["img_h"] = img.shape[1], img.shape[0]
                f["frame_s"] = None
            faces = found
            row.update({k: v for k, v in meta.items() if not k.startswith("_") and v and not row.get(k)})
            row["is_screenshot"] = int(shot)
            row["tags"] = ", ".join(names)
            if shot:
                row["content"] = textinfo.screen_type(text)
            elif text.strip():
                row["content"] = "Photo of a document" if len(text) > 80 else ""
        elif rec["kind"] == "video":
            meta = video_meta(rec["path"])
            row.update({k: v for k, v in meta.items() if v and not row.get(k)})
            with tempfile.TemporaryDirectory() as tmp:
                frames = video_frames(rec["path"], meta.get("duration"), tmp)
                best = []  # faces across frames; the same person in many frames is kept once (clearest one)
                tagcount = {}
                for t, f in frames:
                    img = cv2.imread(f)
                    if img is None:
                        continue
                    for tg in vision.tags(img, top=2, min_p=0.15):
                        tagcount[tg[1]] = tagcount.get(tg[1], 0) + 1
                    for fc in vision.faces(img, min_size=40):
                        same = next((b for b in best if vision.same_person(b["embedding"], fc["embedding"]) > 0.5), None)
                        if same and same["score"] * same["box"][2] >= fc["score"] * fc["box"][2]:
                            continue
                        if same:
                            best.remove(same)
                        fc["thumb"] = cv2.imencode(".jpg", vision.face_thumb(img, fc["box"]), [cv2.IMWRITE_JPEG_QUALITY, 85])[1].tobytes()
                        fc["img_w"], fc["img_h"], fc["frame_s"] = img.shape[1], img.shape[0], round(t, 1)
                        best.append(fc)
                faces = best
                row["tags"] = ", ".join(k for k, _ in sorted(tagcount.items(), key=lambda kv: -kv[1])[:5])
        else:
            text = doc_text(rec["path"], rec["ext"])
            row["content"] = textinfo.doc_type(text)
        if text:
            comp = textinfo.companies(text + "\n" + rec["name"])
            if comp:
                row["company"] = ", ".join(c for c, _ in comp[:3])
                row["sector"] = comp[0][1]
            money = textinfo.money(text)
            if money["main"] and (row.get("content") in ("Payment", "Order / shopping", "Ticket / booking", "Bill / invoice",
                                                          "Bank statement", "Salary slip", "Insurance", "Tax") or row.get("sector") in ("Bank", "Payments")):
                row["currency"], row["amount"] = money["main"]
                row["direction"] = money["direction"]
            row["txn_ids"] = "; ".join(money["txn_ids"])
            row["text"] = text[:20000]
    except Exception as e:
        row["error"] = str(e)[:200]
    if not row.get("taken") and row.get("filename_date"):
        row["taken"] = row["filename_date"]
    row["face_count"] = len(faces)
    return row, faces


# ---------- people ----------

class People:
    """Gives each face a person number: the closest known person if similar enough, otherwise a new person."""

    def __init__(self, db):
        import vision
        self.db, self.th = db, vision.SAME_PERSON
        rows = db.execute("SELECT person_id, centroid, n FROM people WHERE centroid IS NOT NULL").fetchall()
        self.ids = [r["person_id"] for r in rows]
        self.n = [r["n"] for r in rows]
        self.c = np.array([np.frombuffer(r["centroid"], np.float32) for r in rows]).reshape(-1, 128)

    def assign(self, emb, taken=()):
        """taken: people already given to another face in the same photo (one person can't be there twice)."""
        if len(self.ids):
            sims = self.c @ emb
            for j, pid in enumerate(self.ids):
                if pid in taken:
                    sims[j] = -1
            i = int(sims.argmax())
            if sims[i] >= self.th:
                c = self.c[i] * self.n[i] + emb
                self.c[i] = c / np.linalg.norm(c)
                self.n[i] += 1
                self.db.execute("UPDATE people SET centroid=?, n=? WHERE person_id=?",
                                (self.c[i].astype(np.float32).tobytes(), self.n[i], self.ids[i]))
                return self.ids[i]
        cur = self.db.execute("INSERT INTO people (centroid, n, created_at) VALUES (?, 1, ?)",
                              (emb.astype(np.float32).tobytes(), now()))
        self.ids.append(cur.lastrowid)
        self.n.append(1)
        self.c = np.vstack([self.c, emb[None]])
        return cur.lastrowid


def save_result(db, people, row, faces):
    cols = ["sha256", "version", "name", "ext", "kind", "bytes", "width", "height", "duration", "taken", "camera", "lens",
            "lat", "lon", "is_screenshot", "tags", "text", "company", "sector", "content", "amount", "currency",
            "direction", "txn_ids", "face_count", "error", "analysed_at"]
    row = dict(row, version=VERSION, analysed_at=now())
    db.execute(f"INSERT OR REPLACE INTO files ({', '.join(cols)}) VALUES ({', '.join('?' * len(cols))})",
               [row.get(c) for c in cols])
    db.execute("DELETE FROM faces WHERE sha256=?", (row["sha256"],))
    taken = set()
    for f in sorted(faces, key=lambda f: -f["box"][2] * f["score"]):  # clearest faces choose first
        pid = people.assign(f["embedding"], taken)
        taken.add(pid)
        cur = db.execute("""INSERT INTO faces (sha256, frame_s, x, y, w, h, img_w, img_h, score, embedding, age, age_years,
                            gender, gender_conf, emotion, emotion_conf, person_id) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                         (row["sha256"], f["frame_s"], *f["box"], f["img_w"], f["img_h"], f["score"], f["embedding"].tobytes(),
                          f["age"], f["age_years"], f["gender"], f["gender_conf"], f["emotion"], f["emotion_conf"], pid))
        with open(os.path.join(FACES_DIR, f"{cur.lastrowid}.jpg"), "wb") as out:
            out.write(f["thumb"])


def main():
    inv = load(os.path.join(DATA, "inventory.json"), [])
    if not inv:
        sys.exit("Scan a folder first.")
    os.makedirs(FACES_DIR, exist_ok=True)
    db = connect()
    if "--again" in sys.argv:
        db.execute("DELETE FROM files")
    done = {r[0] for r in db.execute("SELECT sha256 FROM files WHERE version=?", (VERSION,))}
    todo, seen = [], set()
    for r in inv:
        if r["sha256"] not in done and r["sha256"] not in seen and "error" not in r:
            todo.append(r)
            seen.add(r["sha256"])  # identical copies are looked at once
    print(f"Looking inside {len(todo)} files" + (f" ({len(done)} done before)" if done else "") + "...", flush=True)
    if not todo:
        print("PROGRESS 1 1", flush=True)
        return
    from models import ensure
    ensure()
    people = People(db)
    workers = max(1, min(4, (os.cpu_count() or 2) // 2))
    t0 = time.time()
    with ProcessPoolExecutor(workers) as ex:
        for n, (row, faces) in enumerate(ex.map(work, todo, chunksize=2), 1):
            save_result(db, people, row, faces)
            if n % 10 == 0 or n == len(todo):
                db.commit()
                print(f"PROGRESS {n} {len(todo)}", flush=True)
            if n % 100 == 0:
                print(f"  {n}/{len(todo)}  ({(time.time() - t0) / n:.1f}s per file)", flush=True)
    db.commit()
    f, p = db.execute("SELECT COUNT(*) FROM faces").fetchone()[0], db.execute("SELECT COUNT(*) FROM people").fetchone()[0]
    print(f"Done in {time.time() - t0:.0f}s: {f} faces of {p} different people so far.", flush=True)


if __name__ == "__main__":
    main()
