"""Tiny Instagram Graph API helper (Instagram API with Facebook Login)."""
import json
import os
import time
import urllib.parse
import urllib.request

VERSION = os.environ.get("GRAPH_VERSION", "v23.0")
BASE = f"https://graph.facebook.com/{VERSION}"
TOKEN = os.environ["IG_ACCESS_TOKEN"]
IG_USER = os.environ["IG_USER_ID"]


def _call(method, path, params=None):
    params = dict(params or {})
    params["access_token"] = TOKEN
    data = urllib.parse.urlencode(params).encode()
    url = f"{BASE}/{path}"
    if method == "GET":
        req = urllib.request.Request(f"{url}?{data.decode()}")
    else:
        req = urllib.request.Request(url, data=data, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"{method} {path} failed: {e.read().decode()}") from None


def get(path, **params):
    return _call("GET", path, params)


def post(path, **params):
    return _call("POST", path, params)


def _wait_ready(container_id, timeout=600):
    """Videos/reels process asynchronously; poll until FINISHED."""
    start = time.time()
    while time.time() - start < timeout:
        status = get(container_id, fields="status_code").get("status_code")
        if status == "FINISHED":
            return
        if status in ("ERROR", "EXPIRED"):
            raise RuntimeError(f"container {container_id} status {status}")
        time.sleep(10)
    raise RuntimeError(f"container {container_id} timed out")


def _container(media_type, url, caption=None, carousel_item=False):
    params = {}
    if caption is not None:
        params["caption"] = caption
    if carousel_item:
        params["is_carousel_item"] = "true"
    if media_type == "IMAGE":
        params["image_url"] = url
    else:  # VIDEO -> post as a Reel
        params["media_type"] = "VIDEO" if carousel_item else "REELS"
        params["video_url"] = url
    cid = post(f"{IG_USER}/media", **params)["id"]
    if media_type != "IMAGE":
        _wait_ready(cid)
    return cid


def publish(items, caption):
    """items: list of (media_type, public_url). One item = single post, 2-10 = carousel."""
    if len(items) == 1:
        cid = _container(items[0][0], items[0][1], caption)
    else:
        children = [_container(t, u, carousel_item=True) for t, u in items[:10]]
        cid = post(f"{IG_USER}/media", media_type="CAROUSEL", caption=caption,
                   children=",".join(children))["id"]
        _wait_ready(cid)
    return post(f"{IG_USER}/media_publish", creation_id=cid)["id"]


def recent_media(username, limit=8):
    """Public posts of another Business/Creator account via Business Discovery."""
    fields = (f"business_discovery.username({username})"
              f"{{media.limit({limit}){{id,caption,media_type,media_url,permalink,timestamp,"
              f"children{{media_type,media_url}}}}}}")
    return get(IG_USER, fields=fields)["business_discovery"]["media"]["data"]
