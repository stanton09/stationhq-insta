"""Daily repost picks: find the best live-fire Reels and open a GitHub issue with tap-to-open links.

You repost them yourself with Instagram's Repost button (allowed by Instagram; the creator's own
"Allow reposts" setting decides). Nothing is posted by this script.

To stay inside Make's free plan it checks up to PICKS_PER_DAY_ACCOUNTS accounts per day, rotating
through the `picks` list in accounts.json.
"""
import datetime as dt
import json
import os
import pathlib
import urllib.request

import ig
from filters import FIRE_WORDS, SKIP_WORDS  # same live-fire filters as automatic reposts

ROOT = pathlib.Path(__file__).resolve().parent.parent
CFG = json.loads((ROOT / "accounts.json").read_text())
ACCOUNTS = CFG.get("picks", [])
STATE_FILE = ROOT / "state/picks.json"
state = json.loads(STATE_FILE.read_text()) if STATE_FILE.exists() else {"next": 0, "picked": []}
REPOSTED = set(json.loads((ROOT / "state/reposts.json").read_text()).get("shared", [])) \
    if (ROOT / "state/reposts.json").exists() else set()
PER_DAY = int(os.environ.get("PICKS_PER_DAY_ACCOUNTS", "6"))
WANT = 4
MAX_AGE_DAYS = 45

now = dt.datetime.now(dt.timezone.utc)
start = state["next"] % max(len(ACCOUNTS), 1)
today = [ACCOUNTS[(start + i) % len(ACCOUNTS)] for i in range(min(PER_DAY, len(ACCOUNTS)))]
state["next"] = (start + len(today)) % max(len(ACCOUNTS), 1)

found = []
for user in today:
    try:
        media = ig.recent_media(user)
    except RuntimeError as e:
        print(f"Skipping @{user}: {e}")
        continue
    for m in media:
        cap = m.get("caption", "")
        if m["media_type"] != "VIDEO" or m["id"] in state["picked"] or m["id"] in REPOSTED:
            continue
        if SKIP_WORDS.search(cap) or not FIRE_WORDS.search(cap):
            continue
        try:
            if (now - dt.datetime.fromisoformat(m["timestamp"].replace("Z", "+00:00"))).days > MAX_AGE_DAYS:
                continue
        except ValueError:
            pass
        score = float(m.get("view_count") or 0) / 20 + float(m.get("like_count") or 0)
        found.append((score, user, m))

found.sort(key=lambda x: -x[0])
picks, used = [], set()
for score, user, m in found:  # at most one per account for variety, then fill
    if user not in used:
        picks.append((user, m)); used.add(user)
    if len(picks) == WANT:
        break
for score, user, m in found:
    if len(picks) == WANT:
        break
    if (user, m) not in picks:
        picks.append((user, m))

date = dt.datetime.now(dt.timezone(dt.timedelta(hours=-5))).strftime("%a %b %-d")
if picks:
    lines = [f"Tap each link, then tap the **Repost** button (two arrows) under the Reel.\n"]
    for i, (user, m) in enumerate(picks, 1):
        cap = (m.get("caption") or "")[:120]
        lines.append(f"### {i}. @{user}\n[▶️ Open in Instagram]({m['permalink']})\n> {cap}\n")
    body = "\n".join(lines)
    title = f"🔥 Repost picks for {date} ({len(picks)})"
else:
    body = "No new live-fire Reels today from the accounts checked. Send Claude more pages to add to the picks list."
    title = f"Repost picks for {date}: none today"

print(title)
print(body)

if os.environ.get("DRY_RUN"):
    raise SystemExit(0)

token, repo = os.environ["GITHUB_TOKEN"], os.environ["GITHUB_REPOSITORY"]


def gh(method, path, payload=None):
    req = urllib.request.Request(f"https://api.github.com/repos/{repo}{path}", method=method,
                                 data=json.dumps(payload).encode() if payload else None,
                                 headers={"Authorization": f"Bearer {token}",
                                          "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


for old in gh("GET", "/issues?state=open&labels=repost-picks"):  # close yesterday's list
    gh("PATCH", f"/issues/{old['number']}", {"state": "closed"})
issue = gh("POST", "/issues", {"title": title, "body": body, "labels": ["repost-picks"],
                               "assignees": [repo.split("/")[0]]})
print(f"Opened {issue['html_url']}")

state["picked"] = (state["picked"] + [m["id"] for _, m in picks])[-1000:]
STATE_FILE.parent.mkdir(exist_ok=True)
STATE_FILE.write_text(json.dumps(state, indent=2))
