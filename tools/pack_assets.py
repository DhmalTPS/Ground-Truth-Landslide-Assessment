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
import hashlib
import json
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetch_assets import EXCLUDE, INCLUDE, MANIFEST, ROOT, sha256, wanted  # noqa: E402

STORED = {".jpg", ".jpeg", ".png", ".webp", ".pt", ".npz", ".zip"}   # already compressed

CARD = """---
license: other
license_name: mixed-per-photo
license_link: LICENSE.md
pretty_name: Ground Truth Landslide Assessment (photos and baseline)
size_categories:
- 1K<n<10K
task_categories:
- image-classification
tags:
- landslides
- geology
- geotechnical-engineering
- field-photos
---

# Ground Truth Landslide Assessment: photos and baseline checkpoint

Ground-level photos of slopes, labelled with a landslide type (Hungr, Leroueil & Picarelli 2014,
the update of the Varnes classification), for the course project
https://github.com/DhmalTPS/Ground-Truth-Landslide-Assessment. The questions below follow
*Datasheets for Datasets* (Gebru et al. 2021).

## Get it into a clone of the code

    pip install -r requirements.txt
    python tools/fetch_assets.py          # checks every file against tools/assets_manifest.json (SHA-256)

## Motivation

A junior engineer at a road or in a valley photographs a slope with a phone; the app says which
landslide type it is, how sure it is, and what to check. Public landslide datasets are almost all
aerial or satellite images, so this set collects photos taken from the ground.

## Composition

4,954 photos (`data/raw/images/`), each with one final label. `reject` = not usable for the task
(aerial, satellite, map, diagram, close-up, no slope visible, or unsure between two types).

| Label | train | val | test | total |
|---|---|---|---|---|
| fall_topple | 194 | 25 | 58 | 277 |
| rotational_slide | 67 | 6 | 11 | 84 |
| translational_slide | 99 | 22 | 32 | 153 |
| debris_flow | 180 | 13 | 29 | 222 |
| earth_mud_flow | 39 | 4 | 8 | 51 |
| no_landslide | 329 | 84 | 125 | 538 |
| reject | 2,406 | 478 | 745 | 3,629 |
| **all** | 3,314 | 632 | 1,008 | 4,954 |

- **Sites:** photos of the same place or event are linked into one site (2,062 sites; the 1,325
  usable photos come from 738). Splits are by site, so no site is in two splits; the test split
  has 263 usable photos from 152 sites.
- **Sources:** Wikimedia Commons 3,684 (many Geograph field photos), Flickr via Openverse 1,267,
  other 3. 322 usable photos are from South Asia (48 in test). 237 usable photos have a phone
  camera in their EXIF.
- **Other files:** `data/metadata.csv` (source URL, title, author, licence, categories, camera,
  site), `data/splits.csv`, `data/labels/claude_ai.csv` and its audit trail
  `data/labels/ai_annotation/`, `data/credits.csv`, `data/vlm_predictions.csv` (Qwen2.5-VL-7B
  zero-shot probabilities, the baseline), `data/site_merge_moves.csv`, `data/cache/` (cached
  DINOv2-base, DINOv2-large and SigLIP2 embeddings of every photo and of fixed phone-style copies,
  so training and evaluation run without recomputing them), `data/field/measurements.csv`
  (empty template for field size measurements).
- **`models/cnn_convnext_tiny.fb_in22k_ft_in1k.pt`:** ConvNeXt-Tiny fine-tuned on train (best epoch
  chosen on val), the comparison baseline (the app uses linear heads on frozen features instead).

## Collection

Title and category searches on Wikimedia Commons and Openverse (scripts `src/collect_commons.py`,
`src/collect_openverse.py`), October 2026. Only openly licensed photos were kept; duplicates were
removed by perceptual hash. The searches favour photos people chose to upload and describe, so the
set is not a random sample of landslides: 1,132 photos are Geograph imports (Britain and Ireland),
and clearly visible, well-described landslides are more likely to be included.

## Labelling (read before using the labels)

- **Every label was made by an AI annotator** (Claude, reviewer `claude_ai`) following the
  repository's `labeling_guide.md` and `tools/ai_labeling_prompt.md`; the test split was
  labelled without model suggestions visible. The labels are not verified by a geologist.
  Two manual spot checks (48 + 24 photos) judged about 80-90% consistent with the guide.
- When the annotator was unsure between two types, the photo was labelled `reject`, so the
  hardest photos are not in the scored test set.
- Accuracy measured on this test split is agreement with these labels, not with verified
  ground truth.

## Uses

Intended: training and evaluating landslide-type classifiers on ground photos, reproducing the
project's results (`src/probe.py`, `src/eval.py`, `tools/system_test.py`; these reproduce the
published `results/summary.md` and `results/system_test.md` byte for byte from this data).
Not suitable as the only basis for safety decisions, for mapping, or for estimating landslide
frequency (the collection is not a random sample).

## Licences

There is no single licence: every photo keeps the licence it was published under, listed with
title, author and source URL in `data/credits.csv`. 2,863 photos are CC BY-SA (any version),
762 CC BY, 753 non-commercial (CC BY-NC, -NC-SA, -NC-ND), 22 CC BY-ND, 407 public domain, 89 CC0,
and 58 under other open terms (GODL-India, OGL 3, GFDL 1.2, Apache 2.0, "no restrictions" and
similar). Credit each photo you show; NC photos may not be used commercially; ND photos may not
be shared modified; SA photos must be shared under the same licence. The labels, splits,
embeddings and checkpoint were made for the course project; cite the repository when you use them.

## Maintenance

Files are versioned in this repository; `tools/assets_manifest.json` in the code repository
pins the exact files (path, size, SHA-256). To report a problem with a photo or a label, open an
issue on the code repository.
"""

