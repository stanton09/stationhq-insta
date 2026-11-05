// Animated StationHQ Reels (1080x1920, 30fps). Renders frames with Playwright, then ffmpeg
// muxes them with synthesized sound effects (generated here, no third-party audio).
// Usage: node reels.js  -> ../content/queue/<name>.mp4 + .txt
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');
const { css, LOGO } = require('./gen.js');

const FPS = 30;
const base = `<style>${css}
body{width:1080px;height:1920px}
.hdr{position:absolute;top:90px;left:0;right:0;display:flex;justify-content:center;align-items:center;gap:20px;font-family:BC;font-weight:700;font-size:48px;letter-spacing:3px}
.hdr img{width:110px}
.hdr b{color:var(--red)}
.cap{position:absolute;left:70px;right:70px;text-align:center;font-family:BC;font-weight:800;text-transform:uppercase;font-size:118px;line-height:.92;opacity:0}
.cap em{font-style:normal;color:var(--red)}
.phone{position:absolute;width:520px;height:1060px;border-radius:78px;background:#05070A;border:12px solid #23282F;box-shadow:0 50px 100px rgba(0,0,0,.6);overflow:hidden}
.time{font-family:BC;font-weight:600;font-size:130px;text-align:center;margin-top:120px;color:#e9ecf1}
.date{text-align:center;color:var(--mute);font-size:28px}
.note{position:absolute;left:24px;right:24px;top:380px;background:rgba(255,255,255,.1);border:2px solid rgba(224,49,43,.8);border-radius:30px;padding:26px 28px;box-shadow:0 0 50px rgba(224,49,43,.4)}
.note .t{display:flex;align-items:center;gap:12px;font-size:22px;color:var(--mute);margin-bottom:10px}
.note .t img{width:34px;height:34px}
.note .h{font-weight:600;font-size:30px}.note .b{font-size:25px;color:#c9ced6;margin-top:6px;line-height:1.35}
.end{position:absolute;left:0;right:0;bottom:260px;text-align:center;opacity:0}
.end .u{font-family:BC;font-weight:700;font-size:60px;letter-spacing:4px}
.end .s{font-size:32px;color:var(--mute);margin-top:14px}
.chev{position:absolute;left:0;right:0;bottom:0;height:26px;background:repeating-linear-gradient(-45deg,var(--red) 0 38px,#F2C230 38px 76px)}
.card{position:absolute;left:80px;right:80px;top:640px;background:var(--panel);border:2px solid var(--line);border-radius:36px;padding:44px 48px;box-shadow:0 30px 70px rgba(0,0,0,.45)}
.ch{display:flex;justify-content:space-between;align-items:center;padding-bottom:26px;border-bottom:2px solid var(--line)}
.ch .u{font-family:BC;font-weight:700;font-size:46px;letter-spacing:2px}
.ch .s{font-family:BC;font-weight:600;font-size:28px;letter-spacing:3px;color:#5BD48A;background:rgba(91,212,138,.12);padding:10px 20px;border-radius:999px;opacity:0}
.row{display:flex;align-items:center;gap:28px;padding:30px 0;border-bottom:1px solid var(--line);font-size:36px;font-weight:500}
.row:last-child{border:0}
.ck{width:56px;height:56px;border-radius:14px;border:3px solid #39414b;display:grid;place-items:center;flex:none;position:relative}
.ck i{position:absolute;inset:-3px;border-radius:14px;background:var(--red);transform:scale(0)}
.ck i:after{content:"";position:absolute;left:17px;top:14px;width:20px;height:11px;border-left:6px solid #fff;border-bottom:6px solid #fff;transform:rotate(-45deg)}
.row small{margin-left:auto;font-size:26px;color:var(--mute);opacity:0}
.bar{height:14px;border-radius:7px;background:#20262d;margin-top:30px;overflow:hidden}.bar div{height:100%;width:0;background:var(--red)}
</style><div class=bg></div><div class=grid></div>
<div class=hdr><img src="${LOGO}">STATION<b>HQ</b></div><div class=chev></div>`;

