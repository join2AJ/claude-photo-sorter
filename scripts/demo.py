"""Make a fake library so you can see the whole app before using your own photos.
  python scripts/demo.py   ->  dashboard/demo/   (open http://127.0.0.1:8765/?demo)

Everything is drawn: shapes for photos, cartoon faces for people, made-up screenshots, bills
and documents. No real photos, people, phone numbers or payments. Also writes the Details page
data (details.json) and a sample Excel file, so the demo works as a plain website (see build_site.py).
"""
import json, os, random, shutil, sys
from datetime import datetime, timedelta

from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, os.path.dirname(__file__))
from common import CATEGORIES, ROOT, load

OUT = os.path.join(ROOT, "dashboard", "demo")
rnd = random.Random(7)
cats = load(CATEGORIES)
catby = {c["key"]: c for c in cats}
if os.path.isdir(OUT):
    shutil.rmtree(OUT)
for d in ("thumbs", "mini", "faces"):
    os.makedirs(os.path.join(OUT, d))

WEIGHTS = {"selfies": 110, "people": 95, "pets": 40, "food": 60, "travel": 85, "city": 70, "home": 120,
           "docs": 55, "memes": 150, "screenshots": 140, "vtalk": 45, "vtravel": 25, "vscreen": 12, "vclips": 50,
           "dfinance": 26, "dids": 8, "dwork": 18, "dother": 10}


def font(size, bold=False):
    for f in (("/System/Library/Fonts/Helvetica.ttc",), ("DejaVuSans-Bold.ttf",) if bold else ("DejaVuSans.ttf",), ("arial.ttf",)):
        try:
            return ImageFont.truetype(f[0], size)
        except OSError:
            pass
    return ImageFont.load_default()


def jitter(c, n=26):
    return tuple(max(0, min(255, v + rnd.randint(-n, n))) for v in c)


# ---------- the made-up people ----------
SKINS = [(241, 205, 175), (224, 180, 140), (198, 145, 105), (160, 112, 78), (120, 82, 58)]
HAIRS = [(30, 24, 20), (60, 40, 28), (110, 70, 40), (20, 20, 22), (150, 150, 150)]
NAMES = {"female": ["Asha", "Meera", "Priya"], "male": ["Rahul", "Arjun", "Kabir"]}  # made-up names for the demo
people = []
for n in range(1, 41):  # 16 regulars, the rest show up once (strangers in group photos)
    g = rnd.choice(["female", "male"])
    people.append({"person_id": n, "gender": g, "age": rnd.choice([6, 9, 17, 24, 28, 31, 36, 45, 52, 63]),
                   "skin": rnd.choice(SKINS), "hair": rnd.choice(HAIRS), "long": g == "female" and rnd.random() < .8,
                   "glasses": rnd.random() < .25, "shirt": (rnd.randint(40, 220), rnd.randint(40, 200), rnd.randint(40, 220))})