LICENSE_MD = """# Licences

Photos in `data/raw/`: each photo keeps its own licence; see `data/credits.csv` (title, author,
licence, source for every photo). Labels, splits, embeddings and the ConvNeXt checkpoint: made for
https://github.com/DhmalTPS/Ground-Truth-Landslide-Assessment (IC202P course project); cite it when
you use them.
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
        st = p.stat()   # mtime: fetch_assets restores it (check_integrity compares result and model dates)
        entries.append({"path": rel, "size": st.st_size, "sha256": sha256(p), "mtime": int(st.st_mtime)})
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


def git_blob_sha1(path):
    """The id git gives a file's content (how Hugging Face identifies files not stored in LFS)."""
    h = hashlib.sha1()
    h.update(b"blob %d\0" % path.stat().st_size)
    with open(path, "rb") as f:
        while chunk := f.read(1 << 20):
            h.update(chunk)
    return h.hexdigest()


def push(repo, manifest, max_files=500, max_bytes=500_000_000):
    """Upload in batches of commits; files already on the Hub with the same content are skipped, so a rerun
    after an interruption only sends what is missing."""
    from huggingface_hub import CommitOperationAdd, HfApi
    api = HfApi()
    try:
        who = api.whoami()["name"]
    except Exception:
        sys.exit("Not logged in to Hugging Face: run `hf auth login` first.")
    print(f"Uploading to dataset {repo} as {who} ...")
    api.create_repo(repo, repo_type="dataset", exist_ok=True)
    for name, text, msg in (("README.md", CARD, "Dataset card"), ("LICENSE.md", LICENSE_MD, "Licences")):
        api.upload_file(path_or_fileobj=text.encode("utf-8"), path_in_repo=name, repo_id=repo,
                        repo_type="dataset", commit_message=msg)
    remote = {e.path: e for e in api.list_repo_tree(repo, repo_type="dataset", recursive=True)
              if getattr(e, "blob_id", None)}

    def on_hub(f):
        r = remote.get(f["path"])
        if r is None or r.size != f["size"]:
            return False
        if r.lfs is not None:
            return r.lfs.sha256 == f["sha256"]
        return r.blob_id == git_blob_sha1(ROOT / f["path"])

    todo = [f for f in manifest["files"] if not on_hub(f)]
    print(f"{len(manifest['files']) - len(todo)} files already there, {len(todo)} to upload "
          f"({sum(f['size'] for f in todo) / 1e9:.2f} GB)")
    batches, cur, cur_b = [], [], 0
    for f in todo:
        if cur and (len(cur) >= max_files or cur_b + f["size"] > max_bytes):
            batches.append(cur)
            cur, cur_b = [], 0
        cur.append(f)
        cur_b += f["size"]
    if cur:
        batches.append(cur)
    for i, b in enumerate(batches, 1):
        ops = [CommitOperationAdd(path_in_repo=f["path"], path_or_fileobj=str(ROOT / f["path"])) for f in b]
        api.create_commit(repo_id=repo, repo_type="dataset", operations=ops,
                          commit_message=f"Add {len(b)} files ({i}/{len(batches)})")
        print(f"  commit {i}/{len(batches)}: {len(b)} files, {sum(f['size'] for f in b) / 1e6:.0f} MB", flush=True)
    print(f"Done: https://huggingface.co/datasets/{repo}")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--zip", metavar="OUT.zip", help="write a zip with models/ and data/ at the top")
    ap.add_argument("--push", metavar="USER/NAME", help="upload to this Hugging Face dataset repo")
    a = ap.parse_args()
    files = collect()
    if not files:
        sys.exit("No asset files found under models/ and data/.")
    manifest = write_manifest(files, a.push)
    if a.zip:
        write_zip(files, a.zip)
    if a.push:
        push(a.push, manifest)


if __name__ == "__main__":
    main()
