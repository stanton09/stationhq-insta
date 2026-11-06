"""Read-only checks of the direct API: account, audio search, collaborators support. Posts nothing."""
import json
import graph

me = graph.call("GET", graph.ig_id(), fields="username,followers_count,media_count")
print("Account:", me)
for args in [dict(), dict(query="rock"), dict(query="metal"), dict(audio_type="original_sound")]:
    try:
        res = graph.search_audio(**args)
        print(f"Audio search {args}: {len(res)} results; fields: {sorted(res[0].keys()) if res else '-'}")
        for r in res[:4]:
            print("   ", {k: (str(v)[:60]) for k, v in r.items() if k != 'download_url'})
    except RuntimeError as e:
        print(f"Audio search {args}: FAILED {e}")
try:
    lim = graph.call("GET", f"{graph.ig_id()}/content_publishing_limit", fields="config,quota_usage")
    print("Publishing limit:", lim)
except RuntimeError as e:
    print("Publishing limit check failed:", e)
