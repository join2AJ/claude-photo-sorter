# Photo sorter

Point it at your camera roll, a zip file or a share link. It looks inside every photo, video and document **on your own computer**, sorts them into folders, finds duplicates, recognises the people in them, reads screenshots and bills, and gives you a website and an Excel file with every detail.

![The dashboard sorting a camera roll](docs/preview.gif)

<sub>The demo above uses drawn placeholder images, not real photos.</sub>

- **Brings files in from anywhere**: a folder, a zip (Google Takeout zips too), or a Google Drive, Dropbox or OneDrive share link.
- **Sorts photos, videos and documents** into folders like Selfies, Food, Travel, Screenshots, Talking videos, Bills & statements, IDs & certificates.
- **Finds people**: every face gets its own number (`F00001`), and the same person in different photos and videos gets one person number (`P0001`). Name them, add a mobile number, record whether they agree to share. Files with no face are marked `un`.
- **Estimates age, gender and emotion** for each clear face (guesses, often wrong, and marked as estimates).
- **Reads screenshots and documents**: the company or app (HDFC, Google Pay, Amazon, Swiggy, Instagram…), what kind of screen it is (payment, order, chat, ticket…), amounts, money in or out, UPI / order / invoice numbers.
- **Finds duplicates**: identical copies, burst shots and re-saved screenshots go to a `_Review` folder.
- **Excel file** with Summary, All files, People (with face pictures), Faces, Screenshots, Money, Documents and Videos sheets.
- **Free and private.** Everything runs on your computer with open-source models. Nothing is uploaded. Your originals are never moved, renamed or deleted.

## Start here (no coding needed)

You need a Mac (Windows and Linux work too) and about 1.5 GB of free space for the tools.

