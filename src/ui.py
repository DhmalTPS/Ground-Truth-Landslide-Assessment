"""Field app interface: one design system shared by the logo, type glyphs and page ("Contour").

The app is drawn as a topographic field instrument:
  paper     cool lichen grey #E9EDE6 / night survey #0F1A1B, spruce-slate ink #15242A
  accent    the logo's moss teal #17695A (dark #5FD1A8); survey flagging-tape orange #FF6A1A for hazards only
  type      DIN family for headings and numbers (road-sign / map lettering, read at a glance), system body face
  form      information sits on open paper divided by contour lines; only blocks you act on (capture, save,
            questions) or must stop for (safety, errors, photo problems) get a container
  signature the summit gauge: seeded contour rings around the type glyph, inked from the foot up to the confidence
Glyphs: same 64x64 grammar as the logo (contour arcs, round caps).
The page works offline (system fonts, inline SVG, no external files) and has a demo mode:
  /?demo=ok | uncertain | family | bad | error   renders a sample result (no photo needed).
"""
import json

import guide
import pano

# ---------------------------------------------------------------- shared SVG definitions
# Glyphs reuse the logo's geometry (64x64 grid, contour arcs, round caps): one visual family.
from logo import C, GROUND, GROUND_AXIS, RADII, SIGNAL, W, _arc_d, _pt, _stops  # noqa: E402

DEFS = ('<svg width="0" height="0" style="position:absolute" aria-hidden="true" focusable="false"><defs>'
        f'<linearGradient id="g-ground" gradientUnits="userSpaceOnUse" x1="{GROUND_AXIS[0][0]}" y1="{GROUND_AXIS[0][1]}" '
        f'x2="{GROUND_AXIS[1][0]}" y2="{GROUND_AXIS[1][1]}">{_stops(GROUND)}</linearGradient>'
        f'<linearGradient id="g-signal" x1="0" y1="0" x2="1" y2="1">{_stops(SIGNAL)}</linearGradient>'
        '</defs></svg>')

_ST = f'fill="none" stroke-width="{W}" stroke-linecap="round" stroke-linejoin="round"'


def _arc(r, a0, a1, grad="g-ground", dx=0.0, dy=0.0, extra=""):
    return f'<path d="{_arc_d(r, a0, a1, dx, dy)}" stroke="url(#{grad})" {_ST}{extra}/>'


def _svg(body, label):
    return f'<svg viewBox="0 0 64 64" role="img" aria-label="{label}">{body}</svg>'


def _hill(outer_break=None):
    """The contour hill; optionally with a gap (degrees) in the outer contour."""
    if outer_break:
        out = _arc(RADII[0], 180, outer_break[1]) + _arc(RADII[0], outer_break[0], 0)
    else:
        out = _arc(RADII[0], 180, 0)
    return out + _arc(RADII[1], 180, 0) + _arc(RADII[2], 180, 0)


_rx, _ry = _pt(RADII[0], 18.0)          # lower end of the broken segment (pivot for rotation)
_e0, _e1 = _pt(RADII[0], 56.0), _pt(RADII[0], 8.0)
GLYPHS = {
    "translational_slide": _svg(_hill((18, 58)) + _arc(RADII[0], 58, 18, "g-signal", 5.6, 6.6), "Translational slide"),
    "rotational_slide": _svg(
        _hill((18, 62)) + _arc(RADII[0], 62, 18, "g-signal", 6.5, 5.0,
                               f' transform="rotate(26 {_rx + 6.5:.2f} {_ry + 5.0:.2f})"'), "Rotational slide"),
    "earth_mud_flow": _svg(
        _hill((8, 56)) +
        f'<path d="M{_e0[0]:.1f} {_e0[1]:.1f}C{_e0[0] + 7:.1f} {_e0[1] + 2:.1f} {_e0[0] + 2:.1f} {_e0[1] + 10:.1f} '
        f'{_e0[0] + 9:.1f} {_e0[1] + 13:.1f}S{_e1[0] + 4:.1f} {C[1] - 1:.1f} {_e1[0] + 6:.1f} {C[1] + 1.5:.1f}" '
        f'stroke="url(#g-signal)" {_ST}/>', "Earthflow or mudflow"),
    "fall_topple": _svg(
        f'<path d="M12 {C[1]}V17M21 {C[1]}V24M30 {C[1]}V33" stroke="url(#g-ground)" {_ST}/>'
        '<circle cx="39" cy="22" r="3.4" fill="url(#g-signal)"/><circle cx="45" cy="31.5" r="2.9" fill="url(#g-signal)"/>'
        f'<circle cx="50.5" cy="{C[1] - 2.2}" r="3.9" fill="url(#g-signal)"/>', "Rock fall or topple"),
    "debris_flow": _svg(
        _arc(22, 90, 0, dx=-21, dy=0) + _arc(13, 90, 0, dx=-21, dy=0) +
        _arc(22, 180, 90, dx=33, dy=0) + _arc(13, 180, 90, dx=33, dy=0) +
        '<circle cx="31" cy="20" r="2.4" fill="url(#g-signal)"/><circle cx="30.4" cy="28.5" r="2.8" fill="url(#g-signal)"/>'
        '<circle cx="31.4" cy="36.5" r="3.1" fill="url(#g-signal)"/>' +
        f'<path d="M23 {C[1] + 1.5}Q31 {C[1] - 6} 39 {C[1] + 1.5}" stroke="url(#g-signal)" {_ST}/>', "Debris flow"),
    "no_landslide": _svg(_hill(), "No landslide visible"),
    "bad_photo": _svg(
        '<path d="M8 20V12Q8 8 12 8H20M44 8H52Q56 8 56 12V20M56 44V52Q56 56 52 56H44M20 56H12Q8 56 8 52V44" '
        f'stroke="url(#g-ground)" {_ST}/>'
        f'<line x1="21" y1="43" x2="43" y2="21" stroke="url(#g-signal)" {_ST}/>', "Unusable photo"),
}
FAMILY_GLYPH = {"flow": "debris_flow", "slide": "translational_slide"}

# small interface icons (stroke = currentColor)
UI_ICONS = {
    "camera": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 8.5A2.5 2.5 0 0 1 6.5 6H8l1.4-2h5.2L16 6h1.5A2.5 2.5 0 0 1 20 8.5v8a2.5 2.5 0 0 1-2.5 2.5h-11A2.5 2.5 0 0 1 4 16.5z"/><circle cx="12" cy="12.5" r="3.6"/></svg>',
    "image": '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3.5" y="4.5" width="17" height="15" rx="2.5"/><circle cx="9" cy="10" r="1.6"/><path d="M4 17l5-5 4 4 2.5-2.5L20 18"/></svg>',
    "check": '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="8.5"/><path d="M8.3 12.3l2.5 2.5 4.9-5.2"/></svg>',
    "alert": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 4.2l8.8 15.3H3.2z"/><path d="M12 10v4.3M12 17.1v.1"/></svg>',
    "pos": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 19L13 6l8 13z"/><circle cx="7" cy="19.5" r="1"/></svg>',
    "frame": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 8V5.5A1.5 1.5 0 0 1 5.5 4H8M16 4h2.5A1.5 1.5 0 0 1 20 5.5V8M20 16v2.5a1.5 1.5 0 0 1-1.5 1.5H16M8 20H5.5A1.5 1.5 0 0 1 4 18.5V16"/></svg>',
    "sun": '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="3.8"/><path d="M12 3v2M12 19v2M3 12h2M19 12h2M5.6 5.6l1.4 1.4M17 17l1.4 1.4M5.6 18.4L7 17M17 7l1.4-1.4"/></svg>',
    "spark": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3.5l1.9 5.2 5.2 1.9-5.2 1.9L12 17.7l-1.9-5.2-5.2-1.9 5.2-1.9z"/></svg>',
}

