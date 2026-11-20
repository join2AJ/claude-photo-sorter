"""Family document vault: whose papers and photos are these, and which folder do they go in?

Every person marked as family (on the Details page) gets the same folder tree (TREE below), e.g.
  Family/Ajay Kumar/1. Documents/3. Legal/1. IDs/
  Family/Ajay Kumar/3. Medical/5. Medical, Life Insurance/2. Life Insurance/2. Premium receipts/
  Family/Ajay Kumar/4. Company/<Employer>/1. Pre-Joining/
Empty folders are made too, so the structure is always complete.

Documents (and photos of documents) are filed by the rules in DOC_RULES, first match wins.
Photos and videos they're in are also copied into their 2. Photos folders (profile, trip, event...).

Whose is it, in this order:
  1. you said so on the Details page (always wins)
  2. their name, or another name they use on documents, is written in it
  3. their face is in it (ID card photo, passport-size photo, or any photo for 2. Photos)
Documents of the right kind that match no one are listed as "Not sure whose" for you to assign.
Plain word rules, no internet. Edit TREE and DOC_RULES to change the folders.
"""
import re

D, EDU, FIN, LEG, PH, MED, CO, MISC = "1. Documents", "1. Educational", "2. Financial", "3. Legal", "2. Photos", "3. Medical", "4. Company", "5. Miscellaneous"
LIFE = f"{MED}/5. Medical, Life Insurance/2. Life Insurance"
RES = f"{D}/{EDU}/2. Resume"
TREE = [
    f"{D}/{EDU}/1. Certificates/1. Skill Certificates", f"{D}/{EDU}/1. Certificates/2. Study Certificates",
    f"{RES}/1. Information Security", f"{RES}/2. Data Analytics", f"{RES}/3. SIEM", f"{RES}/4. Security Automation",
    f"{RES}/5. Physical Security", f"{D}/{EDU}/3. Miscellaneous",
    f"{D}/{FIN}/1. Expenses", f"{D}/{FIN}/2. Income Tax", f"{D}/{FIN}/3. Miscellaneous",
    f"{D}/{LEG}/1. IDs", f"{D}/{LEG}/2. DNA", f"{D}/{LEG}/3. Property/0. Rent", f"{D}/{LEG}/3. Property/1. Company, Land, Building",
    f"{D}/{LEG}/3. Property/2. Vehicle/1. Bike", f"{D}/{LEG}/3. Property/2. Vehicle/2. Car", f"{D}/{LEG}/4. Cases",
    f"{D}/{LEG}/5. Miscellaneous", f"{D}/{LEG}/6. Company Ids",
    f"{PH}/0. Profile Photos", f"{PH}/1. Inspirations", f"{PH}/2. Trip Photos", f"{PH}/3. Event Photos", f"{PH}/4. Miscellaneous",
    f"{MED}/1. Diagnostics", f"{MED}/2. Prescriptions", f"{MED}/3. Vaccinations", f"{MED}/4. Medical History",
    f"{MED}/5. Medical, Life Insurance/1. Medical Insurance", f"{LIFE}/1. Policy Pack", f"{LIFE}/2. Premium receipts",
    f"{LIFE}/3. Annual policy statement", f"{MED}/6. Wellness",
    CO, MISC,
]
COMPANY_SUB = ["1. Pre-Joining", "2. Post-Joining", "3. Farewell", "4. Course or Travel", "5. Others"]

