# Ground Truth Landslide Assessment

Landslide type and size from a ground-level phone photo, with on-site guidance (IC202P course
project). The web app is called *Landslide Type Check*.

**Use case:** a junior engineer standing on a road or in a valley takes a phone photo looking up
at a slope. The app tells them which landslide type it is (Varnes classification, Hungr et al.
2014), how confident it is, what to verify on site and what to stay away from. Aerial, satellite,
map or close-up photos are flagged with tips for retaking the photo. After the type, it estimates
the landslide's size.

## Results

Untouched test split: 263 usable photos from 152 sites, no site shared with train/val
(95% CI: site bootstrap).

| Model | Accuracy | Macro-F1 [95% CI] |
|---|---|---|
| **App model** (DINOv2-base + DINOv2-large + SigLIP2 linear probes) | **0.806** | **0.784** [0.688, 0.857] |
| Fine-tuned ConvNeXt-Tiny | 0.722 | 0.665 |
| Qwen2.5-VL zero-shot | 0.555 | 0.327 |

End to end on all 1,008 test photos (including unusable ones), the app answers 69% of usable
photos confidently, and those answers are right 86% of the time; below 60% confidence it says
*uncertain* and shows the top two types. Method, all results and caveats: **`report.md`**.

**Read these numbers as agreement with AI-made labels.** Every label, test split included, was
made by an AI annotator following `labeling_guide.md` (two manual spot checks judged about
80-90% consistent with the guide); none was verified by a geologist, and photos the annotator
was unsure about were left out (`report.md`, "Label caveat").

