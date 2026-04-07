#!/usr/bin/env python3
"""Count Emoji and common kaomoji / punctuation clusters in text."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

_EMOJI_RE = re.compile(
    "["
    "\U0001F300-\U0001FAFF"
    "\U00002700-\U000027BF"
    "\U00002600-\U000026FF"
    "\U0001F600-\U0001F64F"
    "\U0001F1E0-\U0001F1FF"
    "\U00002300-\U000023FF"
    "\U0000FE00-\U0000FE0F"
    "\U0000200D"
    "]+"
)

_KAOMOJI = re.compile(r"\([^()\n]{1,24}\)")


def extract_emojis(text: str) -> list[str]:
    return _EMOJI_RE.findall(text)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--file", required=True, help="Input .txt path")
    p.add_argument("--output", required=True, help="Output JSON path")
    p.add_argument("--top", type=int, default=40, help="Top N emoji")
    args = p.parse_args()

    path = Path(args.file)
    if not path.is_file():
        raise SystemExit(f"File not found: {path}")

    text = path.read_text(encoding="utf-8", errors="replace")
    emojis = extract_emojis(text)
    emoji_counts = Counter(emojis).most_common(args.top)

    kao = _KAOMOJI.findall(text)
    kao_counts = Counter(kao).most_common(20)

    payload = {
        "source": str(path.resolve()),
        "emoji_total_occurrences": len(emojis),
        "emoji_top": [{"glyph": g, "count": c} for g, c in emoji_counts],
        "kaomoji_top": [{"glyph": g, "count": c} for g, c in kao_counts],
    }

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
