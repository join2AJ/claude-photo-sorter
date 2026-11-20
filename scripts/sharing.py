"""The sharing app (share.html): people see the photos they're in, with other faces blurred unless
those people agreed.

  1. mobile number -> 6-digit code (TEST MODE: no SMS service yet, the code is shown on screen and in the log)
  2. live selfie (3 pictures while turning the head) -> face code -> enroll_check
       same     : this number's own profile -> in
       match    : the face is someone in the photos not registered yet -> the album owner confirms (Details > Requests)
       conflict : the face belongs to a profile registered to ANOTHER number -> blocked, owner alerted
       none     : not found in any photo
  3. their choice: show my face to others in my photos, or blur it (and show to / hide from specific people)
  4. their photos, made on the server for each viewer: a face is clear only if it is the viewer's own,
     or that person said yes (and didn't hide it from this viewer). Unregistered faces are always blurred.
Nothing unblurred ever leaves the server for another person's face.
"""
import hashlib, hmac, io, os, re, secrets, sys, time

sys.path.insert(0, os.path.dirname(__file__))
import facesearch
from analyze import connect
from common import DATA, load

TEST_MODE = not os.environ.get("SMS_PROVIDER")  # set when a real SMS service is connected (part 2 on a server)
CODE_TTL, SESSION_TTL = 300, 30 * 24 * 3600


def _h(s):
    return hashlib.sha256(s.encode()).hexdigest()


def now():
    return time.strftime("%Y-%m-%d %H:%M:%S")


def mask(m):
    return m[:3] + " ••••• " + m[-3:] if m and len(m) > 6 else m


def norm_mobile(m):
    m = re.sub(r"[\s\-()]", "", m or "")
    if re.fullmatch(r"\d{10}", m):
        m = "+91" + m  # a 10-digit number: India
    if not re.fullmatch(r"\+\d{10,15}", m):
        raise ValueError("Enter your mobile number with the country code, like +91 98765 43210.")
    return m


# ---------- 1. mobile + code ----------

def send_code(mobile):
    mobile = norm_mobile(mobile)
    db = connect()
    row = db.execute("SELECT sent FROM otps WHERE mobile=?", (mobile,)).fetchone()
    if row and row["sent"] and time.time() - row["sent"] < 30:
        raise ValueError("A code was just sent. Wait 30 seconds before asking again.")
    code = f"{secrets.randbelow(10 ** 6):06d}"
    db.execute("INSERT OR REPLACE INTO otps (mobile, code_hash, expires, tries, sent) VALUES (?,?,?,0,?)",
               (mobile, _h(mobile + code), time.time() + CODE_TTL, time.time()))
    db.commit()
    if TEST_MODE:
        print(f"[test mode] code for {mask(mobile)}: {code}", flush=True)
        return {"mobile": mobile, "test_code": code}
    raise RuntimeError("No SMS service is connected yet.")


def verify_code(mobile, code):
    mobile = norm_mobile(mobile)
    db = connect()
    row = db.execute("SELECT * FROM otps WHERE mobile=?", (mobile,)).fetchone()
    if not row or row["expires"] < time.time():
        raise ValueError("That code has expired. Ask for a new one.")
    if row["tries"] >= 5:
        raise ValueError("Too many wrong codes. Ask for a new one.")
    if not hmac.compare_digest(row["code_hash"], _h(mobile + re.sub(r"\D", "", code or ""))):
        db.execute("UPDATE otps SET tries=tries+1 WHERE mobile=?", (mobile,))
        db.commit()
        raise ValueError("That code isn't right. Check the message and try again.")
    db.execute("DELETE FROM otps WHERE mobile=?", (mobile,))
    token = secrets.token_urlsafe(32)
    p = db.execute("SELECT person_id FROM people WHERE mobile=? AND mobile_verified=1", (mobile,)).fetchone()
    db.execute("INSERT INTO guest_sessions (token_hash, mobile, stage, person_id, created, expires) VALUES (?,?,?,?,?,?)",
               (_h(token), mobile, "approved" if p else "verified", p["person_id"] if p else None, time.time(), time.time() + SESSION_TTL))
    db.commit()
    return token


