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

const TAGS = '#firefighter #firedepartment #volunteerfirefighter #fireservice #firehouse #stationhq';
const ALL = [
  ['04_groupchat', quote('<i>●</i> FIREHOUSE LIFE', 'Group text said drill at 1900. Half the crew showed up at 1930.', '— every volunteer department, at some point'),
    `We've all been there. 😂\n\nWith StationHQ, drill changes go out as one alert and everyone gets the push notification. No buried texts, no "nobody told me."\n\nTag the member who always shows up late 👇\n\n${TAGS}`],
  ['05_grouptexts', list('<i>●</i> SIGNS', 'Your station runs<br>on <em>group texts</em>', ['Drill changes get buried', 'Nobody knows who is on duty', 'Cert expirations sneak up', 'Rig check sheets go missing']),
    `How many of these hit home? 👀\n\nStationHQ puts alerts, roster, quals and rig checks in one app built for the firehouse.\n\n60-day free trial for your department. Link in bio.\n\n${TAGS}`],
  ['06_spaceheaters', big('<i>●</i> WINTER SAFETY', 'Space heaters<br>need <em>3 feet.</em>', 'Keep anything that can burn at least 3 feet away from heaters, and turn them off when you leave the room or go to bed.'),
    `Heating season is here, and so are the calls. 🔥\n\nShare this with your community. Keep anything that can burn at least 3 feet from space heaters, plug them straight into the wall, and turn them off before bed.\n\nFeel free to share on your department's page.\n\n#firesafety #winterfiresafety #spaceheater #firedepartment #fireprevention #stationhq`],
  ['07_roster', big('<i>●</i> FEATURE', 'Who’s on<br>tonight?<br><em>Know it.</em>', 'Roster and scheduling in one place, so every member sees who’s covering, in real time.'),
    `No more texting around to find out who's on. 📋\n\nStationHQ keeps your roster and schedule on every member's phone.\n\nBuilt by an active firefighter. Link in bio.\n\n${TAGS}`],
  ['08_poll_nozzle', poll('<i>●</i> SETTLE IT', 'Smooth bore<br>or <em>fog?</em>', 'Smooth bore', 'Fog'),
    `The debate that never ends. 🚒💧\n\nA or B? Defend your answer in the comments.\n\n#smoothbore #fognozzle #engineco #firefighter #fireservice #firehouse #stationhq`],
  ['09_dues', big('<i>●</i> FEATURE', 'Dues,<br><em>handled.</em>', 'See who’s paid and who hasn’t, without the spreadsheet or the awkward reminder at the meeting.'),
    `Treasurers, this one's for you. 💵\n\nTrack member dues in StationHQ, right next to your roster.\n\nFree 60-day trial for your department. Link in bio.\n\n${TAGS}`],
  ['10_alarmtest', big('<i>●</i> SAFETY', 'Test your<br>smoke alarms.<br><em>Monthly.</em>', 'Press the test button once a month. If it doesn’t sound, replace the battery or the alarm.'),
    `A smoke alarm only works if it works. 🔔\n\nShare this reminder with your community: test smoke alarms once a month.\n\nFeel free to share on your department's page.\n\n#smokealarm #firesafety #fireprevention #firedepartment #stationhq`],
  ['11_calendar', big('<i>●</i> FEATURE', 'Drills. Training.<br>Meetings.<br><em>One calendar.</em>', 'Every event in one place, with reminders that actually reach your members.'),
    `If it's not on the calendar, it didn't happen. 📅\n\nStationHQ keeps drills, training and meetings in one calendar with push reminders.\n\nLink in bio.\n\n${TAGS}`],
  ['12_tag', big('<i>●</i> SHOUT OUT', 'Tag the member<br>who <em>never</em><br>misses a call.', 'Every firehouse has one. Give them the credit.'),
    `Every firehouse has that one member. 🙌\n\nTag them below and give them the shout out they deserve.\n\n${TAGS}`],
  ['13_joincode', list('<i>●</i> HOW IT WORKS', 'New member?<br><em>Done in a minute.</em>', ['Get your department’s join code', 'Sign up on your phone', 'Admin approves you', 'You’re on the roster']),
    `Onboarding new members shouldn't take a meeting. ✅\n\nWith StationHQ, members join with your department code and admins approve them in the app.\n\nLink in bio.\n\n${TAGS}`],
  ['14_firehouse', list('<i>●</i> FIREHOUSE LIFE', 'Every firehouse<br><em>has one</em>', ['A coffee pot older than the probie', 'A sign-up sheet nobody signs', 'One recliner that’s “taken”', 'A junk drawer full of chargers']),
    `Which one is your station? 😂☕\n\nComment the number, or add one we missed.\n\n${TAGS}`],
  ['15_trial', big('<i>●</i> FREE TRIAL', 'Try it with<br>your whole<br><em>department.</em>', '60 days free. No credit card. Built by an active firefighter for real firehouse workflows.', 'STATIONHQ.APP'),
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