CSS = """
/* "Field Atlas at dawn". The app is a geological field atlas: a painted ridge landscape at the top (dawn in light mode,
   moonlight in dark mode) whose foreground fog becomes the page; panels are atlas plates with an engraved inner rule;
   open sections are separated by lithology symbols (sand, shale, limestone, conglomerate) so scrolling reads as
   descending through strata. Display serif for names and titles (a field guide's specimen labels), system sans for
   reading. Flagging-tape orange is kept for hazards only; every text colour >= 4.5:1, every control edge >= 3:1. */
:root{--teal-950:#082f2a;--teal-800:#0e4d45;--teal-600:#155e51;--teal-400:#4fa587;--sage-300:#8fc9a9;--sage-100:#e4f1e9;
--amber:#e8a400;--orange:#a3401a;--ruby:#b8381f;
--bg:#e7ebe8;--surface:#fbfaf6;--surface-2:#f1f2ee;--ink:#1b272c;--ink-2:#3d4c52;--mute:#53636a;--line:#cfd6d2;--contour:#a6b5b0;--frame:#bcc6c1;
--brand:#1a6a5b;--on-brand:#ffffff;--link:#155e51;--warn:#a3401a;--warn-bg:#fbeee6;--warn-line:#edc4ac;--tape:#ff6a1a;--tape-ink:#1b272c;
--caution:#7c5400;--dup:#3a62c4;--focus:#e8a400;--edge:#6f817c;--info:#1e6edc;
--g-ground:#1a6a5b;--g-signal:#c8562a;--g-track:#a9cfbd;--tint-signal:rgba(200,86,42,.1);--tint-ground:rgba(26,106,91,.09);
--sky1:#a6bccd;--sky2:#dde3e3;--sky3:#f3d6b6;--sun:#f6bf86;--r0:#c4ced7;--r1:#9dadbb;--r2:#728899;--r3:#4b6476;--scar:#c9a27f;--mist:#ffffff;--star:transparent;--scar-ink:#6e4026;--crater:transparent;--grain:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='180' height='180'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.9' numOctaves='2' stitchTiles='stitch'/%3E%3CfeColorMatrix values='0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 .1 0'/%3E%3C/filter%3E%3Crect width='180' height='180' filter='url(%23n)'/%3E%3C/svg%3E");--neat:linear-gradient(var(--frame),var(--frame));--ease-out:cubic-bezier(.16,.84,.24,1);--spring:cubic-bezier(.3,1.45,.5,1);
--lift:0 1px 1px rgba(27,39,44,.05),0 12px 30px -18px rgba(27,39,44,.45);--shadow:0 18px 40px -16px rgba(27,39,44,.45);--r:6px;
--f-disp:"Iowan Old Style","Palatino Linotype","Book Antiqua",Palatino,"Noto Serif",Georgia,"Noto Serif Devanagari","Nirmala UI",serif;
--f-sign:var(--f-disp);
--f-body:ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,"Noto Sans","Noto Sans Devanagari","Nirmala UI",sans-serif;
--s1:4px;--s2:8px;--s3:12px;--s4:16px;--s5:24px;--s6:32px;--tap:48px;
color-scheme:light}
@media (prefers-color-scheme:dark){:root{--bg:#0d1420;--surface:#141d2b;--surface-2:#1a2434;--ink:#e5ebf1;--ink-2:#b9c5d0;--mute:#8f9eac;
--line:#26334a;--contour:#3a4b66;--frame:#30405a;--brand:#6fd3b0;--on-brand:#06261f;--link:#8bdcc0;--teal-600:#8bdcc0;--warn:#ffa27a;--orange:#ffa27a;
--warn-bg:#2a1b17;--warn-line:#5a3326;--tape:#ff7a33;--caution:#f2c25a;--dup:#9db8ff;--focus:#f2c25a;--edge:#70839c;--info:#7fb0ff;
--g-ground:#6fd3b0;--g-signal:#ffa27a;--g-track:#2c5a52;--tint-signal:rgba(255,162,122,.12);--tint-ground:rgba(111,211,176,.1);
--sky1:#08101d;--sky2:#101b30;--sky3:#1d2b46;--sun:#dfe7f2;--r0:#25344d;--r1:#1d2a40;--r2:#172235;--r3:#111a2a;--scar:#7d5a48;--mist:#9fb3cc;--star:#dfe7f2;--scar-ink:#3a1a10;--crater:rgba(120,138,166,.32);--grain:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='180' height='180'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.9' numOctaves='2' stitchTiles='stitch'/%3E%3CfeColorMatrix values='0 0 0 0 1 0 0 0 0 1 0 0 0 0 1 0 0 0 .035 0'/%3E%3C/filter%3E%3Crect width='180' height='180' filter='url(%23n)'/%3E%3C/svg%3E");
--lift:0 1px 1px rgba(0,0,0,.3),0 14px 32px -18px rgba(0,0,0,.85);--shadow:0 18px 40px -16px rgba(0,0,0,.8);color-scheme:dark}}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;min-height:100vh;overflow-x:clip;color:var(--ink);background:var(--grain),var(--bg);background-color:var(--bg);font:16px/1.55 var(--f-body);font-feature-settings:"kern","liga";text-rendering:optimizeLegibility;-webkit-font-smoothing:antialiased;caret-color:var(--brand);accent-color:var(--brand)}
html{scrollbar-color:var(--contour) transparent}::selection{background:var(--sage-300);color:var(--teal-950)}
p,li,dd{text-wrap:pretty}h2,.title,.brand b{text-wrap:balance}
main{position:relative;max-width:620px;margin:0 auto;padding:var(--s4) var(--s4) var(--s6)}
svg{display:block}
a{color:var(--link);text-underline-offset:2px}
:focus-visible{outline:2.5px solid var(--focus);outline-offset:3px}
.ico{width:20px;height:20px;fill:none;stroke:currentColor;stroke-width:1.7;stroke-linecap:round;stroke-linejoin:round;flex:none}
/* the landscape: sky, sun or moon, five ridges in atmospheric perspective, a slide scar, drifting mist; the nearest
   band is the page colour, so the painting dissolves into the page */
.hero{position:absolute;left:50%;width:100vw;transform:translateX(-50%);top:0;height:var(--hero-h);z-index:0;overflow:hidden;pointer-events:none}
:root{--hero-h:clamp(310px,26vw,420px)}
@media (min-width:700px){header{min-height:calc(var(--hero-h) - 60px)!important}}
.hero .lay{animation:rise 1.7s var(--ease-out) both;animation-delay:calc(var(--d)*120ms)}
.hero .sun{animation:rise 2.6s var(--ease-out) both .15s}
@keyframes rise{from{translate:0 30px;opacity:0}}
header>*{animation:settle .9s var(--ease-out) both .55s}header>.brand{animation-delay:.45s}
@keyframes settle{from{translate:0 8px;opacity:0}}
.card.panel{animation:settle 1s var(--ease-out) both .3s}
.hero svg{width:100%;height:100%}
.hero .mist{animation:drift 38s ease-in-out infinite alternate}.hero .mist.b{animation-duration:52s;animation-direction:alternate-reverse}
.hero .tw{animation:tw 4.5s ease-in-out infinite}.hero .tw:nth-child(3n){animation-delay:-1.7s}.hero .tw:nth-child(4n){animation-delay:-3.1s}
@keyframes drift{from{transform:translateX(-60px)}to{transform:translateX(60px)}}
@keyframes tw{50%{opacity:.25}}
header{position:relative;z-index:1;display:flex;align-items:flex-start;gap:var(--s3);min-height:calc(var(--hero-h) - 84px);margin:0;padding-top:var(--s2)}
header .logo{padding:6px;border-radius:50%;background:var(--surface);box-shadow:var(--lift)}
header .logo svg{width:34px;height:34px}
.brand{min-width:0;flex:1;padding-top:2px}
.brand b{display:block;font:600 clamp(1.7rem,1.1rem + 1.5vw,2.6rem)/1.05 var(--f-disp);letter-spacing:-.012em;color:var(--ink)}
.brand span{display:block;font:italic 400 .95rem/1.3 var(--f-disp);color:var(--ink-2);margin-top:6px;white-space:nowrap}
/* Devanagari has tall matras above the headline: give display lines room in Hindi */
:lang(hi) .brand b,:lang(hi) .title,:lang(hi) h2{line-height:1.3}
/* open sections: text on the page, divided by a band of lithology symbols; the symbol changes down the page */
.card{position:relative;z-index:1;margin-top:var(--s5);padding:30px 2px 0;background:none;border:0;border-radius:0;box-shadow:none}
.card::before{content:"";position:absolute;left:0;right:0;top:0;height:12px;background:var(--contour);
-webkit-mask:var(--lith) repeat-x 0 0/24px 12px;mask:var(--lith) repeat-x 0 0/24px 12px}
.card::after{content:"";position:absolute;left:0;right:0;top:15px;height:1px;background:var(--line)}
.card{--lith:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='24' height='12'%3E%3Ccircle cx='4' cy='4' r='1.3'/%3E%3Ccircle cx='16' cy='8' r='1.3'/%3E%3Ccircle cx='11' cy='10.5' r='.9'/%3E%3Ccircle cx='21' cy='2.5' r='.9'/%3E%3C/svg%3E")}
#out>.card:nth-of-type(4n+2),#history>.card{--lith:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='24' height='12'%3E%3Cpath d='M1 3h8M14 3h8M7 9h8M19 9h5M0 9h2' stroke='%23000' stroke-width='1.3'/%3E%3C/svg%3E")}
#out>.card:nth-of-type(4n+3){--lith:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='24' height='12'%3E%3Cpath d='M0 1h24M0 6.5h24M0 11.5h24M6 1v5.5M18 6.5v5' stroke='%23000' stroke-width='1.1' fill='none'/%3E%3C/svg%3E")}
#out>.card:nth-of-type(4n){--lith:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='24' height='12'%3E%3Ccircle cx='5' cy='6' r='3.2' fill='none' stroke='%23000' stroke-width='1.1'/%3E%3Ccircle cx='16' cy='3.5' r='2' fill='none' stroke='%23000' stroke-width='1.1'/%3E%3Ccircle cx='19' cy='9.5' r='1.4' fill='none' stroke='%23000' stroke-width='1.1'/%3E%3C/svg%3E")}
/* plates: blocks you act on or must stop for; paper with an engraved inner rule */
.card.panel,#repsec,#askcard,.card.result,.card.safety,.card.bad,.card.qband{background:var(--grain),var(--surface);background-color:var(--surface);border:1px solid var(--line);border-radius:var(--r);
outline:1px solid var(--frame);outline-offset:-7px;box-shadow:var(--lift);padding:var(--s5) var(--s5) var(--s5)}
.card.panel,#repsec,#askcard,.card.result{background:var(--neat) 3px 3px/8px 8px no-repeat,var(--neat) calc(100% - 3px) 3px/8px 8px no-repeat,var(--neat) 3px calc(100% - 3px)/8px 8px no-repeat,var(--neat) calc(100% - 3px) calc(100% - 3px)/8px 8px no-repeat,var(--grain),var(--surface);background-color:var(--surface)}
.card.qband{outline:0}
.card.panel::before,#repsec::before,#askcard::before,.card.result::before,.card.qband::before,.card.bad::before,
.card.panel::after,#repsec::after,#askcard::after,.card.result::after,.card.qband::after,.card.bad::after,.card.safety::after{display:none}
.card.panel{margin-top:0}
.kicker{font:650 .8rem/1.3 var(--f-body);color:var(--ink-2);letter-spacing:.02em;margin:0 0 var(--s2)}
#out>.card:not(.result):not(.safety)>.kicker:first-child,#history .kicker{font:600 1.3rem/1.2 var(--f-disp);letter-spacing:0;color:var(--ink);margin-bottom:var(--s3)}
#out>.card>.kicker:first-child:has(+h2){font:650 .8rem/1.3 var(--f-body);letter-spacing:.02em;color:var(--ink-2);margin-bottom:var(--s2)}
h2{font:600 1.42rem/1.2 var(--f-disp);margin:0 0 var(--s3);letter-spacing:-.005em}
.tips{display:grid;gap:var(--s3);margin:0 0 var(--s5);padding:0;list-style:none;counter-reset:tp}
.tips li{display:grid;grid-template-columns:28px 1fr;gap:var(--s3);align-items:baseline;color:var(--ink-2);font-size:.98rem;counter-increment:tp}
.tips li::before{content:counter(tp);font:italic 500 1.6rem/1 var(--f-disp);color:var(--link);text-align:right}
.tips li,.hist small,.foot{font-variant-numeric:oldstyle-nums proportional-nums}
.tips .ico{display:none}
.btns{display:grid;grid-template-columns:1fr 1fr;gap:var(--s2)}.btns .wide{grid-column:1/-1}
.btn{position:relative;display:flex;align-items:center;justify-content:center;gap:var(--s2);min-height:54px;padding:var(--s3) var(--s5);border-radius:999px;border:0;
font-weight:650;font-size:1rem;line-height:1.2;font-family:inherit;cursor:pointer;user-select:none;-webkit-tap-highlight-color:transparent;transition:background-color .15s ease,transform .08s ease,box-shadow .15s ease}
.btn.primary{color:var(--on-brand);background:var(--brand);box-shadow:0 1px 0 rgba(255,255,255,.3) inset,0 -3px 0 rgba(0,0,0,.14) inset,0 10px 22px -12px var(--brand),0 2px 4px -2px rgba(0,0,0,.25)}
.btn{transition:background-color .2s ease,transform .35s var(--spring),box-shadow .25s ease,border-color .2s ease,filter .2s ease}
.btn.primary:hover{filter:brightness(.93);transform:translateY(-1px)}.btn:active{transform:scale(.975);transition-duration:.08s}
.btn .ico{transition:transform .35s var(--spring)}.btn:hover .ico{transform:translateY(-1.5px)}
@media (prefers-color-scheme:dark){.btn.primary:hover{filter:brightness(1.08)}}
.btn.ghost{color:var(--link);background:var(--surface);border:1.5px solid var(--edge)}
.btn.ghost:hover{background:var(--tint-ground);border-color:var(--link)}
.btn.text{background:none;color:var(--link);min-height:var(--tap);text-decoration:underline;text-underline-offset:3px}
.btn[disabled]{opacity:.6;cursor:progress}
.btn input{position:absolute;inset:0;opacity:0;cursor:pointer}
.btn:focus-within{outline:3px solid var(--focus);outline-offset:2px}
.span2{grid-column:1/-1}
/* the photo is mounted like a print in the atlas */
figure{position:relative;z-index:1;margin:var(--s5) 0 0;display:none}
figure img{width:100%;max-height:62vh;object-fit:cover;display:block;border:7px solid var(--surface);border-radius:var(--r);box-shadow:var(--lift)}
.chip{position:absolute;left:var(--s4);top:var(--s4);display:inline-flex;align-items:center;gap:7px;padding:6px 12px 6px 10px;border-radius:999px;
font-size:.84rem;font-weight:650;color:#fff;background:rgba(13,20,32,.84)}
.dot{width:8px;height:8px;border-radius:50%;background:var(--sage-300)}
.chip.signal .dot{background:var(--amber)}.chip.bad .dot{background:#ff8a6b}
.chip.signal .dot,.chip.bad .dot{width:11px;height:10px;border-radius:0;clip-path:polygon(50% 0,100% 100%,0 100%)}
.spin{width:14px;height:14px;border-radius:50%;border:2px solid currentColor;border-right-color:transparent;opacity:.8;animation:sp .8s linear infinite}
@keyframes sp{to{transform:rotate(360deg)}}
/* the answer as a specimen label: the type stands on its summit; confidence inks the contour rings from the foot up */
.result{padding:var(--s5)}
.rhead{display:grid;grid-template-columns:auto 1fr;gap:var(--s4);align-items:center}
.summit{position:relative;width:116px;height:116px;flex:none;color:var(--brand)}
.summit.signal{color:var(--caution)}.summit.bad{color:var(--ruby)}
.summit svg.rings{position:absolute;inset:0;width:100%;height:100%;overflow:visible}
.rings path{fill:none;stroke:var(--line);stroke-width:1.1}
.rings path.on{stroke:currentColor;stroke-width:1.7;stroke-dasharray:1;stroke-dashoffset:0;animation:climb .8s cubic-bezier(.3,.7,.2,1) both;animation-delay:calc(var(--i)*80ms)}
.rings path.on.idx{stroke-width:2.6}
@keyframes climb{from{stroke-dashoffset:1}}
.summit .glyph{position:absolute;left:50%;top:47%;transform:translate(-50%,-50%);width:46%;height:46%;border-radius:50%;display:grid;place-items:center;background:none}
.summit .glyph svg{width:78%;height:78%}
.glyph{width:64px;height:64px;flex:none;border-radius:50%;display:grid;place-items:center;background:var(--tint-ground)}
.glyph svg{width:48px;height:48px}
.title{font:600 2.05rem/1.04 var(--f-disp);letter-spacing:-.015em;margin:4px 0 var(--s1);text-wrap:balance}
.result .rhead>div:last-child{animation:settle .8s var(--ease-out) both .15s}.summit .glyph{animation:pop .7s var(--spring) both .45s}
@keyframes pop{from{scale:.6;opacity:0}}
.hungr{font-size:.9rem;color:var(--mute)}
.result .kicker{font:italic 400 1.02rem/1.2 var(--f-disp);letter-spacing:0;color:var(--ink-2);margin-bottom:2px}
.result p.hungr.u-t2{font:italic 400 .98rem/1.45 var(--f-disp);color:var(--ink-2)}
.meter{margin-top:var(--s4);padding-top:var(--s3);border-top:1px solid var(--line)}
.meter .row{display:flex;justify-content:space-between;align-items:baseline;font-size:.95rem;color:var(--ink-2)}.meter .cband{color:var(--ink)}
.meter .val{font:600 2.1rem/1 var(--f-disp);color:var(--ink);font-variant-numeric:lining-nums tabular-nums}
.track{height:6px;border-radius:99px;background:var(--line);overflow:hidden;margin-top:var(--s2)}
.cscale{position:relative;height:16px;margin-top:var(--s2);color:var(--brand);background:repeating-linear-gradient(90deg,var(--contour) 0 1px,transparent 1px 100%) 0 100%/10% 4px repeat-x}
.cscale.signal{color:var(--caution)}.cscale.bad{color:var(--ruby)}
.cscale::before{content:"";position:absolute;left:0;right:0;top:5px;height:4px;border-radius:2px;background:var(--line)}
.cscale i{position:absolute;left:0;top:5px;height:4px;border-radius:2px;width:calc(var(--v)*100%);background:currentColor;transform-origin:left;animation:grow 1.1s var(--ease-out) both .2s}
.cscale::after{content:"";position:absolute;top:0;left:calc(var(--c)*100%);width:2px;height:16px;margin-left:-1px;border-radius:1px;background:var(--ink-2)}
@keyframes grow{from{transform:scaleX(0)}}
.prob .fl{transform-origin:left;animation:grow 1s var(--ease-out) both .3s}
.fill{height:100%;border-radius:99px;background:var(--brand)}
.fill.signal{background:var(--caution)}
.result.lowq{border:2px dashed var(--ruby)}.result.lowq .fill{background:var(--ruby)}
.note{margin:var(--s3) 0 0;padding:var(--s3) var(--s4);border-radius:4px;background:var(--surface-2);color:var(--ink-2);font-size:.95rem;border-left:3px solid var(--caution)}
.probs{display:grid;gap:var(--s3);margin-top:var(--s1)}
.prob{display:grid;grid-template-columns:28px 1fr 56px;gap:var(--s3);align-items:center}
.prob svg{width:28px;height:28px}
.prob .nm{font-size:.96rem;color:var(--ink-2);display:flex;flex-direction:column;gap:6px}
.prob .tr{height:3px;border-radius:99px;background:var(--line);overflow:hidden}
.prob .fl{height:100%;border-radius:99px;background:var(--g-track)}
.prob.top .fl{background:var(--brand)}.prob.top .nm{color:var(--ink);font-weight:650}
.prob .pc{text-align:right;font:500 1.15rem/1 var(--f-disp);font-variant-numeric:lining-nums tabular-nums;color:var(--mute)}
.prob.top .pc{color:var(--ink);font-weight:600}
summary{list-style:none}summary::-webkit-details-marker{display:none}
details>summary::after{content:"";flex:none;width:7px;height:7px;margin:0 0 3px 12px;border:solid currentColor;border-width:0 1.7px 1.7px 0;transform:rotate(45deg);transition:transform .35s var(--spring),margin .35s var(--spring)}
details[open]>summary::after{transform:rotate(225deg);margin-bottom:-3px}
details[open]>:not(summary){animation:unfold .4s var(--ease-out) both}@keyframes unfold{from{opacity:0;translate:0 -6px}}
details.more{margin-top:var(--s2)}details.more>summary{min-height:var(--tap);display:flex;align-items:center;cursor:pointer;color:var(--link);font-weight:600;font-size:.95rem}
.list{list-style:none;padding:0;margin:0;display:grid;gap:var(--s1)}
.list li{display:flex;gap:var(--s2);align-items:flex-start;font-size:.97rem;color:var(--ink-2)}
.list .ico{color:var(--link);margin-top:1px}
/* safety wears survey flagging tape: the one block built to interrupt */
.card.safety{background:var(--warn-bg);border-color:var(--warn-line);box-shadow:var(--lift);padding-top:calc(var(--s5) + 10px);overflow:hidden}
.card.safety::before{display:block;height:10px;mask:none;-webkit-mask:none;border-radius:0;
background:linear-gradient(rgba(255,255,255,.22),rgba(255,255,255,0) 45%,rgba(0,0,0,.14)),repeating-linear-gradient(-45deg,var(--tape) 0 12px,var(--tape-ink) 12px 24px)}
.safety h2{display:flex;gap:var(--s2);align-items:center;color:var(--warn);margin-bottom:var(--s2)}.safety .ico{color:var(--warn)}
.safety p{margin:0;color:var(--ink);font-size:1.02rem}
.card.bad{background:var(--warn-bg);border-color:var(--warn-line)}
ol.steps{margin:var(--s2) 0 0;padding-left:1.2rem;color:var(--ink-2)}ol.steps li{margin:var(--s1) 0}
.skel{height:14px;border-radius:8px;margin:10px 0;background:linear-gradient(90deg,var(--line) 0 35%,var(--surface-2) 50%,var(--line) 65% 100%) 0 0/300% 100%;animation:sheen 1.6s ease-in-out infinite}
@keyframes sheen{from{background-position:100% 0}to{background-position:0 0}}
@keyframes pulse{50%{opacity:.5}}
.foot{position:relative;margin-top:var(--s6);padding-top:var(--s4);border-top:1px solid var(--line);font-size:.86rem;color:var(--mute);text-align:left;line-height:1.6}
.meta{display:block;margin-top:var(--s5);font-size:.86rem;color:var(--mute);text-align:left}
.u-m0{margin:0!important}.u-t1{margin:4px 0 0!important}.u-t2{margin:8px 0 0!important}.u-t3{margin:12px 0 0!important}.u-t4{margin:16px 0 0!important}
.u-b2{margin:0 0 8px!important}.u-b3{margin:0 0 12px!important}.u-tb{margin:4px 0 12px!important}.u-sub{margin:-4px 0 12px!important}.u-blk{display:block!important}
input::placeholder,textarea::placeholder{font-family:var(--f-disp);font-style:italic}
input:not([type=checkbox]):not([type=radio]):focus-visible,textarea:focus-visible,select:focus-visible{outline:0;border-color:var(--brand)!important;box-shadow:0 0 0 4px var(--tint-ground),0 0 0 1px var(--brand)}
/* the colophon: provenance set like the last line of an atlas plate */
.foot{font:italic 400 .95rem/1.6 var(--f-disp);color:var(--ink-2)}
@media (max-width:380px){.btns{grid-template-columns:1fr}.title{font-size:1.7rem}.summit{width:96px;height:96px}.brand b{font-size:1.45rem}}
@media (prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}}
"""