**1. Install Claude Code** from [claude.com/claude-code](https://claude.com/claude-code). Open the **Terminal** app (press `⌘ Space`, type *Terminal*, press Enter), type `claude` and press Enter.

**2. Paste this to Claude:**

```
Set up and open https://github.com/join2AJ/claude-photo-sorter
```

Claude downloads it, sets it up and opens the dashboard in your browser. Claude is only used to set things up; the sorting itself is free and runs on your computer.

**3. In the dashboard:**

1. **Choose folder**, or **Add a zip file or a share link instead**.
2. Pick where the sorted copies should go.
3. Press **Start sorting**.

It shows how long it usually takes, then works on its own while you watch every file fly into its folder. Afterwards press **Details & people** to see everything it found, name people, and download the Excel file.

<details>
<summary>Don't have your photos on your computer yet?</summary>

- **Google Photos:** go to [takeout.google.com](https://takeout.google.com), select only Google Photos and download. Add the zip files directly, no need to unzip.
- **iPhone or Apple Photos:** in Photos on your Mac, select all, then File > Export > Export Unmodified Originals, into a new folder.
- **A shared Google Photos album, iCloud link or WeTransfer:** open it, use its **Download all** button, then add the zip here. (These sites don't allow automatic downloads.)
- **Google Drive / Dropbox / OneDrive:** paste the share link. It must be shared with "Anyone with the link".
</details>

## Using it again

The dashboard lives at **http://127.0.0.1:8765** while it's running. To open it again later, either:

- double-click **Open Photo Sorter.command** in the `claude-photo-sorter` folder (it's in your home folder), or
- tell Claude "open my photo sorter".

Press **New sort** to sort a different folder. People you named are remembered, so the same faces in a new folder (another event, another phone) get the same name.

## The dashboard

| | |
|---|---|
| **Start sorting / Replay** | Before sorting: asks for anything missing, then starts. After sorting: replays the animation (good for screen recording). Add `?d=20` to the address for a slower take. |
| **Details & people** | Everything it found, in tabs: Everything, People, Faces, Screenshots, Money, Documents, Videos. Search, sort any column, click a picture to see it with every face marked and named. |
| **People** (in Details) | Click someone to name them, add their mobile number, set whether others may see their face in group photos, and choose who to show or hide their face from. Move a wrong face to the right person, or **Merge people** when one person was split in two. |
| **Download Excel** | The whole library as a formatted Excel file. A copy is also saved in the sorted folder as `Library details.xlsx`. |
| **Advanced** (in the setup card) | See and change the folders. Choose who picks the folders: **This computer** (free, default), Claude, or Jev. Try 200 files first. |
| **Click a folder** | Browse it. Click a photo to see it full size and **Move to** another folder if it's wrong. |
| **Edit folders** | Rename folders and describe what goes in each. |

Want a look without your own photos? Run `./start.sh --demo`.

## How it works

1. **Import**: zips are unpacked (safely, once) into `inbox/`; links are downloaded there.
2. **Scan**: makes a small preview of every file and a fingerprint to spot copies.
3. **Duplicates**: compares fingerprints, with a pixel check for screenshots. Blank and black frames are never called duplicates.
4. **Look inside** (`scripts/analyze.py`), with free open-source models:

   | What | Model | Licence |
   |---|---|---|
   | Finding faces | YuNet (OpenCV Zoo) | MIT |
   | Same person across photos | SFace (OpenCV Zoo) | Apache 2.0 |
   | Age and gender estimates | GoogLeNet age/gender (ONNX Model Zoo) | Apache 2.0 |
   | Emotion | FER+ (ONNX Model Zoo) | Apache 2.0 |
   | Things in the picture | MobileNetV2, 1,000 everyday things | Apache 2.0 |
   | Text in screenshots and scans | RapidOCR | Apache 2.0 |
   | Dates, camera, GPS | Photo EXIF data, video metadata, Google Takeout files | |
   | Documents | PDF, Word, Excel, PowerPoint, text files | |

   Videos are checked every few seconds; the same person in many frames counts once.
5. **Sort**: picks a folder from what it found (faces, text, company, things in the picture).
6. **Folders**: copies each file into its folder. Writes `sorted.csv`, `duplicates.csv` and `Library details.xlsx`.

Everything found is kept in `work/library.db`, per file content, so sorting again only looks at new files.

### Who picks the folders?

| | This computer (default) | Claude | Jev |
|---|---|---|---|
| Cost | Free | Uses your Claude plan | Paid per file, asks first |
| Privacy | Nothing leaves your computer | Small previews are read by Claude | 280px previews and file names go to TypeSafe |
| Good at | The standard folders | Your own custom folders | Speed |

Faces, text, the Details page and the Excel file always come from your computer, whichever you pick.

## Privacy

- The dashboard only listens on `127.0.0.1`, and refuses requests made through any other web address, so neither your network nor a website can read your photos through it.
- Everything it finds (faces, names, mobile numbers, text, amounts) stays in `dashboard/data/`, `work/` and `inbox/`, which are never committed to git.
- `Library details.xlsx` contains personal information. Keep it private.
- Face data counts as sensitive personal data under privacy laws (India's DPDP Act, GDPR). Ask people before naming them or sharing their photos. Consent changes are logged with the date.

## Coming next: sharing app

People log in with their mobile number and see only photos they're in. In a group photo, a person's face is shown only if they said yes; otherwise it's blurred. People who haven't registered stay blurred. Each person can choose who sees their face. The data for this (mobile numbers, consent, share/hide lists, consent log) is already recorded on the Details page.

## Public demo website (Netlify)

`site/` is a ready-made demo website: the sorting animation, the Details page (people, faces, screenshots, money, documents) and a sample Excel download, all from **drawn pictures and made-up people**. It needs no server, so any static host works.

- **Netlify, from GitHub:** Add new site > Import from Git > pick this repo. `netlify.toml` already points Netlify at `site/`, so leave the build settings as they are and press Deploy.
- **Netlify, by hand:** open [app.netlify.com/drop](https://app.netlify.com/drop) and drag the `site` folder onto the page.
- **After changing the app:** run `python scripts/build_site.py` to rebuild `site/`, then commit (or drag it again).

The demo never contains real photos. Sorting real photos needs the app on your own computer (below).

## Running it by hand

```bash
./setup.sh          # once: Python packages into .venv/ and the models into models/
./start.sh          # opens http://127.0.0.1:8765
```

Every step is a script in `scripts/`: `ingest.py`, `scan.py`, `dupes.py`, `analyze.py`, `label_local.py`, `apply.py`, `excel.py` (and `label_claude.py`, `label_jev.py`). Agents read `CLAUDE.md` (or `AGENTS.md`) for the full playbook. Needs Python 3.9+, and ffmpeg for videos (`brew install ffmpeg`).

## License

MIT. The models keep their own licences (see the table above).
