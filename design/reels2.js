// Animated Reels for the daily StationHQ posts (1080x1920, 30fps): a hook on screen from frame 1,
// animated content, then a StationHQ end card. Sound is synthesized here (ticks/dings, no third-party audio);
// post_own.py lays an Instagram library track underneath when the direct API is available.
// Usage: node reels2.js            -> renders every reel below into ../content/queue/<name>.mp4 (+ .txt kept)
//        ONLY=07_roster node reels2.js
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');
const { css, LOGO } = require('./gen.js');

const FPS = 30;
const THEMES = {
  dark: '',
  paper: `:root{--mute:#6B6F76;--line:#D6CEBF;--panel:#FFFFFF}body{background:#F1ECE2;color:#15171A}
.bg,.grid{display:none}.it{box-shadow:0 8px 22px rgba(0,0,0,.07)}.end .s{color:#6B6F76}.sub{color:#3C4047}`,
};
const base = (theme) => `<style>${css}
body{width:1080px;height:1920px}
.hdr{position:absolute;top:110px;left:0;right:0;display:flex;justify-content:center;align-items:center;gap:20px;font-family:BC;font-weight:700;font-size:48px;letter-spacing:3px}
.hdr img{width:110px}.hdr b{color:var(--red)}
.hook{position:absolute;left:70px;right:70px;top:330px;text-align:center;font-family:BC;font-weight:800;text-transform:uppercase;font-size:124px;line-height:.92}
.hook em{font-style:normal;color:var(--red)}
.sub{position:absolute;left:110px;right:110px;text-align:center;font-size:40px;line-height:1.4;color:#C9CED6;opacity:0}
.list{position:absolute;left:90px;right:90px;top:760px;display:flex;flex-direction:column;gap:26px}
.it{display:flex;align-items:center;gap:30px;background:var(--panel);border:2px solid var(--line);border-radius:28px;padding:34px 40px;font-size:42px;font-weight:500;opacity:0}
.it .n{font-family:BC;font-weight:800;font-size:58px;color:var(--red);width:70px;flex:none}
.it .tag{margin-left:auto;font-family:BC;font-weight:700;font-size:34px;letter-spacing:3px;padding:8px 22px;border-radius:999px;opacity:0}
.ok{background:rgba(46,160,90,.14);color:#1F8A4C}.due{background:rgba(224,49,43,.14);color:var(--red)}
.phone{position:absolute;left:210px;top:700px;width:660px;height:1120px;border-radius:84px;background:#05070A;border:12px solid #23282F;box-shadow:0 50px 100px rgba(0,0,0,.5);padding:80px 34px;overflow:hidden;opacity:0;color:#F4F5F7}
.phone .ttl{font-family:BC;font-weight:700;font-size:38px;letter-spacing:3px;color:#8A93A0;margin:0 10px 26px}
.row{display:flex;align-items:center;gap:20px;background:#14181D;border:2px solid #252B33;border-radius:26px;padding:26px 24px;margin-bottom:18px;font-size:30px;opacity:0}
.row .d{width:20px;height:20px;border-radius:50%;background:#5BD48A;flex:none}.row .d.off{background:var(--red)}
.row b{font-family:BC;font-weight:700;font-size:36px;letter-spacing:1px;width:150px;flex:none}
.row small{margin-left:auto;color:#8A93A0;font-size:24px}
.row.alert{border-color:rgba(224,49,43,.8);box-shadow:0 0 50px rgba(224,49,43,.35)}
.row.alert img{width:48px}
.cal b{width:96px;text-align:center;line-height:1}.cal b span{display:block;font-size:22px;color:var(--red);letter-spacing:2px}
.opts{position:absolute;left:90px;right:90px;top:820px;display:grid;grid-template-columns:1fr 1fr;gap:30px}
.opt{background:var(--panel);border:2px solid var(--line);border-radius:34px;padding:70px 30px;text-align:center;opacity:0}
.opt .k{font-family:BC;font-weight:800;font-size:150px;color:var(--red);line-height:1}
.opt .v{font-family:BC;font-weight:700;font-size:64px;margin-top:20px;text-transform:uppercase}
.ttl2{position:absolute;left:90px;right:90px;top:730px;font-family:BC;font-weight:700;font-size:40px;letter-spacing:5px;color:var(--mute);opacity:0}
.it.big{padding:38px 40px;font-size:46px}.it.big .dt{width:120px;flex:none;text-align:center;font-family:BC;font-weight:800;font-size:72px;line-height:.9}
.it.big .dt span{display:block;font-size:30px;letter-spacing:3px;color:var(--red)}.it.big small{margin-left:auto;font-family:BC;font-weight:700;font-size:44px;color:var(--mute)}
.it.big .d{width:26px;height:26px;border-radius:50%;background:#5BD48A;flex:none}.it.big .d.off{background:var(--red)}
.it.big b{font-family:BC;font-weight:800;font-size:54px;width:250px;flex:none}
.alert2{border-color:rgba(224,49,43,.85)!important;box-shadow:0 0 60px rgba(224,49,43,.35);margin-top:20px}.alert2 img{width:64px}
.split{position:absolute;left:0;right:0;opacity:0;display:flex;flex-direction:column;align-items:center;justify-content:center}
.split .k{font-family:BC;font-weight:800;font-size:220px;line-height:.85}.split .v{font-family:BC;font-weight:800;font-size:120px;text-transform:uppercase;line-height:1}
.sa{top:560px;height:560px;background:var(--red);color:#fff}.sb{top:1120px;height:560px;background:#15171A;color:#fff}.sb .k{color:var(--red)}
.vsb{position:absolute;left:440px;top:1020px;width:200px;height:200px;border-radius:50%;background:#F2C230;color:#111;display:grid;place-items:center;font-family:BC;font-weight:800;font-size:96px;opacity:0;z-index:3;box-shadow:0 20px 50px rgba(0,0,0,.4)}
.ask{position:absolute;left:0;right:0;top:1720px;text-align:center;font-family:BC;font-weight:800;font-size:64px;opacity:0}
.vs{position:absolute;left:0;right:0;top:1330px;text-align:center;font-family:BC;font-weight:800;font-size:70px;opacity:0}
.kin{position:absolute;left:80px;right:80px;text-align:center;font-family:BC;font-weight:800;text-transform:uppercase;font-size:128px;line-height:.92;opacity:0}
.kin em{font-style:normal;color:var(--red)}
.end{position:absolute;left:0;right:0;bottom:250px;text-align:center;opacity:0}
.end img{width:200px}
.end .u{font-family:BC;font-weight:700;font-size:62px;letter-spacing:4px;margin-top:16px}
.end .s{font-size:34px;color:var(--mute);margin-top:12px}
.chev{position:absolute;left:0;right:0;bottom:0;height:26px;background:repeating-linear-gradient(-45deg,var(--red) 0 38px,#F2C230 38px 76px)}
${THEMES[theme]}
</style><div class=bg></div><div class=grid></div>
<div class=hdr><img src="${LOGO}">STATION<b>HQ</b></div><div class=chev></div>`;