JS = r"""
const D=__DATA__, G=D.glyphs, out=document.getElementById('out'), fig=document.getElementById('fig'),
 prev=document.getElementById('prev'), chip=document.getElementById('chip');
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const pct=p=>Math.round(p*100)+'%';
const ico=n=>D.icons[n].replace('<svg','<svg class="ico"');
function setChip(kind,text,busy){chip.className='chip '+kind;chip.innerHTML=(busy?'<span class="spin"></span>':'<span class="dot"></span>')+esc(text)}
async function shrink(file){
 try{const bmp=await createImageBitmap(file,{imageOrientation:'from-image'});
  const s=Math.min(1,1280/Math.max(bmp.width,bmp.height));const c=document.createElement('canvas');
  c.width=Math.round(bmp.width*s);c.height=Math.round(bmp.height*s);c.getContext('2d').drawImage(bmp,0,0,c.width,c.height);
  return await new Promise(r=>c.toBlob(r,'image/jpeg',0.9));}catch(e){return file;}}
// summit gauge: contour rings of a hill drawn from a seed (the type name, so every type has its own terrain);
// confidence = how many rings are inked, from the foot up towards the summit where the type glyph stands
function summit(seed,conf,cls){let s=7;for(const ch of seed)s=(Math.imul(s,31)+ch.charCodeAt(0))>>>0;
 const rnd=()=>(s=(Math.imul(s,1664525)+1013904223)>>>0)/4294967296,K=[2,3,5,7];
 const N=6,on=Math.max(1,Math.floor(conf*N+1e-9)),ph=K.map(()=>rnd()*6.2832),am=[.05,.03,.018,.01].map(a=>a*(.6+rnd()*.8));
 let p='';for(let i=0;i<N;i++){const r0=58-i*5.6,k=1-i*.1;let d='';
  for(let j=0;j<=60;j++){const t=j/60*6.2832;let w=0;for(let q=0;q<4;q++)w+=am[q]*Math.sin(K[q]*t+ph[q]);const r=r0*(1+k*w);
   d+=(j?'L':'M')+(64+r*Math.cos(t)).toFixed(1)+' '+(64-i*1.1+r*Math.sin(t)*.9).toFixed(1)}
  p+=`<path pathLength="1" d="${d}Z" class="${i<on?'on':''}${i%5===0?' idx':''}" style="--i:${i}"/>`}
 return `<div class="summit ${cls}"><svg class="rings" viewBox="0 0 128 128" aria-hidden="true">${p}</svg><div class="glyph">${G[seed]}</div></div>`}
// the landscape behind the header: drawn once from a fixed seed (same view every visit), colours from CSS tokens so it
// is dawn in light mode and moonlight in dark mode. Ridges fade into valley haze (aerial perspective), a pine line on the
// near ridge gives scale, and the slide on the darkest ridge is engraved: hatched scarp, stippled debris fan.
// The layers assemble once on load; while scrolling the far ridges drift slower than the near ones.
(function(){const el=document.getElementById('hero');if(!el)return;let s=20140;const rnd=()=>(s=(Math.imul(s,1664525)+1013904223)>>>0)/4294967296;
 const W=1200,H=310,ridge=(base,amp,rough,ph)=>{const pts=[];for(let x=-20;x<=W+20;x+=12){
   const y=base-amp*(.6*Math.sin(x/150+ph)+.3*Math.sin(x/61+ph*2.1)+.12*Math.sin(x/23+ph*3.7))-rough*(rnd()-.5);pts.push([x,y])}return pts};
 const pathOf=pts=>'M'+pts.map(p=>p[0]+' '+p[1].toFixed(1)).join('L')+`L${W+20} ${H}L-20 ${H}Z`;
 const yAt=(pts,x)=>{for(let i=1;i<pts.length;i++)if(pts[i][0]>=x){const a=pts[i-1],b=pts[i],f=(x-a[0])/(b[0]-a[0]);return a[1]+(b[1]-a[1])*f}return pts[pts.length-1][1]};
 const L=[ridge(150,34,3,.4),ridge(174,28,4,1.9),ridge(198,24,5,3.1),ridge(222,18,6,4.4),ridge(300,5,2,5.6)];
 let stars='';for(let i=0;i<54;i++){const x=rnd()*W,y=rnd()*150,r=rnd()<.15?1.4:.8;stars+=`<circle class="${i%5?'':'tw'}" cx="${x.toFixed(0)}" cy="${y.toFixed(0)}" r="${r}" fill="var(--star)"/>`}
 // pines along a crest: small conifer silhouettes in clusters, none on the slide itself
 const pines=(pts,x0,x1,hmin,hmax,dens,skip)=>{let o='';for(let x=x0;x<x1;x+=5+rnd()*5){if(rnd()>dens||(x>skip[0]&&x<skip[1]))continue;
   const y=yAt(pts,x)+1.5,h=hmin+rnd()*(hmax-hmin);o+=`M${(x-h*.28).toFixed(1)} ${y.toFixed(1)}L${x.toFixed(1)} ${(y-h).toFixed(1)}L${(x+h*.28).toFixed(1)} ${y.toFixed(1)}Z`}return o};
 let sx=600;for(let x=560;x<=740;x+=4)if(yAt(L[3],x)<yAt(L[3],sx))sx=x;const top=yAt(L[3],sx)+4,lp=[],rp=[],N=14;
 // debris slide seen from across the valley: a crown arc, a chute that narrows, a fan that widens and thins downslope
 for(let i=0;i<=N;i++){const t=i/N,cx=sx+7*t*t,y=top+3+64*t,w=t<.42?10-5.5*(t/.42):4.5+12*Math.pow((t-.42)/.58,1.3);
   lp.push([cx-w-(rnd()-.5)*2.2,y]);rp.push([cx+w+(rnd()-.5)*2.2,y])}
 const P2=q=>q[0].toFixed(1)+' '+q[1].toFixed(1),end=sx+7;
 const scar='M'+P2(lp[0])+'Q'+sx+' '+(top-5)+' '+P2(rp[0])+rp.slice(1).map(q=>'L'+P2(q)).join('')+'Q'+end+' '+(top+74)+' '+P2(lp[N])+lp.slice(0,N).reverse().map(q=>'L'+P2(q)).join('')+'Z';
 const crown='M'+P2(lp[0])+'Q'+sx+' '+(top-5)+' '+P2(rp[0]);
 let deb='';for(let i=0;i<22;i++){const t=.62+rnd()*.38,u=rnd()-.5,k=Math.round(t*N),w=rp[k][0]-lp[k][0];deb+=`<circle cx="${(lp[k][0]+w*(u+.5)).toFixed(1)}" cy="${(top+3+64*t).toFixed(1)}" r="${(.45+rnd()*.7).toFixed(2)}"/>`}
 const g=(k,d,inner)=>`<g class="lay" style="--d:${d}" data-k="${k}">${inner}</g>`;
 const grad=(id,a,b)=>`<linearGradient id="${id}" x1="0" y1="0" x2="0" y2="1"><stop offset=".15" style="stop-color:var(${a})"/><stop offset="1" style="stop-color:var(${b})"/></linearGradient>`;
 el.innerHTML=`<svg viewBox="0 0 ${W} ${H}" preserveAspectRatio="xMidYMax slice"><defs><linearGradient id="hsky" x1="0" y1="0" x2="0" y2="1">
  <stop offset="0" style="stop-color:var(--sky1)"/><stop offset=".4" style="stop-color:var(--sky2)"/><stop offset=".64" style="stop-color:var(--sky3)"/></linearGradient>
  <radialGradient id="hmist"><stop offset="0" style="stop-color:var(--mist);stop-opacity:.55"/><stop offset="1" style="stop-color:var(--mist);stop-opacity:0"/></radialGradient>
  <radialGradient id="hhalo"><stop offset=".25" style="stop-color:var(--sun);stop-opacity:.55"/><stop offset=".55" style="stop-color:var(--sun);stop-opacity:.16"/><stop offset="1" style="stop-color:var(--sun);stop-opacity:0"/></radialGradient>
  ${grad('hr0','--r0','--sky3')}${grad('hr1','--r1','--r0')}${grad('hr2','--r2','--r1')}${grad('hr3','--r3','--r2')}
  <linearGradient id="hscar" x1="0" y1="0" x2="0" y2="1"><stop offset="0" style="stop-color:var(--scar)"/><stop offset=".5" style="stop-color:var(--scar);stop-opacity:.75"/><stop offset="1" style="stop-color:var(--scar);stop-opacity:.15"/></linearGradient></defs>
  <rect width="${W}" height="${H}" fill="url(#hsky)"/>${stars}
  ${g(.42,0,`<g class="sun"><circle cx="548" cy="132" r="120" fill="url(#hhalo)"/><circle cx="548" cy="132" r="30" fill="var(--sun)"/><circle cx="539" cy="124" r="6" fill="var(--crater)"/><circle cx="558" cy="140" r="4" fill="var(--crater)"/><circle cx="556" cy="121" r="2.5" fill="var(--crater)"/></g><path d="${pathOf(L[0])}" fill="url(#hr0)"/>`)}
  ${g(.32,1,`<path d="${pathOf(L[1])}" fill="url(#hr1)"/><ellipse class="mist" cx="560" cy="${yAt(L[1],560)+16}" rx="300" ry="22" fill="url(#hmist)"/>`)}
  ${g(.22,2,`<path d="${pathOf(L[2])}" fill="url(#hr2)"/><path d="${pines(L[2],-20,W+20,4,7,.35,[-1,-1])}" fill="var(--r2)"/><ellipse class="mist b" cx="700" cy="${yAt(L[2],700)+18}" rx="260" ry="18" fill="url(#hmist)"/>`)}
  ${g(.12,3,`<path d="${pathOf(L[3])}" fill="url(#hr3)"/><path d="${pines(L[3],-20,W+20,7,13,.6,[sx-80,sx+66])}" fill="var(--r3)"/>
   <path d="${scar}" fill="url(#hscar)"/><path d="${crown}" fill="none" style="stroke:var(--scar-ink)" stroke-width="1.6" stroke-linecap="round"/><g fill="var(--scar-ink)" opacity=".7">${deb}</g>`)}
  ${g(0,4,`<path d="${pathOf(L[4])}" fill="var(--bg)"/>`)}</svg>`;
 const lays=[...el.querySelectorAll('.lay')];if(matchMedia('(prefers-reduced-motion: reduce)').matches)return;let tick=0;
 addEventListener('scroll',()=>{if(tick)return;tick=requestAnimationFrame(()=>{tick=0;const y=Math.min(scrollY,420);lays.forEach(l=>l.style.transform=`translateY(${(y*l.dataset.k).toFixed(1)}px)`)})},{passive:true})})();
function probs(r){const top=r.ranked[0][0],one=([c,p])=>`<div class="prob ${c===top?'top':''}">${G[c]}<div class="nm">${esc(D.names[c])}<div class="tr"><div class="fl" style="width:${(p*100).toFixed(1)}%"></div></div></div><div class="pc">${pct(p)}</div></div>`;
 const rest=r.ranked.slice(3);
 return r.ranked.slice(0,3).map(one).join('')+(rest.length?`<details class="more"><summary>Show all ${r.ranked.length} types</summary><div class="probs">${rest.map(one).join('')}</div></details>`:'')}
function dims(d){
 if(!d.available)return `<section class="card"><div class="kicker">Dimensions</div><p class="hungr u-m0">${esc(d.reason)}</p></section>`;
 const num=v=>v>=100?Math.round(v).toLocaleString():v, row=(k,v)=>`<div class="drow"><span>${esc(k)}</span><b>${v}</b></div>`;
 let h=`<section class="card"><div class="kicker">Estimated dimensions, depth trust: ${esc(d.depth_trust)}</div>`,more='';
 if(d.overlay)h+=`<img class="dimg" src="${d.overlay}" alt="Measured area outlined">`;
 h+=d.measures.map(m=>row(m.name,`${num(m.value)} ${m.unit} <small>(90%: ${num(m.range[0])}–${num(m.range[1])})</small>`)).join('');
 if(d.size_class){const sp=d.size_class_prob||{};h+=row('Size class (Fell 1994)',esc(d.size_class)+(Object.keys(sp).length>1?' <small>('+Object.entries(sp).map(([k,v])=>esc(k)+' '+Math.round(v*100)+'%').join(', ')+')</small>':''));}
 h+=row('Slope angle',d.slope_angle_deg+'°'+(d.tilt==='phone sensor'?' (phone tilt)':''));
 if(d.grains&&d.grains.reliable)h+=row('Grain size D16 / D50 / D84',`${d.grains.D16_m} / ${d.grains.D50_m} / ${d.grains.D84_m} m <small>(D50 90%: ${d.grains.D50_90ci_m.join('–')})</small>`);
 else if(d.grains)more+=row('Grain size','not resolvable in this photo (take a closer photo of the deposit)');
 if(d.block_count!=null)more+=row('Blocks counted',d.block_count+(d.block_size_class?', largest: '+esc(d.block_size_class):''));
 if(d.travel_angle_deg!=null)more+=row('Travel angle (H/L)',`${d.travel_angle_deg}° (${d.H_over_L})`);
 more+=row('Length / width',d.length_width_ratio)+row('Perimeter',num(d.perimeter_m)+' m')+row('Camera to slope',d.distance_m+' m');
 if(d.alternative){const a=d.alternative;more+=`<p class="hungr u-t2">If it is <b>${esc(D.names[a.label]||a.label)}</b> (${Math.round(a.prob*100)}%): ${a.measures.slice(0,3).map(m=>esc(m.name)+' '+num(m.value)+' '+m.unit).join(', ')}</p>`;}
 h+=`<details class="more"><summary>More measurements</summary>${more}</details>`;
 const notes=[...d.notes,...d.depth_issues.map(x=>'Depth check: '+x)];
 h+=`<details class="more"><summary>How the sizes were measured</summary><p class="hungr u-t1">Scale: ${esc(d.scale_source)}. ${notes.map(esc).join(' ')}</p></details></section>`;
 return h}
function render(r){
 const n=D.names;let h='';
 {
  // a photo that fails the photo check still gets its full result, shown as computed (nothing adjusted),
  // clearly marked as not reliable; the quality band above it (guide.py) says why and how to fix it
  const bp=r.status==='bad_photo';
  const i=D.info[r.label],unsure=r.status==='uncertain',fam=unsure&&r.family?D.families[r.family]:null;
  const gname=fam?D.familyGlyph[r.family]:r.label, sig=(unsure&&!fam)||bp;
  setChip(bp?'bad':sig?'signal':'', bp?'Not reliable':fam?'Landslide family':unsure?'Uncertain':'Most likely type');
  const kicker=bp?'Best guess: photo check failed':fam?'Landslide family':unsure?'Uncertain: most likely':'Most likely type';
  const conf=fam?r.ranked[0][1]+r.ranked[1][1]:r.confidence;
  let note='';
  if(bp) note=`<p class="note"><b>Not reliable.</b> <span>This does not look like a ground photo of a slope</span> (${pct(r.usable)} <span>usable</span>). <span>This is the model's own answer, not adjusted. Retake the photo before relying on it:</span></p><ol class="steps">${D.tips.map(t=>`<li>${esc(t)}</li>`).join('')}</ol>`;
  else if(fam) note=`<p class="note">Clearly a ${esc(r.family)}; the exact type is close between <b>${esc(n[r.ranked[0][0]])}</b> and <b>${esc(n[r.ranked[1][0]])}</b>. Check the points below for both.</p>`;
  else if(unsure) note=`<p class="note">Not confident. Second choice: <b>${esc(n[r.ranked[1][0]])}</b>. Take another photo with the whole slope in view, or check the points below for both types.</p>`;
  h=`<section class="card result${bp?' lowq':''}" aria-live="polite"><div class="rhead">${summit(gname,conf,bp?'bad':sig?'signal':'')}<div>
    <div class="kicker">${kicker}</div><div class="title">${esc(fam||i.title)}</div></div></div>
    ${fam?'':`<p class="hungr u-t2"><span>Hungr et al. 2014</span>: ${esc(i.hungr)}</p>`}
    <div class="meter"><div class="row"><span><span>Model confidence</span>${fam?' <span>(family)</span>':''}: <b class="cband">${conf>=.8?'High':conf>=D.conf?'Moderate':'Low'}</b></span><span class="val">${pct(conf)}</span></div>
    <div class="cscale${bp?' bad':sig?' signal':''}" style="--v:${conf};--c:${D.conf}" aria-hidden="true"><i></i></div>
    <p class="hungr u-t1">Answers below ${pct(D.conf)} are marked uncertain.</p></div>${note}</section>
   <section class="card safety"><h2>${ico('alert')}Safety</h2><p>${esc(i.safety)}</p></section>
   <section class="card"><div class="kicker">All types</div><div class="probs u-t3">${probs(r)}</div></section>
   <section class="card" id="checkcard"><div class="kicker">Check on site</div><h2>${esc(i.title)}</h2><ul class="list">${i.check.map(t=>`<li>${ico('check')}<span>${esc(t)}</span></li>`).join('')}</ul></section>`;
 }
 if(r.vlm){h+=`<section class="card"><div class="kicker">Second opinion from Qwen2.5-VL (zero-shot)</div><h2 style="display:flex;gap:8px;align-items:center">${ico('spark')}${esc(n[r.vlm.label]||r.vlm.label)}, ${pct(r.vlm.confidence)}</h2><p class="hungr u-m0">${esc(r.vlm.description)}</p></section>`;}
 if(r.dimensions)h+=dims(r.dimensions);
 h+=`<p class="meta"><span>Model</span>: <span>${esc(r.model)}</span>, <span>${(r.ms/1000).toFixed(1)} s</span></p>`;
 out.innerHTML=h;}
function loading(){setChip('','Analysing…',true);
 out.innerHTML='<section class="card result" aria-busy="true"><div class="kicker">Analysing photo</div><div class="skel" style="width:60%;height:22px"></div><div class="skel" style="width:85%"></div><div class="skel" style="width:40%"></div></section>';}
function fail(msg){setChip('bad','Error');
 out.innerHTML=`<section class="card bad" role="alert"><div class="kicker">Something went wrong</div><h2>${esc(msg)}</h2><p class="hungr u-m0">Check the connection to the laptop running the app, then try again.</p></section>`;}
// photo pick -> the guidance layer (src/guide.py) runs the photo check, upload, progress and next steps
function go(e){const fs=[...e.target.files];if(!fs.length)return;e.target.value='';const cam=e.target.id==='cam';
 if(App.onPicks&&App.onPicks(fs,cam))return;App.onPick(fs[0],cam)}
document.getElementById('cam').onchange=go;document.getElementById('gal').onchange=go;
window.App={D,esc,render,fail,setChip,shrink,dims,onPick:null};
const demo=new URLSearchParams(location.search).get('demo');
if(demo){const S=D.samples[demo]||D.samples.ok;   // sample result, no photo (presentations, UI checks)
 if(demo==='error')fail('could not read the image (use a JPEG or PNG photo under 40 megapixels)');else render(S);}
"""