def session(token):
    if not token:
        return None
    db = connect()
    s = db.execute("SELECT * FROM guest_sessions WHERE token_hash=?", (_h(token),)).fetchone()
    if not s or s["expires"] < time.time():
        return None
    s = dict(s)
    if s["stage"] in ("pending", "verified") and s["enrollment_id"]:  # the owner may have decided meanwhile
        e = db.execute("SELECT status, person_id FROM enrollments WHERE id=?", (s["enrollment_id"],)).fetchone()
        if e and e["status"] in ("approved", "denied"):
            s["stage"], s["person_id"] = e["status"], e["person_id"] if e["status"] == "approved" else None
            db.execute("UPDATE guest_sessions SET stage=?, person_id=? WHERE token_hash=?", (s["stage"], s["person_id"], _h(token)))
            db.commit()
    return s


def logout(token):
    db = connect()
    db.execute("DELETE FROM guest_sessions WHERE token_hash=?", (_h(token or ""),))
    db.commit()


# ---------- 2. live selfie ----------

def selfie(token, frames):
    s = session(token)
    if not s or s["stage"] not in ("verified", "notfound", "denied"):
        raise PermissionError("Verify your mobile number first.")
    code, thumb = facesearch.liveness(frames)
    status, pid, score = facesearch.enroll_check(code, s["mobile"])
    db = connect()
    st = {"conflict": "blocked", "same": "approved", "match": "pending", "none": "notfound"}[status]
    cur = db.execute("INSERT INTO enrollments (mobile, embedding, selfie, status, person_id, score, at) VALUES (?,?,?,?,?,?,?)",
                     (s["mobile"], code.astype("float32").tobytes(), thumb,
                      {"blocked": "conflict", "approved": "approved", "pending": "pending", "notfound": "none"}[st], pid, score, now()))
    if status == "conflict":
        db.execute("INSERT INTO alerts (kind, person_id, mobile, detail, at) VALUES (?,?,?,?,?)",
                   ("impersonation", pid, s["mobile"], f"Someone with {mask(s['mobile'])} tried to sign up with the face of P{pid:04d}, "
                    f"which is registered to another number (match {score:.0%}). They were blocked.", now()))
        db.execute("INSERT INTO consent_log (person_id, action, detail, at) VALUES (?,?,?,?)",
                   (pid, "impersonation blocked", mask(s["mobile"]), now()))
    db.execute("UPDATE guest_sessions SET stage=?, enrollment_id=?, person_id=? WHERE token_hash=?",
               (st, cur.lastrowid, pid if st == "approved" else None, _h(token)))
    db.commit()
    return st


# ---------- owner decisions (Details > Requests) ----------

def decide(enrollment_id, action, person_id=None):
    db = connect()
    e = db.execute("SELECT * FROM enrollments WHERE id=?", (enrollment_id,)).fetchone()
    if not e:
        raise ValueError("That request no longer exists.")
    if action == "deny":
        db.execute("UPDATE enrollments SET status='denied', decided_at=? WHERE id=?", (now(), enrollment_id))
    else:
        pid = int(person_id or e["person_id"] or 0)
        p = db.execute("SELECT * FROM people WHERE person_id=?", (pid,)).fetchone()
        if not p:
            raise ValueError("Pick which person this is.")
        if p["mobile"] and p["mobile_verified"] and p["mobile"] != e["mobile"]:
            raise ValueError("That person is already registered to another number.")
        db.execute("UPDATE people SET mobile=?, mobile_verified=1 WHERE person_id=?", (e["mobile"], pid))
        db.execute("UPDATE enrollments SET status='approved', person_id=?, decided_at=? WHERE id=?", (pid, now(), enrollment_id))
        db.execute("INSERT INTO consent_log (person_id, action, detail, at) VALUES (?,?,?,?)",
                   (pid, "registered", f"{mask(e['mobile'])}, approved by the owner", now()))
    db.commit()


