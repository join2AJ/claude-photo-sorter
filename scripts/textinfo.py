"""Make sense of text read from screenshots and documents: which company or app, what kind of
screen or document, money amounts, transaction ids. Simple word rules, no internet."""
import re

COMPANIES = {
    "Bank": ["HDFC", "ICICI", "SBI", "State Bank of India", "Axis Bank", "Kotak", "Yes Bank", "IDFC", "PNB",
             "Punjab National Bank", "Bank of Baroda", "Canara", "IndusInd", "AU Small Finance", "Federal Bank",
             "Union Bank", "Bank of India", "RBL", "HSBC", "Citibank", "Standard Chartered", "Chase", "Wells Fargo",
             "Bank of America", "Barclays"],
    "Payments": ["Google Pay", "GPay", "PhonePe", "Paytm", "BHIM", "Amazon Pay", "PayPal", "CRED", "Razorpay",
                 "MobiKwik", "Venmo", "Cash App", "Wise", "Revolut", "Stripe"],
    "Shopping": ["Amazon", "Flipkart", "Myntra", "Meesho", "Ajio", "Nykaa", "BigBasket", "Blinkit", "Zepto",
                 "Instamart", "JioMart", "DMart", "Tata CLiQ", "Croma", "Reliance Digital", "IKEA", "eBay", "Walmart",
                 "Etsy", "Shopify", "Decathlon", "Lenskart", "FirstCry", "Snapdeal"],
    "Food": ["Swiggy", "Zomato", "Domino's", "McDonald's", "KFC", "Starbucks", "Pizza Hut", "Burger King", "Subway",
             "EatSure", "Uber Eats", "DoorDash"],
    "Travel": ["Uber", "Ola", "Rapido", "IRCTC", "MakeMyTrip", "Goibibo", "IndiGo", "Air India", "Vistara",
               "SpiceJet", "Akasa", "Booking.com", "Airbnb", "redBus", "Cleartrip", "Yatra", "ixigo", "Agoda",
               "Expedia", "OYO", "Emirates", "Google Maps"],
    "Social": ["WhatsApp", "Instagram", "Facebook", "Twitter", "LinkedIn", "YouTube", "Snapchat", "Telegram",
               "Reddit", "Threads", "Pinterest", "Quora", "Discord", "Signal", "TikTok", "Moj", "ShareChat"],
    "Telecom & bills": ["Jio", "Airtel", "Vodafone", "BSNL", "Tata Power", "BESCOM", "Adani Electricity",
                        "Tata Play", "ACT Fibernet", "Hathway"],
    "Streaming": ["Netflix", "Hotstar", "Prime Video", "Spotify", "JioCinema", "SonyLIV", "ZEE5", "Apple Music",
                  "YouTube Music", "Gaana", "JioSaavn"],
    "Investing & insurance": ["Zerodha", "Kite", "Groww", "Upstox", "Angel One", "Coin", "Smallcase", "LIC",
                              "Policybazaar", "HDFC Life", "ICICI Prudential", "SBI Life", "Star Health",
                              "Coinbase", "Binance", "WazirX", "Robinhood"],
    "Work & email": ["Gmail", "Outlook", "Zoom", "Microsoft Teams", "Slack", "Google Meet", "Notion", "Jira",
                     "Google Drive", "Dropbox", "Excel", "Naukri", "Indeed", "ChatGPT", "Claude"],
    "Government": ["Aadhaar", "UIDAI", "Income Tax", "DigiLocker", "Passport Seva", "EPFO", "GST", "mAadhaar",
                   "Parivahan", "CoWIN", "UMANG"],
}
_PATTERNS = [(name, sector, re.compile(r"(?<![A-Za-z])" + re.escape(name) + r"(?![A-Za-z])", re.I if len(name) > 4 else 0))
             for sector, names in COMPANIES.items() for name in names]

MONEY = re.compile(r"(₹|Rs\.?|INR|\$|USD|€|EUR|£|GBP)\s?([0-9]{1,3}(?:[,][0-9]{2,3})+(?:\.[0-9]{1,2})?|[0-9]+(?:\.[0-9]{1,2})?)", re.I)
TXN = re.compile(r"(UPI\s*(?:Ref(?:erence)?|transaction)\s*(?:No\.?|ID|number)?|UTR(?:\s*No\.?)?|Transaction\s*ID|Txn\s*ID|"
                 r"Order\s*(?:ID|No\.?|number)|Reference\s*(?:No\.?|ID)|Invoice\s*(?:No\.?|number)|PNR(?:\s*No\.?)?|Booking\s*ID)"
                 r"\s*[:#.\-]?\s*([A-Z0-9][A-Z0-9\-]{5,})", re.I)
OUT_WORDS = r"\b(paid|debited|sent|payment to|paid to|spent|withdrawn|purchase|you paid|order total|amount due|total)\b"
BARE = re.compile(r"(?<![\d.,])([0-9]{1,3}(?:,[0-9]{2,3})+(?:\.[0-9]{2})?|[0-9]+\.[0-9]{2})(?![\d,])")  # 1,250.00 with the symbol misread
IN_WORDS = r"\b(received|credited|refund|cashback|deposited|salary|received from)\b"

