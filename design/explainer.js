// Animated fire-safety explainer Reels (1080x1920): flat illustration + one short line per beat,
// ending on a "share this" StationHQ card. Original art drawn here in SVG; sound is synthesized ticks.
// Usage: node explainer.js [name]   -> ../content/explainers/<name>.mp4  (OUT=dir to override)
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');
const { css, LOGO } = require('./gen.js');

const FPS = 30;

// show element from s to e (ms) inside a timeline of length T; s=0 means visible on frame 1
const timelineJs = (T) => `
const T=${T};
function show(id,s,e,inMs=250,outMs=250,from='translateY(30px)'){const el=document.getElementById(id);const o=x=>Math.min(1,Math.max(0,x/T));
 const f=(op,tr,off)=>from===null?{opacity:op,offset:off}:{opacity:op,transform:tr,offset:off};  // from=null: fade only (keeps other motion)
 const k=[];if(s>0){k.push(f(0,from,0),f(0,from,o(s)));}
 k.push(f(1,'none',o(s+(s>0?inMs:0))));
 if(e<T){k.push(f(1,'none',o(e-outMs)),f(0,'none',o(e)),f(0,'none',1));}else k.push(f(1,'none',1));
 el.animate(k,{duration:T,fill:'both'});}
function at(id,kf,delay,dur,ease){document.getElementById(id).animate(kf,{duration:dur,delay,fill:'both',easing:ease||'cubic-bezier(.2,.8,.2,1)'});}
`;

const page = (body, T, script) => `<style>${css}
body{width:1080px;height:1920px;background:#0F1B2A}
.bg,.grid{display:none}
.hdr{position:absolute;top:100px;left:0;right:0;display:flex;justify-content:center;align-items:center;gap:18px;font-family:BC;font-weight:700;font-size:44px;letter-spacing:3px;color:#fff}
.hdr img{width:96px}.hdr b{color:var(--red)}
.hl{position:absolute;left:70px;right:70px;top:300px;text-align:center;font-family:BC;font-weight:800;text-transform:uppercase;font-size:118px;line-height:.92;color:#fff;opacity:0}
.hl em{font-style:normal;color:#FF5A3C}
.ill *{transform-box:fill-box;transform-origin:center}
.ill{position:absolute;left:0;top:640px;width:1080px;height:900px}
.fact{position:absolute;left:80px;right:80px;top:270px;background:rgba(255,255,255,.07);border:2px solid rgba(255,255,255,.14);border-radius:30px;padding:40px 44px;font-size:54px;line-height:1.35;color:#E6EAF0;opacity:0}
.fact b{color:#fff}.fact small{display:block;margin-top:14px;font-size:32px;color:#8FA0B5}
.endbg{position:absolute;inset:0;opacity:0;z-index:4;background:
  radial-gradient(760px 640px at 50% 36%,rgba(224,49,43,.42),transparent 70%),
  radial-gradient(900px 700px at 50% 110%,rgba(224,49,43,.18),transparent 70%),#0B0D10}
.endbg:after{content:"";position:absolute;inset:0;background-image:linear-gradient(rgba(255,255,255,.03) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.03) 1px,transparent 1px);background-size:60px 60px}
.end{position:absolute;left:0;right:0;top:330px;text-align:center;opacity:0;z-index:5}
.end img{width:460px;filter:drop-shadow(0 0 60px rgba(255,59,31,.55))}
.end .u{font-family:BC;font-weight:800;font-size:104px;line-height:.95;margin-top:50px;color:#fff;text-transform:uppercase}
.end .u em{font-style:normal;color:var(--red)}
.end .btn{display:inline-block;margin-top:56px;background:var(--red);color:#fff;font-family:BC;font-weight:700;font-size:54px;letter-spacing:4px;padding:24px 56px;border-radius:20px;box-shadow:0 18px 50px rgba(224,49,43,.45)}
.end .s{font-size:36px;color:#9AA3AF;margin-top:40px}
.chev{z-index:6}
.chev{position:absolute;left:0;right:0;bottom:0;height:26px;background:repeating-linear-gradient(-45deg,var(--red) 0 38px,#F2C230 38px 76px)}
</style>
<div class=hdr><img src="${LOGO}">STATION<b>HQ</b></div><div class=chev></div>
${body}
<script>${timelineJs(T)}${script}</script>`;