const end = (line) => `<div class=end id=end><img src="${LOGO}"><div class=u>${line}</div><div class=s>stationhq.app · link in bio</div></div>`;
// anim helper injected into each page; the hook is visible from frame 1 (no fade-in) so the cover isn't blank
const js = (body) => `<script>{const A=(id,kf,o)=>document.getElementById(id).animate(kf,Object.assign({fill:kf[0].opacity===1?'forwards':'both',easing:'cubic-bezier(.2,.8,.2,1)'},o));
const POP=[{opacity:0,transform:'translateY(60px) scale(.96)'},{opacity:1,transform:'none'}];${body}}</script>`;  // block scope: the page is reused between reels
const outro = (t) => `A('end',[{opacity:0,transform:'translateY(40px)'},{opacity:1,transform:'none'}],{duration:600,delay:${t}});`;

// ---- layouts ----
function listReel({ theme, hook, items, endLine, step = 700, start = 900, hookOut }) {
  const t0 = start, tEnd = start + items.length * step + 1800;
  const html = base(theme) + `<div class=hook id=hook>${hook}</div>
<div class=list>${items.map((t, i) => `<div class=it id=i${i}><span class=n>0${i + 1}</span>${t}</div>`).join('')}</div>${end(endLine)}` + js(`
${items.map((_, i) => `A('i${i}',POP,{duration:450,delay:${t0 + i * step}});`).join('')}
A('hook',[{opacity:1},{opacity:${hookOut ?? 1}}],{duration:300,delay:${tEnd - 400}});
${items.map((_, i) => `A('i${i}',[{opacity:1},{opacity:0}],{duration:300,delay:${tEnd - 300}});`).join('')}
A('hook',[{opacity:1},{opacity:0}],{duration:300,delay:${tEnd - 300}});
${outro(tEnd)}`);
  return { html, secs: (tEnd + 2200) / 1000, sounds: items.map((_, i) => (t0 + i * step) / 1000), tone: 'tick' };
}

