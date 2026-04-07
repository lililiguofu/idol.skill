#!/usr/bin/env python3
"""Fan-sign / 1v1 transcript heuristics: speaker split, mode tags, simple 'entities'."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

_SPEAKER = re.compile(
    r"^(?P<label>粉丝|用户|User|我|爱豆|艺人|Artist|Idol|Bias)[\s:：]\s*(?P<body>.+)$",
    re.I,
)

_CARING = re.compile(r"谢谢|感谢|爱你|辛苦|加油|抱抱|心疼|注意身体", re.I)
_ENERGETIC = re.compile(r"哈哈|嘿嘿|哇|耶|冲|最棒|厉害", re.I)
_LISTENING = re.compile(r"嗯嗯|原来|这样啊|说说|告诉我|听到", re.I)


def split_speakers(lines: list[str]) -> tuple[list[str], list[str]]:
    fan: list[str] = []
    idol: list[str] = []
    for raw in lines:
        line = raw.strip()
        if not line:
            continue
        m = _SPEAKER.match(line)
        if m:
            lab = m.group("label").lower()
            body = m.group("body")
            if lab in ("粉丝", "用户", "user", "我"):
                fan.append(body)
            elif lab in ("爱豆", "艺人", "artist", "idol", "bias"):
                idol.append(body)
            else:
                fan.append(body)
            continue
        idol.append(line)
    return fan, idol


def mode_tags(idol_text: str) -> dict[str, float]:
    t = idol_text
    scores = {
        "caring": len(_CARING.findall(t)),
        "energetic": len(_ENERGETIC.findall(t)),
        "listening": len(_LISTENING.findall(t)),
    }
    total = sum(scores.values()) or 1
    return {k: round(v / total, 3) for k, v in scores.items()}


def guess_entities(text: str) -> list[str]:
    found: list[str] = []
    for pat in (
        r"叫我\s*([\u4e00-\u9fffA-Za-z]{1,12})",
        r"昵称[是为]?\s*([\u4e00-\u9fffA-Za-z]{1,12})",
        r"[「\"]([\u4e00-\u9fffA-Za-z]{1,12})[」\"]",
    ):
        found.extend(re.findall(pat, text))
    seen = set()
    out = []
    for x in found:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out[:20]


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--file", required=True, help="Path to transcript .txt")
    p.add_argument("--output", required=True, help="Output JSON path")
    args = p.parse_args()

    path = Path(args.file)
    if not path.is_file():
        raise SystemExit(f"File not found: {path}")

    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    fan_lines, idol_lines = split_speakers(lines)
    fan_text = "\n".join(fan_lines)
    idol_text = "\n".join(idol_lines)

    payload = {
        "source": str(path.resolve()),
        "stats": {
            "fan_line_count": len(fan_lines),
            "idol_line_count": len(idol_lines),
            "fan_char_count": len(fan_text),
            "idol_char_count": len(idol_text),
        },
        "interaction_modes": mode_tags(idol_text),
        "entities_guess": guess_entities(fan_text + "\n" + idol_text),
        "note": "Heuristic only; refine in persona.md by hand.",
    }

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
