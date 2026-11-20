# Photo sorter: instructions for the agent

This repo sorts a camera roll (photos, videos and documents) into folders, finds duplicates, recognises people, reads screenshots and bills, and shows it all on a local dashboard with a Details page and an Excel export. Everything runs on the person's computer with free open-source models. The person you're helping has probably never used Claude Code or a terminal. Do the technical work yourself, keep messages short, and use plain words ("folder", not "directory").

## Ground rules (never break these)

1. **Never move, rename or delete the user's original photos.** The tool only reads them and makes sorted copies. If they want duplicates deleted, show them `duplicates.csv` and let them do it.
2. **Ask before anything that costs money.** Jev (TypeSafe) is billed per file. Run `label_jev.py --estimate`, show the files and tokens, and wait for a yes.
3. **Keep their photos private.** Never commit anything in `dashboard/data/`, `dashboard/peek/`, `work/`, `inbox/`, `models/`, `*.xlsx` or `.env`. `work/library.db` holds faces, names and mobile numbers: never send it anywhere.
4. **Faces are sensitive.** Only the owner names people or links a mobile number to a face. Age, gender and emotion are estimates: say so.
5. One question at a time, with numbered options they can answer with a number.

## When someone gives you this repo's link (the usual case)

They pasted something like "set up https://github.com/join2AJ/claude-photo-sorter". Do this without asking:

1. **Download it.** If you're not already inside this repo: `git clone https://github.com/join2AJ/claude-photo-sorter.git ~/claude-photo-sorter` (if that folder exists, `git -C ~/claude-photo-sorter pull` instead), then work from that folder.
2. **Set up.** Run `./setup.sh` (installs packages and downloads about 135 MB of free models into `models/`). If Python is missing, ask them to run `xcode-select --install` and wait. If ffmpeg is missing and `brew` exists, offer `brew install ffmpeg` (videos just get grey previews without it).
3. **Open the dashboard.** Run `./start.sh` in the background (it keeps running and opens the browser at http://127.0.0.1:8765).
4. **Tell them, in about three lines:**
   - The dashboard is open in their browser.
   - Click **Choose folder** (or **Add a zip file or a share link**) and pick their photos, then pick where the sorted copies go, then **Start sorting**.
   - Afterwards **Details & people** shows everything found, lets them name people, and **Download Excel** gives the full sheet.
   - It runs by itself and shows progress. Folders can be changed under **Advanced**. To open it again later: double-click `Open Photo Sorter.command` in `~/claude-photo-sorter`, or ask you to "open my photo sorter".
5. Stay available. If they ask questions, answer from what you see in `dashboard/data/` and the server's `/api/state`.

If they don't have an export yet, explain:
- **Google Photos:** takeout.google.com, select only Google Photos, download, unzip into one folder.
- **iPhone / Apple Photos:** in Photos on the Mac, select all, File > Export > Export Unmodified Originals, into a new folder.
Never read `Photos Library.photoslibrary` directly.

## What the dashboard does by itself

**Start sorting** runs everything in order and shows live progress, a timer and a time estimate:

0. Import (only for a zip or link): `scripts/ingest.py` unpacks or downloads into `inbox/`. Google Photos, iCloud and WeTransfer links can't be downloaded: tell them to use "Download all" and add the zip.
1. Scan: inventory of photos, videos and documents, sha256, previews. Zips inside the folder are unpacked too.
2. Duplicates: identical files and look-alikes (blank frames and documents are never look-alikes).
3. Look inside: `scripts/analyze.py` finds faces (person numbers P0001, face numbers F00001), estimates age/gender/emotion, things in the picture, reads text in screenshots and documents, company/app, amounts, transaction ids, dates, camera, GPS. Results live in `work/library.db`, per file content.
4. Sort: `scripts/label_local.py` (free, default). Under **Advanced** they can pick Claude (`label_claude.py`, uses their plan) or Jev (paid).
5. Build folders: copies into `<their folder> (sorted)` (for imports: `~/Pictures/<name> (sorted)`).
6. Excel: `scripts/excel.py` writes `Library details.xlsx` into the sorted folder.

The **Details & people** page (`dashboard/details.html`) has tabs for Everything, People, Faces, Screenshots, Money, Documents and Videos. On People they can name someone, add a mobile number, set consent (pending / yes / no), choose who to show or hide their face from, move a wrong face, and merge two people. Mobile verification, logins and face blurring are part 2 (not built yet): consent and share lists are only recorded for now.

## If they'd rather do it in this chat

| Step | Command |
|---|---|
| Scan | `.venv/bin/python scripts/scan.py "<photos folder>" [--limit 200]` |
| Import a zip or link | `.venv/bin/python scripts/ingest.py "<zip or link>"` (prints `FOLDER <path>`) |
| Duplicates | `.venv/bin/python scripts/dupes.py` (check `work/duplicates.jpg`) |
| Look inside | `.venv/bin/python scripts/analyze.py` |
| Labels (free) | `.venv/bin/python scripts/label_local.py` |
| Sample sheets | `.venv/bin/python scripts/sheets.py --sample` (look at `work/sample/` to suggest folders) |
| Labels (Claude) | `.venv/bin/python scripts/label_claude.py` |
| Labels (Jev, paid) | `.venv/bin/python scripts/label_jev.py --estimate`, then without `--estimate` |
| Build folders | `.venv/bin/python scripts/apply.py "<output folder>"` |
| Excel | `.venv/bin/python scripts/excel.py` |

The open dashboard refreshes itself when these run.

**Choosing folders.** Folders live in `categories.json` (`key`, `kind` photo or video, `label`, `emoji`, `rule`). The `rule` is what the model reads. Offer: 1) the standard folders, 2) folders you suggest after looking at `work/sample/` (a creator gets "Content analytics" and "Talking heads", a parent gets "Kids" and "School"), or 3) their own list. Keep at least one photo and one video folder, and make the last folder of each kind a catch-all.

**Labelling yourself instead of `label_claude.py`.** Run `sheets.py`; each sheet in `work/sheets/` shows 30 previews tagged with ids. `VIDEO` tags need a video folder. Write `work/labels/<name>.json` as `{"id": "key"}` for every id. Use subagents for big libraries.

## If something breaks

- Port 8765 busy: `PORT=8766 ./start.sh`.
- "claude command not found" during sorting: Claude Code isn't on PATH for the server. Restart with `./start.sh` from a terminal where `claude` works, or pick Jev under Advanced.
- A batch failed: press Start sorting again. Finished batches are kept.
- Models missing or a download failed: `.venv/bin/python scripts/models.py`.
- Text reader fails to install on a very new Python: `rapidocr-onnxruntime` supports up to Python 3.12; install Python 3.12 (`brew install python@3.12`) and rerun `./setup.sh`.
- HEIC photos fail to open: `.venv/bin/pip install -U pillow-heif`.
- Jev 401: the key in `.env` is wrong. Jev 400 "Invalid image dimensions": leave `JEV_MODEL` unset.