function cardsReel({ theme, hook, ttl, rows, alertRow, endLine }) {
  // big full-width cards instead of a tiny phone mockup
  const t0 = 900, step = 550, tAlert = t0 + rows.length * step + 400, tEnd = tAlert + (alertRow ? 2200 : 1600);
  const html = base(theme) + `<div class=hook id=hook style="top:300px">${hook}</div>
<div class=ttl2 id=tt>${ttl}</div><div class=list style="top:820px;gap:24px">${rows.map((r, i) => `<div class="it big" id=i${i}>${r}</div>`).join('')}
${alertRow ? `<div class="it big alert2" id=al>${alertRow}</div>` : ''}</div>${end(endLine)}` + js(`
A('tt',[{opacity:0},{opacity:1}],{duration:300,delay:600});
${rows.map((_, i) => `A('i${i}',POP,{duration:420,delay:${t0 + i * step}});`).join('')}
${alertRow ? `A('al',[{opacity:0,transform:'translateY(-80px) scale(.92)'},{opacity:1,transform:'none'}],{duration:450,delay:${tAlert},easing:'cubic-bezier(.2,1.4,.4,1)'});` : ''}
${rows.map((_, i) => `A('i${i}',[{opacity:1},{opacity:0}],{duration:300,delay:${tEnd - 300}});`).join('')}
${alertRow ? `A('al',[{opacity:1},{opacity:0}],{duration:300,delay:${tEnd - 300}});` : ''}
A('tt',[{opacity:1},{opacity:0}],{duration:300,delay:${tEnd - 300}});A('hook',[{opacity:1},{opacity:0}],{duration:300,delay:${tEnd - 300}});
${outro(tEnd)}`);
  const sounds = rows.map((_, i) => (t0 + i * step) / 1000);
  if (alertRow) sounds.push(tAlert / 1000);
  return { html, secs: (tEnd + 2200) / 1000, sounds, tone: alertRow ? 'ding' : 'tick' };
}

function phoneReel({ theme, hook, ttl, rows, alertRow, endLine }) {
  const t0 = 1100, step = 450, tAlert = t0 + rows.length * step + 500, tEnd = tAlert + (alertRow ? 2000 : 1500);
  const html = base(theme) + `<div class=hook id=hook style="top:300px">${hook}</div>
<div class=phone id=ph><div class=ttl>${ttl}</div>${rows.map((r, i) => r.replace('<div class=', `<div id=r${i} class=`)).join('')}
${alertRow ? alertRow.replace('<div class=', '<div id=al class=') : ''}</div>${end(endLine)}` + js(`
A('ph',[{opacity:0,transform:'translateY(300px)'},{opacity:1,transform:'none'}],{duration:800,delay:300});
${rows.map((_, i) => `A('r${i}',POP,{duration:400,delay:${t0 + i * step}});`).join('')}
${alertRow ? `A('al',[{opacity:0,transform:'translateY(-120px) scale(.9)'},{opacity:1,transform:'none'}],{duration:450,delay:${tAlert},easing:'cubic-bezier(.2,1.4,.4,1)'});` : ''}
A('ph',[{opacity:1,transform:'none'},{opacity:0,transform:'translateY(200px)'}],{duration:400,delay:${tEnd - 400}});
A('hook',[{opacity:1},{opacity:0}],{duration:300,delay:${tEnd - 300}});
${outro(tEnd)}`);
  const sounds = rows.map((_, i) => (t0 + i * step) / 1000);
  if (alertRow) sounds.push(tAlert / 1000);
  return { html, secs: (tEnd + 2200) / 1000, sounds, tone: alertRow ? 'ding' : 'tick' };
}