for k, p in enumerate(people[:6]):  # the six named people: three women, three men, all adults
    p.update(gender="female" if k % 2 == 0 else "male", age=rnd.choice([24, 28, 31, 36, 45, 52]))
    p["long"] = p["gender"] == "female"
    p["name"] = NAMES[p["gender"]][k // 2]
FAMILY = {1: "Verma", 2: "Verma", 3: "Verma", 4: "Verma"}  # made-up family: the first four named people
for n, surname in FAMILY.items():
    people[n - 1]["name"] += " " + surname
REGULAR = people[:16]
STRANGERS = people[16:]
EMOTIONS = ["happy"] * 6 + ["neutral"] * 3 + ["surprised", "sad"]


def draw_face(d, cx, cy, r, p, emotion):
    """A cartoon head centred at (cx, cy) with radius r."""
    if p["long"]:
        d.rounded_rectangle((cx - r * 1.1, cy - r * 1.05, cx + r * 1.1, cy + r * 1.25), int(r * .6), fill=p["hair"])
    d.ellipse((cx - r * .9, cy - r, cx + r * .9, cy + r), fill=p["skin"])
    d.pieslice((cx - r * .95, cy - r * 1.12, cx + r * .95, cy + r * .4), 180, 360, fill=p["hair"])
    ey, ex = cy - r * .05, r * .36
    for sx in (-1, 1):
        d.ellipse((cx + sx * ex - r * .1, ey - r * .1, cx + sx * ex + r * .1, ey + r * .1), fill=(30, 25, 25))
        if p["glasses"]:
            d.ellipse((cx + sx * ex - r * .25, ey - r * .22, cx + sx * ex + r * .25, ey + r * .22), outline=(20, 20, 20), width=max(1, int(r * .06)))
    my, mw = cy + r * .45, r * .38
    w = max(1, int(r * .08))
    if emotion == "happy":
        d.arc((cx - mw, my - mw * .8, cx + mw, my + mw * .6), 20, 160, fill=(120, 40, 40), width=w)
    elif emotion == "sad":
        d.arc((cx - mw, my, cx + mw, my + mw * 1.2), 200, 340, fill=(120, 40, 40), width=w)
    elif emotion == "surprised":
        d.ellipse((cx - r * .12, my - r * .12, cx + r * .12, my + r * .16), fill=(110, 40, 40))
    else:
        d.line((cx - mw * .7, my + r * .05, cx + mw * .7, my + r * .05), fill=(120, 40, 40), width=w)


def face_picture(p, emotion, bg, path):
    """A crisp 160px face picture for the People and Faces pages."""
    im = Image.new("RGB", (160, 160), bg)
    d = ImageDraw.Draw(im)
    d.ellipse((10, 118, 150, 230), fill=p["shirt"])
    draw_face(d, 80, 74, 50, p, emotion)
    im.save(path, quality=85)


# ---------- pictures ----------
def paper(ext, title, S=256):
    colors = {".docx": (43, 87, 154), ".xlsx": (33, 115, 70), ".pdf": (180, 40, 40), ".txt": (90, 90, 100), ".pptx": (196, 72, 38)}
    im = Image.new("RGB", (S, S), (236, 233, 226))
    d = ImageDraw.Draw(im)
    d.rectangle((48, 20, 208, 236), fill="white", outline=(200, 196, 188))
    d.text((60, 32), title[:18], fill=(60, 60, 70), font=font(13, True))
    for y in range(66, 140, 14):
        d.line((62, y, 62 + rnd.randint(80, 130), y), fill=(214, 211, 204), width=5)
    d.rounded_rectangle((60, 160, 196, 204), 8, fill=colors.get(ext, (90, 90, 100)))
    d.text((128, 182), ext[1:].upper(), fill="white", font=font(26, True), anchor="mm")
    return im


def screen(lines, dark=False, accent=(52, 120, 246), S=256):
    bg = (24, 24, 28) if dark else (247, 247, 249)
    ink = (225, 225, 232) if dark else (40, 40, 48)
    im = Image.new("RGB", (S, S), bg)
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, S, 30), fill=accent)
    d.text((12, 8), lines[0], fill="white", font=font(13, True))
    y = 44
    for ln in lines[1:]:
        big = ln.startswith("₹")
        d.text((14, y), ln, fill=ink, font=font(22 if big else 12, big))
        y += 34 if big else 20
    return im


