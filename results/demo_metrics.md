# Demo metrics (held-out test: 263 photos, 152 sites; 95 % CI = 2000x site bootstrap)

| Metric | Value [95 % CI] |
|---|---|
| Landslide present? ROC AUC | 0.958 [0.928, 0.980] |
| Landslide present? average precision | 0.960 [0.923, 0.984] |
| Type: macro ROC AUC (6 types) | 0.936 [0.890, 0.979] |
| Type: correct answer in top 2 | 91.3 % [83.1, 96.7] |
| Type: accuracy | 80.6 % [72.0, 87.3] |
| Type: macro-F1 | 0.784 [0.687, 0.856] |
| Accuracy when app is >= 90 % sure (43 % of photos) | 96.5 % [88.9, 100] |
| Accuracy at app default (>= 60 %, 81 % of photos) | 85.4 % [75.9, 92.6] |
| Calibration error (ECE, 15 bins) | 0.049 |
| Zero-shot Qwen2.5-VL-7B on same photos: acc / macro-F1 | 55.5 % / 0.327 |
| Phone-degraded photos: acc / macro-F1 | 76.8 % / 0.697 |

Size scale vs known-height objects (83 photos, 43 sites, leave-site-out): median error 94 % -> 46 %,
within 2x 54 % -> 81 %, bias x1.92 -> x1.05; 90 % ranges contain the truth 94 % (50 % -> 51 %, 80 % -> 81 %).

Figures: results/type_metrics.png, results/size_metrics.png. Thresholds were set on cross-validation, not on test.
