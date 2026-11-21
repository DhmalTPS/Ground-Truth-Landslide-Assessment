# Dimension estimation - evaluation

Device: **cuda**, mean 30.1 s per photo (all models, one photo). 40 photos, 8 per class, seed 0, measured as the labelled class.
No ground-truth sizes exist, so this checks availability, stability, depth consistency and plausibility, not absolute accuracy.

## 1. Availability (outline found)

| label               | available   |
|:--------------------|:------------|
| debris_flow         | 100%        |
| earth_mud_flow      | 100%        |
| fall_topple         | 100%        |
| rotational_slide    | 100%        |
| translational_slide | 100%        |

## 2. Stability under phone-like changes (median |log ratio|; 0.10 = ~10 % change)

Lost = outline not found after the change.

| perturb       |   area |   drop |   length |   volume |   width | lost   |
|:--------------|-------:|-------:|---------:|---------:|--------:|:-------|
| blur          |  0.488 |  0.214 |    0.262 |    0.597 |   0.22  | 0%     |
| brighter_warm |  0.347 |  0.152 |    0.191 |    0.379 |   0.137 | 0%     |
| darker_tone   |  0.092 |  0.044 |    0.049 |    0.153 |   0.03  | 0%     |
| downscale_640 |  0.15  |  0.082 |    0.123 |    0.311 |   0.118 | 0%     |
| jpeg_q35      |  0.395 |  0.152 |    0.216 |    0.455 |   0.151 | 0%     |
| mirror        |  0.051 |  0.022 |    0.027 |    0.078 |   0.016 | 0%     |
| noise         |  0.266 |  0.127 |    0.136 |    0.74  |   0.113 | 0%     |
| tilt_3deg     |  0.307 |  0.174 |    0.145 |    0.357 |   0.189 | 0%     |

| label               |   area |   drop |   length |   volume |   width |
|:--------------------|-------:|-------:|---------:|---------:|--------:|
| debris_flow         |  0.166 |  0.084 |    0.099 |    0.177 |   0.092 |
| earth_mud_flow      |  0.261 |  0.138 |    0.17  |    0.298 |   0.163 |
| fall_topple         |  0.186 |  0.075 |    0.107 |    0.281 |   0.091 |
| rotational_slide    |  0.316 |  0.126 |    0.197 |    0.693 |   0.116 |
| translational_slide |  0.199 |  0.109 |    0.12  |    0.326 |   0.069 |

## 3. Depth checks

Trust verdict: {'medium': '72%', 'low': '28%'}

|       |   chk_tta_flip_logdiff |   chk_haze_rho |   chk_texture_depth_slope |   chk_plane_inliers |   chk_corominas_residual |   chk_max_model_ratio |
|:------|-----------------------:|---------------:|--------------------------:|--------------------:|-------------------------:|----------------------:|
| count |                 40     |         40     |                    28     |              40     |                   32     |                40     |
| mean  |                  0.057 |         -0.34  |                     0.105 |               0.986 |                   -0.097 |                 7.712 |
| std   |                  0.033 |          0.311 |                     0.258 |               0.022 |                    0.311 |                 3.338 |
| min   |                  0.014 |         -0.79  |                    -0.29  |               0.92  |                   -0.78  |                 4.545 |
| 25%   |                  0.034 |         -0.595 |                    -0.09  |               0.98  |                   -0.302 |                 5.556 |
| 50%   |                  0.052 |         -0.365 |                     0.04  |               0.995 |                   -0.13  |                 6.25  |
| 75%   |                  0.062 |         -0.17  |                     0.298 |               1     |                    0.025 |                 9.318 |
| max   |                  0.151 |          0.43  |                     0.78  |               1     |                    0.78  |                16.667 |

Reading: model_ratio near 1 = Depth Pro and Depth Anything agree; flip_stability near 0 = mirror-invariant; haze_rho < 0 = contrast falls with distance as it should; grain slope near 0 = grain size independent of distance.

Scale set by a person/car in the photo: 15%. Grain sizes judged reliable (no size-distance trend): 25%. Outline refined by SAM: 0%. Grains from SAM instances: 0%.

Photos scaled by a person/car (check these by eye): commons_dba915ce6ed1 (person in the photo (x1.324)), commons_b9a4cab5707c (motorcycle in the photo (x4.06)), ov_01320d2ef992 (truck in the photo (x4.909)), ov_66b61d7535bc (person in the photo (x1.838)), commons_511541058ba1 (tree/utility pole in the photo (x2.146)), commons_2458770a93aa (car in the photo (x1.475))

## 4. Plausibility

- distance 2-300 m: 80% of 40
- slope 5-85 deg: 100% of 40
- D50 < width (when grains measured): 100% of 28

## 4b. Uncertainty: median relative 90 % interval width, log(P95/P5); 0.7 = about x2 end to end

| label               |   ci_length |   ci_median_width |   ci_max_width |   ci_drop |   ci_area |   ci_volume |   ci_width |   ci_block |
|:--------------------|------------:|------------------:|---------------:|----------:|----------:|------------:|-----------:|-----------:|
| debris_flow         |        1.65 |              1.76 |           1.65 |      1.65 |      3.34 |        3.93 |     nan    |     nan    |
| earth_mud_flow      |        1.52 |              1.53 |           1.54 |      1.53 |      3.07 |        3.54 |     nan    |     nan    |
| fall_topple         |        1.34 |            nan    |         nan    |      1.51 |      2.67 |        3.2  |       1.49 |       1.93 |
| rotational_slide    |        2.92 |            nan    |         nan    |      2.82 |      5.56 |        5.3  |       2.89 |     nan    |
| translational_slide |        3.09 |            nan    |         nan    |      3.1  |      6.17 |        9.03 |       3.09 |     nan    |

Pre-failure surface volume available: 95%.

## 4c. Same-site consistency (different photos of one landslide)

Median log-sd across photos of the same site (0.10 = about 10 % spread). Viewpoints differ, so some spread is real (different visible extent).

| measure   |   median |   count |
|:----------|---------:|--------:|
| area      |    0.766 |      11 |
| distance  |    0.573 |      11 |
| length    |    0.498 |      11 |
| volume    |    1.036 |      11 |
| width     |    0.318 |      11 |

## 5. Median measures per class

| label               |   length |   width |   area |   volume |   drop |   distance |   slope |   D50 |
|:--------------------|---------:|--------:|-------:|---------:|-------:|-----------:|--------:|------:|
| debris_flow         |     6.82 |    3.34 |  23.4  |    21.4  |   2.55 |       6.15 |    21.5 |  0.17 |
| earth_mud_flow      |     5.69 |    4.39 |  23.75 |    43.85 |   1.66 |       2.6  |    39.5 |  0.36 |
| fall_topple         |     3.86 |    3.97 |  13.85 |     5.88 |   1.98 |       2.75 |    34.5 |  0.16 |
| rotational_slide    |     2.6  |    2.5  |   3.22 |     0.4  |   1.19 |       3.75 |    41.5 |  0.39 |
| translational_slide |     6.08 |    5.48 |  32.15 |    10.18 |   3.03 |       7.4  |    33.5 |  0.11 |

Empirical depth log-sd from model disagreement: 1.921 (n=40); the pipeline uses max(0.25, this).
