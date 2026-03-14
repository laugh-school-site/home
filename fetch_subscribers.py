#!/usr/bin/env python3
"""
fetch_subscribers.py
Fetches the Laugh School Viber channel subscriber count
and patches the number into index.html between the marker comments.

Run locally:  VIBER_TOKEN=your_token python fetch_subscribers.py
Run via CI:   token is read from the VIBER_TOKEN environment variable
"""

import os
import re
import json
import urllib.request
import urllib.error
import sys

VIBER_API = "https://chatapi.viber.com/pa/get_account_info"
HTML_FILE = "index.html"
MARKER_RE = re.compile(
    r"(<!--VIBER_SUBSCRIBERS-->).*?(<!--/VIBER_SUBSCRIBERS-->)",
    re.DOTALL,
)

def fetch_subscribers(token: str) -> int:
    req = urllib.request.Request(
        VIBER_API,
        data=b"{}",
        headers={
            "X-Viber-Auth-Token": token,
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read())

    if data.get("status") != 0:
        raise RuntimeError(f"Viber API error: {data}")

    # Print full response for debugging future issues
    print(f"Viber API response keys: {list(data.keys())}")

    # Try all known field names; handle both int and list responses
    raw = (
        data.get("subscribers_count")
        or data.get("members_count")
        or data.get("total")
        or data.get("members")
        or data.get("subscribers")
        or 0
    )

    # Some endpoints return a list of subscriber objects — count its length
    if isinstance(raw, list):
        return len(raw)

    return int(raw)


def patch_html(count: int) -> None:
    with open(HTML_FILE, "r", encoding="utf-8") as f:
        html = f.read()

    if not MARKER_RE.search(html):
        print(f"ERROR: markers not found in {HTML_FILE}", file=sys.stderr)
        sys.exit(1)

    new_html = MARKER_RE.sub(
        rf"\g<1>{count}\g<2>",
        html,
    )

    with open(HTML_FILE, "w", encoding="utf-8") as f:
        f.write(new_html)

    print(f"✅  Patched {HTML_FILE} with subscriber count: {count}")


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
