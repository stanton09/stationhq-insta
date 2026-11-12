# Captain Brisket & Nozzle — Fire Safety Book Series Notes

Running notes for the kids' book series (about 7 more books planned). Read this before starting a new book.
Book 1 build scripts and fonts: `book1-nozzles-big-night/`.

---

## The series

- **Series name (KDP "Series" field):** A Captain Brisket & Nozzle Fire Safety Story
- **Publisher / copyright holder:** JDX Group LLC (StationHQ brand). Copyright line: "Copyright © 20XX JDX Group LLC. All rights reserved."
- **Author name on KDP:** Jesse Stanton. Use "Written by a real firefighter" on covers.
- **Audience:** ages 3 to 7
- **Goal of each book:** one fire-safety theme, taught through a short story. The kid earns a **badge** at the end. Book 1 = **Escape Badge**.
- **Links printed in the books:** stationhq.app · shop.stationhq.app

## Characters (keep consistent)

- **Captain Brisket:** veteran firefighter, 34 years on the job. Big mustache, quiet, few words, dry humor ("About thirty years." / "...Good." / "Probably."). Always has coffee. Smiles "under the mustache."
- **Nozzle:** Dalmatian puppy. Talks a LOT, eager, wants a "real badge." He is **Mia's dog**. Mia is his favorite person. (Owner correction: NOT "Mia's best friend.")
- **Station 12 / Engine 12:** Captain Brisket's firehouse and engine.
- **The Riveras:** Nozzle's family. Mia (girl), Dad, baby Leo. Meeting spot: the big oak tree.
- Tone: short sentences, a funny beat on most pages, never scary. Sound words in red comic type (BRRRING!, BEEP! BEEP! BEEP!, STOP! DROP! ROLL!).

## Book 1: Nozzle's Big Night (Escape Badge), published Nov 2026

- **The 8 Station 12 Rules** (one per rule page, red "STATION 12 RULE #" box):
  1. When the smoke alarm beeps, get out and stay out.
  2. Get low and go.
  3. Know two ways out of every room.
  4. Pick a meeting spot outside.
  5. Never hide. Never go back in.
  6. If your clothes catch fire: stop, drop and roll.
  7. Firefighters are your friends.
  8. Get outside, then call 9-1-1.
- **Story arc:** Nozzle wants a badge → Captain teaches the rules at the station → Nozzle teaches his family, they draw an escape plan → night-time smoke alarm → family gets out, meets at the oak tree → it was Captain Brisket's **practice drill** with a stopwatch ("Two minutes, ten seconds. ...Good.") → Nozzle earns his badge → naps at the station: "Good work, Firefighter Nozzle."
- **Back matter:** Captain Brisket's Checklist for Grown-Ups (test alarms monthly, two ways out, meeting spot, drill twice a year once at night, get low/never hide/never go back in, kids know address + 9-1-1), Escape Badge certificate ("knows all 8 Station 12 Rules and has earned the Escape Badge!"), and the series page.
- **Series page (printed, can't change for this edition):** Badge 1 = Escape Badge (Nozzle's Big Night). Badges 2–6 = "Badge #N / Coming soon" with a "?". Owner rejected specific names like "Hands Off," "Dispatcher," "Station 12" badges. Future badge names must make sense with the actual book topics.

## Owner feedback to carry forward

- **No speech bubbles.** Layout = picture on the left page, story on the right page, on a styled story panel.
- Story pages: diamond-plate red border, yellow/silver rings, cream panel, Maltese cross watermark, rivets; a round character portrait with a name ribbon; rule box when the page teaches a rule.
- Keep text short. Pages with portraits get crowded, so shrink portraits or cut words.
- Pictures must match the text exactly (book 1 fixes: "get low" page was unclear → show crawling, not hiding under the couch; stop-drop-roll art had to show the real move; the mop-and-bucket slip "is not funny"; fix the fire truck on the drill page).
- Explain plot points clearly (the drill page had to say it was a practice drill so the family could practice).
- Owner makes the illustrations himself (AI image tool) from a scene list we write. Kids won't question small things (a smoke machine for the drill is fine).
- AI disclosure on KDP: text and images were AI-assisted. Tool to name for text = **Claude** (not ChatGPT).

## Specs (KDP paperback)

- Trim **8.5 x 8.5 in**, premium color, white paper, bleed, glossy cover. (8.5x8.5 is paperback only on KDP.)
- Interior pages built at 2588 x 2625 px (8.625 x 8.75 in at 300 dpi, with bleed). Book 1 = **46 pages**.
- Cover = one full wrap: width = 0.125 + 8.5 + spine + 8.5 + 0.125 in; height = 8.75 in. Spine = pages x 0.002347 in (46 pages = 0.108 in → 17.358 x 8.75 in = 5207 x 2625 px).
- **Leave no barcode placeholder**; KDP adds its own white box bottom-right of the back cover.
- Price: **$12.99** list (KDP printing ~$4.68, royalty ~$3.11). Raise after reviews if wanted. Expanded Distribution off.
- Hardcover later through **IngramSpark** (needs his own Bowker ISBN in JDX Group LLC's name, PDF/X-1a CMYK).
- Cover processing in KDP can take 5–10+ minutes; that's normal.

## Files and fonts

- Fonts: Fredoka (story text, variable weight), Bangers (sound words / title). In `book1-nozzles-big-night/fonts/`.
- Scripts in `book1-nozzles-big-night/scripts/`: `textpage.py` (story pages + STORY dict), `portraits.py` (portrait crop per page), `frontback.py` (title, copyright, belongs-to, checklist, certificate, series page, builds the interior PDF), `cover.py` (full wrap).
- Art (20 scenes, a01–a20) and the final PDFs live in the owner's **OneDrive\Desktop\Kids Book** folder (too big for the repo).
- Related: there is also a Captain Brisket & Nozzle **coloring book** (separate KDP listing).

## Ideas for future books (not decided; badges must match topics)

- Kitchen / cooking safety · Matches & lighters ("tell a grown-up") · Calling 9-1-1 and knowing your address · Smoke alarm testing at home · Campfire / outdoor safety · Holiday safety (candles, trees) · Meeting the fire truck and gear (firefighters are friends)

## Process checklist for each new book

1. Pick the topic and badge name; confirm with owner.
2. Write the story (20 scenes like book 1) and a scene list for the art; owner approves.
3. Owner makes the 20 images; check each matches its text.
4. Build pages with the book 1 scripts (update STORY, portraits, title, badge, certificate, series page).
5. Preview spreads; owner reviews every page; fix.
6. Build interior + cover PDFs at the right page count / spine width.
7. KDP: same series name, new book number; owner uploads and publishes.
8. Add it to the shop's Books section and make launch posts.
