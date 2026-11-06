"""Direct Instagram Graph API client (Facebook Login page token, stored encrypted in state/ig_token.enc).
Supports what Make can't: Instagram music (Audio API) and collab invites."""
import json
import os
import pathlib
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request

GRAPH = "https://graph.facebook.com/v26.0"
ROOT = pathlib.Path(__file__).resolve().parent.parent
ENC = ROOT / "state" / "ig_token.enc"
ACCOUNT = ROOT / "state" / "ig_account.json"


def available():
    return ENC.exists() and ACCOUNT.exists() and bool(os.environ.get("META_APP_SECRET"))


def _token():
    t = subprocess.run(["openssl", "enc", "-d", "-aes-256-cbc", "-pbkdf2", "-pass", "env:META_APP_SECRET",
                        "-in", str(ENC)], capture_output=True, check=True).stdout.decode().strip()
    print(f"::add-mask::{t}")
    return t


def ig_id():
    return json.loads(ACCOUNT.read_text())["ig_user_id"]


def call(method, path, **params):
    params["access_token"] = _token()
    data = None
    url = f"{GRAPH}/{path}"
    if method == "GET":
        url += "?" + urllib.parse.urlencode(params)
    else:
        data = urllib.parse.urlencode(params).encode()
    try:
        with urllib.request.urlopen(urllib.request.Request(url, data=data, method=method), timeout=120) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        try:
            err = json.loads(e.read()).get("error", {})
        except Exception:
            err = {}
        raise RuntimeError(f"Graph {method} {path.split('?')[0]}: {err.get('message', e)} "
                           f"(code {err.get('code')}/{err.get('error_subcode')})")


def search_audio(query=None, audio_type="music", limit=10):
    params = {"audio_type": audio_type, "limit": limit}
    if query:
        params["search_query"] = query
    return call("GET", "ig_audio", **params).get("data", [])


def publish(kind, url, caption, collaborators=None, audio=None, share_to_feed=True):
    """kind IMAGE or REELS. collaborators: up to 3 usernames (they get a collab invite).
    audio: dict for audio_configuration, e.g. {"audio_id": "...", "audio_volume": 60, "video_volume": 100}."""
    p = {"caption": caption}
    if kind == "REELS":
        p.update(media_type="REELS", video_url=url, share_to_feed="true" if share_to_feed else "false")
        if audio:
            p["audio_configuration"] = json.dumps(audio)
    else:
        p["image_url"] = url
    if collaborators:
        p["collaborators"] = json.dumps(list(collaborators)[:3])
    container = call("POST", f"{ig_id()}/media", **p)["id"]
    for _ in range(60):  # video processing
        st = call("GET", container, fields="status_code,status").get("status_code")
        if st == "FINISHED":
            break
        if st == "ERROR":
            raise RuntimeError(f"Instagram couldn't process the media: {call('GET', container, fields='status')}")
        time.sleep(10)
    media = call("POST", f"{ig_id()}/media_publish", creation_id=container)["id"]
    return media
