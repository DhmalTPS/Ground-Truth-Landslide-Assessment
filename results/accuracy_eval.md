# Type accuracy: cheap improvements, out-of-fold (site-grouped 5-fold, usable train+val)

Made by `tools/accuracy_eval.py`; n = 1062 photos, 586 sites. Test split not read.

| variant | macro-F1 | site-weighted F1 | accuracy | answered (conf >= 0.6) / acc there | F1 diff vs base [90 % site bootstrap] |
|---|---|---|---|---|---|
| base | 0.704 | 0.714 | 77.3% | 73% / 88.1% | - |
| logpool | 0.694 | 0.707 | 77.4% | 80% / 85.8% | -0.009 [-0.022, +0.005] |
| stack | 0.659 | 0.663 | 73.7% | 68% / 86.0% | -0.045 [-0.068, -0.023] |
| concat | 0.707 | 0.713 | 78.8% | 85% / 82.8% | +0.002 [-0.013, +0.017] |
| mc_test | 0.717 | 0.712 | 78.2% | 74% / 87.0% | +0.012 [-0.004, +0.027] |
| mc_both | 0.715 | 0.727 | 78.2% | 74% / 86.8% | +0.012 [-0.004, +0.027] |
| aug_test | 0.706 | 0.701 | 77.6% | 70% / 89.0% | +0.001 [-0.018, +0.020] |
| mc_aug | 0.713 | 0.708 | 78.0% | 71% / 88.0% | +0.008 [-0.007, +0.024] |
| offsets | 0.713 | 0.705 | 78.4% | 72% / 88.7% | +0.007 [-0.018, +0.030] |
| mc_aug_offsets | 0.699 | 0.701 | 77.0% | 70% / 89.5% | -0.007 [-0.039, +0.023] |
