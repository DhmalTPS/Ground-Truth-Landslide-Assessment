# IC202P Landslide Field Assistant — Complete Technical Report

*Architecture, mathematics, design choices, measured results and improvement paths, end to end.*
*State of the repository: commit `6e7e75b` (2026-11-05). Every number below is copied from a result file or
the code named next to it; nothing is estimated unless it says so.*

---

## Contents

0. [What the system serves](#0-what-the-system-serves)
1. [Headline numbers](#1-headline-numbers)
2. [System architecture](#2-system-architecture)
3. [Data: collection, labels, sites, splits](#3-data)
4. [Classifier: features, heads, ensemble, decision rule](#4-classifier)
5. [Evaluation methodology and every classifier result](#5-evaluation)
6. [Photo quality: client check and server gate](#6-photo-quality)
7. [Size estimation (dimensions)](#7-size-estimation)
8. [Photo sets, walk-along stereo, video and auto sweep](#8-photo-sets-and-video)
9. [Decision support: field questions, signs, families](#9-decision-support)
10. [Server and phone application](#10-server-and-phone-app)
11. [Deployment](#11-deployment)
12. [Engineering practice: leakage guards, reproducibility, integrity](#12-engineering-practice)
13. [Design decision log](#13-design-decision-log)
14. [Improvement history (what changed and why)](#14-improvement-history)
15. [Known weaknesses found in this review](#15-known-weaknesses)
16. [Improvement roadmap](#16-improvement-roadmap)
17. [Appendix A: constants](#appendix-a-constants)
18. [Appendix B: file map](#appendix-b-file-map)

---

## 0. What the system serves

**User.** A junior engineer standing on a road or in a valley, looking *up* at a slope, with a phone.

**Decision supported.** "What kind of landslide is this, how big is it, how sure are we, what must I check
and where must I not stand?" — before a geologist arrives. It is *decision support*, not a decision maker:
every output carries its uncertainty and the app says when it does not know.

**Inputs.** One photo, a 4-shot site survey, an overlapping photo set (turn on the spot / walk along), or a
video; optionally typed distance, steps walked, phone tilt sensors, GPS, notes.

**Outputs.**

| Output | Form | Quantified by |
|---|---|---|
| Landslide type (6 classes, Hungr et al. 2014) | label + all 6 probabilities | confidence; "uncertain" below 0.6; family answer (flow / slide) |
| Photo usability | Good / Fair / Poor / Very poor + reasons | calibrated thresholds; server usable-probability |
| Sizes | length, widths, drop, area, volume, perimeter, slope, travel angle, size class, grains/blocks | median + 90 % range (Monte Carlo), size-class probabilities |
| Field guidance | checklist, safety notes, yes/no questions, next steps | Bayes-updated field probabilities |
| Location | camera position (photo EXIF GPS or phone fix), camera bearing, estimated landslide position, map panel with markers | GPS error (m); landslide 1-σ radius from GPS, bearing and distance errors (§10.3) |
| Records | image report (JPEG with GPS stamp, map marker, every metric, GPS in EXIF), HTML report, share text, history, offline queue, guidance log | — |

**Scope boundary.** One photo sees only what is in frame; cracks or seepage outside it are invisible. Sizes
come from monocular depth and are unverified against field tape measurements. Labels are AI-made (§3.3).

---

## 1. Headline numbers

| Quantity | Value | Source |
|---|---|---|
| Photos collected / usable | 4,954 / 1,325 (2,062 sites) | `data/splits.csv`, report.md §2 |
| **Test accuracy / macro-F1 (selected ensemble)** | **0.806 / 0.784 [95 % CI 0.688, 0.857]** (263 photos, 152 sites) | `results/summary.md` |
| Fine-tuned ConvNeXt-Tiny | 0.722 / 0.665 | same |
| Qwen2.5-VL-7B zero-shot | 0.555 / 0.327 | same |
| Out-of-fold (train+val) accuracy / macro-F1 | 0.773 / 0.704; ECE 0.040 | `results/robustness.md` |
| Confident answers (p ≥ 0.6) | CV: 73 % coverage at 88.1 % accuracy; test: 69.2 % of usable photos at **85.7 %** | robustness.md, system_test.md |
| End-to-end precision over *all* test photos | 0.605 (photo gate is the weak link: ~17 % false reject, ~16 % false accept) | system_test.md |
| Phone-degraded test macro-F1 | 0.697 (accuracy when answered rises to 87.9 %) | summary.md, system_test.md |
| Region shift (no South Asia in training → South Asia) | site-balanced F1 0.578 vs 0.714 CV | robustness.md |
| Size ranges, length (current prior) | 90 % interval ≈ ×/÷ 2.4 (log-width ≥ 1.76, derived) | §7.5 |
| Known-object scale prior | 83 photos / 43 sites, LSO 90 % coverage **94.0 %** (old prior 62.7 %) | object_prior_eval.md |
| Walk-along stereo scale (simulated) | median abs log error 0.120, stated sd 0.150, coverage 87.6 %, success 71 % | stereo_eval.md |
| Photo-set link false-positive rate (simulated) | 0.0 % at 30 inliers | overlap_eval.md |
| Client photo check false flags | train 3.6 %, val 3.9 %; detects blur/dark/sky 100 %, haze 96 %, overexposure 86 % | photo_check.json |
| Latency (RTX 4060 laptop) | type ≈ 2–5 s; sizes ≈ 25 s; full ≈ 40 s via public link | dimension_eval_v4.md, README |
| Latency (CPU, 2 threads) | type 6–19 s; sizes ≈ 8 min | README |

---

## 2. System architecture

### 2.1 Two pipelines

```
OFFLINE (build the model)                                   ONLINE (serve the engineer)
─────────────────────────                                   ───────────────────────────
Commons / Openverse / own photos                            Phone browser (single HTML page)
   │ collect_*.py, import_*.py  (dHash dedup, licences)        │ live viewfinder: metrics + sensors
   ▼                                                          │ instant photo check (same maths as calib.)
metadata.csv ──► link_sites.py (union-find) ──► split.py       │ shrink 1280 px, EXIF f35, gravity, GPS
   │                     (site-disjoint 65/15/20)              ▼
   ▼                                                        app.py (ThreadingHTTPServer, one GPU lock)
labels (AI annotator, review.py for humans)                    │ POST /predict?stage=type
   │ find_label_issues.py (train/val only)                     │    Predictor: 3 frozen backbones
   ▼                                                          │    → gate head (usable) + type head
precompute_embeddings.py (+3 phone copies)                     │    → mean of probabilities → decide()
   ▼                                                          │ POST /measure?job=   (sizes, async)
probe.py ×3 (gate + type heads, C by grouped CV)               │    Dimensioner: depth ×2, outline,
   ▼                                                          │    scale, geometry, grains, volume, MC
robustness_eval.py → selected.json (train+val only)            │ POST /overlap, /pano  (photo sets)
   ▼                                                          │ POST /fuse            (site survey)
eval.py / system_test.py / hard_case_eval.py (test, once)      ▼
calibrate_photo_check.py, train_outline_head.py,            result cards, questions, report, history,
object_prior_eval.py, overlap_eval.py, stereo_eval.py,      offline queue (IndexedDB), Hindi
focal_eval.py  (all train/val or simulation)
check_integrity.py  (must print ALL OK before every commit)
```

### 2.2 Layering principle: "networks propose, statistics decide"

Every stage that produces a number has a learned proposer and a statistical arbiter:

| Stage | Deep learning proposes | Statistics/geometry decide |
|---|---|---|
| Type | 3 frozen foundation models | linear heads, grouped CV, mean pool, calibrated threshold |
| Usability | gate heads | percentile-calibrated pixel statistics |
| Outline | CLIPSeg, DINOv2 head, SAM | graph cut with stability-selected λ |
| Depth | Depth Anything V2, Depth Pro | log-space inverse-variance fusion |
| Scale | OWLv2 objects, Depth Pro focal | weighted median, random-effects prior, stereo triangulation |
| Grains | SAM instances | truncated log-normal MLE, bootstrap |
| Volume | — | published laws ⊕ spline pre-failure surface, inverse variance |
| Uncertainty | — | Monte Carlo, class probabilities |
| Field questions | — | Bayes rule + expected information gain |

Reason: with ~1,000 labelled photos and no measured sizes, no network can be trusted to output a final
number on its own; statistics make each number auditable and give it an error bar.

### 2.3 Hardware constraint shaping the design

One RTX 4060 Laptop GPU (8 GB), limited RAM, Windows. Consequences: frozen backbones instead of fine-tuning;
models parked in CPU RAM and swapped in (`Dimensioner.use`, offload when GPU < 12 GB, kept resident if free
memory > need + 2.6 GB); one GPU lock in the server; resumable ≤ 540 s chunks for every long job; HF cache
moved to the project drive.

### 2.4 Repository structure

`src/` runtime and training code; `tools/` evaluation, calibration and maintenance; `models/` trained heads
and calibration JSON; `src/*.json` calibrations next to the code that reads them; `data/` (git-ignored) the
frozen dataset; `results/` (git-ignored) measured outputs; `deploy/` hosting files. Full map: Appendix B.

---

## 3. Data

### 3.1 Why a new dataset

No public ground-level landslide-*type* dataset exists. LandslideBench, Bijie, Landslide4Sense, LMHLD,
Debrisflow23 and the ESSD coseismic set are overhead imagery and/or detection only (research_notes.md).
So the project built one (Scenario B); Scenario A (a given labelled set) is supported by
`src/import_dataset.py` with a guessed-then-human-checked label map.

### 3.2 Collection

| Source | Method | Key parameters | Yield |
|---|---|---|---|
| Wikimedia Commons, title search | 53 `intitle:` searches with hint labels | 120/search, min side 400 px, thumbnails 1024 px (500 px fallback) | 2,426 photos, 62 % rejected |
| Commons, category trees | 28 roots, depth 1–3, BFS ≤ 400 subcats, round-robin over categories | ≤ 300/category | 879 South-Asian + 379 rock fall/slide; 82 % rejected |
| Openverse (Flickr) | 28 queries, CC only, Wikimedia excluded | 20/page, 5 pages, 3.5 s sleep (20 req/min) | 1,270; 86 % rejected |
| Own photos | `import_local.py`, `<site>/*.jpg` | long side ≤ 1024 | — |

- **Why title searches:** category trees are "full of aerial shots, glaciers and art"; titles return ground
  photos (many Geograph field photos), i.e. what the app will receive.
- **Why thumbnails:** originals were rate-limited (HTTP 429, Retry-After 600 s); thumbnails were not.
- **Deduplication:** difference hash (dHash) on a 9×8 grey resize → 64 bits; a photo is skipped if its
  Hamming distance to any stored hash is ≤ 4.
- **Hint labels** from category/title rules (whole-word matching; "Netherlands" no longer matches "net";
  protection/net/shed categories → `no_landslide` as hard negatives) are shown to a reviewer only and are
  **never used as training labels**.
- **Licences:** stored per photo; 753 non-commercial, 411 no-derivatives, 3,139 share-alike, 30 without
  author (`results/licences.md`). `tools/credits.py` writes attribution for every photo.
- **Phone flag:** EXIF make/model via the Commons API → `is_phone` (636 phone photos; Openverse has no EXIF).

### 3.3 Classes and labelling

| Class | Hungr 2014 types | Visual cues from downhill |
|---|---|---|
| `fall_topple` | rock/ice fall, boulder fall, block/flexural topple | steep rock face, detached blocks, talus |
| `rotational_slide` | rock/clay/silt rotational slide | curved concave scarp, back-tilted block, bulging toe |
| `translational_slide` | rock planar/wedge slide, gravel/sand/debris slide | planar shallow scar, bedding plane, displaced sheet |
| `debris_flow` | debris flow, debris flood, debris avalanche | channel, levees, unsorted boulders, fan |
| `earth_mud_flow` | earthflow, mud flow | fine-grained wet lobe/tongue |
| `no_landslide` | stable slope, cut, quarry, protection works | — |
| `reject` | aerial/satellite, map, art, archive scan, close-up, slope not visible, > ~1 km away | used only by the photo gate |

**Why these 6:** Hungr's 32 types depend partly on properties invisible in a photo (clay sensitivity,
saturation, velocity); these groups are distinguishable from a ground view. Families used later:
*flow* = {debris_flow, earth_mud_flow}, *slide* = {rotational, translational}.

**Rules** (`labeling_guide.md`): label what is visible, not the caption; label the dominant process;
**unsure between two types → reject** (keeps type labels clean; the cost — hard photos are missing from the
scored set — is measured separately, §5.6); the test split is always labelled blind (no VLM suggestion).

**Who labelled.** All 4,954 labels are by an AI annotator (reviewer `claude_ai`, `vlm_shown = 0`), working
from contact sheets (`tools/contact_sheet.py`, 4×3 tiles at 320 px) and `tools/ai_labeling_prompt.md`, with
an audit trail in `data/labels/ai_annotation/`. Two manual spot checks (48 + 24 photos) judged ~80–90 %
consistent (a judgement, not a score). **There are 0 human labels.** `review.py` supports human relabelling;
human labels override AI ones automatically and `eval.py` reports Cohen's κ once they exist.

**Label combination** (`common.final_labels`): human votes take precedence over AI votes; majority vote;
ties excluded from ground truth; viewpoint by majority (ties → "up", deterministic).

**Label noise** (`tools/find_label_issues.py`, train+val only — correcting test toward the model would
inflate the test score): out-of-fold predictions with `GroupKFold(5)` by site, DINOv2-base features,
`StandardScaler + LogisticRegression(C = 0.01, balanced)`. Flag rule: p(own label) < 0.15 and
max p(other) > 0.6 (a simplified confident-learning rule). 299 labels re-looked blind: **63 % agreement**
with the first look — evidence of substantial label noise.

### 3.4 Site linking (leakage control)

Photos of one landslide must never be split between train and test. `tools/link_sites.py` builds a
union-find over photos and merges two photos when any of these hold:

1. same original `site_id` (Commons first category, Flickr photographer, own-photo folder);
2. same title stem (lower-cased, digits/extension/parentheses removed), only if the stem has ≥ 12 characters,
   ≥ 2 words and appears at ≤ 3 original sites;
3. same photo series day (e.g. `starr-YYMMDD`);
4. **visual similarity**: cosine(DINOv2-base embeddings) ≥ 0.90.

Result: 2,142 raw sites → **2,062** merged sites; 230 photos changed split; 0 sites span splits.
A merged site spanning splits moves to its majority split, ties resolved train > val > test ("test only keeps
groups it clearly owns").

### 3.5 Splits

`split.py`: targets 65/15/20 (train/val/test), seed 0; existing assignments never change; sites are shuffled,
sorted largest first, and each goes to the split furthest below its target share
`argmax_s (target_s · N − count_s)`. Splits are fixed **before** labelling so test can be labelled blind.

| | images | sites | fall | rot. | trans. | debris | earth/mud | none | reject | usable (sites) |
|---|---|---|---|---|---|---|---|---|---|---|
| train | 3,314 | 1,348 | 194 | 67 | 99 | 180 | 39 | 329 | 2,406 | 908 (487) |
| val | 632 | 304 | 25 | 6 | 22 | 13 | 4 | 84 | 478 | 154 (99) |
| test | 1,008 | 410 | 58 | 11 | 32 | 29 | 8 | 125 | 745 | 263 (152) |

Subsets: South Asia 322 usable; real phone photos 237 usable (20 in test); "looking down" viewpoint 43.
Largest site: 132 photos of the Nedumpoil (Kerala 2022) debris flow, all in train — the reason all shift
metrics are **site-balanced**.

`check_integrity.py` additionally asserts no usable test photo has a near-duplicate (DINOv2 cosine ≥ 0.95)
in train/val.

---

## 4. Classifier

### 4.1 Feature extraction (frozen foundation models)

| Member | Backbone (Hugging Face) | Input | Feature | Dim |
|---|---|---|---|---|
| `probe_base` | `facebook/dinov2-base` | shortest edge 256, centre crop 224, ImageNet norm | concat(CLS, mean of patch tokens) | 1,536 |
| `probe_large` | `facebook/dinov2-large` | same | concat(CLS, mean patch) | 2,048 |
| `probe_siglip` | `google/siglip2-base-patch16-224` | resize 224×224 (aspect not kept), norm 0.5 | pooled image feature, L2-normalised | 768 |

Built-in horizontal-flip test-time augmentation: \( \phi(x) = \tfrac12[\,\phi_0(x) + \phi_0(\mathrm{flip}_h x)\,] \).
**No vertical flips anywhere** — the downhill viewpoint is part of the signal.

Why DINOv2 + SigLIP2: DINOv2 is self-supervised and strong on texture and structure (debris, scarps);
SigLIP2 is image–text aligned and adds semantic cues. Their errors are partly independent, which is what an
ensemble needs. Concatenating CLS with mean patch tokens keeps both global layout and texture statistics.

### 4.2 Phone-style augmentation (`src/phone_aug.py`)

Each training photo gets 3 deterministic phone-style copies (seed = crc32(`id#k`)), applied in order:

1. random crop, area ∈ U(0.55, 1.0), aspect ∈ U(0.75, 1.0) or U(1.0, 1.78);
2. horizontal flip, p = 0.5;
3. tilt, p = 0.6, angle ∈ U(−7°, 7°), border cropped;
4. brightness ×U(0.7, 1.3), contrast ×U(0.75, 1.25), saturation ×U(0.7, 1.3);
5. white-balance gains U(0.9, 1.1) per channel, p = 0.3;
6. Gaussian blur r ∈ U(0.5, 1.6), p = 0.3;
7. Gaussian noise σ ∈ U(3, 10), p = 0.2;
8. recompression, p = 0.7: with p = 0.5 downscale ×U(0.4, 0.8), then JPEG quality ∈ [35, 85].

Reason: training photos are mostly good cameras from Commons; field photos are phones, hand-held, compressed.
Copies always stay in the same CV fold as their source photo (no leakage through augmentation).

### 4.3 Linear probe heads

Per backbone, two heads on the same features:

\[
\hat p(c \mid x) = \mathrm{softmax}_c\!\big(W\,\tfrac{\phi(x)-\mu}{\sigma} + b\big),\qquad
\min_{W,b}\ \tfrac12\lVert W\rVert^2 + C\sum_i w_{y_i}\,\big[-\log \hat p(y_i\mid x_i)\big],\quad
w_c = \frac{N}{K\,N_c}
\]

(`StandardScaler` + multinomial `LogisticRegression`, `class_weight="balanced"`, max_iter 5000).

- **gate head:** usable vs reject, trained on all 3,946 labelled train+val photos;
- **type head:** 6 classes, trained on the 1,062 usable train+val photos (+ 3 copies each).

**Choosing C:** grid {0.003, 0.03, 0.3, 1.0}, `StratifiedGroupKFold(3, shuffle, seed 0)` over train+val with
groups = site; the C with the best mean macro-F1 wins; then refit on all train+val + copies.
Stored: type C = 0.3 / 0.3 / 0.003 (base / large / siglip), CV macro-F1 0.653 / 0.653 / 0.612; gate C = 0.003
for all, gate CV macro-F1 0.842 / 0.843 / 0.829.

**Why linear probes:** with 40–400 photos per class a linear head on frozen features cannot overfit much,
trains in seconds, and was measured to beat full fine-tuning (§5.4).

### 4.4 Ensemble

Linear opinion pool, equal weights, over the M = 3 members (`predict.py:123-134`):

\[
P(c) = \frac1M\sum_{m=1}^{M} P_m(c),\qquad u = \frac1M\sum_m P_m(\text{usable})
\]

Alternatives were tested out-of-fold (§5.5): log pool \(P\propto\prod_m P_m^{1/M}\) (−0.009 F1), stacked
simplex weights (−0.045, unstable fold weights favouring SigLIP), concatenated features (+0.002). None beat
the plain mean, so the simplest rule stayed.

### 4.5 Decision rule (`Predictor.decide`)

Let \(p_{(1)} \ge p_{(2)}\) be the two largest class probabilities.

```
if u < 0.5                      → status = bad_photo   (result still shown, marked "not reliable")
elif p(1) < confident_min (0.6) → status = uncertain   (top two shown)
else                            → status = ok
family = flow/slide  if status = uncertain and {top1, top2} is a family and p(1)+p(2) ≥ 0.6
```

**How 0.6 was chosen** (`robustness_eval.py`, train+val CV only): the smallest threshold t ∈ {0, 0.4, …, 0.9}
whose accuracy among answered photos ≥ 0.85 at coverage ≥ 0.5. Risk–coverage table (CV):

| t | coverage | accuracy | macro-F1 |
|---|---|---|---|
| 0.0 | 1.00 | 0.773 | 0.704 |
| 0.5 | 0.86 | 0.834 | 0.756 |
| **0.6** | **0.73** | **0.881** | **0.802** |
| 0.7 | 0.60 | 0.911 | 0.829 |
| 0.8 | 0.46 | 0.944 | 0.869 |
| 0.9 | 0.28 | 0.983 | 0.942 |

This is a *selective classifier*: the app trades coverage for reliability, and the trade transferred to the
test split (88.1 % predicted, 85.7 % measured).

### 4.6 Model selection (`tools/robustness_eval.py`, train+val only)

All 7 non-empty subsets of {base, large, siglip} are scored by

\[
\text{robust} = \tfrac14\big[F1_{site}(\text{CV}) + F1_{site}(\text{Commons}\!\to\!\text{Openverse})
+ F1_{site}(\text{non-SA}\!\to\!\text{South Asia}) + F1_{site}(\text{camera}\!\to\!\text{phone})\big]
\]

with \(F1_{site}\) = macro-F1 weighted by 1/(photos in the site), CV = `StratifiedGroupKFold(5)` with C
re-chosen inside each fold, and every shift test site-disjoint. Ties at 3 decimals → fewer members.
Winner: **base+large+siglip, 0.676**; recorded in `models/selected.json` with the SHA-1 of the selection code
and a data fingerprint.

| System | Robust | CV F1 (site) | →Openverse | →South Asia | →phone | ECE | ΔF1 vs selected [90 % CI] |
|---|---|---|---|---|---|---|---|
| **base+large+siglip** | **0.676** | 0.714 | 0.743 | 0.578 | 0.669 | 0.040 | — |
| large+siglip | 0.670 | 0.701 | 0.689 | 0.617 | 0.675 | 0.036 | +0.013 [−0.002, +0.029] |
| base+large | 0.665 | 0.712 | 0.695 | 0.587 | 0.668 | 0.029 | +0.004 [−0.015, +0.024] |
| base+siglip | 0.654 | 0.704 | 0.703 | 0.548 | 0.662 | 0.063 | +0.007 [−0.013, +0.029] |
| large | 0.651 | 0.684 | 0.661 | 0.587 | 0.669 | 0.091 | +0.025 [+0.002, +0.048] |
| base | 0.639 | 0.680 | 0.719 | 0.558 | 0.598 | 0.040 | +0.032 [+0.014, +0.051] |
| siglip | 0.583 | 0.637 | 0.549 | 0.536 | 0.611 | 0.028 | +0.065 [+0.043, +0.089] |

Reading: the ensemble is clearly better than any single backbone; against the two-model ensembles the gap is
within noise. It does not win every shift (large+siglip is better on →South Asia and →phone).

### 4.7 Baselines

- **ConvNeXt-Tiny** (`timm convnext_tiny.fb_in22k_ft_in1k`) fine-tuned end to end at 288 px: AdamW lr 1e-4,
  weight decay 0.05, batch 24, warmup + cosine, label smoothing 0.1, class-balanced sampler, bf16, phone-style
  augmentation on the fly; best epoch 14 of 25 (val macro-F1 0.688). Trained on train only (908 photos).
- **Qwen2.5-VL-7B-Instruct**, 4-bit NF4, zero-shot. The answer is read from next-token logits restricted to
  7 option letters A–G, then softmaxed — deterministic, gives probabilities, never fails to parse. A neutral
  description prompt is used because leading prompts ("scarp, channel…") caused hallucinated features.
  5.5 GB after load, ~1.3 s/photo.

---

## 5. Evaluation

### 5.1 Protocol

| Rule | Implementation |
|---|---|
| Unit of independence is the **site**, not the photo | all CV is site-grouped; CIs are site (cluster) bootstraps |
| Model choice, C, thresholds, calibrations on **train+val only** | robustness_eval, calibrate_*, object_prior_eval |
| Test split read **once**, for the final report | eval.py, system_test.py, hard_case_eval.py |
| Leakage refused in code | models store train ids + data fingerprint; eval/system_test/integrity refuse overlap |
| Imbalance-aware metrics | macro-F1, per-class recall/precision, site-balanced F1 |
| Uncertainty on every comparison | site bootstrap (2,000× for CIs; paired 1,000× for differences) |

Metric definitions: macro-F1 \(=\frac1K\sum_c \frac{2P_cR_c}{P_c+R_c}\); expected calibration error
\(\mathrm{ECE}=\sum_b \frac{n_b}{N}\,|\mathrm{acc}_b-\mathrm{conf}_b|\) over 10 equal-width bins of top-1
confidence; site-balanced F1 uses sample weights \(1/n_{site}\).

### 5.2 Out-of-fold results (selected system, train+val, 1,062 photos, 586 sites)

Accuracy 0.773, macro-F1 0.704 (site-balanced 0.714), fold F1 0.684 ± 0.046 (min 0.638), ECE 0.040.

| Class | n | recall | precision |
|---|---|---|---|
| fall_topple | 219 | 0.78 | 0.73 |
| rotational_slide | 73 | 0.77 | 0.75 |
| translational_slide | 121 | 0.69 | 0.55 |
| debris_flow | 193 | 0.70 | 0.86 |
| earth_mud_flow | 43 | 0.40 | 0.55 |
| no_landslide | 413 | 0.87 | 0.87 |

Largest confusions: debris_flow → translational_slide 40; no_landslide → fall_topple 37; fall_topple →
no_landslide 33; earth_mud_flow → debris_flow 12.

### 5.3 Untouched test split (263 usable photos, 152 sites)

| Model | Accuracy | Macro-F1 [95 % site CI] | Phone-degraded acc / F1 |
|---|---|---|---|
| Qwen2.5-VL-7B zero-shot | 0.555 | 0.327 [0.268, 0.399] | – |
| ConvNeXt-Tiny fine-tuned | 0.722 | 0.665 [0.548, 0.745] | 0.684 / 0.582 |
| probe_siglip | 0.726 | 0.642 [0.536, 0.725] | 0.722 / 0.639 |
| probe_base | 0.745 | 0.649 [0.537, 0.738] | 0.741 / 0.661 |
| probe_large | 0.776 | 0.736 [0.643, 0.810] | 0.787 / 0.745 |
| **selected** | **0.806** | **0.784 [0.688, 0.857]** | 0.768 / 0.697 |

Per class (selected): recall / precision — fall 0.67/0.66, rotational 0.91/0.83 (n = 11), translational
0.53/0.65, debris 0.97/0.93, earth/mud 0.75/0.75 (n = 8), none 0.90/0.88.
Subgroups: uphill views (n = 254) 0.815 / 0.800; South Asia (n = 48) 0.854 / 0.807; real phone photos
(n = 20) 0.600 / 0.526 (very uncertain at n = 20).
VLM per-class recall: debris_flow 0.03, earth_mud_flow 0.00 — it barely recognises flows.

### 5.4 Why frozen probes beat fine-tuning and the VLM

~900–1,060 training photos are too few to fine-tune a whole CNN without overfitting (0.665 vs 0.784); the
zero-shot VLM lacks domain knowledge of flows (0.327). This matches LandslideBench (overhead imagery):
Qwen3-VL-8B zero-shot 19 % vs fine-tuned ConvNeXt 79 %.

### 5.5 Accuracy levers tried (out-of-fold, `tools/accuracy_eval.py`)

| Variant | Macro-F1 | Answered / acc at 0.6 | Δ vs shipped [90 % CI] |
|---|---|---|---|
| shipped mean of 3 | 0.704 | 73 % / 88.1 % | — |
| log opinion pool | 0.694 | 80 % / 85.8 % | −0.009 [−0.022, +0.005] |
| stacked weights (nested) | 0.659 | 68 % / 86.0 % | −0.045 [−0.068, −0.023] |
| concatenated features | 0.707 | 85 % / 82.8 % | +0.002 [−0.013, +0.017] |
| multi-crop TTA (full + 5 crops at 0.85) | 0.717 | 74 % / 87.0 % | +0.012 [−0.004, +0.027] |
| TTA over phone copies | 0.706 | 70 % / 89.0 % | +0.001 [−0.018, +0.020] |
| per-class log offsets (nested) | 0.713 | 72 % / 88.7 % | +0.007 [−0.018, +0.030] |

Gate for adopting a lever: +1 point with the 90 % CI above 0. **None passed**: on these features accuracy has
plateaued and is **data-limited**; the next gain needs more labelled sites (especially translational and
earth/mud) and human-checked labels.

### 5.6 End-to-end system test (all 1,008 test photos, real app pipeline)

| | Original | Phone-degraded |
|---|---|---|
| Photo gate accuracy | 0.836 | 0.832 |
| Usable accepted / unusable rejected | 0.833 / 0.838 | 0.825 / 0.835 |
| Confident answers | 258 | 254 |
| … on photos that should have been rejected | 29.5 % | 31.5 % |
| **End-to-end precision (all photos)** | **0.605** | **0.602** |
| Usable answered confidently / uncertain | 0.692 / 0.141 | 0.662 / 0.163 |
| **Type accuracy when answered (usable)** | **0.857** | **0.879** |

Hard, ambiguous photos (58 real landslides the labeller rejected as unsure): the app rejects 29 %, says
uncertain on 34 % (top-2 contains the best guess in 65 %), answers confidently on 36 % with only 57 % agreement.
So it hesitates on two-thirds of genuinely ambiguous photos — the desired behaviour — but its confident
answers on them are much weaker than on clear photos (57 % vs 86 %).

---

## 6. Photo quality

### 6.1 Client-side instant check (same maths on phone and in Python)

Seven statistics on the photo resized to 512 px long side (`tools/calibrate_photo_check.py`, mirrored in JS):

| Statistic | Definition |
|---|---|
| lum | mean grey level (BT.601) |
| dark | fraction of pixels < 16 |
| bright | fraction of pixels > 239 |
| contrast | standard deviation of grey |
| sharp | 90th percentile, over an 8×8 tile grid, of the variance of the Laplacian per tile |
| sky | fraction of smooth pixels (\|∇²I\| < 6) that are blue (B > R+8, B ≥ G, grey > 100) or grey > 220 |
| resolution | short side (fixed UI rule: < 720 minor, < 480 serious) |

**Calibration.** Thresholds are percentiles of *accepted train photos*: q-th percentile for lower limits
(lum_min, contrast_min, sharp_min) and (100 − q)-th for upper limits. q is the largest value in
{2, 1.5, 1, 0.75, 0.5, 0.25} with combined train false-flag rate ≤ 5 % → **q = 0.5**.
Thresholds: lum 67.1–170.6, dark ≤ 0.176, bright ≤ 0.318, contrast ≥ 27.4, sharp ≥ 354.7, sky ≤ 0.492.
False flags: train 3.6 %, val 3.9 %. Synthetic-failure detection (val): blur 100 %, dark 100 %, sky 100 %,
haze 96.1 %, overexposure 86.4 %. Phone vs Python decisions: 36/36 agree. The JS re-implements Pillow's
antialiased resampling because canvas scaling made sharpness ~40 % higher.

**Severity and grade** (UI layer; the "serious" margins are fixed UI steps, *not* calibrated):
minor = beyond the calibrated threshold; serious = e.g. lum < 0.7·lum_min, dark > 2×, bright > 1.6×,
contrast < 0.65×, sharp < 0.4×, sky > 0.75, roll > 25°, aim outside [−35°, 75°].

\[
\text{grade} = \begin{cases}
3\ \text{Very poor} & \text{server gate failed or } n_{serious}\ge 2\\
2\ \text{Poor} & n_{serious}=1 \text{ or } n_{minor}\ge 3\\
1\ \text{Fair} & n_{minor}\ge 1\\
0\ \text{Good} & \text{otherwise}
\end{cases}
\]

Live hysteresis: a value is displayed only after 2 consecutive identical readings (no flicker).
**Policy: the check never blocks** and results are always shown with a quality band ("nothing is adjusted to
look better"), because the server gate wrongly refuses ~17 % of usable photos.

### 6.2 Server usable-photo gate

Mean of the three gate heads, threshold u < 0.5 → `bad_photo` (default, not calibrated). Test: 83.3 % of
usable photos accepted, 83.8 % of unusable rejected. This is the weakest link of the system (§5.6).

---

## 7. Size estimation

`src/dimension.py` (models, orchestration) + `src/dim_stats.py` (statistics). Steps in code order:
1 depth → 2 outline → 3 scale → 4 geometry → 5 grains → 6 pre-failure surface → 7 volume + Monte Carlo →
8 checks.

### 7.1 Camera model and focal length

Pinhole: a pixel (u, v) at depth z back-projects to
\( P = \big(\tfrac{(u-W/2)\,z}{f},\ \tfrac{(v-H/2)\,z}{f},\ z\big) \), so a length of \(\ell_{px}\) pixels at
depth z is \( \ell = z\,\ell_{px}/f \). All errors are multiplicative → the whole pipeline works in log space.

Focal in pixels: \( f_{px} = \frac{f_{35}}{36}\max(W,H) \). Sources in priority order, with log-sd:
EXIF FocalLengthIn35mmFilm (10–300 mm) 0.02; Depth Pro's own estimate (if within 0.5–3× default) 0.15;
joined-picture focal from homographies 0.145 (2 photos) / 0.161 (3 photos); default 26 mm 0.25.

### 7.2 Depth

| Model | Runs (TTA) | Role |
|---|---|---|
| Depth Anything V2 Metric Outdoor Small | original, mirrored, brightness ×0.8 | metric depth |
| Depth Pro | original, mirrored | metric depth + focal estimate |
| ZoeDepth (KITTI) | **off** | read 4–6× too close (median largest-pair ratio 6.25 on 40 photos), contradicted by known objects |

Fusion in log space, per pixel (`fuse_depths`): with model mean maps \(m_k\) (each shifted to the median of
the models' log-scales, measured on the lower 2/3 of the photo to avoid sky) and TTA variance \(s_k^2\),

\[
w_k = \frac{1}{s_k^2 + \sigma_0^2},\ \sigma_0 = 0.25;\qquad
\hat m = \frac{\sum_k w_k m_k}{\sum_k w_k};\qquad
\mathrm{logvar} = \frac{1}{\sum_k w_k} + \frac{\sum_k w_k (m_k-\hat m)^2}{\sum_k w_k}
\]

i.e. an unstable model counts less at that pixel and model disagreement adds variance. Then a guided filter
(He 2010) on log depth, guided by the grey image (r = max(4, 0.008·max side), ε = 1e-3), so depth edges follow
image edges. σ₀ = 0.25 reflects typical zero-shot outdoor AbsRel 0.2–0.3.

### 7.3 Outline (where is the landslide?)

1. **CLIPSeg** with 4 class prompts and 9 background prompts; per-pixel softmax over all 13; P = sum of the 4
   positives.
2. **Self-trained outline head:** DINOv2-base patch features (448 px → 32×32 patches) + logistic regression,
   trained on *consensus pseudo-labels* (positive where CLIPSeg > 0.6 and SAM > 0.6 and not vegetation/sky;
   negative where both < 0.2 or clearly vegetation/sky). Val AUC 0.990, IoU 0.869 (measured against the
   teacher consensus, not human masks). Fusion weight \( \mathrm{clip}\big(\frac{AUC-0.75}{0.15},0,1\big) = 1 \).
3. **SAM soft mask:** 6 jittered prompt sets (box noise N(0, 0.05·box), 5 positive + 3 negative points); keep the
   candidate maximising IoU(prior mask) × SAM's predicted IoU; average the kept runs; weight 1.5 (sharpest
   boundaries).
4. **Pixel prior:** vegetation by Excess-Green \((2G-R-B)/(R+G+B)\) with an Otsu-centred logistic; sky by
   blue/bright smooth pixels. \(P \leftarrow P\cdot(1-0.8\,\mathrm{bad})\).
5. **Graph cut** (PyMaxflow, ≤ 512 px, 4-connected). Energy

\[
E(L) = \sum_i -\log P(L_i) \;+\; \lambda\sum_{(i,j)} [L_i\ne L_j]\;
e^{-\beta\lVert I_i-I_j\rVert^2}\; e^{-\frac{(\Delta\log z)^2}{2\langle\Delta\log z^2\rangle}},
\quad \beta = \frac{1}{2\langle\lVert\Delta I\rVert^2\rangle}
\]

   — a GrabCut contrast term multiplied by a depth-edge term, so the cut follows scarp crests and deposit
   fronts. **λ by stability selection:** ladder (0.5, 1, 2, 4, 8); each interior rung is scored by the worse
   IoU with its two neighbours; the most stable rung wins. Synthetic test: IoU 1.00 vs 0.55 for a plain
   threshold.
6. **Boundary variants** {graph cut, P > 0.35, P > 0.65} feed the Monte Carlo (outline uncertainty).

### 7.4 Scale (the dominant error source)

Priority (best evidence first):

| # | Source | Scale | log-sd |
|---|---|---|---|
| 1 | Typed distance d | \(z \leftarrow z\cdot d/\mathrm{median}(z_{mask})\) | \(\sqrt{0.07^2+\sigma_f^2}\) |
| 2 | Walk-along stereo points (≥ 8) | \(s=\exp\mathrm{median}\log(z_{tri}/z_{model})\) | \(\sqrt{\sigma_B^2 + (\mathrm{MAD}/\sqrt{\min(n,10)})^2 + (0.3\sigma_f)^2}\), σ_B = 0.15 |
| 3 | OWLv2 objects of known height in the photo | weighted median of \(\log(h_{true}/h_{est})\), 3-MAD outlier removal | \(\max(\text{se}, \text{spread}, 0.05)\) |
| 4 | Field calibration (when field data exist) | per-class factor | from LSO error |
| 5 | Depth ensemble × known-object prior | \(\times\exp\!\big(\log 1.829 - 0.198(\log \tilde z - \log 8.33)\big)\) | \(\sqrt{0.536^2 + \overline{\mathrm{logvar}} + (0.6\sigma_f)^2}\) |

Objects (height m, log-sd): person 1.70/0.06, car 1.50/0.08, motorcycle 1.10/0.10, truck 3.0/0.15,
bus 3.2/0.06, door 2.1/0.06, pole 9.0/0.25, tree 15/0.5. Object depth is read at the bottom of the box
(where it touches the ground), each detection votes with weight score/sd².

**Known-object prior refit** (`tools/object_prior_eval.py`): random-effects model
\( l_i = \mu + b\log z_i + u_{site} + e_i \), τ by DerSimonian–Laird with site-balanced weights,
predictive sd \( \sqrt{\tau^2+\mathrm{Var}\,\hat\mu} \), validated leave-one-site-out:

| Model | factor | depth slope | predictive sd | LSO median abs err | **LSO 90 % coverage** |
|---|---|---|---|---|---|
| old prior (n = 4) | ×1.531 | — | 0.345 | 0.383 | **62.7 %** (too narrow) |
| constant | ×1.749 | 0 | 0.543 | 0.384 | 92.8 % |
| **log-depth covariate (shipped)** | **×1.829** | **−0.198** | **0.536** | 0.378 | **94.0 %** |

Interpretation: the depth models read landslide scenes ~1.8× too close (more so for near scenes); the
honest scale uncertainty without other evidence is ×/÷ e^{1.645·0.536} ≈ ×/÷ 2.4 at 90 %.

### 7.5 Geometry

RANSAC plane on the back-projected mask points (200 iterations on 3-point samples, inlier threshold
\(2.5\cdot1.4826\cdot\mathrm{median}|r|\), SVD refit) gives the slope normal n. Axes: *across* = x̂ projected
onto the plane; *down* = n × across, oriented along gravity g (phone sensor, else (0, 1, 0)).
With \(\mathrm{ext}(x) = P_{98}(x)-P_{2}(x)\) (robust to stray pixels):

| Measure | Formula |
|---|---|
| Track length L | ext(P·down) |
| Width | ext(P·across); median and max over 12 down-slope bands |
| Vertical drop H | ext(P·g) |
| Horizontal length | \(\sqrt{L^2-H^2}\) |
| Area | \(\sum_{i\in mask} (z_i/f)^2 \,/\, \mathrm{clip}(|\hat r_i\cdot n|, 0.25, 1)\) (view-angle corrected) |
| Perimeter | Σ contour segment × z/f |
| Slope angle | arccos\|n·g\| |
| Travel angle | atan(H / horizontal length) |
| L/W, compactness | L/W; \(\min(1, 4\pi A/P^2)\) |

### 7.6 Grains (photo-sieving)

SAM instances at zoom 1 (24×24 point grid) and zoom 2 (≤ 6 tiles, 2× upsampled) → b-axis = minor axis of the
convex hull × z/f. Resolution limits \(6 z_{90}/f\) and \(3 z_{90}/f\). Conversion area-by-number →
grid-by-number (Kellerhals & Bray 1971) by weights \(b^2\). Fit a **left-truncated log-normal** by weighted
maximum likelihood:

\[
\ell(\mu,s) = \sum_i w_i\Big[\log \varphi\!\big(\tfrac{\ln b_i-\mu}{s}\big) - \log s - \log b_i
- \log\Big(1-\Phi\big(\tfrac{\ln b_{lim}-\mu}{s}\big)\Big)\Big]
\]

→ \(D_{x} = \exp(\mu + s\,\Phi^{-1}(x))\) for x = 0.16, 0.5, 0.84; hidden fine fraction
\(\Phi((\ln b_{lim}-\mu)/s)\); bootstrap (200×) 90 % CI of D50; KS distance as fit check. Reliable only if the
two zooms agree (|log ratio| < 0.3), grain size does not trend with distance (|slope| < 0.5) and KS < 0.15.
Synthetic test: D50 0.095 vs true 0.100.
For falls: blocks ≥ 0.2 m counted, largest block range \(b\,e^{\pm1.645\sigma_s}\), block volume πb³/6.

### 7.7 Volume

1. **Pre-failure surface.** Intact ground in a ring around the outline (ring width max(8, 0.04·max side) px,
   vegetation/sky excluded, ≥ 50 % angular coverage) is fitted with a thin-plate spline h(across, down)
   (height above the slope plane), smoothing chosen by 5-fold CV. Extrapolated under the landslide:
   depleted volume \( \sum (h_{pre}-h_{now})^+ a_{px} \) (slides), accumulated \( \sum (h_{now}-h_{pre})^+ a_{px} \)
   (flows, falls). Synthetic pit: 18.4 vs ~15.7 m³.
2. **Published laws.** Slides: Guzzetti et al. 2009, \(V = 0.074\,A^{1.45}\), log-sd 0.6. Flows/falls:
   \(V = A\,t\) with thickness priors (median, 95 %): debris flow 1.0 m (0.3–3), earth/mud flow 2.0 m (0.5–5),
   fall 0.5 m (0.2–2).
3. **Combination** per Monte Carlo draw, inverse variance in log space:
   \( \log V = \frac{w_1 \log V_{law} + w_2 \log V_{surf}}{w_1+w_2},\ w = 1/\sigma^2 \), where the surface
   sd grows smoothly as relief approaches depth noise:
   \( \sigma_{surf} = \mathrm{clip}(\tfrac{\mathrm{cv\_rmse}\cdot A}{V_s}, 0.5, 1.5)(1 + \mathrm{SNR}^{-2}) \),
   \( \mathrm{SNR} = \overline{|\Delta h|}/\max(2\,\mathrm{flip}\,\tilde z,\ 2\,\mathrm{cv\_rmse}) \).
   (A soft weight, not an on/off switch: small input changes cannot flip it.)

### 7.8 Uncertainty propagation (Monte Carlo)

n = 1,000 draws (seed 0). Each draw picks one outline variant uniformly and **one** scale factor
\( s = e^{\varepsilon}, \varepsilon\sim N(0,\sigma_s^2) \) shared by all measures (fully correlated):
lengths ∝ s, areas ∝ s², volumes ∝ s³ (via area and law), angles and ratios ∝ s⁰. Reported: P50 with the
P5–P95 range; **size class probabilities** = share of draws in each Fell (1994) class
(< 500, 5·10³, 5·10⁴, 2.5·10⁵, 10⁶, 5·10⁶ m³). Hence the characteristic range growth: ×/÷ k for lengths,
≈ k² for area, ≈ k³·(law) for volume. Because angles and ratios do not depend on scale, they are far more
certain than the sizes.

### 7.9 Checks and trust

Issues (each lowers trust: high = 0, medium = 1, low ≥ 2): mirrored-depth instability > 0.1; depth models
disagree > 2×; haze ρ (Spearman of depth vs local contrast) > 0.2; plane inliers < 0.5; object factor > 2×;
Corominas residual \( |\log_{10}(H/L) - (-0.047 - 0.085\log_{10}V)| > 0.4 \). Notes: landslide touches > 15 %
of a photo border → "sizes are minimums"; no typed distance and no object → "enter the distance".
Class doubt: when uncertain or margin < 0.2 the slide is also measured as the runner-up class and a
probability-weighted geometric mean is reported.

### 7.10 Several photos of one site (`fuse_site`)

Per measure: \( \exp(\mathrm{median}\log v) \) with range
\( [\exp(\mathrm{med}\log P_5 - 1.645\,s_b),\ \exp(\mathrm{med}\log P_{95} + 1.645\,s_b)] \), s_b = between-photo
log sd. Errors are treated as fully shared (no √n narrowing) — conservative, since photos of one site share
focal, depth bias and prior.

### 7.11 Size results (no ground truth exists; stability, plausibility, consistency)

v4, 40 photos × 8 phone-like edits, median |log change| (0.10 ≈ 10 %):

| Edit | area | length | width | drop | volume |
|---|---|---|---|---|---|
| mirror | 0.058 | 0.029 | 0.026 | 0.025 | 0.105 |
| darker | 0.089 | 0.041 | 0.039 | 0.039 | 0.144 |
| downscale 640 | 0.161 | 0.086 | 0.075 | 0.073 | 0.224 |
| brighter/warm | 0.217 | 0.129 | 0.104 | 0.101 | 0.231 |
| tilt 3° | 0.247 | 0.133 | 0.135 | 0.127 | 0.275 |
| noise | 0.250 | 0.121 | 0.113 | 0.058 | 0.444 |
| blur | 0.305 | 0.231 | 0.163 | 0.137 | 0.349 |
| JPEG q35 | 0.422 | 0.260 | 0.194 | 0.162 | 0.466 |

Availability 100 %; trust high/medium/low 30/42/28 %; distance plausible (2–300 m) 100 %; slope plausible
98 %; pre-failure surface available 95 %; grains reliable 25 %; object scale used 22 %; same-site log-sd
(11 sites) length 0.40, width 0.45, area 0.80, volume 1.15; 25.5 s/photo (RTX 4060).

---

## 8. Photo sets and video

### 8.1 Matching and two-view geometry (`src/overlap.py`)

Features at long side 1024 after CLAHE (clip 2.0, 8×8) so matches survive auto-exposure; SIFT
(4,000 keypoints, contrast threshold 0.02 for low-texture slopes); RootSIFT (L1-normalise, square root);
FLANN + Lowe ratio 0.8 + mutual check; ≥ 12 matches. Robust fits with MAGSAC++: homography (4 px) and
fundamental matrix (1.5 px), 5,000 iterations, confidence 0.999. Sanity: warped outline convex, area ratio
0.1–10, limited perspective terms. Overlap = mean of the two warped-frame shares.

**Turn vs walk.** Parallax = 75th percentile of the homography transfer error *measured on the
fundamental-matrix inliers* (H's own inliers would always look consistent). Turn if parallax ≤ 1.5 px
(calibrated; the floor for real lenses and hand shake), else "moved". A set is "turn" only if every
spanning-tree link is.

**Linking and order.** A pair links at ≥ 30 inliers and ≥ 3 % overlap (30 = the smallest count with ≤ 0.5 %
unrelated pairs linked in simulation; measured 0.0 %). Union-find components; Kruskal *maximum* spanning tree
by inlier count; order by projected centres (turn) or the tree's longest path (walk).
Overlap bands (turn, calibrated): gap < 0.05, weak < 0.20, duplicate > 0.85, ideal 0.30–0.60;
walk bands 0.35 / 0.55 / 0.92, ideal 0.60–0.80 (defaults, not calibrated). Issues: unmatched, gap, weak,
duplicate, moved, roll > 5°, zoom > 1.15, light > 1.4, wide (> 120°), spacing, order.

### 8.2 Focal from homographies and the mosaic

For pure rotation \( H = K R K^{-1} \); the Szeliski–Shum (1997) closed form gives f from each centred
homography; the median over pairs is used (EXIF first if present). Simulated accuracy: log RMS 0.145
(2 photos) / 0.161 (3 photos), bias ≈ −0.07, val coverage 93–98 % → these sds are used (the 0.08 target failed).
Mosaic: homographies chained along the tree from the reference photo; perspective canvas clipped to ±60°;
gain compensation (Brown & Lowe 2007; gains clipped 0.5–2); squared-distance-transform feathering; edges
trimmed to ≥ 60 % valid; empty corners inpainted (TELEA) and blurred so models see no black wedges; the
mosaic's focal written into its EXIF (tag 0xA405) so the size step uses the right field of view.

### 8.3 Walk-along metric scale

Known baseline \( B = \text{steps}\times 0.75\ \text{m} \) (σ_B = 0.15 in log). Essential matrix
(MAGSAC, 1 px, points mapped into the reference pixel frame), `recoverPose` (cheirality), triangulation;
keep points in front of both cameras, reprojection < 2 px, ray angle > 1°; ≥ 8 points. Depths \( z\cdot B \)
fix the scale of the monocular depth (§7.4 #2). Depth error grows as \( \sigma_Z \approx Z^2\sigma_{px}/(fB) \),
so far scenes need more steps. Simulated (160 pairs): success 71 %, median abs log error 0.120, P90 0.272,
stated sd 0.150 (vs 0.536 prior), **coverage 87.6 %**. On the real server a 4-step simulated walk used
1,548 points and narrowed the length range from 5.7× to 3.3× (max/min).

### 8.4 Type from a set

\( P_{set} = w\,P(\text{mosaic}) + (1-w)\,\overline{P(\text{photos})} \), w = 0.25 chosen out-of-fold
(macro-F1 0.710 vs 0.674 for the middle photo alone; differences between w values ≤ 0.018 are within noise).
Then the same `decide()` rule.

### 8.5 Video and live auto sweep (in the browser; no video is uploaded)

On-phone overlap estimate: gradient-magnitude maps 80 px wide, normalised cross-correlation search
(dx ±92 %, dy ±30 %), overlap = (W−|dx|)(H−|dy|)/(WH); score < 0.3 = no overlap. Sharpness = variance of the
Laplacian at 160 px. **Keyframes:** sample every max(0.25 s, T/400), keep the sharpest frame (≥ 0.5 × median)
inside the ideal overlap band, commit when overlap drops below the band; videos > 180 s refused.
**Auto sweep:** shutter fires when overlap is in band, sharpness ≥ 0.6 × median of the last 8, pan speed
≤ 0.35 frame-widths/s on two ticks, ≥ 1.2 s since the last shot. Headless tests: 4 keyframes on a synthetic pan,
none blurred, overlaps 31–72 %; the auto shutter fired only on the sharp in-band frame.

---

## 9. Decision support

**Field questions** (when uncertain, bad photo, or top-2 margin < 0.2): 8 yes/no questions (fresh scar,
curved scarp, planar surface, blocks, channel, levees, fine material, steep face) with expert likelihoods
\( L_c = P(\text{yes}\mid c) \in [0.05, 0.92] \) from Hungr 2014 (bounded so one answer cannot overrule a
confident model). Bayes update and question choice:

\[
p'_c \propto p_c\,L_c\ (\text{yes}),\quad p'_c \propto p_c(1-L_c)\ (\text{no});\qquad
q^* = \arg\max_q\Big[H(p) - \sum_{a\in\{y,n\}} P(a)\,H(p\mid a)\Big]
\]

with entropy H in bits; stop after 5 questions, when no question gains ≥ 0.05 bits, or when the top class
reaches 0.85. Answers can be undone. The result is shown as *field probabilities* next to (never replacing)
the model's. The likelihoods are not fitted to data and the screen says so.

**Tickable on-site signs** per type with a tally; when uncertain, the top two types' signs side by side.
**Family answer** (§4.5). **Safety card** and **next steps** (retake, add distance, scale shot, deposit
close-up). **Practice quiz** (5 photo-taking pairs). **Site survey** (4 shots: whole slope, scarp, deposit,
scale object) fused by `/fuse`: type = mean of the shots' probabilities; sizes = `fuse_site`; grains from the
deposit shot.

---

## 10. Server and phone app

### 10.1 Server (`src/app.py`)

| Endpoint | Purpose | Limits |
|---|---|---|
| `GET /` | single self-contained HTML page (no external requests except optional OSM map tiles for the image report, §10.3) | — |
| `POST /predict?stage=type\|full` | classify (type in ~2–5 s, returns a job id) or classify + measure | 25 MB body, 40 MP |
| `POST /measure?job=` | sizes for a kept photo; 410 if evicted (phone re-sends) | GPU lock |
| `POST /overlap` | check a set of 2–8 photos | 40 MB, CPU lock |
| `POST /pano?set=&steps=` | join/measure a set | — |
| `POST /fuse` | combine survey shots | 2 MB |

`ThreadingHTTPServer`; one lock serialises decode/predict/save (bounded memory); LRU caches of 6 jobs and
3 sets; 30 s socket timeout; Pillow decompression-bomb guard; parameter validation (distance 0.5–5,000 m,
gravity |g| ≤ 1.01, f35 8–200); errors as JSON. Options: `--token` (access key), `--https` (self-signed,
825 days, SAN = LAN IP) or `--cert`, `--no-save`, `--max-saved`, `--no-dims`, `--vlm`. Uploads (when saved)
are logged with prediction and guidance flags for later labelling and for `tools/guidance_report.py`
(Wilson 95 % CIs of weak-answer rates by guidance use).

### 10.2 Phone app (`ui.py`, `guide.py`, `pano.py`, `guide_data.py`)

Journey stepper Safe spot → Frame → Check → Result. First-use tour; per-session safety checklist; single /
4-shot survey / photo-set modes; distance helper (steps × stride); live viewfinder (requires https): framing
bands, rule-of-thirds, level line and aim from device orientation, live quality meter, one instruction at a
time with an arrow, voice and haptics, shutter always works; instant photo check; upload shrunk to 1,280 px
(EXIF orientation applied; f35 read from EXIF tag 0xA405 *before* shrinking and sent separately); staged
progress paced by learned server times (EMA 0.6/0.4); result cards with all probabilities, quality band,
sizes with 90 % ranges, glossary; history (20 results, IndexedDB); offline queue (retries on reconnect and
every 60 s); image report, HTML report and share (§10.3); GPS, compass bearing and notes. **Hindi**: dictionary (~300 strings + ~18 patterns) applied
by a MutationObserver to every text node and aria attribute (machine-drafted, needs native review).
**Accessibility**: aria-live regions, dialogs with focus return, keyboard (Enter/Space/Esc), reduced motion,
dark mode, high-contrast sun mode, spoken summary. Tested headlessly in Edge (English and Hindi): 51 guidance
checks per language (incl. 12 location/report checks and 11 UX-law checks, §10.4) and the photo-set suite, 0 failures.


### 10.3 Location, GPS marker and reports (`guide.py`, `pano.py`)

**What it serves.** A field record must say *where*: the camera position, which way the camera looked, and
where the landslide itself is. The landslide is usually 20–300 m from the engineer, so the phone's own GPS fix
alone puts the marker in the wrong place by the whole viewing distance.

**Sources, in priority order.**

| Quantity | Source 1 | Source 2 | Notes |
|---|---|---|---|
| Camera position | EXIF GPS IFD (tag 0x8825) of the *original* file, read before the 1,280 px shrink strips it (lat/lon DMS rationals + refs, altitude 0x05/0x06, bearing 0x11, horizontal error 0x1F) | phone fix (`navigator.geolocation`, high accuracy) | the photo's own GPS is the exact place and time of the shot; a phone fix records its age vs the photo time |
| Camera bearing | compass at the shutter (≤ 5 s old) | EXIF GPSImgDirection | camera photos only; gallery photos rarely carry it |
| Distance | typed distance | median model depth of the outlined area (`distance_m`) | |

Location permission is asked only on the user's tap ("Add my location"). Once it is granted, every camera photo
silently gets a fresh fix (`maximumAge` 20 s); a fix that arrives up to 3 min after the photo is attached to
that photo's record and the stored result is updated. Location needs https (browser rule).

**Compass bearing.** iOS: `webkitCompassHeading` (+ `webkitCompassAccuracy`). Elsewhere, from an *absolute*
`deviceorientation(absolute)` event, the back camera looks along the device −z axis. With the W3C rotation
R = R_z(α)·R_x(β)·R_y(γ) in the east-north-up frame:

    v_E = −cos α sin γ − sin α sin β cos γ,   v_N = −sin α sin γ + cos α sin β cos γ,   bearing = atan2(v_E, v_N)

This is valid when the phone is held upright, as it is for slope photos (the formula gives 0° = north for
α = 0, β = 90°). The bearing is discarded when the horizontal component is below 0.2 (camera pointing straight up
or down). It is magnetic north; the declination in the Indian Himalaya is under 1°, which is far below the
compass error.

**Landslide position.** The destination point on a sphere (R = 6,371,008.8 m) from the camera (φ1, λ1),
bearing θ and distance d, with δ = d / R:

    φ2 = asin(sin φ1 cos δ + cos φ1 sin δ cos θ)
    λ2 = λ1 + atan2(sin θ sin δ cos φ1, cos δ − sin φ1 sin φ2)

The 1-σ radius combines the GPS error, the bearing error and the distance error:

    σ = sqrt(σ_GPS² + (d·σ_θ)² + σ_d²)

| Term | Value used |
|---|---|
| σ_θ | the phone's own compass accuracy when it reports one, else 15° |
| σ_d | 5 % of d for a typed distance; 30 % of d for model depth (the depth log-sd is about 0.25–0.3, §7.2) |
| σ_GPS | the phone's or the EXIF's stated error, else 10 m |

Example: GPS ±8 m, bearing ±10°, typed 100 m gives ±19.8 m, which the headless test reproduces.

**Image report (one JPEG, 1,600 px wide, landscape).**

The first version was a single 1,080 px column, about 1 : 2.5. That is awkward on a phone gallery, in a chat preview
and in a printed annex, and its long phrases wrapped onto second lines. It is now a two-column sheet of about 8 : 7
(1,600 × about 1,350 px for a full result).
- **Header across the top:** the title on the left; the date and time, shot and set on the right.
- **Left column (900 px):**
  - the photo, with the measured outline when there is one, carrying a GPS-camera style stamp: a pin, the position in DMS ± error, decimal degrees, altitude, bearing with its cardinal direction, the time, and the estimated landslide position;
  - below it, the size table: measure, value, 90 % range, plus size class, slope, distance and grains, then the scale source and the depth trust.
- **Right column (588 px):**
  - type, confidence and the top-3 probability bars;
  - the field-answer result;
  - the location map. It uses OSM tiles at zoom 18 → 3, chosen so that d + σ fits in 40 % of the panel. Markers: a blue camera dot with its GPS-error circle, a view cone of ±σ_θ, a dashed line along the bearing, and a red pin at the landslide with its σ circle. Map furniture: scale bar, north arrow and attribution;
  - under the map, the coordinates as aligned key : value lines.
- **Balancing:** photo quality and the field check (answers, signs seen, weather, notes) are placed in whichever column is shorter at that point, so the two columns end at nearly the same height.
- **Footer across the bottom:** the disclaimer on one line; model, WGS-84 and the map credit on the next.
- **One line per phrase:** nothing is wrapped. A phrase that does not fit shrinks, down to 72 % of its size. Only if it still does not fit does it end in "…". The web page report keeps the full text, for example long notes.

The JPEG also carries EXIF written by the phone, so gallery apps and GIS place the file on a map:

| Tag | Content |
|---|---|
| ImageDescription | a summary of type, confidence, status, position and landslide position |
| Software, DateTime | the app name and the photo time |
| GPS IFD | version 2.3, lat/lon as DMS rationals, altitude, bearing (ref M), WGS-84 datum, horizontal error |

The EXIF block is a little-endian TIFF, inserted as APP1 after the JFIF APP0.

**Robustness (design choices).**

| Failure | Handling |
|---|---|
| Map tiles slow, blocked, offline or tainting the canvas | tiles are all-or-nothing (5 s each); any failure, including a SecurityError at `toBlob`, redraws the whole report with a plain grid map; offline phones never request tiles |
| One section fails (missing or odd field) | that section is blanked and listed as "not drawn"; the rest of the report is kept (same per-section guard in the HTML report) |
| Canvas cannot be drawn at all | falls back to the HTML report automatically |
| Download blocked (in-app browsers, iOS) | download link → share sheet → open in a new tab; the report image is also shown on the page (long-press to save) with "Save again" and "Share image" buttons that run on a fresh tap, because share needs a user gesture |
| Photo missing (old history entry) | the stamp and all metrics are still drawn; the photo is listed as not drawn |
| Unescaped text in the HTML report | every value is now escaped; unknown classes in the ticked signs no longer crash it |
| Stale phone fix | its age vs the photo time is printed in the report |

**Privacy.** Coordinates stay on the phone. The upload is the shrunk JPEG without EXIF, so the server never
receives or logs a location. When online, the image report asks tile.openstreetmap.org for the 4–6 tiles
around the site; this is the only network request that reveals the area. It happens only on "Save image
report" and is covered by the OSM tile policy, with low-volume, user-initiated use and attribution.

**Verified (headless Edge, English and Hindi, 40/40 each).**
- DMS formatting.
- Destination point: 100 m at 45° comes back as 100.00 m at 45.00°.
- σ formula; no location gives no marker; no bearing gives no landslide position.
- A 1,600 × 1,356 JPEG with all sections (was 1,080 × 2,532 as one column). Its EXIF GPS reads back to 1e-6° with the app's own reader, altitude, bearing and error included, and PIL decodes the file and the GPS IFD independently.
- Odd results, no photo and no location still produce both reports.
- A late GPS fix is attached to the shown photo.
- The image report is shown on the page and saved, and so is the page report.


### 10.4 Interface audit: 20 UX laws and 20 "looks machine-made" signs

The whole page was checked against two public lists:
- 20 UX laws: Laws of UX, Yablonski;
- 20 signs that an app "looks vibecoded".

The checks covered every mode (single, survey, photo set), light and dark, English and Hindi, at a true 375 px
phone width (rendered in an iframe, because headless Edge cannot be narrower than about 496 px).

**Measured before → after.**

| Measure | Before | After | How |
|---|---|---|---|
| Visible text below WCAG AA contrast (result page, light + dark) | 5, e.g. dark-mode links 3.34, light subtitle and footer 4.13; white on the gradient button down to 2.40 | **0** of 71–86 text elements | in-page scan of every text node against its effective background |
| Controls under 44 px (all three modes) | many: small buttons ~34 px, summaries ~20 px, a 24 px delete button | **0** | in-page scan of every visible control |
| Decorative gradients in the UI (logo and glyphs excluded) | 11 | 0 | source scan |
| Glass blur (`backdrop-filter`) | 2 | 0 | source scan |
| One-off inline margins | 46 | 0 (spacing utilities on a 4 px scale) | source scan |
| Em dashes in visible text | 3 | 0 | source scan + in-page check |
| Invalid `font:… inherit` shorthands | 9 (buttons fell back to 13.3 px) | 0 | source scan |
| Types shown at once | 6 | 3 (+ "Show all 6 types") | UI test |
| Size rows shown at once | 11 | 6 (+ "More measurements") | screenshot |
| Report actions | 3 equal buttons | 1 primary + 2 secondary | UI test |

**Each point and what was done.**

| # | Point | Status before | Action |
|---|---|---|---|
| U1 | Aesthetic-usability | busy: gradients, blobs, pills | flat tokens, one accent, one type scale, 4 px spacing scale |
| U2 | Hick's law | 3 equal report buttons, 6 types, 11 size rows | one primary action per card; top 3 types; key sizes first |
| U3 | Fitts's law | many targets 20–34 px | every control ≥ 44 px (measured); the set-photo delete button has a 44 px hit area |
| U4 | Jakob's law | mostly standard | help top right, segmented mode control, standard Save / Share words, share sheet |
| U5 | Miller's law | 11 size rows in one list | chunked: measures + size class + slope + grains; the rest grouped |
| U6 | Doherty threshold (< 400 ms) | report feedback only by toast | the button itself shows a spinner and "Making the image report…" in the same frame; the instant photo check stays on the phone |
| U7 | Proximity | location line separate from report buttons; distance hint far from its box | location inside the report card; the hint directly under the distance box |
| U8 | Similarity | two button systems with different colours | one button family (primary / ghost / small) on the same tokens |
| U9 | Common region | report actions loose on the page | one "Save and share" card: location, actions, result of saving |
| U10 | Visual hierarchy | a "Good" quality card above the answer competed with it | a clean photo is one quiet line inside the result card; problems stay on top in colour |
| U11 | Progressive disclosure | everything open | "Show all 6 types", "More measurements", glossary, distance helper |
| U12 | Recognition over recall | icon-only language button "हिं", steps only in text | language button names the language ("हिंदी" / "English"); the distance hint shows accepted forms; the saved file name is shown |
| U13 | Von Restorff | safety had the same weight as other cards | safety is the one filled warning panel, placed right after the answer |
| U14 | Peak-end rule | the page just stopped after saving | "Report saved" line + preview + "Start the next observation" |
| U15 | Goal-gradient | 4-step journey ended at Result | 5th step "Report": Result done, Report highlighted until the report is saved (measured 5/5 after saving) |
| U16 | Serial position | safety in the middle; tech pills last | answer first; safety second; save and next observation last; tech details as one quiet line |
| U17 | Tesler's law | location only from a buried button | the first camera tap asks for location once (https), and fixes attach automatically (§10.3) |
| U18 | Postel's law | number box rejected "40 m", "130 ft", "40,5" | accepts 40, 40.5, 40,5, 40 m, 40m, 130 ft, 0.5 km and Devanagari digits; says "Sizes will use 39.6 m" |
| U19 | Occam's razor | eyebrow labels, three tech pills, "nothing to fix" card, decorative tip icons | removed or merged; tips became numbered steps |
| U20 | Feedback loops | silent distance box | live parse feedback; ticks update a tally; save → spinner → "Report saved"; haptic tick on save |
| V1 | Purple-to-blue gradient | none (teal brand) | kept none |
| V2 | Gradient hero text | none | — |
| V3 | Emojis in headings | none | — |
| V4 | Inter everywhere | system UI fonts (offline, fast, Devanagari) | kept; Noto Sans Devanagari added to the stack |
| V5 | Coloured border cards | gradient accent stripe on safety and error cards | removed; filled warning panel instead |
| V6 | Glassmorphism | blurred chip and modal backdrop | solid 86 % chip, solid scrim (also cheaper on low-end phones) |
| V7 | Low-contrast dark mode | links 3.34 : 1 | dark tokens ≥ 7.9 : 1 for links, 8.1 : 1 for the primary button |
| V8 | 3 icon boxes in a row | none | — |
| V9 | Badge above the headline | uppercase letter-spaced eyebrow on ~28 cards | plain sentence-case section labels; removed where they repeated the heading |
| V10 | Lucide icons everywhere | decorative icons on tips | icons only where they carry meaning (camera, gallery, warning, ticks) |
| V11 | Untouched shadcn UI | not used | — |
| V12 | Fade-in on scroll | none (bars grew on load) | removed the bar animation; only spinners move; reduced motion respected |
| V13 | Cursor-following beam | none | — |
| V14 | Buttons fade on hover | brightness filter | solid colour change, 1 px press |
| V15 | Inconsistent spacing | 46 inline margins of 18 sizes | 4 px scale tokens + utilities |
| V16 | Em dashes everywhere | 3 in visible copy | replaced by colons (Hindi keys updated) |
| V17 | Generic buzzword copy | none found (scan for 14 buzzwords) | copy stays concrete |
| V18 | Serif italic accents | none | — |
| V19 | Space Grotesk + Instrument Serif | none | — |
| V20 | Grain over a gradient | three radial colour blobs behind the page | flat paper background |

**Found on the way:**
- **Invalid `font` shorthands.** Writing `font:650 .9rem inherit` is invalid CSS, so browsers dropped it, and every small button and segmented button had been showing the browser's 13.3 px default font.
- **History thumbnails could stall saving.** The thumbnail used `fetch()` on a data URL. That can stall, and because results are saved in order, every later save waited behind it. It now decodes the image directly with a 5 s limit. This also removed a test flake.

**Kept on purpose.**
- Gradients stay in the logo and the type glyphs, where they are brand art.
- The dashed red border on a failed-photo result and the coloured quality bands stay, because they are status information, not decoration.

The checks for U2, U3, U13, U15, U16, U18, U20, V7, V15, V16 and V20 are in the headless test (§10.2).


### 10.5 Visual design: "Contour", and the wording of every block

**Who reads the page, and in what state.** Two readers use the same page.
- **The site engineer** is standing below an unstable slope, often in glare or rain, holding a phone in one hand,
  sometimes under time pressure from traffic or weather. They need to see three things at a glance:
  what it most likely is, whether it is safe to stand here, and what to do next.
- **The office engineer or reviewer** reads the saved report later, at a desk. They need to know:
  what was observed, where and when, by which method, how strong the answer is, and what its limits are.

Under stress, attention narrows. People read the first words of each block, notice one colour that stands out,
and trust a page that looks calm and orderly. Every design choice below follows from that.

**Concept.** The app is drawn as a topographic field instrument, the visual language engineers already read every
day on survey sheets. No generic app template is used.

| Element | Choice | Why (perception) |
|---|---|---|
| Paper | cool lichen grey `#E9EDE6`; night-survey `#0F1A1B` in dark mode | low chroma and cool hue keep arousal low for a stressed user; not the cream/terracotta or black/neon look of template pages |
| Ink | spruce-slate `#15242A` | about 14 : 1 on the paper, so text stays readable in glare without the harshness of pure black |
| Accent | the logo's moss teal `#17695A` (dark mode `#5FD1A8`) | one accent only, always meaning "you can act here or this is done" |
| Hazard | survey flagging-tape orange `#FF6A1A`, striped with ink | the only saturated warm colour on the page, so the eye finds it before reading (Von Restorff). It reuses a signal crews already know from flagged slopes |
| Headings and numbers | DIN family from the phone itself: "DIN Alternate" on iOS, Bahnschrift on Windows, a condensed Roboto on Android | road-sign and map lettering, designed to be read at a glance and at a distance; fixed-width numbers line up in columns; no font download, so the page still works offline |
| Body | the system UI face, plus Noto Sans Devanagari | the face people already read all day; Hindi renders correctly |
| Structure | information sits on open paper, separated by a wavy contour line; only blocks you **act on** (capture, save, questions) or must **stop for** (result, safety, errors, photo problems) get a container | removes the "identical rounded cards" look. A boxed panel now means something (common region): a box is either a decision or a warning |
| Corner radius | 12 px on buttons and 18 px on panels | the radius follows the hierarchy, not one value for everything |
| Header | static contour lines of a hillside behind the title, with a slide hollow above and its deposit lobe below, fading out | says "landslide field tool" before any word is read; static, so it never competes with the content |
| Journey | the five stations rise along a trail towards "Report" | goal-gradient as an ascent: each completed step is visibly higher, and the report is the summit |
| Safety | a filled panel with a flagging-tape band on top | a domain signal, not decoration; the one block designed to interrupt |
| **Signature: summit gauge** | the type glyph stands on its summit, surrounded by 6 contour rings. The ring shape is drawn from a seed (the type name), so every type has its own terrain. Confidence inks the rings from the foot upward: 87 % inks 5 of 6 rings, 46 % inks 3. Colour: teal for a confident answer, amber for uncertain, red for a failed photo | confidence is shown as how far up the hill the answer has climbed. Pre-attentive (count, colour), but the exact number sits beside it, so nothing is hidden behind the metaphor |
| Motion | one orchestrated moment only: the inked rings draw in from the foot upward (70 ms apart, about 1 s in all), when a result appears. Nothing moves on scroll. Reduced motion shows the final state | one peak of delight at the moment of the answer (peak-end); no scattered effects |

**Wording: what each block says, and why it is placed there.**

| Block, in order | Text | Reasoning |
|---|---|---|
| Header | "Landslide Type Check" / "Field classifier after Hungr 2014" | names the job and the standard. A reviewer trusts a named classification more than a brand. The middle-dot separator is gone |
| Journey | Safe spot, Frame, Check, Result, Report | starts with safety, so the first thing asked is "are you standing somewhere safe"; ends with the deliverable the office needs |
| Capture | "Photograph the slope from below" plus 3 numbered steps | an imperative heading tells the user the action; the three steps are a real sequence, so numbering is honest |
| Distance | "Distance to the slope (optional)" / "Makes the sizes more accurate. 40, 40 m or 130 ft all work." | says why to fill it in and which inputs work, at the moment of input |
| Result kicker | "**Most likely type**", was "Landslide type" | a model gives a hypothesis to check, not a verdict. Engineers are trained to verify; the wording invites that instead of false certainty |
| Confidence | "**Model confidence: High / Moderate / Low** 87 %" plus "Answers below 60 % are marked uncertain." | a bare percentage is read as a probability of being right. The band word (High ≥ 80 %, Moderate ≥ the 60 % threshold, Low below it) gives the meaning in one word, and the one-line rule tells the office reader how the threshold works. The word "model" assigns the claim to the tool, not to the engineer |
| Class line | "Hungr et al. 2014: …" on its own line under the head | the standard term a report needs, given full width so it no longer squeezes the title |
| Safety (2nd) | type-specific, one paragraph | serial position: read second, right after the answer, before any detail |
| All types (top 3, then "Show all 6 types") | names + score | shows what to rule out; the full list is one tap away |
| Check on site | "Tap each sign you can see on site." + tally | turns the model's answer into the engineer's own observation, so the record shows what a person confirmed |
| Sizes | value + 90 % range on every line; "More measurements" folded | every number carries its uncertainty, which an office reviewer will ask for |
| Save and share | one primary "Save report" | the deliverable; one obvious action |
| Meta line | "model, seconds" | traceability without clutter. The threshold moved to the confidence block, where it is understood |
| Footer | "Decision support only: confirm with a geologist or geotechnical engineer before acting." | states responsibility plainly, as a firm's QA process expects |

All middle-dot meta strings in the page, the reports and the Hindi text were changed to commas or colons, with the
English keys and Hindi translations changed together.

**Coverage of the 40 points (§10.4) by this pass.**
- **Aesthetic-usability, Visual hierarchy:** the identity above; the result now has one focal element.
- **Von Restorff:** the hazard tape is the only saturated warm colour.
- **Goal-gradient:** the climbing journey and the summit.
- **Peak-end:** the one draw-in moment, plus the existing "Report saved" end.
- **Common region, Similarity:** a box means action or warning; buttons, panels and chips each have one radius.
- **Recognition over recall:** a band word next to the number.
- **Feedback:** the gauge colour follows the status.
- **Machine-made signs:**
  - no gradients in the UI. The tape stripe is a hazard signal, not a background, and the page background stays flat; this is checked;
  - no glass effect, no emoji, no Inter;
  - no identical cards;
  - no eyebrow badges;
  - no middle-dot or em-dash strings;
  - no animation on scroll;
  - no serif-italic accents.

**Measured after the redesign:**
- **Contrast:** 0 text elements below WCAG AA, checked on 75–90 text elements in each of the ok, uncertain, family and bad-photo results, in light and dark mode.
- **Tap targets:** 0 controls under 44 px in the single, survey and photo-set modes.
- **Headless tests:** 51/51 guidance checks in English and in Hindi; the photo-set suite completes in both languages with 0 script errors.

**Not built yet (from the same review):**
- **Observer name and organisation on the report.** A firm's reviewer will expect it. It needs a stored profile field and consent, so it was left for a later change.
- **A short reference ID printed on the report** for correspondence. Today the file name carries the date and time.


### 10.6 Fixes after review on a real phone session

The redesign (§10.5) was then reviewed on a live session: dark mode, desktop width, survey mode, a real poor photo.
Every problem found was fixed.

| Problem seen | Cause | Fix |
|---|---|---|
| "High" printed on top of "Model confidence", inside a dashed orange box | the new class `band` already existed for the viewfinder's dashed framing guides (absolute position) | renamed it to `cband`; a new headless check (9 CLASH) fails if any viewfinder style reaches the result |
| contour lines crossed the title, and stopped sharply at the column edges on a wide screen | lines at full strength, limited to the 620 px column | lines at 55 % strength, full window width |
| at 94 % every ring was inked: a bullseye, plus a dark disc behind the glyph | ring count was rounded | rings are counted down (the top ring is inked only at 100 %); no disc |
| photo-quality "Poor" panel was orange, like the hazard tape | old quality colours | quality uses amber; orange now means "hazard" and nothing else |
| the same caveat ("ranges were checked on usable photos") appeared twice | quality panel and size block both said it | the quality panel says only "the confidence and sizes are the model's own"; the size caveat stays with the sizes |
| three bright filled buttons under "Next steps" | every action used the primary style | only the first action is filled; rows sit on the paper with dividers |
| every survey shot row was boxed | border on all rows | only the current shot is boxed |
| the photo label said "Landslide type"; the result said "Most likely type" | two words for one thing | one wording |
| "sizes are minimums. turn right or step back." | lowercase after a full stop | sentence case |
| scale method text (depth ensemble, x2.075, n = 83) shown openly to the site user | | under "How the sizes were measured", kept for the office reader |
| the model line had no label | | "Model: …" |
| "Help decide" repeated the type list right above "All types", and sometimes said only "No further question would change the answer much" | card drawn even when there was nothing to ask | the card is hidden when there is nothing to ask and nothing answered; its bars appear only after an answer changes them |
| section labels were small grey text, hard to find when scrolling | | labels in the DIN heading face, ink colour |

After these fixes:
- **Contrast:** 0 text elements below AA, light and dark, in 4 result states.
- **Tap targets:** 0 controls under 44 px.
- **Guide tests:** 52/52 checks in English and in Hindi (the earlier run of 51 plus the new 9 CLASH check).
- **Photo-set suite:** complete in both languages, 0 script errors.


### 10.7 Design scheme: functional Bauhaus on the Contour base

**Choice.** Nineteen named graphic-design schemes were compared for this app's two readers (§10.5): the site
engineer in glare and under stress, and the office reviewer judging credibility.

| Role | Scheme | Why |
|---|---|---|
| Base | **Bauhaus**, used as a working system rather than a poster style | best fit for both readers |
| Diagrams only | **Isometric** | engineers read technical drawings fluently |
| One instrument cue | **Skeuomorphism**, a light touch | the summit gauge |
| Rejected | Neumorphism | control edges around 1.1–1.5 : 1, it disappears in sunlight, and pressed versus unpressed is ambiguous |
| Rejected | Glitch | it imitates malfunction |
| Rejected | Memphis, Vaporwave, Psychedelic | they signal "not serious" |
| Rejected | De Stijl | it uses red, yellow and blue as decoration, which breaks the safety colour code |

**Why Bauhaus, in terms of perception:**
- **Fluency:** a grid, plain shapes and no ornament keep extraneous load low. Information that is easy to process is also judged more true and more trustworthy (Reber, Schwarz and Winkielman, 2004).
- **Credibility:** in Fogg's 2003 Stanford study, "design look" was the most-cited factor in whether people trusted a site.
- **Safety colours:** its primary palette maps onto the ISO 3864 safety colours engineers already know from site signs: red for danger, yellow or amber for warning, blue for information, green for safe.
- **Lineage:** the DIN typeface (DIN 1451, 1931) comes from the same functionalist tradition.

**What changed.**

| Element | Before | After | Reason |
|---|---|---|---|
| Section dividers | wavy contour line | 1 px hairline plus a 32 × 3 px ink bar at the left edge | one structural mark; the waves stay only in the header art and the gauge |
| Control edges (ghost buttons, inputs, small buttons, round icon buttons, mode switch, checklists, selects) | 1.3–2.1 : 1 | ≥ 3 : 1, from a new `--edge` token, in light and dark | WCAG 1.4.11 non-text contrast: users must see what can be tapped, in glare |
| Selected capture mode | lighter fill plus a soft shadow | outlined with the edge colour, bold label | pressed versus not pressed is unambiguous |
| Status shapes | coloured dots | triangle = caution or failure (photo chip, photo-quality marker); circle = fine or information; the camera location is a blue circle | ISO meaning without relying on colour, which helps the about 8 % of men with colour-vision deficiency |
| Caution note ("Not confident…") | grey side bar | amber side bar | same caution colour everywhere |
| Corner radius | 12 to 18 px | buttons 8, panels 12, chips fully round | crisper geometry; the radius still follows the hierarchy |
| Panel shadow | soft drop shadow | 1 px edge only | flat holds up better in sunlight; depth is kept for modal sheets |
| Model line and footer | centred | left-aligned, footer above a hairline | asymmetric grid; provenance reads like a document footer |
| Tour card "Stand below, see it all" | flat side view | isometric site diagram: observer in front, slope block behind, dashed sight lines to scarp and toe, a 20–80 m dimension line | spatial instructions read faster as a technical drawing |
| Image report section titles | title and full rule | title, full rule and a short ink bar | the same mark as the page |

**Measured after the change:**
- **Text contrast:** 0 text elements below AA, light and dark, in 4 result states.
- **Control edges:** 0 controls below 3 : 1 out of 10–11 per result page, light and dark. This scan is new. Computed from the colour values, the previous borders were 1.3–1.9 : 1 in light mode and 1.4–2.1 : 1 in dark mode. The new edge colour is 3.3–3.6 : 1 in light mode and 4.4–4.9 : 1 in dark mode.
- **Tap targets:** 0 controls under 44 px in all three modes.
- **Guide tests:** 52/52 in English and in Hindi.
- **Photo-set suite:** complete in both languages, 0 script errors.

### 10.8 Visual identity: "Field Atlas at dawn"

The Bauhaus pass (§10.7) fixed function: edges, shapes, contrast. It did not give the app a character. This pass
redraws the whole surface as a **plate from a geological field atlas**. The functional rules of §10.7 stay as they
are: edge colour, ISO shapes, 44 px targets and the amber/red hazard code.

| Element | Design | Why |
|---|---|---|
| Header | a landscape drawn in inline SVG behind the title: four ridges in aerial perspective, mist between them, and a small landslide scar with its debris fan on the nearest ridge. The scene is dawn in light mode and moonlight with stars in dark mode | the first thing on screen is the subject itself, a slope seen from below, which is the view the app asks the engineer to photograph |
| Motion | ridges move at different speeds when the page scrolls (parallax 0–0.42); mist drifts over 38–52 s and stars twinkle; all of it is off under `prefers-reduced-motion` | one quiet depth cue; nothing moves on its own near the controls |
| Type | headings in a book serif (Iowan Old Style, Palatino, Noto Serif / Noto Serif Devanagari, then Georgia); body stays sans | atlas plates and survey reports use serif titles; numbers such as 87 % read like a printed figure |
| Panels where you act (capture, result, save, ask, safety) | atlas plates: paper surface with an engraved inner rule 5 px inside the edge | a framed plate says "this is the instrument"; the open text between plates stays unframed |
| Section dividers | a 12 px band of lithology symbols as in a geological column: sand dots, shale dashes, limestone bricks and conglomerate pebbles, changing down the page | the divider carries the subject's own drawing convention instead of an arbitrary line |
| Colours | light: mist grey-green ground `#e7ebe8`, paper `#fbfaf6`, ink `#1b272c`, forest teal `#1a6a5b`; dark: night blue `#0d1420` with a paler teal | the palette of a misty hill slope; teal = vegetation and "done", warm colours kept only for hazard |
| Buttons | fully rounded pills | a different shape from the plates, so controls and containers separate at a glance |
| Hindi | Devanagari display lines get line-height 1.3 | matras above the line need room; at 1.05 the two title lines touched |

The landscape is drawn from a fixed seed, so it looks the same on every visit. It uses only CSS colour tokens and
no image files, so the page still works offline and the scene follows the theme without a second drawing.

**Measured after the change:**
- **Text contrast:** 0 text elements below AA, light and dark, in 4 result states (67–82 elements per state).
- **Control edges:** 0 of 10–11 controls below 3 : 1, light and dark.
- **Tap targets:** 0 controls under 44 px in all three modes.
- **Guide tests:** 52/52 in English and in Hindi, 0 script errors.
- **Photo-set suite:** complete in both languages, 0 script errors.

### 10.9 The atlas scheme carried into every layer

§10.8 set the identity at the top of the page. This pass carries the same scheme, a printed geological field atlas,
into every layer: material, motion, controls, data, type and secondary screens. Each element borrows a real atlas or
survey convention instead of a generic web pattern.

| Layer | Element | Atlas convention it borrows | What it does for the reader |
|---|---|---|---|
| Material | paper grain on the page, the plates and the sheets (inline SVG noise, 4–10 % alpha) | printed paper | the screen reads as a document, not as glass |
| Material | the plate's inner rule is an outline 7 px inside, with 8 px blocks where it turns at the corners | map neatline with corner blocks | marks the panels you act on |
| Landscape | ridges fade into valley haze, the sun or moon has a glow, the moon has craters, pine silhouettes on the two near ridges | aerial perspective in survey sketches | depth and scale from shapes alone |
| Landscape | the slide is built from a centreline: a crown arc, a chute that narrows, a fan that widens and thins downslope, with debris stipple. It sits on the highest point of the near crest, so it shows above the panel on phone and desktop | a field sketch of a debris slide | the subject of the app is in the first view |
| Motion | the ridges assemble from far to near on load, the sun rises, then the header and the first plate settle in (about 1.7 s, once) | — | one orchestrated moment; everything else moves only in answer to an action |
| Motion | the result reveal: contour rings climb, the type name settles, the glyph pops, the confidence ruler and the type bars grow | — | shows that a new answer arrived |
| Steps | the walked trail is a solid line in the brand colour, the trail ahead is dotted, the current station breathes slowly | trail symbols on a topographic map | where you are and what is left, without reading |
| Mode switch | one engraved thumb slides between Single photo, Site survey and Overlapping set | — | the choice is a physical position |
| Buttons | a flat fill with a lit top edge and a pressed lower edge (inset shadows, no gradient); a springy press; hover lifts by 1 px; the icon nudges | — | tactile feedback in glare, where colour change alone is hard to see |
| Disclosures | a chevron that turns when opened; the opened content unfolds | — | shows that more is hidden, and where it went |
| Confidence | a ruler graduated in tenths, with the "uncertain below" threshold (60 %) as an upright mark; the reading is brand teal, amber when uncertain, red for a bad photo | an instrument scale | shows the distance to the threshold without extra words |
| Size table | label, dot leader, figure; the 90 % range in italics | an atlas index | the eye travels from name to value |
| Type | italic serif for the field-guide labels ("Most likely type"), the Hungr citation, the step numerals, the colophon and the input hints; old-style figures in running text, lining tabular figures in data | book and citation conventions | labels, citations and data are distinct voices |
| History | thumbnails mounted like prints, with a paper margin and a hairline frame; type names and percentages in serif; poor-photo tags as amber or red outlines with the ISO triangle; ruled rows | specimen register | a field record, not a list of files |
| Sheets | grain paper with a handle; they rise on a spring over a blurred, dimmed page; subsection titles and list numerals in serif | — | the sheet is a separate page laid on top |
| Small parts | survey-tape stripes moving on the progress bar; a light sweep on the loading skeleton; a toast with a brand edge that springs up; the tour dots stretch on the current card; ticks pop when a sign is checked; brand-coloured caret, selection, accent and scrollbar | — | the same material and motion language everywhere |

Constraints kept: system fonts only and no network requests, so the page still works offline. All motion is off
under `prefers-reduced-motion`. Text contrast ≥ AA, control edges ≥ 3 : 1, targets ≥ 44 px. The "flat primary
button" check from the §10.4 audit still holds, because the depth comes from inset shadows on a flat fill.

**A browser detail found on the way:** the walked trail first used a custom property set by a `:has()` selector.
Chromium did not restyle the `::after` element when the step changed: the parent reported 90 %, the line stayed at
10 %. The step function now sets `--walk` itself.

**Measured after the change:**
- **Text contrast:** 0 text elements below AA, light and dark, in 4 result states.
- **Control edges:** 0 controls below 3 : 1.
- **Tap targets:** 0 controls under 44 px in all three modes.
- **Guide tests:** 52/52 in English and in Hindi. One English run first showed a timing flake in the history check; two reruns passed 52/52.
- **Photo-set suite:** complete in both languages, 0 script errors.

---

## 11. Deployment

| Option | Status | Measured |
|---|---|---|
| Laptop + LAN / hotspot | default; `--https` for the live camera | type ≈ 2–5 s, sizes ≈ 25 s |
| Laptop + Cloudflare quick tunnel (`tools/serve_public.py`) | **working**: app on 127.0.0.1, tunnel over HTTP/2 (QUIC blocked on this network), random https link per start | page 2.4 s, full result with sizes 40 s |
| Hugging Face Docker Space (CPU) | files ready (`deploy/hf_space`, `tools/build_hf_space.py`), **refused**: Docker Spaces now need PRO | CPU 2 threads: startup 27–46 s, type 6–19 s, sizes ≈ 8 min → planned `--no-dims` |

---

## 12. Engineering practice

- **Leakage guards in code:** every model stores its training ids and a content fingerprint of
  split + labels (SHA-1 of the sorted table); `eval.py`, `system_test.py` and `check_integrity.py` refuse a model
  that saw a test photo or is stale.
- **`tools/check_integrity.py` (ALL OK before every commit):** files exist, ids unique, every photo split and
  labelled, no site spans splits, no lock/tmp leftovers, embedding caches complete, no test near-duplicates in
  train/val (cos ≥ 0.95), model fingerprints current, results newer than models.
- **Reproducibility:** fixed seeds; per-item SHA-256 seeds for simulations so resumed runs are identical;
  atomic CSV/cache writes; cross-process lock with stale-lock recovery; selection code hash stored with the model.
- **Resumable compute:** long jobs run as ≤ 540 s foreground chunks with state files (the laptop kills idle
  background jobs under memory pressure).
- **Calibration JSON next to the code** that reads it (`src/photo_check.json`, `overlap_check.json`,
  `focal_check.json`, `models/dimension_object_prior.json`), each with n, split and method.
- **Two full audits** (2026-10-16) fixed leakage, selection on test, unstratified folds, site domination,
  mislabelled South-Asia tags, subgroup F1 counting absent classes, and many crash paths; everything was
  re-run (identical test results after the second audit).

---

## 13. Design decision log

| # | Decision | Alternatives considered | Evidence / reason |
|---|---|---|---|
| 1 | 6 visible classes + reject | 32 Hungr types; merge flows | invisible properties; flows kept separate, family answer instead |
| 2 | Build own ground-level dataset | overhead datasets | viewpoint mismatch; none exist |
| 3 | Title searches over category trees | categories only | reject 62 % vs 82 % |
| 4 | Split by linked site, before labelling | split by photo / by category | category split leaked ~40–50 test photos |
| 5 | Frozen backbones + linear heads | fine-tune ConvNeXt; zero-shot VLM | test F1 0.784 vs 0.665 vs 0.327 |
| 6 | Three-backbone mean ensemble | single backbones; log pool; stacking; concat | robust score 0.676 best; alternatives ≤ noise or worse |
| 7 | Selection by robust score incl. 3 shift tests | CV only | deployment differs in region/camera |
| 8 | Site-balanced metrics | photo-weighted | one site = 132 photos |
| 9 | Phone-style copies, no vertical flip | standard ImageNet aug | field input is phone; viewpoint is signal |
| 10 | Selective prediction at 0.6 | always answer | 88 % accuracy at 73 % coverage, transferred to test (85.7 %) |
| 11 | Family answer when unsure | top-1 only | related-type answer still useful |
| 12 | Show results even for failed photo check | block bad photos | gate falsely rejects 17 % of usable photos |
| 13 | Percentile-calibrated photo check, q = 0.5 | hand thresholds | ≤ 5 % false flags; 3.9 % on val |
| 14 | Hybrid "networks propose, statistics decide" sizes | end-to-end network | no measured sizes to train on |
| 15 | Log-space everything, Monte Carlo ranges | point estimates | errors multiplicative; scale shared across measures |
| 16 | ZoeDepth dropped | 3-model ensemble | 4–6× too close; contradicted by objects |
| 17 | Known-object prior refit with depth covariate | old ×1.53 (n = 4) | coverage 62.7 % → 94.0 % (honest beats narrow) |
| 18 | Graph-cut λ by stability selection | fixed λ | synthetic IoU 1.00 vs 0.55 |
| 19 | Soft weights instead of on/off switches | thresholds | volume stability blur 0.60 → 0.35 |
| 20 | Volume = law ⊕ pre-failure surface | law only | uses visible relief when it exceeds noise |
| 21 | Walk-along stereo with typed steps | object prior only | sd 0.150 vs 0.536, coverage 87.6 % (simulated) |
| 22 | Mosaic weight w = 0.25 | 0, 0.5, 1 | best OOF F1 (within noise) |
| 23 | Keyframes chosen on the phone | upload video | field bandwidth; reuses the set pipeline |
| 24 | Type first, sizes after (two-stage) | one call | type in seconds; user acts while sizes compute |
| 25 | Bayesian questions with bounded expert likelihoods | free-text checklist | principled update; cannot overrule model |
| 26 | Single self-contained page, offline queue | external libs, online only | field connectivity |
| 27 | AI annotation with blind test and audit trail | human labels | time; flagged as the main open item |
| 28 | Landslide position = camera + distance along compass bearing | phone fix only; manual map tap | the fix alone is off by the viewing distance (20–300 m); stated σ instead of false precision |
| 29 | Image report drawn on the phone (canvas) with EXIF GPS | server-rendered PDF; HTML only | works offline, no location sent to the server, opens in any gallery / WhatsApp, GIS-readable |
| 30 | OSM tiles optional, all-or-nothing, grid fallback | bundled offline map; always online map | single-page app stays small; field phones are often offline |
| 31 | Location asked on the first camera tap, then refreshed silently | prompt on load; only a buried button | a prompt tied to a user action is understood; https required anyway |
| 32 | Flat tokens, one accent, AA contrast measured in-page | keep gradient UI | 0 text elements below AA (was 5); gradients read as template output |
| 33 | Safety directly after the answer; one primary action per card | equal-weight cards | serial position and Von Restorff: the field-critical warning is seen second |
| 34 | Liberal distance input (units, commas, Devanagari digits) | strict number box | phones type "40 m" or "130 ft"; the box rejected them silently |
| 35 | "Contour" visual identity: survey paper, DIN numerals, flagging-tape hazard, summit confidence gauge (§10.5) | generic card UI | a field engineer reads map conventions at a glance; one saturated warm colour = danger |
| 36 | "Most likely type" + Model confidence band (High / Moderate / Low) | "Landslide type" + bare % | a model output is a hypothesis to verify; a band word gives the meaning of the number |
| 37 | Functional Bauhaus as the design scheme; ISO 3864 colour + shape for status; control edges ≥ 3 : 1 (§10.7) | neumorphism, decorative styles | fluency and credibility for the office reader; edges and shapes that survive glare and colour-vision deficiency on site |
| 38 | "Field Atlas at dawn" identity: SVG ridge landscape header, serif headings, atlas plates, lithology dividers (§10.8) | flat Bauhaus surface only | the subject and its drawing conventions give the app a character; the functional rules of §10.7 stay |
| 39 | Atlas conventions in every layer: grain paper, neatline corners, trail steps, graduated confidence ruler with threshold mark, dot-leader size index, mounted history prints (§10.9) | identity only in the header | each element borrows a real atlas or survey convention, so the whole page speaks one visual language |

---

## 14. Improvement history

| Date | Change | Measured effect |
|---|---|---|
| 10-15 | Plan: ConvNeXt main model, VLM pre-labels | superseded by evidence |
| 10-16 | Frozen probes + robustness selection; first test | test F1 0.784 (final) |
| 10-16 | Audit 1: site linking, train+val-only selection, stratified folds, site-balanced shifts | 230 photos re-split; all re-run |
| 10-16 | Audit 2: content fingerprints, deterministic ties, crash paths | identical test results |
| 10-26 | Dimensions v1 (CLIPSeg + SAM, 2 depth models) | 7 s/photo; mirror area stability 0.196 |
| 10-26 | v2: ZoeDepth added | max model ratio 6.25; plausible distance 80 % |
| 10-26 | v3: ZoeDepth dropped | distance plausible 100 % |
| 10-26 | v4: object prior, soft weights | volume blur 0.60 → 0.35; mirror area 0.058 |
| 11-02 | Guidance: live viewfinder, calibrated photo check, questions, Hindi, offline | 36/36 phone–Python agreement |
| 11-03 | Photo sets, walk stereo, focal of mosaics, video, auto sweep | stereo coverage 87.6 %; focal sd measured |
| 11-03 | Object prior refit (n = 83) | coverage 62.7 % → 94.0 % |
| 11-03 | 9 accuracy levers | none significant: data-limited |
| 11-04 | Graded photo quality, results always shown | 56 headless checks pass |
| 11-04/05 | Deployment: HF Space files, Cloudflare tunnel | public link: 40 s full result |
| 11-14 | GPS marker: photo EXIF GPS, compass bearing, landslide position, image report with map + EXIF, robust saving | 12 new headless checks; EXIF round-trip exact to 1e-6° |
| 11-14 | "Contour" redesign and engineer-facing wording (§10.5) | AA 0 failures light + dark in 4 result states; controls < 44 px: 0; 51/51 tests en + hi |
| 11-14 | UX audit against 20 UX laws + 20 machine-made signs (§10.4) | AA failures 5 → 0; controls < 44 px → 0; 11 new checks; 2 latent bugs fixed |
| 11-14 | "Field Atlas at dawn" visual identity (§10.8) | AA 0 failures light + dark in 4 states; edges < 3 : 1: 0; controls < 44 px: 0; 52/52 tests en + hi |
| 11-14 | Atlas scheme carried into every layer (§10.9) | AA 0 failures light + dark in 4 states; edges < 3 : 1: 0; controls < 44 px: 0; 52/52 tests en + hi |

---

## 15. Known weaknesses

Found or confirmed while writing this report (none hidden; ordered by impact):

1. **All labels are AI-made** (0 human labels; blind re-look agreement 63 % on flagged photos). Every
   accuracy number is agreement with these labels. A blind human relabel of the 263 test photos is the largest
   open item.
2. **The usable-photo gate is weak and uncalibrated** (threshold 0.5 fixed; ~17 % false rejects, ~16 % false
   accepts; end-to-end precision 0.605).
3. **Size scale is unverified**: no field measurements exist; v4 stability tables were produced with the old
   prior (sd 0.345), so the reported v4 interval widths are narrower than the current code gives (sd 0.536);
   a v5 re-run is needed.
4. **Field-calibration tool has two bugs** (`tools/calibrate_dimensions.py`, inactive because no field data
   exist): it fits against estimates that still include the object-prior factor while the app applies the
   calibration to uncorrected depth (would be off by ~×1.8); and it filters object-scaled photos by
   `startswith("a ")`, which no longer matches the scale-source text.
5. **D50 grain range** reflects grain sampling only, not the scale error (~×/÷ 2.4 at 90 %).
6. **Walk stride is not sent from the phone** for photo sets (only steps), so the server always uses 0.75 m even
   if the user set another stride for the distance helper.
7. **Weak classes**: earth/mud flow (CV recall 0.40, n = 43) and translational slide (precision 0.55); real
   phone subset only n = 20 (F1 0.526); South Asia shift F1 0.578.
8. **Shipped C vs evaluated C**: shipped type heads use C = 0.3 (base/large), while inner CV folds mostly chose
   0.003 — `choose_C` with 3 folds and 4 grid points is unstable.
9. **Photo sets**: no bundle adjustment (chained homographies drift over 5–8 photos); focal bias −0.07
   uncorrected; walk bands uncalibrated; all set results are from simulation; stereo succeeds on 71 % of pairs.
10. **Uncalibrated heuristics**: "serious" quality margins, steadiness limit, pan speed 0.35/s, auto-shot
    0.6 × median, question likelihoods.
11. **Focal convention** uses 36 mm on the long side; exact for 3:2 frames, ~4 % off for 4:3 (test was
    inconclusive: Commons EXIF had only 3:2 sensors).
12. **Outline head** validated only against its own pseudo-label teacher, not human masks.
13. **fuse_site** cannot narrow with more photos and is noisy at n = 2.
14. **Server**: small caches (6 jobs / 3 sets) and a single GPU lock limit concurrent users; token in the URL.
15. **Hindi** machine-drafted.
16. **Landslide position is unvalidated in the field**: phone compasses are often off by 10–30° near vehicles,
    rebar or power lines, and the 15° default and the 30 % model-depth distance error are assumptions, not
    measurements. A field check against surveyed points is needed. The bearing uses magnetic north.
17. **Map tiles need a connection** (offline reports have a grid map with scale and north arrow, not streets),
    and the request reveals the area to the tile server.
18. **Photo sets / video** do not carry photo EXIF GPS or bearing yet (only the phone fix).

---

## 16. Improvement roadmap

Ordered by value per effort; each must pass the project's gate (held-out or simulated evidence, coverage
kept within 85–95 %).

| Priority | Improvement | Expected effect | Needs |
|---|---|---|---|
| 1 | Blind human relabel of test (`review.py --relabel-others`) + Cohen's κ | trustworthy headline numbers | 1–2 people, ~2 h |
| 2 | Field visit: 5–10 sites with tape/rangefinder lengths and 30–50 local phone photos | first real size coverage; real phone accuracy; activates `calibrate_dimensions.py` (after fixing bugs #4) | a field day |
| 3 | Calibrate the gate threshold on OOF train+val; add hard negatives | fewer false rejects and false accepts | compute only |
| 4 | Fix: forward stride; D50 range including scale error; calibration bugs; stale fallback thresholds | correctness | small code changes |
| 5 | Re-run dimension eval as v5 with the current prior; report interval coverage | current honest widths | ~20 min GPU |
| 6 | More labelled sites for translational and earth/mud flow, especially South Asia | the only lever shown to matter (§5.5) | labelling |
| 7 | Multi-crop TTA (+1.2 pt, CI includes 0) once more data confirms it | small accuracy gain | evaluation |
| 8 | Conformal label sets instead of the family heuristic | guaranteed set coverage | OOF probabilities |
| 9 | Rotation bundle adjustment with shared focal; GRIC turn/walk test | better mosaics and focal | multiview work |
| 10 | 3D reconstruction from sets (VGGT/MASt3R) + DEM skyline scale and pre-failure surface | narrower scale and volume from geometry | feasibility test on 8 GB |
| 11 | Runout zone (travel angle + Corominas + DEM flow path), rock-joint stereonet, repeat-photo monitoring | hazard outputs beyond type and size | features 3–5 of the design notes |
| 12 | Native-speaker Hindi review; larger job cache; per-user rate limit | field usability, multi-user hosting | — |

---

## Appendix A: constants

| Constant | Value | Where |
|---|---|---|
| Split targets | 0.65 / 0.15 / 0.20, seed 0 | split.py |
| dHash duplicate | Hamming ≤ 4 of 64 | collectors |
| Site link visual threshold | cosine ≥ 0.90 (DINOv2-base) | link_sites.py |
| Test near-duplicate check | cosine ≥ 0.95 | check_integrity.py |
| Probe C grid | 0.003, 0.03, 0.3, 1.0 | probe.py |
| Phone copies per photo | 3 | probe.py |
| confident_min | 0.6 | models/selected.json |
| USABLE_MIN | 0.5 | predict.py |
| Photo check q | 0.5 percentile | photo_check.json |
| DEPTH_SD | 0.25 | dimension.py |
| FOCAL_SD | EXIF 0.02, Depth Pro 0.15, joined 0.145/0.161, default 0.25 | dimension.py, focal_check.json |
| Default focal | 26 mm (35 mm-equiv.) | dimension.py, overlap.py |
| Object prior | ×1.829 at 8.33 m, slope −0.198, sd 0.536, n = 83 / 43 sites | dimension_object_prior.json |
| Guzzetti law | V = 0.074 A^1.45, log-sd 0.6 | dimension.py |
| Thickness priors | debris 1.0 (0.3–3), earth/mud 2.0 (0.5–5), fall 0.5 (0.2–2) m | dimension.py |
| Corominas | log10(H/L) = −0.047 − 0.085 log10 V; flag \|r\| > 0.4 | dim_stats.py |
| Monte Carlo draws | 1,000, seed 0 | dim_stats.py |
| Graph-cut λ ladder | 0.5, 1, 2, 4, 8 | dim_stats.py |
| Cut-off note | border coverage > 0.15 | dimension.py |
| SIFT | 4,000 kp, contrast 0.02, ratio 0.8 | overlap.py |
| MAGSAC thresholds | H 4 px, F 1.5 px, E 1 px | overlap.py |
| Link rule | ≥ 30 inliers, ≥ 3 % overlap | overlap_check.json |
| Parallax (turn) | ≤ 1.5 px | overlap_check.json |
| Turn bands | gap 0.05, weak 0.20, dup 0.85, ideal 0.30–0.60 | overlap_check.json |
| Mosaic weight | 0.25 | overlap_check.json |
| Stride / baseline sd | 0.75 m / 0.15 | app.py, overlap.py |
| Stereo point filters | reproj < 2 px, ray angle > 1°, ≥ 8 points | overlap.py |
| Auto sweep | sharp ≥ 0.6× median, pan ≤ 0.35 W/s, ≥ 1.2 s apart | pano.py |
| Question likelihood bounds | 0.05–0.92; ≤ 5 questions; stop at 0.85 | guide_data.py, guide.py |
| Server caches | 6 jobs, 3 sets; bodies 25 / 40 / 2 MB; 40 MP | app.py |
| Compass | fresh ≤ 5 s at shutter; default σ 15°; horizontal component ≥ 0.2 | guide.py |
| Landslide position error | σ_d typed 5 %, model depth 30 %; GPS default 10 m; Earth R 6,371,008.8 m | guide.py |
| Late GPS fix attached | ≤ 3 min after the photo; silent refresh maximumAge 20 s | guide.py |
| Image report | 1,600 px wide, two columns 900 + 588 px, photo ≤ 640 px high, one line per phrase (shrink to 72 %, then …), JPEG q 0.9, map 588 × 329, zoom ≤ 18, tiles 5 s | guide.py |
| UI tokens | spacing 4/8/12/16/24/32 px; tap ≥ 44–48 px; text ≥ 4.5 : 1 (AA); paper #e9ede6 / #0f1a1b, ink #15242a, hazard tape #ff6a1a, summit gauge 6 rings, DIN headings; accent #17695a light / #5fd1a8 dark | ui.py |

## Appendix B: file map

| Area | Files |
|---|---|
| Shared config | `src/common.py` |
| Collection | `src/collect_commons.py`, `src/collect_openverse.py`, `src/import_local.py`, `src/import_dataset.py`, `tools/camera_info.py`, `tools/explore_commons.py`, `tools/count_commons.py` |
| Labels | `src/review.py`, `labeling_guide.md`, `tools/contact_sheet.py`, `tools/ai_labels.py`, `tools/ai_labeling_prompt.md`, `tools/find_label_issues.py`, `tools/credits.py` |
| Sites/splits | `tools/link_sites.py`, `src/split.py` |
| Classifier | `tools/precompute_embeddings.py`, `src/phone_aug.py`, `src/probe.py`, `src/predict.py`, `src/train_cnn.py`, `src/vlm_label.py` |
| Evaluation | `tools/robustness_eval.py`, `src/eval.py`, `tools/system_test.py`, `tools/hard_case_eval.py`, `tools/accuracy_eval.py` |
| Photo quality | `tools/calibrate_photo_check.py`, `src/photo_check.json` |
| Sizes | `src/dimension.py`, `src/dim_stats.py`, `tools/train_outline_head.py`, `tools/object_prior_eval.py`, `tools/dimension_eval.py`, `tools/calibrate_dimensions.py` |
| Sets/video | `src/overlap.py`, `src/pano.py`, `tools/overlap_eval.py`, `tools/stereo_eval.py`, `tools/focal_eval.py`, `src/overlap_check.json`, `src/focal_check.json` |
| App | `src/app.py`, `src/ui.py`, `src/guide.py`, `src/guide_data.py`, `src/logo.py`, `tools/guidance_report.py` |
| Deployment | `tools/serve_public.py`, `tools/build_hf_space.py`, `deploy/hf_space/` |
| Integrity | `tools/check_integrity.py` |
| Documents | `README.md`, `report.md`, `design.md` (original plan), `research_notes.md`, `papers/` |
