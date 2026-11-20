"""Step 4: build the folders.  python scripts/apply.py "/where/to/put/Sorted"

Reads labels from work/labels/*.json (Claude) and/or work/jev.json (Jev).
If both exist: Jev's answer wins when it is >= 70% confident, otherwise Claude's.
COPIES files into <output>/<Folder>/ and duplicates into <output>/_Review/duplicates/.
On a Mac (same disk) copies are APFS clones: instant and they take no extra space.
Originals are never moved, renamed or deleted. Also writes sorted.csv and duplicates.csv.
"""
import csv, glob, os, shutil, subprocess, sys

sys.path.insert(0, os.path.dirname(__file__))
from common import CATEGORIES, DATA, JEV_OUT, LABELS, WORK, categories, load, save

OVERRIDES = os.path.join(WORK, "overrides.json")
src_dir = load(os.path.join(DATA, "source.json"), {}).get("source", "")
default = os.path.join(os.path.dirname(src_dir.rstrip("/")), os.path.basename(src_dir.rstrip("/")) + " (sorted)") if src_dir else ""
dest = os.path.expanduser(sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] else default)
if not dest:
    sys.exit('Usage: python scripts/apply.py "/where/to/put/Sorted"')
if src_dir and os.path.abspath(dest).startswith(os.path.abspath(src_dir) + os.sep):
    sys.exit("Put the sorted folders outside the photos folder, or the next scan would count them twice.")
recs = load(os.path.join(DATA, "inventory.json"))
cats = {c["key"]: c for c in categories()}
dupes = load(os.path.join(DATA, "dupes.json"), [])

claude = {}
for f in sorted(glob.glob(os.path.join(LABELS, "*.json"))):
    claude.update({str(k): v for k, v in load(f).items()})
jev = load(JEV_OUT, {})
if not claude and not jev:
    sys.exit("No labels yet. Label the files first (Claude: work/labels/*.json, or Jev: scripts/label_jev.py).")

labels, fixed, missing = {}, 0, 0
for r in recs:
    k = str(r["id"])
    j = jev.get(k, {})
    pick = j.get("key") if j.get("confidence", 0) >= 0.7 or k not in claude else claude.get(k)
    pick = pick or claude.get(k)
    if pick is None:
        missing += 1
    if pick not in cats or cats[pick]["kind"] != r["kind"]:  # photos only in photo folders, videos in video folders
        fallback = [c for c in cats.values() if c["kind"] == r["kind"]][-1]["key"]
        fixed += pick is not None
        pick = fallback
    labels[k] = pick

for k, v in load(OVERRIDES, {}).items():  # moves made by hand in the dashboard win
    if k in labels and v in cats:
        labels[k] = v

save(os.path.join(DATA, "labels.json"), labels)

# family papers go to Family/<Name>/<their folder tree>/ instead; photos they're in are also copied there (vault.py)
family_dir, family_extra, family_roots = {}, {}, []
try:
    import details, vault
    L = details.library()
    home = lambda p: os.path.join("Family", vault.safe(p["name"] or p["display"]))
    for p in L["people"].values():
        if p.get("family"):
            family_roots.append(home(p))
    for f in L["files"]:
        v = f.get("vault")
        if not v or v["person_id"] not in L["people"]:
            continue
        where = [os.path.join(home(L["people"][i]), *v["path"].split("/")) for i in [v["person_id"]] + v.get("also", []) if i in L["people"]]
        if v.get("extra"):
            family_extra[f["id"]] = where
        else:
            family_dir[f["id"]] = where[0]
except Exception as e:  # never stop the sort over this
    print(f"  (family folders skipped: {e})", flush=True)
src_info = load(os.path.join(DATA, "source.json"), {})
src_info["sorted"] = os.path.abspath(dest)
save(os.path.join(DATA, "source.json"), src_info)
shutil.copy(CATEGORIES, os.path.join(DATA, "categories.json"))

dupe_of = {d: g for g in dupes for d in g["dupes"]}
byid = {r["id"]: r for r in recs}