def draw(key, faces_out, S=256):
    """A drawn picture for this folder. Fills faces_out with (person, emotion, box) for people pictures."""
    im = Image.new("RGB", (S, S))
    d = ImageDraw.Draw(im)
    r = rnd.randint
    if key == "travel" or key == "vtravel":
        sky = jitter(rnd.choice([(150, 190, 230), (250, 170, 120), (200, 215, 235)]), 15)
        d.rectangle((0, 0, S, S), fill=sky)
        for k in range(3):
            base = jitter((90 - k * 20, 110 - k * 20, 130 - k * 15), 15)
            x = r(-60, 120)
            d.polygon([(x, S), (x + r(80, 140), r(70, 140)), (x + r(220, 300), S)], fill=base)
            if rnd.random() < .6:
                d.polygon([(x + 120, r(70, 100)), (x + 95, 125), (x + 150, 125)], fill=(248, 248, 250))
    elif key == "city":
        d.rectangle((0, 0, S, S), fill=jitter((22, 26, 48), 10))
        x = 0
        while x < S:
            w, h = r(28, 60), r(80, 210)
            d.rectangle((x, S - h, x + w, S), fill=jitter((40, 44, 70), 12))
            for wy in range(S - h + 10, S - 8, 16):
                for wx in range(x + 6, x + w - 6, 12):
                    if rnd.random() < .45:
                        d.rectangle((wx, wy, wx + 5, wy + 7), fill=(250, 214, 120))
            x += w + 4
    elif key == "food":
        d.rectangle((0, 0, S, S), fill=jitter((180, 130, 90), 30))
        d.ellipse((30, 30, S - 30, S - 30), fill=(245, 245, 240))
        for _ in range(7):
            cx, cy, rr = r(80, 176), r(80, 176), r(14, 30)
            d.ellipse((cx - rr, cy - rr, cx + rr, cy + rr), fill=jitter(rnd.choice([(200, 80, 50), (90, 150, 70), (230, 180, 60)]), 25))
    elif key == "pets":
        d.rectangle((0, 0, S, S), fill=jitter((150, 190, 140), 30))
        fur = jitter(rnd.choice([(190, 140, 90), (60, 50, 45), (230, 220, 200)]), 20)
        d.ellipse((60, 90, 196, 230), fill=fur)
        d.polygon([(70, 120), (80, 50), (118, 100)], fill=fur)
        d.polygon([(186, 120), (176, 50), (138, 100)], fill=fur)
        for ex in (102, 154):
            d.ellipse((ex - 8, 140, ex + 8, 156), fill=(25, 25, 25))
    elif key == "home":
        d.rectangle((0, 0, S, S), fill=jitter((225, 215, 200), 20))
        d.rectangle((0, 170, S, S), fill=jitter((150, 120, 95), 20))
        d.rectangle((r(20, 60), 60, r(140, 200), 150), fill=jitter((70, 90, 120), 30))
        d.rectangle((r(150, 190), 120, 240, 175), fill=jitter((200, 190, 170), 20))
    elif key == "vscreen":
        d.rectangle((0, 0, S, S), fill=(30, 30, 36))
        d.rounded_rectangle((70, 16, 186, 240), 14, fill=(246, 246, 248))
        for y in range(40, 220, 22):
            d.rounded_rectangle((82, y, 82 + r(40, 90), y + 9), 4, fill=(200, 200, 210))
    else:  # people: selfies, groups, talking videos, everyday clips
        bg = jitter(rnd.choice([(225, 215, 200), (190, 205, 225), (160, 160, 175), (235, 200, 190)]), 20)
        d.rectangle((0, 0, S, S), fill=bg)
        n = 1 if key in ("selfies", "vtalk") else rnd.choice([0, 1, 2, 3]) if key == "vclips" else r(2, 5)
        who = rnd.sample(REGULAR[:6], 1) if n == 1 and rnd.random() < .7 else []
        while len(who) < n:
            p = rnd.choice(REGULAR) if rnd.random() < .75 else rnd.choice(STRANGERS)
            if p not in who:
                who.append(p)
        for k, p in enumerate(who):
            cx = S // 2 if n == 1 else int(36 + k * (184 / max(1, n - 1)))
            rr = 52 if n == 1 else max(18, 34 - n * 3)
            cy = 104 if n == 1 else 120 + (k % 2) * 14
            d.ellipse((cx - rr * 1.8, cy + rr * 1.1, cx + rr * 1.8, cy + rr * 4), fill=p["shirt"])
            emo = rnd.choice(EMOTIONS)
            draw_face(d, cx, cy, rr, p, emo)
            faces_out.append((p, emo, [int(cx - rr), int(cy - rr * 1.1), int(rr * 2), int(rr * 2.2)], bg))
    return im.filter(ImageFilter.GaussianBlur(0.5))