def requests_and_alerts():
    import base64
    db = connect()
    reqs = [dict(r, embedding=None, selfie="data:image/jpeg;base64," + base64.b64encode(r["selfie"]).decode() if r["selfie"] else None)
            for r in db.execute("SELECT * FROM enrollments ORDER BY id DESC LIMIT 200")]
    for r in reqs:
        r.pop("embedding")
    alerts = [dict(r) for r in db.execute("SELECT * FROM alerts ORDER BY id DESC LIMIT 200")]
    return reqs, alerts


# ---------- 3. their choice ----------

def set_consent(token, b):
    s = _approved(token)
    db = connect()
    pid = s["person_id"]
    cur = db.execute("SELECT consent FROM people WHERE person_id=?", (pid,)).fetchone()
    consent = b.get("consent")
    if consent not in ("yes", "no"):
        raise ValueError("Choose to show or to blur your face.")
    ids = lambda k: ",".join(str(int(x)) for x in b.get(k, []) if str(x).isdigit() and int(x) != pid)
    db.execute("UPDATE people SET consent=?, consent_at=?, share_with=?, hide_from=? WHERE person_id=?",
               (consent, now(), ids("share_with"), ids("hide_from"), pid))
    if cur["consent"] != consent:
        db.execute("INSERT INTO consent_log (person_id, action, detail, at) VALUES (?,?,?,?)",
                   (pid, "consent " + consent, "set by the person in the sharing app", now()))
    db.commit()


def forget_me(token):
    s = _approved(token)
    db = connect()
    db.execute("UPDATE people SET consent='no', consent_at=? WHERE person_id=?", (now(), s["person_id"]))
    db.execute("INSERT INTO alerts (kind, person_id, mobile, detail, at) VALUES (?,?,?,?,?)",
               ("delete request", s["person_id"], s["mobile"], f"P{s['person_id']:04d} asked to have their face data deleted. "
                "Their face is blurred for everyone until you delete it.", now()))
    db.execute("INSERT INTO consent_log (person_id, action, detail, at) VALUES (?,?,?,?)", (s["person_id"], "asked to be deleted", "", now()))
    db.commit()


# ---------- 4. their photos ----------

def _approved(token):
    s = session(token)
    if not s or s["stage"] != "approved" or not s["person_id"]:
        raise PermissionError("Sign in first.")
    return s


def visible(viewer, face_person, people):
    """Is face_person's face shown clearly to viewer?"""
    if face_person == viewer:
        return True
    p = people.get(face_person)
    if not p or not p.get("mobile_verified") or p.get("consent") != "yes":
        return False  # not registered, not asked, or said no: blurred
    hide = {int(x) for x in (p.get("hide_from") or "").split(",") if x}
    share = {int(x) for x in (p.get("share_with") or "").split(",") if x}
    return viewer not in hide and (not share or viewer in share)


def _people(db):
    return {r["person_id"]: dict(r) for r in db.execute(
        "SELECT person_id, name, mobile_verified, consent, share_with, hide_from FROM people")}


def me(token):
    s = session(token)
    if not s:
        return {"stage": "signed-out"}
    out = {"stage": s["stage"], "mobile": mask(s["mobile"]), "test_mode": TEST_MODE}
    if s["stage"] != "approved":
        return out
    import details
    L = details.library()
    pid = s["person_id"]
    db = connect()
    people = _people(db)
    p = L["people"].get(pid, {})
    face_by_id = {f["face_id"]: f for f in L["faces"]}
    photos, others = [], {}
    for f in L["files"]:
        if pid not in f["people_ids"] or f.get("duplicate_of"):
            continue
        fs = [face_by_id[i] for i in f["face_ids"] if i in face_by_id]
        hidden = sum(1 for x in fs if not visible(pid, x["person_id"], people))
        if f["kind"] == "video" and hidden:
            continue  # videos can't be blurred yet: only shown when every face in them is shared
        photos.append({"id": f["id"], "kind": f["kind"], "taken": f["taken"], "faces": len(fs), "blurred": hidden,
                       "labels": [t for t in f.get("labels", []) if not people.get(t)], "w": f["width"], "h": f["height"]})
        for x in fs:
            q = people.get(x["person_id"])
            if x["person_id"] != pid and q and q["mobile_verified"] and q["name"]:
                others[x["person_id"]] = q["name"]
    photos.sort(key=lambda x: x["taken"] or "", reverse=True)
    out.update(person={"id": pid, "name": p.get("display"), "consent": people.get(pid, {}).get("consent"),
                       "share_with": people.get(pid, {}).get("share_with") or "", "hide_from": people.get(pid, {}).get("hide_from") or ""},
               photos=photos, others=[{"id": k, "name": v} for k, v in sorted(others.items(), key=lambda kv: kv[1])])
    return out


