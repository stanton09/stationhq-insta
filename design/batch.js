// Renders a batch of StationHQ posts (1080x1350 JPEG) + captions into ../content/queue.
// Usage: node batch.js
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const { css, shell, LOGO } = require('./gen.js');

const extra = `
.l{position:absolute;top:250px;left:80px;right:80px}
.sub2{font-size:36px;line-height:1.45;color:#B9C0CA;margin-top:44px}
.list{position:absolute;left:80px;right:80px;top:640px;display:flex;flex-direction:column;gap:20px}
.li{display:flex;align-items:center;gap:26px;background:var(--panel);border:2px solid var(--line);border-radius:24px;padding:28px 34px;font-size:34px;font-weight:500}
.li .n{font-family:BC;font-weight:800;font-size:46px;color:var(--red);width:56px}
.q{position:absolute;left:80px;right:80px;top:260px}
.q .mark{font-family:IN;font-weight:600;font-size:300px;line-height:.8;color:var(--red);height:150px}
.q .t{font-family:BC;font-weight:700;font-size:88px;line-height:1.02;text-transform:uppercase;margin-top:10px}
.q .by{margin-top:40px;font-size:30px;color:var(--mute)}
.poll{position:absolute;left:80px;right:80px;top:700px;display:grid;grid-template-columns:1fr 1fr;gap:24px}
.opt{background:var(--panel);border:2px solid var(--line);border-radius:28px;padding:46px 30px;text-align:center}
.opt .k{font-family:BC;font-weight:800;font-size:90px;color:var(--red);line-height:1}
.opt .v{font-family:BC;font-weight:700;font-size:52px;margin-top:16px;text-transform:uppercase}
.bgmark{position:absolute;right:-90px;bottom:120px;width:620px;opacity:.13;filter:grayscale(.2)}
.cta{display:inline-block;margin-top:50px;background:var(--red);color:#fff;font-family:BC;font-weight:700;font-size:44px;letter-spacing:3px;padding:22px 40px;border-radius:16px}
`;
const page = (kicker, body) => shell(kicker, `<style>${extra}</style>${body}`);
const big = (kicker, h, sub, cta) => page(kicker, `<img class=bgmark src="${LOGO}"><div class=l><h1>${h}</h1>${sub ? `<p class=sub2>${sub}</p>` : ''}${cta ? `<div class=cta>${cta}</div>` : ''}</div>`);
const list = (kicker, h, items) => page(kicker, `<div class=l><h1 style="font-size:120px">${h}</h1></div><div class=list>${items.map((t, i) => `<div class=li><span class=n>0${i + 1}</span>${t}</div>`).join('')}</div>`);
const quote = (kicker, t, by) => page(kicker, `<img class=bgmark src="${LOGO}"><div class=q><div class=t>${t}</div><div class=by>${by}</div></div>`);
const poll = (kicker, h, a, b) => page(kicker, `<div class=l><h1 style="font-size:130px">${h}</h1><p class=sub2>Drop your answer in the comments 👇</p></div><div class=poll><div class=opt><div class=k>A</div><div class=v>${a}</div></div><div class=opt><div class=k>B</div><div class=v>${b}</div></div></div>`);

