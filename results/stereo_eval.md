# Walk-along metric scale: simulated stereo pairs with known depth

Made by `tools/stereo_eval.py` (simulation from train photos; field errors simulated: walked distance log-sd 0.15, focal log-sd 0.02 or 0.25).

- Pairs: 160, scale found: 113 (71%)
- Scale error (log, what sizes carry): median |err| **0.120**, RMS 0.167, 90th pct |err| 0.272
- Stated sd: median **0.150** (current object prior: 0.345)
- 90 % interval coverage: **87.6%** (target 85-95 %)

| distance | steps | B/Z | pairs | found | median abs err | coverage |
|---|---|---|---|---|---|---|
| 20 m | 2 | 1/13 | 14 | 14 | 0.151 | 79% |
| 20 m | 4 | 1/7 | 1 | 1 | 0.201 | 100% |
| 50 m | 2 | 1/33 | 12 | 12 | 0.057 | 92% |
| 50 m | 4 | 1/17 | 16 | 16 | 0.060 | 75% |
| 50 m | 8 | 1/8 | 5 | 5 | 0.159 | 100% |
| 100 m | 2 | 1/67 | 15 | 14 | 0.151 | 93% |
| 100 m | 4 | 1/33 | 7 | 7 | 0.145 | 100% |
| 100 m | 8 | 1/17 | 12 | 12 | 0.124 | 92% |
| 200 m | 2 | 1/133 | 14 | 3 | 0.089 | 67% |
| 200 m | 4 | 1/67 | 18 | 16 | 0.067 | 88% |
| 200 m | 8 | 1/33 | 13 | 13 | 0.147 | 92% |
