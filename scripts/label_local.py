"""Pick a folder for every file on this computer, for free, from what analyze.py found.

  python scripts/label_local.py      -> work/labels/local.json  ({"id": "folder key"})

Rules, in order:
  screenshots   payment / order / ticket / bank / government -> documents & receipts,
                social posts and videos apps -> memes & saved posts, the rest -> other screenshots
  photos        a page of text -> documents; one big face -> selfie; faces -> people;
                animals -> pets; food -> food; mountains, beaches, landmarks -> travel; streets, cars, shops -> city;
                anything else -> home & everyday
  videos        screen recordings; a face filling the frame -> talking videos; nature -> travel clips; the rest -> everyday
  documents     bills, statements, payslips -> finance; IDs, certificates, medical -> IDs; study and work -> work
Folders you added yourself are used when their name or rule mentions what was found (e.g. "cars", "Swiggy").
"""
import json, os, re, sqlite3, sys

sys.path.insert(0, os.path.dirname(__file__))
from common import DATA, DB, LABELS, MODELS, categories, load, save

NAMES = {int(k): v.split(",")[0] for k, v in json.load(open(os.path.join(MODELS, "imagenet.json"))).items()}
ANIMALS = {NAMES[i] for i in range(0, 398)}
FOOD = {NAMES[i] for i in range(923, 970)} | {"restaurant", "soup bowl", "frying pan", "wok", "coffee mug", "beer glass",
                                               "wine bottle", "beer bottle", "red wine", "espresso", "cup", "plate"}
NATURE = {NAMES[i] for i in range(970, 981)} | {"boathouse", "castle", "church", "palace", "mosque", "monastery", "stupa",
          "obelisk", "triumphal arch", "pier", "breakwater", "suspension bridge", "steel arch bridge", "dam", "beacon",
          "airliner", "canoe", "speedboat", "liner", "mountain tent", "yurt", "sandbar", "lakeside", "seashore",
          "valley", "cliff", "promontory", "geyser", "coral reef", "megalith", "dock", "paddle", "snowmobile", "ski"}
CITY = {"streetcar", "cab", "limousine", "sports car", "convertible", "traffic light", "street sign", "parking meter",
        "cinema", "tobacco shop", "bookshop", "grocery store", "toyshop", "barbershop", "bakery", "butcher shop",
        "confectionery", "shoe shop", "trolleybus", "school bus", "minibus", "passenger car", "police van",
        "moving van", "jeep", "minivan", "motor scooter", "moped", "mountain bike", "stage", "water tower",
        "racer", "car wheel", "pickup", "tow truck", "trailer truck", "fire engine", "ambulance", "garbage truck",
        "electric guitar", "spotlight", "scoreboard", "shopping cart", "planetarium", "library", "prison", "thatch"}
DOCLIKE = {"menu", "web site", "envelope", "book jacket", "comic book", "crossword puzzle", "binder", "notebook"}
FIN_SCREENS = {"Payment", "Order / shopping", "Ticket / booking"}
FIN_SECTORS = {"Bank", "Payments", "Government", "Investing & insurance"}
SOCIAL = {"Social", "Streaming"}
DOC_MAP = {"Bank statement": "dfinance", "Bill / invoice": "dfinance", "Salary slip": "dfinance", "Insurance": "dfinance",
           "Tax": "dfinance", "ID document": "dids", "Certificate": "dids", "Medical": "dids",
           "Resume": "dwork", "Study notes": "dwork", "Agreement": "dwork", "Ticket / booking": "dfinance"}
STANDARD = {"selfies", "people", "pets", "food", "travel", "city", "home", "docs", "memes", "screenshots",
            "vtalk", "vtravel", "vscreen", "vclips", "dfinance", "dids", "dwork", "dother"}


def words(s):
    return {w for w in re.findall(r"[a-z]{3,}", (s or "").lower())}


def custom_match(cats, kind, info):
    """A folder you added whose name/rule shares a word with the tags, company or content."""
    found = words(" ".join(str(info.get(k) or "") for k in ("tags", "company", "sector", "content")))
    best, score = None, 0
    for c in cats:
        if c["kind"] != kind or c["key"] in STANDARD:
            continue
        n = len(found & (words(c["label"]) | words(c.get("rule"))))
        if n > score:
            best, score = c["key"], n
    return best


def pick(r, info, faces, have):
    """The folder key for one inventory record."""
    def first(*keys):
        return next((k for k in keys if k in have), None)
    tags = [t.strip() for t in (info.get("tags") or "").split(",") if t.strip()]
    if r["kind"] == "doc":
        return first(DOC_MAP.get(info.get("content") or "", "dother"), "dother")
    if r["kind"] == "video":
        name = r["name"].lower()
        if "screen" in name or "rpreplay" in name:
            return first("vscreen")
        big = max([f["w"] * f["h"] / max(1, f["img_w"] * f["img_h"]) for f in faces] or [0])
        if big >= 0.03:
            return first("vtalk")
        if NATURE & set(tags):
            return first("vtravel")
        return first("vclips")
    if info.get("is_screenshot"):
        if info.get("content") in FIN_SCREENS or info.get("sector") in FIN_SECTORS:
            return first("docs", "screenshots")
        if info.get("content") == "Social post" or info.get("sector") in SOCIAL:
            return first("memes", "screenshots")
        return first("screenshots")
    if info.get("content") == "Photo of a document" or (DOCLIKE & set(tags[:2]) and not faces):
        return first("docs")
    if faces:
        areas = sorted((f["w"] * f["h"] / max(1, f["img_w"] * f["img_h"]) for f in faces), reverse=True)
        if areas[0] >= 0.06 and (len(areas) == 1 or areas[1] < areas[0] / 3):
            return first("selfies", "people")
        if areas[0] >= 0.004:
            return first("people")
    for t in tags[:3]:
        if t in ANIMALS:
            return first("pets")
        if t in FOOD:
            return first("food")
        if t in NATURE:
            return first("travel")
        if t in CITY:
            return first("city")
    return first("home")


def main():
    inv = load(os.path.join(DATA, "inventory.json"), [])
    cats = categories()
    have = {c["key"] for c in cats}
    db = sqlite3.connect(DB)
    db.row_factory = sqlite3.Row
    info = {r["sha256"]: dict(r) for r in db.execute("SELECT * FROM files")}
    faces = {}
    for f in db.execute("SELECT sha256, w, h, img_w, img_h FROM faces"):
        faces.setdefault(f["sha256"], []).append(dict(f))
    out = {}
    for n, r in enumerate(inv, 1):
        i = info.get(r["sha256"], {})
        key = custom_match(cats, r["kind"], i) or pick(r, i, faces.get(r["sha256"], []), have)
        if key:
            out[str(r["id"])] = key  # no key: apply.py puts it in the last folder of its kind
        if n % 200 == 0 or n == len(inv):
            print(f"PROGRESS {n} {len(inv)}", flush=True)
    os.makedirs(LABELS, exist_ok=True)
    save(os.path.join(LABELS, "local.json"), out)
    counts = {}
    for k in out.values():
        counts[k] = counts.get(k, 0) + 1
    print("Sorted on this computer: " + ", ".join(f"{k} {v}" for k, v in sorted(counts.items(), key=lambda kv: -kv[1])), flush=True)


if __name__ == "__main__":
    main()
