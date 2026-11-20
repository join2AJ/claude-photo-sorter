"""Family document vault: whose papers are these, and which folder do they go in?

For people marked as family (on the Details page), documents and photos of documents are filed as
  Family/<Name>/<Folder>/   e.g. Family/Ajay Kumar/Insurance/
Folders: Certificates, Corporate Resume, DNA (biometrics), ID, Insurance, Medical, Education,
Finance & Tax, Property & Home, Vehicle, Travel, Other papers. Some get a sub-type (health, term, car, bike...).

Whose is it, in this order:
  1. you said so on the Details page (always wins)
  2. their name, or another name they use on documents, is written in it (ID cards, certificates, policies...)
  3. their face is in it (photo on an ID card, passport-size photo)
Documents of the right kind that match no one are listed as "Not sure whose" for you to assign.
Plain word rules, no internet.
"""
import re

# (key, folder, what goes in it, rules [(sub-type, pattern)])  -- order matters: the first match wins
FOLDERS = [
    ("dna", "DNA", "fingerprints, passport-size photos, signatures", [
        ("fingerprint", r"\b(finger ?prints?|thumb impression|biometric)\b"),
        ("signature", r"\bspecimen signature\b"),
    ]),
    ("id", "ID", "government IDs: Aadhaar, PAN, passport, voter ID, driving licence", [
        ("Aadhaar", r"\b(aadhaar|aadhar|uidai|unique identification authority)\b"),
        ("PAN", r"\b(permanent account number|income tax department.{0,40}card|pan card)\b"),
        ("passport", r"\b(republic of india.{0,60}passport|passport no|type\W+p\W+code|passport)\b"),
        ("voter ID", r"\b(election commission|voter id|elector'?s photo identity)\b"),
        ("driving licence", r"\b(driving licen[cs]e|licence no|dl no)\b"),
        ("ration card", r"\bration card\b"),
    ]),
    ("vehicle", "Vehicle", "RC, PUC, service and challans", [
        ("RC", r"\b(registration certificate|certificate of registration|chassis no|engine no)\b"),
        ("PUC", r"\b(pollution under control|puc certificate)\b"),
        ("challan", r"\bchallan\b"),
    ]),
    ("insurance", "Insurance", "health, term, car, bike and other policies", [
        ("health", r"\b(health insurance|mediclaim|health policy|star health|care health|niva bupa|hospitali[sz]ation cover)\b"),
        ("term", r"\b(term (plan|insurance|life)|life insurance|sum assured|lic of india)\b"),
        ("car", r"\b(private car|motor insurance.{0,40}car|car insurance|four wheeler)\b"),
        ("bike", r"\b(two wheeler|bike insurance|motor ?cycle)\b"),
        ("", r"\b(insurance|policy (no|number|schedule)|premium|insured|policyholder)\b"),
    ]),
    ("medical", "Medical", "prescriptions, diagnosis, lab reports, hospital bills", [
        ("prescription", r"\b(prescription|rx\b|tab\.|cap\.|dosage|twice daily|once daily)"),
        ("lab report", r"\b(lab(oratory)? report|haemoglobin|hemoglobin|blood test|test report|reference range|pathology)\b"),
        ("diagnosis", r"\b(diagnosis|discharge summary|impression|consultation|opd)\b"),
        ("hospital bill", r"\b(hospital|pharmacy|chemist|clinic).{0,80}\b(bill|invoice|receipt)\b"),
    ]),
    ("education", "Education", "marksheets, degrees, transcripts", [
        ("marksheet", r"\b(mark ?sheet|statement of marks|grade card|cgpa|sgpa)\b"),
        ("degree", r"\b(degree|diploma|bachelor of|master of|convocation|provisional certificate)\b"),
        ("transcript", r"\btranscript\b"),
    ]),
    ("finance", "Finance & Tax", "bank statements, salary slips, ITR, Form 16, investments", [
        ("bank statement", r"\b(account statement|statement of account|bank statement)\b"),
        ("salary slip", r"\b(salary slip|pay ?slip|payslip)\b"),
        ("tax", r"\b(form 16|itr|income tax return|form 26as|tds certificate)\b"),
        ("investment", r"\b(mutual fund|demat|folio|sip|fixed deposit|ppf|nps)\b"),
    ]),
    ("resume", "Corporate Resume", "resumes and CVs (security automation, GRC...)", [
        ("", r"\b(curriculum vitae|resume|résumé|professional summary|work experience|career objective)\b"),
    ]),
    ("certificates", "Certificates", "skills, courses, standards (ISO, CISSP, CISA...)", [
        ("standard", r"\b(iso ?\d{4,5}|lead auditor|lead implementer|cissp|cisa|cism|crisc|ceh|oscp|comptia|pmp|itil|ccna|ccnp|aws certified|azure|google cloud certified|cobit|togaf)\b"),
        ("course", r"\b(course completion|completed the course|has successfully completed|certificate of completion|training)\b"),
        ("award", r"\b(certificate of (appreciation|achievement|excellence|merit)|awarded to)\b"),
        ("", r"\b(certificate|certification|certify that|certified)\b"),
    ]),
    ("property", "Property & Home", "rent agreements, sale deeds, property tax, utility bills", [
        ("agreement", r"\b(rent agreement|rental agreement|lease deed|leave and licen[cs]e)\b"),
        ("deed", r"\b(sale deed|gift deed|property card|khata|encumbrance)\b"),
        ("tax", r"\bproperty tax\b"),
        ("utility bill", r"\b(electricity bill|water bill|gas bill|bescom|tata power|adani electricity)\b"),
    ]),
    ("travel", "Travel", "visas, tickets, boarding passes", [
        ("visa", r"\b(visa|immigration)\b"),
        ("ticket", r"\b(boarding pass|e-ticket|pnr|itinerary)\b"),
    ]),
]
FOLDER_NAME = {k: name for k, name, _, _ in FOLDERS}
DESCRIBE = {k: what for k, _, what, _ in FOLDERS}
OTHER = ("other", "Other papers", "family documents that fit nowhere else")
FOLDER_NAME[OTHER[0]], DESCRIBE[OTHER[0]] = OTHER[1], OTHER[2]