function pollReel({ theme, hook, a, b, endLine }) {
  const html = base(theme) + `<div class=hook id=hook style="top:290px">${hook}</div>
<div class="split sa" id=sa><div class=k>A</div><div class=v>${a}</div></div>
<div class="split sb" id=sb><div class=k>B</div><div class=v>${b}</div></div>
<div class=vsb id=vs>VS</div><div class=ask id=ask>COMMENT A OR B 👇</div>${end(endLine)}` + js(`
A('sa',[{opacity:0,transform:'translateX(-100%)'},{opacity:1,transform:'none'}],{duration:500,delay:700});
A('sb',[{opacity:0,transform:'translateX(100%)'},{opacity:1,transform:'none'}],{duration:500,delay:1500});
A('vs',[{opacity:0,transform:'scale(2.2) rotate(-20deg)'},{opacity:1,transform:'none'}],{duration:400,delay:2300,easing:'cubic-bezier(.2,1.6,.4,1)'});
A('ask',[{opacity:0,transform:'translateY(30px)'},{opacity:1,transform:'none'}],{duration:400,delay:3000});
${['sa', 'sb', 'vs', 'ask', 'hook'].map(id => `A('${id}',[{opacity:1},{opacity:0}],{duration:300,delay:6000});`).join('')}
${outro(6300)}`);
  return { html, secs: 8.5, sounds: [0.7, 1.5, 2.3], tone: 'thud' };
}

function oldPollReel({ theme, hook, a, b, endLine }) {
  const html = base(theme) + `<div class=hook id=hook>${hook}</div>
<div class=opts><div class=opt id=oa><div class=k>A</div><div class=v>${a}</div></div><div class=opt id=ob><div class=k>B</div><div class=v>${b}</div></div></div>
<div class=vs id=vs>DROP YOUR ANSWER 👇</div>${end(endLine)}` + js(`
A('oa',[{opacity:0,transform:'translateX(-200px)'},{opacity:1,transform:'none'}],{duration:450,delay:900});
A('ob',[{opacity:0,transform:'translateX(200px)'},{opacity:1,transform:'none'}],{duration:450,delay:1700});
A('vs',[{opacity:0,transform:'scale(1.4)'},{opacity:1,transform:'none'}],{duration:400,delay:2900});
A('vs',[{transform:'none'},{transform:'scale(1.06)'},{transform:'none'}],{duration:700,delay:3500,iterations:3});
A('vs',[{opacity:1},{opacity:0}],{duration:300,delay:5900});A('oa',[{opacity:1},{opacity:0}],{duration:300,delay:5900});
A('ob',[{opacity:1},{opacity:0}],{duration:300,delay:5900});A('hook',[{opacity:1},{opacity:0}],{duration:300,delay:5900});
${outro(6200)}`);
  return { html, secs: 8.4, sounds: [0.9, 1.7, 2.9], tone: 'tick' };
}

