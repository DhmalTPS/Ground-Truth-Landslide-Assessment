"""Guidance layer of the field app: it leads a junior engineer from "where do I stand?" to "what do I do next?".

Each stage of the journey has its own aid:

  before   first-run tour (4 illustrated cards, can be replayed), a per-session safety check,
           single-photo or 4-shot site-survey mode with a shot list, a distance helper (pace it out)
  capture  live viewfinder (needs https or localhost): framing bands for scarp and toe, rule-of-thirds
           grid, a level line and aim angle from the phone sensors, live light, sharpness and steadiness,
           a ready ring, haptic and optional voice cues. Without https the phone's own camera is used.
  check    an instant on-phone photo check before upload: light, shadows, highlights, haze, blur,
           resolution, level and aim. Thresholds come from the training photos
           (tools/calibrate_photo_check.py -> src/photo_check.json); it only warns and never blocks.
  wait     upload progress, then stages paced by the measured server time, field tips, cancel
  result   a "next steps" card (retake, add the distance and re-measure, close-up of the deposit, next
           survey shot), on-site signs that can be ticked (top-2 types compared when the model is
           unsure), a glossary of the numbers, spoken summary
  always   help sheet (photo guide, safety, reading results, glossary, limits, settings), recent
           observations, offline banner, retry, sun mode (high contrast), voice, keyboard and
           screen-reader support

Settings and history stay in this browser (localStorage); nothing extra is sent to the server.
"""
import json
from pathlib import Path

from guide_data import HI, QUESTIONS, QUIZ

_CHECK = Path(__file__).with_name("photo_check.json")
_DEFAULT = {"thresholds": {"lum_min": 71.1, "lum_max": 169.7, "dark_max": 0.157, "bright_max": 0.283,
                           "contrast_min": 28.9, "sharp_min": 414.2}, "percentile_q": 0.75}


def photo_check():
    try:
        return json.loads(_CHECK.read_text())
    except (OSError, ValueError):
        return _DEFAULT


GLOSSARY = {
    "Scarp / crown": "The steep break at the top where the ground tore away. Fresh scarps are bare and sharp-edged.",
    "Toe / deposit": "The bottom of the landslide, where the moved material piled up.",
    "Confidence": "How sure the model is about the type (0-100%). Below the 'confident' mark, the app says Uncertain.",
    "Uncertain / family": "Unsure about the exact type. 'Family' means it is sure of the group (flow or slide), not which member.",
    "90% range": "The size lies in this range with about 90% probability, given the photo. Wide range = rough estimate.",
    "Depth trust": "How well the 3-D depth checks agreed (high / medium / low). Low: treat sizes as order-of-magnitude.",
    "Grain size D16/D50/D84": "Block or boulder sizes: 16%, 50% and 84% of the counted pieces are smaller than these.",
    "Travel angle (H/L)": "Drop height over run-out length. A low angle means the material travelled far (mobile, dangerous).",
    "Size class (Fell 1994)": "Volume class from 'extremely small' (<500 m3) to 'very large', used in hazard reports.",
    "Slope angle": "Steepness of the ground surface in the outlined area, in degrees.",
}

SHOTS = [
    {"id": "overview", "t": "Whole slope", "frame": "full",
     "d": "From below, 20-80 m away. Get the top (scarp) and the bottom (deposit) in one frame."},
    {"id": "source", "t": "Source / scarp", "frame": "top",
     "d": "Zoom in (do not climb) so the upper break, cracks or bare face fill the frame."},
    {"id": "deposit", "t": "Deposit close-up", "frame": "bottom",
     "d": "5-15 m from the toe, boulders and soil filling the frame. This gives the grain size."},
    {"id": "scale", "t": "Something for scale", "frame": "full",
     "d": "The whole slope again with a person, car or pole near the toe. This fixes the metres."},
]

SAFETY = [
    "I am below or beside the slope, not on it or on the deposit.",
    "Nothing hangs over me and I am outside the path of falling rocks.",
    "No fresh cracking, rumbling, running muddy water or moving debris right now.",
    "On a road: I am out of traffic, or someone is watching for me.",
]

FIELD_TIPS = [
    "Cracks above the scarp mean the slope may still be moving: keep clear of the crown.",
    "Photos from two or three spots give a more reliable type than one photo.",
    "Typing the distance to the slope makes the sizes much more accurate.",
    "A person or car in the photo lets the app check its own scale.",
    "Morning or late-afternoon side light shows cracks and steps best.",
    "Wipe the lens: dust and rain drops make photos soft and hazy.",
    "Note the date, location and weather with your observation.",
]

# simple illustrations for the tour (stroke = currentColor, accents use the app gradients)
_IL = 'viewBox="0 0 240 130" class="il" aria-hidden="true"'
ILLUS = [
    '<svg viewBox="0 0 240 130" class="il" aria-hidden="true"><path d="M105.0 44.0L182.9 89.0L136.2 116.0L58.2 71.0Z" fill="currentColor" fill-opacity=".05" stroke="currentColor" stroke-opacity=".35" stroke-width="1"/><path d="M89.4 89.0L58.2 71.0L58.2 35.0Z" fill="#0e4d45"/><path d="M136.2 62.0L105.0 8.0L58.2 35.0L89.4 89.0Z" fill="#34b08c"/><path d="M91.8 24.6Q91.0 48.5 109.7 71.9" fill="none" stroke="#ff745e" stroke-width="4" stroke-linecap="round"/><path d="M147.1 85.0L81.6 21.5M147.1 85.0L112.8 75.5" stroke="currentColor" stroke-width="1.2" stroke-dasharray="3 3" fill="none"/><path d="M147.1 95.3L147.1 87.0" stroke="currentColor" stroke-width="3" stroke-linecap="round"/><circle cx="147.1" cy="83.2" r="3.2" fill="currentColor"/><path d="M88.6 89.4L122.9 109.2M88.6 85.4V93.4M122.9 105.2V113.2" stroke="currentColor" stroke-width="1.2"/><text x="71.8" y="115.3" font-size="10" fill="currentColor">20-80 m</text><text x="155.1" y="99.3" font-size="10" fill="currentColor">you, below</text><text x="119.6" y="27.5" font-size="10" fill="currentColor">whole slope in view</text></svg>',
    f'<svg {_IL}><rect x="18" y="14" width="88" height="104" rx="10" fill="none" stroke="currentColor" stroke-width="2.5"/>'
    '<path d="M24 100L60 36L100 36V112H24Z" fill="url(#g-ground)" opacity=".85"/><path d="M24 28H100M24 100H100" stroke="url(#g-signal)" stroke-width="2" stroke-dasharray="5 4"/>'
    '<text x="38" y="26" font-size="9" fill="currentColor">scarp</text><text x="38" y="113" font-size="9" fill="currentColor">toe</text>'
    '<path d="M44 124l6 5 10-10" stroke="#34b08c" stroke-width="3" fill="none" stroke-linecap="round"/>'
    '<rect x="134" y="14" width="88" height="104" rx="10" fill="none" stroke="currentColor" stroke-width="2.5"/>'
    '<path d="M140 60L222 40V112H140Z" fill="url(#g-ground)" opacity=".45"/><circle cx="176" cy="80" r="16" fill="none" stroke="currentColor" stroke-width="1.5" opacity=".5"/>'
    '<path d="M168 120l12 8M180 120l-12 8" stroke="#e04e2b" stroke-width="3" stroke-linecap="round"/></svg>',
    f'<svg {_IL}><circle cx="52" cy="40" r="14" fill="url(#g-signal)"/><path d="M52 16V8M52 72V64M28 40H20M84 40H76" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>'
    '<rect x="120" y="24" width="56" height="92" rx="9" fill="none" stroke="currentColor" stroke-width="2.5"/>'
    '<path d="M104 70H192" stroke="url(#g-signal)" stroke-width="2.5"/><circle cx="148" cy="70" r="5" fill="#34b08c"/>'
    '<text x="196" y="74" font-size="10" fill="currentColor">level</text><text x="20" y="98" font-size="10" fill="currentColor">daylight, sun behind</text>'
    '<text x="20" y="112" font-size="10" fill="currentColor">two hands, hold still</text></svg>',
    f'<svg {_IL}><rect x="20" y="18" width="200" height="12" rx="6" fill="currentColor" opacity=".12"/><rect x="20" y="18" width="160" height="12" rx="6" fill="url(#g-ground)"/>'
    '<text x="20" y="48" font-size="10" fill="currentColor">confidence: how sure the type is</text>'
    '<path d="M40 86H200" stroke="currentColor" stroke-width="2" opacity=".35"/><path d="M70 86H170" stroke="url(#g-signal)" stroke-width="6" stroke-linecap="round"/>'
    '<circle cx="112" cy="86" r="6" fill="currentColor"/><text x="20" y="112" font-size="10" fill="currentColor">size and its 90% range (wide = rough)</text></svg>',
]
TOUR = [
    ("What this app does", "Photograph a landslide from the ground. The app names its type, shows the on-site signs "
     "to confirm, and estimates its size. It supports your judgement; it does not replace a geologist."),
    ("Stand below, see it all", "Stand at the foot of the slope or across the road, 20-80 m away, never on the slope "
     "or the deposit. Face up at it."),
    ("Frame top to bottom", "Fit the whole failure: the scarp at the top and the toe at the bottom. Not just a close-up "
     "of soil, not mostly sky."),
    ("Light, level, steady", "Daylight with the sun behind or beside you. Hold the phone level with two hands. The live "
     "guide turns green when the shot is good."),
    ("Read the answer", "Confidence says how sure the type is. Sizes come with a 90% range. Below each result, "
     "'Next steps' tells you what extra photo or detail would make it better."),
]

CSS = """
.iconbtn{margin-left:0;flex:none;min-width:44px;height:44px;border-radius:22px;border:1.5px solid var(--edge);background:var(--surface);color:var(--ink);font-weight:700;font-size:1.02rem;line-height:1;font-family:inherit;cursor:pointer}
/* the journey is a climb: stations rise along a trail towards the report, the goal at the top */
.journey{position:relative;display:flex;gap:4px;margin:2px 0 16px;padding:0;list-style:none;counter-reset:j}
.journey::before{content:"";position:absolute;left:0;right:0;top:0;height:40px;background:var(--contour);-webkit-mask:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 40' preserveAspectRatio='none'%3E%3Cpolyline points='10,24 30,21 50,18 70,15 90,12' fill='none' stroke='%23000' stroke-width='1.6' vector-effect='non-scaling-stroke'/%3E%3C/svg%3E") 0 0/100% 100% no-repeat;mask:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 40' preserveAspectRatio='none'%3E%3Cpolyline points='10,24 30,21 50,18 70,15 90,12' fill='none' stroke='%23000' stroke-width='1.6' vector-effect='non-scaling-stroke'/%3E%3C/svg%3E") 0 0/100% 100% no-repeat}
.journey li{position:relative;flex:1;padding-top:12px;font-size:.74rem;line-height:1.25;color:var(--mute);text-align:center;counter-increment:j}
.journey li:nth-child(1){--up:0px}.journey li:nth-child(2){--up:-3px}.journey li:nth-child(3){--up:-6px}.journey li:nth-child(4){--up:-9px}.journey li:nth-child(5){--up:-12px}
.journey li::before{content:counter(j);display:grid;place-items:center;width:24px;height:24px;margin:0 auto 6px;border-radius:50%;border:1.5px solid var(--contour);font-weight:600;font-size:.8rem;font-family:var(--f-sign);background:var(--surface);color:var(--ink-2);transform:translateY(var(--up));transition:background-color .3s ease}
.journey li.done::before{content:"\\2713";background:var(--brand);border-color:var(--brand);color:var(--on-brand)}
.journey li.on{color:var(--ink);font-weight:650}.journey li.on::before{border:2.5px solid var(--brand);color:var(--link);box-shadow:0 0 0 4px var(--tint-ground)}
.seg{display:grid;grid-auto-flow:column;grid-auto-columns:1fr;gap:4px;padding:4px;border-radius:10px;background:var(--surface-2);border:1px solid var(--edge);margin:0 0 14px}
.seg button{border:0;border-radius:9px;padding:8px;min-height:44px;font-weight:600;font-size:.88rem;font-family:inherit;background:transparent;color:var(--ink-2);cursor:pointer}
.seg button[aria-pressed=true]{background:var(--surface);color:var(--ink);box-shadow:inset 0 0 0 1.5px var(--edge);font-weight:700}
.shots{list-style:none;margin:0 0 14px;padding:0;display:grid;gap:8px}
.shots li{display:grid;grid-template-columns:26px 1fr;gap:10px;padding:10px 12px;border-radius:12px;border:1px solid transparent;font-size:.88rem;color:var(--ink-2);cursor:pointer}
.shots li b{display:block;color:var(--ink);font-size:.93rem}
.shots li .n{width:26px;height:26px;border-radius:50%;display:grid;place-items:center;font-weight:700;border:1.5px solid var(--line)}
.shots li.cur{border-color:var(--brand);background:var(--tint-ground)}.shots li.newsite{border-color:var(--contour)}.shots li.cur .n{background:var(--brand);color:var(--on-brand);border:0}
.shots li.done .n{background:var(--tint-ground);color:var(--link);border-color:var(--teal-400)}
.pace{margin-top:8px;font-size:.85rem;color:var(--ink-2)}.pace summary{cursor:pointer;color:var(--link);font-weight:600;min-height:44px;display:flex;align-items:center}
.pace .pr{display:flex;flex-wrap:wrap;gap:6px;align-items:center;margin-top:8px}
.pace input{width:76px;min-height:44px;padding:8px;border-radius:9px;border:1px solid var(--edge);font:inherit;background:transparent;color:inherit}
.locl{display:flex;gap:10px;align-items:flex-start;margin-top:14px;padding:10px 12px;border:1px solid var(--line);border-radius:12px;background:var(--surface-2);font-size:.9rem;line-height:1.45}.locl a{color:var(--link);word-break:break-all}.locl small{opacity:.7}.lpin{flex:none;width:14px;height:14px;margin-top:3px;border-radius:50%;background:var(--info);box-shadow:0 0 0 4px rgba(30,110,220,.18)}
.minibtn{min-height:44px;border:1.5px solid var(--edge);background:var(--surface);color:var(--link);border-radius:8px;padding:8px 14px;font-weight:650;font-size:.9rem;font-family:inherit;cursor:pointer}.minibtn:hover{border-color:var(--link)}
.minibtn.pri{background:var(--brand);color:var(--on-brand);border-color:var(--brand)}
.fieldmsg.okmsg{color:var(--link)}.qband.qlite{margin:var(--s3) 0 0;padding:var(--s2) 0 0;border:0;border-top:1px solid var(--line);border-radius:0;background:none}.qband.qlite p{display:none}
.done-line{margin:0 0 var(--s2);display:flex;flex-wrap:wrap;gap:6px;align-items:baseline}.done-line b{color:var(--link)}
.fieldmsg{font-size:.84rem;color:var(--warn);margin-top:4px;min-height:1em}
.modal{position:fixed;inset:0;z-index:50;display:grid;place-items:end center;background:rgba(6,16,13,.62)}
.modal[hidden]{display:none}
.sheet{width:min(620px,100%);max-height:92vh;overflow:auto;background:var(--surface);color:var(--ink);border-radius:22px 22px 0 0;padding:20px 18px calc(20px + env(safe-area-inset-bottom));box-shadow:var(--shadow)}
@media (min-width:700px){.modal{place-items:center}.sheet{border-radius:22px}}
.sheet h2{margin-top:0}.sheet h3{font-size:.95rem;margin:18px 0 6px}.sheet p,.sheet li{color:var(--ink-2);font-size:.92rem}
.sheet .row{display:flex;gap:8px;justify-content:space-between;align-items:center;margin-top:16px}
.il{width:100%;height:auto;max-height:150px;color:var(--ink-2);margin:4px 0 8px}
.dots{display:flex;gap:6px}.dots i{width:7px;height:7px;border-radius:50%;background:var(--line)}.dots i.on{background:var(--brand)}
.chk{display:flex;gap:10px;align-items:flex-start;padding:10px;border-radius:12px;border:1px solid var(--edge);margin:8px 0;cursor:pointer;font-size:.92rem;color:var(--ink-2)}
.chk input{width:22px;height:22px;margin:0;flex:none;accent-color:#17695a}
.qc li{display:grid;grid-template-columns:22px 1fr;gap:10px;padding:7px 0;border-bottom:1px solid var(--line);font-size:.92rem;color:var(--ink-2)}
.qc{list-style:none;margin:8px 0 12px;padding:0}.qc b{color:var(--ink)}
.qc .ok{color:var(--link)}.qc .warn{color:var(--warn)}
.prog{height:8px;border-radius:99px;background:var(--line);overflow:hidden;margin:12px 0 6px}
.prog i{display:block;height:100%;width:0;background:var(--brand);transition:width .4s linear}
.stages{list-style:none;padding:0;margin:10px 0 0;display:grid;gap:6px;font-size:.88rem;color:var(--mute)}
.stages li::before{content:"\\25CB  "}.stages li.done{color:var(--ink-2)}.stages li.done::before{content:"\\2713  ";color:var(--link)}
.stages li.on{color:var(--ink);font-weight:650}.stages li.on::before{content:"\\25CF  ";color:var(--amber)}
.tipline{margin-top:12px;font-size:.85rem;color:var(--ink-2);padding:10px 12px;border-radius:12px;background:var(--surface-2);border:1px solid var(--line);min-height:3em}
.acts{list-style:none;padding:0;margin:8px 0 0;display:grid;gap:10px}
.acts li{display:grid;grid-template-columns:1fr auto;gap:12px;align-items:center;font-size:.94rem;color:var(--ink-2);padding:10px 0;border-bottom:1px solid var(--line)}.acts li:last-child{border-bottom:0}.acts li:not(:first-child) .minibtn.pri{background:var(--surface);color:var(--link);border-color:var(--edge)}
.acts li b{color:var(--ink)}
.tick{cursor:pointer;border-radius:10px;padding:10px 6px;margin:0 -6px;min-height:44px}.tick:hover{background:var(--surface-2)}.tick[aria-checked=true] .ico{color:var(--on-brand);background:var(--brand);border-radius:50%}
.tick[aria-checked=false] .ico{opacity:.45}.tally{margin-top:12px;font-size:.88rem;color:var(--ink-2)}
.cmp{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:8px}.cmp div{padding:10px;border-radius:12px;border:1px solid var(--line);text-align:center;font-size:.85rem}
.cmp b{display:block;font-size:1.3rem}.cmp .lead{border-color:var(--teal-400);background:var(--tint-ground)}
.gloss dt{font-weight:650;color:var(--ink);margin-top:8px;font-size:.9rem}.gloss dd{margin:2px 0 0;color:var(--ink-2);font-size:.88rem}
details.what{margin-top:10px;font-size:.88rem}details.what summary{cursor:pointer;color:var(--link);font-weight:600;min-height:44px;display:flex;align-items:center}
.hist{list-style:none;padding:0;margin:8px 0 0;display:grid;gap:8px}
.hist li{display:grid;grid-template-columns:48px 1fr auto;gap:10px;align-items:center;min-height:56px;padding:4px;font-size:.88rem;color:var(--ink-2)}
.hist img{width:48px;height:48px;object-fit:cover;border-radius:10px}.hist b{color:var(--ink)}
.netbar{position:sticky;top:0;z-index:40;margin:-8px -4px 10px;padding:9px 12px;border-radius:12px;background:#7a2b1d;color:#fff;font-size:.86rem;text-align:center}
.netbar[hidden]{display:none}
.switch{display:flex;justify-content:space-between;align-items:center;min-height:48px;padding:6px 0;border-bottom:1px solid var(--line);font-size:.92rem}
.switch input{width:22px;height:22px;accent-color:#17695a}
.vf{position:fixed;inset:0;z-index:60;background:#000;color:#fff;overflow:hidden}.vf[hidden]{display:none}
.vf video{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}
.vfg{position:absolute;inset:7% 5% 20%;pointer-events:none}
.vfg i{position:absolute;background:rgba(255,255,255,.28)}.vfg .h1,.vfg .h2{left:0;right:0;height:1px}.vfg .h1{top:33.3%}.vfg .h2{top:66.6%}
.vfg .v1,.vfg .v2{top:0;bottom:0;width:1px}.vfg .v1{left:33.3%}.vfg .v2{left:66.6%}
.band{position:absolute;left:0;right:0;border:2px dashed rgba(255,200,98,.85);border-radius:12px;font-size:.75rem;font-weight:650;padding:4px 8px;color:#ffd58a;text-shadow:0 1px 2px #000}
.vfg .top{top:0;height:18%}.vfg .bot{bottom:0;height:18%;display:flex;align-items:flex-end}
.vfg[data-frame=top] .bot,.vfg[data-frame=bottom] .top{display:none}.vfg[data-frame=top] .top{height:70%}.vfg[data-frame=bottom] .bot{height:70%}
.lvl{position:absolute;left:50%;top:50%;width:46%;height:0;border-top:2px solid #ff745e;transform:translate(-50%,-50%);transition:transform .15s linear,border-color .2s}
.lvl.ok{border-color:#5fd1a8}.lvl::before,.lvl::after{content:"";position:absolute;top:-6px;width:2px;height:10px;background:inherit;border-left:2px solid currentColor;opacity:.6}
.vft{position:absolute;top:0;left:0;right:0;display:flex;justify-content:space-between;align-items:center;gap:8px;padding:calc(10px + env(safe-area-inset-top)) 12px 10px;background:linear-gradient(rgba(0,0,0,.6),transparent)}
.vft button{width:44px;height:44px;border-radius:50%;border:0;background:rgba(0,0,0,.45);color:#fff;font-size:1.1rem;cursor:pointer}
.vfs{font-size:.86rem;font-weight:650;text-align:center;flex:1}
.pills{position:absolute;left:0;right:0;top:calc(62px + env(safe-area-inset-top));display:flex;flex-wrap:wrap;gap:6px;justify-content:center;padding:0 10px}
.pills span{padding:4px 10px;border-radius:99px;font-size:.75rem;font-weight:650;background:rgba(0,0,0,.5)}
.pills .ok{box-shadow:inset 0 0 0 1.5px #5fd1a8}.pills .warn{box-shadow:inset 0 0 0 1.5px #ffc862;color:#ffd58a}
.vfmsg{position:absolute;left:12px;right:12px;bottom:calc(118px + env(safe-area-inset-bottom));text-align:center;font-weight:650;font-size:.95rem;text-shadow:0 1px 3px #000}
.vfb{position:absolute;left:0;right:0;bottom:0;display:grid;grid-template-columns:1fr auto 1fr;align-items:center;padding:14px 16px calc(18px + env(safe-area-inset-bottom));background:linear-gradient(transparent,rgba(0,0,0,.7))}
.vfb .alt{justify-self:start;min-height:44px;border:0;background:rgba(0,0,0,.45);color:#fff;border-radius:99px;padding:9px 12px;font-weight:600;font-size:.8rem;font-family:inherit;cursor:pointer}
.shutter{width:78px;height:78px;border-radius:50%;border:4px solid #ffc862;background:transparent;padding:5px;cursor:pointer;transition:border-color .2s}
.shutter span{display:block;width:100%;height:100%;border-radius:50%;background:#fff}.shutter.ready{border-color:#5fd1a8;box-shadow:0 0 0 6px rgba(95,209,168,.25)}
.vfr{justify-self:end;font-size:.78rem;font-weight:650}
.toast{position:fixed;left:50%;bottom:calc(18px + env(safe-area-inset-bottom));transform:translate(-50%,140%);z-index:70;max-width:min(92vw,520px);padding:11px 16px;border-radius:14px;background:#15242a;color:#fff;font-size:.88rem;box-shadow:var(--shadow);transition:transform .25s ease}
.toast.on{transform:translate(-50%,0)}
.qband{display:grid;grid-template-columns:auto 1fr;gap:10px;align-items:start;padding:12px 14px;margin:14px 0;border-radius:14px;border:1.5px solid var(--line);background:var(--surface)}
.qband .qd{width:14px;height:14px;border-radius:50%;margin-top:4px}.qband b{color:var(--ink)}.qband p{margin:4px 0 0;font-size:.88rem;color:var(--ink-2)}
.qband ul{margin:6px 0 0;padding-left:18px;font-size:.88rem;color:var(--ink-2)}.qband .btns{margin-top:10px}
.q0{--qc:#2f9e7e}.q1{--qc:#c9a227}.q2{--qc:#c8901a}.q3{--qc:#d2452b}
.qband .qd{background:var(--qc)}.qband.q1 .qd,.qband.q2 .qd,.qband.q3 .qd{border-radius:0;width:15px;height:13px;clip-path:polygon(50% 0,100% 100%,0 100%)}.qband.q1,.qband.q2,.qband.q3{border-color:var(--qc)}.qband.q2{background:var(--surface)}.qband.q3{background:rgba(210,69,43,.1);border-width:2px}
.qm{display:inline-flex;gap:3px;vertical-align:middle;margin-left:8px}.qm i{width:15px;height:6px;border-radius:3px;background:rgba(127,127,127,.35)}.qm i.on{background:var(--qc)}
.sev{display:inline-block;margin-left:6px;padding:1px 7px;border-radius:99px;font-size:.75rem;font-weight:700;color:#fff;background:#8a5d00;vertical-align:1px}.sev.s2{background:#b8381f}
.vfq{position:absolute;left:50%;transform:translateX(-50%);bottom:calc(152px + env(safe-area-inset-bottom));display:flex;align-items:center;gap:4px;padding:6px 12px;border-radius:99px;background:rgba(0,0,0,.6);font-size:.8rem;font-weight:700;white-space:nowrap;color:var(--qc)}
.vfq.q0{--qc:#5fd1a8}.vfq.q1{--qc:#ffc862}.vfq.q2{--qc:#ff9a52}.vfq.q3{--qc:#ff745e}.vfq:empty{display:none}
.vfarrow{position:absolute;left:50%;top:44%;transform:translate(-50%,-50%);font-size:68px;line-height:1;color:#ffc862;text-shadow:0 2px 10px #000;pointer-events:none;animation:nudge 1.2s ease-in-out infinite}
.vfarrow:empty{display:none}@keyframes nudge{50%{transform:translate(-50%,-62%)}}@media (prefers-reduced-motion:reduce){.vfarrow{animation:none}}
.pills .bad{box-shadow:inset 0 0 0 1.5px #ff745e;color:#ffb3a3}.shutter.poor{border-color:#ff745e}.netbar.sync{background:#0e4d45}
.qa{display:flex;gap:8px;flex-wrap:wrap}.qa .minibtn{min-width:84px;min-height:44px}
.quiz{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin:6px 0}.quiz button{border:2px solid var(--edge);border-radius:14px;background:var(--surface-2);padding:6px;cursor:pointer;color:var(--ink-2);font-weight:700;font-size:.9rem;font-family:inherit}
.quiz svg{width:100%;height:auto;max-height:190px}.quiz .right{border-color:#34b08c;box-shadow:0 0 0 3px rgba(52,176,140,.25)}.quiz .wrong{opacity:.5}
#obsbox textarea,#obsbox select{width:100%;margin-top:8px;padding:9px;border-radius:10px;border:1px solid var(--edge);font:inherit;background:transparent;color:inherit}#obsbox select{width:auto}
.hist li[role=button]{cursor:pointer;border-radius:10px}.hist li[role=button]:hover{background:var(--surface-2)}
.shots li.newsite{border-style:dashed}.switch select{font:inherit;padding:4px 6px;border-radius:8px;background:transparent;color:inherit;border:1px solid var(--edge)}
.langbtn{margin-left:6px;width:auto;padding:0 10px;border-radius:21px;font-size:.85rem}
body.sun{--mute:var(--ink-2);--line:#9aa6a0;font-size:17.5px}body.sun .card{border-width:2px}body.sun .hungr{color:var(--ink-2)}
"""