VEHICLE = r"\b(registration certificate|certificate of registration|chassis no|engine no|pollution under control|puc|challan|motor insurance|private car|two wheeler|car insurance|bike insurance|vehicle)\b"
BIKE = r"\b(two wheeler|bike|motor ?cycle|scooter|scooty)\b"
COMPANY_DOC = [
    ("1. Pre-Joining", r"\b(offer letter|letter of offer|appointment letter|letter of appointment|background verification|joining (kit|formalities|date)|we are pleased to offer)\b"),
    ("3. Farewell", r"\b(relieving letter|experience letter|resignation|full and final|f&f settlement|last working day|farewell)\b"),
    ("2. Post-Joining", r"\b(salary slip|pay ?slip|payslip|appraisal|increment|promotion|confirmation letter|performance review|bonus letter)\b"),
    ("4. Course or Travel", r"\b(travel (request|reimbursement|policy)|business travel|training nomination|sponsored course)\b"),
]
RESUME_FOCUS = [
    ("1. Information Security", r"\b(information security|cyber ?security|iso ?27001|grc|vapt|risk assessment|isms)\b"),
    ("2. Data Analytics", r"\b(data analytics|data analyst|power ?bi|tableau|data visuali[sz]ation|pandas)\b"),
    ("3. SIEM", r"\b(siem|splunk|qradar|sentinel|arcsight|soc analyst|security operations cent(er|re))\b"),
    ("4. Security Automation", r"\b(security automation|soar|automation|ansible|python scripting)\b"),
    ("5. Physical Security", r"\b(physical security|cctv|access control|guarding|perimeter security)\b"),
]
# (folder, pattern): the first match wins, so the more specific rules come first
DOC_RULES = [
    (f"{D}/{LEG}/2. DNA", r"\b(finger ?prints?|thumb impression|biometric|specimen signature|dna)\b"),
    (f"{D}/{LEG}/1. IDs", r"\b(aadhaar|aadhar|uidai|unique identification authority|permanent account number|pan card|passport no|republic of india.{0,60}passport|election commission|voter id|elector'?s photo identity|driving licen[cs]e|ration card)\b"),
    (f"{D}/{LEG}/6. Company Ids", r"\b(employee id( card)?|employee code|staff id|access card)\b"),
    ("company", None),  # offer letters, payslips, relieving letters... -> 4. Company/<Employer>/
    ("vehicle", None),
    (f"{D}/{LEG}/3. Property/0. Rent", r"\b(rent agreement|rental agreement|lease deed|leave and licen[cs]e|rent receipt|tenancy)\b"),
    (f"{D}/{LEG}/3. Property/1. Company, Land, Building", r"\b(sale deed|gift deed|property tax|khata|encumbrance|property card|plot no|land record|7/12|building plan)\b"),
    (f"{D}/{LEG}/4. Cases", r"\b(court|first information report|\bfir\b|legal notice|summons|petition|advocate|vakalatnama|hearing)\b"),
    (f"{MED}/5. Medical, Life Insurance/1. Medical Insurance", r"\b(health insurance|mediclaim|health policy|star health|care health|niva bupa|family floater|cashless)\b"),
    (f"{LIFE}/2. Premium receipts", r"\b(premium (paid )?receipt|premium paid certificate|renewal premium receipt)\b"),
    (f"{LIFE}/3. Annual policy statement", r"\b(annual (policy )?statement|policy statement for the year|unit statement)\b"),
    (f"{LIFE}/1. Policy Pack", r"\b(term (plan|insurance|life)|life insurance|sum assured|life assured|policy (document|schedule|bond)|lic of india)\b"),
    (f"{MED}/3. Vaccinations", r"\b(vaccin\w*|immuni[sz]ation|cowin|booster dose)\b"),
    (f"{MED}/2. Prescriptions", r"(\bprescription\b|\brx\b|\btab\.|\bcap\.|\bdosage\b|twice daily|once daily)"),
    (f"{MED}/1. Diagnostics", r"\b(lab(oratory)? report|blood test|haemoglobin|hemoglobin|x-?ray|mri|ct scan|ultrasound|pathology|test report|reference range|diagnos\w*)\b"),
    (f"{MED}/4. Medical History", r"\b(discharge summary|medical history|admission|hospital(i[sz]ation)?|surgery|opd)\b"),
    (f"{MED}/6. Wellness", r"\b(gym|fitness|diet plan|yoga|wellness|nutrition)\b"),
    (f"{D}/{FIN}/2. Income Tax", r"\b(form 16|itr|income tax return|form 26as|tds certificate|advance tax)\b"),
    (f"{D}/{EDU}/1. Certificates/2. Study Certificates", r"\b(degree|diploma|mark ?sheet|statement of marks|grade card|transcript|bachelor of|master of|convocation|school leaving|cgpa|sgpa)\b"),
    ("resume", r"\b(curriculum vitae|resume|résumé|professional summary|career objective)\b"),
    (f"{D}/{EDU}/1. Certificates/1. Skill Certificates", r"\b(certificate|certification|certify|certified|course completion|iso ?\d{4,5}|lead auditor|cissp|cisa|cism|ceh|oscp|comptia|pmp|itil|ccna|aws certified)\b"),
    (f"{D}/{EDU}/3. Miscellaneous", r"\b(lecture|notes|assignment|syllabus|exam|semester)\b"),
    (f"{D}/{FIN}/3. Miscellaneous", r"\b(account statement|statement of account|bank statement|mutual fund|demat|fixed deposit|ppf|nps|loan|emi)\b"),
    (f"{D}/{FIN}/1. Expenses", r"\b(invoice|bill|receipt|payment|order total|amount payable|paid)\b"),
    (f"{D}/{LEG}/5. Miscellaneous", r"\b(agreement|contract|affidavit|notary|power of attorney|undertaking|declaration)\b"),
    (MISC, r"\b(ticket|boarding pass|itinerary|visa|warranty|manual)\b"),
]
TRAVEL_TAGS = {"trip", "mountains", "beach", "lake", "landmark", "travel", "snow", "desert", "forest"}
EVENT_TAGS = {"event", "party", "stage", "wedding", "concert", "celebration"}
EMPLOYER = re.compile(r"\b((?:[A-Z][A-Za-z&]+\s+){0,3}[A-Z][A-Za-z&]+)\s*,?\s+(?:Pvt\.?\s*Ltd\.?|Private\s+Limited|Limited|Ltd\.?|LLP|Inc\.?)\b")


