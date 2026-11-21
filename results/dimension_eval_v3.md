# Dimension estimation - evaluation

Device: **cuda**, mean 23.0 s per photo (all models, one photo). 40 photos, 8 per class, seed 0, measured as the labelled class.
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
| blur          |  0.319 |  0.137 |    0.229 |    0.382 |   0.166 | 0%     |
| brighter_warm |  0.22  |  0.084 |    0.127 |    0.243 |   0.101 | 0%     |
| darker_tone   |  0.088 |  0.039 |    0.041 |    0.145 |   0.04  | 0%     |
| downscale_640 |  0.166 |  0.083 |    0.086 |    0.288 |   0.073 | 0%     |
| jpeg_q35      |  0.42  |  0.162 |    0.257 |    0.464 |   0.193 | 0%     |
| mirror        |  0.058 |  0.023 |    0.03  |    0.095 |   0.026 | 0%     |
| noise         |  0.25  |  0.06  |    0.122 |    0.456 |   0.113 | 0%     |
| tilt_3deg     |  0.23  |  0.121 |    0.126 |    0.326 |   0.125 | 0%     |

| label               |   area |   drop |   length |   volume |   width |
|:--------------------|-------:|-------:|---------:|---------:|--------:|
| debris_flow         |  0.15  |  0.053 |    0.061 |    0.185 |   0.077 |
| earth_mud_flow      |  0.239 |  0.102 |    0.117 |    0.233 |   0.121 |
| fall_topple         |  0.15  |  0.061 |    0.105 |    0.27  |   0.063 |
| rotational_slide    |  0.186 |  0.075 |    0.132 |    0.407 |   0.092 |
| translational_slide |  0.207 |  0.086 |    0.115 |    0.323 |   0.081 |

## 3. Depth checks

Trust verdict: {'medium': '42%', 'high': '30%', 'low': '28%'}

|       |   chk_tta_flip_logdiff |   chk_haze_rho |   chk_texture_depth_slope |   chk_plane_inliers |   chk_corominas_residual |   chk_max_model_ratio |
|:------|-----------------------:|---------------:|--------------------------:|--------------------:|-------------------------:|----------------------:|
| count |                 40     |         40     |                    27     |              40     |                   32     |                40     |
| mean  |                  0.057 |         -0.338 |                     0.111 |               0.988 |                   -0.045 |                 3.591 |
| std   |                  0.033 |          0.309 |                     0.253 |               0.019 |                    0.306 |                 2.907 |
| min   |                  0.014 |         -0.81  |                    -0.23  |               0.93  |                   -0.71  |                 1.087 |
| 25%   |                  0.034 |         -0.565 |                    -0.085 |               0.98  |                   -0.242 |                 1.7   |
| 50%   |                  0.052 |         -0.38  |                     0.03  |               0.995 |                   -0.035 |                 2.771 |
| 75%   |                  0.062 |         -0.16  |                     0.235 |               1     |                    0.075 |                 4.545 |
| max   |                  0.151 |          0.42  |                     0.83  |               1     |                    1.04  |                14.286 |

Reading: model_ratio near 1 = Depth Pro and Depth Anything agree; flip_stability near 0 = mirror-invariant; haze_rho < 0 = contrast falls with distance as it should; grain slope near 0 = grain size independent of distance.

Scale set by a person/car in the photo: 22%. Grain sizes judged reliable (no size-distance trend): 25%. Outline used SAM: 92%. Outline used the trained head: 100%.

Photos scaled by a person/car (check these by eye): commons_dba915ce6ed1 (person in the photo (x1.269)), commons_b9a4cab5707c (motorcycle in the photo (x1.916)), commons_3fd890a4d447 (door/utility pole in the photo (x3.07)), ov_01320d2ef992 (truck in the photo (x2.666)), ov_66b61d7535bc (person in the photo (x1.847)), commons_511541058ba1 (tree/utility pole in the photo (x1.832)), commons_1017aef1654f (tree/truck in the photo (x4.358)), commons_2458770a93aa (car in the photo (x1.044)), commons_8afb313360a6 (utility pole in the photo (x3.099))

## 4. Plausibility

- distance 2-300 m: 100% of 40
- slope 5-85 deg: 98% of 40
- D50 < width (when grains measured): 100% of 28

## 4b. Uncertainty: median relative 90 % interval width, log(P95/P5); 0.7 = about x2 end to end

| label               |   ci_length |   ci_median_width |   ci_max_width |   ci_drop |   ci_area |   ci_volume |   ci_width |   ci_block |
|:--------------------|------------:|------------------:|---------------:|----------:|----------:|------------:|-----------:|-----------:|
| debris_flow         |        1.45 |              1.49 |           1.52 |      1.46 |      2.97 |        3.51 |     nan    |     nan    |
| earth_mud_flow      |        2.07 |              1.99 |           2    |      2.05 |      4.08 |        4.97 |     nan    |     nan    |
| fall_topple         |        2.73 |            nan    |         nan    |      2.73 |      5.46 |        6.15 |       2.74 |       2.69 |
| rotational_slide    |        2.46 |            nan    |         nan    |      2.4  |      5.1  |        7.57 |       2.6  |     nan    |
| translational_slide |        1.47 |            nan    |         nan    |      1.42 |      2.93 |        4.59 |       1.41 |     nan    |

Pre-failure surface volume available: 95%.

## 4c. Same-site consistency (different photos of one landslide)

Median log-sd across photos of the same site (0.10 = about 10 % spread). Viewpoints differ, so some spread is real (different visible extent).

| measure   |   median |   count |
|:----------|---------:|--------:|
| area      |    0.863 |      11 |
| distance  |    0.555 |      11 |
| length    |    0.398 |      11 |
| volume    |    1.222 |      11 |
| width     |    0.521 |      11 |

## 5. Median measures per class

| label               |   length |   width |   area |   volume |   drop |   distance |   slope |   D50 |
|:--------------------|---------:|--------:|-------:|---------:|-------:|-----------:|--------:|------:|
| debris_flow         |     7.6  |    5.14 |  48.05 |    45.5  |   3.28 |       6.55 |    22.5 |  0.2  |
| earth_mud_flow      |     9.71 |   11.22 | 104.8  |   187.1  |   4.46 |       6.25 |    39   |  0.54 |
| fall_topple         |     7.58 |    7.74 |  56.95 |    23    |   4.26 |       5.1  |    37.5 |  0.33 |
| rotational_slide    |     4.24 |    4.99 |  12    |     2.6  |   2.34 |       6.75 |    41   |  2.79 |
| translational_slide |     7.74 |    7.86 |  47.2  |    20.05 |   4.18 |      12    |    35   |  0.17 |