// ---------------- Space heaters ----------------
const heaterSvg = `
<svg class=ill viewBox="0 0 1080 900">
 <defs>
  <radialGradient id=glow><stop offset="0" stop-color="#FF7A2F" stop-opacity=".75"/><stop offset="1" stop-color="#FF7A2F" stop-opacity="0"/></radialGradient>
 </defs>
 <rect x="0" y="0" width="1080" height="700" fill="#14243A"/>
 <rect x="0" y="700" width="1080" height="200" fill="#0B1522"/>
 <rect x="0" y="696" width="1080" height="8" fill="#22354F"/>
 <!-- wall outlet -->
 <g id=outlet><rect x="120" y="330" width="130" height="190" rx="18" fill="#EDE6D6"/>
  <rect x="160" y="360" width="50" height="56" rx="10" fill="#C9C0AE"/><rect x="160" y="436" width="50" height="56" rx="10" fill="#C9C0AE"/>
  <rect x="172" y="374" width="7" height="22" rx="3" fill="#5A5246"/><rect x="191" y="374" width="7" height="22" rx="3" fill="#5A5246"/>
  <rect x="172" y="450" width="7" height="22" rx="3" fill="#5A5246"/><rect x="191" y="450" width="7" height="22" rx="3" fill="#5A5246"/></g>
 <!-- power strip on the floor -->
 <g id=strip><rect x="80" y="745" width="330" height="56" rx="14" fill="#E6E8EC"/>
  ${[0, 1, 2, 3, 4].map(i => `<rect x="${110 + i * 52}" y="760" width="32" height="26" rx="6" fill="#B8BDC6"/>`).join('')}
  <rect x="372" y="758" width="24" height="30" rx="5" fill="#E0312B"/></g>
 <path id=stripcord d="M 92 773 C 40 773, 60 500, 185 450" stroke="#D9DCE2" stroke-width="10" fill="none"/>
 <!-- heat glow + heater -->
 <circle id=glowc cx="560" cy="560" r="300" fill="url(#glow)"/>
 <g id=heater><rect x="450" y="420" width="220" height="270" rx="34" fill="#E9ECF0"/>
  <rect x="478" y="450" width="164" height="150" rx="16" fill="#3A2A22"/>
  <g id=coils>${[0, 1, 2, 3, 4, 5].map(i => `<rect x="490" y="${462 + i * 22}" width="140" height="10" rx="5" fill="#FF7A2F"/>`).join('')}</g>
  <circle cx="512" cy="640" r="16" fill="#9AA3AF"/><rect x="560" y="630" width="70" height="22" rx="8" fill="#E0312B"/>
  <rect x="470" y="688" width="40" height="14" rx="5" fill="#9AA3AF"/><rect x="610" y="688" width="40" height="14" rx="5" fill="#9AA3AF"/></g>
 <g id=waves stroke="#FF7A2F" stroke-width="9" fill="none" stroke-linecap="round">
  <path d="M 520 400 c -16 -26 16 -40 0 -66"/><path d="M 560 390 c -16 -26 16 -40 0 -66"/><path d="M 600 400 c -16 -26 16 -40 0 -66"/></g>
 <!-- cords: heater -> strip (bad) and heater -> wall (good) -->
 <path id=cordbad d="M 455 660 C 400 700, 420 770, 396 773" stroke="#D9DCE2" stroke-width="10" fill="none"/>
 <path id=cordgood d="M 455 660 C 330 640, 300 470, 196 470" stroke="#D9DCE2" stroke-width="10" fill="none"/>
 <rect id=plug x="168" y="452" width="40" height="36" rx="8" fill="#D9DCE2"/>
 <!-- couch (things that burn) -->
 <g id=couch><rect x="720" y="520" width="300" height="120" rx="30" fill="#5B7BA6"/><rect x="700" y="590" width="340" height="100" rx="30" fill="#6F8FBA"/>
  <rect x="690" y="560" width="60" height="140" rx="26" fill="#5B7BA6"/><rect x="990" y="560" width="60" height="140" rx="26" fill="#5B7BA6"/>
  <rect x="720" y="690" width="20" height="14" fill="#33465F"/><rect x="1000" y="690" width="20" height="14" fill="#33465F"/></g>
 <!-- 3 ft marker -->
 <g id=ruler><line x1="680" y1="760" x2="900" y2="760" stroke="#F2C230" stroke-width="8" stroke-dasharray="18 12"/>
  <path d="M 680 740 v 40 M 900 740 v 40" stroke="#F2C230" stroke-width="8"/>
  <text x="790" y="840" text-anchor="middle" font-family="BC" font-weight="800" font-size="84" fill="#F2C230">3 FT</text></g>
 <!-- verdict badges -->
 <g id=xstrip><circle cx="240" cy="773" r="70" fill="none" stroke="#E0312B" stroke-width="12"/><path d="M 195 728 l 90 90 M 285 728 l -90 90" stroke="#E0312B" stroke-width="12"/></g>
 <g id=chkwall><circle cx="300" cy="350" r="44" fill="#2EA05A"/><path d="M 280 350 l 14 14 l 26 -28" stroke="#fff" stroke-width="10" fill="none" stroke-linecap="round" stroke-linejoin="round"/></g>
 <g id=chkft><circle cx="790" cy="440" r="44" fill="#2EA05A"/><path d="M 770 440 l 14 14 l 26 -28" stroke="#fff" stroke-width="10" fill="none" stroke-linecap="round" stroke-linejoin="round"/></g>
 <!-- off / sleep -->
 <g id=moon><circle cx="900" cy="170" r="70" fill="#F2E7B8"/><circle cx="935" cy="145" r="62" fill="#14243A"/>
  <text x="980" y="110" font-family="BC" font-weight="800" font-size="56" fill="#F2E7B8">z</text><text x="1020" y="70" font-family="BC" font-weight="800" font-size="40" fill="#F2E7B8">z</text></g>
</svg>`;