// ---- extra looks so the feed isn't one template on repeat ----
const looks = `
.chat{position:absolute;left:80px;right:80px;top:470px;background:#14181D;border:2px solid #252B33;border-radius:36px;padding:0 0 30px;overflow:hidden}
.chat .top{display:flex;align-items:center;gap:18px;padding:26px 34px;border-bottom:2px solid #252B33;font-family:IN;font-weight:600;font-size:28px}
.chat .top small{display:block;font-weight:400;font-size:22px;color:#8A93A0}
.chat .av{width:58px;height:58px;border-radius:50%;background:#2A3038;display:grid;place-items:center;font-size:28px}
.msg{margin:16px 34px 0;max-width:72%}.msg .who{font-size:20px;color:#8A93A0;margin:0 0 6px 16px}
.msg .b{display:inline-block;background:#2A3038;border-radius:28px;padding:18px 26px;font-size:30px;line-height:1.3}
.msg.me{margin-left:auto;text-align:right}.msg.me .b{background:#2F7CF6}
.msg .ts{font-size:19px;color:#6B7380;margin:8px 0 0 16px}
.sep{text-align:center;color:#6B7380;font-size:21px;margin-top:22px}
.phone2{position:absolute;right:60px;top:300px;width:470px;height:930px;border-radius:64px;background:#05070A;border:10px solid #22272F;box-shadow:0 40px 80px rgba(0,0,0,.6);padding:60px 26px;overflow:hidden}
.phone2 .ttl{font-family:BC;font-weight:700;font-size:30px;letter-spacing:3px;color:#8A93A0;margin:0 8px 20px}
.row2{display:flex;align-items:center;gap:16px;background:#14181D;border:2px solid #252B33;border-radius:22px;padding:20px 20px;margin-bottom:14px;font-size:24px}
.row2 .d{width:16px;height:16px;border-radius:50%;background:#5BD48A;flex:none}.row2 .d.off{background:var(--red)}
.row2 b{font-family:BC;font-weight:700;font-size:28px;letter-spacing:1px;width:110px;flex:none;color:#fff}
.row2 small{margin-left:auto;color:#8A93A0;font-size:19px}
.cal b{width:86px;text-align:center;line-height:1}.cal b span{display:block;font-size:18px;color:var(--red);letter-spacing:2px}
.ph-l{position:absolute;left:80px;top:300px;width:450px}
.ledger{position:absolute;left:80px;right:80px;top:640px;background:#fff;border:2px solid #D6CEBF;border-radius:28px;padding:16px 44px;box-shadow:0 20px 50px rgba(0,0,0,.08)}
.lr{display:flex;align-items:center;padding:24px 0;border-bottom:2px dashed #E3DCCF;font-size:34px;font-weight:500}.lr:last-child{border:0}
.lr .tag{margin-left:auto;font-family:BC;font-weight:700;font-size:28px;letter-spacing:3px;padding:8px 20px;border-radius:999px}
.lr .ok{background:rgba(46,160,90,.12);color:#1F8A4C}.lr .due{background:rgba(224,49,43,.12);color:var(--red)}
`;
const THEMES = {
  paper: `:root{--mute:#6B6F76;--line:#D6CEBF;--panel:#FFFFFF}
body{background:#F1ECE2;color:#15171A}
body:before{content:"";position:absolute;left:0;right:0;top:0;height:14px;background:var(--red);z-index:3}
.tg{color:#6B6F76}.sub2{color:#3C4047!important}.li{box-shadow:0 6px 18px rgba(0,0,0,.06)}
.foot span:last-child{color:#15171A}.bgmark{opacity:.06}`,
  redp: `:root{--mute:rgba(255,255,255,.85);--line:rgba(255,255,255,.45);--panel:rgba(0,0,0,.18)}
body{background:linear-gradient(160deg,#E53A2F 0%,#B81F1A 100%);color:#fff}
h1 em,.opt .k,.kicker i{color:#FFD23F!important}.sub2{color:rgba(255,255,255,.92)!important}.logo b{color:#111}.tg{color:rgba(255,255,255,.85)}
.chev{background:repeating-linear-gradient(-45deg,#111 0 34px,#F2C230 34px 68px)!important}.cta{background:#111!important}.bgmark{opacity:.10}`,
};
const wrapTheme = (theme, html) => html.replace('<div class=bg></div><div class=grid></div>', '') + `<style>${looks}${THEMES[theme]}</style>`;
const paperBig = (kicker, h, sub, cta) => wrapTheme('paper', big(kicker, h, sub, cta));
const paperList = (kicker, h, items) => wrapTheme('paper', list(kicker, h, items));
const redBig = (kicker, h, sub, cta) => wrapTheme('redp', big(kicker, h, sub, cta));
const redPoll = (kicker, h, a, b) => wrapTheme('redp', poll(kicker, h, a, b));
const twoTimes = () => page('<i>●</i> FIREHOUSE LIFE', `<style>
.tt{position:absolute;left:80px;right:80px;top:250px}
.tt h1{font-size:104px}
.clocks{position:absolute;left:80px;right:80px;top:500px;display:grid;grid-template-columns:1fr 1fr;gap:26px}
.ck2{background:var(--panel);border:2px solid var(--line);border-radius:30px;padding:44px 40px 40px}
.ck2 .lb{font-family:BC;font-weight:600;font-size:28px;letter-spacing:4px;color:var(--mute);text-transform:uppercase;line-height:1.3;height:80px}
.ck2 .tm{font-family:BC;font-weight:800;font-size:190px;line-height:.9;margin-top:22px}
.ck2.late{border-color:rgba(224,49,43,.7);box-shadow:0 0 60px rgba(224,49,43,.18)}.ck2.late .tm{color:var(--red)}
.fix{position:absolute;left:80px;right:80px;top:930px;display:flex;align-items:center;gap:30px;font-size:38px;line-height:1.35;color:#D5DAE1}
.fix img{width:110px;flex:none}
.fix b{color:#fff;font-weight:600}
</style>
<div class=tt><h1>Same drill.<br><em>Two different times.</em></h1></div>
<div class=clocks>
<div class=ck2><div class=lb>What the group<br>text said</div><div class=tm>1900</div></div>
<div class="ck2 late"><div class=lb>When half the<br>crew showed up</div><div class=tm>1930</div></div>
</div>
<div class=fix><img src="${LOGO}"><div><b>One alert. Every phone.</b><br>Drill changes go out once, and everyone gets them.</div></div>`);
const groupChat = () => page('<i>●</i> FIREHOUSE LIFE', `<style>${looks}</style>
<div class=l style="top:240px"><h1 style="font-size:112px">The group text<br><em>strikes again.</em></h1></div>
<div class=chat><div class=top><div class=av>🚒</div><div>Station 2 Members<small>34 people</small></div></div>
<div class=msg><div class=who>Capt.</div><div class=b>Drill moved to 1900 tonight. Pass it on.</div><div class=ts>2:14 PM</div></div>
<div class=sep>· · · 86 messages about who's bringing food · · ·</div>
<div class=msg><div class=who>Lt.</div><div class=b>Where is everyone??</div><div class=ts>7:04 PM</div></div>
<div class=msg><div class=who>Probie</div><div class=b>Thought it was 1930 😬</div></div>
<div class=msg><div class=who>Engineer</div><div class=b>What drill</div></div>
</div>`);
const phoneFeature = (kicker, h, sub, ttl, rows) => page(kicker, `<style>${looks}</style>
<div class=ph-l><h1 style="font-size:124px">${h}</h1><p class=sub2>${sub}</p></div>
<div class=phone2><div class=ttl>${ttl}</div>${rows}</div>`);
const ledger = (kicker, h, sub, rows) => wrapTheme('paper', page(kicker, `<div class=l><h1 style="font-size:140px">${h}</h1><p class=sub2>${sub}</p></div>
<div class=ledger>${rows.map(([n, ok]) => `<div class=lr>${n}<span class="tag ${ok ? 'ok' : 'due'}">${ok ? 'PAID' : 'DUE'}</span></div>`).join('')}</div>`));

