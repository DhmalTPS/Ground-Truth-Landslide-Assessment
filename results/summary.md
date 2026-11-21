# Test results

Test split: 263 usable photos from 152 sites (no site also appears in train/val). Labels made with VLM suggestion visible: 0 (should be 0).

**Label source:** 263 of 263 test labels were made only by an AI annotator (reviewer `*_ai`); these numbers measure agreement with those labels, not verified ground truth. Have a person re-label the test split blind (`python src/review.py --reviewer <name> --split test --relabel-others`) to replace them.

| Model | Scored | Accuracy | Macro-F1 [95% CI, site bootstrap] |
|---|---|---|---|
| cnn | 263/263 | 0.722 | 0.665 [0.548, 0.745] |
| cnn_phonesim | 263/263 | 0.684 | 0.582 [0.455, 0.677] |
| probe_base | 263/263 | 0.745 | 0.649 [0.537, 0.738] |
| probe_base_phonesim | 263/263 | 0.741 | 0.661 [0.558, 0.750] |
| probe_large | 263/263 | 0.776 | 0.736 [0.643, 0.810] |
| probe_large_phonesim | 263/263 | 0.787 | 0.745 [0.652, 0.824] |
| probe_siglip | 263/263 | 0.726 | 0.642 [0.536, 0.725] |
| probe_siglip_phonesim | 263/263 | 0.722 | 0.639 [0.533, 0.730] |
| selected | 263/263 | 0.806 | 0.784 [0.688, 0.857] |
| selected_phonesim | 263/263 | 0.768 | 0.697 [0.599, 0.780] |
| vlm_Qwen2.5-VL-7B-Instruct | 263/263 | 0.555 | 0.327 [0.268, 0.399] |

## Deployment case: ground photos looking up/across at the slope

 n = 254; classes: {'no_landslide': 123, 'fall_topple': 55, 'translational_slide': 31, 'debris_flow': 26, 'rotational_slide': 11, 'earth_mud_flow': 8}. Macro-F1 over the classes present in this subset.

| Model | n | Accuracy | Macro-F1 |
|---|---|---|---|
| cnn | 254 | 0.736 | 0.692 |
| cnn_phonesim | 254 | 0.693 | 0.596 |
| probe_base | 254 | 0.760 | 0.671 |
| probe_base_phonesim | 254 | 0.752 | 0.680 |
| probe_large | 254 | 0.783 | 0.750 |
| probe_large_phonesim | 254 | 0.791 | 0.757 |
| probe_siglip | 254 | 0.736 | 0.653 |
| probe_siglip_phonesim | 254 | 0.736 | 0.656 |
| selected | 254 | 0.815 | 0.800 |
| selected_phonesim | 254 | 0.776 | 0.709 |
| vlm_Qwen2.5-VL-7B-Instruct | 254 | 0.563 | 0.333 |

## South Asia (deployment region)

Tagged from category/title/description place names (common.is_south_asia). n = 48; classes: {'no_landslide': 25, 'translational_slide': 9, 'debris_flow': 7, 'fall_topple': 7}. Macro-F1 over the classes present in this subset.

| Model | n | Accuracy | Macro-F1 |
|---|---|---|---|
| cnn | 48 | 0.792 | 0.793 |
| cnn_phonesim | 48 | 0.771 | 0.766 |
| probe_base | 48 | 0.729 | 0.675 |
| probe_base_phonesim | 48 | 0.708 | 0.662 |
| probe_large | 48 | 0.812 | 0.775 |
| probe_large_phonesim | 48 | 0.771 | 0.714 |
| probe_siglip | 48 | 0.729 | 0.696 |
| probe_siglip_phonesim | 48 | 0.854 | 0.843 |
| selected | 48 | 0.854 | 0.807 |
| selected_phonesim | 48 | 0.792 | 0.750 |
| vlm_Qwen2.5-VL-7B-Instruct | 48 | 0.667 | 0.516 |

## Real phone photos (EXIF camera = phone)

Small n -> wide uncertainty. n = 20; classes: {'no_landslide': 11, 'translational_slide': 4, 'fall_topple': 3, 'debris_flow': 2}. Macro-F1 over the classes present in this subset.

| Model | n | Accuracy | Macro-F1 |
|---|---|---|---|
| cnn | 20 | 0.650 | 0.542 |
| cnn_phonesim | 20 | 0.750 | 0.655 |
| probe_base | 20 | 0.650 | 0.617 |
| probe_base_phonesim | 20 | 0.600 | 0.526 |
| probe_large | 20 | 0.600 | 0.517 |
| probe_large_phonesim | 20 | 0.700 | 0.592 |
| probe_siglip | 20 | 0.500 | 0.411 |
| probe_siglip_phonesim | 20 | 0.650 | 0.539 |
| selected | 20 | 0.600 | 0.526 |
| selected_phonesim | 20 | 0.650 | 0.539 |
| vlm_Qwen2.5-VL-7B-Instruct | 20 | 0.550 | 0.414 |

## Recall per class

| Class | n | cnn | cnn_phonesim | probe_base | probe_base_phonesim | probe_large | probe_large_phonesim | probe_siglip | probe_siglip_phonesim | selected | selected_phonesim | vlm_Qwen2.5-VL-7B-Instruct |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| fall_topple | 58 | 0.62 | 0.64 | 0.69 | 0.67 | 0.66 | 0.78 | 0.66 | 0.69 | 0.67 | 0.71 | 0.66 |
| rotational_slide | 11 | 0.91 | 0.82 | 0.64 | 0.82 | 0.91 | 0.82 | 0.82 | 0.73 | 0.91 | 0.82 | 0.64 |
| translational_slide | 32 | 0.38 | 0.38 | 0.34 | 0.34 | 0.47 | 0.44 | 0.41 | 0.50 | 0.53 | 0.34 | 0.28 |
| debris_flow | 29 | 0.86 | 0.83 | 0.79 | 0.83 | 0.93 | 0.93 | 0.90 | 0.66 | 0.97 | 0.97 | 0.03 |
| earth_mud_flow | 8 | 0.62 | 0.25 | 0.62 | 0.62 | 0.75 | 0.75 | 0.50 | 0.75 | 0.75 | 0.62 | 0.00 |
| no_landslide | 125 | 0.82 | 0.77 | 0.88 | 0.86 | 0.86 | 0.85 | 0.81 | 0.81 | 0.90 | 0.86 | 0.73 |


`<model>_phonesim` = the same model scored on fixed phone-degraded copies of the test photos (crop, tilt, blur, noise, JPEG; src/phone_aug.py). `selected` = the app's model (models/selected.json).