# ---------- made-up screenshot and document contents ----------
PAYMENTS = [("Google Pay", "Payments", "Swiggy"), ("PhonePe", "Payments", "Zomato"), ("Paytm", "Payments", "Uber"),
            ("Google Pay", "Payments", "Amazon"), ("PhonePe", "Payments", "Airtel"), ("HDFC", "Bank", "Flipkart"),
            ("Google Pay", "Payments", "Blinkit"), ("Paytm", "Payments", "IRCTC")]
SOCIAL = [("Instagram", (193, 53, 132)), ("Twitter", (29, 155, 240)), ("Reddit", (255, 69, 0)), ("YouTube", (230, 33, 23)), ("LinkedIn", (10, 102, 194))]
OTHER = [("WhatsApp", "Social", "Chat", (37, 211, 102)), ("Google Maps", "Travel", "Map / directions", (66, 133, 244)),
         ("Gmail", "Work & email", "Email", (234, 67, 53)), ("Amazon", "Shopping", "Order / shopping", (35, 47, 62)),
         ("Netflix", "Streaming", "App screen", (20, 20, 20)), ("Zerodha", "Investing & insurance", "App screen", (56, 126, 209))]
DOCS = {
    "dfinance": [("Electricity bill {m}.pdf", "Bill / invoice", "Tata Power", (900, 4200)), ("HDFC statement {m}.pdf", "Bank statement", "HDFC", (20000, 90000)),
                 ("Salary slip {m}.pdf", "Salary slip", "", (45000, 120000)), ("Amazon invoice {n}.pdf", "Bill / invoice", "Amazon", (300, 9000)),
                 ("Flight ticket {m}.pdf", "Ticket / booking", "IndiGo", (3500, 14000)), ("Insurance premium {m}.pdf", "Insurance", "LIC", (5000, 30000))],
    "dids": [("Driving licence.pdf", "ID document", "Parivahan", None), ("Course certificate.pdf", "Certificate", "", None),
             ("Blood test report.pdf", "Medical", "", None), ("Passport copy.pdf", "ID document", "Passport Seva", None)],
    "dwork": [("Resume.docx", "Resume", "", None), ("Rent agreement.pdf", "Agreement", "", None), ("Lecture notes {n}.txt", "Study notes", "", None),
              ("Budget {y}.xlsx", "", "", None), ("Team plan.pptx", "", "Microsoft Teams", None)],
    "dother": [("Recipe.txt", "", "", None), ("Packing list.docx", "", "", None), ("Manual.pdf", "", "", None)],
}
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
PLACES = [(12.9716, 77.5946), (15.2993, 74.124), (26.9124, 75.7873), (32.2432, 77.1892), (19.076, 72.8777), (28.6139, 77.209)]
THINGS = {"selfies": "", "people": "", "pets": "golden retriever, tabby cat", "food": "pizza, plate, cup", "travel": "alp, valley, lakeside",
          "city": "streetcar, traffic light, cinema", "home": "desk, monitor, sofa", "vtravel": "valley, seashore", "vclips": "", "vtalk": "",
          "vscreen": "web site"}


def money(lo, hi):
    return round(rnd.uniform(lo, hi), 2) if rnd.random() < .5 else float(rnd.randint(lo, hi))


