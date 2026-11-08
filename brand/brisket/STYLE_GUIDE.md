# Captain Brisket: series style guide (approved Nov 8, 2026)

Follow this for every new episode so they all look and sound the same. Code: `scripts/brisket_eps.py` (v2 functions: `rigcheck2`, `dues2`, `roster2`, `replyall2`) and `scripts/brisket.py` (shared sounds, faces, end card).

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