const TAGS = '#firefighter #firedepartment #volunteerfirefighter #fireservice #firehouse #stationhq';
const ALL = [
  ['04_groupchat', twoTimes(),
    `We've all been there. 😂\n\nWith StationHQ, drill changes go out as one alert and everyone gets the push notification. No buried texts, no "nobody told me."\n\nTag the member who always shows up late 👇\n\n${TAGS}`],
  ['05_grouptexts', paperList('<i>●</i> SIGNS', 'Your station runs<br>on <em>group texts</em>', ['Drill changes get buried', 'Nobody knows who is on duty', 'Cert expirations sneak up', 'Rig check sheets go missing']),
    `How many of these hit home? 👀\n\nStationHQ puts alerts, roster, quals and rig checks in one app built for the firehouse.\n\n60-day free trial for your department. Link in bio.\n\n${TAGS}`],
  ['06_spaceheaters', big('<i>●</i> WINTER SAFETY', 'Space heaters<br>need <em>3 feet.</em>', 'Keep anything that can burn at least 3 feet away from heaters, and turn them off when you leave the room or go to bed.'),
    `Heating season is here, and so are the calls. 🔥\n\nShare this with your community. Keep anything that can burn at least 3 feet from space heaters, plug them straight into the wall, and turn them off before bed.\n\nFeel free to share on your department's page.\n\n#firesafety #winterfiresafety #spaceheater #firedepartment #fireprevention #stationhq`],
  ['07_roster', phoneFeature('<i>●</i> FEATURE', 'Who’s on<br>tonight?<br><em>Know it.</em>', 'Every member sees who’s covering, in real time.', 'TONIGHT · STATION 2',
      [['ENGINE 1', 'Capt + 3 FF', 'full'], ['LADDER', '4 FF', 'full'], ['RESCUE', '2 FF', '1 open'], ['EMS', '2 EMT', 'full'], ['CHIEF', 'Duty chief', 'on call']]
        .map(([u, c, st]) => `<div class=row2><span class="d${st.includes('open') ? ' off' : ''}"></span><b>${u}</b>${c}<small>${st}</small></div>`).join('')),
    `No more texting around to find out who's on. 📋\n\nStationHQ keeps your roster and schedule on every member's phone.\n\nBuilt by an active firefighter. Link in bio.\n\n${TAGS}`],
  ['08_poll_nozzle', wrapTheme('paper', poll('<i>●</i> SETTLE IT', 'Smooth bore<br>or <em>fog?</em>', 'Smooth bore', 'Fog')),
    `The debate that never ends. 🚒💧\n\nA or B? Defend your answer in the comments.\n\n#smoothbore #fognozzle #engineco #firefighter #fireservice #firehouse #stationhq`],
  ['09_dues', ledger('<i>●</i> FEATURE', 'Dues,<br><em>handled.</em>', 'See who’s paid, without the spreadsheet or the awkward reminder at the meeting.', [['Member 01', 1], ['Member 02', 1], ['Member 03', 0], ['Member 04', 1], ['Member 05', 0]]),
    `Treasurers, this one's for you. 💵\n\nTrack member dues in StationHQ, right next to your roster.\n\nFree 60-day trial for your department. Link in bio.\n\n${TAGS}`],
  ['10_alarmtest', big('<i>●</i> SAFETY', 'Test your<br>smoke alarms.<br><em>Monthly.</em>', 'Press the test button once a month. If it doesn’t sound, replace the battery or the alarm.'),
    `A smoke alarm only works if it works. 🔔\n\nShare this reminder with your community: test smoke alarms once a month.\n\nFeel free to share on your department's page.\n\n#smokealarm #firesafety #fireprevention #firedepartment #stationhq`],
  ['11_calendar', phoneFeature('<i>●</i> FEATURE', 'One<br><em style="font-size:100px">calendar.</em>', 'Drills, training and meetings, with reminders that reach every member.', 'THIS WEEK',
      [['TUE', '10', 'Drill · ladder ops', '1900'], ['THU', '12', 'EMS con-ed', '1930'], ['SAT', '14', 'Rig check', '0900'], ['MON', '16', 'Monthly meeting', '1930']]
        .map(([d, n, t, h]) => `<div class="row2 cal"><b><span>${d}</span>${n}</b>${t}<small>${h}</small></div>`).join('')
      + `<div class=row2 style="border-color:rgba(224,49,43,.7);margin-top:30px"><img src="${LOGO}" style="width:40px">Reminder: drill in 1 hr</div>`),
    `If it's not on the calendar, it didn't happen. 📅\n\nStationHQ keeps drills, training and meetings in one calendar with push reminders.\n\nLink in bio.\n\n${TAGS}`],
  ['12_tag', paperBig('<i>●</i> SHOUT OUT', 'Tag the member<br>who <em>never</em><br>misses a call.', 'Every firehouse has one. Give them the credit.'),
    `Every firehouse has that one member. 🙌\n\nTag them below and give them the shout out they deserve.\n\n${TAGS}`],
  ['13_joincode', paperList('<i>●</i> HOW IT WORKS', 'New member?<br><em>Done in a minute.</em>', ['Get your department’s join code', 'Sign up on your phone', 'Admin approves you', 'You’re on the roster']),
    `Onboarding new members shouldn't take a meeting. ✅\n\nWith StationHQ, members join with your department code and admins approve them in the app.\n\nLink in bio.\n\n${TAGS}`],
  ['14_firehouse', list('<i>●</i> FIREHOUSE LIFE', 'Every firehouse<br><em>has one</em>', ['A coffee pot older than the probie', 'A sign-up sheet nobody signs', 'One recliner that’s “taken”', 'A junk drawer full of chargers']),
    `Which one is your station? 😂☕\n\nComment the number, or add one we missed.\n\n${TAGS}`],
  ['15_trial', paperBig('<i>●</i> FREE TRIAL', 'Try it with<br>your whole<br><em>department.</em>', '60 days free. No credit card. Built by an active firefighter for real firehouse workflows.', 'STATIONHQ.APP'),
    `Ready to get off the group texts? 🚒\n\nStart a free 60-day trial for your department. No credit card needed.\n\nLink in bio.\n\n${TAGS}`],
  ['16_cooking', big('<i>●</i> HOLIDAY SAFETY', 'Stay in<br>the <em>kitchen.</em>', 'Cooking is the leading cause of home fires. Don’t leave the stove while frying, boiling or broiling.'),
    `Holiday cooking season is here. 🦃🔥\n\nShare this with your community: stay in the kitchen while you cook, and keep a lid nearby to smother a grease fire. Never use water.\n\n#cookingsafety #greasefire #holidayfiresafety #firesafety #firedepartment #stationhq`],
  ['03b_sendfootage', big('<i>●</i> GET FEATURED', 'Send us your<br><em>fire footage.</em>', 'Working fires, ride-alongs, drills done right. DM us your videos and we’ll feature them with full credit to you and your department.', 'DM @STATIONHQOFFICIAL'),
    `📹 Want your department featured?\n\nSend us your fireground footage: working fires, rig ride-alongs, drills. DM the video to @stationhqofficial with your handle and department.\n\nBy sending it, you're giving us permission to post it. We'll always credit you and tag your page, and we'll take it down anytime you ask.\n\n#firefighter #firedepartment #fireground #workingfire #fireservice #firehouse #stationhq`],
  ['17_founding', big('<i>●</i> CHARTER DEPARTMENTS', 'Lock in your<br><em>founding rate.</em>', 'The first 11 charter departments keep their rate for 3 years.', 'CLAIM A SPOT'),
    `Charter spots are limited. 🔒\n\nThe first 11 departments on StationHQ lock in their rate for 3 years, plus a 60-day free trial.\n\nChiefs and officers, DM us or tap the link in bio.\n\n${TAGS}`],
];

const ONLY = process.env.ONLY;
const posts = ONLY ? ALL.filter(p => p[0] === ONLY) : ALL;

(async () => {
  const out = path.join(__dirname, '../content/queue');
  const b = await chromium.launch();
  const pg = await b.newPage({ viewport: { width: 1080, height: 1350 } });
  for (const [name, html, caption] of posts) {
    await pg.setContent(html, { waitUntil: 'load' });
    await pg.evaluate(() => document.fonts.ready);
    await pg.screenshot({ path: path.join(out, name + '.jpg'), type: 'jpeg', quality: 92 });
    fs.writeFileSync(path.join(out, name + '.txt'), caption + '\n');
  }
  await b.close();
  console.log(`rendered ${posts.length} posts`);
})();