JS = r"""
(()=>{const A=window.App,D=A.D,esc=A.esc,G=D.guide,T=G.check.thresholds,$=s=>document.querySelector(s),out=$('#out');
const store={get(k,d){try{const v=localStorage.getItem('lsg.'+k);return v==null?d:JSON.parse(v)}catch(_){return d}},
 set(k,v){try{localStorage.setItem('lsg.'+k,JSON.stringify(v))}catch(_){}}};
const sess={get(k){try{return sessionStorage.getItem('lsg.'+k)}catch(_){return null}},set(k,v){try{sessionStorage.setItem('lsg.'+k,v)}catch(_){}}};
const buzz=p=>{try{navigator.vibrate&&navigator.vibrate(p)}catch(_){}};
let voice=store.get('voice',false),lang=store.get('lang','en');
function say(t){if(!voice||!window.speechSynthesis)return;try{speechSynthesis.cancel();const u=new SpeechSynthesisUtterance(lang==='hi'?tr(t):t);u.lang=lang==='hi'?'hi-IN':'en-IN';u.rate=1.03;speechSynthesis.speak(u)}catch(_){}}
const ICO=n=>D.icons[n].replace('<svg','<svg class="ico"');
const LIVE=!!(navigator.mediaDevices&&navigator.mediaDevices.getUserMedia&&window.isSecureContext);
if(store.get('sun',false))document.body.classList.add('sun');

/* ---------- journey stepper, mode and survey shot list ---------- */
const J=['Safe spot','Frame','Check','Result','Report'];
$('#journey').innerHTML=J.map(t=>`<li>${t}</li>`).join('');
function step(i){[...$('#journey').children].forEach((li,k)=>{li.className=k<i?'done':k===i?'on':''})}
step(sess.get('safe')?1:0);
let mode=store.get('mode','single'),shot=+(sess.get('shot')||0),done=new Set(JSON.parse(sess.get('done')||'[]'));
function saveShots(){sess.set('shot',shot);sess.set('done',JSON.stringify([...done]))}
function drawMode(){
 $('#mode').innerHTML=`<button type="button" data-m="single" aria-pressed="${mode==='single'}">Single photo</button><button type="button" data-m="survey" aria-pressed="${mode==='survey'}">Site survey (4 shots)</button><button type="button" data-m="pano" aria-pressed="${mode==='pano'}">Overlapping set</button>`;
 $('#shots').innerHTML=mode!=='survey'?'':G.shots.map((s,k)=>`<li data-k="${k}" class="${k===shot?'cur':''} ${done.has(s.id)?'done':''}" tabindex="0" role="button" aria-current="${k===shot}"><span class="n">${done.has(s.id)?'&#10003;':k+1}</span><span><b>${esc(s.t)}</b><span>${esc(s.d)}</span></span></li>`).join('')+(done.size?`<li class="newsite" data-new="1" role="button" tabindex="0"><span class="n">+</span><span><b>Start a new site</b><span>Clears the shot list, notes and location for the next landslide.</span></span></li>`:'');
 const h=$('#capH');if(h)h.textContent=mode==='survey'?'Shot '+(shot+1)+' of '+G.shots.length+': '+G.shots[shot].t:mode==='pano'?'Cover the slope with overlapping photos':'Photograph the slope from below';
 A.pano&&A.pano.show(mode==='pano')}
$('#mode').addEventListener('click',e=>{const m=e.target.dataset.m;if(m){mode=m;store.set('mode',m);drawMode()}});
$('#shots').addEventListener('click',e=>{const li=e.target.closest('li');if(!li)return;if(li.dataset.new){newSite();return}shot=+li.dataset.k;saveShots();drawMode()});
function newSite(){done.clear();shot=0;saveShots();['survey','site','notes','gps','weather'].forEach(k=>sess.set(k,''));sess.set('siteId',String(Date.now()));
 const n=$('#notes');if(n){n.value='';$('#weather').value='';gps=null;$('#gpsout').textContent=''}drawMode();$('#sitecard')?.remove();toast('New site started.')}
$('#shots').addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();e.target.click()}});
drawMode();
const curShot=()=>mode==='survey'?G.shots[shot]:null;

/* ---------- distance helper ---------- */
const dist=$('#dist');
function parseDist(v){v=String(v||'').trim().toLowerCase().replace(/[०-९]/g,c=>'०१२३४५६७८९'.indexOf(c)).replace(/(\d),(\d)/,'$1.$2');if(!v)return null;
 const m=v.match(/^(\d+(?:\.\d+)?)\s*(m|mtr|mtrs|meter|meters|metre|metres|मी|मीटर|ft|feet|foot|'|yd|yds|yard|yards|km)?\.?$/);if(!m)return NaN;
 const k={ft:.3048,feet:.3048,foot:.3048,"'":.3048,yd:.9144,yds:.9144,yard:.9144,yards:.9144,km:1000}[m[2]]||1;return Math.round(parseFloat(m[1])*k*10)/10}
A._parseDist=v=>parseDist(v);const distM=()=>{const v=parseDist(dist.value);return v>=1&&v<=3000?v:null};
($('#disthint')||dist).insertAdjacentHTML('afterend',`<div class="fieldmsg" id="distmsg" aria-live="polite"></div>
<details class="pace"><summary>Don't know the distance?</summary>
<div class="pr">Pace it to the toe (only where safe): <input id="steps" type="number" min="1" inputmode="numeric" placeholder="steps"> &times;
<input id="stride" type="number" step="0.05" min="0.4" max="1.2" value="${store.get('stride',0.75)}" aria-label="metres per step"> m =
<b id="paced">&ndash;</b><button type="button" class="minibtn" id="usepace">Use</button></div>
<p class="u-t2">Other ways: a laser rangefinder, or Google Maps &rarr; right-click &rarr; <i>Measure distance</i> from where you stand to the slope. A normal walking step is about 0.75 m; measure 10 of your steps once to know yours.</p></details>`);
const paced=()=>{const s=parseFloat($('#steps').value),k=parseFloat($('#stride').value);return s>0&&k>0?Math.round(s*k*10)/10:null};
$('#steps').oninput=$('#stride').oninput=()=>{const p=paced();$('#paced').textContent=p?p+' m':'–';if(+$('#stride').value)store.set('stride',+$('#stride').value)};
$('#usepace').onclick=()=>{const p=paced();if(p){dist.value=p;dist.dispatchEvent(new Event('input'));buzz(15)}};
dist.addEventListener('input',()=>{const v=parseDist(dist.value),el=$('#distmsg');el.classList.remove('okmsg');
 if(!dist.value.trim()){el.textContent='';return}
 if(!(v>=1&&v<=3000)){el.textContent=tr('Use a distance between 1 and 3000 m (or leave it empty).');return}
 el.classList.add('okmsg');el.textContent=tr('Sizes will use')+' '+v+' m'});

/* ---------- modals: tour, safety, help ---------- */
document.body.insertAdjacentHTML('beforeend',`<div class="modal" id="mTour" hidden role="dialog" aria-modal="true" aria-labelledby="tourT"><div class="sheet"></div></div>
<div class="modal" id="mSafe" hidden role="dialog" aria-modal="true" aria-labelledby="safeT"><div class="sheet"></div></div>
<div class="modal" id="mHelp" hidden role="dialog" aria-modal="true" aria-labelledby="helpT"><div class="sheet"></div></div>
<div class="vf" id="vf" hidden role="dialog" aria-modal="true" aria-label="Camera with framing guide"><video playsinline muted autoplay></video>
<div class="vfg" data-frame="full"><i class="h1"></i><i class="h2"></i><i class="v1"></i><i class="v2"></i><div class="band top">Top of the slope (scarp)</div><div class="band bot">Bottom (toe / deposit)</div></div>
<div class="lvl" aria-hidden="true"></div>
<div class="vft"><button type="button" data-a="close" aria-label="Close camera">&#10005;</button><span class="vfs"></span><button type="button" data-a="voice" aria-label="Voice guidance"></button></div>
<div class="pills" aria-hidden="true"></div><div class="vfarrow" aria-hidden="true"></div><div class="vfq" aria-hidden="true"></div><div class="vfmsg" aria-live="polite"></div>
<div class="vfb"><button type="button" class="alt" data-a="native">Phone camera</button><button type="button" class="shutter" data-a="shoot" aria-label="Take photo"><span></span></button><span class="vfr"></span></div></div>`);
let lastFocus=null;
function openM(id,html){const m=$('#'+id);m.firstElementChild.innerHTML=html;m.hidden=false;lastFocus=document.activeElement;
 (m.querySelector('[data-f]')||m.querySelector('button,input'))?.focus();return m}
function closeM(id){$('#'+id).hidden=true;lastFocus?.focus?.()}
document.addEventListener('keydown',e=>{if(e.key!=='Escape')return;['mTour','mSafe','mHelp'].forEach(id=>{if(!$('#'+id).hidden)closeM(id)});if(!$('#vf').hidden)closeFinder()});
document.querySelectorAll('.modal').forEach(m=>m.addEventListener('click',e=>{if(e.target===m)closeM(m.id)}));

function tour(i=0){const [t,b]=G.tour[i],n=G.tour.length;
 openM('mTour',`<div class="kicker">Guide ${i+1} of ${n}</div><h2 id="tourT">${esc(t)}</h2>${i>0?G.illus[i-1]:''}<p>${esc(b)}</p>
 <div class="row"><button type="button" class="minibtn" data-a="skip">${i?'Back':'Skip'}</button><div class="dots">${G.tour.map((_,k)=>`<i class="${k===i?'on':''}"></i>`).join('')}</div>
 <button type="button" class="minibtn pri" data-f data-a="next">${i<n-1?'Next':'Start'}</button></div>`);
 $('#mTour').onclick=e=>{const a=e.target.dataset.a;if(e.target.id==='mTour'||a==='skip'&&!i){store.set('toured',1);closeM('mTour')}
  else if(a==='skip')tour(i-1);else if(a==='next'){if(i<n-1)tour(i+1);else{store.set('toured',1);quiz(0)}}}}
if(!store.get('toured',0)&&!new URLSearchParams(location.search).get('demo'))tour(0);

function safety(then){
 openM('mSafe',`<div class="kicker">Before you photograph</div><h2 id="safeT">${ICO('alert')} Are you in a safe spot?</h2>
 ${G.safety.map((s,k)=>`<label class="chk"><input type="checkbox" data-s="${k}"><span>${esc(s)}</span></label>`).join('')}
 <p class="hungr">If any of these is not true, move back first. If the slope is moving, leave and report it; no photo is worth it.</p>
 <div class="row"><button type="button" class="minibtn" data-a="cancel">Not now</button><button type="button" class="minibtn pri" data-a="ok" disabled>I am safe, continue</button></div>`);
 const m=$('#mSafe'),ok=m.querySelector('[data-a=ok]');
 m.onchange=()=>{ok.disabled=![...m.querySelectorAll('input')].every(c=>c.checked)};
 m.onclick=e=>{const a=e.target.dataset.a;if(a==='cancel'||e.target===m)closeM('mSafe');if(a==='ok'){sess.set('safe','1');closeM('mSafe');step(1);buzz(15);then()}}}

function help(){const g=G.glossary;
 openM('mHelp',`<div class="row u-m0"><h2 id="helpT" class="u-m0">Help &amp; guide</h2><button type="button" class="minibtn" data-a="x" data-f aria-label="Close help">Close</button></div>
 <h3>Taking a good photo</h3><ol class="steps"><li>Stand below the slope or across the road, 20&ndash;80 m away; never on it.</li><li>Fit the scarp (top) and the toe (bottom) in one frame. Portrait or landscape both work.</li>
 <li>Daylight, sun behind or beside you. Wipe the lens. Hold level with two hands, tap the slope to focus.</li><li>Unsure result? Take more photos from other spots, or use <b>Site survey</b> mode.</li><li>Type the distance (or pace it) for better sizes; a person or car near the toe also helps.</li></ol>
 <h3>Safety</h3><ul class="steps">${G.safety.map(s=>`<li>${esc(s)}</li>`).join('')}</ul>
 <h3>Reading the result</h3><dl class="gloss">${Object.entries(g).map(([k,v])=>`<dt>${esc(k)}</dt><dd>${esc(v)}</dd>`).join('')}</dl>
 <h3>Limits</h3><p>Labels used to train the model were made by AI and the sizes are not yet checked against field measurements; treat sizes as estimates within their ranges. Always confirm with a geologist or geotechnical engineer before acting.</p>
 <h3>Settings</h3><label class="switch">Voice guidance (camera and results)<input type="checkbox" id="sVoice" ${voice?'checked':''}></label>
 <label class="switch">Sun mode (high contrast, bigger text)<input type="checkbox" id="sSun" ${document.body.classList.contains('sun')?'checked':''}></label>
 <label class="switch">Language / भाषा<select id="sLang"><option value="en" ${lang==='en'?'selected':''}>English</option><option value="hi" ${lang==='hi'?'selected':''}>हिन्दी</option></select></label>
 <div class="row"><button type="button" class="minibtn" data-a="tour">Replay the guide</button><button type="button" class="minibtn" data-a="quiz">Practice quiz</button><button type="button" class="minibtn" data-a="clear">Clear recent photos</button></div>
 <p class="hungr">Live camera guide: ${LIVE?'available':'needs a secure address (https or localhost); the phone camera app is used instead'}.</p>`);
 const m=$('#mHelp');
 m.onclick=e=>{const a=e.target.dataset.a;if(a==='x'||e.target===m)closeM('mHelp');if(a==='tour'){closeM('mHelp');tour(0)}if(a==='quiz'){closeM('mHelp');quiz(0)}if(a==='clear'){store.set('hist',[]);safe(async()=>{for(const x of await DB.all('results'))await DB.del('results',x.id)});drawHist();e.target.textContent='Cleared'}};
 m.onchange=e=>{if(e.target.id==='sVoice'){voice=e.target.checked;store.set('voice',voice);say('Voice guidance on')}
  if(e.target.id==='sSun'){document.body.classList.toggle('sun',e.target.checked);store.set('sun',e.target.checked)}
  if(e.target.id==='sLang'){store.set('lang',e.target.value);location.reload()}}}
function quiz(i=0,score=0){const Q=G.quiz,n=Q.length;
 if(i>=n){store.set('quizzed',score);openM('mTour',`<div class="kicker">Practice</div><h2 id="tourT">${score} of ${n} correct</h2><p>${score===n?'Well done. You are ready for the field.':'Read the photo tips once more; the live camera guide will also help on site.'}</p><div class="row"><span></span><button type="button" class="minibtn pri" data-f data-a="end">Done</button></div>`);
  $('#mTour').onclick=e=>{if(e.target.dataset.a==='end'||e.target.id==='mTour')closeM('mTour')};return}
 const q=Q[i];let answered=false;openM('mTour',`<div class="kicker">Practice ${i+1} of ${n}</div><h2 id="tourT">${esc(q.q)}</h2><div class="quiz"><button type="button" data-c="a" aria-label="Photo A">${q.a}<span>A</span></button><button type="button" data-c="b" aria-label="Photo B">${q.b}<span>B</span></button></div>
 <p id="qwhy" class="hungr" aria-live="polite"></p><div class="row"><button type="button" class="minibtn" data-a="skip">Skip practice</button><button type="button" class="minibtn pri" data-a="next" hidden>Next</button></div>`);
 $('#mTour').onclick=e=>{const c=e.target.closest('[data-c]')?.dataset.c,a=e.target.dataset.a;
  if(c&&!answered){answered=true;const ok=c===q.correct;if(ok)score++;buzz(ok?30:[40,60,40]);$('#mTour').querySelectorAll('[data-c]').forEach(b=>b.classList.add(b.dataset.c===q.correct?'right':'wrong'));
   $('#qwhy').innerHTML=`<b>${ok?'Correct.':'Not quite.'}</b> <span>${esc(q.why)}</span>`;const nx=$('#mTour').querySelector('[data-a=next]');nx.hidden=false;nx.focus();say((ok?'Correct. ':'Not quite. ')+q.why)}
  if(a==='next')quiz(i+1,score);if(a==='skip'||e.target.id==='mTour')closeM('mTour')}}
$('#helpBtn').onclick=help;

/* ---------- capture entry points ---------- */
const camIn=$('#cam'),galIn=$('#gal');
function autoGps(){if(store.get('gpsAsked',0)||!navigator.geolocation||!window.isSecureContext)return;store.set('gpsAsked',1);
 navigator.geolocation.getCurrentPosition(setGps,()=>{},{enableHighAccuracy:true,timeout:20000,maximumAge:60000})}
function openCamera(){autoGps();if(LIVE)openFinder();else camIn.click()}
camIn.addEventListener('click',()=>autoGps());
camIn.parentElement.addEventListener('click',e=>{if(e.target===camIn)return;   // the input's own click (label activation or programmatic) passes through
 if(!sess.get('safe')){e.preventDefault();safety(openCamera);return}
 if(LIVE){e.preventDefault();openFinder()}});
galIn.parentElement.addEventListener('click',()=>{if(sess.get('safe'))step(1)});

/* ---------- photo metrics (same as tools/calibrate_photo_check.py) ---------- */
let mc=null,prevG=null;
function pctl(a,p){a=[...a].sort((x,y)=>x-y);const i=(a.length-1)*p/100,l=Math.floor(i);return a[l]+(a[Math.min(l+1,a.length-1)]-a[l])*(i-l)}
// Pillow's antialiased bilinear resampling (triangle filter, support scaled by the reduction, horizontal pass
// then vertical, uint8 after each pass), so the phone computes the same numbers as the calibration script.
// Browser canvas scaling differs between browsers and made sharpness ~40% higher in tests.
function taps(inN,outN){const sc=inN/outN,fs=Math.max(1,sc),T=[];for(let i=0;i<outN;i++){const c=(i+.5)*sc,a=Math.max(0,Math.floor(c-fs+.5)),b=Math.min(inN,Math.floor(c+fs+.5)),w=[];let s=0;
 for(let x=a;x<b;x++){const t=Math.max(0,1-Math.abs((x-c+.5)/fs));w.push(t);s+=t}T.push([a,w.map(v=>s?v/s:0)])}return T}
function metrics(src,keep){const w0=src.videoWidth||src.width,h0=src.videoHeight||src.height,k0=Math.min(1,(keep?1024:4096)/Math.max(w0,h0)),W=Math.round(w0*k0),H=Math.round(h0*k0);
 mc=mc||document.createElement('canvas');mc.width=W;mc.height=H;const x=mc.getContext('2d',{willReadFrequently:true});x.drawImage(src,0,0,W,H);
 const S=x.getImageData(0,0,W,H).data,s=512/Math.max(W,H),w=Math.max(3,Math.round(W*s)),h=Math.max(3,Math.round(H*s)),tx=taps(W,w),ty=taps(H,h),M=new Uint8Array(w*H*3),R=v=>v<0?0:v>255?255:Math.floor(v+.5);
 for(let y=0;y<H;y++)for(let i=0;i<w;i++){const [a,wt]=tx[i];let r=0,gg=0,b=0;for(let k=0,p=(y*W+a)*4;k<wt.length;k++,p+=4){const c=wt[k];r+=S[p]*c;gg+=S[p+1]*c;b+=S[p+2]*c}const q=(y*w+i)*3;M[q]=R(r);M[q+1]=R(gg);M[q+2]=R(b)}
 const n=w*h,g=new Float32Array(n),C3=new Uint8Array(n*3);let su=0,sq=0,dk=0,br=0,sk=0,ni=0;
 for(let j=0;j<h;j++){const [a,wt]=ty[j];for(let i=0;i<w;i++){let r=0,gg=0,b=0;for(let k=0,q=(a*w+i)*3;k<wt.length;k++,q+=w*3){const c=wt[k];r+=M[q]*c;gg+=M[q+1]*c;b+=M[q+2]*c}
  const rr=R(r),g2=R(gg),bb=R(b),v=Math.fround(Math.fround(Math.fround(.299*rr)+Math.fround(.587*g2))+Math.fround(.114*bb)),o=(j*w+i)*3;C3[o]=rr;C3[o+1]=g2;C3[o+2]=bb;g[j*w+i]=v;su+=v;sq+=v*v;if(v<16)dk++;else if(v>239)br++}}
 const tv=[];for(let a=0;a<8;a++)for(let b=0;b<8;b++){const y0=1+Math.floor(a*(h-2)/8),y1=1+Math.floor((a+1)*(h-2)/8),x0=1+Math.floor(b*(w-2)/8),x1=1+Math.floor((b+1)*(w-2)/8);let s1=0,s2=0,k=0;
  for(let y=y0;y<y1;y++)for(let q=y*w+x0,e=y*w+x1;q<e;q++){const l=g[q-w]+g[q+w]+g[q-1]+g[q+1]-4*g[q];s1+=l;s2+=l*l;k++;
   const o=q*3,gv=g[q];ni++;if(Math.abs(l)<6&&((C3[o+2]>C3[o]+8&&C3[o+2]>=C3[o+1]&&gv>100)||gv>220))sk++}tv.push(k?s2/k-(s1/k)**2:0)}
 let motion=null;if(keep){if(prevG&&prevG.length===n){let m=0;for(let j=0;j<n;j+=7)m+=Math.abs(g[j]-prevG[j]);motion=m/(n/7)}prevG=g}
 const mean=su/n;return {lum:mean,dark:dk/n,bright:br/n,contrast:Math.sqrt(Math.max(0,sq/n-mean*mean)),sharp:pctl(tv,90),sky:ni?sk/ni:0,w:w0,h:h0,motion}}
// each check: [name, advice or null, severity 0 ok / 1 minor / 2 serious]. "Minor" = outside the calibrated
// range of the training photos (photo_check.json); "serious" = far outside it (G.severe, a fixed margin).
function judge(m,t){const c=[],V=G.severe,add=(k,s1,s2,msg)=>c.push([k,s1||s2?msg:null,s2?2:s1?1:0]);
 add('Light',m.lum<T.lum_min||m.lum>T.lum_max,m.lum<T.lum_min*V.lum_lo||m.lum>T.lum_max+(255-T.lum_max)*V.lum_hi,
  m.lum<T.lum_min?'Too dark. Face the slope with the sun behind or beside you, or wait for better light.':'Too bright. Point less at the sky; tap the slope on screen to set exposure.');
 add('Shadows',m.dark>T.dark_max,m.dark>T.dark_max*V.dark_x,'Large black areas: deep shadow hides the surface. Step sideways so the slope is evenly lit.');
 add('Highlights',m.bright>T.bright_max,m.bright>T.bright_max*V.bright_x,'Large white areas: sky or glare is blown out. Tilt down so less sky is in the frame.');
 add('Haze / contrast',m.contrast<T.contrast_min,m.contrast<T.contrast_min*V.contrast_x,'Flat, low-contrast image (fog, rain or a dirty lens). Wipe the lens; in fog, move closer.');
 add('Framing',m.sky>T.sky_max,m.sky>V.sky,'Mostly sky. Tilt down so the slope fills most of the frame.');
 add('Sharpness',m.sharp<T.sharp_min,m.sharp<T.sharp_min*V.sharp_x,'Blurred. Use two hands, tap the slope to focus, and hold still while the photo is taken.');
 add('Resolution',Math.min(m.w,m.h)<720,Math.min(m.w,m.h)<V.res,'Small image ('+m.w+'×'+m.h+'). Use the original camera photo, not a screenshot or a chat-app copy.');
 if(t){add('Level',Math.abs(t.roll)>10,Math.abs(t.roll)>V.roll,'Phone tilted sideways by '+Math.round(Math.abs(t.roll))+'°. Hold it level.');
  add('Aim',t.elev<-15||t.elev>60,t.elev<V.elev_lo||t.elev>V.elev_hi,t.elev<-15?'Camera points down. Stand below the slope and look up at it.':'Camera points steeply up. Step back so the whole slope fits.')}
 return c}
// overall quality of the analysis: 0 Good, 1 Fair, 2 Poor, 3 Very poor (a failed server photo check is 3)
const QL=['Good','Fair','Poor','Very poor'];
function grade(c,failed){const s2=c.filter(x=>x[2]===2).length,s1=c.filter(x=>x[2]===1).length;
 return failed||s2>=2?3:s2===1||s1>=3?2:s1?1:0}
const qmeter=l=>`<span class="qm" aria-hidden="true">${[0,1,2,3].map(k=>`<i class="${k<4-l?'on':''}"></i>`).join('')}</span>`;
// hold a changing value until it is seen on n ticks in a row (stops the live hints from flickering)
function hold(st,v,n=2){if(v===st.cand)st.k++;else{st.cand=v;st.k=1}if(st.v===undefined||st.k>=n)st.v=v;return st.v}

/* ---------- phone orientation: gravity in image axes (x right, y down, z forward) ---------- */
let ori=null;
function onOri(e){if(e.beta==null)return;const b=e.beta*Math.PI/180,g=(e.gamma||0)*Math.PI/180,x=Math.cos(b)*Math.sin(g),y=Math.sin(b),z=Math.cos(b)*Math.cos(g),
 th=((screen.orientation&&screen.orientation.angle)??window.orientation??0)*Math.PI/180,ix=x*Math.cos(th)-y*Math.sin(th),iy=x*Math.sin(th)+y*Math.cos(th);
 ori={g:[ix,iy,z].map(v=>v.toFixed(3)).join(','),roll:Math.atan2(ix,iy)*180/Math.PI,elev:Math.atan2(-z,Math.hypot(ix,iy))*180/Math.PI}}
let oriOn=false;async function listenOri(){if(oriOn)return;oriOn=true;try{if(window.DeviceOrientationEvent&&DeviceOrientationEvent.requestPermission)await DeviceOrientationEvent.requestPermission()}catch(_){}
 window.addEventListener('deviceorientation',onOri);window.addEventListener('deviceorientation',onHead);window.addEventListener('deviceorientationabsolute',onHead)}
/* compass bearing of the back camera (degrees from true/magnetic north, clockwise): iOS gives it directly; elsewhere it is
   the -z device axis of R = Rz(alpha) Rx(beta) Ry(gamma) in the east-north-up frame, valid only for absolute alpha */
let head=null;
function onHead(e){let h=null,acc=null;
 if(e.webkitCompassHeading!=null){h=e.webkitCompassHeading;acc=e.webkitCompassAccuracy}
 else if((e.absolute||e.type==='deviceorientationabsolute')&&e.alpha!=null&&e.beta!=null){const r=Math.PI/180,ca=Math.cos(e.alpha*r),sa=Math.sin(e.alpha*r),sb=Math.sin(e.beta*r),cg=Math.cos((e.gamma||0)*r),sg=Math.sin((e.gamma||0)*r);
  const vE=-ca*sg-sa*sb*cg,vN=-sa*sg+ca*sb*cg;if(Math.hypot(vE,vN)<.2)return;h=Math.atan2(vE,vN)/r}
 if(h==null||!isFinite(h))return;head={deg:((h%360)+360)%360,acc:acc!=null&&acc>=0?acc:null,t:Date.now()}}
A._head=onHead;A._headNow=()=>head;
document.querySelectorAll('.btn').forEach(b=>b.addEventListener('click',listenOri,{once:true}));

/* ---------- live viewfinder ---------- */
let stream=null,loop=null,wasReady=false,lastSay=0,cap=null;
const vf=$('#vf'),vid=vf.querySelector('video');
async function openFinder(){listenOri();step(1);vf.hidden=false;const s=curShot(),pz=mode==='pano'&&A.pano;
 vf.querySelector('.vfg').dataset.frame=s?s.frame:pz?'pano':'full';vf.querySelector('.vfs').textContent=s?'Shot '+(shot+1)+': '+s.t:pz?A.pano.label():'Frame the whole slope';
 if(pz)A.pano.finder(true);
 vf.querySelector('[data-a=voice]').textContent=voice?'\u{1F50A}':'\u{1F507}';
 try{stream=await navigator.mediaDevices.getUserMedia({video:{facingMode:{ideal:'environment'},width:{ideal:3840},height:{ideal:2160}},audio:false});
  vid.srcObject=stream;await vid.play();
  try{const tr=stream.getVideoTracks()[0];cap=window.ImageCapture?new ImageCapture(tr):null}catch(_){cap=null}
  prevG=null;wasReady=false;loop=setInterval(liveTick,450);say(s?s.d:pz?A.pano.hint():'Frame the whole slope from below, top to bottom.');
  vf.querySelector('[data-a=shoot]').focus()}
 catch(err){closeFinder();camIn.click()}}
function closeFinder(){clearInterval(loop);loop=null;if(stream)stream.getTracks().forEach(t=>t.stop());stream=null;vf.hidden=true;A.pano&&A.pano.finder(false)}
function liveTick(){if(!vid.videoWidth)return;liveShow(metrics(vid,true),ori,mode==='pano'&&A.pano?A.pano.tick(vid,ori):null)}
// one live reading -> pills (coloured by severity), quality meter, one instruction with a direction arrow, shutter
// ring. Level and instruction change only after 2 readings in a row agree. The shutter always works.
const lv={q:{},m:{}};
function liveShow(m,t,px){const c=judge(m,t).filter(x=>x[0]!=='Resolution'&&!(mode==='pano'&&x[0]==='Framing')),pills=[];
 const steady=m.motion==null||m.motion<G.steadyMax,own=c.filter(x=>x[1]).sort((a,b)=>b[2]-a[2]);if(!steady)own.push(['Steady','Hold still for a moment.',1]);
 const bad=(px?px.bad.map(b=>[b[0],b[1],1]):[]).concat(own);
 const lvl=vf.querySelector('.lvl');if(t){lvl.style.display='';lvl.style.transform=`translate(-50%,-50%) rotate(${-t.roll}deg)`;lvl.classList.toggle('ok',Math.abs(t.roll)<=3)}else lvl.style.display='none';
 const cls=s=>s===2?'bad':s?'warn':'ok';
 for(const [k,v,s] of c)pills.push(`<span class="${cls(v?s:0)}">${k}</span>`);pills.push(`<span class="${steady?'ok':'warn'}">Steady</span>`);
 if(t)pills.push(`<span class="${t.elev>=-10&&t.elev<=45?'ok':'warn'}">Aim ${Math.round(t.elev)}°</span>`);
 if(px)pills.unshift(...px.pills);
 vf.querySelector('.pills').innerHTML=pills.join('');
 const q=hold(lv.q,grade(c.concat(steady?[]:[['Steady','',1]]),false)),top=hold(lv.m,bad.length?bad[0][0]:''),hit=bad.find(x=>x[0]===top)||bad[0],ready=!top;
 const vq=vf.querySelector('.vfq');vq.className='vfq q'+q;vq.innerHTML=esc(tr('Photo quality'))+': '+esc(tr(QL[q]))+qmeter(q);
 const msg=ready||!hit?(px&&px.good)||'Good. Take the photo.':hit[1];vf.querySelector('.vfmsg').textContent=msg;
 const k=ready?'':top;vf.querySelector('.vfarrow').textContent=k==='Framing'||(k==='Aim'&&t&&t.elev>60)?'\u2193':k==='Aim'?'\u2191':'';
 const sh=vf.querySelector('.shutter');sh.classList.toggle('ready',ready&&q===0);sh.classList.toggle('poor',q>=2);
 sh.setAttribute('aria-label',tr('Take photo')+', '+tr('Photo quality')+': '+tr(QL[q]));
 vf.querySelector('.vfr').textContent=ready&&q===0?'Ready':q===1?'OK to shoot':q>=2?'Can still shoot':'';
 const now=Date.now();if(ready&&!wasReady){buzz(30);say(msg);lastSay=now}else if(!ready&&(msg!==lv.said||now-lastSay>5000)){say(msg);lastSay=now}lv.said=msg;wasReady=ready;
 return {q,ready,msg}}
async function shoot(){const t=ori;let blob=null;buzz([20,40,20]);
 try{if(cap&&cap.takePhoto)blob=await cap.takePhoto()}catch(_){blob=null}
 if(!blob){const c=document.createElement('canvas');c.width=vid.videoWidth;c.height=vid.videoHeight;c.getContext('2d').drawImage(vid,0,0);blob=await new Promise(r=>c.toBlob(r,'image/jpeg',.92))}
 if(mode==='pano'&&A.pano){gstate.live=true;A.pano.shot(blob,t,vid);return}
 closeFinder();start(blob,true,t,true)}
vf.addEventListener('click',e=>{const a=e.target.closest('[data-a]')?.dataset.a;if(a==='close')closeFinder();if(a==='shoot')shoot();
 if(a==='native'){closeFinder();camIn.click()}if(a==='voice'){voice=!voice;store.set('voice',voice);e.target.textContent=voice?'\u{1F50A}':'\u{1F507}';say('Voice guidance on')}});

/* ---------- language: English / Hindi (text nodes are translated as they appear) ---------- */
const HI=G.hi||{};
const RX=[[/^Shot (\d) of (\d): (.+)$/,(m,a,b,c)=>`शॉट ${a}/${b}: ${HI[c]||c}`],[/^Shot (\d): (.+)$/,(m,a,b)=>`शॉट ${a}: ${HI[b]||b}`],
 [/^Uploading… (\d+)%$/,(m,a)=>`अपलोड हो रहा है… ${a}%`],[/^(\d+) s, about (\d+) s left$/,(m,a,b)=>`${a} सेकंड, लगभग ${b} सेकंड बाकी`],
 [/^(\d+) s, taking longer than usual, still working$/,(m,a)=>`${a} सेकंड, सामान्य से अधिक समय, काम जारी है`],[/^Guide (\d) of (\d)$/,(m,a,b)=>`गाइड ${a}/${b}`],
 [/^Practice (\d) of (\d)$/,(m,a,b)=>`अभ्यास ${a}/${b}`],[/^(\d) of (\d) correct$/,(m,a,b)=>`${b} में से ${a} सही`],[/^Tip: (.+)$/,(m,a)=>'सुझाव: '+(HI[a]||a)],
 [/^Aim (-?\d+)°$/,(m,a)=>`दिशा ${a}°`],[/^(\d) things could be better$/,(m,a)=>`${a} चीज़ें बेहतर हो सकती हैं`],[/^(.+):$/,(m,a)=>HI[a]?HI[a]+':':m],
 [/^Estimated dimensions, depth trust: (\w+)$/,(m,a)=>`अनुमानित आयाम, गहराई भरोसा: ${HI[a]||a}`],[/^Site result, (\d) shots combined$/,(m,a)=>`स्थल परिणाम, ${a} शॉट मिलाकर`],
 [/^Recent observations \(this phone\)$/,()=>'हाल के अवलोकन (यह फ़ोन)'],[/^Answers below (\d+)% are marked uncertain\.$/,(m,a)=>`${a}% से कम वाले उत्तर अनिश्चित माने जाते हैं।`],[/^Volume \((.+)\)$/,(m,a)=>`आयतन (${a})`],
 [/^(.+) \(second choice\)$/,(m,a)=>`${HI[a]||a} (दूसरा विकल्प)`],[/^Measured with your distance of ([\d.]+) m\.$/,(m,a)=>`आपकी ${a} मीटर दूरी से मापा गया।`]];
function tr(s){if(lang!=='hi'||!s)return s;const k=s.trim();if(!k)return s;let v=HI[k];if(v==null)for(const [re,f] of RX){if(re.test(k)){v=k.replace(re,f);break}}return v==null?s:s.replace(k,v)}
function trTree(n){if(n.nodeType===3){const v=tr(n.nodeValue);if(v!==n.nodeValue)n.nodeValue=v;return}
 if(n.nodeType!==1||/^(SCRIPT|STYLE|svg|TEXTAREA)$/.test(n.tagName))return;
 for(const a of ['placeholder','aria-label','title']){const v=n.getAttribute(a);if(v){const t=tr(v);if(t!==v)n.setAttribute(a,t)}}
 n.childNodes.forEach(trTree)}
if(lang==='hi'){document.documentElement.lang='hi';trTree(document.body);
 new MutationObserver(ms=>{for(const m of ms)m.addedNodes.forEach(trTree)}).observe(document.body,{childList:true,subtree:true})}
$('#langBtn').textContent=lang==='hi'?'English':'हिंदी';$('#langBtn').onclick=()=>{store.set('lang',lang==='hi'?'en':'hi');location.reload()};

/* ---------- local database: offline queue and full results (IndexedDB, this phone only) ---------- */
const DB=(()=>{let p=null;const open=()=>p||(p=new Promise((res,rej)=>{try{const r=indexedDB.open('landslide-guide',1);
 r.onupgradeneeded=()=>{const d=r.result;d.createObjectStore('queue',{keyPath:'id'});d.createObjectStore('results',{keyPath:'id'})};r.onsuccess=()=>res(r.result);r.onerror=()=>rej(r.error)}catch(e){rej(e)}}));
 const run=async(st,m,fn)=>{const d=await open();return new Promise((res,rej)=>{const t=d.transaction(st,m),q=fn(t.objectStore(st));let v;if(q)q.onsuccess=()=>{v=q.result};t.oncomplete=()=>res(v);t.onerror=()=>rej(t.error)})};
 return {put:(s,v)=>run(s,'readwrite',o=>o.put(v)),get:(s,k)=>run(s,'readonly',o=>o.get(k)),del:(s,k)=>run(s,'readwrite',o=>o.delete(k)),all:s=>run(s,'readonly',o=>o.getAll())}})();
const safe=async(f,d)=>{try{return await f()}catch(_){return d}};
function toast(t){let el=$('#toast');if(!el){document.body.insertAdjacentHTML('beforeend','<div id="toast" class="toast" role="status" aria-live="polite"></div>');el=$('#toast')}
 el.textContent=t;el.classList.add('on');clearTimeout(el._t);el._t=setTimeout(()=>el.classList.remove('on'),5000)}
async function photoURL(blob,max){try{const b=await createImageBitmap(blob),s=Math.min(1,max/Math.max(b.width,b.height)),c=document.createElement('canvas');c.width=Math.round(b.width*s);c.height=Math.round(b.height*s);
 c.getContext('2d').drawImage(b,0,0,c.width,c.height);return c.toDataURL('image/jpeg',max>200?.82:.6)}catch(_){return ''}}
// thumbnail from a data URL: decoded as an image with a time limit (no fetch(), which can stall and hold up the save queue)
async function urlShrink(u,max){if(!u)return '';try{const i=await loadImg(u,false,5000);if(!i)return '';const s=Math.min(1,max/Math.max(i.naturalWidth,i.naturalHeight)),c=document.createElement('canvas');
 c.width=Math.max(1,Math.round(i.naturalWidth*s));c.height=Math.max(1,Math.round(i.naturalHeight*s));c.getContext('2d').drawImage(i,0,0,c.width,c.height);return c.toDataURL('image/jpeg',.6)}catch(_){return ''}}

/* ---------- observation record: notes, weather, location ---------- */
$('.pace').insertAdjacentHTML('afterend',`<details class="pace" id="obsbox"><summary>Notes &amp; location (for the report)</summary>
<textarea id="notes" rows="2" placeholder="Site name, road / km, what you saw"></textarea>
<div class="pr"><select id="weather" aria-label="Weather"><option value="">Weather…</option><option value="Dry">Dry</option><option value="Raining now">Raining now</option><option value="Rain in the last 24 h">Rain in the last 24 h</option></select>
<button type="button" class="minibtn" id="gpsbtn">Add my location</button></div><div class="hungr" id="gpsout"></div></details>`);
const notes=$('#notes'),weather=$('#weather');notes.value=sess.get('notes')||'';weather.value=sess.get('weather')||'';
notes.oninput=()=>sess.set('notes',notes.value);weather.onchange=()=>sess.set('weather',weather.value);
let gps=null;try{gps=JSON.parse(sess.get('gps')||'null')}catch(_){}
if(gps&&!(isFinite(gps.lat)&&isFinite(gps.lon)))gps=null;
const showGps=()=>{$('#gpsout').textContent=gps?`Location: ${gps.lat.toFixed(5)}, ${gps.lon.toFixed(5)} (±${Math.round(gps.acc||0)} m)`:''};showGps();
// a fix arriving shortly after a photo belongs to that photo: it is attached to its record and the report is refreshed
function setGps(p){const c=p.coords;if(!isFinite(c.latitude)||!isFinite(c.longitude))return;
 gps={lat:c.latitude,lon:c.longitude,acc:c.accuracy,alt:c.altitude??null,altAcc:c.altitudeAccuracy??null,t:Date.now()};sess.set('gps',JSON.stringify(gps));showGps();
 if(curMeta&&Math.abs(gps.t-curMeta.t)<180000&&(!curMeta.gps||Math.abs(curMeta.gps.t-curMeta.t)>180000||curMeta.gps.acc>gps.acc)){curMeta.gps=gps;if(cur&&cur.__id)finish(cur)}
 locLine()}
function askGps(){if(!navigator.geolocation||!window.isSecureContext){$('#gpsout').textContent='Location needs a secure address (start the app with --https). You can type it in the notes.';toast(tr('Location needs a secure address (start the app with --https). You can type it in the notes.'));return}
 $('#gpsout').textContent='Finding your location…';navigator.geolocation.getCurrentPosition(p=>{setGps(p);buzz(20)},
  e=>{$('#gpsout').textContent='Location not available ('+e.message+'). You can type it in the notes.'},{enableHighAccuracy:true,timeout:20000,maximumAge:60000})}
$('#gpsbtn').onclick=askGps;
// once the user has allowed location, every camera photo gets a fresh fix without asking again
async function freshGps(){if(!navigator.geolocation||!window.isSecureContext)return;
 try{const s=navigator.permissions&&await navigator.permissions.query({name:'geolocation'});if(!s||s.state!=='granted')return}catch(_){return}
 navigator.geolocation.getCurrentPosition(setGps,()=>{},{enableHighAccuracy:true,timeout:15000,maximumAge:20000})}
let lastPGps=null,lastHead=null;
const meta=()=>({t:Date.now(),notes:notes.value.trim(),weather:weather.value,gps,pgps:lastPGps,head:lastHead,shot:curShot()?.t||'',shotId:curShot()?.id||'',mode,dist:lastDist});

/* ---------- what the guidance did (sent with the photo, logged for tools/guidance_report.py) ---------- */
let gstate={flags:[],override:false,retakes:0,live:false};
const gx=()=>JSON.stringify({flags:gstate.flags,override:gstate.override,retakes:gstate.retakes,live:gstate.live,mode,shot:curShot()?.id||'',lang,set:mode==='pano'&&A.pano?A.pano.gx():''});
function params(o){const q=new URLSearchParams(location.search);q.delete('demo');for(const [k,v] of Object.entries(o))if(v!=null&&v!=='')q.set(k,v);return q}
const gArg=()=>lastSrc==='cam'&&lastTilt?lastTilt.g:null;
const ema=(k,v,d)=>Math.round(.6*store.get(k,d)+.4*v);

/* ---------- instant photo check ---------- */
const sevTag=s=>s?`<span class="sev s${s}">${s===2?'serious':'minor'}</span>`:'';
let photoQ={level:0,issues:[]};
let lastF35=null,lastBlob=null,lastTilt=null,lastSrc='cam',lastDist=null,xhr=null,job=null,cur=null,curMeta=null,curPhoto='';
A.onPick=(f,fromCam)=>start(f,fromCam,fromCam?ori:null,false);
async function start(file,fromCam,t,live){lastSrc=fromCam?'cam':'gal';gstate.live=!!live;gstate.override=false;step(2);
 lastHead=fromCam&&head&&Date.now()-head.t<5000?{...head,src:'compass'}:null;if(fromCam)freshGps();
 lastF35=A.f35Of?await A.f35Of(file):null;lastPGps=A.gpsOf?await A.gpsOf(file):null;
 const fig=$('#fig'),prev=$('#prev');prev.src=URL.createObjectURL(file);fig.style.display='block';A.setChip('','Checking photo…',true);
 fig.scrollIntoView({behavior:'smooth',block:'start'});
 let m=null;try{const bmp=await createImageBitmap(file,{imageOrientation:'from-image'});m=metrics(bmp);bmp.close&&bmp.close()}catch(_){}
 lastBlob=await A.shrink(file);lastTilt=t;
 const c=m?judge(m,t):[],bad=c.filter(x=>x[1]).sort((a,b)=>b[2]-a[2]);gstate.flags=bad.map(b=>b[0]);
 photoQ={level:grade(c,false),issues:bad};
 if(photoQ.level<2){send();return}       // Good / Fair: no stop; a Fair result carries its quality band
 const l=photoQ.level;A.setChip(l===3?'bad':'signal',tr('Photo quality')+': '+tr(QL[l]));say(tr('Photo quality')+': '+tr(QL[l])+'. '+tr(bad[0][1]));buzz([40,60,40]);
 out.innerHTML=`<section class="card qband q${l}" aria-live="polite" style="display:block"><div class="kicker">Instant photo check</div><h2><span>Photo quality</span>: <span>${QL[l]}</span>${qmeter(l)}</h2>
 <ul class="qc">${c.map(([k,v,s])=>`<li>${v?`<span class="warn">${ICO('alert')}</span><span><b>${k}:</b>${sevTag(s)} <span>${esc(v)}</span></span>`:`<span class="ok">${ICO('check')}</span><span><b>${k}</b> <span>OK</span></span>`}</li>`).join('')}</ul>
 <p class="hungr u-b3">${l===3?'The answer from this photo is likely to be wrong. Retaking is strongly advised.':'The answer from this photo will be rough.'} <span>You can still analyse it: the result is shown as computed and marked with this quality.</span></p>
 <div class="btns"><button type="button" class="btn primary" data-a="retake">${ICO('camera')}Retake</button><button type="button" class="btn ghost" data-a="send">Analyse anyway</button></div></section>`;
 out.querySelector('[data-a=retake]').onclick=()=>{gstate.retakes++;fig.style.display='none';out.innerHTML='';step(1);lastSrc==='cam'?openCamera():galIn.click()};
 out.querySelector('[data-a=send]').onclick=()=>{gstate.override=true;send()}}

/* ---------- requests with progress: type first (seconds), then sizes ---------- */
function prog(el,stages,eta,withUpload){
 el.innerHTML=`<div class="prog"><i></i></div><div class="hungr ptime">${withUpload?'Uploading…':''}</div><ul class="stages">${stages.map(s=>`<li>${esc(s[1])}</li>`).join('')}</ul>`;
 const bar=el.querySelector('.prog i'),tm=el.querySelector('.ptime'),li=[...el.querySelectorAll('.stages li')],t0=Date.now(),U=withUpload?12:0;let up=0,ts=withUpload?0:Date.now();
 const iv=setInterval(()=>{if(!el.isConnected){clearInterval(iv);return}
  if(!ts){bar.style.width=(up*U).toFixed(1)+'%';tm.textContent='Uploading… '+Math.round(up*100)+'%';return}
  const f=(Date.now()-ts)/eta,p=f<1?f*.9:.9+.09*(1-Math.exp(-(f-1)*2)),left=Math.max(0,Math.round((eta-(Date.now()-ts))/1000));
  bar.style.width=(U+p*(100-U)).toFixed(1)+'%';tm.textContent=Math.round((Date.now()-t0)/1000)+' s'+(f<1?', about '+left+' s left':', taking longer than usual, still working');
  li.forEach((x,k)=>{const a=stages[k][0],b=k+1<stages.length?stages[k+1][0]:9;x.className=f>=b?'done':f>=a?'on':''})},400);
 return {up:v=>{up=v},srv:()=>{ts=ts||Date.now()},stop:()=>clearInterval(iv)}}
function tipRot(el){let i=Math.floor(Math.random()*G.tips.length);const put=()=>{el.textContent='Tip: '+G.tips[i]};put();
 const iv=setInterval(()=>{if(!el.isConnected){clearInterval(iv);return}i=(i+1)%G.tips.length;put()},7000)}
function post(url,body,P,h){const x=new XMLHttpRequest();xhr=x;x.open('POST',url);x.timeout=240000;
 if(body){x.setRequestHeader('Content-Type',body.type||'application/octet-stream');x.upload.onprogress=e=>{if(e.lengthComputable&&P)P.up(e.loaded/e.total)};x.upload.onload=()=>P&&P.srv()}
 x.onload=()=>{P&&P.stop();let r;try{r=JSON.parse(x.responseText)}catch(_){r={error:'Unexpected reply from the server ('+x.status+')'}}x.status===200?h.ok(r):h.err(r.error||('Server error '+x.status),x.status)};
 x.onerror=()=>{P&&P.stop();h.err('Could not reach the server. Check the Wi-Fi or hotspot connection to the laptop running the app.',0)};
 x.ontimeout=()=>{P&&P.stop();h.err('The server took more than 4 minutes. It may be busy or out of memory; try again.',-1)};
 x.onabort=()=>{P&&P.stop();h.err(null,-2)};x.send(body||null);return x}
function busy(title){out.innerHTML=`<section class="card result" aria-busy="true"><div class="kicker">${esc(title)}${curShot()?', '+esc(curShot().t):''}</div><div id="pg"></div><div class="tipline" id="ptip"></div>
 <div class="u-t3"><button type="button" class="minibtn" id="pcancel">Cancel</button></div></section>`;tipRot($('#ptip'));$('#pcancel').onclick=()=>xhr&&xhr.abort()}
function cancelled(){A.setChip('','Cancelled');out.innerHTML='';step(1)}
function send(){lastDist=distM();curMeta=meta();job=null;
 if(!navigator.onLine){queueIt();return}
 A.setChip('','Identifying…',true);busy('Analysing photo');
 const P=prog($('#pg'),G.stagesType,store.get('etaT',4000),true);
 post('predict?'+params({stage:'type',d:lastDist,g:gArg(),f35:lastF35,gx:gx()}),lastBlob,P,{
  ok:r=>{if(r.ms)store.set('etaT',ema('etaT',r.ms,4000));cur=r;job=r.job||null;withQ(r);A.render(r);afterType(r);sizes(r)},
  err:(m,s)=>s===-2?cancelled():fail(m,s===0)})}
function fullSend(d0){A.setChip('','Analysing…',true);busy('Sending the photo again');
 const P=prog($('#pg'),G.stagesType.concat(G.stagesDims.map(([f,t])=>[.12+f*.88,t])),store.get('etaT',4000)+store.get('etaD',28000),true);
 post('predict?'+params({stage:'full',d:d0??lastDist,g:gArg(),f35:lastF35,gx:gx()}),lastBlob,P,{
  ok:r=>{if(d0)lastDist=d0;const id=cur&&cur.__id;cur=r;if(id)r.__id=id;job=null;withQ(r);A.render(r);afterType(r);if(r.dimensions)afterDims(r);finish(r)},
  err:(m,s)=>s===-2?cancelled():fail(m,s===0)})}
function measure(d0){const slot=document.createElement('section');slot.className='card';slot.id='dimslot';
 slot.innerHTML=`<div class="kicker">Estimated dimensions</div><p class="hungr u-t1">The type is ready above. Measuring the size now; you can already tick the signs and answer the questions.</p><div id="dpg"></div>
 <button type="button" class="minibtn u-t3" id="dcancel">Skip sizes</button>`;
 const old=$('#dimcard');if(old)old.replaceWith(slot);else{const m=out.querySelector('.meta');m?out.insertBefore(slot,m):out.appendChild(slot)}
 A.setChip('','Measuring…',true);$('#dcancel').onclick=()=>xhr&&xhr.abort();
 const dv=d0??lastDist,P=prog($('#dpg'),G.stagesDims,store.get('etaD',28000),false);
 post('measure?'+params({job,d:dv,g:gArg()}),null,P,{
  ok:res=>{store.set('etaD',ema('etaD',res.ms||28000,28000));lastDist=dv||null;if(curMeta)curMeta.dist=lastDist;cur.dimensions=res.dimensions;placeDims(cur);afterDims(cur);finish(cur)},
  err:(m,s)=>{if(s===410&&lastBlob){fullSend(dv);return}
   slot.innerHTML=`<div class="kicker">Estimated dimensions</div><p class="hungr">${s===-2?'Sizes skipped.':'Sizes could not be measured: '+esc(m)}</p><button type="button" class="minibtn" id="dretry">Measure sizes</button>`;
   $('#dretry').onclick=()=>measure(dv);typeChip(cur);finish(cur)}})}
function typeChip(r){A.setChip(r.status==='uncertain'?'signal':r.status==='bad_photo'?'bad':'',r.status==='uncertain'?'Uncertain':r.status==='bad_photo'?'Not reliable':'Most likely type')}
// the quality of this analysis travels with the result (saved, reports, history)
function withQ(r){const lv=Math.max(photoQ.level,r.status==='bad_photo'?3:0);r.quality={level:lv,issues:photoQ.issues.map(x=>[x[0],x[1],x[2]]),failed:r.status==='bad_photo'};photoQ={level:0,issues:[]};return r}
function qLevel(r){return r.quality?r.quality.level:r.status==='bad_photo'?3:0}
function qBand(r){const q=r.quality||{level:qLevel(r),issues:[],failed:r.status==='bad_photo'},l=q.level,old=$('#qband');if(old)old.remove();
 const what=['Nothing to fix: the photo meets the quality checks.','Small issues: the result is a little less reliable than usual.',
  'Rough result: treat it as a first look and retake if you can.','Not reliable: shown only for reference. Retake before acting on it.'][l];
 const items=q.issues.map(([k,v,s])=>`<li><b>${esc(k)}</b>${sevTag(s)} <span>${esc(v)}</span></li>`);
 if(q.failed)items.unshift(`<li><b>Photo check</b>${sevTag(2)} <span>This does not look like a ground photo of a slope</span> (${Math.round((r.usable||0)*100)}% <span>usable</span>).</li>`);
 const h=`<section class="qband q${l}" id="qband" role="status"><span class="qd"></span><div><b><span>Photo quality</span>: <span>${QL[l]}</span></b>${qmeter(l)}<p>${what}</p>
  ${items.length?`<ul>${items.join('')}</ul>`:''}${l?`<p>Nothing is adjusted to look better: the confidence and sizes are the model's own.</p>`:''}
  ${l>=2?`<div class="btns"><button type="button" class="btn ${l===3?'primary':'ghost'}" data-a="retake">${ICO('camera')}Retake</button></div>`:''}</div></section>`;
 const rc=out.querySelector('.card.result');if(l===0&&rc)rc.insertAdjacentHTML('beforeend',h.replace('class="qband q0"','class="qband q0 qlite"'));else out.insertAdjacentHTML('afterbegin',h);
 $('#qband [data-a=retake]')?.addEventListener('click',()=>act('retake'))}
// sizes: measured straight away, except after a failed photo check, where one tap asks for them
function sizes(r){if(!job){finish(r);return}if(r.status!=='bad_photo'){measure();return}
 const slot=document.createElement('section');slot.className='card';slot.id='dimslot';
 slot.innerHTML=`<div class="kicker">Estimated dimensions</div><p class="hungr u-tb">Sizes from a photo that failed the photo check are not reliable, so they are not measured automatically.</p><button type="button" class="minibtn" id="dany">Estimate sizes anyway</button>`;
 const m=out.querySelector('.meta');m?out.insertBefore(slot,m):out.appendChild(slot);$('#dany').onclick=()=>measure();finish(r)}
function findDims(){return $('#dimcard')||[...out.querySelectorAll('.card')].find(c=>/^Estimated dimensions|^अनुमानित आयाम/.test((c.querySelector('.kicker')?.textContent||'').trim())&&c.id!=='dimslot')}
function placeDims(r){const w=document.createElement('div');w.innerHTML=A.dims(r.dimensions);const c=w.firstElementChild;c.id='dimcard';
 if(qLevel(r)>=2&&r.dimensions.available)c.insertAdjacentHTML('afterbegin',`<p class="note u-b3"><b>${esc(tr('Photo quality'))}: ${esc(tr(QL[qLevel(r)]))}.</b> <span>The 90% ranges were checked on usable photos; with this photo the real error can be larger than shown.</span></p>`);const s=$('#dimslot')||$('#dimcard');s?s.replaceWith(c):out.appendChild(c);typeChip(r)}
function fail(msg,net){A.fail(msg);const c=out.firstElementChild;
 c.insertAdjacentHTML('beforeend',`<div class="btns u-t3"><button type="button" class="btn primary" data-a="retry">Try again</button>${net?'<button type="button" class="btn ghost" data-a="later">Send later</button>':'<button type="button" class="btn ghost" data-a="new">New photo</button>'}</div>`);
 c.querySelector('[data-a=retry]').onclick=()=>lastBlob&&send();
 c.querySelector('[data-a=later]')?.addEventListener('click',queueIt);c.querySelector('[data-a=new]')?.addEventListener('click',()=>{out.innerHTML='';$('#fig').style.display='none';step(1)});
 say(tr('Something went wrong')+'. '+tr(msg));buzz([80,60,80])}

/* ---------- after the type: next steps, decision questions, tick-able signs ---------- */
function addAct(t,l,a){const nc=$('#nextcard');if(!nc)return;nc.hidden=false;const li=document.createElement('li');
 li.innerHTML=`<span>${t}</span>${l?`<button type="button" class="minibtn${a==='next'||a==='retake'?' pri':''}" data-a="${a}">${l}</button>`:''}`;
 nc.querySelector('.acts').appendChild(li);li.querySelector('button')?.addEventListener('click',()=>act(a))}
function afterType(r,replay){step(4);const N=D.names,top=r.ranked[0][0],sec=r.ranked[1][0],close=r.ranked[0][1]-r.ranked[1][1]<.2;
 (out.querySelector('.card.safety')||out.querySelector('.card.result')).insertAdjacentHTML('afterend','<section class="card" id="nextcard" hidden><div class="kicker">Next steps</div><ul class="acts"></ul></section>');
 qBand(r);
 if(r.status==='bad_photo')addAct('Retake from below with the whole slope in view.','Retake','retake');
 else if(r.status==='uncertain')addAct(r.family?`Answer the questions or tick the signs below to tell <b>${esc(N[top])}</b> from <b>${esc(N[sec])}</b>.`:'Not sure. Answer the questions below, or take a second photo from another spot.','Another photo','retake');
 if(r.status==='bad_photo'||r.status==='uncertain'||close)ask(r,replay);
 ticks(r);reportBar();
 if(!replay){buzz(r.status==='ok'?40:[40,80,40]);say(r.status==='bad_photo'?tr('Very poor photo. Best guess')+' '+tr(N[r.label])+'. '+tr('Please retake the photo.'):(r.status==='uncertain'?tr('Uncertain. Most likely')+' ':'')+tr(N[r.label])+', '+Math.round(r.confidence*100)+' %.')}}
function afterDims(r,replay){const d=r.dimensions;if(!d)return;locLine();const c=findDims();if(c)c.id='dimcard';
 if(!d.available){if(r.status!=='bad_photo')addAct(esc(d.reason||'No size estimate for this photo.'),'','');return}
 const ce=d.cut_edges||[];if(ce.length)addAct(cutMsg(ce),'Retake','retake');
 if(!replay&&!lastDist&&!/object|person|car|calibrat/i.test(d.scale_source||''))addAct('Add the distance to the slope and re-measure: sizes get much tighter ranges.','Add distance','dist');
 if(!replay&&lastDist)addAct(`Measured with your distance of ${lastDist} m.`,'Change','dist');
 if(d.depth_trust==='low')addAct('Sizes are rough here. A person, car or pole near the toe lets the app check its scale.','Scale shot','scale');
 if(d.grains&&!d.grains.reliable&&['debris_flow','fall_topple','earth_mud_flow'].includes(d.label))addAct('Grain size not readable. A close-up of the deposit (5–15 m) gives it.','Close-up','deposit');
 gloss();const m=d.measures&&d.measures[0];if(!replay&&m)say(tr(m.name)+' '+m.value+' '+(m.unit==='m'?tr('metres'):m.unit))}
function cutMsg(e){const how={top:'tilt the phone up or step back so the scarp is inside the frame',bottom:'tilt down or step back so the toe and deposit are inside',left:'turn left or step back',right:'turn right or step back'};
 return `<b>${esc(tr('The landslide runs off the edge of the photo'))}</b> (${e.map(x=>esc(tr(x))).join(', ')}): ${esc(tr('sizes are minimums'))}. ${(s=>s.charAt(0).toUpperCase()+s.slice(1))(e.map(x=>esc(tr(how[x]))).join('; '))}.`}
function act(a){if(a==='retake'){gstate.retakes++;out.innerHTML='';$('#fig').style.display='none';step(1);lastSrc==='cam'?openCamera():galIn.click();return}
 if(a==='dist'){dist.scrollIntoView({behavior:'smooth',block:'center'});dist.focus();$('.pace').open=!dist.value;
  if(!$('#remeasure')){dist.insertAdjacentHTML('afterend','<button type="button" class="minibtn pri u-t2" id="remeasure">Re-measure this photo</button>');
   $('#remeasure').onclick=()=>{const v=distM();if(!v){$('#distmsg').textContent='Type a distance between 1 and 3000 m first.';return}
    $('#remeasure').remove();if(job){findDims()?.scrollIntoView({behavior:'smooth',block:'center'});measure(v)}else if(lastBlob)fullSend(v);else toast('Re-measuring needs the photo: take it again.')}}
  return}
 if(a==='sitereport'){siteReport();return}
 if(a==='newobs'){out.innerHTML='';$('#fig').style.display='none';cur=null;curMeta=null;step(1);A.setChip('','');window.scrollTo({top:0,behavior:'smooth'});return}
 const k={scale:3,deposit:2,next:shot}[a];if(k!=null){if(a!=='next'){mode='survey';store.set('mode','survey')}shot=k;saveShots();drawMode();out.innerHTML='';$('#fig').style.display='none';step(1);openCamera()}}

/* decision questions: Bayes update of the model's probabilities with yes/no field answers; the next question is
   the one with the largest expected information gain. Likelihoods are expert rules of thumb (G.questions). */
function ask(r,replay){let p={};r.ranked.forEach(([c,v])=>p[c]=Math.max(v,1e-4));const Q=G.questions,asked=[],ans=r.answers||[];r.answers=ans;
 const card=document.createElement('section');card.className='card';card.id='askcard';$('#nextcard').after(card);
 const H=o=>-Object.values(o).reduce((s,v)=>s+(v>0?v*Math.log2(v):0),0);
 const upd=(o,q,y)=>{const n={};let z=0;for(const c in o){const L=q.L[c]??.5;n[c]=o[c]*(y?L:1-L);z+=n[c]}for(const c in n)n[c]/=z||1;return n};
 const gain=q=>{const py=Object.keys(p).reduce((s,c)=>s+p[c]*(q.L[c]??.5),0);return H(p)-(py*H(upd(p,q,1))+(1-py)*H(upd(p,q,0)))};
 const pick=()=>{let best=null,bg=0;for(const q of Q){if(asked.includes(q.id))continue;const g=gain(q);if(g>bg){bg=g;best=q}}return bg>=.05?best:null};
 for(const a of ans){const q=Q.find(x=>x.t===a.q);if(q){asked.push(q.id);if(a.a!=='not sure')p=upd(p,q,a.a==='yes')}}
 const draw=()=>{const rk=Object.entries(p).sort((a,b)=>b[1]-a[1]),q=!replay&&asked.length<5&&rk[0][1]<.85?pick():null,moved=ans.some(a=>a.a!=='not sure');
  // nothing to ask and nothing answered: no card (it would only repeat the type list below)
  card.hidden=!q&&!ans.length;if(card.hidden)return;
  card.innerHTML=`<div class="kicker">Help decide: answer what you can see</div>${q?`<h2>${esc(q.t)}</h2>${q.hint?`<p class="hungr u-sub">${esc(q.hint)}</p>`:''}
  <div class="qa"><button type="button" class="minibtn pri" data-y="1">Yes</button><button type="button" class="minibtn pri" data-y="0">No</button><button type="button" class="minibtn" data-y="-">Not sure</button></div>`
  :`<h2>${ans.some(a=>a.a!=='not sure')?esc(tr('Your answers point to'))+' '+esc(tr(D.names[rk[0][0]]))+' ('+Math.round(rk[0][1]*100)+'%)':esc(tr('No further question would change the answer much'))}</h2>`}
  ${moved?`<div class="probs u-t3">${rk.slice(0,3).map(([c,v],k)=>`<div class="prob ${k?'':'top'}">${D.glyphs[c]}<div class="nm">${esc(D.names[c])}<div class="tr"><div class="fl" style="width:${(v*100).toFixed(1)}%"></div></div></div><div class="pc">${Math.round(v*100)}%</div></div>`).join('')}</div>`:''}
  <p class="hungr u-t3">${ans.length?esc(tr('Model result combined with your answers.')):esc(tr('Starts from the model result.'))} ${esc(tr('The answer weights are expert rules of thumb from the Hungr 2014 type descriptions, not trained on data; a geologist has the final word.'))}</p>
  ${ans.length&&!replay?'<button type="button" class="minibtn u-t2" data-y="undo">Undo last answer</button>':''}`;
  card.querySelectorAll('[data-y]').forEach(b=>b.onclick=()=>{const y=b.dataset.y;
   if(y==='undo'){const l=ans.pop();asked.pop();p=l.prev||p;draw();return}
   ans.push({q:q.t,a:y==='1'?'yes':y==='0'?'no':'not sure',prev:p});asked.push(q.id);if(y!=='-')p=upd(p,q,y==='1');r.fieldRanked=Object.entries(p).sort((a,b)=>b[1]-a[1]);draw();buzz(15);
   if(cur&&cur.__id)finish(cur)})};
 draw()}
function tickList(ul,cb,saved){const lis=[...ul.querySelectorAll('li')];lis.forEach((li,i)=>{li.classList.add('tick');li.setAttribute('role','checkbox');li.setAttribute('aria-checked',saved&&saved[i]?'true':'false');li.tabIndex=0;
  const tg=()=>{li.setAttribute('aria-checked',li.getAttribute('aria-checked')==='true'?'false':'true');cb()};li.onclick=tg;li.onkeydown=e=>{if(e.key===' '||e.key==='Enter'){e.preventDefault();tg()}}});return lis}
function ticks(r){const card=$('#checkcard');if(!card)return;const N=D.names,top=r.ranked[0][0],sec=r.ranked[1][0],cmp=r.status==='uncertain'&&sec!=='no_landslide'&&D.info[sec];
 card.querySelector('h2').insertAdjacentHTML('afterend','<p class="hungr u-sub">Tap each sign you can see on site.</p>');
 if(cmp)card.insertAdjacentHTML('beforeend',`<h2 class="u-t4">${esc(D.info[sec].title)} (second choice)</h2><ul class="list" id="ck2">${D.info[sec].check.map(t=>`<li>${ICO('check')}<span>${esc(t)}</span></li>`).join('')}</ul>`);
 card.insertAdjacentHTML('beforeend','<div class="tally" id="tally" aria-live="polite"></div>');
 const ul1=card.querySelector('ul.list'),ul2=$('#ck2'),sv=r.signs||{};let l1=[],l2=[];
 const upd=()=>{const on=l=>l.map(li=>li.getAttribute('aria-checked')==='true'),a=on(l1).filter(Boolean).length,b=on(l2).filter(Boolean).length;
  r.signs={[top]:on(l1),...(cmp?{[sec]:on(l2)}:{})};
  $('#tally').innerHTML=!cmp?`<span>Signs seen:</span> <b>${a} / ${l1.length}</b>${a===0?'':', <span>'+(a>=Math.ceil(l1.length/2)?'The field signs support this type.':'Few signs match: take another photo or ask a geologist.')+'</span>'}`:
  `<div class="cmp"><div class="${a/l1.length>b/l2.length?'lead':''}">${esc(N[top])}<b>${a}/${l1.length}</b></div><div class="${b/l2.length>a/l1.length?'lead':''}">${esc(N[sec])}<b>${b}/${l2.length}</b></div></div><p class="hungr u-t2">The type with the larger share of signs seen is the better field match.</p>`};
 l1=tickList(ul1,()=>{upd();cur&&cur.__id&&finish(cur)},sv[top]);if(ul2)l2=tickList(ul2,()=>{upd();cur&&cur.__id&&finish(cur)},sv[sec]);upd()}
function gloss(){const card=findDims();if(!card||card.querySelector('.what'))return;
 card.insertAdjacentHTML('beforeend',`<details class="what"><summary>What do these numbers mean?</summary><dl class="gloss">${Object.entries(G.glossary).slice(4).map(([k,v])=>`<dt>${esc(k)}</dt><dd>${esc(v)}</dd>`).join('')}</dl></details>`)}

/* ---------- finish: keep the result on the phone, survey bookkeeping, combine the site ---------- */
const strip=d=>{if(!d)return d;const o={...d};delete o.overlay;return o};
let saving=Promise.resolve();
function finish(r){saving=saving.then(()=>finishNow(r)).catch(()=>{});return saving}
async function finishNow(r){const first=!r.__id;if(first){r.__id=Date.now();curPhoto=await photoURL(lastBlob,720)}
 await saveResult(r.__id,r,curMeta||meta(),curPhoto,false,lastBlob);
 if(!first)return;gstate={flags:[],override:false,retakes:0,live:false};
 const sid=(curMeta||{}).shotId;
 if(mode==='survey'&&sid&&r.status!=='bad_photo'){let sv={};try{sv=JSON.parse(sess.get('survey')||'{}')}catch(_){}
  sv[sid]={id:sid,ranked:r.ranked,dimensions:strip(r.dimensions)};sess.set('survey',JSON.stringify(sv));done.add(sid);
  const nx=G.shots.findIndex(s=>!done.has(s.id));if(nx>=0){shot=nx;addAct(`<span>${esc(tr('Survey: next shot'))}</span> <b>${esc(G.shots[nx].t)}</b>. <span>${esc(G.shots[nx].d)}</span>`,'Take it','next')}
  else addAct('Survey complete: all 4 shots taken. The combined site result is above.','Site report','sitereport');
  saveShots();drawMode();if(Object.keys(sv).length>=2)fuse(sv)}}
function fuse(sv){const x=new XMLHttpRequest();x.open('POST','fuse?'+params({}));x.setRequestHeader('Content-Type','application/json');
 x.onload=()=>{if(x.status!==200)return;let s;try{s=JSON.parse(x.responseText)}catch(_){return}sess.set('site',JSON.stringify(s));siteCard(s)};x.send(JSON.stringify({shots:Object.values(sv)}))}
const num=v=>v>=100?Math.round(v).toLocaleString():v;
function siteCard(s){const N=D.names,t=s.type.ranked,d=s.dimensions,old=$('#sitecard');
 let h=`<section class="card" id="sitecard"><div class="kicker">Site result, ${s.n} shots combined</div><h2>${esc(N[t[0][0]])}, ${Math.round(t[0][1]*100)}%</h2>
 <div class="probs">${t.slice(0,3).map(([c,v],k)=>`<div class="prob ${k?'':'top'}">${D.glyphs[c]}<div class="nm">${esc(N[c])}<div class="tr"><div class="fl" style="width:${(v*100).toFixed(1)}%"></div></div></div><div class="pc">${Math.round(v*100)}%</div></div>`).join('')}</div>`;
 if(d&&d.available)h+=d.measures.map(m=>`<div class="drow"><span>${esc(m.name)}</span><b>${num(m.value)} ${m.unit} <small>(90%: ${num(m.range[0])}–${num(m.range[1])})</small></b></div>`).join('')+
  (d.measures.some(m=>m.between_photo_log_sd>.7)?`<p class="note">${esc(tr('The shots disagree strongly on size (more than 2x). Check that they show the same landslide, or retake the whole-slope shot with the distance typed in.'))}</p>`:'')+
  `<p class="hungr u-t2">${esc(tr('Sizes: median of the whole-slope shots, with the spread between photos added to the range.'))} (${s.size_shots.map(k=>esc((G.shots.find(x=>x.id===k)||{}).t||k)).join(', ')})</p>`;
 if(s.grains)h+=`<div class="drow"><span>Grain size D16 / D50 / D84</span><b>${s.grains.D16_m} / ${s.grains.D50_m} / ${s.grains.D84_m} m</b></div>`;
 h+=`<div class="u-t3"><button type="button" class="minibtn pri" data-a="sitereport">Save site report</button></div></section>`;
 const w=document.createElement('div');w.innerHTML=h;const c=w.firstElementChild,first=out.querySelector('.card.result');if(old)old.replaceWith(c);else if(first)first.after(c);else return;c.querySelector('[data-a]').onclick=siteReport}

/* ---------- location: where the photo was taken and, with a compass bearing and a distance, where the landslide is ----------
   camera = EXIF GPS of the original photo (exact place and time of the shot) or else the phone fix nearest the photo.
   landslide = destination point on the sphere: camera + distance (typed, else the model's median depth of the outlined
   area) along the camera bearing. 1-sigma radius = hypot(GPS error, distance x bearing error (compass +-15 deg unless the
   phone reports it), distance error (typed 5 %, model depth 30 %)). */
const R2D=180/Math.PI;
function locOf(mt,r){mt=mt||{};const t0=mt.t||Date.now(),pg=mt.pgps,pp=mt.gps;let cam=null;
 if(pg&&isFinite(pg.lat)&&isFinite(pg.lon))cam={lat:pg.lat,lon:pg.lon,acc:pg.acc||null,alt:isFinite(pg.alt)?pg.alt:null,src:'photo'};
 else if(pp&&isFinite(pp.lat)&&isFinite(pp.lon))cam={lat:pp.lat,lon:pp.lon,acc:pp.acc||null,alt:isFinite(pp.alt)&&pp.alt!==null?pp.alt:null,src:'phone',age:Math.round(Math.abs(t0-(pp.t||t0))/60000)};
 if(!cam)return null;
 const hd=mt.head&&isFinite(mt.head.deg)?mt.head:pg&&isFinite(pg.head)?{deg:pg.head,acc:null,src:'photo'}:null;
 const d=r&&r.dimensions,dist=mt.dist||(d&&d.available&&isFinite(d.distance_m)&&d.distance_m>0?d.distance_m:null);let tgt=null;
 if(hd&&dist>0){const R=6371008.8,dl=dist/R,th=hd.deg/R2D,p1=cam.lat/R2D,l1=cam.lon/R2D;
  const p2=Math.asin(Math.sin(p1)*Math.cos(dl)+Math.cos(p1)*Math.sin(dl)*Math.cos(th)),l2=l1+Math.atan2(Math.sin(th)*Math.sin(dl)*Math.cos(p1),Math.cos(dl)-Math.sin(p1)*Math.sin(p2));
  const sh=(hd.acc>0?hd.acc:15)/R2D,sd=(mt.dist?.05:.3)*dist;
  tgt={lat:p2*R2D,lon:((l2*R2D+540)%360)-180,acc:Math.hypot(cam.acc||10,dist*sh,sd),dist,typed:!!mt.dist}}
 return {cam,head:hd,tgt}}
const dmsOf=(v,p,n)=>{const T=Math.round(Math.abs(v)*36000),d=Math.floor(T/36000),m=Math.floor(T%36000/600),s=(T%600)/10;return `${d}°${String(m).padStart(2,'0')}'${s.toFixed(1).padStart(4,'0')}"${v<0?n:p}`};
const cardOf=h=>['N','NE','E','SE','S','SW','W','NW'][Math.round(h/45)%8];
const osm=p=>`https://www.openstreetmap.org/?mlat=${p.lat.toFixed(6)}&mlon=${p.lon.toFixed(6)}#map=17/${p.lat.toFixed(6)}/${p.lon.toFixed(6)}`;
const ll=p=>`${p.lat.toFixed(6)}, ${p.lon.toFixed(6)}`,pm=a=>a?` ±${Math.round(a)} m`:'';
function locHTML(L){if(!L)return '<p>No location recorded.</p>';const c=L.cam;
 let h=`<table><tr><td>Camera position</td><td><a href="${osm(c)}">${ll(c)}</a>${pm(c.acc)}<br>${dmsOf(c.lat,'N','S')} ${dmsOf(c.lon,'E','W')}${c.alt!=null?`, ${Math.round(c.alt)} m altitude`:''}</td></tr>
 <tr><td>Location source</td><td>${c.src==='photo'?'GPS stored in the photo':'Phone GPS'+(c.age>2?` (${c.age} min from the photo time)`:'')}</td></tr>`;
 if(L.head)h+=`<tr><td>Camera facing</td><td>${Math.round(L.head.deg)}° ${cardOf(L.head.deg)}${L.head.acc?` (±${Math.round(L.head.acc)}°)`:''}</td></tr>`;
 if(L.tgt)h+=`<tr><td>Landslide (estimated)</td><td><a href="${osm(L.tgt)}">${ll(L.tgt)}</a>${pm(L.tgt.acc)}<br>${Math.round(L.tgt.dist)} m along the camera bearing (${L.tgt.typed?'your distance':'model depth'})</td></tr>`;
 return h+'</table>'}
// in the result view: where this photo was taken, with a one-tap fix when there is none
function locLine(){const el=$('#locline');if(!el)return;const L=cur?locOf(curMeta,cur):null;
 if(!L){el.innerHTML=`<span class="lpin"></span><div><span>No location for this photo.</span> <button type="button" class="minibtn" data-a="gps">Add my location</button></div>`;el.querySelector('[data-a=gps]').onclick=askGps;return}
 const c=L.cam;el.innerHTML=`<span class="lpin"></span><div><b>Location</b> <a href="${osm(c)}" target="_blank" rel="noopener">${ll(c)}</a>${pm(c.acc)} <small>(${c.src==='photo'?'photo GPS':'phone GPS'})</small>`+
  (L.tgt?`<br><span>Landslide about</span> <a href="${osm(L.tgt)}" target="_blank" rel="noopener">${ll(L.tgt)}</a>${pm(L.tgt.acc)}`:'')+'</div>'}

/* ---------- image report: the photo with a GPS stamp, a map panel with markers and every result, as one JPEG ---------- */
const loadImg=(src,cors,ms=6000)=>new Promise(res=>{if(!src){res(null);return}const i=new Image();if(cors)i.crossOrigin='anonymous';const t=setTimeout(()=>res(null),ms);
 i.onload=()=>{clearTimeout(t);res(i.naturalWidth?i:null)};i.onerror=()=>{clearTimeout(t);res(null)};i.src=src});
async function blobImg(b){if(!b)return null;let u='';try{u=URL.createObjectURL(b)}catch(_){return null}const i=await loadImg(u);setTimeout(()=>URL.revokeObjectURL(u),2000);return i}
function pin(x,px,py,s,col){x.save();x.translate(px,py);x.beginPath();x.moveTo(0,0);x.bezierCurveTo(-s*.15,-s*.35,-s*.55,-s*.55,-s*.55,-s);x.arc(0,-s,s*.55,Math.PI,0);
 x.bezierCurveTo(s*.55,-s*.55,s*.15,-s*.35,0,0);x.closePath();x.fillStyle=col;x.fill();x.lineWidth=Math.max(2,s*.08);x.strokeStyle='#fff';x.stroke();x.beginPath();x.arc(0,-s,s*.2,0,7);x.fillStyle='#fff';x.fill();x.restore()}
const wpx=(lat,lon,z)=>{const n=256*2**z,s=Math.min(.9999,Math.max(-.9999,Math.sin(lat/R2D)));return [(lon+180)/360*n,(.5-Math.log((1+s)/(1-s))/(4*Math.PI))*n]};
// map panel: OSM tiles when online (all or none, 5 s each), else a plain grid; blue = camera (+ GPS error, view cone), red pin = landslide
async function drawMap(x,X0,Y0,w,h,L,tiles){const c=L.cam,t=L.tgt,mpp=z=>156543.034*Math.cos(c.lat/R2D)/2**z,span=Math.max(t?t.dist+t.acc:0,c.acc||0,40);
 let z=18;while(z>3&&span/mpp(z)>Math.min(w,h)*.4)z--;const m=mpp(z),pc=wpx(c.lat,c.lon,z),pt=t?wpx(t.lat,t.lon,z):pc,ox=(pc[0]+pt[0])/2-w/2,oy=(pc[1]+pt[1])/2-h/2,P=p=>[X0+p[0]-ox,Y0+p[1]-oy];
 x.save();x.beginPath();x.rect(X0,Y0,w,h);x.clip();x.fillStyle='#e9efe9';x.fillRect(X0,Y0,w,h);let used=false;
 if(tiles&&navigator.onLine!==false){const n=2**z,jobs=[];
  for(let tx=Math.floor(ox/256);tx<=Math.floor((ox+w)/256);tx++)for(let ty=Math.floor(oy/256);ty<=Math.floor((oy+h)/256);ty++)if(ty>=0&&ty<n)
   jobs.push(loadImg(`https://tile.openstreetmap.org/${z}/${((tx%n)+n)%n}/${ty}.png`,true,5000).then(i=>[i,tx,ty]));
  const got=await Promise.all(jobs);if(got.length&&got.every(g=>g[0])){got.forEach(([i,tx,ty])=>x.drawImage(i,X0+tx*256-ox,Y0+ty*256-oy,256,256));used=true}}
 if(!used){x.strokeStyle='rgba(31,122,104,.2)';x.lineWidth=1;const g=48;
  for(let gx=X0+((-ox)%g+g)%g;gx<X0+w;gx+=g){x.beginPath();x.moveTo(gx,Y0);x.lineTo(gx,Y0+h);x.stroke()}
  for(let gy=Y0+((-oy)%g+g)%g;gy<Y0+h;gy+=g){x.beginPath();x.moveTo(X0,gy);x.lineTo(X0+w,gy);x.stroke()}}
 const [cx,cy]=P(pc);
 if(c.acc){x.beginPath();x.arc(cx,cy,Math.max(4,c.acc/m),0,7);x.fillStyle='rgba(30,110,220,.15)';x.fill();x.strokeStyle='rgba(30,110,220,.6)';x.lineWidth=2;x.stroke()}
 if(L.head){const a=(L.head.deg-90)/R2D,sp=((L.head.acc>0?L.head.acc:15))/R2D,len=t?Math.hypot(...P(pt).map((v,k)=>v-[cx,cy][k])):70;
  x.beginPath();x.moveTo(cx,cy);x.arc(cx,cy,Math.max(40,len),a-sp,a+sp);x.closePath();x.fillStyle='rgba(30,110,220,.18)';x.fill()}
 if(t){const [tx,ty]=P(pt);x.setLineDash([8,6]);x.beginPath();x.moveTo(cx,cy);x.lineTo(tx,ty);x.strokeStyle='#1e6edc';x.lineWidth=3;x.stroke();x.setLineDash([]);
  x.beginPath();x.arc(tx,ty,Math.max(6,t.acc/m),0,7);x.fillStyle='rgba(217,58,43,.14)';x.fill();x.strokeStyle='rgba(217,58,43,.7)';x.lineWidth=2;x.stroke()}
 x.beginPath();x.arc(cx,cy,10,0,7);x.fillStyle='#1e6edc';x.fill();x.lineWidth=4;x.strokeStyle='#fff';x.stroke();
 const [px,py]=t?P(pt):[cx,cy];pin(x,px,py-(t?0:10),44,'#d93a2b');
 // scale bar and north arrow
 const nice=[5,10,20,50,100,200,500,1000,2000,5000,10000,20000,50000,1e5].filter(v=>v/m<w*.32).pop()||5,bl=nice/m;
 x.fillStyle='rgba(255,255,255,.85)';x.fillRect(X0+10,Y0+h-40,bl+20,30);x.fillStyle='#13201c';x.fillRect(X0+20,Y0+h-18,bl,5);x.font='600 15px system-ui,sans-serif';
 x.fillText(nice>=1000?nice/1000+' km':nice+' m',X0+20,Y0+h-24);
 x.fillStyle='rgba(255,255,255,.85)';x.beginPath();x.arc(X0+w-28,Y0+30,20,0,7);x.fill();x.fillStyle='#13201c';x.beginPath();x.moveTo(X0+w-28,Y0+14);x.lineTo(X0+w-36,Y0+36);x.lineTo(X0+w-20,Y0+36);x.closePath();x.fill();
 x.font='700 13px system-ui,sans-serif';x.fillText('N',X0+w-32,Y0+48);
 if(used){x.font='12px system-ui,sans-serif';const s='© OpenStreetMap contributors',sw=x.measureText(s).width;x.fillStyle='rgba(255,255,255,.85)';x.fillRect(X0+w-sw-12,Y0+h-20,sw+12,20);x.fillStyle='#13201c';x.fillText(s,X0+w-sw-6,Y0+h-6)}
 x.restore();x.strokeStyle='#c9d4cf';x.lineWidth=2;x.strokeRect(X0,Y0,w,h);return used}
function wrapT(x,s,X,Y,maxW,lh){const words=String(s??'').split(/\s+/);let line='',y=Y;
 for(const w of words){const t=line?line+' '+w:w;if(x.measureText(t).width>maxW&&line){x.fillText(line,X,y);y+=lh;line=w}else line=t}
 if(line){x.fillText(line,X,y);y+=lh}return y}
const STW={ok:'Confident',uncertain:'Uncertain',bad_photo:'Not reliable'};
async function reportImage(r,mt,photo,blob,tiles){
 /* A landscape sheet (about 8:7 instead of a 1:2.5 strip): header across the top, then two columns. The photo and the
    size table go left, the answer and the map go right; photo quality and field notes go to whichever column is
    shorter, so the two columns end level. Every phrase is drawn on one line: it shrinks a little to fit and, only
    as a last resort, ends in an ellipsis (the web page report keeps the full text). */
 const W=1600,M=44,G=36,N=D.names,d=r.dimensions,L=locOf(mt,r),T=s=>tr(s),miss=[],when=new Date(mt.t||Date.now()).toLocaleString();
 const cv=document.createElement('canvas');cv.width=W;cv.height=4000;const x=cv.getContext('2d');if(!x)throw new Error('no canvas');
 const F=(sz,wt=400)=>`${wt} ${sz}px ${wt>=600?'"Palatino Linotype","Book Antiqua",Palatino,"Noto Serif",Georgia,':''}system-ui,-apple-system,"Segoe UI",Roboto,"Noto Sans","Noto Sans Devanagari","Nirmala UI",sans-serif`,
  ink='#15242a',ink2='#3a4c50',line='#c9d3cb',teal='#17695a';
 // one line, never wrapped: shrink to 72 % of the size, then cut with an ellipsis; align 'l' | 'r'
 const one=(s,X,Y,maxW,sz,wt=400,col=ink,al='l')=>{s=String(s??'');let z=sz;x.font=F(z,wt);
  while(x.measureText(s).width>maxW&&z>Math.max(13,sz*.72)){z--;x.font=F(z,wt)}
  if(x.measureText(s).width>maxW){while(s.length>1&&x.measureText(s+'…').width>maxW)s=s.slice(0,-1);s=s.trimEnd()+'…'}
  x.fillStyle=col;x.fillText(s,al==='r'?X+maxW-x.measureText(s).width:X,Y);return z};
 x.fillStyle='#fff';x.fillRect(0,0,W,cv.height);
 // header: title left, time / shot / set right, one line each
 x.fillStyle='#13463b';x.fillRect(0,0,W,96);one(T('Landslide observation'),M,62,W/2-M,40,700,'#fff');
 one([when,mt.shot?T(mt.shot):'',mt.set||''].filter(Boolean).join(', '),W/2,60,W/2-M,24,400,'#cfe5dd','r');
 const LW=900,RX=M+LW+G,cols={l:{x:M,w:LW,y:128},r:{x:RX,w:W-M-RX,y:128}};
 const sec=(c,t)=>{c.y+=10;one(T(t),c.x,c.y+28,c.w,28,700,teal);c.y+=40;x.fillStyle=line;x.fillRect(c.x,c.y,c.w,2);x.fillStyle=ink;x.fillRect(c.x,c.y-1,44,4);c.y+=14};
 const part=(c,name,f)=>{const y0=c.y;try{f(c)}catch(e){x.fillStyle='#fff';x.fillRect(c.x-2,y0,c.w+4,Math.max(0,c.y-y0)+60);c.y=y0;miss.push(name)}};
 const kv=(c,k,v,col)=>{const kw=Math.round(c.w*.37);one(T(k)+':',c.x,c.y+24,kw,19,600,ink2);one(v,c.x+kw+4,c.y+24,c.w-kw-4,20,400,col||ink);c.y+=32};
 // LEFT 1: the photo (with the measured outline when there is one) and its GPS stamp
 const im=(d&&d.available&&d.overlay?await loadImg(d.overlay):null)||await blobImg(blob)||await loadImg(photo);
 {const c=cols.l;if(im){const s=Math.min(c.w/im.naturalWidth,640/im.naturalHeight),w=Math.round(im.naturalWidth*s),h=Math.round(im.naturalHeight*s),X=c.x,y=c.y;
   x.drawImage(im,X,y,w,h);const sh=L?(L.tgt?104:76):46;x.fillStyle='rgba(0,0,0,.64)';x.fillRect(X,y+h-sh,w,sh);
   if(L){const k=L.cam;pin(x,X+32,y+h-sh/2+18,30,'#d93a2b');
    one(`${dmsOf(k.lat,'N','S')}  ${dmsOf(k.lon,'E','W')}${pm(k.acc)}`,X+62,y+h-sh+32,w-80,24,700,'#fff');
    one(`${ll(k)}${k.alt!=null?', '+Math.round(k.alt)+' m':''}${L.head?', '+T('facing')+' '+Math.round(L.head.deg)+'° '+cardOf(L.head.deg):''}, ${when}`,X+62,y+h-sh+60,w-80,19,400,'#e6efeb');
    if(L.tgt)one(`${T('Landslide about')} ${ll(L.tgt)}${pm(L.tgt.acc)}`,X+62,y+h-sh+90,w-80,19,400,'#ffd7d2')}
   else one(T('No location recorded')+', '+when,X+16,y+h-16,w-32,20,400,'#fff');
   c.y+=h+8;if(d&&d.available&&d.overlay){one(T('Outlined area = the measured landslide'),c.x,c.y+18,c.w,18,400,ink2);c.y+=26}}
  else miss.push('photo')}
 // LEFT 2: sizes, one row per measure (name | value | 90 % range)
 part(cols.l,'sizes',c=>{if(!d)return;sec(c,'Estimated dimensions');
  if(!d.available){one(d.reason||T('No size estimate for this photo.'),c.x,c.y+22,c.w,20,400,ink2);c.y+=34;return}
  const C=[c.x,c.x+c.w*.52,c.x+c.w*.74],cw=[c.w*.5,c.w*.21,c.w*.26];
  const row=(a,b,e,head)=>{const wt=head?600:400,cl=head?ink2:ink;one(a,C[0],c.y+24,cw[0],head?18:20,wt,cl);one(b,C[1],c.y+24,cw[1],head?18:20,head?600:700,cl);if(e)one(e,C[2],c.y+24,cw[2],head?18:19,wt,head?ink2:'#3a4c50');c.y+=36;x.fillStyle=line;x.fillRect(c.x,c.y-5,c.w,1)};
  row(T('Measure'),T('Value'),T('90% range'),true);
  for(const m of d.measures||[])row(T(m.name),`${num(m.value)} ${m.unit}`,m.range?`${num(m.range[0])} – ${num(m.range[1])}`:'');
  if(d.size_class)row(T('Size class'),T(d.size_class),'');if(d.slope_angle_deg!=null)row(T('Slope angle'),d.slope_angle_deg+'°','');
  if(d.distance_m)row(T('Distance to the slope'),(mt.dist||d.distance_m)+' m',mt.dist?T('your distance'):T('model depth'));
  if(d.grains&&d.grains.reliable)row(T('Grain size D16 / D50 / D84'),`${d.grains.D16_m} / ${d.grains.D50_m} / ${d.grains.D84_m} m`,'');
  c.y+=4;one(`${T('Scale')}: ${d.scale_source||''}`,c.x,c.y+20,c.w,17,400,ink2);c.y+=26;
  one(`${T('Depth trust')}: ${T(d.depth_trust||'')}${(d.cut_edges||[]).length?', '+T('sizes are minimums')+' ('+d.cut_edges.map(T).join(', ')+')':''}`,c.x,c.y+20,c.w,17,400,ink2);c.y+=30});
 // RIGHT 1: the answer
 part(cols.r,'type',c=>{sec(c,'Landslide type');one(T(N[r.label]||r.label),c.x,c.y+38,c.w,38,700,ink);c.y+=52;
  one(`${Math.round((r.confidence||0)*100)}%, ${T(STW[r.status]||r.status)}${r.family?', '+T(r.family)+' '+T('family'):''}`,c.x,c.y+22,c.w,22,600,r.status==='ok'?teal:r.status==='uncertain'?'#8a5d00':'#b8381f');c.y+=36;
  const nw=Math.round(c.w*.44),bx=c.x+nw+12,bw=c.w-nw-12-62;
  for(const [k,p] of (r.ranked||[]).slice(0,3)){one(T(N[k]||k),c.x,c.y+20,nw,19,400,ink);x.fillStyle='#e3ebe7';x.fillRect(bx,c.y+6,bw,16);
   x.fillStyle=teal;x.fillRect(bx,c.y+6,bw*Math.max(0,Math.min(1,p)),16);one(Math.round(p*100)+'%',c.x+c.w-56,c.y+21,56,19,600,ink,'r');c.y+=32}
  if(r.fieldRanked&&r.answers&&r.answers.some(a=>a.a!=='not sure')){one(`${T('With your field answers')}: ${T(N[r.fieldRanked[0][0]])} ${Math.round(r.fieldRanked[0][1]*100)}%`,c.x,c.y+22,c.w,20,600,ink);c.y+=34}});
 // RIGHT 2: location map and coordinates
 {const c=cols.r;sec(c,'Location');
  if(L){const mh=Math.round(c.w*.56);let used=false;try{used=await drawMap(x,c.x,c.y,c.w,mh,L,tiles)}catch(e){miss.push('map')}c.y+=mh+10;
   const k=L.cam;kv(c,'Camera position',`${dmsOf(k.lat,'N','S')} ${dmsOf(k.lon,'E','W')}`,'#1e6edc');kv(c,'Decimal',ll(k)+pm(k.acc)+(k.alt!=null?', '+Math.round(k.alt)+' m':''),'#1e6edc');
   kv(c,'Location source',k.src==='photo'?T('GPS stored in the photo'):T('Phone GPS')+(k.age>2?` (${k.age} min)`:''));
   if(L.head)kv(c,'Camera facing',`${Math.round(L.head.deg)}° ${cardOf(L.head.deg)}${L.head.acc?' ±'+Math.round(L.head.acc)+'°':''}`);
   if(L.tgt){kv(c,'Landslide (estimated)',ll(L.tgt)+pm(L.tgt.acc),'#d93a2b');kv(c,'From the camera',`${Math.round(L.tgt.dist)} m ${T('along the camera bearing')} (${T(L.tgt.typed?'your distance':'model depth')})`)}
   else kv(c,'Landslide (estimated)',T('needs a compass bearing and a distance'));
   if(used)mt.__tiles=true}
  else{one(T('No location recorded'),c.x,c.y+22,c.w,20,600,ink2);c.y+=30;one(T('Tap Add my location (needs https) or use a photo with GPS.'),c.x,c.y+20,c.w,18,400,ink2);c.y+=30}}
 // flexible blocks go to the shorter column
 const low=()=>cols.l.y<=cols.r.y?cols.l:cols.r;
 part(low(),'quality',c=>{const ql=qLevel(r);sec(c,'Photo quality');one(T(QL[ql]),c.x,c.y+22,c.w,22,700,['#17695a','#7a5c00','#9a4a00','#b8381f'][ql]);c.y+=32;
  const iss=(r.quality&&r.quality.issues||[]).map(i=>T(i[0])+(i[2]===2?' ('+T('serious')+')':''));if(r.status==='bad_photo')iss.unshift(T('photo check failed: the result is not reliable'));
  for(const s of iss){one(s,c.x,c.y+20,c.w,19,400,ink2);c.y+=28}});
 part(low(),'field',c=>{const ans=r.answers||[],sg=r.signs||{};if(!ans.length&&!Object.keys(sg).length&&!mt.notes&&!mt.weather)return;sec(c,'Field check');
  for(const a of ans){one(`${T(a.q)}${/[?:]$/.test(T(a.q))?' ':': '}${T(a.a)}`,c.x,c.y+20,c.w,19,400,ink);c.y+=28}
  for(const [k,v] of Object.entries(sg)){one(`${T('Signs seen:')} ${v.filter(Boolean).length} / ${v.length} (${T(N[k]||k)})`,c.x,c.y+20,c.w,19,400,ink);c.y+=28}
  if(mt.weather){one(`${T('Weather')}: ${T(mt.weather)}`,c.x,c.y+20,c.w,19,400,ink);c.y+=28}
  if(mt.notes){one(`${T('Notes')}: ${String(mt.notes).replace(/\s+/g,' ')}`,c.x,c.y+20,c.w,19,400,ink);c.y+=28}});
 // footer across both columns: responsibility on one line, provenance on the next
 let y=Math.max(cols.l.y,cols.r.y)+18;x.fillStyle=line;x.fillRect(M,y,W-2*M,2);y+=8;
 one(T('Decision support only: confirm with a geologist or geotechnical engineer before acting.'),M,y+24,W-2*M,18,600,ink2);y+=30;
 one([r.model?T('Model')+': '+r.model:'','WGS-84',mt.__tiles?'Map © OpenStreetMap contributors':'',miss.length?'not drawn: '+miss.join(', '):''].filter(Boolean).join(', '),M,y+22,W-2*M,16,400,ink2);y+=32;
 const tiled=!!mt.__tiles;delete mt.__tiles;
 const o=document.createElement('canvas');o.width=W;o.height=Math.ceil(y+12);const ox=o.getContext('2d');ox.drawImage(cv,0,0);
 const jb=await new Promise((res,rej)=>{try{o.toBlob(b=>b?res(b):rej(new Error('toBlob')),'image/jpeg',.9)}catch(e){rej(e)}});   // a tainted canvas throws here
 const desc=`Landslide observation: ${N[r.label]||r.label} ${Math.round((r.confidence||0)*100)}% (${r.status})`+(L?` at ${ll(L.cam)}`:'')+(L&&L.tgt?`; landslide about ${ll(L.tgt)}`:'');
 return {blob:await withExif(jb,exifOf(L,mt.t||Date.now(),desc)),tiles:tiled,miss}}

/* EXIF for the saved JPEG (little-endian TIFF): description, software, time and, with a location, a GPS IFD with the
   camera position, altitude, bearing (magnetic, 'M') and horizontal error, so photo apps and GIS place it on a map */
function exifOf(L,t,desc){const enc=s=>{s=String(s).slice(0,240);const a=new Uint8Array(s.length+1);for(let i=0;i<s.length;i++){const c=s.charCodeAt(i);a[i]=c>=32&&c<127?c:63}return a};
 const rat=v=>{const b=new Uint8Array(8*v.length),dv=new DataView(b.buffer);v.forEach(([n,dn],i)=>{dv.setUint32(8*i,Math.max(0,Math.min(4294967295,Math.round(n))),true);dv.setUint32(8*i+4,dn,true)});return b};
 const dmsR=v=>{const a=Math.abs(v),dd=Math.floor(a),mm=Math.floor((a-dd)*60),ss=((a-dd)*60-mm)*60;return rat([[dd,1],[mm,1],[ss*1e4,1e4]])};
 const dt=new Date(t),p2=n=>String(n).padStart(2,'0'),ptr=new Uint8Array(4);
 const E=[[0x010E,2,enc(desc)],[0x0131,2,enc('Landslide Type Check field app')],[0x0132,2,enc(`${dt.getFullYear()}:${p2(dt.getMonth()+1)}:${p2(dt.getDate())} ${p2(dt.getHours())}:${p2(dt.getMinutes())}:${p2(dt.getSeconds())}`)]],G=[];
 if(L){const c=L.cam;E.push([0x8825,4,ptr]);
  G.push([0,1,new Uint8Array([2,3,0,0])],[1,2,enc(c.lat<0?'S':'N')],[2,5,dmsR(c.lat)],[3,2,enc(c.lon<0?'W':'E')],[4,5,dmsR(c.lon)],[0x12,2,enc('WGS-84')]);
  if(c.alt!=null&&isFinite(c.alt))G.push([5,1,new Uint8Array([c.alt<0?1:0])],[6,5,rat([[Math.abs(c.alt)*100,100]])]);
  if(L.head)G.push([0x10,2,enc('M')],[0x11,5,rat([[L.head.deg*100,100]])]);
  if(c.acc)G.push([0x1F,5,rat([[c.acc*100,100]])])}
 const ifds=G.length?[E,G]:[E],cnt=e=>e[1]===5?e[2].length/8:e[1]===4?e[2].length/4:e[2].length,ext=e=>e[2].length>4?e[2].length+(e[2].length&1):0;
 ifds.forEach(f=>f.sort((a,b)=>a[0]-b[0]));const offs=[];let o=8;for(const f of ifds){offs.push(o);o+=2+12*f.length+4+f.reduce((s,e)=>s+ext(e),0)}
 if(G.length)new DataView(ptr.buffer).setUint32(0,offs[1],true);
 const buf=new Uint8Array(o),dv=new DataView(buf.buffer);buf.set([0x49,0x49,42,0]);dv.setUint32(4,8,true);
 ifds.forEach((f,k)=>{const p=offs[k];let q2=p+2+12*f.length+4;dv.setUint16(p,f.length,true);
  f.forEach((e,i)=>{const q=p+2+12*i;dv.setUint16(q,e[0],true);dv.setUint16(q+2,e[1],true);dv.setUint32(q+4,cnt(e),true);
   if(e[2].length<=4)buf.set(e[2],q+8);else{dv.setUint32(q+8,q2,true);buf.set(e[2],q2);q2+=ext(e)}});dv.setUint32(p+2+12*f.length,0,true)});
 return buf}
async function withExif(blob,tiff){try{const a=new Uint8Array(await blob.arrayBuffer());if(a[0]!==0xFF||a[1]!==0xD8||tiff.length>65000)return blob;
 let p=2;if(a[2]===0xFF&&a[3]===0xE0)p=4+((a[4]<<8)|a[5]);const L=8+tiff.length,hd=new Uint8Array([0xFF,0xE1,L>>8,L&255,0x45,0x78,0x69,0x66,0,0]);
 return new Blob([a.slice(0,p),hd,tiff,a.slice(p)],{type:'image/jpeg'})}catch(_){return blob}}

/* ---------- saving that works on every phone browser: download link -> share sheet -> open in a tab, and the image is
   also shown on the page (long-press to save) so a blocked download never loses the report ---------- */
function saveBlob(blob,name){try{const u=URL.createObjectURL(blob),a=document.createElement('a');a.href=u;a.download=name;a.rel='noopener';a.style.display='none';
 document.body.appendChild(a);a.click();setTimeout(()=>{URL.revokeObjectURL(u);a.remove()},120000);return true}catch(_){return false}}
async function shareBlob(blob,name,text){try{const f=new File([blob],name,{type:blob.type});if(navigator.canShare&&navigator.canShare({files:[f]})){await navigator.share({files:[f],text:text||''});return true}}
 catch(e){if(e&&e.name==='AbortError')return true}return false}
function openBlob(blob){try{return !!window.open(URL.createObjectURL(blob),'_blank')}catch(_){return false}}
function reportBar(){$('#repsec')?.remove();
 const c=document.createElement('section');c.className='card';c.id='repsec';
 c.innerHTML=`<h2>Save and share</h2><p class="hungr u-b3">One image with the photo, the location marker and every result. It also opens offline.</p><div class="locl u-b3" id="locline"></div>
 <div class="btns" id="repbar"><button type="button" class="btn primary span2" data-a="img">Save report</button><button type="button" class="btn ghost" data-a="share">Share</button><button type="button" class="btn ghost" data-a="report">Save as web page</button></div>`;
 const m=out.querySelector('.meta');m?out.insertBefore(c,m):out.appendChild(c);
 c.querySelector('#repbar').onclick=e=>{const a=e.target.closest('[data-a]')?.dataset.a;if(a==='img')saveImageReport();if(a==='report')saveReport();if(a==='share')share()};locLine()}
let repBusy=false;
async function saveImageReport(){if(!cur||repBusy)return;repBusy=true;const btn=$('#repbar [data-a=img]'),bt=btn?btn.innerHTML:'';
 if(btn){btn.disabled=true;btn.setAttribute('aria-busy','true');btn.innerHTML='<span class="spin"></span>'+esc(tr('Making the image report…'))}
 const r=cur,mt=curMeta||meta();let res=null;
 for(const tiles of [true,false]){try{res=await reportImage(r,mt,curPhoto,lastBlob,tiles);break}catch(_){res=null}}   // retry without map tiles (offline, blocked, tainted)
 repBusy=false;if(btn){btn.disabled=false;btn.removeAttribute('aria-busy');btn.innerHTML=bt}
 if(!res){toast(tr('The image report could not be drawn on this phone: the page report is saved instead.'));saveReport();return null}
 const name=fname('observation',mt.t,'jpg');const ok=saveBlob(res.blob,name);repShow(res.blob,name,res.tiles,ok);
 if(ok){toast(tr('Report saved')+': '+name);step(5);buzz(30)}return res}
function repShow(blob,name,tiles,ok){$('#repcard')?.remove();let u='';try{u=URL.createObjectURL(blob)}catch(_){}
 const c=document.createElement('div');c.id='repcard';c.className='u-t4';
 c.innerHTML=`<p class="done-line" role="status"><b>${ok?esc(tr('Report saved')):esc(tr('Image report'))}</b> <span class="hungr">${esc(name)}</span></p>${u?`<img class="dimg" src="${u}" alt="Image report with location and results">`:''}<p class="hungr u-b3"><span>If no file was downloaded, long-press the image to save it, or use Share.</span>${tiles?' <span>Map © OpenStreetMap contributors.</span>':''}</p>
 <div class="btns"><button type="button" class="btn ghost" data-a="sh">Share image</button><button type="button" class="btn ghost" data-a="dl">Save again</button><button type="button" class="btn primary span2" data-a="new">Start the next observation</button></div>`;
 const sec=$('#repsec');sec?sec.appendChild(c):out.appendChild(c);
 c.onclick=async e=>{const a=e.target.closest('[data-a]')?.dataset.a;
  if(a==='new'){act('newobs');return}
  if(a==='dl'&&!saveBlob(blob,name)&&!openBlob(blob))toast(tr('Could not save the report on this browser.'));
  if(a==='sh'&&!(await shareBlob(blob,name,shareText()))&&!openBlob(blob))toast(tr('Sharing is not available here: use Save report.'))}}

/* ---------- page report: a standalone HTML page (opens anywhere, prints to PDF) and a short shareable text ---------- */
const RCSS='body{font:15px/1.5 system-ui,sans-serif;max-width:780px;margin:24px auto;padding:0 16px;color:#13201c}h1{font-size:1.35rem}h2{font-size:1.05rem;margin-top:22px}table{border-collapse:collapse;width:100%}td,th{border-bottom:1px solid #ddd;padding:6px;text-align:left;vertical-align:top}img{max-width:100%;border-radius:8px;margin:8px 0}.m{color:#5c6b65;font-size:.9rem}';
function metaHTML(mt){mt=mt||{};const g=mt.gps&&isFinite(mt.gps.lat)?mt.gps:null;return `<p class="m">${new Date(mt.t||Date.now()).toLocaleString()}${g?`, <a href="${osm(g)}">${g.lat.toFixed(5)}, ${g.lon.toFixed(5)}</a>${pm(g.acc)}`:''}${mt.weather?', '+esc(mt.weather):''}${mt.shot?', '+esc(mt.shot):''}${mt.set?', '+esc(mt.set):''}${mt.dist?', distance '+esc(mt.dist)+' m':''}</p>${mt.notes?`<p><b>Notes:</b> ${esc(mt.notes)}</p>`:''}`}
// every section is written on its own: a missing or odd field costs that section, never the whole report
const partH=(name,f)=>{try{return f()}catch(e){return `<p class="m">(${esc(name)}: this part could not be written)</p>`}};
function resultHTML(r,photo,mt){const N=D.names,d=r.dimensions;let h=photo?`<img src="${photo}" alt="photo">`:'';
 h+=partH('location',()=>`<h2>Location</h2>${locHTML(locOf(mt,r))}`);
 h+=partH('photo quality',()=>{const ql=qLevel(r);return `<h2>Photo quality</h2><p><b>${QL[ql]}</b>${r.quality&&r.quality.issues&&r.quality.issues.length?': '+r.quality.issues.map(x=>esc(x[0])+(x[2]===2?' (serious)':'')).join(', '):''}${r.status==='bad_photo'?', photo check failed: the result is not reliable':''}</p>`});
 h+=partH('type',()=>`<h2>Type</h2><p><b>${esc(N[r.label]||r.label)}</b>, ${Math.round((r.confidence||0)*100)}% (${esc(r.status)}${r.family?', '+esc(r.family)+' family':''})</p><table>${(r.ranked||[]).map(([c,p])=>`<tr><td>${esc(N[c]||c)}</td><td>${Math.round(p*100)}%</td></tr>`).join('')}</table>`);
 if(r.answers&&r.answers.length)h+=partH('field questions',()=>`<h2>Field questions</h2><table>${r.answers.map(a=>`<tr><td>${esc(a.q)}</td><td>${esc(a.a)}</td></tr>`).join('')}</table>${r.fieldRanked?`<p>With these answers: <b>${esc(N[r.fieldRanked[0][0]])}</b> ${Math.round(r.fieldRanked[0][1]*100)}%</p>`:''}`);
 if(r.signs)h+=partH('signs',()=>`<h2>Signs checked on site</h2><table>${Object.entries(r.signs).map(([c,v])=>v.map((on,i)=>`<tr><td>${esc(((D.info[c]||{}).check||[])[i]||'sign '+(i+1))}</td><td>${on?'seen':'not seen'}</td></tr>`).join('')).join('')}</table>`);
 if(d&&d.available)h+=partH('dimensions',()=>`<h2>Estimated dimensions</h2>${d.overlay?`<img src="${d.overlay}" alt="measured outline">`:''}<table><tr><th>Measure</th><th>Value</th><th>90% range</th></tr>${(d.measures||[]).map(m=>`<tr><td>${esc(m.name)}</td><td>${esc(num(m.value))} ${esc(m.unit)}</td><td>${m.range?esc(num(m.range[0]))+' – '+esc(num(m.range[1])):''}</td></tr>`).join('')}
  ${d.size_class?`<tr><td>Size class (Fell 1994)</td><td colspan="2">${esc(d.size_class)}</td></tr>`:''}${d.slope_angle_deg!=null?`<tr><td>Slope angle</td><td colspan="2">${esc(d.slope_angle_deg)}°</td></tr>`:''}${d.distance_m?`<tr><td>Distance to the slope</td><td colspan="2">${esc(d.distance_m)} m</td></tr>`:''}${d.grains&&d.grains.reliable?`<tr><td>Grain size D16 / D50 / D84</td><td colspan="2">${esc(d.grains.D16_m)} / ${esc(d.grains.D50_m)} / ${esc(d.grains.D84_m)} m</td></tr>`:''}</table>
  <p class="m">Scale: ${esc(d.scale_source)}. Depth trust: ${esc(d.depth_trust)}. ${esc([...(d.notes||[]),...((d.cut_edges||[]).length?['Runs off the '+d.cut_edges.join(', ')+' edge of the photo.']:[])].join(' '))}</p>`);
 else if(d&&d.reason)h+=`<h2>Estimated dimensions</h2><p>${esc(d.reason)}</p>`;
 return h}
const foot=m=>`<p class="m">Landslide Type Check field app${m?' ('+esc(m)+')':''}. Decision support only: confirm with a geologist or geotechnical engineer before acting. Coordinates WGS-84.</p>`;
function download(name,html){const b=new Blob([html],{type:'text/html'});if(saveBlob(b,name)){toast(tr('Report saved')+': '+name);if(cur)step(5)}else if(!openBlob(b))toast(tr('Could not save the report on this browser.'))}
const fname=(k,t,ext='html')=>`landslide_${k}_${new Date(t||Date.now()).toISOString().slice(0,16).replace(/[:T]/g,'-')}.${ext}`;
const page=(title,body)=>`<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>${title}</title><style>${RCSS}</style></head><body>${body}</body></html>`;
function saveReport(){if(!cur)return;const mt=curMeta||meta();
 download(fname('observation',mt.t),page('Landslide observation',`<h1>Landslide observation</h1>${metaHTML(mt)}${resultHTML(cur,curPhoto,mt)}${foot(cur.model)}`))}
async function siteReport(){let s=null;try{s=JSON.parse(sess.get('site')||'null')}catch(_){}const hs=store.get('hist',[]),N=D.names,mt=meta();
 const ids=hs.filter(o=>o.site===siteId()).map(o=>o.id),rs=(await Promise.all(ids.map(id=>safe(()=>DB.get('results',id),null)))).filter(Boolean).reverse();
 let h=`<h1>Landslide site survey</h1>${metaHTML(mt)}`;
 if(s)h+=partH('site result',()=>{const t=s.type.ranked,d=s.dimensions;let q=`<h2>Site result (${s.n} shots combined)</h2><p><b>${esc(N[t[0][0]])}</b>, ${Math.round(t[0][1]*100)}%</p>`;
  if(d&&d.available)q+=`<table><tr><th>Measure</th><th>Value</th><th>90% range</th></tr>${d.measures.map(m=>`<tr><td>${esc(m.name)}</td><td>${esc(num(m.value))} ${esc(m.unit)}</td><td>${esc(num(m.range[0]))} – ${esc(num(m.range[1]))}</td></tr>`).join('')}</table><p class="m">Median of the whole-slope shots; the spread between photos is added to the range.</p>`;
  if(s.grains)q+=`<p>Grain size D16 / D50 / D84: ${esc(s.grains.D16_m)} / ${esc(s.grains.D50_m)} / ${esc(s.grains.D84_m)} m</p>`;return q});
 for(const x of rs)h+=partH('photo',()=>`<hr><h2>${esc(x.meta&&x.meta.shot||'Photo')}</h2>${metaHTML(x.meta)}${resultHTML(x.r,x.photo,x.meta)}`);
 download(fname('site',mt.t),page('Landslide site survey',h+foot('')))}
function shareText(){const r=cur,mt=curMeta||meta(),N=D.names,d=r.dimensions,L=locOf(mt,r);
 return [`Landslide observation, ${new Date(mt.t||Date.now()).toLocaleString()}`,`${N[r.label]||r.label} (${Math.round((r.confidence||0)*100)}%, ${r.status})`,`Photo quality: ${QL[qLevel(r)]}${r.status==='bad_photo'?' (not reliable)':''}`,
  ...(d&&d.available?(d.measures||[]).slice(0,4).map(m=>`${m.name}: ${num(m.value)} ${m.unit} (90%: ${num(m.range[0])}-${num(m.range[1])})`):[]),
  L?`Camera position: ${ll(L.cam)}${pm(L.cam.acc)} ${osm(L.cam)}`:'',L&&L.tgt?`Landslide about: ${ll(L.tgt)}${pm(L.tgt.acc)} ${osm(L.tgt)}`:'',
  mt.weather?'Weather: '+mt.weather:'',mt.notes?'Notes: '+mt.notes:'','Decision support only; confirm with a geologist.'].filter(Boolean).join('\n')}
async function share(){if(!cur)return;const txt=shareText();
 try{const f=lastBlob?new File([lastBlob],'landslide.jpg',{type:'image/jpeg'}):null;
  if(f&&navigator.canShare&&navigator.canShare({files:[f]}))await navigator.share({text:txt,files:[f]});else if(navigator.share)await navigator.share({text:txt});
  else{await navigator.clipboard.writeText(txt);toast('Summary copied: paste it into a message or e-mail.')}}catch(e){if(e&&e.name!=='AbortError')toast('Sharing is not available here: use Save report.')}}
A._rep={locOf,reportImage,exifOf,withExif,dmsOf,resultHTML,saveImageReport,setGps:p=>setGps(p)};   // exposed for tests

/* ---------- offline queue: photos wait on the phone and are sent when the connection is back ---------- */
async function queueIt(){const it={id:Date.now(),blob:lastBlob,q:params({stage:'full',d:lastDist,g:gArg(),f35:lastF35,gx:gx()}).toString(),meta:curMeta||meta(),photo:await photoURL(lastBlob,720),site:siteId()};
 const ok=await safe(async()=>{await DB.put('queue',it);return true},false);
 A.setChip('signal',ok?'Saved for later':'Offline');step(1);
 out.innerHTML=`<section class="card bad" aria-live="polite"><div class="kicker">No connection</div><h2>${ok?'Saved on the phone: it will be analysed automatically when the connection is back':'You are offline and this browser cannot store the photo'}</h2>
 <p class="hungr u-m0">${ok?'Keep the app open or open it again later. You can keep photographing; each photo waits in the queue.':'Reconnect to the laptop or server and tap Try again.'}</p></section>`;
 if(ok&&mode==='survey'&&it.meta.shotId){done.add(it.meta.shotId);const nx=G.shots.findIndex(s=>!done.has(s.id));if(nx>=0)shot=nx;saveShots();drawMode()}
 gstate={flags:[],override:false,retakes:0,live:false};netUI()}
let flushing=false;
async function flush(){if(flushing||!navigator.onLine)return;const q=await safe(()=>DB.all('queue'),[]);if(!q.length){netUI();return}flushing=true;netUI();
 for(const it of q.sort((a,b)=>a.id-b.id)){try{const res=await fetch('predict?'+it.q,{method:'POST',body:it.blob,headers:{'Content-Type':it.blob.type||'application/octet-stream'}});
   if(res.status>=500)break;const r=await res.json().catch(()=>null);
   if(res.ok&&r){r.__id=it.id;await saveResult(it.id,r,it.meta,it.photo,true,it.blob,it.site);
    if(it.meta.mode==='survey'&&it.meta.shotId&&r.status!=='bad_photo'&&it.site===siteId()){let sv={};try{sv=JSON.parse(sess.get('survey')||'{}')}catch(_){}sv[it.meta.shotId]={id:it.meta.shotId,ranked:r.ranked,dimensions:strip(r.dimensions)};sess.set('survey',JSON.stringify(sv));if(Object.keys(sv).length>=2)fuse(sv)}
    toast(tr('A saved photo was analysed')+': '+(r.status==='bad_photo'?tr('retake needed'):tr(D.names[r.label]))+'. '+tr('See Recent observations.'))}
   await DB.del('queue',it.id)}catch(_){break}}
 flushing=false;netUI()}
const nb=$('#netbar');
async function netUI(){const n=(await safe(()=>DB.all('queue'),[])).length;nb.hidden=navigator.onLine&&!n;nb.classList.toggle('sync',navigator.onLine);
 nb.textContent=navigator.onLine?(n?`Sending ${n} saved photo(s)…`:''):(n?`You are offline. ${n} photo(s) waiting to be sent.`:'You are offline. New photos will be saved and sent later.')}
window.addEventListener('online',()=>{netUI();flush()});window.addEventListener('offline',netUI);netUI();setTimeout(flush,1500);setInterval(flush,60000);

/* ---------- history: every result is kept on this phone (last 20) and can be reopened ---------- */
function siteId(){let s=sess.get('siteId');if(!s){s=String(Date.now());sess.set('siteId',s)}return s}
async function saveResult(id,r,mt,photo,queued,blob,site){await safe(()=>DB.put('results',{id,r,meta:mt,photo,blob}));
 const d=r.dimensions,m=d&&d.available&&d.measures[0],old=store.get('hist',[]),prev=old.find(o=>o.id===id);
 const th=prev&&prev.th?prev.th:await urlShrink(photo,96),h=old.filter(o=>o.id!==id);
 h.unshift({id,t:mt?.t||id,label:r.label,status:r.status,q:qLevel(r),conf:r.confidence,shot:mt?.shot||'',size:m?m.name.split(' (')[0]+' '+num(m.value)+' '+m.unit:'',th,queued:!!queued,site:site||(mt&&mt.mode==='survey'?siteId():'')});
 h.sort((a,b)=>b.t-a.t);const keep=h.slice(0,20);store.set('hist',keep);
 const ids=new Set(keep.map(o=>o.id));for(const x of await safe(()=>DB.all('results'),[]))if(!ids.has(x.id))safe(()=>DB.del('results',x.id));drawHist()}
function drawHist(){const h=store.get('hist',[]),el=$('#history');if(!h.length){el.innerHTML='';return}
 el.innerHTML=`<section class="card"><div class="kicker">Recent observations (this phone)</div><ul class="hist">${h.map(o=>`<li ${o.id?`data-id="${o.id}" role="button" tabindex="0"`:''}>${o.th?`<img src="${o.th}" alt="">`:'<span></span>'}<span><b>${esc(D.names[o.label]||o.label)}</b>${o.q>=2?` <span class="sev s${o.q-1}">${o.q===3?'Very poor photo':'Poor photo'}</span>`:''}${o.status==='uncertain'?' <span>(uncertain)</span>':''}${o.queued?' <span>(sent later)</span>':''}<br>${esc([o.shot,o.size].filter(Boolean).join(', '))}</span><span>${Math.round(o.conf*100)}%<br><small>${new Date(o.t).toLocaleTimeString([],{hour:'2-digit',minute:'2-digit'})}</small></span></li>`).join('')}</ul></section>`;
 el.querySelectorAll('li[data-id]').forEach(li=>{const go=()=>openHist(+li.dataset.id);li.onclick=go;li.onkeydown=e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();go()}}})}
async function openHist(id){const x=await safe(()=>DB.get('results',id),null);if(!x){toast('This result is no longer stored on the phone.');return}
 cur=x.r;curMeta=x.meta;curPhoto=x.photo||'';lastBlob=x.blob||null;lastDist=x.meta&&x.meta.dist||null;job=null;
 $('#prev').src=curPhoto;$('#fig').style.display=curPhoto?'block':'none';photoQ={level:0,issues:[]};A.render(cur);typeChip(cur);afterType(cur,true);if(cur.dimensions)afterDims(cur,true);
 $('#fig').scrollIntoView({behavior:'smooth',block:'start'})}
drawHist();A._metrics=metrics;A._judge=judge;A._grade=grade;A._hold=hold;A._live=liveShow;A._fuse=fuse;A._flush=flush;A._q=()=>safe(()=>DB.all('queue'),[]);A._st=()=>({flushing,done:[...done],shot,mode,curId:cur&&cur.__id,metaShot:curMeta&&curMeta.shotId,site:!!sess.get('site')});   // exposed for tests
/* ---------- shared with the overlapping-set module (src/pano.py) ---------- */
function runSet(r,blob,g,label){lastBlob=blob;lastPGps=null;lastHead=null;lastSrc=g?'cam':'gal';lastTilt=g?{g}:null;lastDist=distM();
 curMeta=meta();curMeta.set=label||'';cur=r;job=r.job||null;const fig=$('#fig');$('#prev').src=URL.createObjectURL(blob);fig.style.display='block';
 if(r.ms)store.set('etaT',ema('etaT',r.ms,4000));photoQ={level:0,issues:[]};withQ(r);A.render(r);afterType(r);sizes(r)}
A._g={say,buzz,toast,tr,store,sess,step,safety,openFinder,closeFinder,openCamera,ICO,LIVE,prog,post,busy,cancelled,params,gx,runSet,fail,RX,out,vf,vid,
 ori:()=>ori,mode:()=>mode,shoot:()=>shoot(),setMode:m=>{mode=m;store.set('mode',m);drawMode()},abort:()=>xhr&&xhr.abort(),camIn,galIn,ema};
A.pano&&A.pano.init();
const demo=new URLSearchParams(location.search).get('demo');   // demo pages show the guidance too (nothing saved)
if(demo&&D.samples[demo]&&out.firstElementChild){cur=D.samples[demo];afterType(cur,true);if(cur.dimensions)afterDims(cur,true)}
})();
"""


