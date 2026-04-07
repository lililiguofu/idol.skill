#!/usr/bin/env python3
"""
Weverse / Phoning fetch helper — requires user-supplied credentials.

Without WEVERSE_COOKIE (or --cookie), exits with code 2 and prints setup instructions.
Optional dry-run lists what would be requested when configured.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

try:
    import requests
except ImportError:
    requests = None  # type: ignore


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--url",
        default="",
        help="Optional post URL to fetch (Weverse web). Requires cookie.",
    )
    p.add_argument(
        "--cookie",
        default="",
        help="Cookie header value; overrides env WEVERSE_COOKIE.",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Only validate env and print the request plan; no network.",
    )
    args = p.parse_args()

    cookie = args.cookie or os.environ.get("WEVERSE_COOKIE", "").strip()

    if args.dry_run:
        print("[parse_weverse] dry-run: no HTTP request performed.")
        print(f"  cookie set: {bool(cookie)}")
        print(f"  url: {args.url or '(none)'}")
        sys.exit(0)

    if not cookie:
        print(
            "Weverse 抓取需要用户自行配置 Cookie。\n"
            "  设置环境变量 WEVERSE_COOKIE，或使用：\n"
            "    python tools/parsers/parse_weverse.py --cookie \"<从浏览器复制的 Cookie>\" --url \"<帖子URL>\"\n"
            "请遵守 Weverse 服务条款与当地法律；勿分享 Cookie 给他人。\n"
            "依赖：pip install requests（见 requirements.txt）",
            file=sys.stderr,
        )
        sys.exit(2)

    if requests is None:
        print("Missing dependency: requests. Run: pip install -r requirements.txt", file=sys.stderr)
        sys.exit(1)

    if not args.url:
        print("Provide --url when cookie is set, or use --dry-run to test config.", file=sys.stderr)
        sys.exit(2)

    headers = {
        "User-Agent": "idol-skill-parse-weverse/1.0",
        "Cookie": cookie,
    }
    r = requests.get(args.url, headers=headers, timeout=30)
    r.raise_for_status()
    text = r.text
    snippet = text[:2000].replace("\n", " ")
    print(
        json.dumps(
            {
                "bytes": len(text),
                "snippet": snippet,
                "note": "raw HTML/text; parse as needed locally",
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