DOC_TYPES = [
    ("Bank statement", r"\b(account statement|statement of account|bank statement|opening balance|closing balance)\b"),
    ("Salary slip", r"\b(salary slip|pay ?slip|payslip|net pay|gross salary|earnings and deductions)\b"),
    ("Bill / invoice", r"\b(tax invoice|invoice|bill of supply|receipt|bill no|amount payable|gstin|total amount)\b"),
    ("ID document", r"\b(aadhaar|uidai|permanent account number|income tax department|passport|driving licen[cs]e|voter id|election commission)\b"),
    ("Insurance", r"\b(insurance|policy (no|number)|premium|sum assured|insured)\b"),
    ("Ticket / booking", r"\b(boarding pass|e-ticket|pnr|booking (id|confirmed|confirmation)|itinerary|check-in)\b"),
    ("Tax", r"\b(form 16|itr|income tax return|tds|form 26as)\b"),
    ("Resume", r"\b(curriculum vitae|resume|work experience|education)\b"),
    ("Certificate", r"\b(certificate|certify that|awarded to)\b"),
    ("Agreement", r"\b(agreement|contract|lease|terms and conditions|hereinafter)\b"),
    ("Medical", r"\b(prescription|diagnosis|patient|hospital|lab report|blood test|doctor)\b"),
    ("Study notes", r"\b(chapter|lecture|assignment|exam|syllabus|university|semester)\b"),
]

SCREEN_TYPES = [
    ("Payment", r"\b(upi|paid to|payment successful|transaction successful|debited|credited|amount|₹|rs\.)"),
    ("Order / shopping", r"\b(order (placed|confirmed|id)|delivered|add to cart|buy now|track order|out for delivery)\b"),
    ("Ticket / booking", r"\b(boarding pass|pnr|booking|e-ticket|check-in|seat)\b"),
    ("Chat", r"\b(typing|online|last seen|message|reply|whatsapp|telegram)\b|\b\d{1,2}:\d{2}\s?(am|pm)\b.*\n.*\b\d{1,2}:\d{2}\s?(am|pm)\b"),
    ("Social post", r"\b(likes?|followers|following|comments?|reels?|retweet|repost|subscribe|views)\b"),
    ("Map / directions", r"\b(directions|route|km|mins?|arrive|navigation|google maps)\b"),
    ("Email", r"\b(inbox|subject:|from:|to:|cc:|unsubscribe|gmail|outlook)\b"),
    ("Code / work", r"\b(def |function|import |error|exception|console|dashboard|meeting)\b"),
]


def companies(text):
    """[(company, sector)] most mentioned first."""
    hits = {}
    for name, sector, pat in _PATTERNS:
        n = len(pat.findall(text))
        if n:
            hits[name] = (n, sector)
    # "Amazon Pay" also matches "Amazon": keep the longer name
    for a in list(hits):
        if any(a != b and a.lower() in b.lower() for b in hits):
            hits.pop(a, None)
    return [(k, v[1]) for k, v in sorted(hits.items(), key=lambda kv: -kv[1][0])]


def money(text):
    """All amounts, the main amount, its currency, money in or out, transaction ids."""
    found = []
    for cur, num in MONEY.findall(text):
        try:
            found.append((cur.upper().replace("RS.", "INR").replace("RS", "INR").replace("₹", "INR"), float(num.replace(",", ""))))
        except ValueError:
            pass
    found = [(c, v) for c, v in found if v > 0]
    if not found:  # text readers often miss the ₹ sign: take plain money-looking numbers instead
        for num in BARE.findall(re.sub(r"\b\d{1,2}:\d{2}\b", " ", text)):
            try:
                found.append(("", float(num.replace(",", ""))))
            except ValueError:
                pass
    main = None
    if found:
        low = text.lower()
        for m in re.finditer(OUT_WORDS + "|" + IN_WORDS, low):  # first amount right after a money word
            after = MONEY.search(text, m.end())
            if after and after.start() - m.end() < 80:
                main = after
                break
        if main:
            c, v = main.group(1).upper(), float(main.group(2).replace(",", ""))
            main = (c.replace("RS.", "INR").replace("RS", "INR").replace("₹", "INR"), v)
        else:
            main = max(found, key=lambda cv: cv[1])
    low = text.lower()
    direction = "out" if re.search(OUT_WORDS, low) else "in" if re.search(IN_WORDS, low) else ""
    if re.search(IN_WORDS, low) and not re.search(r"\b(paid|debited|sent|paid to)\b", low):
        direction = "in"
    txns = list(dict.fromkeys(f"{k.strip()} {v}" for k, v in TXN.findall(text)))[:5]
    return {"amounts": found, "main": main, "direction": direction, "txn_ids": txns}


def classify(text, rules):
    low = text.lower()
    for name, pat in rules:
        if re.search(pat, low):
            return name
    return ""


def doc_type(text):
    return classify(text, DOC_TYPES) or ("Other" if text.strip() else "")


def screen_type(text):
    return classify(text, SCREEN_TYPES) or ("App screen" if text.strip() else "")
