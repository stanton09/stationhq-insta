const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');
const f = (pkg, file) => 'data:font/woff2;base64,' + fs.readFileSync(path.join(__dirname, 'node_modules/@fontsource', pkg, 'files', file)).toString('base64');

const css = `
@font-face{font-family:BC;font-weight:800;src:url(${f('barlow-condensed','barlow-condensed-latin-800-normal.woff2')})}
@font-face{font-family:BC;font-weight:700;src:url(${f('barlow-condensed','barlow-condensed-latin-700-normal.woff2')})}
@font-face{font-family:BC;font-weight:600;src:url(${f('barlow-condensed','barlow-condensed-latin-600-normal.woff2')})}
@font-face{font-family:IN;font-weight:400;src:url(${f('inter','inter-latin-400-normal.woff2')})}
@font-face{font-family:IN;font-weight:500;src:url(${f('inter','inter-latin-500-normal.woff2')})}
@font-face{font-family:IN;font-weight:600;src:url(${f('inter','inter-latin-600-normal.woff2')})}
:root{--red:#E0312B;--red2:#ff5a3c;--ink:#0B0D10;--panel:#14181D;--line:#252B33;--mute:#8A93A0}
*{margin:0;padding:0;box-sizing:border-box}
body{width:1080px;height:1350px;overflow:hidden;position:relative;background:var(--ink);color:#F4F5F7;font-family:IN}
.bg{position:absolute;inset:0;background:
  radial-gradient(900px 700px at 100% 0%,rgba(224,49,43,.22),transparent 60%),
  radial-gradient(700px 600px at 0% 100%,rgba(47,140,255,.10),transparent 60%);}
.grid{position:absolute;inset:0;background-image:linear-gradient(rgba(255,255,255,.035) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.035) 1px,transparent 1px);background-size:60px 60px;mask-image:linear-gradient(180deg,#000,transparent 75%)}
header{position:absolute;top:48px;left:80px;right:80px;display:flex;justify-content:space-between;align-items:center}
.logo{display:flex;align-items:center;gap:18px;font-family:BC;font-weight:700;font-size:38px;letter-spacing:3px}
.mark{width:54px;height:54px;border-radius:12px;background:var(--red);display:grid;place-items:center;font-family:BC;font-weight:800;font-size:26px;letter-spacing:0;box-shadow:0 8px 24px rgba(224,49,43,.45)}
.logo b{color:var(--red)}.badge{width:150px;height:152px;filter:drop-shadow(0 0 18px rgba(255,59,31,.35))}.wm{font-size:46px;letter-spacing:3px;line-height:1}.wm sup{font-family:IN;font-size:18px;color:var(--mute);margin-left:4px;vertical-align:top;position:relative;top:4px}.tg{font-family:IN;font-weight:500;font-size:17px;letter-spacing:3px;color:var(--mute);margin-top:10px}
.kicker{font-family:BC;font-weight:600;font-size:26px;letter-spacing:5px;color:var(--mute);border:2px solid var(--line);padding:10px 20px;border-radius:999px}
.kicker i{font-style:normal;color:var(--red2)}
h1{font-family:BC;font-weight:800;text-transform:uppercase;font-size:150px;line-height:.88;letter-spacing:-1px}
h1 em{font-style:normal;color:var(--red)}
.sub{font-size:34px;line-height:1.45;color:#B9C0CA;max-width:820px}
footer{z-index:5;position:absolute;left:0;right:0;bottom:0;height:150px}
.chev{position:absolute;left:0;right:0;bottom:0;height:22px;background:repeating-linear-gradient(-45deg,var(--red) 0 34px,#F2C230 34px 68px);opacity:.95}
.foot{position:absolute;left:80px;right:80px;bottom:62px;display:flex;justify-content:space-between;font-family:BC;font-weight:600;font-size:28px;letter-spacing:4px;color:var(--mute)}
.foot span:last-child{color:#fff}
`;

const LOGO='data:image/png;base64,'+fs.readFileSync(path.join(__dirname,'../brand/logo_badge.png')).toString('base64');
const shell = (kicker, body) => `<style>${css}</style><div class=bg></div><div class=grid></div>
<header><div class=logo><img class=badge src="${LOGO}"><div><div class=wm>STATION<b>HQ</b><sup>™</sup></div><div class=tg>YOUR STATION · YOUR MEMBERS</div></div></div><div class=kicker>${kicker}</div></header>
${body}
<footer><div class=foot><span>BUILT BY FIREFIGHTERS</span><span>STATIONHQ.APP</span></div><div class=chev></div></footer>`;