def copy(src, dst):
    if sys.platform == "darwin" and subprocess.run(["cp", "-c", "-p", src, dst], capture_output=True).returncode == 0:
        return
    shutil.copy2(src, dst)


os.makedirs(dest, exist_ok=True)
old = os.path.join(dest, "sorted.csv")
if os.path.exists(old):  # rebuilding: remove only the copies this tool made last time
    with open(old) as f:
        for row in csv.DictReader(f):
            p = os.path.join(dest, row["file"])
            if os.path.isfile(p):
                os.remove(p)
    for d, subdirs, files in os.walk(dest, topdown=False):
        if d != dest and not os.listdir(d):
            os.rmdir(d)
with open(os.path.join(dest, "sorted.csv"), "w", newline="") as fc, \
     open(os.path.join(dest, "duplicates.csv"), "w", newline="") as fd:
    wc, wd = csv.writer(fc), csv.writer(fd)
    wc.writerow(["file", "folder", "original_path"])
    wd.writerow(["duplicate", "kept_copy", "type", "duplicate_path", "kept_path"])
    for n, r in enumerate(recs, 1):
        folder = cats[labels[str(r["id"])]]["label"].replace("&", "and").replace("/", "-")
        if r["id"] in family_dir:
            folder = family_dir[r["id"]]
        if r["id"] in dupe_of:
            g = dupe_of[r["id"]]
            k = byid[g["keep"]]
            wd.writerow([r["name"], k["name"], g["type"], r["path"], k["path"]])
            folder = os.path.join("_Review", "duplicates")
        out_dir = os.path.join(dest, folder)
        os.makedirs(out_dir, exist_ok=True)
        target = os.path.join(out_dir, r["name"])
        if os.path.exists(target):  # same name from another folder/year
            b, e = os.path.splitext(r["name"])
            target = os.path.join(out_dir, f"{b}__{r['id']}{e}")
        if not os.path.exists(target):
            copy(r["path"], target)
        wc.writerow([os.path.relpath(target, dest), folder, r["path"]])
        for extra in family_extra.get(r["id"], []):  # a copy in each family member's 2. Photos folder
            os.makedirs(os.path.join(dest, extra), exist_ok=True)
            t2 = os.path.join(dest, extra, os.path.basename(target))
            if not os.path.exists(t2):
                copy(r["path"], t2)
            wc.writerow([os.path.relpath(t2, dest), extra, r["path"]])
        if n % 25 == 0 or n == len(recs):
            print(f"PROGRESS {n} {len(recs)}", flush=True)
        if n % 500 == 0:
            print(f"  copied {n}/{len(recs)}", flush=True)

for root in family_roots:  # the whole folder tree, empty folders too
    for sub in vault.TREE:
        os.makedirs(os.path.join(dest, root, *sub.split("/")), exist_ok=True)

# folders show the date of their newest file as "Modified" (like 9 Jan 2021), not today's date
newest = {}
for d, _, fs in os.walk(dest, topdown=False):
    times = [os.path.getmtime(os.path.join(d, f)) for f in fs if not f.endswith(".csv") and not f.endswith(".xlsx")]
    times += [newest[os.path.join(d, s)] for s in os.listdir(d) if os.path.join(d, s) in newest]
    if times and d != dest:
        newest[d] = max(times)
        os.utime(d, (newest[d], newest[d]))

counts = {}
for r in recs:
    if r["id"] not in dupe_of:
        counts[labels[str(r["id"])]] = counts.get(labels[str(r["id"])], 0) + 1
print(f"Sorted into {dest}")
for k, c in cats.items():
    print(f"  {c['label']:24} {counts.get(k, 0)}")
print(f"  {'_Review/duplicates':24} {len(dupe_of)}")
if family_dir:
    print(f"  {'Family':24} {len(family_dir)} papers, {sum(map(len, family_extra.values()))} photo copies, {len(family_roots)} people")
if missing or fixed:
    print(f"  ({missing} files had no label and {fixed} had a wrong-type label; they went to the last folder of their kind)")
