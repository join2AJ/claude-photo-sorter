"""Step 0: bring files in from a folder, a zip file or a share link.

  python scripts/ingest.py "/path/to/folder"           # used as it is (zips inside it are unpacked by scan.py)
  python scripts/ingest.py "/path/to/takeout-001.zip"  # unpacked into inbox/
  python scripts/ingest.py "https://drive.google.com/drive/folders/..."   # downloaded into inbox/

Links that work: Google Drive files and folders (shared with "Anyone with the link"), Dropbox,
OneDrive, and any direct download link. Google Photos, iCloud and WeTransfer pages can't be
downloaded automatically: use their own "Download all" button, then add the zip here.
The last line printed is "FOLDER <path>", the folder to scan. Your originals are never changed.
"""
import os, re, shutil, sys, time, urllib.parse, urllib.request

sys.path.insert(0, os.path.dirname(__file__))
from common import INBOX, safe_unzip

UNSUPPORTED = {
    "photos.app.goo.gl": "Google Photos", "photos.google.com": "Google Photos", "icloud.com": "iCloud",
    "wetransfer.com": "WeTransfer", "we.tl": "WeTransfer",
}


def slug(s):
    return re.sub(r"[^A-Za-z0-9._ -]+", "_", s).strip(" ._")[:60] or "download"


def fresh_dir(name):
    d = os.path.join(INBOX, time.strftime("%Y-%m-%d %H%M ") + slug(name))
    os.makedirs(d, exist_ok=True)
    return d


def download(url, folder):
    """Plain HTTP download with progress. Returns the saved file path."""
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (photo-sorter)"})
    with urllib.request.urlopen(req, timeout=60) as r:
        ctype = r.headers.get("Content-Type", "")
        if "text/html" in ctype:
            raise RuntimeError("That link opens a web page, not a file. Use a direct download link, "
                               "or download it yourself and add the file or zip.")
        name = None
        cd = r.headers.get("Content-Disposition", "")
        m = re.search(r"filename\*=UTF-8''([^;]+)", cd) or re.search(r'filename="?([^";]+)"?', cd)
        if m:
            name = urllib.parse.unquote(m.group(1))
        name = slug(name or os.path.basename(urllib.parse.urlparse(r.geturl()).path) or "download")
        total = int(r.headers.get("Content-Length") or 0)
        if total and total > shutil.disk_usage(folder).free * 0.9:
            raise RuntimeError(f"Not enough disk space: the download is {total / 1e9:.1f} GB.")
        path, got = os.path.join(folder, name), 0
        with open(path, "wb") as f:
            while chunk := r.read(1 << 20):
                f.write(chunk)
                got += len(chunk)
                print(f"PROGRESS {got} {max(total, got)}", flush=True)
    return path


def from_link(url):
    host = urllib.parse.urlparse(url).netloc.lower()
    for h, name in UNSUPPORTED.items():
        if host == h or host.endswith("." + h):
            raise RuntimeError(f"{name} links can't be downloaded automatically. Open the link, use "
                               f"\"Download all\" to get a zip, then add that zip here.")
    folder = fresh_dir(host.replace("www.", ""))
    if "drive.google.com" in host or "docs.google.com" in host:
        import gdown
        if "/folders/" in url:
            gdown.download_folder(url, output=folder, quiet=False, remaining_ok=True)
        else:
            gdown.download(url, output=folder + os.sep, quiet=False, fuzzy=True)
    else:
        if "dropbox.com" in host:  # ?dl=1 gives the file (a shared folder comes as one zip)
            url = re.sub(r"([?&])dl=0", r"\1dl=1", url)
            url += "" if "dl=1" in url else ("&" if "?" in url else "?") + "dl=1"
        elif "1drv.ms" in host or "onedrive.live.com" in host or "sharepoint.com" in host:
            url += ("&" if "?" in url else "?") + "download=1"
        download(url, folder)
    if not any(fs for _, _, fs in os.walk(folder)):
        raise RuntimeError("Nothing was downloaded. Check the link is shared with \"Anyone with the link\".")
    return folder


def ingest(src):
    src = src.strip().strip('"').strip("'")
    if re.match(r"https?://", src, re.I):
        return from_link(src)
    path = os.path.expanduser(src)
    if os.path.isdir(path):
        return path.rstrip("/")
    if os.path.isfile(path) and path.lower().endswith(".zip"):
        name = os.path.splitext(os.path.basename(path))[0]
        dest = os.path.join(INBOX, slug(name) + f" ({os.path.getsize(path)})")
        print(f"Unpacking {os.path.basename(path)}...", flush=True)
        return safe_unzip(path, dest)
    if os.path.isfile(path):
        raise RuntimeError("That's a single file. Choose the folder it's in, or a zip file.")
    raise RuntimeError(f"Not found: {src}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    try:
        print("FOLDER " + ingest(sys.argv[1]), flush=True)
    except Exception as e:
        sys.exit(str(e))
