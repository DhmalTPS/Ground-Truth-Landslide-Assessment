"""Download the large files that are not in the git repository, into the exact places the code expects.

    python tools/fetch_assets.py                  # everything (dataset + ConvNeXt baseline), from Hugging Face
    python tools/fetch_assets.py --only models    # just the ConvNeXt baseline checkpoint (models/*.pt)
    python tools/fetch_assets.py --only data      # just the dataset (data/)
    python tools/fetch_assets.py --zip assets.zip # from a zip instead (a local file or an https URL)
    python tools/fetch_assets.py --check          # only verify what is already on disk

The app itself does not need any of this: its trained heads are in models/ in the repository and its
backbones download from Hugging Face on first start. These files are for retraining, re-evaluating and the
ConvNeXt comparison.

Where the files go does not depend on the name of the cloned folder: everything lands under this
repository's root (the folder above tools/). tools/assets_manifest.json lists every file with its size and
SHA-256; after a download each file is checked against it, and the script exits with code 1 if anything is
missing or different.

Photo licences: each photo in data/raw/ keeps its own licence (CC BY, CC BY-SA, CC BY-NC(-ND/-SA), CC0,
public domain); data/credits.csv gives title, author, licence and source for every photo.
"""
import argparse
import fnmatch
import hashlib
import json
import os
import shutil
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "tools" / "assets_manifest.json"

# What the asset bundle contains (paths relative to the repository root, fnmatch patterns: "*" also matches "/").
INCLUDE = ["models/cnn_*.pt", "data/raw/*", "data/cache/*", "data/labels/*", "data/field/*", "data/*.csv"]
EXCLUDE = ["data/app_uploads/*",            # photos people uploaded through the app: never published
           "models/*.best.pt", "models/*.state.pt",   # unfinished training checkpoints
           "*/Thumbs.db", "*/desktop.ini", "*/.DS_Store"]
PARTS = {"models": ["models/*"], "data": ["data/*"]}


def wanted(rel, only=None):
    """True if the repository-relative posix path belongs to the bundle (and to the --only part, if given)."""
    if not any(fnmatch.fnmatch(rel, p) for p in INCLUDE) or any(fnmatch.fnmatch(rel, p) for p in EXCLUDE):
        return False
    return only is None or any(fnmatch.fnmatch(rel, p) for p in PARTS[only])


def sha256(path, bufsize=1 << 20):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(bufsize):
            h.update(chunk)
    return h.hexdigest()


def load_manifest():
    if not MANIFEST.exists():
        sys.exit(f"{MANIFEST.relative_to(ROOT)} is missing; it comes with the repository (git pull).")
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def verify(manifest, only=None, quick=False):
    """-> (ok, missing, different) over the manifest entries of the chosen part."""
    files = [f for f in manifest["files"] if wanted(f["path"], only)]
    missing, different = [], []
    for i, f in enumerate(files, 1):
        p = ROOT / f["path"]
        if not p.is_file():
            missing.append(f["path"])
        elif p.stat().st_size != f["size"] or (not quick and sha256(p) != f["sha256"]):
            different.append(f["path"])
        if i % 500 == 0 or i == len(files):
            print(f"\r  checked {i}/{len(files)} files", end="", flush=True)
    print()
    return len(files) - len(missing) - len(different), missing, different


def restore_times(manifest, only):
    """Give downloaded files their original modification time (a download stamps them 'now', which would make
    the results in results/ look older than the models they were computed from, see tools/check_integrity.py)."""
    for f in manifest["files"]:
        p = ROOT / f["path"]
        if "mtime" in f and wanted(f["path"], only) and p.is_file() and p.stat().st_size == f["size"]:
            os.utime(p, (f["mtime"], f["mtime"]))


def report(manifest, only, quick):
    ok, missing, different = verify(manifest, only, quick)
    for label, items in (("missing", missing), ("different from the manifest", different)):
        if items:
            print(f"{len(items)} file(s) {label}, e.g.:")
            for x in items[:10]:
                print("   ", x)
    if missing or different:
        print("Run the download again (it only fetches what is missing), or see README.md, 'Large files'.")
        return 1
    print(f"All {ok} files are in place and match tools/assets_manifest.json.")
    return 0


def from_hub(repo, only):
    try:
        from huggingface_hub import snapshot_download
    except ImportError:
        sys.exit("huggingface_hub is not installed: pip install -r requirements.txt")
    patterns = PARTS[only] if only else ["models/*", "data/*"]   # never the dataset card or anything at the top
    print(f"Downloading {repo} (Hugging Face dataset) into {ROOT} ...")
    snapshot_download(repo_id=repo, repo_type="dataset", local_dir=str(ROOT), allow_patterns=patterns)


def from_zip(src, only):
    zpath = Path(src)
    if src.startswith(("http://", "https://")):
        import requests
        zpath = ROOT / ".cache" / "assets_download.zip"
        zpath.parent.mkdir(parents=True, exist_ok=True)
        print(f"Downloading {src} ...")
        with requests.get(src, stream=True, timeout=60) as r:
            r.raise_for_status()
            total, done = int(r.headers.get("content-length", 0)), 0
            with open(zpath, "wb") as f:
                for chunk in r.iter_content(1 << 20):
                    f.write(chunk)
                    done += len(chunk)
                    if total:
                        print(f"\r  {done / 1e9:.2f} / {total / 1e9:.2f} GB", end="", flush=True)
        print()
    if not zpath.is_file():
        sys.exit(f"zip not found: {zpath}")
    root = ROOT.resolve()
    with zipfile.ZipFile(zpath) as z:
        names = [n for n in z.namelist() if not n.endswith("/")]
        # accept a zip with models/ and data/ at the top, or the same inside one folder (any name)
        tops = {n.split("/", 1)[0] for n in names}
        strip = "" if tops & {"models", "data"} else (next(iter(tops)) + "/" if len(tops) == 1 else "")
        n_out = 0
        for n in names:
            rel = n[len(strip):] if strip and n.startswith(strip) else n
            if not wanted(rel, only):
                continue
            dest = (root / rel).resolve()
            if root not in dest.parents:          # no writing outside the repository
                sys.exit(f"unsafe path in zip: {n}")
            dest.parent.mkdir(parents=True, exist_ok=True)
            with z.open(n) as fi, open(dest, "wb") as fo:
                shutil.copyfileobj(fi, fo, 1 << 20)
            n_out += 1
    print(f"Extracted {n_out} files into {ROOT}")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--repo", help="Hugging Face dataset id (default: the one in tools/assets_manifest.json)")
    ap.add_argument("--zip", metavar="FILE_OR_URL", help="extract from a zip instead of Hugging Face")
    ap.add_argument("--only", choices=sorted(PARTS), help="fetch only the models or only the data")
    ap.add_argument("--check", action="store_true", help="only verify the files already on disk")
    ap.add_argument("--quick", action="store_true", help="verify sizes only (skip SHA-256)")
    a = ap.parse_args()
    manifest = load_manifest()
    if not a.check:
        if a.zip:
            from_zip(a.zip, a.only)
        else:
            repo = a.repo or manifest.get("repo")
            if not repo:
                sys.exit("No Hugging Face dataset is set in tools/assets_manifest.json yet; pass --repo USER/NAME "
                         "or --zip FILE_OR_URL.")
            from_hub(repo, a.only)
        restore_times(manifest, a.only)
    sys.exit(report(manifest, a.only, a.quick))


if __name__ == "__main__":
    main()
