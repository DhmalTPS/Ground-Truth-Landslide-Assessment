---
title: Landslide Type Classifier
emoji: ⛰️
colorFrom: yellow
colorTo: green
sdk: docker
app_port: 7860
pinned: false
short_description: Landslide type from a ground photo, with field guidance
models:
  - facebook/dinov2-base
  - facebook/dinov2-large
  - google/siglip2-base-patch16-224
---

# Landslide type classifier (online demo)

Take or upload a ground-level photo of a slope. The app checks that the photo is usable, names
the landslide type (Hungr et al. 2014), shows how sure it is, and gives a safety note, an on-site
checklist and next steps. English and Hindi.

## How to use it

1. Stand downhill of the slope (or across the road) and fit the whole slope in the frame, from
   the top of the scar to the debris at the bottom.
2. Tap **Guided camera**, or pick an existing photo (**From gallery** on a phone, **Upload a
   photo** on a computer).
3. Read the type and confidence, then tick the signs you can see on site. **Save report** keeps
   one image with the photo and every result.

## Types it recognises

Fall / topple, rotational slide, translational (planar) slide, debris flow, earth / mud flow, and
no landslide. Photos that are not ground photos of a slope (drone, satellite or map images) are
flagged as not reliable.

## How accurate it is

On an untouched test set of 263 usable photos from 152 sites, none shared with training:
accuracy **0.81**, macro-F1 **0.78**. Below 60% confidence the app says *uncertain* and shows
the two most likely types instead of guessing. Full method and evaluation: `report.md` in the
GitHub repository.

## Limits of this demo

- It runs on 2 free CPU cores: a photo takes about 15–20 s, longer when several people use it at
  once. The first visit after a quiet period wakes the app, which takes a minute or two.
- **Size estimates are switched off**: on a CPU one estimate takes several minutes. Run the app
  on a laptop with a GPU for sizes (see the repository).
- Uploaded photos are not stored.
- Decision support only: confirm with a geologist or geotechnical engineer before acting.

Code, method and evaluation: https://github.com/DhmalTPS/Landslide-Category-Classifier
