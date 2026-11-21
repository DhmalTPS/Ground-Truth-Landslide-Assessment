"""Maintainer side of tools/fetch_assets.py: list, pack and publish the large files that are not in git.

    python tools/pack_assets.py                        # (re)write tools/assets_manifest.json from the local files
    python tools/pack_assets.py --zip OUT.zip          # also write a zip with models/ and data/ at the top
    python tools/pack_assets.py --push USER/NAME       # also upload them to a Hugging Face dataset repo
                                                       # (needs `hf auth login` first; makes the repo if new)

What is included is defined once, in tools/fetch_assets.py (INCLUDE / EXCLUDE): the ConvNeXt baseline
checkpoint models/cnn_*.pt and data/ (raw photos, cached embeddings, labels, field set, CSVs), never
data/app_uploads/ (photos people sent to the app). Commit the manifest after changing it, so that a clone
can check its download.
"""
import argparse
import json
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetch_assets import EXCLUDE, INCLUDE, MANIFEST, ROOT, sha256, wanted  # noqa: E402

STORED = {".jpg", ".jpeg", ".png", ".webp", ".pt", ".npz", ".zip"}   # already compressed

CARD = """---
license: other
license_name: mixed-cc
license_link: LICENSE.md
pretty_name: Landslide type photos and ConvNeXt baseline
size_categories:
- 1K<n<10K
task_categories:
- image-classification
---

# Landslide type photos (data and baseline checkpoint)

Large files for https://github.com/DhmalTPS/Landslide-Category-Classifier that are not stored in git:

- `data/raw/`: ground-level photos of slopes, labelled with a landslide type (Hungr et al. 2014);
- `data/labels/`, `data/*.csv`: labels, site-grouped splits, credits and metadata;
- `data/cache/`: cached backbone embeddings (so evaluation runs without recomputing them);
- `data/field/`: the field photo set;
- `models/cnn_*.pt`: the fine-tuned ConvNeXt-Tiny baseline (the app does not use it).

Get them into a clone of the repository, at the paths the code expects:

    pip install -r requirements.txt
    python tools/fetch_assets.py

## Licences

There is no single licence. Every photo keeps the licence it was published under (CC BY, CC BY-SA,
CC BY-NC, CC BY-NC-SA, CC BY-NC-ND, CC BY-ND, CC0 or public domain); `data/credits.csv` gives the title,
author, licence and source of each photo. Respect the licence of each photo you reuse: some forbid
commercial use (NC) or changes (ND), and SA photos must be shared under the same licence. Labels, splits,
embeddings and the checkpoint: same licence as the code repository.
"""

LICENSE_MD = """# Licences

Photos in `data/raw/`: each photo keeps its own licence; see `data/credits.csv` (title, author,
licence, source for every photo). Everything else: the licence of
https://github.com/DhmalTPS/Landslide-Category-Classifier.
"""


def collect():
    out = []
    for top in ("models", "data"):
        for p in sorted((ROOT / top).rglob("*")):
            if p.is_file():
                rel = p.relative_to(ROOT).as_posix()
                if wanted(rel):
                    out.append(rel)
    return out


def write_manifest(files, repo):
    old = json.loads(MANIFEST.read_text(encoding="utf-8")) if MANIFEST.exists() else {}
    entries = []
    for i, rel in enumerate(files, 1):
        p = ROOT / rel
        entries.append({"path": rel, "size": p.stat().st_size, "sha256": sha256(p)})
        if i % 500 == 0 or i == len(files):
            print(f"\r  hashed {i}/{len(files)}", end="", flush=True)
    print()
    m = {"repo": repo or old.get("repo"), "repo_type": "dataset",
         "include": INCLUDE, "exclude": EXCLUDE,
         "n_files": len(entries), "total_bytes": sum(e["size"] for e in entries),
         "files": entries}
    head = json.dumps({k: v for k, v in m.items() if k != "files"}, ensure_ascii=False)[:-1]
    body = ",\n".join(json.dumps(e, ensure_ascii=False) for e in entries)   # one file per line: readable diffs
    MANIFEST.write_text(f'{head}, "files": [\n{body}\n]}}\n', encoding="utf-8")
    print(f"{MANIFEST.relative_to(ROOT)}: {m['n_files']} files, {m['total_bytes'] / 1e9:.2f} GB")
    return m


def write_zip(files, out):
    out = Path(out).resolve()
    with zipfile.ZipFile(out, "w", allowZip64=True) as z:
        for i, rel in enumerate(files, 1):
            comp = zipfile.ZIP_STORED if Path(rel).suffix.lower() in STORED else zipfile.ZIP_DEFLATED
            z.write(ROOT / rel, rel, compress_type=comp)
            if i % 500 == 0 or i == len(files):
                print(f"\r  zipped {i}/{len(files)}", end="", flush=True)
    print(f"\n{out}: {out.stat().st_size / 1e9:.2f} GB")


def push(repo):
    from huggingface_hub import HfApi
    api = HfApi()
    try:
        who = api.whoami()["name"]
    except Exception:
        sys.exit("Not logged in to Hugging Face: run `hf auth login` first.")
    print(f"Uploading to dataset {repo} as {who} ...")
    api.create_repo(repo, repo_type="dataset", exist_ok=True)
    api.upload_file(path_or_fileobj=CARD.encode("utf-8"), path_in_repo="README.md", repo_id=repo,
                    repo_type="dataset", commit_message="Dataset card")
    api.upload_file(path_or_fileobj=LICENSE_MD.encode("utf-8"), path_in_repo="LICENSE.md", repo_id=repo,
                    repo_type="dataset", commit_message="Licences")
    # upload straight from the repository root, restricted to the bundle (resumable, no staging copy)
    api.upload_large_folder(repo_id=repo, repo_type="dataset", folder_path=str(ROOT),
                            allow_patterns=INCLUDE, ignore_patterns=EXCLUDE)
    print(f"Done: https://huggingface.co/datasets/{repo}")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--zip", metavar="OUT.zip", help="write a zip with models/ and data/ at the top")
    ap.add_argument("--push", metavar="USER/NAME", help="upload to this Hugging Face dataset repo")
    a = ap.parse_args()
    files = collect()
    if not files:
        sys.exit("No asset files found under models/ and data/.")
    write_manifest(files, a.push)
    if a.zip:
        write_zip(files, a.zip)
    if a.push:
        push(a.push)


if __name__ == "__main__":
    main()