const posts = {
'01_alerts': shell('<i>●</i> FEATURE', `
<style>
.l{position:absolute;top:250px;left:80px}
.phone{position:absolute;right:-60px;top:700px;width:560px;height:900px;border-radius:70px;background:#05070A;border:10px solid #22272F;box-shadow:0 40px 80px rgba(0,0,0,.6),0 0 0 2px #333 inset;padding:90px 30px}
.time{text-align:center;font-family:BC;font-weight:600;font-size:110px;color:#e9ecf1;margin-bottom:6px}
.date{text-align:center;color:var(--mute);font-size:24px;margin-bottom:50px}
.n{background:rgba(255,255,255,.08);backdrop-filter:blur(10px);border-radius:28px;padding:24px 26px;margin-bottom:16px}
.n .t{display:flex;align-items:center;gap:12px;font-size:20px;color:var(--mute);margin-bottom:10px}

.n .h{font-weight:600;font-size:25px;margin-bottom:4px}.n .b{font-size:22px;color:#c9ced6;line-height:1.35}
.n.hot{border:2px solid rgba(224,49,43,.7);box-shadow:0 0 40px rgba(224,49,43,.35)}
.pts{position:absolute;left:80px;top:860px;display:flex;flex-direction:column;gap:30px}
.pt{font-family:BC;font-weight:700;font-size:40px;letter-spacing:2px;text-transform:uppercase;display:flex;align-items:center;gap:18px}
.pt:before{content:"";width:14px;height:14px;background:var(--red);transform:rotate(45deg)}
</style>
<div class=l><h1>One alert.<br>Every phone.<br><em>Instantly.</em></h1>
<p class=sub style="margin-top:40px;max-width:440px">Chiefs send it once. The whole department gets it.</p></div>
<div class=pts><div class=pt>Drill</div><div class=pt>Training</div><div class=pt>Emergency</div></div>
<div class=phone><div class=time>18:42</div><div class=date>Tuesday</div>
<div class="n hot"><div class=t><img src="${LOGO}" style="width:30px;height:30px">STATIONHQ · now</div><div class=h>⚠ Drill Alert</div><div class=b>Ladder ops tonight, 1900 at Station 2. RSVP in app.</div></div>
</div>`),

'02_rigcheck': shell('<i>●</i> RIG CHECK', `
<style>
.l{position:absolute;top:250px;left:80px}
.card{position:absolute;left:80px;right:80px;top:600px;background:var(--panel);border:2px solid var(--line);border-radius:32px;padding:44px 50px;box-shadow:0 30px 60px rgba(0,0,0,.4)}
.ch{display:flex;justify-content:space-between;align-items:center;padding-bottom:26px;border-bottom:2px solid var(--line);margin-bottom:10px}
.ch .u{font-family:BC;font-weight:700;font-size:40px;letter-spacing:2px}.ch .s{font-family:BC;font-weight:600;font-size:24px;letter-spacing:3px;color:#5BD48A;background:rgba(91,212,138,.12);padding:8px 18px;border-radius:999px}
.row{display:flex;align-items:center;gap:28px;padding:24px 0;border-bottom:1px solid var(--line);font-size:32px;font-weight:500}
.row:last-child{border:0}
.ck{width:46px;height:46px;border-radius:12px;background:var(--red);display:grid;place-items:center;flex:none}
.ck:after{content:"";width:18px;height:10px;border-left:5px solid #fff;border-bottom:5px solid #fff;transform:rotate(-45deg) translate(2px,-2px)}
.row small{margin-left:auto;font-size:22px;color:var(--mute);font-weight:400}
</style>
<div class=l><h1>Rig check,<br><em>done right.</em></h1></div>
<div class=card><div class=ch><div class=u>ENGINE 1 · DAILY CHECK</div><div class=s>COMPLETE</div></div>
<div class=row><div class=ck></div>Photo proof on every item<small>12 photos</small></div>
<div class=row><div class=ck></div>Works offline in the bay<small>synced</small></div>
<div class=row><div class=ck></div>Quals &amp; cert expirations<small>tracked</small></div>
<div class=row><div class=ck></div>LOSAP hours in one place<small>logged</small></div>
</div>`),

'03_founding': shell('<i>●</i> FOUNDING OFFER', `
<style>
.l{position:absolute;top:250px;left:80px;right:80px}
.big{position:absolute;right:40px;top:150px;font-family:BC;font-weight:800;font-size:620px;line-height:1;color:transparent;-webkit-text-stroke:3px rgba(224,49,43,.28)}
.stats{position:absolute;left:80px;right:80px;top:820px;display:grid;grid-template-columns:repeat(3,1fr);gap:22px}
.st{background:var(--panel);border:2px solid var(--line);border-radius:28px;padding:36px 30px}
.st .v{font-family:BC;font-weight:800;font-size:96px;line-height:1;color:#fff}.st .v em{font-style:normal;color:var(--red);font-size:56px;margin-left:4px}
.st .k{margin-top:14px;font-size:24px;color:var(--mute);line-height:1.35}
</style>
<div class=big>11</div>
<div class=l><h1>Built by an<br>active<br><em>firefighter.</em></h1>
<p class=sub style="margin-top:40px;max-width:560px">Only the first 11 charter departments get the founding rate.</p></div>
<div class=stats>
<div class=st><div class=v>60<em>DAY</em></div><div class=k>Free trial for your department</div></div>
<div class=st><div class=v>3<em>YR</em></div><div class=k>Founding rate, locked in</div></div>
<div class=st><div class=v>$0</div><div class=k>No credit card needed</div></div>
</div>`)
};

module.exports = { css, shell, LOGO };

if (require.main === module) (async () => {
  const b = await chromium.launch();
  const pg = await b.newPage({ viewport: { width: 1080, height: 1350 } });
  for (const [n, h] of Object.entries(posts)) {
    await pg.setContent(h, { waitUntil: 'load' });
    await pg.evaluate(() => document.fonts.ready);
    await pg.screenshot({ path: n + '.png' });
  }
  await b.close();
})();
