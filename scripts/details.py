"""One place that joins everything known about the library: the files, their folders, faces and people.
Used by the Excel export and the Details page."""
import csv, os, sqlite3, sys
from collections import Counter

sys.path.insert(0, os.path.dirname(__file__))
from common import CATEGORIES, DATA, DB, load
import tags, vault
from datetime import datetime

NO_FACE = "un"


def person_name(p):
    return p["name"] or f"Person {p['person_id']}"


def pid(n):
    return f"P{n:04d}"


def fid(n):
    return f"F{n:05d}"


def connect():
    if not os.path.exists(DB):
        return None
    from analyze import connect as open_db  # also adds columns that older libraries don't have yet
    db = open_db()
    return db


def library():
    """Everything, as plain dicts: files (one per inventory entry), faces, people, folders."""
    inv = load(os.path.join(DATA, "inventory.json"), [])
    labels = load(os.path.join(DATA, "labels.json"), {})
    cats = {c["key"]: c for c in load(CATEGORIES, [])}
    dupes = load(os.path.join(DATA, "dupes.json"), [])
    src = load(os.path.join(DATA, "source.json"), {})
    dupe_of = {d: g["keep"] for g in dupes for d in g["dupes"]}
    copies = {}
    if src.get("sorted") and os.path.exists(os.path.join(src["sorted"], "sorted.csv")):
        with open(os.path.join(src["sorted"], "sorted.csv")) as f:
            for row in csv.DictReader(f):
                copies[row["original_path"]] = os.path.join(src["sorted"], row["file"])
    db = connect()
    info, faces, people, overrides = {}, [], {}, {}
    if db:
        info = {r["sha256"]: dict(r) for r in db.execute("SELECT * FROM files")}
        people = {r["person_id"]: dict(r) for r in db.execute(
            "SELECT person_id, name, mobile, mobile_verified, consent, consent_at, share_with, hide_from, notes, created_at, "
            "family, aliases FROM people")}
        overrides = {r["sha256"]: dict(r) for r in db.execute("SELECT * FROM vault_overrides")}
        faces = [dict(r) for r in db.execute(
            "SELECT face_id, sha256, frame_s, x, y, w, h, img_w, img_h, score, age, age_years, gender, gender_conf, "
            "emotion, emotion_conf, person_id, manual FROM faces ORDER BY face_id")]
    by_sha = {}
    for f in faces:
        by_sha.setdefault(f["sha256"], []).append(f)
    byid = {r["id"]: r for r in inv}
    files = []
    for r in inv:
        i = info.get(r["sha256"], {})
        fs = by_sha.get(r["sha256"], [])
        key = labels.get(str(r["id"]))
        folder = "Duplicates (review)" if r["id"] in dupe_of else (cats[key]["label"] if key in cats else "")
        files.append({
            "id": r["id"], "sha256": r["sha256"], "name": r["name"], "kind": r["kind"], "ext": r["ext"], "path": r["path"], "bytes": r["bytes"],
            "folder": folder, "folder_key": "_dupes" if r["id"] in dupe_of else key,
            "duplicate_of": byid[dupe_of[r["id"]]]["name"] if r["id"] in dupe_of else "",
            "copy": copies.get(r["path"], ""),
            "taken": i.get("taken"), "camera": i.get("camera"), "lens": i.get("lens"),
            "lat": i.get("lat"), "lon": i.get("lon"), "width": r.get("w"), "height": r.get("h"),
            "duration": r.get("duration") or i.get("duration"),
            "screenshot": bool(i.get("is_screenshot")), "tags": i.get("tags") or "", "text": i.get("text") or "",
            "company": i.get("company") or "", "sector": i.get("sector") or "", "content": i.get("content") or "",
            "amount": i.get("amount"), "currency": i.get("currency") or "", "direction": i.get("direction") or "",
            "txn_ids": i.get("txn_ids") or "", "error": r.get("error") or i.get("error") or "",
            "plain_bg": i.get("plain_bg"), "colors": i.get("colors") or "",
            "modified": i.get("taken") or (datetime.fromtimestamp(r["mtime"]).strftime("%Y-%m-%d %H:%M") if r.get("mtime") else None),
            "analysed": bool(i), "face_ids": [f["face_id"] for f in fs],
            "people_ids": sorted({f["person_id"] for f in fs if f["person_id"]}),
        })
    # per-person summaries
    for p in people.values():
        p.update(display=person_name(p), photos=0, videos=0, faces=0, ages=[], genders=Counter(), emotions=Counter(),
                 first=None, last=None, cover=None, _cover_q=-1, files=[])
    file_by_sha = {}
    for f in files:
        file_by_sha.setdefault(f["sha256"], []).append(f)
    for f in faces:
        p = people.get(f["person_id"])
        if not p:
            continue
        p["faces"] += 1
        if f["age_years"] is not None:
            p["ages"].append(f["age_years"])
        if f["gender"]:
            p["genders"][f["gender"]] += 1
        if f["emotion"]:
            p["emotions"][f["emotion"]] += 1
        if f["w"] * (f["score"] or 0) > p["_cover_q"]:
            p["cover"], p["_cover_q"] = f["face_id"], f["w"] * (f["score"] or 0)
        for fl in file_by_sha.get(f["sha256"], []):
            if fl["id"] in p["files"]:
                continue
            p["files"].append(fl["id"])
            p["videos" if fl["kind"] == "video" else "photos"] += 1
            if fl["taken"]:
                p["first"] = min(p["first"] or fl["taken"], fl["taken"])
                p["last"] = max(p["last"] or fl["taken"], fl["taken"])
    for p in people.values():
        p.pop("_cover_q", None)
        p["age_est"] = round(sum(p["ages"]) / len(p["ages"])) if p["ages"] else None
        p["gender_est"] = p["genders"].most_common(1)[0][0] if p["genders"] else ""
        p["emotion_usual"] = p["emotions"].most_common(1)[0][0] if p["emotions"] else ""
        p["emotion_mix"] = ", ".join(f"{k} {v}" for k, v in p["emotions"].most_common(3))
        p.pop("ages"); p.pop("genders"); p.pop("emotions")
    for f in files:
        f["people"] = ", ".join(people[i]["display"] for i in f["people_ids"] if i in people) or NO_FACE
    for f in faces:
        f["file_ids"] = [fl["id"] for fl in file_by_sha.get(f["sha256"], [])]
        f["file"] = file_by_sha.get(f["sha256"], [{}])[0].get("name", "")
        f["person"] = people[f["person_id"]]["display"] if f["person_id"] in people else ""
    face_by_id = {f["face_id"]: f for f in faces}
    for f in files:
        f["labels"] = tags.make_labels(f, [face_by_id[i] for i in f["face_ids"] if i in face_by_id], people)
    vmap = vault.assign(files, face_by_id, people, overrides)
    for f in files:
        f["vault"] = vmap.get(f["id"])
    return {"files": files, "faces": faces, "people": people, "source": src, "categories": list(cats.values())}