const HEATER_T = 21000;
const heater = page(`
<div class=hl id=h1>Space heater<br><em>running?</em></div>
<div class=hl id=h2>Give it <em>3 feet</em><br>on every side</div>
<div class=hl id=h3><em>Never</em> a<br>power strip</div>
<div class=hl id=h4>Straight into<br><em>the wall</em></div>
<div class=hl id=h5>Off when you<br><em>leave or sleep</em></div>
${heaterSvg}
<div class=fact id=fact><b>Portable heaters cause just 3% of home heating fires, but 41% of the deadly ones.</b><small>Source: U.S. Fire Administration</small></div>
<div class=endbg id=endbg></div>
<div class=end id=end><img src="${LOGO}"><div class=u>Share this with<br><em>your community</em></div><div class=btn>STATIONHQ.APP</div><div class=s>From your firefighters at StationHQ</div></div>
`, HEATER_T, `
show('h1',0,3200);show('h2',3200,7000);show('h3',7000,9800);show('h4',9800,12600);show('h5',12600,15800);
show('fact',15800,18800,300,300);
show('endbg',18600,${HEATER_T},500,0,null);show('end',18900,${HEATER_T},450,0,'scale(.94)');
// illustration stays up until the end card
['outlet','heater','couch'].forEach(id=>show(id,0,18800,0,400,null));
// the power strip leaves when the heater goes straight into the wall
show('strip',0,10000,0,400,null);show('stripcord',0,10000,0,400,null);
// heat: glow + waves pulse while it's on, off at the 'leave or sleep' beat
document.getElementById('glowc').animate([{transform:'scale(.85)'},{transform:'scale(1.1)'},{transform:'scale(.85)'}],{duration:1200,iterations:12});
show('glowc',0,13600,0,700,null);show('coils',0,13600,0,700,null);show('waves',0,13600,0,700,null);
document.getElementById('waves').animate([{transform:'translateY(0)'},{transform:'translateY(-14px)'},{transform:'translateY(0)'}],{duration:900,iterations:15});
// 3 ft: couch slides away, ruler + check
at('couch',[{transform:'translateX(-120px)'},{transform:'translateX(-120px)'}],0,1);
at('couch',[{transform:'translateX(-120px)'},{transform:'translateX(0)'}],3700,900);
show('ruler',4600,7000);show('chkft',5200,7000,250,250,'scale(.4)');
// power strip bad -> wall good
show('cordbad',0,9800,0,300);show('xstrip',7500,9800,250,250,'scale(.4)');
show('cordgood',9800,18800,300,400);show('plug',9800,18800,300,400);show('chkwall',10400,12600,250,250,'scale(.4)');
show('moon',12900,15800,350,300,'translateY(-30px)');
`);