def finish(f, im, found, key, kind, when):
    """Save the pictures and faces of one made-up file and add it to the library."""
    global i, fid
    im.save(os.path.join(OUT, "thumbs", f"{i}.jpg"), quality=78)
    im.resize((72, 72)).save(os.path.join(OUT, "mini", f"{i}.jpg"), quality=72)
    for p, emo, box, bg in found:
        fid += 1
        small = box[2] < 32
        est_age = max(1, p["age"] + rnd.randint(-6, 6))
        bucket = next(b for b, hi in (("0-2", 3), ("4-6", 7), ("8-12", 13), ("15-20", 22), ("25-32", 34), ("38-43", 45), ("48-53", 56), ("60+", 200)) if est_age < hi)
        faces.append({"face_id": fid, "sha256": f["sha256"], "frame_s": round(rnd.uniform(0, f["duration"]), 1) if f["duration"] else None,
                      "x": box[0], "y": box[1], "w": box[2], "h": box[3], "img_w": 256, "img_h": 256, "score": round(rnd.uniform(.82, .99), 3),
                      "age": None if small else bucket, "age_years": None if small else est_age,
                      "gender": None if small else p["gender"], "gender_conf": None if small else round(rnd.uniform(.7, .99), 2),
                      "emotion": None if small else emo, "emotion_conf": None if small else round(rnd.uniform(.5, .98), 2),
                      "person_id": p["person_id"], "manual": 0, "file_ids": [i], "file": f["name"]})
        face_picture(p, emo, bg, os.path.join(OUT, "faces", f"{fid}.jpg"))
        f["face_ids"].append(fid)
        if p["person_id"] not in f["people_ids"]:
            f["people_ids"].append(p["person_id"])
    f["bytes"] = rnd.randint(20, 90) * 10**6 if kind == "video" else rnd.randint(1, 30) * 10**5 if kind == "doc" else rnd.randint(18, 60) * 10**5
    inv.append({"id": i, "name": f["name"], "kind": kind, "ext": f["ext"], "bytes": f["bytes"],
                "duration": f["duration"], "taken": int(when.timestamp())})
    labels[str(i)] = key
    files.append(f)
    i += 1


# ---------- build the library ----------
inv, labels, files, faces = [], {}, [], []
start = datetime(2023, 1, 1)
i = fid = 0
for c in cats:
    for _ in range(WEIGHTS.get(c["key"], 40)):
        key, kind = c["key"], c["kind"]
        when = start + timedelta(minutes=rnd.randint(0, 3 * 365 * 24 * 60))
        f = {"id": i, "sha256": f"demo{i}", "kind": kind, "path": "", "folder": c["label"], "folder_key": key, "duplicate_of": "",
             "copy": "", "taken": when.strftime("%Y-%m-%d %H:%M"), "camera": "", "lens": None, "lat": None, "lon": None,
             "width": 4032, "height": 3024, "duration": None, "screenshot": False, "tags": THINGS.get(key, ""), "text": "",
             "company": "", "sector": "", "content": "", "amount": None, "currency": "", "direction": "", "txn_ids": "",
             "error": "", "analysed": True, "face_ids": [], "people_ids": []}
        found = []
        if kind == "doc":
            tmpl, dtype, comp, rng = rnd.choice(DOCS[key])
            name = tmpl.format(m=f"{MONTHS[when.month - 1]} {when.year}", n=rnd.randint(100, 999), y=when.year)
            ext = os.path.splitext(name)[1]
            im = paper(ext, name)
            f.update(name=name, ext=ext, content=dtype, company=comp, width=None, height=None,
                     text=f"{dtype or 'Document'}\n{comp}\n{name}\n(made-up demo text)")
            if rng:
                f.update(amount=money(*rng), currency="INR", direction="in" if dtype in ("Salary slip", "Bank statement") else "out",
                         txn_ids=f"Invoice No IN-{rnd.randint(10000, 99999)}" if dtype == "Bill / invoice" else "")
        elif key in ("docs", "memes", "screenshots"):
            f.update(screenshot=True, ext=".png", name=f"Screenshot_{when:%Y%m%d-%H%M%S}.png", width=1170, height=2532, camera="",
                     tags="web site")
            if key == "docs":
                app, sector, payee = rnd.choice(PAYMENTS)
                amt = money(49, 4999)
                ref = f"{rnd.randint(10**11, 10**12 - 1)}"
                im = screen([app, "Payment successful", f"₹{amt:,.2f}", f"Paid to {payee}", f"UPI Ref No {ref}", when.strftime("%d %b %Y, %I:%M %p")],
                            accent=(26, 115, 232) if app == "Google Pay" else (95, 37, 159) if app == "PhonePe" else (0, 186, 242))
                f.update(company=f"{app}, {payee}", sector=sector, content="Payment", amount=amt, currency="INR", direction="out",
                         txn_ids=f"UPI Ref No {ref}", text=f"{app}\nPayment successful\n₹{amt:,.2f}\nPaid to {payee}\nUPI Ref No {ref}")
            elif key == "memes":
                app, col = rnd.choice(SOCIAL)
                im = screen([app, f"@creator{rnd.randint(1, 99)}", "", "", "", f"{rnd.randint(1, 90)},{rnd.randint(100, 999)} likes", "View all comments"],
                            dark=rnd.random() < .5, accent=col)
                ImageDraw.Draw(im).rectangle((14, 64, 242, 150), fill=jitter((200, 120, 90), 60))
                f.update(company=app, sector="Social", content="Social post", text=f"{app}\nlikes\ncomments")
            else:
                app, sector, what, col = rnd.choice(OTHER)
                im = screen([app, "Today", "Hi! Are we still on for tonight?" if what == "Chat" else what, "See you at 8", "Last seen 9:41 pm"],
                            dark=rnd.random() < .4, accent=col)
                f.update(company=app, sector=sector, content=what, text=f"{app}\n(made-up demo text)")
        else:
            im = draw(key, found)
            video = kind == "video"
            f.update(name=f"{'VID' if video else 'IMG'}_{4000 + i}.{'MOV' if video else 'JPG'}", ext=".mov" if video else ".jpg",
                     camera=rnd.choice(["Apple iPhone 14", "Apple iPhone 13", "Samsung Galaxy S23", "Google Pixel 8"]),
                     duration=round(rnd.uniform(4, 95), 1) if video else None, width=1920 if video else 4032, height=1080 if video else 3024)
            if key in ("travel", "city", "food", "vtravel") or rnd.random() < .3:
                lat, lon = rnd.choice(PLACES)
                f.update(lat=round(lat + rnd.uniform(-.05, .05), 5), lon=round(lon + rnd.uniform(-.05, .05), 5))
        finish(f, im, found, key, kind, when)

