"""Field app interface: one design system shared by the logo, type glyphs and page.

Palette (from the logo; complementary pair, analogous gradients):
  ground / interface   mint #B4F0D3 -> emerald #34B08C -> deep teal #084045
  signal / movement    amber #FFC862 -> coral #FF745E -> rose #E04282   (only for moving mass and warnings)
  neutrals             warm paper #F5F4EF / ink #13201C (light), #0D1311 / #E6EEEA (dark)
Glyphs: same 64x64 grammar as the logo (contour arcs, round caps): mint->teal ground, the moving
mass in the sunset gradient; transparent backgrounds, nothing painted behind the shapes.
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
/* Design tokens. Flat colours (no decorative gradients: those stay in the logo and type glyphs only), one accent,
   every text colour >= 4.5:1 on its background in light and dark (WCAG AA, checked), spacing on a 4 px scale. */
:root{--teal-950:#082f2a;--teal-800:#0e4d45;--teal-600:#17695a;--teal-400:#4fa587;--sage-300:#8fc9a9;--sage-100:#e4f1e9;
--amber:#f7b74a;--orange:#b13e1f;--ruby:#b8381f;
--bg:#f5f4ef;--surface:#ffffff;--surface-2:#f9f8f4;--ink:#13201c;--ink-2:#3c4b45;--mute:#5d6a64;--line:#e4e2da;
--brand:#17695a;--on-brand:#ffffff;--link:#17695a;--caution:#8a5d00;--dup:#3a62c4;--warn:#b13e1f;--warn-bg:#fdf1ec;--warn-line:#f0c6b8;
--g-ground:#17695a;--g-signal:#d9622b;--g-track:#9fd8bf;--tint-signal:rgba(217,98,43,.09);--tint-ground:rgba(23,105,90,.08);
--shadow:0 1px 2px rgba(16,33,26,.06),0 6px 18px -10px rgba(16,33,26,.16);--r:16px;
--s1:4px;--s2:8px;--s3:12px;--s4:16px;--s5:24px;--s6:32px;--tap:48px;
color-scheme:light}
@media (prefers-color-scheme:dark){:root{--bg:#0c1210;--surface:#141c19;--surface-2:#18221e;--ink:#e6eeea;--ink-2:#bccac3;--mute:#8b9b94;
--line:#2a3833;--brand:#5fd1a8;--on-brand:#062b23;--link:#7fd3b3;--caution:#ffc862;--dup:#9db8ff;--teal-600:#7fd3b3;--warn:#ff9a7a;--orange:#ff9a7a;--warn-bg:#2a1d18;--warn-line:#5a3427;
--g-ground:#5fd1a8;--g-signal:#ff9a7a;--g-track:#2f6b5a;--tint-signal:rgba(255,154,122,.1);--tint-ground:rgba(95,209,168,.09);
--shadow:0 1px 2px rgba(0,0,0,.4),0 8px 22px -12px rgba(0,0,0,.6);color-scheme:dark}}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;min-height:100vh;color:var(--ink);background:var(--bg);font:16px/1.5 ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,"Helvetica Neue",Arial,"Noto Sans","Noto Sans Devanagari",sans-serif}
main{max-width:620px;margin:0 auto;padding:var(--s4) var(--s4) var(--s6)}
svg{display:block}
a{color:var(--link);text-underline-offset:2px}
:focus-visible{outline:3px solid var(--amber);outline-offset:2px}
.ico{width:20px;height:20px;fill:none;stroke:currentColor;stroke-width:1.7;stroke-linecap:round;stroke-linejoin:round;flex:none}
header{display:flex;align-items:center;gap:var(--s2);margin:var(--s1) 0 var(--s4)}
header .logo svg{width:36px;height:36px}
.brand{min-width:0;flex:1}
.brand b{display:block;font-size:1rem;letter-spacing:-.01em;font-weight:720;line-height:1.2}
.brand span{display:block;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;font-size:.8rem;color:var(--mute);margin-top:1px}
.card{background:var(--surface);border:1px solid var(--line);border-radius:var(--r);box-shadow:var(--shadow);padding:var(--s4);margin-top:var(--s3)}
/* section label: plain sentence-case text, not an uppercase eyebrow badge */
.kicker{font-size:.85rem;color:var(--ink-2);font-weight:650;margin:0 0 var(--s1)}
h2{font-size:1.08rem;margin:0 0 var(--s3);letter-spacing:-.01em;line-height:1.3}
.tips{display:grid;gap:var(--s2);margin:0 0 var(--s4);padding:0;list-style:none;counter-reset:tp}
.tips li{display:grid;grid-template-columns:24px 1fr;gap:var(--s2);align-items:start;color:var(--ink-2);font-size:.95rem;counter-increment:tp}
.tips li::before{content:counter(tp);display:grid;place-items:center;width:24px;height:24px;border-radius:50%;background:var(--tint-ground);color:var(--link);font-weight:700;font-size:.8rem}
.tips .ico{display:none}
.btns{display:grid;grid-template-columns:1fr 1fr;gap:var(--s2)}
.btn{position:relative;display:flex;align-items:center;justify-content:center;gap:var(--s2);min-height:52px;padding:var(--s3) var(--s4);border-radius:12px;border:0;
font-weight:650;font-size:.98rem;line-height:1.2;font-family:inherit;cursor:pointer;user-select:none;-webkit-tap-highlight-color:transparent;transition:background-color .15s ease,transform .08s ease}
.btn.primary{color:var(--on-brand);background:var(--brand)}
.btn.primary:hover{background:#0f574a}.btn:active{transform:translateY(1px)}
@media (prefers-color-scheme:dark){.btn.primary:hover{background:#78dcb8}}
.btn.ghost{color:var(--link);background:var(--surface);border:1.5px solid var(--line)}
.btn.ghost:hover{border-color:var(--link)}
.btn.text{background:none;color:var(--link);min-height:var(--tap);text-decoration:underline;text-underline-offset:3px}
.btn[disabled]{opacity:.6;cursor:progress}
.btn input{position:absolute;inset:0;opacity:0;cursor:pointer}
.btn:focus-within{outline:3px solid var(--amber);outline-offset:2px}
.span2{grid-column:1/-1}
figure{position:relative;margin:var(--s3) 0 0;display:none}
figure img{width:100%;max-height:62vh;object-fit:cover;border-radius:var(--r);display:block}
/* status chip on the photo: solid, readable on any photo, no blur */
.chip{position:absolute;left:var(--s3);top:var(--s3);display:inline-flex;align-items:center;gap:7px;padding:6px 11px 6px 9px;border-radius:999px;
font-size:.82rem;font-weight:650;color:#fff;background:rgba(10,22,18,.86)}
.dot{width:8px;height:8px;border-radius:50%;background:var(--sage-300)}
.chip.signal .dot{background:var(--amber)}.chip.bad .dot{background:#ff8a6b}
.spin{width:13px;height:13px;border-radius:50%;border:2px solid rgba(255,255,255,.35);border-top-color:#fff;animation:sp .8s linear infinite}
@keyframes sp{to{transform:rotate(360deg)}}
.result{padding:var(--s4)}
.rhead{display:flex;gap:var(--s3);align-items:center}
.glyph{width:64px;height:64px;flex:none;border-radius:16px;display:grid;place-items:center;background:var(--tint-ground)}
.glyph.signal{background:var(--tint-signal)}.glyph svg{width:48px;height:48px}
.title{font-size:1.45rem;font-weight:750;letter-spacing:-.02em;line-height:1.15;margin:2px 0 var(--s1)}
.hungr{font-size:.86rem;color:var(--mute)}
.meter{margin-top:var(--s4)}
.meter .row{display:flex;justify-content:space-between;align-items:baseline;font-size:.88rem;color:var(--mute)}
.meter .val{font-size:1.5rem;font-weight:750;color:var(--ink);font-variant-numeric:tabular-nums;letter-spacing:-.02em}
.track{height:10px;border-radius:99px;background:var(--line);overflow:hidden;margin-top:6px}
.fill{height:100%;border-radius:99px;background:var(--brand)}
.fill.signal{background:var(--g-signal)}
.result.lowq{border:2px dashed var(--ruby)}.result.lowq .fill{background:var(--ruby)}
.note{margin:var(--s3) 0 0;padding:var(--s3);border-radius:12px;background:var(--surface-2);color:var(--ink-2);font-size:.93rem;border:1px solid var(--line)}
.probs{display:grid;gap:var(--s2);margin-top:var(--s1)}
.prob{display:grid;grid-template-columns:28px 1fr 46px;gap:var(--s2);align-items:center}
.prob svg{width:28px;height:28px}
.prob .nm{font-size:.92rem;color:var(--ink-2);display:flex;flex-direction:column;gap:5px}
.prob .tr{height:7px;border-radius:99px;background:var(--line);overflow:hidden}
.prob .fl{height:100%;border-radius:99px;background:var(--g-track)}
.prob.top .fl{background:var(--brand)}.prob.top .nm{color:var(--ink);font-weight:650}
.prob .pc{text-align:right;font-variant-numeric:tabular-nums;font-size:.9rem;color:var(--mute)}
.prob.top .pc{color:var(--ink);font-weight:700}
details.more{margin-top:var(--s2)}details.more>summary{min-height:var(--tap);display:flex;align-items:center;cursor:pointer;color:var(--link);font-weight:600;font-size:.92rem}
.list{list-style:none;padding:0;margin:0;display:grid;gap:var(--s1)}
.list li{display:flex;gap:var(--s2);align-items:flex-start;font-size:.95rem;color:var(--ink-2)}
.list .ico{color:var(--link);margin-top:1px}
/* safety: a filled warning panel (no accent stripe), the one deliberately different block on the result page */
.safety{background:var(--warn-bg);border-color:var(--warn-line)}
.safety h2{display:flex;gap:var(--s2);align-items:center;color:var(--warn);margin-bottom:var(--s2)}.safety .ico{color:var(--warn)}
.safety p{margin:0;color:var(--ink)}
.card.bad{background:var(--warn-bg);border-color:var(--warn-line)}
ol.steps{margin:var(--s2) 0 0;padding-left:1.2rem;color:var(--ink-2)}ol.steps li{margin:var(--s1) 0}
.skel{height:14px;border-radius:8px;background:var(--line);margin:10px 0;animation:pulse 1.4s ease-in-out infinite}
@keyframes pulse{50%{opacity:.5}}
.foot{margin-top:var(--s5);font-size:.82rem;color:var(--mute);text-align:center;line-height:1.55}
.meta{display:block;margin-top:var(--s4);font-size:.8rem;color:var(--mute);text-align:center}
.meta span+span::before{content:" \\00B7  "}
/* spacing utilities on the 4 px scale (replace one-off inline margins) */
.u-m0{margin:0!important}.u-t1{margin:4px 0 0!important}.u-t2{margin:8px 0 0!important}.u-t3{margin:12px 0 0!important}.u-t4{margin:16px 0 0!important}
.u-b2{margin:0 0 8px!important}.u-b3{margin:0 0 12px!important}.u-tb{margin:4px 0 12px!important}.u-sub{margin:-4px 0 12px!important}.u-blk{display:block!important}
@media (max-width:380px){.btns{grid-template-columns:1fr}.title{font-size:1.28rem}}
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
function probs(r){const top=r.ranked[0][0],one=([c,p])=>`<div class="prob ${c===top?'top':''}">${G[c]}<div class="nm">${esc(D.names[c])}<div class="tr"><div class="fl" style="width:${(p*100).toFixed(1)}%"></div></div></div><div class="pc">${pct(p)}</div></div>`;
 const rest=r.ranked.slice(3);
 return r.ranked.slice(0,3).map(one).join('')+(rest.length?`<details class="more"><summary>Show all ${r.ranked.length} types</summary><div class="probs">${rest.map(one).join('')}</div></details>`:'')}
function dims(d){
 if(!d.available)return `<section class="card"><div class="kicker">Dimensions</div><p class="hungr u-m0">${esc(d.reason)}</p></section>`;
 const num=v=>v>=100?Math.round(v).toLocaleString():v, row=(k,v)=>`<div class="drow"><span>${esc(k)}</span><b>${v}</b></div>`;
 let h=`<section class="card"><div class="kicker">Estimated dimensions · depth trust: ${esc(d.depth_trust)}</div>`,more='';
 if(d.overlay)h+=`<img class="dimg" src="${d.overlay}" alt="Measured area outlined">`;
 h+=d.measures.map(m=>row(m.name,`${num(m.value)} ${m.unit} <small>(90%: ${num(m.range[0])}–${num(m.range[1])})</small>`)).join('');
 if(d.size_class){const sp=d.size_class_prob||{};h+=row('Size class (Fell 1994)',esc(d.size_class)+(Object.keys(sp).length>1?' <small>('+Object.entries(sp).map(([k,v])=>esc(k)+' '+Math.round(v*100)+'%').join(', ')+')</small>':''));}
 h+=row('Slope angle',d.slope_angle_deg+'°'+(d.tilt==='phone sensor'?' (phone tilt)':''));
 if(d.grains&&d.grains.reliable)h+=row('Grain size D16 / D50 / D84',`${d.grains.D16_m} / ${d.grains.D50_m} / ${d.grains.D84_m} m <small>(D50 90%: ${d.grains.D50_90ci_m.join('–')})</small>`);
 else if(d.grains)more+=row('Grain size','not resolvable in this photo (take a closer photo of the deposit)');
 if(d.block_count!=null)more+=row('Blocks counted',d.block_count+(d.block_size_class?' · largest: '+esc(d.block_size_class):''));
 if(d.travel_angle_deg!=null)more+=row('Travel angle (H/L)',`${d.travel_angle_deg}° (${d.H_over_L})`);
 more+=row('Length / width',d.length_width_ratio)+row('Perimeter',num(d.perimeter_m)+' m')+row('Camera to slope',d.distance_m+' m');
 if(d.alternative){const a=d.alternative;more+=`<p class="hungr u-t2">If it is <b>${esc(D.names[a.label]||a.label)}</b> (${Math.round(a.prob*100)}%): ${a.measures.slice(0,3).map(m=>esc(m.name)+' '+num(m.value)+' '+m.unit).join(' · ')}</p>`;}
 h+=`<details class="more"><summary>More measurements</summary>${more}</details>`;
 const notes=[...d.notes,...d.depth_issues.map(x=>'Depth check: '+x)];
 h+=`<p class="hungr u-t2">Scale: ${esc(d.scale_source)}. ${notes.map(esc).join(' ')}</p></section>`;
 return h}
function render(r){
 const n=D.names;let h='';
 {
  // a photo that fails the photo check still gets its full result, shown as computed (nothing adjusted),
  // clearly marked as not reliable; the quality band above it (guide.py) says why and how to fix it
  const bp=r.status==='bad_photo';
  const i=D.info[r.label],unsure=r.status==='uncertain',fam=unsure&&r.family?D.families[r.family]:null;
  const gname=fam?D.familyGlyph[r.family]:r.label, sig=(unsure&&!fam)||bp;
  setChip(bp?'bad':sig?'signal':'', bp?'Not reliable':fam?'Landslide family':unsure?'Uncertain':'Landslide type');
  const kicker=bp?'Best guess · photo check failed':fam?'Landslide family':unsure?'Uncertain: most likely':'Landslide type';
  const conf=fam?r.ranked[0][1]+r.ranked[1][1]:r.confidence;
  let note='';
  if(bp) note=`<p class="note"><b>Not reliable.</b> <span>This does not look like a ground photo of a slope</span> (${pct(r.usable)} <span>usable</span>). <span>This is the model's own answer, not adjusted. Retake the photo before relying on it:</span></p><ol class="steps">${D.tips.map(t=>`<li>${esc(t)}</li>`).join('')}</ol>`;
  else if(fam) note=`<p class="note">Clearly a ${esc(r.family)}; the exact type is close between <b>${esc(n[r.ranked[0][0]])}</b> and <b>${esc(n[r.ranked[1][0]])}</b>. Check the points below for both.</p>`;
  else if(unsure) note=`<p class="note">Not confident. Second choice: <b>${esc(n[r.ranked[1][0]])}</b>. Take another photo with the whole slope in view, or check the points below for both types.</p>`;
  h=`<section class="card result${bp?' lowq':''}" aria-live="polite"><div class="rhead"><div class="glyph ${gname==='no_landslide'?'':'signal'}">${G[gname]}</div><div>
    <div class="kicker">${kicker}</div><div class="title">${esc(fam||i.title)}</div>
    <div class="hungr">${fam?'':'Hungr et al. 2014 · '+esc(i.hungr)}</div></div></div>
    <div class="meter"><div class="row"><span>Confidence${fam?' (family)':''}</span><span class="val">${pct(conf)}</span></div>
    <div class="track"><div class="fill ${sig?'signal':''}" style="width:${(conf*100).toFixed(1)}%"></div></div></div>${note}</section>
   <section class="card safety"><h2>${ico('alert')}Safety</h2><p>${esc(i.safety)}</p></section>
   <section class="card"><div class="kicker">All types</div><div class="probs u-t3">${probs(r)}</div></section>
   <section class="card" id="checkcard"><div class="kicker">Check on site</div><h2>${esc(i.title)}</h2><ul class="list">${i.check.map(t=>`<li>${ico('check')}<span>${esc(t)}</span></li>`).join('')}</ul></section>`;
 }
 if(r.vlm){h+=`<section class="card"><div class="kicker">Second opinion · Qwen2.5-VL (zero-shot)</div><h2 style="display:flex;gap:8px;align-items:center">${ico('spark')}${esc(n[r.vlm.label]||r.vlm.label)} · ${pct(r.vlm.confidence)}</h2><p class="hungr u-m0">${esc(r.vlm.description)}</p></section>`;}
 if(r.dimensions)h+=dims(r.dimensions);
 h+=`<p class="meta"><span>${esc(r.model)}</span><span>${(r.ms/1000).toFixed(1)} s</span><span>confident ≥ ${pct(D.conf)}</span></p>`;
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
<meta name="theme-color" content="#0e4d45">
<style>__CSS____GCSS____PCSS__.drow{display:flex;justify-content:space-between;gap:12px;padding:8px 0;border-bottom:1px solid var(--line);font-size:.92rem}.drow b{text-align:right;font-weight:600}.drow small{opacity:.65;font-weight:400}.dimg{width:100%;border-radius:10px;margin:10px 0}.dist{display:block;margin-top:var(--s4);font-size:.9rem;color:var(--ink-2)}.dist .dl{font-weight:650;color:var(--ink)}.dist .hint{display:block;margin-top:var(--s1);font-size:.84rem;color:var(--mute)}.dist input{display:block;width:100%;min-height:var(--tap);margin-top:6px;padding:10px 12px;border-radius:10px;border:1.5px solid var(--line);font:inherit;background:var(--surface);color:inherit}.dist input:focus{border-color:var(--link);outline:none}
</style></head><body>__DEFS__<main>
<header><div class="logo">__LOGO__</div><div class="brand"><b>Landslide Type Check</b><span>Field classifier &middot; Hungr 2014</span></div><button type="button" id="helpBtn" class="iconbtn" aria-label="Help and guide">?</button><button type="button" id="langBtn" class="iconbtn langbtn" aria-label="Language: English or Hindi">हिं</button></header>
<div id="netbar" class="netbar" role="status" hidden>You are offline. Photos cannot be analysed until the connection is back.</div>
<section class="card"><ol class="journey" id="journey" aria-label="Progress"></ol><div class="seg" id="mode" role="group" aria-label="Capture mode"></div><ul class="shots" id="shots"></ul><h2 id="capH">Photograph the slope from below</h2>
<ul class="tips">
<li>__I_pos__<span>Stand at the foot of the slope or across the road, facing up at it.</span></li>
<li>__I_frame__<span>Fit the whole slope: the top (scarp or source) and the bottom (deposit).</span></li>
<li>__I_sun__<span>Hold the phone level, in daylight. One slope per photo.</span></li></ul>
<div class="btns">
<label class="btn primary">__I_camera__Take photo<input id="cam" type="file" accept="image/*" capture="environment"></label>
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