// ---------- Reel 1: one alert, every phone ----------
const phones = [[-60, 760, -8], [280, 700, 0], [620, 760, 8]];
const reel1 = base + `
<div class=cap id=c1 style="top:330px">Drill moved to <em>1900.</em></div>
<div class=cap id=c2 style="top:330px">Who got the<br><em>message?</em></div>
<div class=cap id=c3 style="top:330px"><em>Everyone.</em></div>
${phones.map(([x, y, r], i) => `<div class=phone id=p${i} style="left:${x}px;top:${y}px;transform:rotate(${r}deg)">
<div class=time>18:42</div><div class=date>Tuesday</div>
<div class=note id=n${i}><div class=t><img src="${LOGO}">STATIONHQ · now</div><div class=h>🚨 Drill Alert</div><div class=b>Drill moved to 1900 tonight. Station 2. Tap to RSVP.</div></div></div>`).join('')}
<div class=end id=e><div class=u>ONE ALERT. EVERY PHONE.</div><div class=s>stationhq.app</div></div>
<script>
const A=(id,kf,o)=>document.getElementById(id).animate(kf,Object.assign({fill:'both'},o));
A('c1',[{opacity:0,transform:'translateY(40px)'},{opacity:1,transform:'none'}],{duration:500,delay:200});
A('c1',[{opacity:1},{opacity:0}],{duration:300,delay:2600,composite:'replace'});
A('c2',[{opacity:0,transform:'translateY(40px)'},{opacity:1,transform:'none'}],{duration:400,delay:2900});
A('c2',[{opacity:1},{opacity:0}],{duration:300,delay:5600});
A('c3',[{opacity:0,transform:'scale(.8)'},{opacity:1,transform:'none'}],{duration:400,delay:5900});
[0,1,2].forEach(i=>{
  A('p'+i,[{opacity:0,translate:'0 200px'},{opacity:1,translate:'0 0'}],{duration:700,delay:300+i*150,easing:'cubic-bezier(.2,.8,.2,1)'});
  A('n'+i,[{opacity:0,transform:'translateY(-160px) scale(.9)'},{opacity:1,transform:'none'}],{duration:450,delay:3400+i*700,easing:'cubic-bezier(.2,1.4,.4,1)'});
  A('p'+i,[{boxShadow:'0 0 0 rgba(224,49,43,0)'},{boxShadow:'0 0 90px rgba(224,49,43,.85)'},{boxShadow:'0 50px 100px rgba(0,0,0,.6)'}],{duration:900,delay:3400+i*700});
});
A('e',[{opacity:0,transform:'translateY(30px)'},{opacity:1,transform:'none'}],{duration:600,delay:7000});
</script>`;
const reel1Sounds = [3.4, 4.1, 4.8];  // notification dings (seconds)

// ---------- Reel 2: rig check ----------
const items = [['Air packs at full pressure', '4/4'], ['Hose loads & nozzles', 'OK'], ['Saws fuel & start', '📷'], ['Lights & sirens', 'OK'], ['Fuel level', '¾']];
const reel2 = base + `
<div class=cap id=c1 style="top:330px">Morning<br><em>rig check.</em></div>
<div class=cap id=c2 style="top:330px">Done right.<br><em>Logged.</em></div>
<div class=card id=card><div class=ch><div class=u>ENGINE 1 · DAILY</div><div class=s id=st>COMPLETE ✓</div></div>
${items.map(([t, v], i) => `<div class=row><div class=ck><i id=k${i}></i></div>${t}<small id=v${i}>${v}</small></div>`).join('')}
<div class=bar><div id=bar></div></div></div>
<div class=end id=e><div class=u>PHOTO PROOF. WORKS OFFLINE.</div><div class=s>stationhq.app</div></div>
<script>
const A=(id,kf,o)=>document.getElementById(id).animate(kf,Object.assign({fill:'both'},o));
A('c1',[{opacity:0,transform:'translateY(40px)'},{opacity:1,transform:'none'}],{duration:500,delay:200});
A('c1',[{opacity:1},{opacity:0}],{duration:300,delay:4600});
A('c2',[{opacity:0,transform:'scale(.85)'},{opacity:1,transform:'none'}],{duration:450,delay:4900});
A('card',[{opacity:0,translate:'0 160px'},{opacity:1,translate:'0 0'}],{duration:700,delay:400,easing:'cubic-bezier(.2,.8,.2,1)'});
[0,1,2,3,4].forEach(i=>{
  A('k'+i,[{transform:'scale(0)'},{transform:'scale(1.25)'},{transform:'scale(1)'}],{duration:350,delay:1400+i*600});
  A('v'+i,[{opacity:0},{opacity:1}],{duration:250,delay:1500+i*600});
});
A('bar',[{width:'0%'},{width:'100%'}],{duration:3000,delay:1400,easing:'linear'});
A('st',[{opacity:0,transform:'scale(1.6)'},{opacity:1,transform:'none'}],{duration:400,delay:4500,easing:'cubic-bezier(.2,1.6,.4,1)'});
A('e',[{opacity:0,transform:'translateY(30px)'},{opacity:1,transform:'none'}],{duration:600,delay:5600});
</script>`;
const reel2Sounds = [1.4, 2.0, 2.6, 3.2, 3.8];  // check clicks

