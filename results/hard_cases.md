# Hard-case behaviour (model: probe_base + probe_large + probe_siglip, confident ≥ 0.6)

Photos the first labeling pass rejected; a second AI pass found these usable (labels are AI best guesses, see data/labels/ai_annotation/hard_cases/).

## hard (n = 58)

| Outcome | Share | Agrees with best guess |
|---|---|---|
| rejected as unusable photo | 0.29 | – |
| uncertain (top two shown) | 0.34 | top-2 contains best guess: 0.65 |
| … of which family answer | 0.03 | 1.00 |
| confident type | 0.36 | 0.57 |

## wrongly_rejected (n = 6)

| Outcome | Share | Agrees with best guess |
|---|---|---|
| rejected as unusable photo | 0.83 | – |
| uncertain (top two shown) | 0.00 | top-2 contains best guess: nan |
| … of which family answer | 0.00 | nan |
| confident type | 0.17 | 1.00 |