**Reproducible:** from the published data (see [Large files](#large-files-dataset-and-baseline-checkpoint)),
`src/probe.py` (three heads), `src/eval.py` and `tools/system_test.py` regenerate
`results/summary.md` and `results/system_test.md` byte for byte (checked on 2026-11-22: about
15 minutes on an 8 GB laptop GPU).

## Quick start

Needs Python 3.11 and git. About 5 GB of disk for the Python packages and the backbones; an NVIDIA
GPU is optional (without one, a photo takes a few seconds longer and sizes take minutes).

```
git clone https://github.com/DhmalTPS/Ground-Truth-Landslide-Assessment
cd Ground-Truth-Landslide-Assessment
```

| | Windows | macOS / Linux |
|---|---|---|
| 1. Environment | `py -3.11 -m venv .venv` | `python3.11 -m venv .venv` |
| 2a. PyTorch, NVIDIA GPU | `.venv\Scripts\python -m pip install torch==2.11.0 torchvision==0.26.0 --index-url https://download.pytorch.org/whl/cu128` | Linux: same command with `.venv/bin/python` |
| 2b. PyTorch, no NVIDIA GPU | same, with `.../whl/cpu` instead of `.../whl/cu128` | Linux: `.../whl/cpu`; macOS: `.venv/bin/python -m pip install torch==2.11.0 torchvision==0.26.0` |
| 3. Packages | `.venv\Scripts\python -m pip install -r requirements.txt` | `.venv/bin/python -m pip install -r requirements.txt` |
| 4. Run the app | `.venv\Scripts\python src/app.py` | `.venv/bin/python src/app.py` |

Then open `http://localhost:8000` on the computer, or the printed `http://<computer-ip>:8000` on a
phone. Commands below are written as `python ...`: use the venv's Python as in the table, from the
repository folder (any folder name works; paths are found relative to the code).

Nothing else to download by hand: the app's trained heads are in `models/` (under 1 MB) and the
three backbones (about 2 GB) download from Hugging Face on first start, into `.cache/huggingface/`
inside the repository (set `HF_HOME` to put them elsewhere). The first start therefore needs
internet and takes a few minutes; after that the app also works offline.
`python src/predict.py photo.jpg` gives the same answer on the command line.

The dataset and the ConvNeXt baseline checkpoint are only needed to retrain or re-evaluate:
see [Large files](#large-files-dataset-and-baseline-checkpoint).

Phones open the computer's address, so they must be on the same Wi-Fi, or the computer on the
phone's hotspot (this works in the field without internet). To reach it from anywhere, see
[Sharing beyond this computer](#sharing-beyond-this-computer).

## Documents

| File | Read it for |
|---|---|
| `README.md` | running, using and reproducing the app (this file) |
| `report.md` | the project report: data, models, results, limitations |
| `TECHNICAL_REPORT.md` | every component in full detail (architecture, maths, UI design, audits) |
| `research_notes.md` | literature background and early findings; paper links in `papers/README.md` |
| `labeling_guide.md` | how photos were labelled (also the AI annotator's instructions) |
| `design.md` | the original plan from before the build (history only) |
| `CITATION.cff` | how to cite the code and dataset (GitHub shows it as "Cite this repository") |

## Using the app

**Phones.** The live camera guide needs https, which `src/app.py` serves by default on port 8443
next to http on 8000 (self-signed certificate made once in `.cache/tls`; tap Advanced > Proceed
once on the phone). Phones that open the http address are redirected to https; the computer itself keeps
`http://localhost:8000`. `--no-https` turns it off. On shared networks add `--token SECRET`
(phones then open `http://<computer-ip>:8000/?t=SECRET`). Uploads are saved to `data/app_uploads/`
for later labelling (`--no-save` to disable; capped by `--max-saved`).

**Phone on the same Wi-Fi cannot open the app?** (Windows; on macOS/Linux allow the ports 8000
and 8443 in your firewall.) Windows makes inbound *Block* rules for
python.exe when its first "Allow access?" popup is cancelled, and they apply on Public networks
(hostel/campus Wi-Fi, a new hotspot). Run `src/app.py --lan` (Windows only): one UAC popup, then an elevated
guardian pauses those Block rules and adds one Allow rule (only the app's ports, only from the
local subnet, only for the Python that listens: the base Python 3.11 `python.exe`, because the
venv's `python.exe` is just a launcher). The guardian restores the firewall exactly on Ctrl+C, a crash
or a closed window, and the app prints the confirmation. After a power loss a normal start warns
and `src/app.py --lan-restore` undoes it. Log: `.cache/lan/guardian.log`. If the phone still times
out, the Wi-Fi isolates devices from each other (common on hostel Wi-Fi): use a phone hotspot or
`tools/serve_public.py`.

**Three ways to add a photo:** *Guided camera* (the live camera inside the page), *Phone camera*
(the phone's own camera app, no live guide) and *From gallery* (*Upload a photo* on a computer).
If the guided camera cannot start, the page says why and how to fix it (https link, camera
permission, in-app browser, camera busy) and starts by itself once permission is allowed.

**Computers.** At 1100 CSS px and wider (a 1920x1080 laptop at 150 % Windows scaling is 1280 px)
the page becomes a work area: a left rail for set-up (mode, how to shoot, distance, notes) and,
before a result, a large drop zone (click, drag a photo in, or Ctrl+V). From 1200 px a result is
laid out in two independent columns: the photo, size and on-site checklist on the left; the
verdict, safety, all types, next steps and save on the right (one column at 1100-1199 px, with
the photo kept short so the verdict is on screen). Keys: U upload, C camera, ? help, Space shoots
and Esc closes in the viewfinder. Ctrl+P prints the result on white; Windows high-contrast themes
keep every control outlined. The page is sent gzipped (~110 KB instead of ~400 KB).

**What the guidance adds** (`src/guide.py`; details and tests in `report.md` §5.1-5.2):
- a first-run tour, a per-session safety checklist (with "Continue anyway") and a help sheet with
  a glossary;
- single-photo, 4-shot site-survey and overlapping-set modes;
- a live framing and level viewfinder with a photo-quality meter (Good / Fair / Poor / Very poor),
  one instruction at a time and a big arrow (up/down from aim; left/right from the compass or from
  steps); for overlapping sets the live overlap with the last photo against the ideal band;
- an instant on-phone photo check, each problem graded minor or serious, plus cut-off-edge and
  mostly-sky warnings;
- results that are always shown, even for a photo that fails the photo check: a quality band says
  how reliable the result is, and nothing is adjusted to look better;
- type first, then sizes; yes/no questions when the model is unsure; a combined site result for
  surveys; next steps and tickable on-site signs;
- notes, a GPS marker (the camera position plus compass bearing and distance give an estimated
  position of the landslide), and saved or shared reports, including one JPEG with the photo, a
  map and every result, with GPS in its EXIF (`TECHNICAL_REPORT.md` §10.3);
- an offline queue, a practice quiz and Hindi.

Measuring whether the guidance helps: `tools/guidance_report.py` (after field use without
`--no-save`). Photo-check thresholds: recalibrate after the dataset changes with
`tools/calibrate_photo_check.py` (train split only).

## Photo sets and video (too big for one photo)

In the app, choose **Overlapping set**, then:
- **Turn on the spot:** the photos are joined into one picture.
- **Walk along:** the photos are analysed together. Type the normal steps between photos to get
  real sizes from triangulation.
- **Auto sweep:** switch "Auto" on in the camera view, take the first photo, then turn or walk
  slowly. The next photos are taken by themselves.
- **Video:** pick one slow sweep from the gallery, and the phone picks sharp, overlapping frames
  from it. For a walk video, type the total steps walked during it.

The tools behind this (simulated sets from train photos; the test split is never read):
`tools/overlap_eval.py` (thresholds and the joined-picture weight, `src/overlap_check.json`),
`tools/stereo_eval.py` (walk-along scale), `tools/focal_eval.py` (focal length of a joined picture,
`src/focal_check.json`), `tools/accuracy_eval.py` (out-of-fold accuracy experiments) and
`tools/object_prior_eval.py` (the known-object scale prior, `models/dimension_object_prior.json`).
All run in resumable chunks (`--budget 540`); results in `report.md` §4.6 and §5.3.

## Size estimation

`src/dimension.py` (deep-learning models and orchestration) and `src/dim_stats.py` (pixel
statistics) measure the landslide once it is classified. The app does this automatically; skip
it with `--no-dims`. From the command line:
`src/dimension.py photo.jpg [--label debris_flow] [--distance 40] [--save-overlay] [--json]`.
The architecture table and the assumed values are in `report.md` §6b. In short:

- **Outline:** CLIPSeg, the self-trained head and the jittered SAM soft mask are fused, damped by
  a vegetation/sky prior, and cut by a graph cut with colour and depth edges.
- **Depth:** Depth Anything V2 and Depth Pro, each with test-time augmentation, fused per pixel by
  inverse variance, then guided-filtered. ZoeDepth was tested and dropped (`report.md` §6b).
- **Scale**, best first: your typed distance; OWLv2 known-height objects (weighted median); the
  field calibration; the ensemble, corrected by the known-object prior.
- **Measurement:** RANSAC plane geometry and per-class measures. Volume comes from published laws
  combined with a reconstructed pre-failure surface. Grains are SAM instances at two zooms,
  fitted with a truncated log-normal.
- **Uncertainty:** Monte Carlo P5-P95 ranges and size-class probabilities. The ranges are computed
  and evaluated (`tools/dimension_eval.py`) but not shown in the app or its saved reports, which
  show the estimate only.
- **Class doubt:** when the classifier is unsure, the landslide is also measured as the runner-up
  class.

Training and calibration (both leakage-free): `tools/train_outline_head.py` self-trains the
outline head on the train split and selects it on val (test is never used);
`tools/calibrate_dimensions.py` fits the scale from field measurements in
`data/field/measurements.csv`, validated leave-one-site-out.

`src/dimension.py a.jpg b.jpg c.jpg --site` fuses several photos of ONE landslide: the median of
the photos, with the between-photo spread added to the uncertainty. Different photos of one site
typically differ by about 1.5-2x, so use this for important sites.

`tools/dimension_eval.py [--tag v4] [--budget-min 3]` is resumable: on low-RAM machines run it in
chunks; exit code 3 means rerun to continue. It reports availability, stability under phone-like
edits, the depth checks, interval widths and same-site consistency, and writes the known-object
scale evidence.

## Sharing beyond this computer

**Public link from this computer (free, with sizes).** `tools/serve_public.py` starts the app on
127.0.0.1 and opens a Cloudflare quick tunnel; it prints `https://<random words>.trycloudflare.com`,
which works on any phone (https, so the live camera guide works) while the window stays open.
It needs Cloudflare's `cloudflared` program (free, no account): install it so it is on `PATH`, or
set `CLOUDFLARED` to its full path. The tunnel uses HTTP/2, which also works on networks that block
QUIC. Options: `--save` keeps uploads, `--no-dims` drops
sizes. Checked through the public link: page 2.4 s, full result with sizes 40 s (one train photo).

**Hugging Face Space (no sizes).** `tools/build_hf_space.py --push USER/ground-truth-landslide`
stages `deploy/hf_space/` (Dockerfile, Space README), `src/` and the trained heads from `models/`,
then uploads them as a Docker Space (needs `hf auth login` once with a write token). Note (Nov
2026): Hugging Face now requires a PRO subscription for Docker Spaces. The Space has 2 CPU cores
and 16 GB RAM and serves over https. Timing on the development laptop with CUDA off and 2 threads (the Space
CPU may differ): startup 27-46 s, landslide type 6-19 s per photo, one size estimate ~8 min, so the
Space runs with `--no-dims` and `--no-save`. Behind a hosting proxy the app does not redirect to
its own https port, `--port` defaults to `$PORT`, and the Dockerfile runs with `--no-https`.

**Your own server.** It runs on CPU (three backbones + linear heads, a few seconds per photo,
~3 GB RAM). Clone the repository (or copy `src/` and `models/`), install CPU PyTorch and
`requirements.txt`, and run `src/app.py --port 8000 --token ... --no-dims` behind HTTPS (sizes
need a GPU to be quick). Hosting is a deliberate decision for the team:
it publishes the service and its uploads.

## Reproducing the model

Classes: `fall_topple`, `rotational_slide`, `translational_slide`, `debris_flow`,
`earth_mud_flow`, `no_landslide` (+ `reject` for unusable photos). Definitions and Hungr 2014
types: `src/common.py` and `labeling_guide.md`.

**One GPU job at a time.** Qwen-VL uses ~6 GB of an 8 GB GPU; running DINOv2 or ConvNeXt alongside
it fails (the probe falls back to CPU; CNN training does not). With little free RAM, run long GPU
jobs in the foreground in chunks (`train_cnn.py --max-minutes 8 --resume`).

- **Scenario B (default, what was done): we build the dataset** with steps 1-5 below.
- **Scenario A: a labeled dataset is given.** Instead of steps 1-5:
  ```
  python src/import_dataset.py <dataset_folder> --name given
  ```
  Folder-per-class (`<label>/*.jpg`) or `<train|val|test>/<label>/*.jpg` both work; a CSV with
  `--csv`, `--image-col`, `--label-col` (and `--group-col`, `--split-col` if present) too.
  The first run writes `data/label_map_given.json` with guessed mappings to our classes:
  check every line, then rerun with `--map data/label_map_given.json`. The dataset's own
  split is kept. **If it has no train/val/test split, run `src/split.py` afterwards** (pass
  `--group-col` at import if there is a site/event column, otherwise photos of one site may land
  in different splits). A dataset without `reject` labels trains no photo check (every upload is
  treated as usable). Then continue at step 6.

| Step | Command | What it does |
|---|---|---|
| 1a. Collect | `src/collect_commons.py --search-only` | Wikimedia Commons ground photos (title searches; many Geograph field photos) + licence info -> `data/raw/images`, `data/metadata.csv` |
| 1b. | `src/collect_commons.py --match "India\|Nepal\|Himachal\|Uttarakhand\|Kerala\|Wayanad\|Sikkim\|Bhutan\|Pakistan\|Sri Lanka\|Bangladesh\|Road cuts"` | South-Asian landslide/road categories (category trees are otherwise mostly aerial/glacier/art) |
| 1c. | `src/collect_openverse.py` | CC photos from Flickr via Openverse (Indian/Nepali hill roads); skips Commons duplicates |
| 1d. Own photos | `src/import_local.py field_photos` | one subfolder per site: `field_photos/<site>/*.jpg` |
| 1e. Camera EXIF | `tools/camera_info.py` | flags phone photos (`is_phone`) for the phone tests |
| 2a. Link sites | `tools/link_sites.py` | merges photos of the same place/event (titles, photo series, visual similarity) into one site |
| 2b. Split | `src/split.py` | train/val/test **by site**, before labeling (review.py also does this for new photos) |
| 3. VLM | `src/vlm_label.py` (all) or `--split test` (baseline only) | Qwen2.5-VL-7B (4-bit) zero-shot probabilities -> `data/vlm_predictions.csv` |
| 4. Label | `src/review.py --reviewer <name>` | browser tool: keys 1-6 / R, V = viewpoint; test split shown blind |
| 4b. AI labels | `tools/contact_sheet.py OUT --cols 4 --rows 3 --tile 320 --skip-labeled`, then `tools/ai_labels.py OUT codes.txt` | what was used here (reviewer `claude_ai`; instructions `tools/ai_labeling_prompt.md`; audit trail `data/labels/ai_annotation/`) |
| 4c. Label noise | `tools/find_label_issues.py OUT` | flags doubtful train/val labels for a second look (never test) |
| 5. Features | `tools/precompute_embeddings.py --backbone <bb>` for `facebook/dinov2-base`, `facebook/dinov2-large`, `google/siglip2-base-patch16-224` | caches features of every photo + phone-style copies (resumable) |
| 6a. Probes | `src/probe.py --backbone <bb> --name probe_base` (and `probe_large`, `probe_siglip`) | photo-check head + type head per backbone; C by grouped CV on train+val |
| 6b. Choose | `tools/robustness_eval.py` | train+val only: site-grouped CV + 3 unseen-source tests for every backbone/ensemble -> `models/selected.json` (the app's model + threshold), `results/robustness.md` |
| 6c. CNN | `src/train_cnn.py --epochs 25 --max-minutes 8 --resume` (repeat until done) | fine-tuned ConvNeXt-Tiny, for comparison (its 106 MB checkpoint is not in the repository) |
| 7a. Evaluate | `src/eval.py` | every model on the untouched test split (+ phone-degraded copies, uphill views, South Asia, phone photos) -> `results/summary.md`; writes `pred_selected*.csv` |
| 7b. System test | `tools/system_test.py` | the real app pipeline on every test photo (photo check + type + uncertain) -> `results/system_test.md` |
| 7c. Hard cases | `tools/hard_case_eval.py` | app behaviour on ambiguous photos the labels rejected -> `results/hard_cases.md` |
| 8. Check | `tools/check_integrity.py` | everything complete and consistent, no train/test leakage |
| Credits | `tools/credits.py` | per-photo attribution `data/credits.csv`, licence summary `results/licences.md` |

Collection results change over time (Commons/Openverse are live); to reproduce the numbers, use
the frozen dataset instead (next section). Every step writes its outputs (`data/`, `models/`,
`results/`); of `results/`, only the short write-ups (`results/*.md`) and the test predictions
they were computed from (`results/pred_*.csv`) are in the repository.

### Labeling rules (details: `labeling_guide.md`)
- Label what is **visible**. Unusable photo (aerial, map, close-up, no slope, …): **R**.
  Unsure between two landslide types: also **R** (the rule all current labels follow; the
  hardest cases are therefore evaluated separately, see 7c).
- Human labels always override the AI annotator's. Two teammates labeling the same images
  (`--relabel-others`) gives inter-annotator agreement (eval.py); ties: `--conflicts`.
- Never label the test split with VLM suggestions visible (the tool enforces this; eval.py
  reports the count, which must be 0).
- Expert check: `review.py --reviewer faculty --split test --relabel-others --skip-ai-rejects --sample 50`.

### Photo licences
Every photo keeps licence, author and source URL in `data/metadata.csv` (`tools/credits.py`
writes `data/credits.csv`). 753 photos are non-commercial (NC) and 411 no-derivatives (ND): fine
for this course project, but credit every photo you show ("Title" by Author, Licence, URL), do not
publish modified versions of ND photos, and remove NC photos before any commercial use.
See `results/licences.md`.

## Large files (dataset and baseline checkpoint)

Not in git (GitHub refuses files over 100 MB, and the data is 2.2 GB), but published separately
with a checksum for every file in `tools/assets_manifest.json`:

| Part | Size | Needed for |
|---|---|---|
| `data/` (photos, labels, site splits, credits, cached embeddings) | 2.07 GB, 5,086 files | retraining, `src/eval.py`, `tools/system_test.py`, `tools/check_integrity.py` |
| `models/cnn_convnext_tiny.fb_in22k_ft_in1k.pt` (ConvNeXt baseline) | 106 MB | the ConvNeXt row of the results |

```
python tools/fetch_assets.py                 # both, from the Hugging Face dataset in the manifest
python tools/fetch_assets.py --only models   # or --only data
python tools/fetch_assets.py --zip FILE_OR_URL   # the same files from a zip instead
python tools/fetch_assets.py --check         # verify what is on disk (sizes + SHA-256)
```

The files land at the paths the code expects, whatever the clone's folder is called; a rerun
fetches only what is missing, and the script exits with an error if any file is missing or
differs from the manifest. With them, `python tools/check_integrity.py` prints ALL OK in a fresh
clone. The files are published as the Hugging Face dataset
[dhmaltps/ground-truth-landslide-data](https://huggingface.co/datasets/dhmaltps/ground-truth-landslide-data). Photos people send to the app (`data/app_uploads/`) are never included.
Maintainers: `tools/pack_assets.py` rewrites the manifest and `--zip OUT.zip` / `--push USER/NAME`
publish the files (after `hf auth login`).

Every photo keeps its own licence (see [Photo licences](#photo-licences)): reuse them only with
the credit in `data/credits.csv` and within each licence.

## Why these choices
- **Zero-shot VLM is a baseline, not the main model.** LandslideBench (2026, overhead imagery)
  measured Qwen3-VL-8B zero-shot at 19% vs 79% for a fine-tuned ConvNeXt; on our ground photos
  Qwen2.5-VL is similarly far behind the trained models (`report.md`).
- **Frozen features + linear heads:** with ~40-400 photos per class, frozen foundation-model
  features (DINOv2, SigLIP2) + logistic regression generalise better than fine-tuning a whole
  network (confirmed: the fine-tuned ConvNeXt scores lower).
- **Split by site, and sites linked across categories:** photos of the same landslide in train
  and test would inflate accuracy.
- **Model chosen on train+val only** by site-balanced CV + distribution-shift tests; the test
  split is only used to report.
- **No vertical flips in augmentation:** the downhill viewpoint is part of the signal.