// ---------------- shared pieces ----------------
const END = `<div class=endbg id=endbg></div>
<div class=end id=end><img src="${LOGO}"><div class=u>Share this with<br><em>your community</em></div><div class=btn>STATIONHQ.APP</div><div class=s>From your firefighters at StationHQ</div></div>`;
const endJs = (s, T) => `show('endbg',${s - 200},${T},500,0,null);show('end',${s + 100},${T},450,0,'scale(.94)');`;
const CHK = (id, cx, cy) => `<g id=${id}><circle cx="${cx}" cy="${cy}" r="46" fill="#2EA05A"/><path d="M ${cx - 20} ${cy} l 14 14 l 26 -28" stroke="#fff" stroke-width="10" fill="none" stroke-linecap="round" stroke-linejoin="round"/></g>`;
const XM = (id, cx, cy, r = 70) => `<g id=${id}><circle cx="${cx}" cy="${cy}" r="${r}" fill="none" stroke="#E0312B" stroke-width="12"/><path d="M ${cx - r * .64} ${cy - r * .64} l ${r * 1.28} ${r * 1.28} M ${cx + r * .64} ${cy - r * .64} l ${-r * 1.28} ${r * 1.28}" stroke="#E0312B" stroke-width="12"/></g>`;
const RULER = (id, x1, x2, y, label) => `<g id=${id}><line x1="${x1}" y1="${y}" x2="${x2}" y2="${y}" stroke="#F2C230" stroke-width="8" stroke-dasharray="18 12"/>
 <path d="M ${x1} ${y - 20} v 40 M ${x2} ${y - 20} v 40" stroke="#F2C230" stroke-width="8"/>
 <text x="${(x1 + x2) / 2}" y="${y + 80}" text-anchor="middle" font-family="BC" font-weight="800" font-size="80" fill="#F2C230">${label}</text></g>`;
const ROOM = `<rect x="0" y="0" width="1080" height="700" fill="#14243A"/><rect x="0" y="700" width="1080" height="200" fill="#0B1522"/><rect x="0" y="696" width="1080" height="8" fill="#22354F"/>`;
// one transform animation across the whole timeline: [[ms, transform], ...]
const moveJs = (id, T, steps) => `document.getElementById('${id}').animate([${steps.map(([t, tr]) => `{transform:'${tr}',offset:${Math.min(1, t / T).toFixed(4)}}`).join(',')}],{duration:${T},fill:'both'});`;

