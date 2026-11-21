# Focal length from turning sets (simulation from real photos)

Made by `tools/focal_eval.py`; true focal 22-30 mm (35 mm eq.), lens distortion, noise, JPEG; no EXIF.

| split | photos in set | sets | focal found | bias (log) | RMS | robust sd | 90th pct abs |
|---|---|---|---|---|---|---|---|
| train | 2 | 68 | 100% | -0.044 | 0.145 | 0.075 | 0.297 |
| train | 3 | 52 | 100% | -0.072 | 0.161 | 0.103 | 0.297 |
| val | 2 | 60 | 100% | -0.077 | 0.126 | 0.089 | 0.212 |
| val | 3 | 60 | 100% | -0.074 | 0.121 | 0.094 | 0.198 |

focal_sd (train RMS): {'2': 0.145, '3': 0.161}; val 90 % coverage: 2 photos 93.3%, 3 photos 98.3%
Gate (sd < 0.08 for 3-photo sets): FAIL
