"""Plain-word tags for every photo and video: what's in it (dine-out, beach, mountains, dog...),
the light and sky (sky, sunset, night, greenery), who's in it (selfie, couple, group, family, names),
the mood (happy, sad...) and when (morning, evening, weekend). Used for search on the Details page."""
import json, os
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
try:
    _N = {int(k): v.split(",")[0] for k, v in json.load(open(os.path.join(ROOT, "models", "imagenet.json"))).items()}
except OSError:  # models not downloaded yet: fall back to the word lists below
    _N = {}
ANIMALS = {_N[i] for i in range(0, 398) if i in _N}
DOGS = {_N[i] for i in range(151, 269) if i in _N} | {"golden retriever", "labrador retriever", "pug", "beagle"}
CATS = {_N[i] for i in range(281, 286) if i in _N} | {"tabby cat", "tabby", "persian cat", "siamese cat"}
FOOD = {_N[i] for i in range(924, 970) if i in _N} | {"pizza", "cheeseburger", "ice cream", "espresso", "plate", "cup"}
DINING = {"restaurant", "plate", "menu", "dining table", "wine bottle", "beer glass", "red wine", "cup", "espresso", "soup bowl"}
WORDS = {
    "mountains": {"alp", "valley", "volcano", "cliff", "promontory", "mountain tent"},
    "beach": {"seashore", "sandbar", "beach wagon", "swimming trunks", "sarong"},
    "lake": {"lakeside", "boathouse", "canoe", "paddle"},
    "landmark": {"palace", "castle", "church", "mosque", "monastery", "stupa", "obelisk", "triumphal arch", "megalith", "dome", "bell cote"},
    "city": {"streetcar", "cab", "traffic light", "street sign", "trolleybus", "cinema", "parking meter", "tobacco shop", "bookshop", "grocery store"},
    "car": {"sports car", "convertible", "limousine", "jeep", "minivan", "car wheel", "racer", "pickup"},
    "bike": {"motor scooter", "moped", "mountain bike", "bicycle-built-for-two", "tricycle"},
    "event": {"stage", "spotlight", "electric guitar", "microphone", "academic gown", "mortarboard", "balloon", "maypole"},
    "home": {"desk", "sofa", "studio couch", "monitor", "television", "bookcase", "four-poster", "dining table", "wardrobe"},
    "snow": {"ski", "snowmobile", "bobsled", "dogsled"},
    "flowers": {"daisy", "pot", "vase"},
}
TRAVEL = {"mountains", "beach", "lake", "landmark", "snow"}


def color_tags(im):
    """Sky, sunset, night and greenery from the colours of a PIL image."""
    import colorsys
    im = im.convert("RGB").resize((48, 48))
    px = list(im.getdata())
    top = px[: 48 * 16]
    hsv = lambda p: colorsys.rgb_to_hsv(*(c / 255 for c in p))
    th = [hsv(p) for p in top]
    allh = [hsv(p) for p in px]
    out = []
    if sum(1 for h, s, v in th if 0.5 <= h <= 0.7 and s > 0.15 and v > 0.45) > 0.4 * len(th):
        out.append("sky")
    if sum(1 for h, s, v in th if (h <= 0.12 or h >= 0.95) and s > 0.35 and v > 0.55) > 0.3 * len(th):
        out.append("sunset")
    if sum(v for _, _, v in allh) / len(allh) < 0.22:
        out.append("night")
    if sum(1 for h, s, v in allh if 0.19 <= h <= 0.45 and s > 0.25 and v > 0.2) > 0.3 * len(allh):
        out.append("greenery")
    return out


def make_labels(f, faces, people):
    """All tags for one file (a details.py file dict, its face dicts, and the people dict)."""
    t = []
    names = [x.strip() for x in (f.get("tags") or "").split(",") if x.strip()]
    found = set(names)
    if f.get("screenshot"):
        t.append("screenshot")
    if f["kind"] == "doc" or f.get("content") == "Photo of a document":
        t.append("document")
    if f["kind"] == "video":
        t.append("video")
    if f["kind"] != "doc" and not f.get("screenshot"):
        if found & FOOD:
            t.append("food")
            if found & DINING or len(faces) >= 2:
                t.append("dine-out")
        if found & DOGS:
            t.append("dog")
        elif found & CATS:
            t.append("cat")
        elif found & ANIMALS:
            t.append("animals")
        for word, keys in WORDS.items():
            if found & keys:
                t.append(word)
        if TRAVEL & set(t):
            t.append("trip")
        t += [c for c in (f.get("colors") or "").split(",") if c]
        n = len({x["person_id"] for x in faces})
        if n == 1 and max(x["w"] * x["h"] / max(1, x["img_w"] * x["img_h"]) for x in faces) >= 0.06:
            t.append("selfie")
        elif n == 2:
            t.append("couple")
        elif n >= 3:
            t.append("group")
        fam = [x["person_id"] for x in faces if people.get(x["person_id"], {}).get("family")]
        if len(set(fam)) >= 2:
            t.append("family")
        for x in faces:
            p = people.get(x["person_id"])
            if p and p.get("name"):
                t.append(p["display"])
        for x in faces:
            if x.get("emotion"):
                t.append(x["emotion"])
        if f.get("taken"):
            try:
                d = datetime.strptime(f["taken"][:16], "%Y-%m-%d %H:%M")
                t.append("morning" if 5 <= d.hour < 12 else "afternoon" if d.hour < 17 else "evening" if d.hour < 21 else "late night")
                if d.weekday() >= 5:
                    t.append("weekend")
            except ValueError:
                pass
    return list(dict.fromkeys(t))