function ledgerReel({ theme, hook, rows, endLine }) {
  const t0 = 900, step = 550, tStamp = t0 + rows.length * step + 300, tEnd = tStamp + rows.length * 300 + 1200;
  const html = base(theme) + `<div class=hook id=hook>${hook}</div>
<div class=list style="top:720px">${rows.map(([n, ok], i) => `<div class=it id=i${i}>${n}<span class="tag ${ok ? 'ok' : 'due'}" id=t${i}>${ok ? 'PAID' : 'DUE'}</span></div>`).join('')}</div>${end(endLine)}` + js(`
${rows.map((_, i) => `A('i${i}',POP,{duration:400,delay:${t0 + i * step}});A('t${i}',[{opacity:0,transform:'scale(1.8) rotate(-8deg)'},{opacity:1,transform:'none'}],{duration:300,delay:${tStamp + i * 300},easing:'cubic-bezier(.2,1.6,.4,1)'});`).join('')}
${rows.map((_, i) => `A('i${i}',[{opacity:1},{opacity:0}],{duration:300,delay:${tEnd - 300}});`).join('')}
A('hook',[{opacity:1},{opacity:0}],{duration:300,delay:${tEnd - 300}});
${outro(tEnd)}`);
  return { html, secs: (tEnd + 2200) / 1000, sounds: rows.map((_, i) => (tStamp + i * 300) / 1000), tone: 'tick' };
}

function kineticReel({ theme, lines, endLine }) {
  // lines: [html, top]; first line shows from frame 1, the rest slam in
  const html = base(theme) + lines.map(([t, top], i) => `<div class=kin id=k${i} style="top:${top}px${i === 0 ? ';opacity:1' : ''}">${t}</div>`).join('') + end(endLine) + js(`
${lines.slice(1).map((_, j) => `A('k${j + 1}',[{opacity:0,transform:'scale(1.5)'},{opacity:1,transform:'none'}],{duration:350,delay:${900 + j * 900},easing:'cubic-bezier(.2,1.4,.4,1)'});`).join('')}
${lines.map((_, i) => `A('k${i}',[{opacity:1},{opacity:0}],{duration:300,delay:${900 + lines.length * 900 + 600}});`).join('')}
${outro(900 + lines.length * 900 + 900)}`);
  const tEnd = 900 + lines.length * 900 + 900;
  return { html, secs: (tEnd + 2200) / 1000, sounds: lines.slice(1).map((_, j) => (900 + j * 900) / 1000), tone: 'thud' };
}

// ---- the queue (names match content/queue so captions stay; the .jpg is replaced by the .mp4) ----
const REELS = {
  '05_grouptexts': listReel({ theme: 'paper', hook: 'Your station<br>runs on <em>group texts</em><br>if…', items: ['Drill changes get buried', 'Nobody knows who’s on duty', 'Cert expirations sneak up', 'Rig check sheets go missing'], endLine: 'ONE APP FOR THE FIREHOUSE' }),
  '07_roster': cardsReel({ theme: 'dark', hook: 'Who’s on<br><em>tonight?</em>', ttl: 'TONIGHT · STATION 2',
    rows: [['ENGINE 1', 'Capt + 3 FF', 'full'], ['LADDER', '4 FF', 'full'], ['RESCUE', '2 FF', '1 open'], ['EMS', '2 EMT', 'full'], ['CHIEF', 'Duty chief', 'on call']]
      .map(([u, c, st]) => `<span class="d${st.includes('open') ? ' off' : ''}"></span><b>${u}</b>${c}<small>${st}</small>`),
    endLine: 'KNOW WHO’S COVERING' }),
  '08_poll_nozzle': pollReel({ theme: 'paper', hook: 'Smooth bore<br>or <em>fog?</em>', a: 'Smooth bore', b: 'Fog', endLine: 'SETTLE IT IN THE COMMENTS' }),
  '09_dues': ledgerReel({ theme: 'paper', hook: 'Who’s paid<br><em>their dues?</em>', rows: [['Member 01', 1], ['Member 02', 1], ['Member 03', 0], ['Member 04', 1], ['Member 05', 0]], endLine: 'DUES, HANDLED.' }),
  '11_calendar': cardsReel({ theme: 'dark', hook: 'Drills. Training.<br><em>One calendar.</em>', ttl: 'THIS WEEK',
    rows: [['TUE', '10', 'Drill · ladder ops', '1900'], ['THU', '12', 'EMS con-ed', '1930'], ['SAT', '14', 'Rig check', '0900'], ['MON', '16', 'Monthly meeting', '1930']]
      .map(([d, n, t, h]) => `<span class=dt><span>${d}</span>${n}</span>${t}<small>${h}</small>`),
    alertRow: `<img src="${LOGO}">Reminder: drill in 1 hour`,
    endLine: 'REMINDERS THAT REACH EVERYONE' }),
  '12_tag': kineticReel({ theme: 'dark', lines: [['Every<br>firehouse<br>has one', 330], ['First <em>in.</em>', 820], ['Last <em>out.</em>', 1000], ['Never misses<br>a <em>call.</em>', 1180]], endLine: 'TAG THEM 👇' }),
  '13_joincode': listReel({ theme: 'paper', hook: 'New member?<br><em>On the roster<br>in a minute.</em>', items: ['Get your department’s join code', 'Sign up on your phone', 'Admin approves you', 'You’re on the roster ✅'], endLine: 'ONBOARDING, DONE' }),
};

