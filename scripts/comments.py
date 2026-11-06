"""Comment replies for @stationhqofficial.

  python comments.py list    -> print new comments on our last 20 posts that we haven't replied to
                                (JSON lines between COMMENTS-START/END), for Claude to write replies
  python comments.py reply   -> post the replies in env PAYLOAD: [{"id": "<comment id>", "message": "..."}]
"""
import json
import os
import pathlib
import sys

import graph

ROOT = pathlib.Path(__file__).resolve().parent.parent
STATE = ROOT / "state" / "comments.json"
state = json.loads(STATE.read_text()) if STATE.exists() else {"done": []}
me = json.loads((ROOT / "state" / "ig_account.json").read_text())["username"]


def list_new():
    media = graph.call("GET", f"{graph.ig_id()}/media", fields="id,caption,permalink,timestamp", limit=20)["data"]
    print("COMMENTS-START")
    n = 0
    for m in media:
        r = graph.call("GET", f"{m['id']}/comments",
                       fields="id,text,username,timestamp,replies{username}", limit=50).get("data", [])
        for c in r:
            if c["id"] in state["done"] or c.get("username") == me:
                continue
            if any(x.get("username") == me for x in (c.get("replies") or {}).get("data", [])):
                continue  # already answered (by you or the bot)
            n += 1
            print(json.dumps({"id": c["id"], "from": c.get("username"), "comment": c.get("text"),
                              "post": (m.get("caption") or "").split("\n")[0][:120], "link": m["permalink"]}))
    print("COMMENTS-END")
    print(f"{n} new comments")


def reply():
    items = json.loads(os.environ.get("PAYLOAD") or "[]")
    for it in items:
        if it["id"] in state["done"]:
            continue
        if it.get("message"):
            graph.call("POST", f"{it['id']}/replies", message=it["message"])
            print(f"Replied to {it['id']}: {it['message']}")
        else:
            print(f"Skipped {it['id']} (no reply)")
        state["done"].append(it["id"])
    state["done"] = state["done"][-3000:]
    STATE.write_text(json.dumps(state, indent=2))


{"list": list_new, "reply": reply}[sys.argv[1]]()
