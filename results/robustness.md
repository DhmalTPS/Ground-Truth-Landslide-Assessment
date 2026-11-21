# Robustness report

Photos used: train+val only (test split untouched). Usable labeled photos: 1062 from 586 sites (South Asia 274, Openverse 157, phone EXIF 217; known non-phone camera 688). All numbers measure agreement with the AI-made labels (see report.md, label caveat).

## All systems (sorted by robustness score)

robust score = mean **site-balanced** macro-F1 of: CV, Commons→Openverse, outside→South Asia, known non-phone cameras→phone. Δ vs selected = paired site bootstrap of CV macro-F1 (selected − system): mean [90% interval], P(Δ ≤ 0).

| System | robust score | CV macro-F1 site-bal. (plain; fold mean ± sd) | CV acc | phone-degraded F1 | →Openverse F1 | →South Asia F1 (acc) | →phone cam F1 | ECE | Δ vs selected |
|---|---|---|---|---|---|---|---|---|---|
| base+large+siglip | **0.676** | 0.714 (0.704; 0.684 ± 0.046) | 0.773 | 0.677 | 0.743 | 0.578 (0.741) | 0.669 | 0.040 | selected |
| large+siglip | **0.670** | 0.701 (0.689; 0.671 ± 0.044) | 0.766 | 0.660 | 0.689 | 0.617 (0.741) | 0.675 | 0.036 | +0.013 [-0.002, +0.029], P=0.08 |
| base+large | **0.665** | 0.712 (0.700; 0.682 ± 0.047) | 0.772 | 0.653 | 0.695 | 0.587 (0.734) | 0.668 | 0.029 | +0.004 [-0.015, +0.024], P=0.38 |
| base+siglip | **0.654** | 0.704 (0.697; 0.676 ± 0.034) | 0.777 | 0.676 | 0.703 | 0.548 (0.737) | 0.662 | 0.063 | +0.007 [-0.013, +0.029], P=0.32 |
| large | **0.651** | 0.684 (0.679; 0.654 ± 0.019) | 0.753 | 0.634 | 0.661 | 0.587 (0.712) | 0.669 | 0.091 | +0.025 [+0.002, +0.048], P=0.04 |
| base | **0.639** | 0.680 (0.673; 0.655 ± 0.042) | 0.756 | 0.664 | 0.719 | 0.558 (0.723) | 0.598 | 0.040 | +0.032 [+0.014, +0.051], P=0.00 |
| siglip | **0.583** | 0.637 (0.639; 0.609 ± 0.053) | 0.719 | 0.624 | 0.549 | 0.536 (0.690) | 0.611 | 0.028 | +0.065 [+0.043, +0.089], P=0.00 |

Largest site among phone photos: commons:Landslide at Nedumpoil ghat road (108 of 217)

## Selected: `base+large+siglip`

### Per class (site-grouped CV)

| Class | n | recall | precision |
|---|---|---|---|
| fall_topple | 219 | 0.78 | 0.73 |
| rotational_slide | 73 | 0.77 | 0.75 |
| translational_slide | 121 | 0.69 | 0.55 |
| debris_flow | 193 | 0.70 | 0.86 |
| earth_mud_flow | 43 | 0.40 | 0.55 |
| no_landslide | 413 | 0.87 | 0.87 |

### Confusion (CV)

| true \ predicted | fall_topple | rotational_slide | translational_slide | debris_flow | earth_mud_flow | no_landslide |
|---|---|---|---|---|---|---|
| fall_topple | 170 | 1 | 9 | 4 | 2 | 33 |
| rotational_slide | 0 | 56 | 8 | 1 | 2 | 6 |
| translational_slide | 14 | 10 | 83 | 3 | 1 | 10 |
| debris_flow | 9 | 0 | 40 | 136 | 4 | 4 |
| earth_mud_flow | 2 | 5 | 4 | 12 | 17 | 3 |
| no_landslide | 37 | 3 | 7 | 2 | 5 | 359 |

### Selective prediction (CV, type head only, before the photo check)

| Confidence ≥ | Coverage | Accuracy on answered | Macro-F1 on answered |
|---|---|---|---|
| 0.0 | 1.00 | 0.773 | 0.704 |
| 0.4 | 0.96 | 0.791 | 0.720 |
| 0.5 | 0.86 | 0.834 | 0.756 |
| 0.6 | 0.73 | 0.881 | 0.802 |
| 0.7 | 0.60 | 0.911 | 0.829 |
| 0.8 | 0.46 | 0.944 | 0.869 |
| 0.9 | 0.28 | 0.983 | 0.942 |

App threshold: answer confidently at ≥ 0.6 (first threshold with accuracy ≥ 0.85 at ≥ 50% coverage); below it the app says 'uncertain' and shows the top two.

C chosen per CV fold: base: [0.003, 0.003, 0.03, 0.003, 0.03]; large: [0.003, 0.03, 0.003, 0.03, 0.3]; siglip: [0.003, 0.003, 0.003, 0.003, 0.003]
