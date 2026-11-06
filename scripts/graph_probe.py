"""Read-only checks of the direct API (audio search variants). Posts nothing."""
import json
import graph

base = {"ig_user_id": graph.ig_id()}
tries = [
    {"audio_type": "music"},
    {"audio_type": "music", "search_query": "rock"},
    {"audio_type": "MUSIC", "search_query": "rock"},
    {"product": "REELS", "audio_type": "music", "search_query": "rock"},
    {"product": "INSTAGRAM", "audio_type": "music", "search_query": "rock"},
    {"product": "CONTENT_PUBLISHING", "audio_type": "music"},
    {"q": "rock"},
    {"search_query": "rock"},
    {"audio_type": "original_sound", "search_query": "fire"},
]
for t in tries:
    try:
        r = graph.call("GET", "ig_audio", **base, **t)
        d = r.get("data", [])
        print(f"{t}: {len(d)} results, keys={sorted(r.keys())} {json.dumps(d[:2])[:300] if d else ''}")
    except RuntimeError as e:
        print(f"{t}: FAILED {str(e)[:260]}")
try:
    print("Permissions:", graph.call("GET", "me/permissions"))
except RuntimeError as e:
    print("Permissions check:", str(e)[:200])
