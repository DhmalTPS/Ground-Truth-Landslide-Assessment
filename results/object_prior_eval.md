# Known-object scale prior refit (train+val photos, test not read)

Photos scanned: 1062; with a tight-height object scale: 83 (43 sites). Objects: bus, car, door, motorcycle, person

| model | factor (at median depth) | depth slope | tau | predictive sd | LSO median abs err | LSO MSE | LSO 90 % coverage |
|---|---|---|---|---|---|---|---|
| constant | x1.749 | +0.000 | 0.518 | 0.543 | 0.384 | 0.311 | 92.8% |
| log depth covariate | x1.829 | -0.198 | 0.503 | 0.536 | 0.378 | 0.281 | 94.0% |

Old prior: x1.531, predictive sd 0.345 (n = 4); on these 83 photos its 90 % interval covers 62.7% (median abs err 0.383).
Chosen: log depth covariate; gate (coverage 85-95 % and narrower than 0.345 or the old prior under-covers): PASS