def data():
    return {"check": photo_check(), "glossary": GLOSSARY, "shots": SHOTS, "safety": SAFETY, "tips": FIELD_TIPS,
            "tour": TOUR, "illus": ILLUS, "questions": QUESTIONS, "quiz": QUIZ, "hi": HI,
            # live steadiness: mean |grey change| between frames 0.45 s apart at 512 px. A heuristic (no
            # labelled video exists to calibrate it); it only delays the green "ready" ring, never the shutter.
            "steadyMax": 8.0,
            # "serious" margins of the photo check (beyond the calibrated "minor" thresholds). Fixed UI steps, not
            # calibrated on labelled data: light < 0.7 x lum_min or above halfway from lum_max to white, shadow /
            # highlight areas 2x / 1.6x the limit, contrast < 0.65 x, sharpness < 0.4 x, sky > 75 %, short side
            # < 480 px, roll > 25 deg, aim < -35 or > 75 deg.
            "severe": {"lum_lo": 0.7, "lum_hi": 0.5, "dark_x": 2.0, "bright_x": 1.6, "contrast_x": 0.65,
                       "sharp_x": 0.4, "sky": 0.75, "res": 480, "roll": 25, "elev_lo": -35, "elev_hi": 75},
            # stage starts as a fraction of the expected time of each request (type ~4 s, sizes ~28 s); the
            # expected times are learned on the phone from past requests (moving average)
            "stagesType": [[0, "Checking it is a usable slope photo"], [0.4, "Identifying the landslide type"]],
            "stagesDims": [[0, "Outlining the landslide (CLIPSeg, SAM, outline head)"],
                           [0.4, "Estimating depth and scale"], [0.75, "Measuring sizes and their ranges"]]}
