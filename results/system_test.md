# End-to-end system test (test split, model: probe_base + probe_large + probe_siglip, confident ≥ 0.6)

1008 test photos, 263 usable ground photos of slopes. Training sets of the deployed models are disjoint from these photos (checked).

| | original | phone-degraded |
|---|---|---|
| Photo check accuracy (usable vs reject) | 0.836 | 0.832 |
| Usable photos accepted | 0.833 | 0.825 |
| Unusable photos rejected | 0.838 | 0.835 |
| **All photos:** confident answers given | 258 | 254 |
| **All photos:** share of confident answers on photos that should have been rejected | 0.295 | 0.315 |
| **All photos: end-to-end precision** (confident answer on a usable photo AND correct type) | 0.605 | 0.602 |
| Usable photos answered confidently | 0.692 | 0.662 |
| Usable photos marked uncertain | 0.141 | 0.163 |
| **Usable photos: type accuracy when answered** | 0.857 | 0.879 |
| Usable photos: top-guess accuracy on all accepted | 0.817 | 0.770 |
| Uncertain answers given as a family (flow/slide) | 5 | 5 |
| Family answers correct | 0.600 | 0.600 |

The test split keeps the collection's mix (about 3 rejects per usable photo); in the field, where most uploads are slope photos, end-to-end precision will be closer to the usable-photo figure.
