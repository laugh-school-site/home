#!/usr/bin/env python3
"""
fetch_subscribers.py
Fetches the Laugh School Viber community member count
and patches the number into index.html between the marker comments.
"""

import os
import re
import json
import urllib.request
import sys

HTML_FILE = "index.html"
MARKER_RE = re.compile(
    r"(<!--VIBER_SUBSCRIBERS-->).*?(<!--/VIBER_SUBSCRIBERS-->)",
    re.DOTALL,
)

def viber_post(endpoint: str, token: str, payload: bytes = b"{}") -> dict:
    req = urllib.request.Request(
        f"https://chatapi.viber.com/pa/{endpoint}",
        data=payload,
        headers={
            "X-Viber-Auth-Token": token,
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read())


def fetch_subscribers(token: str) -> int:
    # ── 1. get_account_info ───────────────────────────────────────────────────
    info = viber_post("get_account_info", token)
    print(f"[get_account_info] keys: {list(info.keys())}")
    print(f"[get_account_info] full response: {json.dumps(info, ensure_ascii=False)}")

    # Try every known field
    for field in ("members_count", "subscribers_count", "total", "members", "subscribers"):
        raw = info.get(field)
        if raw is not None:
            count = len(raw) if isinstance(raw, list) else int(raw)
            if count > 0:
                print(f"[get_account_info] using field '{field}' = {count}")
                return count

    # ── 2. get_online (community endpoint — returns present members) ──────────
    try:
        # get_online accepts a list of user IDs; empty body returns community online count
        online = viber_post("get_online", token)
        print(f"[get_online] full response: {json.dumps(online, ensure_ascii=False)}")
        for field in ("users", "members", "total"):
            raw = online.get(field)
            if raw is not None:
                count = len(raw) if isinstance(raw, list) else int(raw)
                if count > 0:
                    print(f"[get_online] using field '{field}' = {count}")
                    return count
    except Exception as e:
        print(f"[get_online] failed: {e}")

    # ── 3. Couldn't determine count ───────────────────────────────────────────
    print("WARNING: could not find a usable member count in any API response.")
    return 0


def patch_html(count: int) -> None:
    with open(HTML_FILE, "r", encoding="utf-8") as f:
        html = f.read()

    if not MARKER_RE.search(html):
        print(f"ERROR: markers not found in {HTML_FILE}", file=sys.stderr)
        sys.exit(1)

    new_html = MARKER_RE.sub(rf"\g<1>{count}\g<2>", html)

    with open(HTML_FILE, "w", encoding="utf-8") as f:
        f.write(new_html)

    print(f"✅  Patched {HTML_FILE} with member count: {count}")


if __name__ == "__main__":
    token = os.environ.get("VIBER_TOKEN", "").strip()
    if not token:
        print("ERROR: VIBER_TOKEN environment variable is not set.", file=sys.stderr)
        sys.exit(1)

    try:
        count = fetch_subscribers(token)
        patch_html(count)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