const reels = [
  { name: '05b_alert_reel', html: reel1, secs: 9.5, sounds: reel1Sounds, tone: 'ding',
    caption: `Drill moved. Who got the message? 📲\n\nWith StationHQ, one alert hits every member's phone at the same time. No buried group texts.\n\n60-day free trial for your department. Link in bio.\n\n#firefighter #firedepartment #volunteerfirefighter #fireservice #firehouse #stationhq` },
  { name: '11b_rigcheck_reel', html: reel2, secs: 8.5, sounds: reel2Sounds, tone: 'tick',
    caption: `Morning rig check, done right. ✅\n\nCheck items off on your phone, add photo proof, and it's logged, even with no signal in the bay.\n\nBuilt by an active firefighter. Link in bio.\n\n#rigcheck #firetruck #firefighter #fireservice #firehouse #stationhq` },
];

function soundTrack(file, secs, times, tone) {
  // Build simple synthesized effects with ffmpeg: a two-note ding or a short tick at each time.
  const parts = [], labels = [];
  times.forEach((t, i) => {
    const ms = Math.round(t * 1000);
    const src = tone === 'ding'
      ? `sine=f=1320:d=0.35,volume=0.5,afade=t=out:st=0.05:d=0.3[a${i}x];sine=f=1760:d=0.35,volume=0.35,adelay=90,afade=t=out:st=0.15:d=0.3[a${i}y];[a${i}x][a${i}y]amix=2:normalize=0`
      : `sine=f=2200:d=0.06,volume=0.6,afade=t=out:st=0.01:d=0.05`;
    parts.push(`${src},adelay=${ms}|${ms}[s${i}]`);
    labels.push(`[s${i}]`);
  });
  const bed = `anoisesrc=d=${secs}:c=brown:a=0.02,lowpass=f=300[bed]`;
  const graph = [bed, ...parts, `[bed]${labels.join('')}amix=inputs=${times.length + 1}:normalize=0:duration=first,aformat=channel_layouts=stereo[out]`].join(';');
  execFileSync('ffmpeg', ['-y', '-loglevel', 'error', '-filter_complex', graph, '-map', '[out]', '-t', String(secs), '-ar', '44100', '-c:a', 'aac', '-b:a', '128k', file]);
}

(async () => {
  const outDir = path.join(__dirname, '../content/queue');
  const b = await chromium.launch();
  const pg = await b.newPage({ viewport: { width: 1080, height: 1920 } });
  for (const r of reels) {
    const tmp = fs.mkdtempSync('/tmp/reel-');
    await pg.setContent(r.html, { waitUntil: 'load' });
    await pg.evaluate(() => document.fonts.ready);
    await pg.evaluate(() => document.getAnimations().forEach(a => a.pause()));
    const n = Math.round(r.secs * FPS);
    for (let f = 0; f < n; f++) {
      await pg.evaluate(t => document.getAnimations().forEach(a => { a.currentTime = t; }), (f * 1000) / FPS);
      await pg.screenshot({ path: path.join(tmp, `f${String(f).padStart(4, '0')}.png`) });
    }
    const aud = path.join(tmp, 'a.m4a');
    soundTrack(aud, r.secs, r.sounds, r.tone);
    execFileSync('ffmpeg', ['-y', '-loglevel', 'error', '-framerate', String(FPS), '-i', path.join(tmp, 'f%04d.png'), '-i', aud,
      '-c:v', 'libx264', '-preset', 'veryfast', '-b:v', '4M', '-maxrate', '4.5M', '-bufsize', '9M', '-pix_fmt', 'yuv420p',
      '-c:a', 'copy', '-shortest', '-movflags', '+faststart', path.join(outDir, r.name + '.mp4')]);
    fs.writeFileSync(path.join(outDir, r.name + '.txt'), r.caption + '\n');
    fs.rmSync(tmp, { recursive: true, force: true });
    console.log('rendered', r.name);
  }
  await b.close();
})();