PAGE = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>Landslide Type Check</title>
<link rel="icon" type="image/svg+xml" href="favicon.svg">
<link rel="icon" type="image/png" sizes="48x48" href="favicon.ico">
<link rel="apple-touch-icon" href="apple-touch-icon.png">
<meta name="theme-color" content="#a6bccd" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#08101d" media="(prefers-color-scheme: dark)">
<style>__CSS____GCSS____PCSS__.drow{display:flex;justify-content:space-between;align-items:baseline;gap:8px;padding:7px 0;font-size:.92rem}
.drow>span{display:flex;align-items:baseline;flex:1;min-width:0;gap:8px}
.drow>span::after{content:"";flex:1;min-width:14px;border-bottom:2px dotted var(--contour);translate:0 -4px}.drow b{text-align:right;font-weight:600;font-variant-numeric:lining-nums tabular-nums}.drow small{opacity:.75;font-weight:400;font-style:italic}.dimg{width:100%;border-radius:10px;margin:10px 0}.dist{display:block;margin-top:var(--s4);font-size:.9rem;color:var(--ink-2)}.dist .dl{font-weight:650;color:var(--ink)}.dist .hint{display:block;margin-top:var(--s1);font-size:.84rem;color:var(--mute)}.dist input{display:block;width:100%;min-height:var(--tap);margin-top:6px;padding:10px 12px;border-radius:8px;border:1.5px solid var(--edge);transition:border-color .2s ease,box-shadow .25s ease;font:inherit;background:var(--surface);color:inherit}.dist input:focus{border-color:var(--link);outline:none}
</style></head><body>__DEFS__<main>
<div class="hero" id="hero" aria-hidden="true"></div>
<header><div class="logo">__LOGO__</div><div class="brand"><b>Landslide Type Check</b><span>Field classifier after Hungr 2014</span></div><button type="button" id="helpBtn" class="iconbtn" aria-label="Help and guide">?</button><button type="button" id="langBtn" class="iconbtn langbtn" aria-label="Language: English or Hindi">हिं</button></header>
<div id="netbar" class="netbar" role="status" hidden>You are offline. Photos cannot be analysed until the connection is back.</div>
<section class="card panel"><ol class="journey" id="journey" aria-label="Progress"></ol><div class="seg" id="mode" role="group" aria-label="Capture mode"></div><ul class="shots" id="shots"></ul><h2 id="capH">Photograph the slope from below</h2>
<ul class="tips">
<li>__I_pos__<span>Stand at the foot of the slope or across the road, facing up at it.</span></li>
<li>__I_frame__<span>Fit the whole slope: the top (scarp or source) and the bottom (deposit).</span></li>
<li>__I_sun__<span>Hold the phone level, in daylight. One slope per photo.</span></li></ul>
<div class="btns">
<button type="button" class="btn primary wide" id="camBtn">__I_camera__Guided camera</button>
<label class="btn ghost" id="camNat">__I_camera__Phone camera<input id="cam" type="file" accept="image/*" capture="environment"></label>
<label class="btn ghost">__I_image__From gallery<input id="gal" type="file" accept="image/*"></label>
</div>
<label class="dist"><span class="dl">Distance to the slope (optional)</span>
<input id="dist" type="text" inputmode="decimal" autocomplete="off" placeholder="e.g. 40" aria-describedby="disthint"><span class="hint" id="disthint">Makes the sizes more accurate. 40, 40 m or 130 ft all work.</span></label></section>
<figure id="fig"><img id="prev" alt="Your photo"><div id="chip" class="chip"></div></figure>
<div id="out"></div>
<div id="history"></div>
<p class="foot">Decision support only: confirm with a geologist or geotechnical engineer before acting.<br>
Classification after Hungr, Leroueil &amp; Picarelli (2014).</p>
</main><script>__JS__</script><script>__PJS__</script><script>__GJS__</script></body></html>"""


def build_page(logo_svg, info, names, tips, confident_min):
    """The complete HTML page (inline CSS/JS/SVG; no external requests)."""
    top = lambda c, p: [[c, p]] + [[o, round((1 - p) / 5, 4)] for o in names if o != c]  # noqa: E731
    samples = {
        "ok": {"status": "ok", "usable": .94, "label": "translational_slide", "family": None, "confidence": .87,
               "dimensions": {"available": True, "label": "translational_slide", "depth_trust": "medium",
                              "measures": [{"key": "width", "name": "Width (across slope)", "value": 18.4, "unit": "m", "range": [12.0, 24.8]},
                                           {"key": "length", "name": "Length (down slope)", "value": 31.2, "unit": "m", "range": [20.3, 42.1]},
                                           {"key": "area", "name": "Area of the scar", "value": 452.0, "unit": "m²", "range": [203.4, 813.6]},
                                           {"key": "volume", "name": "Volume (Guzzetti 2009 area-volume law)", "unit": "m³", "value": 530.0, "range": [167.0, 1240.0]}],
                              "size_class": "very small", "slope_angle_deg": 34, "travel_angle_deg": 31, "H_over_L": 0.6,
                              "length_width_ratio": 1.7, "perimeter_m": 88.0, "distance_m": 42.0, "tilt": "assumed upright",
                              "grains": {"reliable": False}, "scale_source": "demo values", "notes": [], "depth_issues": []},
               "ranked": [["translational_slide", .87], ["debris_flow", .05], ["fall_topple", .04],
                          ["rotational_slide", .02], ["earth_mud_flow", .01], ["no_landslide", .01]],
               "model": "demo", "ms": 0},
        "uncertain": {"status": "uncertain", "usable": .9, "label": "fall_topple", "family": None, "confidence": .46,
                      "ranked": [["fall_topple", .46], ["no_landslide", .31], ["translational_slide", .12],
                                 ["rotational_slide", .05], ["debris_flow", .04], ["earth_mud_flow", .02]],
                      "model": "demo", "ms": 0},
        "family": {"status": "uncertain", "usable": .92, "label": "debris_flow", "family": "flow", "confidence": .48,
                   "ranked": [["debris_flow", .48], ["earth_mud_flow", .39], ["translational_slide", .07],
                              ["rotational_slide", .03], ["fall_topple", .02], ["no_landslide", .01]],
                   "model": "demo", "ms": 0},
        "bad": {"status": "bad_photo", "usable": .12, "label": "no_landslide", "family": None, "confidence": .5,
                "ranked": top("no_landslide", .5), "model": "demo", "ms": 0},
    }
    data = {"guide": guide.data(), "pano": pano.data(), "glyphs": GLYPHS, "icons": UI_ICONS, "info": info, "names": names, "tips": tips,
            "families": {"flow": "Flow-type landslide", "slide": "Slide (rotational or translational)"},
            "familyGlyph": FAMILY_GLYPH, "conf": confident_min, "samples": samples}
    page = PAGE.replace("__CSS__", CSS).replace("__DEFS__", DEFS).replace("__LOGO__", logo_svg)
    for k, v in UI_ICONS.items():
        page = page.replace(f"__I_{k}__", v.replace("<svg", '<svg class="ico"'))
    # JSON inside <script>: escape "</" so no string can close the script element
    page = page.replace("__GCSS__", guide.CSS).replace("__GJS__", guide.JS).replace("__PCSS__", pano.CSS).replace("__PJS__", pano.JS)
    return page.replace("__JS__", JS.replace("__DATA__", json.dumps(data).replace("</", "<\\/")))
