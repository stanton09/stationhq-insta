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
.end{position:absolute;left:0;right:0;top:620px;text-align:center;opacity:0}
.end img{width:260px}.end .u{font-family:BC;font-weight:800;font-size:96px;line-height:.95;margin-top:30px;color:#fff;text-transform:uppercase}
.end .u em{font-style:normal;color:#FF5A3C}.end .s{font-size:36px;color:#8FA0B5;margin-top:24px}
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
<div class=fact id=fact><b>Space heaters are involved in most home heating fire deaths.</b><small>Source: NFPA</small></div>
<div class=end id=end><img src="${LOGO}"><div class=u>Share this with<br><em>your community</em></div><div class=s>From your firefighters at StationHQ</div></div>
`, HEATER_T, `
show('h1',0,3200);show('h2',3200,7000);show('h3',7000,9800);show('h4',9800,12600);show('h5',12600,15800);
show('fact',15800,18800,300,300);
show('end',18800,${HEATER_T},400,0,'scale(.94)');
// illustration stays up until the end card
['outlet','strip','heater','couch','stripcord'].forEach(id=>show(id,0,18800,0,400,null));
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

const EXPLAINERS = {
  heaters: { html: heater, secs: HEATER_T / 1000, sounds: [3.2, 4.6, 5.2, 7.0, 7.5, 9.8, 10.4, 12.6, 15.8, 18.8],
    caption: `Space heater season. 🔥\n\nGive it 3 feet on every side, plug it straight into the wall (never a power strip or extension cord), and turn it off when you leave the room or go to bed.\n\nSpace heaters are involved in most home heating fire deaths, per NFPA.\n\nShare this with your community. Departments, feel free to repost to your story.\n\n#firesafety #spaceheater #winterfiresafety #fireprevention #firedepartment #stationhq` },
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
