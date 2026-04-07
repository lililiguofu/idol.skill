#!/usr/bin/env python3
"""Parse plain-text Bubble/chat exports: punctuation, word freq, optional timestamps."""

from __future__ import annotations

import argparse
import json
import re
import statistics
from collections import Counter
from datetime import datetime
from pathlib import Path

# Rough time patterns (HH:MM or YYYY-MM-DD ...)
_TIME_LINE = re.compile(
    r"^(?P<ts>\d{4}[-/]\d{1,2}[-/]\d{1,2}[\sT]\d{1,2}:\d{2}|"
    r"\d{1,2}:\d{2}(?::\d{2})?)\s*[-:：]\s*(?P<rest>.+)$"
)
_HANGUL_CHATS = re.compile(r"[ㅋㅎㅠㅜ]+")
# Bubble export lines: 「：内容」或「[日期] :内容」
_BUBBLE_AFTER_HEADER = re.compile(r"^\[[^\]]+\]\s*[：:]\s*(.+)$")
_BUBBLE_PREFIX_ONLY = re.compile(r"^[：:]\s*(.+)$")
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


def _tokenize(text: str) -> list[str]:
    parts = re.findall(r"[\u4e00-\u9fff]+|[a-zA-Z']+|\d+", text.lower())
    return [p for p in parts if len(p) > 1 or p.isalpha()]


def _extract_bubble_message_lines(lines: list[str]) -> list[str]:
    """从导出文本中抽取疑似「单条泡泡」内容行（以 ： 或 : 起头，或 [hdr] : 形式）。"""
    out: list[str] = []
    for raw in lines:
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        m = _BUBBLE_AFTER_HEADER.match(line)
        if m:
            s = m.group(1).strip()
            if s:
                out.append(s)
            continue
        m = _BUBBLE_PREFIX_ONLY.match(line)
        if m:
            s = m.group(1).strip()
            if s:
                out.append(s)
    return out


def _percentile_ns(sorted_vals: list[int], p: float) -> float | None:
    if not sorted_vals:
        return None
    n = len(sorted_vals)
    if n == 1:
        return float(sorted_vals[0])
    k = (n - 1) * p
    lo = int(k)
    hi = min(lo + 1, n - 1)
    return sorted_vals[lo] + (k - lo) * (sorted_vals[hi] - sorted_vals[lo])


def bubble_metrics_from_messages(messages: list[str]) -> dict:
    """每条消息：字数（含 Emoji）、标点与语气粗特征 —— 用于按爱豆对齐语料长度与风格。"""
    if not messages:
        return {
            "bubble_message_count": 0,
            "char_lengths": [],
            "chars_mean": None,
            "chars_median": None,
            "chars_p25": None,
            "chars_p75": None,
            "chars_p90": None,
            "chars_min": None,
            "chars_max": None,
            "emoji_per_message_mean": None,
            "lines_with_tilde_ratio": None,
            "lines_with_haha_ratio": None,
            "style_summary_zh": "无可用泡泡行（请检查导出是否为「：」前缀或 [日期] : 格式）。",
        }

    lengths: list[int] = []
    emoji_counts: list[int] = []
    tilde_hits = 0
    haha_hits = 0
    for msg in messages:
        lengths.append(len(msg))
        emoji_counts.append(len(_EMOJI_RE.findall(msg)))
        if "~" in msg or "～" in msg:
            tilde_hits += 1
        if "哈哈" in msg or "hh" in msg.lower() or "ㅎㅎ" in msg:
            haha_hits += 1

    sl = sorted(lengths)
    n = len(sl)
    mean = sum(lengths) / n
    med = statistics.median(sl)

    def _pct(p: float) -> float | None:
        return _percentile_ns(sl, p)

    style_summary_zh = (
        f"本文件共解析 **{n}** 条泡泡式短行；"
        f"每行 **字数**（含 Emoji）中位数约 **{med:.0f}** 字，"
        f"均值约 **{mean:.1f}**，P90 约 **{_pct(0.9) or 0:.0f}**。"
        f"约 **{100 * tilde_hits / n:.0f}%** 行含「~ / ～」，"
        f"约 **{100 * haha_hits / n:.0f}%** 行含哈哈类语气；"
        f"平均每行 Emoji 约 **{sum(emoji_counts) / n:.2f}** 个。"
    )

    return {
        "bubble_message_count": n,
        "char_lengths": lengths,
        "chars_mean": round(mean, 2),
        "chars_median": round(med, 2),
        "chars_p25": round(_pct(0.25) or 0, 2),
        "chars_p75": round(_pct(0.75) or 0, 2),
        "chars_p90": round(_pct(0.9) or 0, 2),
        "chars_min": sl[0],
        "chars_max": sl[-1],
        "emoji_per_message_mean": round(sum(emoji_counts) / n, 3),
        "lines_with_tilde_ratio": round(tilde_hits / n, 3),
        "lines_with_haha_ratio": round(haha_hits / n, 3),
        "style_summary_zh": style_summary_zh,
    }


def _punctuation_stats(text: str) -> dict[str, int]:
    keys = "~！!…?.、，,ㅋㅎㅠㅜ"
    counts: dict[str, int] = {}
    for k in keys:
        if k in text:
            counts[k] = text.count(k)
    for m in _HANGUL_CHATS.finditer(text):
        s = m.group(0)
        counts[s] = counts.get(s, 0) + 1
    return dict(sorted(counts.items(), key=lambda x: -x[1]))


def analyze_lines(lines: list[str], target: str) -> dict:
    target_l = target.lower()
    idol_lines: list[str] = []
    other_lines: list[str] = []
    hour_bins = Counter()
    for raw in lines:
        line = raw.strip()
        if not line:
            continue
        ts = None
        content = line
        m = _TIME_LINE.match(line)
        if m:
            ts = m.group("ts")
            content = m.group("rest")
        blob = content.lower()
        if target_l and target_l in blob:
            idol_lines.append(content)
        else:
            other_lines.append(content)
        if ts:
            try:
                for fmt in ("%H:%M", "%H:%M:%S"):
                    try:
                        t = datetime.strptime(ts.split()[-1][:8], fmt)
                        hour_bins[t.hour] += 1
                        break
                    except ValueError:
                        continue
            except (IndexError, ValueError):
                pass

    idol_text = "\n".join(idol_lines)
    all_text = "\n".join(lines)

    words = _tokenize(idol_text if idol_lines else all_text)
    word_freq = Counter(words).most_common(80)

    bubble_msgs = _extract_bubble_message_lines(lines)
    bubble_metrics = bubble_metrics_from_messages(bubble_msgs)

    summary = {
        "target": target,
        "lines_attributed_to_target": len(idol_lines),
        "total_non_empty_lines": len([l for l in lines if l.strip()]),
        "punctuation": _punctuation_stats(idol_text if idol_text else all_text),
        "word_frequency_top": word_freq[:40],
        "hour_histogram_utc_or_naive": dict(sorted(hour_bins.items())),
        "bubble_metrics": bubble_metrics,
    }
    return summary


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--file", required=True, help="Path to .txt chat export")
    p.add_argument("--target", required=True, help='Name/nickname to tag "idol" lines (substring match)')
    p.add_argument("--output", required=True, help="Output JSON path")
    args = p.parse_args()

    path = Path(args.file)
    if not path.is_file():
        raise SystemExit(f"File not found: {path}")

    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    summary = analyze_lines(lines, args.target)

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {"source": str(path.resolve()), "summary": summary}
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
