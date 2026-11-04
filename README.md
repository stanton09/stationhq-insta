# StationHQ Instagram autopost

Posts to Instagram automatically via GitHub Actions:

| Time (ET) | What |
|---|---|
| 9:07 AM | Next StationHQ post from `content/queue/` |
| 12:07 PM, 4:07 PM, 8:07 PM | Repost from the next account in `accounts.json`, credited `📸 @handle` |

## How it works
- **Your posts:** each post is an image (`.png`/`.jpg`) or video (`.mp4`) in `content/queue/` with a matching `.txt` caption. They post in filename order and move to `content/posted/` afterwards.
- **Reposts:** `scripts/repost.py` takes the newest post from the next account that hasn't been shared yet. It keeps track in `state/reposts.json` so nothing posts twice.
- **Design:** `design/gen.js` renders the branded graphics (logo in `brand/`).

## One-time setup
Posting goes through two free Make.com scenarios (see `scripts/ig.py` for exactly what each does).
1. The repo must be **public** so Instagram can fetch the images.
2. Add two secrets under Settings → Secrets and variables → Actions:
   - `MAKE_PUBLISH_URL`: webhook URL of the "StationHQ publish" scenario
   - `MAKE_LOOKUP_URL`: webhook URL of the "StationHQ lookup" scenario
3. Test: Actions → Instagram autopost → Run workflow → leave "Dry run" checked.

## Notes
- Reposts only work from Business or Creator accounts. Videos with licensed music may be skipped, and carousels share their first slide.
- Get permission from the departments you repost.