# ---------- family papers (made up): each family member's IDs, certificates, insurance, medical... ----------
PAPERS = [
    ("Certificate - ISO 27001 Lead Auditor.pdf", "This is to certify that {NAME} has successfully completed ISO 27001 Lead Auditor training"),
    ("Certificate - Python for security automation.pdf", "Certificate of completion. {NAME} has successfully completed the course"),
    ("{FIRST} resume - security automation, GRC.docx", "{NAME}\nProfessional summary: security automation, GRC, ISO 27001\nWork experience"),
    ("Fingerprint record.pdf", "Biometric fingerprint record of {NAME}"),
    ("Aadhaar.pdf", "Unique Identification Authority of India\n{UPPER}\nAadhaar"),
    ("PAN card.pdf", "INCOME TAX DEPARTMENT Permanent Account Number card {UPPER}"),
    ("Passport.pdf", "Republic of India Passport No Z1234567 {UPPER}"),
    ("Health insurance policy.pdf", "Health insurance policy schedule. Insured: {NAME}. Premium INR 18,400"),
    ("Term plan.pdf", "Term insurance policy. Life assured {NAME}. Sum assured INR 1,00,00,000"),
    ("Car insurance.pdf", "Private car package policy. Policyholder {NAME}. Premium INR 12,900"),
    ("Bike insurance.pdf", "Two wheeler package policy. Insured {NAME}"),
    ("Prescription.pdf", "Dr. S. Rao Clinic. Patient: {NAME}. Rx Tab. Paracetamol 500 twice daily"),
    ("Blood test report.pdf", "Laboratory report. Patient {NAME}. Haemoglobin 13.8 g/dL reference range"),
    ("Hospital invoice.pdf", "City Hospital invoice. Patient {NAME}. Amount INR 8,250"),
    ("Degree certificate.pdf", "University convocation. Bachelor of Technology awarded to {NAME}"),
    ("Form 16 {YEAR}.pdf", "Form 16 TDS certificate. Employee {UPPER}"),
]
for n in FAMILY:
    p = people[n - 1]
    full = p["name"]
    for tmpl, text in rnd.sample(PAPERS, 11):
        when = start + timedelta(days=rnd.randint(0, 3 * 365), minutes=rnd.randint(0, 1440))
        name = tmpl.format(FIRST=full.split()[0], YEAR=when.year)
        ext = os.path.splitext(name)[1]
        f = {"id": i, "sha256": f"demo{i}", "kind": "doc", "path": "", "folder": catby["dids"]["label"], "folder_key": "dids",
             "duplicate_of": "", "copy": "", "taken": when.strftime("%Y-%m-%d %H:%M"), "camera": "", "lens": None, "lat": None, "lon": None,
             "width": None, "height": None, "duration": None, "screenshot": False, "tags": "", "name": name, "ext": ext,
             "text": text.format(NAME=full, UPPER=full.upper()) + "\n(made-up demo document)", "company": "", "sector": "",
             "content": "", "amount": None, "currency": "", "direction": "", "txn_ids": "", "error": "", "analysed": True,
             "face_ids": [], "people_ids": []}
        finish(f, paper(ext, name), [], "dids", "doc", when)
    # a passport-size photo: one face, plain background, portrait
    when = start + timedelta(days=rnd.randint(0, 3 * 365))
    im = Image.new("RGB", (256, 256), (236, 240, 246))
    d = ImageDraw.Draw(im)
    d.ellipse((128 - 94, 180, 128 + 94, 340), fill=p["shirt"])
    draw_face(d, 128, 112, 62, p, "neutral")
    f = {"id": i, "sha256": f"demo{i}", "kind": "photo", "path": "", "folder": catby["selfies"]["label"], "folder_key": "selfies",
         "duplicate_of": "", "copy": "", "taken": when.strftime("%Y-%m-%d %H:%M"), "camera": "", "lens": None, "lat": None, "lon": None,
         "width": 413, "height": 531, "duration": None, "screenshot": False, "tags": "", "name": f"Passport photo {full.split()[0]}.jpg",
         "ext": ".jpg", "text": "", "company": "", "sector": "", "content": "", "amount": None, "currency": "", "direction": "",
         "txn_ids": "", "error": "", "analysed": True, "face_ids": [], "people_ids": [], "plain_bg": 2.0}
    finish(f, im, [(p, "neutral", [66, 44, 124, 136], (236, 240, 246))], "selfies", "photo", when)