function soundTrack(file, secs, times, tone) {
  const parts = [], labels = [];
  times.forEach((t, i) => {
    const ms = Math.round(t * 1000);
    const src = tone === 'ding'
      ? `sine=f=1320:d=0.35,volume=0.5,afade=t=out:st=0.05:d=0.3[a${i}x];sine=f=1760:d=0.35,volume=0.35,adelay=90,afade=t=out:st=0.15:d=0.3[a${i}y];[a${i}x][a${i}y]amix=2:normalize=0`
      : tone === 'thud'
        ? `sine=f=70:d=0.25,volume=1.2,afade=t=out:st=0.02:d=0.22`
        : `sine=f=2200:d=0.06,volume=0.6,afade=t=out:st=0.01:d=0.05`;
    parts.push(`${src},adelay=${ms}|${ms}[s${i}]`);
    labels.push(`[s${i}]`);
  });
  const bed = `anoisesrc=d=${secs}:c=brown:a=0.02,lowpass=f=300[bed]`;
  const graph = [bed, ...parts, `[bed]${labels.join('')}amix=inputs=${times.length + 1}:normalize=0:duration=first,aformat=channel_layouts=stereo[out]`].join(';');
  execFileSync('ffmpeg', ['-y', '-loglevel', 'error', '-filter_complex', graph, '-map', '[out]', '-t', String(secs), '-ar', '44100', '-c:a', 'aac', '-b:a', '128k', file]);
}

(async () => {
  const outDir = process.env.OUT || path.join(__dirname, '../content/queue');
  const names = process.env.ONLY ? process.env.ONLY.split(',') : Object.keys(REELS);
  const b = await chromium.launch();
  const pg = await b.newPage({ viewport: { width: 1080, height: 1920 } });
  for (const name of names) {
    const r = REELS[name];
    const tmp = fs.mkdtempSync('/tmp/reel-');
    await pg.setContent(r.html, { waitUntil: 'load' });
    await pg.evaluate(() => document.fonts.ready);
    await pg.evaluate(() => document.getAnimations().forEach(a => a.pause()));
    const n = Math.round(r.secs * FPS);
    for (let f = 0; f < n; f++) {
      await pg.evaluate(t => document.getAnimations().forEach(a => { a.currentTime = t; }), (f * 1000) / FPS);
      await pg.screenshot({ path: path.join(tmp, `f${String(f).padStart(4, '0')}.jpg`), type: 'jpeg', quality: 90 });
    }
    const aud = path.join(tmp, 'a.m4a');
    soundTrack(aud, r.secs, r.sounds, r.tone);
    execFileSync('ffmpeg', ['-y', '-loglevel', 'error', '-framerate', String(FPS), '-i', path.join(tmp, 'f%04d.jpg'), '-i', aud,
      '-c:v', 'libx264', '-preset', 'veryfast', '-b:v', '4M', '-maxrate', '4.5M', '-bufsize', '9M', '-pix_fmt', 'yuv420p',
      '-c:a', 'copy', '-shortest', '-movflags', '+faststart', path.join(outDir, name + '.mp4')]);
    fs.rmSync(tmp, { recursive: true, force: true });
    console.log('rendered', name, r.secs.toFixed(1) + 's');
  }
  await b.close();
})();