def category(text, name=""):
    """(folder key, sub-type) for a document's text and file name, or (None, '') when it's not a family paper."""
    low = f"{name}\n{text}".lower()
    for key, _, _, rules in FOLDERS:
        for sub, pat in rules:
            if re.search(pat, low):
                return key, sub
    return None, ""


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


def _name_pattern(name):
    words = [re.escape(w) for w in re.findall(r"[a-z]+", name.lower()) if len(w) > 1]
    if len(words) < 2:  # a single first name is too easy to mistake: needs a surname or another name
        return None
    forward = r"\b" + r"[\s.,]+".join(words) + r"\b"
    backward = r"\b" + r"[\s.,]+".join(reversed(words)) + r"\b"  # KUMAR AJAY on some IDs
    return re.compile(forward + "|" + backward)


def assign(files, faces_by_id, people, overrides=None):
    """{file id: {"person_id", "folder", "folder_name", "sub", "by"}} for family papers.
    person_id is None for papers of the right kind that match no family member ("Not sure whose")."""
    overrides = overrides or {}
    family = {p["person_id"]: p for p in people.values() if p.get("family")}
    pats = []
    for p in family.values():
        for n in [p.get("name") or ""] + [a for a in re.split(r"[,;\n]", p.get("aliases") or "")]:
            pat = _name_pattern(n.strip())
            if pat:
                pats.append((p["person_id"], pat))
    out = {}
    for f in files:
        if f.get("duplicate_of"):
            continue
        fs = [faces_by_id[i] for i in f["face_ids"] if i in faces_by_id]
        text = f.get("text") or ""
        key, sub = (None, "")
        if f["kind"] == "doc" or (f["kind"] == "photo" and len(text) > 30):
            key, sub = category(text, f["name"])
        if key is None and looks_like_passport_photo(f, fs):
            key, sub = "dna", "passport-size photo"
        ov = overrides.get(f["sha256"])
        if key is None and not ov:
            continue
        who, by = None, ""
        if ov:
            who, by = ov.get("person_id"), "you"
            key = ov.get("folder") or key or OTHER[0]
            if who is None and ov.get("not_family"):
                continue  # you said: not a family paper
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
        out[f["id"]] = {"person_id": who, "folder": key, "folder_name": FOLDER_NAME.get(key, OTHER[1]), "sub": sub, "by": by}
    return out


def safe(name):
    return re.sub(r'[\\/:*?"<>|]+', "-", name).strip(" .") or "Unnamed"
