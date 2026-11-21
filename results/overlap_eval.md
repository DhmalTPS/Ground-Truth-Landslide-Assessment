# Overlapping photo sets: calibration and test (simulated sets from real photos)

Made by `tools/overlap_eval.py`. Train photos set the thresholds, out-of-fold train+val photos choose how the joined picture and the single photos are combined; test photos are not read.

## Train: 450 turn pairs, 300 walk pairs, 150 unrelated pairs

- Link threshold: **30 inliers** (unrelated pairs linked: 0.0%)
- Overlap estimate error (linked turn pairs): mean absolute error **0.2 points**
- Parallax threshold: **1.5 px** (95th percentile of turn pairs at 1024 px)
- Walk pairs called moved or not linked: step 8 % of width 100%, 15 % 100% (parallax above threshold: 100%, 100%)
- 'Weak' overlap band below **20%** (95 % of turn pairs link from 15% up); 'gap' below **5%**; ideal band 30%-60%

| true overlap | pairs | linked |
|---|---|---|
| 0%-5% | 11 | 27% |
| 5%-10% | 20 | 75% |
| 10%-15% | 25 | 92% |
| 15%-20% | 27 | 100% |
| 20%-25% | 25 | 100% |
| 25%-30% | 21 | 100% |
| 30%-35% | 17 | 94% |
| 35%-40% | 28 | 100% |
| 40%-45% | 18 | 100% |
| 45%-50% | 23 | 100% |
| 50%-55% | 28 | 100% |
| 55%-60% | 38 | 100% |
| 60%-65% | 36 | 100% |
| 65%-70% | 31 | 100% |
| 70%-75% | 27 | 100% |
| 75%-80% | 17 | 100% |
| 80%-85% | 25 | 100% |
| 85%-90% | 31 | 100% |
| 90%-95% | 2 | 100% |

## Type from a 3-photo turning set: 300 train+val photos, out-of-fold heads (site-grouped 5-fold)

Each photo is split into 3 overlapping views (half its width each), joined, and classified by probe heads refit without its site (0 photos skipped: too narrow to split or not joined).

| type from | macro-F1 | accuracy | same answer as whole photo |
|---|---|---|---|
| whole photo (reference) | 0.712 | 77.7% | 100.0% |
| w = 0.0 | 0.702 | 76.0% | 88.7% |
| w = 0.25 | 0.710 | 77.0% | 89.7% |
| w = 0.5 | 0.707 | 76.7% | 91.7% |
| w = 0.75 | 0.699 | 76.3% | 92.0% |
| w = 1.0 | 0.692 | 75.7% | 91.3% |
| middle photo alone | 0.674 | 74.3% | 86.0% |

Chosen: **w = 0.25** (w = weight of the joined picture).