def employer(text):
    m = EMPLOYER.search(text or "")
    if not m:
        return "Unknown company"
    name = re.sub(r"\b(Dear|To|From|The|M/s)\s+", "", m.group(1)).strip()
    name = re.sub(r"\s+(Private|Pvt\.?)$", "", name)
    return name[:40] or "Unknown company"


def folder_for_text(text, name=""):
    """The folder path for a document from its text and file name, or None when it's not a family paper."""
    low = f"{name}\n{text}".lower()
    for path, pat in DOC_RULES:
        if path == "company":
            for sub, p in COMPANY_DOC:
                if re.search(p, low):
                    return f"{CO}/{safe(employer(text))}/{sub}"
            continue
        if path == "vehicle":
            if re.search(VEHICLE, low):
                return f"{D}/{LEG}/3. Property/2. Vehicle/" + ("1. Bike" if re.search(BIKE, low) else "2. Car")
            continue
        if not re.search(pat, low):
            continue
        if path == "resume":
            hits = [(len(re.findall(p, low)), sub) for sub, p in RESUME_FOCUS]
            best = max(hits)
            return f"{RES}/{best[1]}" if best[0] else RES
        return path
    return None


def looks_like_passport_photo(f, faces):
    """One clear face filling a portrait picture with a plain background (or 'passport' in the name)."""
    if f["kind"] != "photo" or f.get("screenshot") or len(faces) != 1:
        return False
    if re.search(r"passport|pp[_ -]?(size|photo)|\bphoto ?id\b", f["name"], re.I):
        return True
    x = faces[0]
    w, h = f.get("width") or 0, f.get("height") or 0
    area = x["w"] * x["h"] / max(1, x["img_w"] * x["img_h"])
    plain = f.get("plain_bg")
    return bool(w and h and 1.1 <= h / w <= 1.6 and area >= 0.12 and plain is not None and plain < 14)