for tmpl, text in [("Scanned ID.pdf", "Election Commission of India elector's photo identity card"),
                   ("Insurance renewal.pdf", "Two wheeler package policy renewal notice"),
                   ("Lab report.pdf", "Pathology lab report reference range")]:  # papers with no family name in them
    when = start + timedelta(days=rnd.randint(0, 3 * 365))
    f = {"id": i, "sha256": f"demo{i}", "kind": "doc", "path": "", "folder": catby["dids"]["label"], "folder_key": "dids",
         "duplicate_of": "", "copy": "", "taken": when.strftime("%Y-%m-%d %H:%M"), "camera": "", "lens": None, "lat": None, "lon": None,
         "width": None, "height": None, "duration": None, "screenshot": False, "tags": "", "name": tmpl, "ext": ".pdf",
         "text": text + "\n(made-up demo document)", "company": "", "sector": "", "content": "", "amount": None, "currency": "",
         "direction": "", "txn_ids": "", "error": "", "analysed": True, "face_ids": [], "people_ids": []}
    finish(f, paper(".pdf", tmpl), [], "dids", "doc", when)

dupes = []
for _ in range(38):  # pretend a few are burst shots
    k = rnd.randrange(1, len(inv))
    if inv[k]["kind"] == "photo" and not files[k]["screenshot"]:
        dupes.append({"keep": k - 1, "dupes": [k], "type": "near", "freed": inv[k]["bytes"]})
seen = set()
dupes = [g for g in dupes if g["dupes"][0] not in seen and not seen.add(g["dupes"][0])]
for g in dupes:
    d = files[g["dupes"][0]]
    d.update(folder="Duplicates (review)", folder_key="_dupes", duplicate_of=files[g["keep"]]["name"])