// ---------------- Portable generators (CPSC) ----------------
const GEN_T = 19500;
const fumes = (id, pts) => `<g id=${id} fill="#9AA3AF">${pts.map(([x, y, r]) => `<circle cx="${x}" cy="${y}" r="${r}" opacity=".55"/>`).join('')}</g>`;
const generator = page(`
<div class=hl id=h1>Power's out.<br><em>Generator time?</em></div>
<div class=hl id=h2><em>Never</em> in the<br>garage</div>
<div class=hl id=h3><em>Not</em> by an<br>open window</div>
<div class=hl id=h4><em>20 feet</em> from<br>the house</div>
<svg class=ill viewBox="0 0 1080 900">${ROOM}
 <polygon points="20,300 280,140 540,300" fill="#1E2C40"/>
 <rect x="40" y="300" width="480" height="400" fill="#2B3E5A"/>
 <rect x="90" y="380" width="150" height="130" rx="8" fill="#0E1826"/><rect id=winopen x="96" y="386" width="138" height="60" fill="#0B1522"/>
 <rect x="90" y="440" width="150" height="8" fill="#3E5677"/>
 <rect x="290" y="450" width="210" height="250" fill="#0B1522"/><rect x="290" y="440" width="210" height="14" fill="#3E5677"/>
 <g id=gen><g transform="translate(0,590)">
  <rect x="0" y="0" width="160" height="100" rx="12" fill="#F2C230"/><rect x="18" y="18" width="80" height="50" rx="8" fill="#2B2B2B"/>
  <rect x="112" y="22" width="30" height="16" rx="4" fill="#2B2B2B"/><circle cx="30" cy="104" r="16" fill="#2B2B2B"/><circle cx="130" cy="104" r="16" fill="#2B2B2B"/>
  <rect x="150" y="10" width="26" height="14" rx="4" fill="#5A5A5A"/></g></g>
 ${fumes('f1', [[350, 560, 40], [410, 520, 52], [460, 580, 44], [330, 500, 36], [440, 480, 40]])}
 ${fumes('f2', [[230, 560, 34], [200, 500, 42], [170, 450, 36], [140, 420, 30]])}
 ${fumes('f3', [[1050, 560, 30], [1010, 520, 38], [1060, 480, 26]])}
 ${XM('x1', 395, 380, 80)}${XM('x2', 165, 300, 70)}
 ${RULER('rul', 520, 880, 780, '20 FT')}${CHK('c1', 960, 520)}
</svg>
<div class=fact id=fact><b>About 85 people die each year from carbon monoxide from portable generators.</b><small>Source: U.S. Consumer Product Safety Commission</small></div>
${END}`, GEN_T, `
show('h1',0,3000);show('h2',3000,6200);show('h3',6200,9600);show('h4',9600,13000);show('fact',13000,16500,300,300);
${moveJs('gen', GEN_T, [[0, 'translateX(320px)'], [6200, 'translateX(320px)'], [6900, 'translateX(80px)'], [9600, 'translateX(80px)'], [10400, 'translateX(860px)'], [GEN_T, 'translateX(860px)']])}
show('f1',3300,6200,500,300,'translateY(40px)');show('x1',3800,6200,250,250,'scale(.4)');
show('f2',6900,9600,500,300,'translate(30px,40px)');show('x2',7400,9600,250,250,'scale(.4)');
show('f3',10500,16500,500,400,'translateX(-40px)');show('rul',10600,13000);show('c1',11200,13000,250,250,'scale(.4)');
['f1','f2','f3'].forEach(id=>document.getElementById(id).animate([{transform:'translateY(0)'},{transform:'translateY(-18px)'},{transform:'translateY(0)'}],{duration:1400,iterations:14,composite:'add'}));
${endJs(16500, GEN_T)}`);

