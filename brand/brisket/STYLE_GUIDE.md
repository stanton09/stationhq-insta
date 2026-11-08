# Captain Brisket: series style guide (approved Nov 8, 2026)

Follow this for every new episode so they all look and sound the same. Code: `scripts/brisket_eps.py` (v2 functions: `rigcheck2`, `dues2`, `roster2`, `replyall2`) and `scripts/brisket.py` (shared sounds, faces, end card).

## Rules (from the owner, Nov 8)
- **Not the same concept over and over.** Rotate shapes; never two episodes in a row with the same one:
  1. Problem -> Roy boils -> StationHQ fixes it (max about one a month: Group Chat, Rig Check, Dues)
  2. Rate the excuse (score cards, twist on the last one)
  3. Roy reads the comments
  4. Probie vs. Captain (split screen)
  5. Roy explains (grumpy 15-s lesson)
  6. Kevin's first... (running series, "part 2" cliffhangers)
- **Not corny:** deadpan (Roy barely reacts), jokes from real firehouse life, punchline LAST, no explaining the joke.
  Steam / mustache dance / "YES CAP!!!" are signature beats: use about two per episode, not all.
- StationHQ appears only when it's part of the joke (about one in three episodes). Others end on a comment-bait card.
- Length: about 20-30 s, same as the approved episodes.
- One Brisket episode a week at most. Owner approves every preview before it posts.

## Format
- 1080x1920, 30 fps, about 25-28 s. Vertical Reel (also works as a Story).
- Beat order: **hook (2 s) → setup → crew chaos → Kevin makes it worse → Roy boils (steam close-up) → "NOW WITH STATIONHQ" fix → end card.**
- Hook: two lines, Barlow Condensed, black then red, on a cream panel at the top: "WHEN THE ___ / ___…"
- End card: StationHQ logo, two-line headline (black/red), "Keep your station updates simple.", red "FOLLOW FOR MORE CAPTAIN BRISKET" pill, Roy's head popping up with the mustache dance and a real "ta-da".

## Framing (approved after 3 tries)
- Rooms: scale the ChatGPT background to exactly the screen height (`roomfit()`), no stretching (a stretched floor leaves a blurry seam). The camera pans across it. The people are made big, not the room small.
- People: Roy about **1520 px tall**, Kevin about **1420 px**, cut off around the shins (bottom = screen + 260). They should fill most of the frame, waist-up reading clearly on a phone. Roy left, Kevin right.
- When a big prop fills the top (the whiteboard), people a bit smaller (Roy 1200, Kevin 1130).
- Text bubbles go above heads or beside them, never on a face. Captions sit on a cream panel so they read over busy rooms.

## Art
- Only art made in ChatGPT from `Roy_Approved_Master_Transparent.png`. Never hand-draw or edit faces.
- Ask ChatGPT for: "plain flat light-gray background, no white outline around the character, no text".
- Save full-size images from ChatGPT to Downloads (pasted images arrive small).
- Cut-outs must be checked on a bright magenta background: no gray between arms/legs, no white rim.
- Keep every original in `originals_chatgpt/`, cut-outs in `cutouts/`, rooms in `backgrounds/`.

## Sound
- Music: one Kevin MacLeod track per episode (incompetech, CC BY 4.0, credit in the caption), loud (85%) under the effects. Don't reuse the last episode's track.
- Real recorded effects (Pixabay): truck air horn "honk HONK" for the StationHQ alert, "grrr" when Roy gets mad, "ta-da" on the end card. Synth effects: bubble pops, record scratch at the "wait…what?" line, kettle whistle with the ear steam, stamps, dings.
- No sound effects during the mustache dance except the ta-da.

## Characters
- **Capt. Roy Brisket**: 34 years on the job, deadpan, mustache, few words. Verdict lines in quotes, like a report: "Message status: buried. Cause: group text."
- **Kevin (probie)**: too eager ("YES CAP!!!"), causes the problem, sweats when caught.
- Crew names used so far: Marco, Donna, Pete, Sully, Darcy, Nick, Big Mike, Rosa, T.J., Jenkins, McCarron.
- New characters: make a ChatGPT sheet (4 full-body poses + 4 heads) from the master, add to `cutouts/`, add a line here.

## Captions
Roy's voice, one line of setup, a "tag the guy who…" line, then "StationHQ: … Link in bio." and the music credit, 5-6 hashtags ending #stationhq.

## Owner feedback log
- Group Chat (problem -> app fix): approved, posting Nov 9.
- Rate the Excuse: "not bad". Twist ending on Kevin works.
- Probie vs. Captain (split screen, one tap): "pretty good". The best app plug so far: the app IS the punchline.
- Roy Explains StationHQ (feature list with one-liners): rejected, "don't like it at all". Don't make feature-list/explainer ads.
- Lesson: the app works when it's the punchline of a real firehouse situation, not when Roy lists features.

## Show format: "STATION 12" (approved direction Nov 8)
Every episode is wrapped like a mockumentary / reality show:
1. Cold open on the funniest frame (no slow intro, no logo first). Big hook text.
2. Freeze frame + record scratch, B&W, subtitle "Yep. That's me. / You're probably wondering how I got here."
3. VHS rewind "<< X HOURS EARLIER".
4. Title card: STATION 12 / EPISODE N / title.
5. Story with handheld drift on every shot, a change of view every 2-3 s.
6. One "look to camera" cutaway (Roy deadpan into the lens) mid-chaos, snap zoom.
7. Documentary crash zoom on the key line.
8. Confessional (talking head) in the office with name strip (red name / black title). Music ducks to near silence for the first beat.
9. Payoff, end card.
Editing rules from research: hook decided in ~1.5-3 s; cut/angle change every 2-3 s but vary the type of change;
cut to the reaction right after the line; sound effect lands exactly on the cut; silence after a key line; don't overuse confessionals (one per episode).
Most viewers start with sound off: all jokes must read as on-screen text.

## Research playbook (Nov 8): reports/Animated firehouse series playbook.md
Key rules adopted: no title card/logo before the hook (show name rides as a small chyron); contradiction cut to a deadpan talking head;
one look-to-camera; camera zooms in a few frames late; silence/ambience drop on Roy's deadpan; goal of every episode = something a firefighter SENDS to the crew chat (sends are Instagram's top reach signal); caption CTA asks for a send; test openings with Trial Reels; app shows up in about 1 in 5 episodes, as a prop.
