# Dimension estimation - evaluation

Device: **cuda**, mean 25.5 s per photo (all models, one photo). 40 photos, 8 per class, seed 0, measured as the labelled class.
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
| blur          |  0.305 |  0.137 |    0.231 |    0.349 |   0.163 | 0%     |
| brighter_warm |  0.217 |  0.101 |    0.129 |    0.231 |   0.104 | 0%     |
| darker_tone   |  0.089 |  0.039 |    0.041 |    0.144 |   0.039 | 0%     |
| downscale_640 |  0.161 |  0.073 |    0.086 |    0.224 |   0.075 | 0%     |
| jpeg_q35      |  0.422 |  0.162 |    0.26  |    0.466 |   0.194 | 0%     |
| mirror        |  0.058 |  0.025 |    0.029 |    0.105 |   0.026 | 0%     |
| noise         |  0.25  |  0.058 |    0.121 |    0.444 |   0.113 | 0%     |
| tilt_3deg     |  0.247 |  0.127 |    0.133 |    0.275 |   0.135 | 0%     |

| label               |   area |   drop |   length |   volume |   width |
|:--------------------|-------:|-------:|---------:|---------:|--------:|
| debris_flow         |  0.151 |  0.053 |    0.063 |    0.175 |   0.077 |
| earth_mud_flow      |  0.239 |  0.102 |    0.116 |    0.202 |   0.121 |
| fall_topple         |  0.151 |  0.06  |    0.104 |    0.233 |   0.063 |
| rotational_slide    |  0.187 |  0.076 |    0.132 |    0.374 |   0.095 |
| translational_slide |  0.207 |  0.088 |    0.119 |    0.317 |   0.082 |

## 3. Depth checks

Trust verdict: {'medium': '42%', 'high': '30%', 'low': '28%'}

|       |   chk_tta_flip_logdiff |   chk_haze_rho |   chk_texture_depth_slope |   chk_plane_inliers |   chk_corominas_residual |   chk_max_model_ratio |
|:------|-----------------------:|---------------:|--------------------------:|--------------------:|-------------------------:|----------------------:|
| count |                 40     |         40     |                    27     |              40     |                   32     |                40     |
| mean  |                  0.057 |         -0.338 |                     0.111 |               0.988 |                   -0.015 |                 3.591 |
| std   |                  0.033 |          0.309 |                     0.253 |               0.019 |                    0.307 |                 2.907 |
| min   |                  0.014 |         -0.81  |                    -0.23  |               0.93  |                   -0.66  |                 1.087 |
| 25%   |                  0.034 |         -0.565 |                    -0.085 |               0.98  |                   -0.205 |                 1.7   |
| 50%   |                  0.052 |         -0.38  |                     0.03  |               0.995 |                   -0.015 |                 2.771 |
| 75%   |                  0.062 |         -0.16  |                     0.235 |               1     |                    0.1   |                 4.545 |
| max   |                  0.151 |          0.42  |                     0.83  |               1     |                    1.08  |                14.286 |

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
| debris_flow         |        1.39 |              1.44 |           1.39 |      1.38 |      2.85 |        3.45 |     nan    |     nan    |
| earth_mud_flow      |        1.37 |              1.37 |           1.35 |      1.36 |      2.71 |        3.41 |     nan    |     nan    |
| fall_topple         |        1.38 |            nan    |         nan    |      1.38 |      2.74 |        3.42 |       1.37 |       1.35 |
| rotational_slide    |        1.44 |            nan    |         nan    |      1.42 |      3    |        4.72 |       1.41 |     nan    |
| translational_slide |        1.43 |            nan    |         nan    |      1.38 |      2.79 |        4.47 |       1.37 |     nan    |

Pre-failure surface volume available: 95%.

## 4c. Same-site consistency (different photos of one landslide)

Median log-sd across photos of the same site (0.10 = about 10 % spread). Viewpoints differ, so some spread is real (different visible extent).

| measure   |   median |   count |
|:----------|---------:|--------:|
| area      |    0.797 |      11 |
| distance  |    0.44  |      11 |
| length    |    0.396 |      11 |
| volume    |    1.153 |      11 |
| width     |    0.451 |      11 |

## 5. Median measures per class

| label               |   length |   width |   area |   volume |   drop |   distance |   slope |   D50 |
|:--------------------|---------:|--------:|-------:|---------:|-------:|-----------:|--------:|------:|
| debris_flow         |    10.5  |    7.79 |  95.1  |    93.35 |   4.31 |       9.5  |    22.5 |  0.29 |
| earth_mud_flow      |    14.85 |   13.6  | 245.6  |   448    |   6.82 |       7.65 |    39   |  0.54 |
| fall_topple         |    11.65 |   11.85 | 133.45 |    60.6  |   6.51 |       7.75 |    37.5 |  0.51 |
| rotational_slide    |     5.85 |    7.64 |  28.2  |     9.35 |   3.58 |      10.3  |    41   |  2.84 |
| translational_slide |    11.85 |   11.4  | 110.55 |    69.6  |   6.39 |      14.3  |    35   |  0.22 |

Known-size object evidence (tight heights only): factors [1.269, 1.916, 1.847, 1.044], median x1.531 (n=4)