// ---------------- Clothes dryers (USFA) ----------------
const DRY_T = 19500;
const dryer = page(`
<div class=hl id=h1>Dryer running<br><em>all winter?</em></div>
<div class=hl id=h2>Clean the lint<br>filter <em>every load</em></div>
<div class=hl id=h3>Vent hose <em>not<br>crushed</em> or kinked</div>
<div class=hl id=h4>Outside flap<br>should <em>open</em></div>
<svg class=ill viewBox="0 0 1080 900">${ROOM}
 <rect x="930" y="300" width="150" height="400" fill="#1A2D47"/><rect x="930" y="300" width="8" height="400" fill="#22354F"/>
 <path id=hosebad d="M 700 440 l 40 -30 l 20 40 l 30 -50 l 25 45 l 30 -40 l 20 30 l 45 -30" stroke="#B8BDC6" stroke-width="34" fill="none" stroke-linejoin="round"/>
 <path id=hosegood d="M 700 430 C 790 380, 860 380, 935 400" stroke="#B8BDC6" stroke-width="34" fill="none" stroke-linecap="round"/>
 <g id=flapbox><rect x="1000" y="360" width="70" height="90" rx="8" fill="#C9CFD8"/>
  <rect id=flap x="1006" y="366" width="58" height="78" rx="6" fill="#9AA3AF"/></g>
 <g id=air stroke="#D9E2EE" stroke-width="8" fill="none" stroke-linecap="round" opacity=".8">
  <path d="M 1040 470 c 10 20 -10 30 0 50"/><path d="M 1060 470 c 10 20 -10 30 0 50"/></g>
 <rect x="380" y="330" width="320" height="370" rx="26" fill="#E9ECF0"/><rect x="380" y="330" width="320" height="70" rx="26" fill="#D3D8DF"/>
 <circle cx="430" cy="365" r="16" fill="#9AA3AF"/><rect x="520" y="355" width="140" height="20" rx="8" fill="#2EA05A" opacity=".8"/>
 <circle cx="540" cy="545" r="112" fill="#C3C9D2"/><circle cx="540" cy="545" r="90" fill="#25344A"/>
 <g id=drum>${[0, 1, 2, 3].map(i => `<circle cx="${540 + 45 * Math.cos(i * 1.57)}" cy="${545 + 45 * Math.sin(i * 1.57)}" r="26" fill="${['#E0312B', '#5B7BA6', '#F2C230', '#9AA3AF'][i]}"/>`).join('')}</g>
 <g id=lint><rect x="465" y="120" width="150" height="200" rx="16" fill="#B8BDC6"/><rect x="480" y="135" width="120" height="170" rx="10" fill="#7E8794"/>
  <g id=fuzz fill="#D9D2C4">${[[505, 170, 22], [550, 160, 26], [585, 190, 20], [520, 220, 26], [570, 240, 24], [510, 275, 20], [575, 280, 18]].map(([x, y, r]) => `<circle cx="${x}" cy="${y}" r="${r}"/>`).join('')}</g></g>
 ${CHK('c1', 680, 160)}${XM('x1', 820, 420, 80)}${CHK('c2', 830, 300)}${CHK('c3', 1000, 240)}
</svg>
<div class=fact id=fact><b>Not cleaning is the #1 cause of dryer fires, and they peak in January.</b><small>Source: U.S. Fire Administration</small></div>
${END}`, DRY_T, `
show('h1',0,3000);show('h2',3000,6800);show('h3',6800,10200);show('h4',10200,13200);show('fact',13200,16500,300,300);
document.getElementById('drum').animate([{transform:'rotate(0deg)'},{transform:'rotate(360deg)'}],{duration:1600,iterations:13});
document.getElementById('drum').style.transformOrigin='540px 545px';document.getElementById('drum').style.transformBox='view-box';
show('lint',3200,6800,450,300,'translateY(160px)');show('fuzz',0,4900,0,500,null);show('c1',5200,6800,250,250,'scale(.4)');
show('hosebad',0,8700,0,300,null);show('x1',7300,8700,250,250,'scale(.4)');show('hosegood',8700,16500,300,400,null);show('c2',9100,10200,250,250,'scale(.4)');
${moveJs('flap', DRY_T, [[0, 'none'], [10600, 'none'], [11100, 'translateX(46px) scaleX(.2)'], [DRY_T, 'translateX(46px) scaleX(.2)']])}
show('air',11100,16500,300,300,null);show('c3',11500,13200,250,250,'scale(.4)');
document.getElementById('air').animate([{transform:'translateY(0)'},{transform:'translateY(16px)'},{transform:'translateY(0)'}],{duration:700,iterations:28,composite:'add'});
${endJs(16500, DRY_T)}`);

