# Dimension estimation - evaluation

Device: **cuda**, mean 7.0 s per photo (all models, one photo). 40 photos, 8 per class, seed 0, measured as the labelled class.
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
| blur          |  0.372 |  0.168 |    0.264 |    0.443 |   0.146 | 0%     |
| brighter_warm |  0.25  |  0.101 |    0.132 |    0.3   |   0.112 | 0%     |
| darker_tone   |  0.151 |  0.076 |    0.085 |    0.154 |   0.098 | 2%     |
| downscale_640 |  0.251 |  0.102 |    0.104 |    0.285 |   0.101 | 0%     |
| jpeg_q35      |  0.483 |  0.223 |    0.313 |    0.544 |   0.225 | 0%     |
| mirror        |  0.196 |  0.101 |    0.063 |    0.251 |   0.104 | 0%     |
| noise         |  0.238 |  0.113 |    0.091 |    0.303 |   0.134 | 0%     |
| tilt_3deg     |  0.265 |  0.188 |    0.197 |    0.319 |   0.136 | 0%     |

| label               |   area |   drop |   length |   volume |   width |
|:--------------------|-------:|-------:|---------:|---------:|--------:|
| debris_flow         |  0.358 |  0.207 |    0.142 |    0.365 |   0.158 |
| earth_mud_flow      |  0.24  |  0.105 |    0.133 |    0.24  |   0.15  |
| fall_topple         |  0.197 |  0.109 |    0.138 |    0.2   |   0.102 |
| rotational_slide    |  0.21  |  0.107 |    0.119 |    0.305 |   0.115 |
| translational_slide |  0.301 |  0.128 |    0.179 |    0.44  |   0.111 |

## 3. Depth checks

Trust verdict: {'medium': '75%', 'high': '12%', 'low': '12%'}

|       |   chk_flip_stability |   chk_model_ratio_pro_over_da |   chk_haze_rho |   chk_grain_size_vs_distance_slope |   chk_shadow_fraction |
|:------|---------------------:|------------------------------:|---------------:|-----------------------------------:|----------------------:|
| count |               40     |                        40     |         40     |                             27     |                40     |
| mean  |                0.056 |                         0.842 |         -0.335 |                              0.796 |                 0.143 |
| std   |                0.038 |                         0.969 |          0.307 |                              0.424 |                 0.07  |
| min   |                0.011 |                         0.07  |         -0.81  |                             -0.04  |                 0.013 |
| 25%   |                0.027 |                         0.248 |         -0.55  |                              0.57  |                 0.086 |
| 50%   |                0.05  |                         0.37  |         -0.375 |                              0.69  |                 0.145 |
| 75%   |                0.067 |                         1.085 |         -0.16  |                              0.865 |                 0.197 |
| max   |                0.179 |                         4.18  |          0.42  |                              2.23  |                 0.294 |

Reading: model_ratio near 1 = Depth Pro and Depth Anything agree; flip_stability near 0 = mirror-invariant; haze_rho < 0 = contrast falls with distance as it should; grain slope near 0 = grain size independent of distance.

Scale set by a person/car in the photo: 12%. Grain sizes judged reliable (no size-distance trend): 40%. Outline refined by SAM: 92%. Grains from SAM instances: 48%.

Photos scaled by a person/car (check these by eye): commons_122d585af34f (a car in the photo (depth x2.79)), ov_01320d2ef992 (a car in the photo (depth x0.57)), commons_511541058ba1 (a car in the photo (depth x0.7)), commons_2458770a93aa (a car in the photo (depth x0.76)), commons_8afb313360a6 (a car in the photo (depth x1.04))

## 4. Plausibility

- distance 2-300 m: 100% of 40
- slope 5-85 deg: 100% of 40
- D50 < width (when grains measured): 100% of 40

## 5. Median measures per class

| label               |   length |   width |   area |   volume |   drop |   distance |   slope |   D50 |
|:--------------------|---------:|--------:|-------:|---------:|-------:|-----------:|--------:|------:|
| debris_flow         |     7.55 |    4.25 |  34.25 |    34.25 |   2.95 |       7.05 |    22.5 |  0.18 |
| earth_mud_flow      |     9.05 |    5.2  |  66    |   130.85 |   3.05 |       4.95 |    39   |  0.12 |
| fall_topple         |     7.95 |    8    |  60.1  |    30.05 |   4    |       5.1  |    40.5 |  0.16 |
| rotational_slide    |     6.3  |    5.2  |  13.7  |     3.3  |   2.7  |       6.5  |    34   |  0.26 |
| translational_slide |     6.8  |    6.85 |  38.45 |    14.75 |   3.8  |       6.4  |    36   |  0.18 |
