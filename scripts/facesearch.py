"""Search by face, a simple live-selfie check, and the impersonation check for sign-ups.

Every face in the library is stored as a face code: 128 numbers (SFace). Two codes of the same person
are close (similarity near 1), different people are far apart. Searching = comparing one code with all.

  search(image)            -> people whose faces match, best first
  liveness(frames)         -> did the selfie come from a live person turning their head (basic check)
  enroll_check(code, mob)  -> new / already this number / matches someone not yet registered /
                              CONFLICT: the face belongs to a profile registered to another number
Face matching makes mistakes (twins, siblings, children): access is never given on a face alone.
"""
import base64, os, sys

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
import vision
from analyze import connect

STRONG = 0.55    # same person, for giving access (stricter than grouping photos)
POSSIBLE = 0.42  # probably the same person, shown as "possible"


def decode(data_url, max_side=1280):
    """A data: URL or base64 JPEG/PNG from the browser -> OpenCV image."""
    raw = base64.b64decode(data_url.split(",", 1)[-1])
    if len(raw) > 12_000_000:
        raise ValueError("That picture is too big. Use one under 12 MB.")
    img = cv2.imdecode(np.frombuffer(raw, np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("That file isn't a picture we can read. Use a JPG or PNG.")
    h, w = img.shape[:2]
    if max(h, w) > max_side:
        s = max_side / max(h, w)
        img = cv2.resize(img, (int(w * s), int(h * s)))
    return img


def main_face(img):
    fs = vision.faces(img, min_size=40)
    if not fs:
        raise ValueError("No face found. Use a clear, front-facing photo with good light.")
    f = max(fs, key=lambda x: x["box"][2] * x["box"][3])
    thumb = cv2.imencode(".jpg", vision.face_thumb(img, f["box"]), [cv2.IMWRITE_JPEG_QUALITY, 85])[1].tobytes()
    return f, thumb, len(fs)


def _all_faces(db):
    rows = db.execute("SELECT face_id, person_id, embedding FROM faces WHERE embedding IS NOT NULL").fetchall()
    if not rows:
        return [], np.zeros((0, 128), np.float32)
    return rows, np.stack([np.frombuffer(r["embedding"], np.float32) for r in rows])


def search(data_url, limit=12):
    img = decode(data_url)
    f, thumb, n = main_face(img)
    db = connect()
    rows, E = _all_faces(db)
    people = {}
    if len(rows):
        sims = E @ f["embedding"]
        for r, s in zip(rows, sims):
            if s < POSSIBLE:
                continue
            p = people.setdefault(r["person_id"], {"person_id": r["person_id"], "score": 0.0, "face_ids": []})
            p["score"] = max(p["score"], float(s))
            p["face_ids"].append(r["face_id"])
    out = sorted(people.values(), key=lambda p: -p["score"])[:limit]
    for p in out:
        p["level"] = "strong" if p["score"] >= STRONG else "possible"
        p["score"] = round(p["score"], 3)
    return {"query": "data:image/jpeg;base64," + base64.b64encode(thumb).decode(), "faces_in_picture": n,
            "estimate": {k: f[k] for k in ("age", "gender", "emotion")}, "people": out}


TURN = 0.12  # how far the nose must move sideways, in eye-widths, for a head turn to count


def liveness(frames, steps=("straight", "left", "right")):
    """Live-selfie check from 3 frames: looking straight, then turning the head the way the server asked,
    in a random order (so a recording made earlier won't match). One face in each, the same person in all,
    and each turn really goes the asked way (from the eyes and nose). It stops photos and most replayed
    videos; it does NOT stop a mask or a deepfake. Always pair it with the SMS code and owner review."""
    if len(frames) < 3:
        raise ValueError("We need three pictures: straight, then the two head turns.")
    found = []
    for d in frames[:3]:
        img = decode(d, 960)
        fs = vision.faces(img, min_size=60)
        if len(fs) != 1:
            raise ValueError("Make sure only your face is in the circle, close to the camera, in good light." if fs
                             else "We couldn't see your face. Move closer and face the light.")
        found.append((fs[0], img.shape[1]))
    a, b, c = (x[0] for x in found)
    same = min(float(a["embedding"] @ b["embedding"]), float(a["embedding"] @ c["embedding"]))
    if same < 0.45:
        raise ValueError("The pictures don't look like the same person. Try again, slowly.")
    base = a["yaw"]
    for f, want in zip((b, c), steps[1:3]):
        d = f["yaw"] - base
        if (want == "left" and d < TURN) or (want == "right" and d > -TURN):
            raise ValueError(f"We didn't see your head turn to your {want}. Turn it a little more, slowly, when asked.")
    best = max((x[0] for x in found), key=lambda f: f["score"] * f["box"][2])
    img = decode(frames[[x[0] for x in found].index(best)], 960)
    thumb = cv2.imencode(".jpg", vision.face_thumb(img, best["box"]), [cv2.IMWRITE_JPEG_QUALITY, 85])[1].tobytes()
    return best["embedding"], thumb


def enroll_check(code, mobile):
    """Who does this face belong to? -> (status, person_id, score)
    status: none | same (this number's own profile) | match (someone not registered yet: owner confirms)
            | conflict (registered to ANOTHER number: blocked and reported)"""
    db = connect()
    rows, E = _all_faces(db)
    if not len(rows):
        return "none", None, 0.0
    sims = E @ code
    best = {}
    for r, s in zip(rows, sims):
        if s >= best.get(r["person_id"], -1):
            best[r["person_id"]] = float(s)
    pid, score = max(best.items(), key=lambda kv: kv[1])
    if score < STRONG:
        return "none", None, round(score, 3)
    p = db.execute("SELECT mobile, mobile_verified FROM people WHERE person_id=?", (pid,)).fetchone()
    if p and p["mobile"] and p["mobile_verified"]:
        return ("same" if p["mobile"] == mobile else "conflict"), pid, round(score, 3)
    return "match", pid, round(score, 3)