def photo_folder(f, fs, labels):
    """Where a photo or video of a family member goes inside their 2. Photos folder."""
    big = max([x["w"] * x["h"] / max(1, x["img_w"] * x["img_h"]) for x in fs] or [0])
    if len(fs) == 1 and big >= 0.06 and f["kind"] == "photo":
        return f"{PH}/0. Profile Photos"
    if TRAVEL_TAGS & set(labels):
        return f"{PH}/2. Trip Photos"
    if len(fs) >= 3 or EVENT_TAGS & set(labels):
        return f"{PH}/3. Event Photos"
    return f"{PH}/4. Miscellaneous"


def _name_pattern(name):
    words = [re.escape(w) for w in re.findall(r"[a-z]+", name.lower()) if len(w) > 1]
    if len(words) < 2:  # a single first name is too easy to mistake: needs a surname or another name
        return None
    forward = r"\b" + r"[\s.,]+".join(words) + r"\b"
    backward = r"\b" + r"[\s.,]+".join(reversed(words)) + r"\b"  # KUMAR AJAY on some IDs
    return re.compile(forward + "|" + backward)


def leaf(path):
    return path.rsplit("/", 1)[-1]


def assign(files, faces_by_id, people, overrides=None):
    """{file id: {"person_id", "path", "folder_name", "by", "extra"}} for family papers and photos.
    person_id is None for papers that match no family member ("Not sure whose").
    extra=True: a photo they're in; it keeps its normal folder and is also copied into theirs."""
    overrides = overrides or {}
    family = {p["person_id"]: p for p in people.values() if p.get("family")}
    pats = []
    for p in family.values():
        for n in [p.get("name") or ""] + re.split(r"[,;\n]", p.get("aliases") or ""):
            pat = _name_pattern(n.strip())
            if pat:
                pats.append((p["person_id"], pat))
    out = {}
    for f in files:
        if f.get("duplicate_of"):
            continue
        fs = [faces_by_id[i] for i in f["face_ids"] if i in faces_by_id]
        text = f.get("text") or ""
        path = None
        if f["kind"] == "doc" or (f["kind"] == "photo" and len(text) > 30 and not fs):
            path = folder_for_text(text, f["name"])
        if path is None and looks_like_passport_photo(f, fs):
            path = f"{D}/{LEG}/2. DNA"
        ov = overrides.get(f["sha256"])
        if ov and ov.get("not_family"):
            continue  # you said: not a family paper
        if path is None and not ov:
            fam = sorted({x["person_id"] for x in fs if x["person_id"] in family})
            if fam and f["kind"] in ("photo", "video") and not f.get("screenshot"):
                where = photo_folder(f, fs, f.get("labels") or [])
                out[f["id"]] = {"person_id": fam[0], "also": fam[1:], "path": where, "folder_name": leaf(where), "by": "face", "extra": True}
            continue
        who, by = None, ""
        if ov:
            who, by = ov.get("person_id"), "you"
            path = ov.get("folder") or path or MISC
        else:
            low = f"{f['name']}\n{text}".lower()
            hits = {}
            for pid_, pat in pats:
                n = len(pat.findall(low))
                if n:
                    hits[pid_] = hits.get(pid_, 0) + n
            if hits:
                who, by = max(hits, key=hits.get), "name"
            else:
                fam = [x["person_id"] for x in fs if x["person_id"] in family]
                if len(set(fam)) == 1:
                    who, by = fam[0], "face"
        out[f["id"]] = {"person_id": who, "also": [], "path": path, "folder_name": leaf(path), "by": by, "extra": False}
    return out


def safe(name):
    return re.sub(r'[\\/:*?"<>|]+', "-", name).strip(" .") or "Unnamed"