def photo(token, file_id, size=1600):
    """One photo for this viewer, with every face they may not see blurred (made fresh, never cached unblurred)."""
    from PIL import Image, ImageFilter, ImageOps
    s = _approved(token)
    pid = s["person_id"]
    inv = {r["id"]: r for r in load(os.path.join(DATA, "inventory.json"), [])}
    rec = inv.get(int(file_id))
    db = connect()
    faces = [dict(r) for r in db.execute("SELECT person_id, x, y, w, h, img_w, img_h, frame_s FROM faces WHERE sha256=?", (rec["sha256"],))] if rec else []
    if not rec or pid not in {f["person_id"] for f in faces}:
        raise PermissionError("You can only see photos you're in.")
    people = _people(db)
    if rec["kind"] == "video":
        im = Image.open(os.path.join(DATA, "thumbs", f"{rec['id']}.jpg"))
        if any(not visible(pid, f["person_id"], people) for f in faces):
            raise PermissionError("This video has faces that aren't shared.")
    else:
        try:
            from pillow_heif import register_heif_opener
            register_heif_opener()
        except ImportError:
            pass
        im = ImageOps.exif_transpose(Image.open(rec["path"])).convert("RGB")
        im.thumbnail((1600, 1600))  # blur at full detail first, shrink afterwards
        # Look for faces again (small background faces too). A face stays clear only if it is clearly one of
        # the recorded faces this viewer may see; every other face is blurred.
        import cv2, numpy as np, vision
        arr = cv2.cvtColor(np.asarray(im), cv2.COLOR_RGB2BGR)
        shown = []
        for f in faces:
            if f["frame_s"] is None and visible(pid, f["person_id"], people):
                sx, sy = im.width / f["img_w"], im.height / f["img_h"]
                shown.append((f["x"] * sx, f["y"] * sy, f["w"] * sx, f["h"] * sy))
        def overlap(a, b):
            ix = max(0, min(a[0] + a[2], b[0] + b[2]) - max(a[0], b[0]))
            iy = max(0, min(a[1] + a[3], b[1] + b[3]) - max(a[1], b[1]))
            return ix * iy / max(1, min(a[2] * a[3], b[2] * b[3]))
        hidden = []
        for f in faces:  # every recorded face this viewer may not see: always blurred
            if f["frame_s"] is None and not visible(pid, f["person_id"], people):
                sx, sy = im.width / f["img_w"], im.height / f["img_h"]
                hidden.append((int(f["x"] * sx), int(f["y"] * sy), int(f["w"] * sx), int(f["h"] * sy)))
        for b in vision.detect_boxes(arr):  # plus any face found now that isn't clearly a shared one
            if not any(overlap(b, s) > 0.5 for s in shown):
                hidden.append(tuple(b))
        for x, y, w, h in hidden:
            m = 0.3
            box = (int(max(0, x - w * m)), int(max(0, y - h * m)), int(min(im.width, x + w * (1 + m))), int(min(im.height, y + h * (1 + m))))
            region = im.crop(box)
            small = region.resize((max(1, region.width // 12), max(1, region.height // 12)))  # pixelate, then blur: nothing to undo
            im.paste(small.resize(region.size).filter(ImageFilter.GaussianBlur(max(4, region.width // 10))), box)
    im.thumbnail((size, size))
    buf = io.BytesIO()
    im.convert("RGB").save(buf, "JPEG", quality=86)
    return buf.getvalue()
