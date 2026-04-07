#!/usr/bin/env python3
"""Fetch a public baseline summary from Wikipedia REST API (user-confirmed title)."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from urllib.parse import quote

try:
    import requests
except ImportError:
    requests = None  # type: ignore

# zh.wikipedia.org — change wiki via --wiki if needed
DEFAULT_WIKI = "zh.wikipedia.org"


def fetch_summary(title: str, wiki_host: str) -> dict:
    if requests is None:
        raise SystemExit("Missing dependency: requests. Run: pip install -r requirements.txt")
    encoded = quote(title.replace(" ", "_"), safe="()%")
    url = f"https://{wiki_host}/api/rest_v1/page/summary/{encoded}"
    r = requests.get(
        url,
        headers={"User-Agent": "idol-skill-baseline/1.0 (local fan project; contact: local)"},
        timeout=30,
    )
    if r.status_code == 404:
        raise SystemExit(f"Page not found: {title!r} on {wiki_host}")
    r.raise_for_status()
    return r.json()


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--title", required=True, help="Exact Wikipedia page title (user must confirm disambiguation)")
    p.add_argument("--wiki", default=DEFAULT_WIKI, help=f"Wikipedia host (default: {DEFAULT_WIKI})")
    p.add_argument("--output", default="", help="Write JSON to this path instead of stdout")
    args = p.parse_args()

    data = fetch_summary(args.title.strip(), args.wiki.strip())
    extract = data.get("extract") or ""
    source_url = data.get("content_urls", {}).get("desktop", {}).get("page") or data.get("titles", {}).get(
        "canonical", ""
    )
    payload = {
        "title": args.title,
        "wiki": args.wiki,
        "summary": extract,
        "source_url": source_url,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "note": "Public baseline only; supplement with private corpus for voice fidelity.",
    }
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    if args.output:
        from pathlib import Path

        Path(args.output).write_text(text, encoding="utf-8")
        print(f"Wrote {args.output}", file=sys.stderr)
    else:
        print(text)


if __name__ == "__main__":
    main()