// ---------------- Candles (USFA) ----------------
const CAN_T = 19500;
const candle = page(`
<div class=hl id=h1>Lighting<br><em>candles?</em></div>
<div class=hl id=h2><em>12 inches</em> from<br>anything that burns</div>
<div class=hl id=h3>Sturdy holder that<br><em>won't tip</em></div>
<div class=hl id=h4>Or go<br><em>flameless</em></div>
<svg class=ill viewBox="0 0 1080 900">${ROOM}
 <rect x="60" y="80" width="300" height="420" rx="10" fill="#0E1826"/><rect x="60" y="80" width="300" height="420" rx="10" fill="none" stroke="#3E5677" stroke-width="10"/>
 <rect x="40" y="60" width="420" height="16" rx="8" fill="#6B5A48"/>
 <g id=curtain fill="#B5443B"><path d="M 50 76 h 120 c -20 160 30 300 0 480 h -120 z"/><path d="M 330 76 h 120 c -30 170 20 300 -10 480 h -110 c 20 -170 -20 -320 0 -480 z"/></g>
 <rect x="200" y="600" width="760" height="34" rx="10" fill="#6B5A48"/><rect x="240" y="634" width="30" height="66" fill="#54463A"/><rect x="890" y="634" width="30" height="66" fill="#54463A"/>
 <g id=cmove><g id=cwob>
  <rect x="-70" y="548" width="140" height="52" rx="14" fill="#9AA3AF"/>
  <rect x="-38" y="400" width="76" height="150" rx="12" fill="#F2E7D0"/>
  <rect x="-4" y="378" width="8" height="24" fill="#3A2A22"/>
  <path id=flame d="M 0 300 C 30 340, 26 372, 0 384 C -26 372, -30 340, 0 300 z" fill="#FF9A3C"/>
  <circle id=led cx="0" cy="350" r="30" fill="#FFE08A"/>
  <circle id=ledglow cx="0" cy="350" r="80" fill="#FFE08A" opacity=".25"/>
 </g></g>
 ${RULER('rul', 460, 740, 760, '12 IN')}${CHK('c1', 600, 250)}${CHK('c2', 800, 450)}${CHK('c3', 800, 300)}
</svg>
<div class=fact id=fact><b>Almost half of December home decoration fires are started by candles.</b><small>Source: U.S. Fire Administration</small></div>
${END}`, CAN_T, `
show('h1',0,3000);show('h2',3000,6500);show('h3',6500,10000);show('h4',10000,13300);show('fact',13300,16500,300,300);
${moveJs('cmove', CAN_T, [[0, 'translateX(520px)'], [3400, 'translateX(520px)'], [4300, 'translateX(740px)'], [CAN_T, 'translateX(740px)']])}
document.getElementById('flame').animate([{transform:'scale(1,1)'},{transform:'scale(.9,1.12)'},{transform:'scale(1.05,.95)'},{transform:'scale(1,1)'}],{duration:700,iterations:20});
document.getElementById('flame').style.transformOrigin='center bottom';
${moveJs('cwob', CAN_T, [[0, 'none'], [6700, 'none'], [7000, 'rotate(-7deg)'], [7300, 'rotate(6deg)'], [7600, 'rotate(-4deg)'], [7900, 'none'], [CAN_T, 'none']])}
document.getElementById('cwob').style.transformOrigin='0px 600px';document.getElementById('cwob').style.transformBox='view-box';
show('rul',4400,6500);show('c1',4900,6500,250,250,'scale(.4)');show('c2',8400,10000,250,250,'scale(.4)');
show('flame',0,10400,0,300,null);show('led',10400,16500,300,300,null);show('ledglow',10400,16500,400,300,null);show('c3',11000,13300,250,250,'scale(.4)');
${endJs(16500, CAN_T)}`);

const EXPLAINERS = {
  heaters: { html: heater, secs: HEATER_T / 1000, sounds: [3.2, 4.6, 5.2, 7.0, 7.5, 9.8, 10.4, 12.6, 15.8, 18.8],
    caption: `Space heater season. 🔥\n\nGive it 3 feet on every side, plug it straight into the wall (never a power strip or extension cord), and turn it off when you leave the room or go to bed.\n\nPortable heaters cause just 3% of home heating fires, but 41% of the deadly ones (U.S. Fire Administration).\n\nShare this with your community. Departments, feel free to repost to your story.\n\n#firesafety #spaceheater #winterfiresafety #fireprevention #firedepartment #stationhq` },
  generator: { html: generator, secs: GEN_T / 1000, sounds: [3.0, 3.8, 6.2, 7.4, 9.6, 10.6, 11.2, 13.0, 16.5],
    caption: `Power out? Before you fire up the generator. ⚡\n\nRun it outside only, at least 20 feet from the house. Never in the garage, basement or on the porch, and an open door or window won't vent it.\n\nAbout 85 people die each year from carbon monoxide from portable generators (U.S. Consumer Product Safety Commission).\n\nShare this with your community. Departments, feel free to repost to your story.\n\n#generatorsafety #carbonmonoxide #winterstorm #firesafety #firedepartment #stationhq` },
  dryer: { html: dryer, secs: DRY_T / 1000, sounds: [3.0, 5.2, 6.8, 7.3, 9.1, 10.2, 11.5, 13.2, 16.5],
    caption: `Dryers work overtime this time of year. 🧺\n\nClean the lint filter every load, make sure the vent hose behind it isn't crushed or kinked, and check that the outside flap opens when it runs.\n\nNot cleaning is the #1 cause of dryer fires, and they peak in January (U.S. Fire Administration).\n\nShare this with your community. Departments, feel free to repost to your story.\n\n#dryerfire #firesafety #fireprevention #firedepartment #stationhq` },
  candles: { html: candle, secs: CAN_T / 1000, sounds: [3.0, 4.4, 4.9, 6.5, 7.0, 8.4, 10.0, 11.0, 13.3, 16.5],
    caption: `Candle season. 🕯️\n\nKeep candles at least 12 inches from anything that burns, use a sturdy holder that won't tip, and think about flameless candles.\n\nAlmost half of December home decoration fires are started by candles (U.S. Fire Administration).\n\nShare this with your community. Departments, feel free to repost to your story.\n\n#candlesafety #holidayfiresafety #firesafety #firedepartment #stationhq` },
};

