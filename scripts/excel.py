"""Write everything into one Excel file, with tables you can filter and sort.

  python scripts/excel.py                     -> "<sorted folder>/Library details.xlsx" (or work/ before sorting)
  python scripts/excel.py "/path/out.xlsx"

Sheets: Summary, All files, People, Faces, Screenshots, Money, Documents, Videos.
Faces and people get their picture in the sheet. Ages, genders and emotions are estimates.
"""
import os, sys
from collections import Counter
from datetime import datetime

from openpyxl import Workbook
from openpyxl.drawing.image import Image as XLImage
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.table import Table, TableStyleInfo

sys.path.insert(0, os.path.dirname(__file__))
from common import DATA, WORK
from details import NO_FACE, fid, library, pid

INK, MUTED, ACCENT, SOFT, LINE = "1F2937", "6B7280", "C2412F", "FBF3EE", "E5E7EB"
MAX_PICS = 3000  # pictures make the file big: only the first ones get one
H1 = Font(name="Calibri", size=22, bold=True, color=INK)
H2 = Font(name="Calibri", size=13, bold=True, color=INK)
SMALL = Font(name="Calibri", size=10, color=MUTED)
BIG = Font(name="Calibri", size=24, bold=True, color=ACCENT)
LINK = Font(color="1D4ED8", underline="single")
WRAP = Alignment(wrap_text=True, vertical="top")
TOP = Alignment(vertical="center")


def mb(b):
    return round(b / 1e6, 2)


def link(cell, path, text=None):
    if path:
        cell.value = text or path
        cell.hyperlink = "file://" + path.replace(" ", "%20")
        cell.font = LINK


def table(ws, name, headers, rows, widths, style="TableStyleMedium2", pics=None, pic_col=None, row_h=None):
    """A real Excel table: banded rows, filter buttons, frozen header."""
    ws.append(headers)
    for r in rows:
        ws.append([v if not isinstance(v, (list, tuple)) else ", ".join(map(str, v)) for v in r])
    last = get_column_letter(len(headers))
    if rows:
        t = Table(displayName=name, ref=f"A1:{last}{len(rows) + 1}")
        t.tableStyleInfo = TableStyleInfo(name=style, showRowStripes=True)
        ws.add_table(t)
    ws.freeze_panes = "B2" if pic_col is None else get_column_letter(pic_col + 1) + "2"
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    for row in ws.iter_rows(min_row=2, max_row=len(rows) + 1):
        for c in row:
            c.alignment = TOP
    ws.row_dimensions[1].height = 30
    for c in ws[1]:
        c.alignment = Alignment(vertical="center", wrap_text=True)
    if pics and pic_col:
        for n, path in enumerate(pics[:MAX_PICS], 2):
            if path and os.path.exists(path):
                img = XLImage(path)
                img.width = img.height = row_h - 4
                ws.add_image(img, f"{get_column_letter(pic_col)}{n}")
                ws.row_dimensions[n].height = row_h * 0.75
    return ws