# ---------- people summaries (same shape as details.py) ----------
by_id = {p["person_id"]: p for p in people}
plist = {}
for p in people:
    n = p["person_id"]
    named = n <= 6
    plist[n] = {"person_id": n, "name": p["name"] if named else None,
                "mobile": f"+91 90000 000{n:02d}" if n <= 4 else None, "mobile_verified": 0,
                "consent": ["yes", "yes", "no", "pending"][n - 1] if n <= 4 else "pending",
                "consent_at": "2025-06-01 10:00:00" if n <= 3 else None,
                "share_with": "2,3" if n == 1 else "", "hide_from": "4" if n == 3 else "",
                "notes": "made-up demo person", "created_at": "2025-06-01 09:00:00",
                "family": 1 if n in FAMILY else 0, "aliases": "",
                "display": p["name"] if named else f"Person {n}", "photos": 0, "videos": 0, "faces": 0,
                "first": None, "last": None, "cover": None, "files": [], "_q": -1, "_ages": [], "_g": {}, "_e": {}}
for fc in faces:
    P = plist[fc["person_id"]]
    f = files[fc["file_ids"][0]]
    P["faces"] += 1
    if fc["w"] * fc["score"] > P["_q"]:
        P["cover"], P["_q"] = fc["face_id"], fc["w"] * fc["score"]
    if fc["age_years"] is not None:
        P["_ages"].append(fc["age_years"])
        P["_g"][fc["gender"]] = P["_g"].get(fc["gender"], 0) + 1
        P["_e"][fc["emotion"]] = P["_e"].get(fc["emotion"], 0) + 1
    if f["id"] not in P["files"]:
        P["files"].append(f["id"])
        P["videos" if f["kind"] == "video" else "photos"] += 1
        P["first"] = min(P["first"] or f["taken"], f["taken"])
        P["last"] = max(P["last"] or f["taken"], f["taken"])
for P in plist.values():
    P["age_est"] = round(sum(P["_ages"]) / len(P["_ages"])) if P["_ages"] else None
    P["gender_est"] = max(P["_g"], key=P["_g"].get) if P["_g"] else ""
    emos = sorted(P["_e"].items(), key=lambda kv: -kv[1])
    P["emotion_usual"] = emos[0][0] if emos else ""
    P["emotion_mix"] = ", ".join(f"{k} {v}" for k, v in emos[:3])
    for k in ("_q", "_ages", "_g", "_e"):
        P.pop(k)
plist = {k: v for k, v in plist.items() if v["faces"]}
for f in files:
    f["people"] = ", ".join(plist[n]["display"] for n in f["people_ids"]) or "un"
for fc in faces:
    fc["person"] = plist[fc["person_id"]]["display"]

import vault
for f in files:
    f["modified"] = f["taken"]
vmap = vault.assign(files, {x["face_id"]: x for x in faces}, plist)
for f in files:
    f["vault"] = vmap.get(f["id"])
VAULT_FOLDERS = [{"key": k, "name": n, "what": w} for k, n, w, _ in vault.FOLDERS] + [dict(zip(("key", "name", "what"), vault.OTHER))]
source = {"source": "~/Pictures/Camera roll (demo)", "sorted": "~/Pictures/Camera roll (demo) (sorted)"}
details = {"files": files, "faces": faces, "source": source, "categories": cats, "running": False, "demo": True,
           "vault_folders": VAULT_FOLDERS,
           "people": sorted(plist.values(), key=lambda p: (-(p["photos"] + p["videos"]), p["person_id"]))}
for name, obj in (("inventory.json", inv), ("labels.json", labels), ("dupes.json", dupes), ("categories.json", cats),
                  ("source.json", {"source": source["source"]}), ("details.json", details)):
    with open(os.path.join(OUT, name), "w") as fh:
        json.dump(obj, fh, ensure_ascii=False, separators=(",", ":"))

try:  # the sample Excel file, from the same made-up data
    import excel
    excel.build(os.path.join(OUT, "Library details (demo).xlsx"),
                {"files": files, "faces": faces, "people": plist, "source": source, "categories": cats}, base=OUT)
except ImportError:
    print("  (openpyxl not installed: no demo Excel file)")
print(f"Demo library: {len(inv)} files, {len(faces)} faces of {len(plist)} people, "
      f"{sum(1 for f in files if f['vault'])} family papers, in dashboard/demo/")