function soundTrack(file, secs, times) {
  const parts = [], labels = [];
  times.forEach((t, i) => {
    const ms = Math.round(t * 1000);
    parts.push(`sine=f=1320:d=0.25,volume=0.45,afade=t=out:st=0.03:d=0.22,adelay=${ms}|${ms}[s${i}]`);
    labels.push(`[s${i}]`);
  });
  const bed = `anoisesrc=d=${secs}:c=brown:a=0.02,lowpass=f=300[bed]`;
  const graph = [bed, ...parts, `[bed]${labels.join('')}amix=inputs=${times.length + 1}:normalize=0:duration=first,aformat=channel_layouts=stereo[out]`].join(';');
  execFileSync('ffmpeg', ['-y', '-loglevel', 'error', '-filter_complex', graph, '-map', '[out]', '-t', String(secs), '-ar', '44100', '-c:a', 'aac', '-b:a', '128k', file]);
}

(async () => {
  const outDir = process.env.OUT || path.join(__dirname, '../content/explainers');
  fs.mkdirSync(outDir, { recursive: true });
  const names = process.argv.slice(2).length ? process.argv.slice(2) : Object.keys(EXPLAINERS);
  const b = await chromium.launch();
  for (const name of names) {
    const r = EXPLAINERS[name];
    const pg = await b.newPage({ viewport: { width: 1080, height: 1920 } });
    const tmp = fs.mkdtempSync('/tmp/expl-');
    await pg.setContent(r.html, { waitUntil: 'load' });
    await pg.evaluate(() => document.fonts.ready);
    await pg.evaluate(() => document.getAnimations().forEach(a => a.pause()));
    const n = Math.round(r.secs * FPS);
    for (let f = 0; f < n; f++) {
      await pg.evaluate(t => document.getAnimations().forEach(a => { a.currentTime = t; }), (f * 1000) / FPS);
      await pg.screenshot({ path: path.join(tmp, `f${String(f).padStart(4, '0')}.jpg`), type: 'jpeg', quality: 90 });
    }
    const aud = path.join(tmp, 'a.m4a');
    soundTrack(aud, r.secs, r.sounds);
    execFileSync('ffmpeg', ['-y', '-loglevel', 'error', '-framerate', String(FPS), '-i', path.join(tmp, 'f%04d.jpg'), '-i', aud,
      '-c:v', 'libx264', '-preset', 'veryfast', '-b:v', '4M', '-maxrate', '4.5M', '-bufsize', '9M', '-pix_fmt', 'yuv420p',
      '-c:a', 'copy', '-shortest', '-movflags', '+faststart', path.join(outDir, name + '.mp4')]);
    fs.writeFileSync(path.join(outDir, name + '.txt'), r.caption + '\n');
    fs.rmSync(tmp, { recursive: true, force: true });
    await pg.close();
    console.log('rendered', name, r.secs + 's');
  }
  await b.close();
})();
