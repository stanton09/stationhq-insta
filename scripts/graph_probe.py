"""Read-only: show what Instagram's audio search returns. Posts nothing."""
import json
import graph
r = graph.call("GET", "ig_audio", ig_user_id=graph.ig_id(), audio_type="music", search_query="rock")
print("RAW:", json.dumps(r)[:1500])
for q in [None, "rock", "metal", "hard rock", "epic", "intense"]:
    res = graph.search_audio(q)
    print(f"{q}: {len(res)}")
    for x in res[:5]:
        print("   ", json.dumps({k: v for k, v in x.items() if 'url' not in k})[:240])
