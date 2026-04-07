#!/usr/bin/env python3
"""meta.json CRUD, backup, scene presets, and migrate legacy nested idol layouts."""

from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

SCHEMA_VERSION = 1

CORPUS_KEYS = ("bubble", "weverse", "fansign", "social", "memory")
ITINERARY = ("comeback", "tour", "rest", "unknown")
SCENE_PRESETS = (
    "none",
    "bubble",
    "fansign",
    "backstage",
    "transit",
    "dorm",
    "studio",
    "custom",
)


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def default_scene() -> dict:
    return {"preset": "none", "summary": "", "detail": ""}


def default_meta(slug: str, display_name: str) -> dict:
    return {
        "schema_version": SCHEMA_VERSION,
        "slug": slug,
        "display_name": display_name,
        "created_at": utc_now_iso(),
        "updated_at": utc_now_iso(),
        "itinerary_status": "unknown",
        "last_comeback_mentioned": None,
        "corpus_weights": {k: 0 for k in CORPUS_KEYS},
        "current_mood": "",
        "scene": default_scene(),
        "warnings": {"low_corpus_purity": False, "messages": []},
    }


def load_meta(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def save_meta(path: Path, data: dict) -> None:
    data["updated_at"] = utc_now_iso()
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def cmd_init(args: argparse.Namespace) -> None:
    root = repo_root()
    slug = args.slug
    base = root / "idols" / slug
    base.mkdir(parents=True, exist_ok=True)
    meta_path = base / "meta.json"
    if meta_path.exists() and not args.force:
        raise SystemExit(f"Already exists: {meta_path} (use --force to overwrite defaults)")
    display = args.display_name or slug
    data = default_meta(slug, display)
    if meta_path.exists() and args.force:
        old = load_meta(meta_path)
        data["created_at"] = old.get("created_at", data["created_at"])
    save_meta(meta_path, data)
    print(f"Wrote {meta_path}")


def cmd_touch(args: argparse.Namespace) -> None:
    meta_path = repo_root() / "idols" / args.slug / "meta.json"
    if not meta_path.is_file():
        raise SystemExit(f"Not found: {meta_path}")
    data = load_meta(meta_path)
    _ensure_scene(data)
    save_meta(meta_path, data)
    print(f"updated_at refreshed: {meta_path}")


def cmd_set_itinerary(args: argparse.Namespace) -> None:
    meta_path = repo_root() / "idols" / args.slug / "meta.json"
    data = load_meta(meta_path)
    if args.status not in ITINERARY:
        raise SystemExit(f"status must be one of: {ITINERARY}")
    data["itinerary_status"] = args.status
    if args.last_comeback is not None:
        data["last_comeback_mentioned"] = args.last_comeback
    save_meta(meta_path, data)
    print(f"Updated itinerary: {meta_path}")


def cmd_set_mood(args: argparse.Namespace) -> None:
    meta_path = repo_root() / "idols" / args.slug / "meta.json"
    data = load_meta(meta_path)
    data["current_mood"] = args.text
    save_meta(meta_path, data)
    print(f"Updated current_mood: {meta_path}")


def _ensure_scene(data: dict) -> dict:
    if "scene" not in data or not isinstance(data.get("scene"), dict):
        data["scene"] = default_scene()
        return data["scene"]
    s = data["scene"]
    for k, v in default_scene().items():
        s.setdefault(k, v)
    return s


def cmd_set_scene(args: argparse.Namespace) -> None:
    meta_path = repo_root() / "idols" / args.slug / "meta.json"
    if not meta_path.is_file():
        raise SystemExit(f"Not found: {meta_path}")
    data = load_meta(meta_path)
    scene = _ensure_scene(data)
    if args.clear:
        cleared = default_scene()
        scene.clear()
        scene.update(cleared)
    else:
        if args.preset is None:
            raise SystemExit("Use --preset … or --clear")
        if args.preset not in SCENE_PRESETS:
            raise SystemExit(f"preset must be one of: {SCENE_PRESETS}")
        if args.preset == "custom" and not (args.summary or "").strip():
            raise SystemExit("preset=custom requires non-empty --summary")
        scene["preset"] = args.preset
        if args.summary is not None:
            scene["summary"] = args.summary
        if args.detail is not None:
            scene["detail"] = args.detail
    save_meta(meta_path, data)
    print(f"Updated scene: {meta_path}")
    print(json.dumps(data["scene"], ensure_ascii=False, indent=2))


def cmd_record_corpus(args: argparse.Namespace) -> None:
    meta_path = repo_root() / "idols" / args.slug / "meta.json"
    data = load_meta(meta_path)
    key = args.type
    if key not in CORPUS_KEYS:
        raise SystemExit(f"type must be one of: {CORPUS_KEYS}")
    w = data.setdefault("corpus_weights", {k: 0 for k in CORPUS_KEYS})
    w[key] = int(w.get(key, 0)) + int(args.delta)
    save_meta(meta_path, data)
    print(f"corpus_weights: {data['corpus_weights']}")


def cmd_set_warning(args: argparse.Namespace) -> None:
    meta_path = repo_root() / "idols" / args.slug / "meta.json"
    data = load_meta(meta_path)
    warn = data.setdefault("warnings", {"low_corpus_purity": False, "messages": []})
    warn["low_corpus_purity"] = bool(args.low_corpus)
    if args.message:
        msgs = warn.setdefault("messages", [])
        msgs.append(args.message)
    save_meta(meta_path, data)
    print(f"Updated warnings: {meta_path}")


def cmd_backup(args: argparse.Namespace) -> None:
    root = repo_root()
    src = root / "idols" / args.slug
    if not src.is_dir():
        raise SystemExit(f"Not found: {src}")
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    dest = root / "idols" / "_backups" / f"{args.slug}-{ts}"
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(src, dest)
    print(f"Backed up to {dest}")


def cmd_migrate(args: argparse.Namespace) -> None:
    root = repo_root()
    base = root / "idols" / args.slug
    if not base.is_dir():
        raise SystemExit(f"Not found: {base}")

    u_old = base / "universe" / "universe.md"
    u_new = base / "universe.md"
    p_old = base / "persona" / "persona.md"
    p_new = base / "persona.md"

    if u_old.is_file() and not u_new.exists():
        u_new.write_text(u_old.read_text(encoding="utf-8"), encoding="utf-8")
        shutil.rmtree(base / "universe", ignore_errors=False)
        print(f"Migrated -> {u_new}")
    if p_old.is_file() and not p_new.exists():
        p_new.write_text(p_old.read_text(encoding="utf-8"), encoding="utf-8")
        shutil.rmtree(base / "persona", ignore_errors=False)
        print(f"Migrated -> {p_new}")

    meta_path = base / "meta.json"
    if not meta_path.is_file():
        display = args.display_name or args.slug
        save_meta(meta_path, default_meta(args.slug, display))
        print(f"Created {meta_path}")

    print("migrate done.")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)

    p_init = sub.add_parser("init", help="Create default meta.json under idols/{slug}/")
    p_init.add_argument("--slug", required=True)
    p_init.add_argument("--display-name", default="")
    p_init.add_argument("--force", action="store_true")
    p_init.set_defaults(func=cmd_init)

    p_touch = sub.add_parser("touch", help="Refresh updated_at")
    p_touch.add_argument("--slug", required=True)
    p_touch.set_defaults(func=cmd_touch)

    p_it = sub.add_parser("set-itinerary", help="Set itinerary_status and optional last_comeback")
    p_it.add_argument("--slug", required=True)
    p_it.add_argument("--status", required=True, choices=list(ITINERARY))
    p_it.add_argument("--last-comeback", default=None, help="Free-text mention of last comeback")
    p_it.set_defaults(func=cmd_set_itinerary)

    p_mood = sub.add_parser("set-mood", help="Set current_mood string")
    p_mood.add_argument("--slug", required=True)
    p_mood.add_argument("--text", required=True)
    p_mood.set_defaults(func=cmd_set_mood)

    p_scene = sub.add_parser(
        "set-scene",
        help="Set imagined dialogue scene (preset + summary/detail); use --clear to reset",
    )
    p_scene.add_argument("--slug", required=True)
    p_scene.add_argument(
        "--preset",
        default=None,
        choices=list(SCENE_PRESETS),
        help="Scene preset; required unless --clear",
    )
    p_scene.add_argument("--summary", default=None, help="One-line scene label (e.g. 签售结束回酒店路上)")
    p_scene.add_argument("--detail", default=None, help="Optional longer free-text scene notes")
    p_scene.add_argument(
        "--clear",
        action="store_true",
        help="Reset scene to none with empty summary/detail",
    )
    p_scene.set_defaults(func=cmd_set_scene)

    p_rc = sub.add_parser("record-corpus", help="Increment corpus weight counter")
    p_rc.add_argument("--slug", required=True)
    p_rc.add_argument("--type", required=True, choices=list(CORPUS_KEYS))
    p_rc.add_argument("--delta", type=int, default=1)
    p_rc.set_defaults(func=cmd_record_corpus)

    p_w = sub.add_parser("set-warning", help="Set low_corpus_purity and optional message")
    p_w.add_argument("--slug", required=True)
    p_w.add_argument("--low-corpus", type=int, required=True, choices=(0, 1))
    p_w.add_argument("--message", default="")
    p_w.set_defaults(func=cmd_set_warning)

    p_b = sub.add_parser("backup", help="Copy idols/{slug} to idols/_backups/{slug}-{timestamp}/")
    p_b.add_argument("--slug", required=True)
    p_b.set_defaults(func=cmd_backup)

    p_m = sub.add_parser("migrate", help="Move universe/universe.md -> universe.md, persona/persona.md -> persona.md")
    p_m.add_argument("--slug", required=True)
    p_m.add_argument("--display-name", default="", help="For new meta.json if missing")
    p_m.set_defaults(func=cmd_migrate)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