def build(out):
    L = library()
    files, faces, people = L["files"], L["faces"], L["people"]
    wb = Workbook()

    # ---- All files
    ws = wb.active
    ws.title = "All files"
    hdr = ["Preview", "File ID", "Name", "Type", "Folder", "Date taken", "Camera / phone", "People in it", "Person IDs",
           "Face IDs", "Faces", "Ages (est.)", "Genders (est.)", "Emotions (est.)", "Things in it", "Screenshot",
           "Company / app", "Kind of content", "Amount", "Currency", "Money in/out", "Transaction / order IDs",
           "Size (MB)", "Width", "Height", "Length (s)", "GPS", "Duplicate of", "Original file", "Sorted copy"]
    face_by_id = {f["face_id"]: f for f in faces}
    rows, pics = [], []
    for f in files:
        fs = [face_by_id[i] for i in f["face_ids"] if i in face_by_id]
        rows.append(["", f["id"], f["name"], f["kind"], f["folder"], f["taken"], f["camera"], f["people"],
                     ", ".join(pid(i) for i in f["people_ids"]) or NO_FACE, ", ".join(fid(i) for i in f["face_ids"]),
                     len(f["face_ids"]), ", ".join(x["age"] or "?" for x in fs), ", ".join(x["gender"] or "?" for x in fs),
                     ", ".join(x["emotion"] or "?" for x in fs), f["tags"], "yes" if f["screenshot"] else "",
                     f["company"], f["content"], f["amount"], f["currency"], f["direction"], f["txn_ids"],
                     mb(f["bytes"]), f["width"], f["height"], round(f["duration"], 1) if f["duration"] else None,
                     f"{f['lat']:.5f}, {f['lon']:.5f}" if f["lat"] is not None else "", f["duplicate_of"], "", ""])
        pics.append(os.path.join(DATA, "mini", f"{f['id']}.jpg"))
    table(ws, "AllFiles", hdr, rows, [9, 8, 28, 8, 22, 16, 18, 30, 16, 18, 7, 14, 14, 16, 30, 10, 20, 18, 11, 9, 10, 26,
                                      9, 7, 7, 9, 20, 20, 40, 40], pics=pics, pic_col=1, row_h=48)
    for n, f in enumerate(files, 2):
        link(ws.cell(n, 29), f["path"])
        link(ws.cell(n, 30), f["copy"])
        if f["lat"] is not None:
            link(ws.cell(n, 27), None)
            ws.cell(n, 27).value = f"{f['lat']:.5f}, {f['lon']:.5f}"
            ws.cell(n, 27).hyperlink = f"https://maps.google.com/?q={f['lat']},{f['lon']}"
            ws.cell(n, 27).font = LINK
        ws.cell(n, 19).number_format = "#,##0.00"

    # ---- People
    ws = wb.create_sheet("People")
    plist = sorted(people.values(), key=lambda p: (-(p["photos"] + p["videos"]), p["person_id"]))
    hdr = ["Face", "Person ID", "Name", "Registered", "Mobile", "Mobile verified", "Consent", "Photos", "Videos",
           "Faces seen", "Age (est.)", "Gender (est.)", "Usual emotion", "Emotions seen", "First seen", "Last seen", "File IDs"]
    rows = [["", pid(p["person_id"]), p["display"], "yes" if p["name"] else "no", p["mobile"] or "",
             "yes" if p["mobile_verified"] else "no", p["consent"], p["photos"], p["videos"], p["faces"], p["age_est"],
             p["gender_est"], p["emotion_usual"], p["emotion_mix"], p["first"], p["last"],
             ", ".join(map(str, p["files"][:200]))] for p in plist]
    table(ws, "People", hdr, rows, [11, 10, 20, 11, 15, 10, 11, 8, 8, 9, 9, 11, 13, 26, 16, 16, 40],
          style="TableStyleMedium7", pics=[os.path.join(DATA, "faces", f"{p['cover']}.jpg") if p["cover"] else None for p in plist],
          pic_col=1, row_h=64)

    # ---- Faces
    ws = wb.create_sheet("Faces")
    hdr = ["Face", "Face ID", "Person ID", "Name", "File", "File IDs", "Video time (s)", "Age (est.)", "Age years (est.)",
           "Gender (est.)", "Gender sure", "Emotion (est.)", "Emotion sure", "Face size (px)", "Detection sure", "Moved by hand"]
    rows = [["", fid(f["face_id"]), pid(f["person_id"]) if f["person_id"] else "", f["person"], f["file"],
             ", ".join(map(str, f["file_ids"])), f["frame_s"], f["age"] or "too small", f["age_years"], f["gender"] or "",
             f["gender_conf"], f["emotion"] or "", f["emotion_conf"], f"{f['w']}×{f['h']}", f["score"], "yes" if f["manual"] else ""]
            for f in faces]
    table(ws, "Faces", hdr, rows, [11, 10, 10, 18, 28, 10, 10, 11, 10, 11, 9, 12, 9, 11, 9, 10], style="TableStyleMedium4",
          pics=[os.path.join(DATA, "faces", f"{f['face_id']}.jpg") for f in faces], pic_col=1, row_h=64)
    for row in ws.iter_rows(min_row=2, min_col=11, max_col=15):
        for c in row:
            if isinstance(c.value, float) and c.value <= 1:
                c.number_format = "0%"

    # ---- Screenshots
    ws = wb.create_sheet("Screenshots")
    shots = [f for f in files if f["screenshot"]]
    hdr = ["Preview", "File ID", "Name", "Date", "Company / app", "Sector", "What it shows", "Amount", "Currency",
           "Money in/out", "Transaction / order IDs", "Things in it", "Text (start)", "Folder", "Original file"]
    rows = [["", f["id"], f["name"], f["taken"], f["company"], f["sector"], f["content"], f["amount"], f["currency"],
             f["direction"], f["txn_ids"], f["tags"], f["text"][:400], f["folder"], ""] for f in shots]
    table(ws, "Screenshots", hdr, rows, [9, 8, 28, 16, 22, 16, 16, 11, 9, 10, 26, 22, 60, 22, 40], style="TableStyleMedium3",
          pics=[os.path.join(DATA, "mini", f"{f['id']}.jpg") for f in shots], pic_col=1, row_h=48)
    for n, f in enumerate(shots, 2):
        ws.cell(n, 13).alignment = WRAP
        link(ws.cell(n, 15), f["path"])

    # ---- Money
    ws = wb.create_sheet("Money")
    money = sorted((f for f in files if f["amount"] and not f["duplicate_of"]), key=lambda f: f["taken"] or "")
    hdr = ["Date", "Company / app", "Sector", "What", "Amount", "Currency", "In/out", "Signed amount",
           "Transaction / order IDs", "From", "File ID", "Name", "Original file"]
    rows = [[f["taken"], f["company"], f["sector"], f["content"], f["amount"], f["currency"], f["direction"],
             (-f["amount"] if f["direction"] == "out" else f["amount"] if f["direction"] == "in" else None), f["txn_ids"],
             "screenshot" if f["screenshot"] else f["kind"], f["id"], f["name"], ""] for f in money]
    table(ws, "Money", hdr, rows, [16, 24, 18, 18, 12, 9, 8, 13, 30, 11, 8, 28, 40], style="TableStyleMedium6")
    for n, f in enumerate(money, 2):
        for c in (5, 8):
            ws.cell(n, c).number_format = "#,##0.00;[Red]-#,##0.00"
        link(ws.cell(n, 13), f["path"])
    if money:
        t = len(money) + 3
        ws.cell(t, 4, "Total (filtered rows)").font = Font(bold=True)
        ws.cell(t, 5, f"=SUBTOTAL(109,E2:E{len(money) + 1})").number_format = "#,##0.00"
        ws.cell(t, 8, f"=SUBTOTAL(109,H2:H{len(money) + 1})").number_format = "#,##0.00;[Red]-#,##0.00"
        ws.cell(t + 1, 4, "Amounts are read from screenshots and documents: check important ones.").font = SMALL

    # ---- Documents
    ws = wb.create_sheet("Documents")
    docs = [f for f in files if f["kind"] == "doc"]
    hdr = ["Preview", "File ID", "Name", "Type", "Kind of document", "Company", "Amount", "Currency", "Reference IDs",
           "Size (MB)", "Folder", "Text (start)", "Original file"]
    rows = [["", f["id"], f["name"], f["ext"][1:].upper(), f["content"], f["company"], f["amount"], f["currency"],
             f["txn_ids"], mb(f["bytes"]), f["folder"], f["text"][:400], ""] for f in docs]
    table(ws, "Documents", hdr, rows, [9, 8, 30, 7, 18, 20, 11, 9, 26, 9, 24, 60, 40], style="TableStyleMedium5",
          pics=[os.path.join(DATA, "mini", f"{f['id']}.jpg") for f in docs], pic_col=1, row_h=48)
    for n, f in enumerate(docs, 2):
        ws.cell(n, 12).alignment = WRAP
        link(ws.cell(n, 13), f["path"])

    # ---- Videos
    ws = wb.create_sheet("Videos")
    vids = [f for f in files if f["kind"] == "video"]
    hdr = ["Preview", "File ID", "Name", "Date", "Length (s)", "Camera / phone", "People in it", "Person IDs", "Things in it",
           "Size (MB)", "Folder", "GPS", "Original file"]
    rows = [["", f["id"], f["name"], f["taken"], round(f["duration"] or 0, 1), f["camera"], f["people"],
             ", ".join(pid(i) for i in f["people_ids"]) or NO_FACE, f["tags"], mb(f["bytes"]), f["folder"],
             f"{f['lat']:.5f}, {f['lon']:.5f}" if f["lat"] is not None else "", ""] for f in vids]
    table(ws, "Videos", hdr, rows, [9, 8, 28, 16, 9, 18, 30, 16, 26, 9, 22, 20, 40], style="TableStyleMedium9",
          pics=[os.path.join(DATA, "mini", f"{f['id']}.jpg") for f in vids], pic_col=1, row_h=48)
    for n, f in enumerate(vids, 2):
        link(ws.cell(n, 13), f["path"])

    # ---- Summary (first sheet)
    ws = wb.create_sheet("Summary", 0)
    ws.sheet_view.showGridLines = False
    ws.column_dimensions["A"].width = 3
    for c, w in zip("BCDEFGHI", (24, 14, 4, 24, 14, 4, 24, 14)):
        ws.column_dimensions[c].width = w
    ws["B2"] = "Library details"
    ws["B2"].font = H1
    ws["B3"] = f"{L['source'].get('source') or ''}   ·   made {datetime.now():%d %b %Y, %H:%M}"
    ws["B3"].font = SMALL
    kinds = Counter(f["kind"] for f in files)
    named = sum(1 for p in people.values() if p["name"])
    kpis = [("Files", len(files)), ("Photos", kinds["photo"]), ("Videos", kinds["video"]), ("Documents", kinds["doc"]),
            ("Screenshots", len(shots)), ("People", len(people)), ("Faces", len(faces)),
            ("Named people", named), ("With no face (un)", sum(1 for f in files if f["people"] == NO_FACE))]
    fill, border = PatternFill("solid", fgColor=SOFT), Border(bottom=Side(style="thin", color=LINE))
    for n, (label, val) in enumerate(kpis):
        col, row = 2 + (n % 3) * 3, 5 + (n // 3) * 3
        a, b = ws.cell(row, col, label), ws.cell(row + 1, col, val)
        a.font, b.font = SMALL, BIG
        for c in (a, b):
            c.fill = fill
        ws.cell(row, col + 1).fill = ws.cell(row + 1, col + 1).fill = fill
    r = 15

    def block(title, pairs, col=2):
        nonlocal r
        ws.cell(r, col, title).font = H2
        for i, (k, v) in enumerate(pairs, 1):
            ws.cell(r + i, col, k).border = border
            ws.cell(r + i, col + 1, v).border = border
        return len(pairs) + 2

    folders = Counter(f["folder"] or "Not sorted yet" for f in files).most_common()
    top_people = [(p["display"], p["photos"] + p["videos"]) for p in plist[:12]]
    comps = Counter(c.strip() for f in files for c in f["company"].split(",") if c.strip()).most_common(12)
    h = max(block("Folders", folders), block("People seen most", top_people, 5), block("Companies & apps", comps, 8))
    r += h
    totals = Counter()
    for f in money:
        if f["direction"] in ("in", "out"):
            totals[(f["currency"] or "?", f["direction"])] += f["amount"]
    if totals:
        block("Money found (estimate)", [(f"{'In' if d == 'in' else 'Out'} ({c if c != '?' else 'currency not read'})", round(v, 2))
                                         for (c, d), v in sorted(totals.items())])
        for i in range(len(totals)):
            ws.cell(r + 1 + i, 3).number_format = "#,##0.00"
        r += len(totals) + 2
    ws.cell(r, 2, "Ages, genders and emotions are guesses by a computer model and are often wrong. "
                  "Amounts are read from pictures: check important ones.").font = SMALL
    ws.cell(r + 1, 2, "This file contains personal information (faces, names, phone numbers, money). Keep it private.").font = SMALL

    for s in wb.worksheets[1:]:
        s.sheet_properties.tabColor = {"All files": "1F2937", "People": ACCENT, "Faces": "B45309", "Screenshots": "2563EB",
                                       "Money": "15803D", "Documents": "7C3AED", "Videos": "0E7490"}.get(s.title)
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    wb.save(out)
    return out


def default_out():
    from common import load
    src = load(os.path.join(DATA, "source.json"), {})
    return os.path.join(src.get("sorted") or WORK, "Library details.xlsx")


if __name__ == "__main__":
    out = build(sys.argv[1] if len(sys.argv) > 1 else default_out())
    print(f"PROGRESS 1 1\nExcel saved: {out}", flush=True)
