"""One-time setup: turn the short-lived user token (secret META_USER_TOKEN) into a never-expiring
Page token for the StationHQ page, verify it can see @stationhqofficial, and store it encrypted in
state/ig_token.enc (key = secret META_APP_SECRET). Tokens are never printed."""
import json
import os
import pathlib
import subprocess
import urllib.parse
import urllib.request

GRAPH = "https://graph.facebook.com/v21.0"
ROOT = pathlib.Path(__file__).resolve().parent.parent
user_token = os.environ["META_USER_TOKEN"].strip()
secret = os.environ["META_APP_SECRET"].strip()


def get(path, **params):
    url = f"{GRAPH}/{path}?{urllib.parse.urlencode(params)}"
    try:
        with urllib.request.urlopen(url, timeout=60) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        body = json.loads(e.read() or b"{}")
        raise SystemExit(f"Graph error on {path}: {body.get('error', {}).get('message', e)}")


def mask(v):
    print(f"::add-mask::{v}")


mask(user_token); mask(secret)
app = get("app", access_token=user_token)
print(f"App: {app.get('name')} ({app['id']})")
long = get("oauth/access_token", grant_type="fb_exchange_token", client_id=app["id"],
           client_secret=secret, fb_exchange_token=user_token)["access_token"]
mask(long)
pages = get("me/accounts", fields="name,access_token,instagram_business_account", access_token=long)["data"]
for p in pages:
    mask(p["access_token"])
print("Pages:", ", ".join(f"{p['name']} (IG: {'yes' if p.get('instagram_business_account') else 'no'})" for p in pages))
page = next((p for p in pages if p.get("instagram_business_account")), None)
if not page:
    raise SystemExit("No page with a linked Instagram account was shared with the app.")
ig_id = page["instagram_business_account"]["id"]
me = get(ig_id, fields="username,followers_count", access_token=page["access_token"])
print(f"Instagram: @{me['username']} ({me.get('followers_count')} followers), id {ig_id}")
dbg = get("debug_token", input_token=page["access_token"], access_token=f"{app['id']}|{secret}")["data"]
exp = dbg.get("expires_at", 0)
print(f"Token expires: {'never' if not exp else exp}; scopes: {', '.join(dbg.get('scopes', []))}")
subprocess.run(["openssl", "enc", "-aes-256-cbc", "-pbkdf2", "-salt", "-pass", "env:META_APP_SECRET",
                "-out", str(ROOT / "state" / "ig_token.enc")], input=page["access_token"].encode(), check=True)
(ROOT / "state" / "ig_account.json").write_text(json.dumps({"ig_user_id": ig_id, "username": me["username"],
                                                            "page": page["name"], "app_id": app["id"]}, indent=2))
print("Saved encrypted page token to state/ig_token.enc")
