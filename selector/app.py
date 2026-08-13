#!/usr/bin/env python3
from __future__ import annotations

"""
Avatar Selector GUI — Generalised Flask Backend

A web-based tool for reviewing, selecting, and managing generated avatar images.
Works with any project's character definitions provided as JSON.

Usage:
    cd scripts/avatar-generation
    pip install flask Pillow requests
    python selector/app.py \\
        --characters characters/toogether-avatars.json \\
        [--avatars-dir ../../toogether/generated-avatars] \\
        [--port 5050]

The tool will open automatically in your default browser.
"""

import io
import json
import os
import random
import re
import shutil
import subprocess
import sys
import webbrowser
from pathlib import Path
from threading import Timer

from flask import Flask, jsonify, render_template, request, send_file

# ---------------------------------------------------------------------------
# Resolve paths
# ---------------------------------------------------------------------------
SELECTOR_DIR = Path(__file__).resolve().parent
AVATAR_GEN_DIR = SELECTOR_DIR.parent  # scripts/avatar-generation/
REPO_ROOT = AVATAR_GEN_DIR.parent.parent  # repo root

# Add shared modules to path
sys.path.insert(0, str(AVATAR_GEN_DIR))

from image_processing import HAS_PILLOW, create_circle_mask, create_neon_ring  # noqa: E402
from prompt_builder import load_character_file  # noqa: E402

# ---------------------------------------------------------------------------
# Flask App
# ---------------------------------------------------------------------------
app = Flask(
    __name__,
    template_folder=str(SELECTOR_DIR / "templates"),
    static_folder=str(SELECTOR_DIR / "static"),
)

# Global state
_avatars_dir: Path = Path("generated-avatars")
_api_key: str | None = None
_character_data: dict = {}
_all_characters: list[dict] = []
_archetypes: dict = {}


def _load_characters(path: str | Path) -> None:
    """Load character definitions from a JSON file."""
    global _character_data, _all_characters, _archetypes
    _character_data = load_character_file(path)
    _all_characters = _character_data.get("characters", [])
    _archetypes = _character_data.get("archetypes", {})


def _get_api_key() -> str | None:
    """Get API key from multiple sources (priority order)."""
    global _api_key
    if _api_key:
        return _api_key

    key = os.environ.get("LEONARDO_AI_API_KEY")
    if key:
        _api_key = key
        return key

    for env_dir in [REPO_ROOT, REPO_ROOT / _character_data.get("project", "")]:
        env_file = env_dir / ".env"
        if env_file.exists():
            for line in env_file.read_text().splitlines():
                line = line.strip()
                if line.startswith("LEONARDO_AI_API_KEY="):
                    key = line.split("=", 1)[1].strip().strip("'\"")
                    if key:
                        _api_key = key
                        return key

    return None


def _parse_filename(filename: str) -> dict | None:
    """Parse an avatar filename into its components.

    Supports two patterns:
      1. With archetype/age/gender: portrait_{arch}_{age}_{gender}_{name}[_s{seed}].png
      2. Simple: portrait_{name}[_s{seed}].png
    """
    # Pattern 1: full pattern (toogether-style)
    pattern_full = re.compile(
        r"^(portrait|background|circle|composite|keyvisual)_"
        r"([a-z]+)_"
        r"(adult|teen|child)_"
        r"(male|female)_"
        r"([a-z]+)"
        r"(?:_s(\d+))?"
        r"\.png$",
        re.IGNORECASE,
    )
    match = pattern_full.match(filename)
    if match:
        return {
            "type": match.group(1).lower(),
            "archetype": match.group(2).upper(),
            "age_group": match.group(3).lower(),
            "gender": match.group(4).lower(),
            "name": match.group(5).capitalize(),
            "seed": int(match.group(6)) if match.group(6) else None,
        }

    # Pattern 2: simple pattern (org-spirits-style, categories)
    pattern_simple = re.compile(
        r"^(portrait|background|circle|composite|keyvisual)_"
        r"([a-z_]+?)"
        r"(?:_s(\d+))?"
        r"\.png$",
        re.IGNORECASE,
    )
    match = pattern_simple.match(filename)
    if match:
        return {
            "type": match.group(1).lower(),
            "archetype": "",
            "age_group": "",
            "gender": "",
            "name": match.group(2),
            "seed": int(match.group(3)) if match.group(3) else None,
        }

    return None


def _character_key(char: dict) -> str:
    """Create a unique key for a character."""
    parts = []
    if char.get("archetype"):
        parts.append(char["archetype"].lower())
    if char.get("age_group"):
        parts.append(char["age_group"])
    if char.get("gender"):
        parts.append(char["gender"])
    parts.append(char["name"].lower())
    return "_".join(parts)


def _variant_label(char: dict) -> str:
    """Human-readable variant label."""
    parts = []
    if char.get("age_group"):
        parts.append(char["age_group"].capitalize())
    if char.get("gender"):
        parts.append(char["gender"].capitalize())
    return " ".join(parts) if parts else char["name"]


def _scan_avatars() -> dict:
    """Scan the generated-avatars directory and build a character map."""
    avatars_dir = _avatars_dir
    result = {}

    for char in _all_characters:
        key = _character_key(char)
        archetype = char.get("archetype", "")
        theme = _archetypes.get(archetype, {})
        result[key] = {
            "key": key,
            "archetype": archetype,
            "age_group": char.get("age_group", ""),
            "gender": char.get("gender", ""),
            "name": char["name"],
            "variant": _variant_label(char),
            "neon_rgb": theme.get("neon_rgb", [100, 200, 255]),
            "has_kv_prompt": bool(char.get("kv_prompt")),
            "portraits": [],
            "backgrounds": [],
            "key_visuals": [],
            "circles": [],
            "composites": [],
            "portrait_selected": None,
            "background_selected": None,
            "key_visual_selected": None,
            "portrait_sorted_out": [],
            "background_sorted_out": [],
            "key_visual_sorted_out": [],
        }

    subdirs = {
        "portraits": "portrait",
        "backgrounds": "background",
        "key-visuals": "keyvisual",
        "circle-cropped": "circle",
        "composites": "composite",
    }

    for subdir_name, file_type in subdirs.items():
        subdir = avatars_dir / subdir_name
        if not subdir.exists():
            continue
        for f in sorted(subdir.iterdir()):
            if not f.name.endswith(".png"):
                continue
            parsed = _parse_filename(f.name)
            if not parsed or parsed["type"] != file_type:
                continue
            key = _character_key(parsed)
            if key not in result:
                continue
            entry = {
                "filename": f.name,
                "seed": parsed["seed"],
                "path": str(f.relative_to(avatars_dir)),
            }
            if file_type == "keyvisual":
                result[key]["key_visuals"].append(entry)
            else:
                target = f"{file_type}s" if file_type != "circle" else "circles"
                result[key][target].append(entry)

    # Check selected directory
    selected_avatar_dir = avatars_dir / "selected" / "avatar"
    selected_bg_dir = avatars_dir / "selected" / "background"
    selected_kv_dir = avatars_dir / "selected" / "key_visual"

    if selected_avatar_dir.exists():
        for f in selected_avatar_dir.iterdir():
            if not f.name.endswith(".png"):
                continue
            parsed = _parse_filename(f.name.replace("avatar_", "portrait_", 1))
            if not parsed:
                continue
            key = _character_key(parsed)
            if key in result:
                meta_file = selected_avatar_dir / f.name.replace(".png", ".meta.json")
                seed = None
                if meta_file.exists():
                    try:
                        meta = json.loads(meta_file.read_text())
                        seed = meta.get("seed")
                    except (json.JSONDecodeError, OSError):
                        pass
                result[key]["portrait_selected"] = seed if seed is not None else "selected"

    if selected_bg_dir.exists():
        for f in selected_bg_dir.iterdir():
            if not f.name.endswith(".png"):
                continue
            parsed = _parse_filename(f.name)
            if not parsed:
                continue
            key = _character_key(parsed)
            if key in result:
                meta_file = selected_bg_dir / f.name.replace(".png", ".meta.json")
                seed = None
                if meta_file.exists():
                    try:
                        meta = json.loads(meta_file.read_text())
                        seed = meta.get("seed")
                    except (json.JSONDecodeError, OSError):
                        pass
                result[key]["background_selected"] = seed if seed is not None else "selected"

    if selected_kv_dir.exists():
        for f in selected_kv_dir.iterdir():
            if not f.name.endswith(".png"):
                continue
            parsed = _parse_filename(f.name)
            if not parsed:
                continue
            key = _character_key(parsed)
            if key in result:
                meta_file = selected_kv_dir / f.name.replace(".png", ".meta.json")
                seed = None
                if meta_file.exists():
                    try:
                        meta = json.loads(meta_file.read_text())
                        seed = meta.get("seed")
                    except (json.JSONDecodeError, OSError):
                        pass
                result[key]["key_visual_selected"] = seed if seed is not None else "selected"

    # Check tobedeleted directory
    tobedeleted_dir = avatars_dir / "tobedeleted"
    if tobedeleted_dir.exists():
        for f in tobedeleted_dir.iterdir():
            if not f.name.endswith(".png"):
                continue
            parsed = _parse_filename(f.name)
            if not parsed:
                continue
            key = _character_key(parsed)
            if key not in result:
                continue
            if parsed["type"] == "portrait":
                result[key]["portrait_sorted_out"].append(parsed["seed"])
            elif parsed["type"] == "background":
                result[key]["background_sorted_out"].append(parsed["seed"])
            elif parsed["type"] == "keyvisual":
                result[key]["key_visual_sorted_out"].append(parsed["seed"])

    return result


def _build_filename(file_type: str, char_data: dict, seed: int | None) -> str:
    """Build a standard avatar filename."""
    parts = [file_type]
    if char_data.get("archetype"):
        parts.append(char_data["archetype"].lower())
    if char_data.get("age_group"):
        parts.append(char_data["age_group"])
    if char_data.get("gender"):
        parts.append(char_data["gender"])
    parts.append(char_data["name"].lower())
    base = "_".join(parts)
    if seed is not None:
        base += f"_s{seed}"
    return base + ".png"


def _find_file(file_type: str, char_data: dict,
               seed: int | None) -> Path | None:
    """Find a specific file in the avatars directory."""
    subdir_map = {
        "portrait": "portraits",
        "background": "backgrounds",
        "keyvisual": "key-visuals",
        "circle": "circle-cropped",
        "composite": "composites",
    }
    subdir = _avatars_dir / subdir_map.get(file_type, file_type)
    filename = _build_filename(file_type, char_data, seed)
    path = subdir / filename
    if path.exists():
        return path

    if seed is None and subdir.exists():
        base = _build_filename(file_type, char_data, None).replace(".png", "")
        for f in sorted(subdir.iterdir()):
            if f.name.startswith(base) and f.name.endswith(".png"):
                return f
    return None


def _resolve_image_path(filepath: str) -> Path | None:
    """Resolve and validate an image path within the avatars directory."""
    full_path = (_avatars_dir / filepath).resolve()
    if not str(full_path).startswith(str(_avatars_dir.resolve())):
        return None
    if not full_path.exists():
        return None
    return full_path


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/avatars")
def api_avatars():
    avatars = _scan_avatars()
    return jsonify({"avatars": list(avatars.values())})


@app.route("/api/progress")
def api_progress():
    avatars = _scan_avatars()
    total = len(avatars)
    portraits_selected = sum(
        1 for a in avatars.values() if a["portrait_selected"] is not None
    )
    backgrounds_selected = sum(
        1 for a in avatars.values() if a["background_selected"] is not None
    )
    key_visuals_selected = sum(
        1 for a in avatars.values() if a["key_visual_selected"] is not None
    )
    portraits_available = sum(
        1 for a in avatars.values() if len(a["portraits"]) > 0
    )
    backgrounds_available = sum(
        1 for a in avatars.values() if len(a["backgrounds"]) > 0
    )
    key_visuals_available = sum(
        1 for a in avatars.values() if len(a["key_visuals"]) > 0
    )

    archetypes_map = {}
    for a in avatars.values():
        arch = a.get("archetype", "default")
        if arch not in archetypes_map:
            archetypes_map[arch] = {
                "total": 0,
                "portraits_selected": 0,
                "backgrounds_selected": 0,
                "key_visuals_selected": 0,
                "portraits_available": 0,
                "backgrounds_available": 0,
                "key_visuals_available": 0,
            }
        archetypes_map[arch]["total"] += 1
        if a["portrait_selected"] is not None:
            archetypes_map[arch]["portraits_selected"] += 1
        if a["background_selected"] is not None:
            archetypes_map[arch]["backgrounds_selected"] += 1
        if a["key_visual_selected"] is not None:
            archetypes_map[arch]["key_visuals_selected"] += 1
        if len(a["portraits"]) > 0:
            archetypes_map[arch]["portraits_available"] += 1
        if len(a["backgrounds"]) > 0:
            archetypes_map[arch]["backgrounds_available"] += 1
        if len(a["key_visuals"]) > 0:
            archetypes_map[arch]["key_visuals_available"] += 1

    return jsonify({
        "total": total,
        "portraits_selected": portraits_selected,
        "backgrounds_selected": backgrounds_selected,
        "key_visuals_selected": key_visuals_selected,
        "portraits_available": portraits_available,
        "backgrounds_available": backgrounds_available,
        "key_visuals_available": key_visuals_available,
        "archetypes": archetypes_map,
    })


@app.route("/api/image/<path:filepath>")
def api_image(filepath):
    full_path = _resolve_image_path(filepath)
    if full_path is None:
        return jsonify({"error": "File not found or access denied"}), 404
    return send_file(full_path, mimetype="image/png")


@app.route("/api/dynamic-circle")
def api_dynamic_circle():
    if not HAS_PILLOW:
        return jsonify({"error": "Pillow not installed"}), 500

    portrait_rel = request.args.get("portrait", "")
    portrait_path = _resolve_image_path(portrait_rel)
    if not portrait_path:
        return jsonify({"error": "Portrait not found"}), 404

    from PIL import Image
    img = Image.open(portrait_path).convert("RGBA")
    size = img.width
    mask = create_circle_mask(size)
    result = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    result.paste(img, (0, 0), mask)

    buf = io.BytesIO()
    result.save(buf, "PNG")
    buf.seek(0)
    return send_file(buf, mimetype="image/png")


@app.route("/api/dynamic-composite")
def api_dynamic_composite():
    if not HAS_PILLOW:
        return jsonify({"error": "Pillow not installed"}), 500

    portrait_rel = request.args.get("portrait", "")
    bg_rel = request.args.get("background", "")
    archetype = request.args.get("archetype", "").upper()

    portrait_path = _resolve_image_path(portrait_rel)
    bg_path = _resolve_image_path(bg_rel)

    if not portrait_path:
        return jsonify({"error": "Portrait not found"}), 404
    if not bg_path:
        return jsonify({"error": "Background not found"}), 404

    theme = _archetypes.get(archetype, {})
    neon_rgb = tuple(theme.get("neon_rgb", [100, 200, 255]))

    from PIL import Image
    # Image.LANCZOS was moved to Image.Resampling.LANCZOS in Pillow 10+
    lanczos = getattr(Image, "Resampling", Image).LANCZOS
    bg = Image.open(bg_path).convert("RGBA")
    portrait = Image.open(portrait_path).convert("RGBA")
    size = bg.width

    if portrait.size != bg.size:
        portrait = portrait.resize(bg.size, lanczos)

    mask = create_circle_mask(size)
    cropped = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    cropped.paste(portrait, (0, 0), mask)

    ring = create_neon_ring(size, neon_rgb)

    result = Image.alpha_composite(bg, cropped)
    result = Image.alpha_composite(result, ring)

    buf = io.BytesIO()
    result.save(buf, "PNG")
    buf.seek(0)
    return send_file(buf, mimetype="image/png")


@app.route("/api/select-portrait", methods=["POST"])
def api_select_portrait():
    req = request.json
    char_key = req.get("key")
    seed = req.get("seed")

    avatars = _scan_avatars()
    if char_key not in avatars:
        return jsonify({"error": "Character not found"}), 404

    char_data = avatars[char_key]
    src = _find_file("portrait", char_data, seed)
    if not src:
        return jsonify({"error": "Portrait file not found"}), 404

    dest_dir = _avatars_dir / "selected" / "avatar"
    dest_dir.mkdir(parents=True, exist_ok=True)

    # Build destination filename
    parts = ["avatar"]
    if char_data.get("archetype"):
        parts.append(char_data["archetype"].lower())
    if char_data.get("age_group"):
        parts.append(char_data["age_group"])
    if char_data.get("gender"):
        parts.append(char_data["gender"])
    parts.append(char_data["name"].lower())
    dest_name = "_".join(parts) + ".png"
    dest = dest_dir / dest_name
    shutil.copy2(src, dest)

    meta = {
        "source": src.name,
        "seed": seed,
        "character": char_data["name"],
    }
    meta_file = dest_dir / dest_name.replace(".png", ".meta.json")
    meta_file.write_text(json.dumps(meta, indent=2))

    return jsonify({"ok": True, "destination": str(dest)})


@app.route("/api/deselect-portrait", methods=["POST"])
def api_deselect_portrait():
    req = request.json
    char_key = req.get("key")

    avatars = _scan_avatars()
    if char_key not in avatars:
        return jsonify({"error": "Character not found"}), 404

    char_data = avatars[char_key]
    dest_dir = _avatars_dir / "selected" / "avatar"
    parts = ["avatar"]
    if char_data.get("archetype"):
        parts.append(char_data["archetype"].lower())
    if char_data.get("age_group"):
        parts.append(char_data["age_group"])
    if char_data.get("gender"):
        parts.append(char_data["gender"])
    parts.append(char_data["name"].lower())
    dest_name = "_".join(parts) + ".png"
    dest = dest_dir / dest_name
    meta = dest_dir / dest_name.replace(".png", ".meta.json")

    if dest.exists():
        dest.unlink()
    if meta.exists():
        meta.unlink()

    return jsonify({"ok": True})


@app.route("/api/archetype-backgrounds")
def api_archetype_backgrounds():
    archetype = request.args.get("archetype", "").upper()
    if not archetype:
        return jsonify({"error": "Missing archetype parameter"}), 400

    avatars = _scan_avatars()
    backgrounds = []
    for _key, data in avatars.items():
        if data.get("archetype") != archetype:
            continue
        for bg in data["backgrounds"]:
            backgrounds.append({
                "path": bg["path"],
                "seed": bg["seed"],
                "variant": data["variant"],
                "name": data["name"],
                "key": data["key"],
            })
    return jsonify({"backgrounds": backgrounds})


@app.route("/api/select-background", methods=["POST"])
def api_select_background():
    req = request.json
    char_key = req.get("key")
    seed = req.get("seed")
    source_key = req.get("source_key")

    avatars = _scan_avatars()
    if char_key not in avatars:
        return jsonify({"error": "Character not found"}), 404

    char_data = avatars[char_key]

    if source_key and source_key in avatars:
        source_data = avatars[source_key]
        if source_data.get("archetype") != char_data.get("archetype"):
            return jsonify({"error": "Source must be same archetype"}), 400
    else:
        source_data = char_data

    src = _find_file("background", source_data, seed)
    if not src:
        return jsonify({"error": "Background file not found"}), 404

    dest_dir = _avatars_dir / "selected" / "background"
    dest_dir.mkdir(parents=True, exist_ok=True)

    parts = ["background"]
    if char_data.get("archetype"):
        parts.append(char_data["archetype"].lower())
    if char_data.get("age_group"):
        parts.append(char_data["age_group"])
    if char_data.get("gender"):
        parts.append(char_data["gender"])
    parts.append(char_data["name"].lower())
    dest_name = "_".join(parts) + ".png"
    dest = dest_dir / dest_name
    shutil.copy2(src, dest)

    meta = {
        "source": src.name,
        "seed": seed,
        "character": char_data["name"],
    }
    if source_key and source_key != char_key:
        meta["source_variant"] = source_data["variant"]
        meta["source_character"] = source_data["name"]
    meta_file = dest_dir / dest_name.replace(".png", ".meta.json")
    meta_file.write_text(json.dumps(meta, indent=2))

    return jsonify({"ok": True, "destination": str(dest)})


@app.route("/api/deselect-background", methods=["POST"])
def api_deselect_background():
    req = request.json
    char_key = req.get("key")

    avatars = _scan_avatars()
    if char_key not in avatars:
        return jsonify({"error": "Character not found"}), 404

    char_data = avatars[char_key]
    dest_dir = _avatars_dir / "selected" / "background"
    parts = ["background"]
    if char_data.get("archetype"):
        parts.append(char_data["archetype"].lower())
    if char_data.get("age_group"):
        parts.append(char_data["age_group"])
    if char_data.get("gender"):
        parts.append(char_data["gender"])
    parts.append(char_data["name"].lower())
    dest_name = "_".join(parts) + ".png"
    dest = dest_dir / dest_name
    meta = dest_dir / dest_name.replace(".png", ".meta.json")

    if dest.exists():
        dest.unlink()
    if meta.exists():
        meta.unlink()

    return jsonify({"ok": True})


@app.route("/api/select-key-visual", methods=["POST"])
def api_select_key_visual():
    req = request.json
    char_key = req.get("key")
    seed = req.get("seed")

    avatars = _scan_avatars()
    if char_key not in avatars:
        return jsonify({"error": "Character not found"}), 404

    char_data = avatars[char_key]
    src = _find_file("keyvisual", char_data, seed)
    if not src:
        return jsonify({"error": "Key visual file not found"}), 404

    dest_dir = _avatars_dir / "selected" / "key_visual"
    dest_dir.mkdir(parents=True, exist_ok=True)

    parts = ["keyvisual"]
    if char_data.get("archetype"):
        parts.append(char_data["archetype"].lower())
    if char_data.get("age_group"):
        parts.append(char_data["age_group"])
    if char_data.get("gender"):
        parts.append(char_data["gender"])
    parts.append(char_data["name"].lower())
    dest_name = "_".join(parts) + ".png"
    dest = dest_dir / dest_name
    shutil.copy2(src, dest)

    meta = {
        "source": src.name,
        "seed": seed,
        "character": char_data["name"],
    }
    meta_file = dest_dir / dest_name.replace(".png", ".meta.json")
    meta_file.write_text(json.dumps(meta, indent=2))

    return jsonify({"ok": True, "destination": str(dest)})


@app.route("/api/deselect-key-visual", methods=["POST"])
def api_deselect_key_visual():
    req = request.json
    char_key = req.get("key")

    avatars = _scan_avatars()
    if char_key not in avatars:
        return jsonify({"error": "Character not found"}), 404

    char_data = avatars[char_key]
    dest_dir = _avatars_dir / "selected" / "key_visual"
    parts = ["keyvisual"]
    if char_data.get("archetype"):
        parts.append(char_data["archetype"].lower())
    if char_data.get("age_group"):
        parts.append(char_data["age_group"])
    if char_data.get("gender"):
        parts.append(char_data["gender"])
    parts.append(char_data["name"].lower())
    dest_name = "_".join(parts) + ".png"
    dest = dest_dir / dest_name
    meta = dest_dir / dest_name.replace(".png", ".meta.json")

    if dest.exists():
        dest.unlink()
    if meta.exists():
        meta.unlink()

    return jsonify({"ok": True})


@app.route("/api/sort-out", methods=["POST"])
def api_sort_out():
    req = request.json
    char_key = req.get("key")
    file_type = req.get("type")
    seed = req.get("seed")

    if file_type not in ("portrait", "background", "keyvisual"):
        return jsonify({"error": "Type must be 'portrait', 'background', or 'keyvisual'"}), 400

    avatars = _scan_avatars()
    if char_key not in avatars:
        return jsonify({"error": "Character not found"}), 404

    char_data = avatars[char_key]
    src = _find_file(file_type, char_data, seed)
    if not src:
        return jsonify({"error": f"{file_type.capitalize()} file not found"}), 404

    dest_dir = _avatars_dir / "tobedeleted"
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / src.name
    shutil.move(str(src), str(dest))

    if file_type == "portrait":
        circle_src = _find_file("circle", char_data, seed)
        if circle_src and circle_src.exists():
            shutil.move(str(circle_src), str(dest_dir / circle_src.name))
        comp_src = _find_file("composite", char_data, seed)
        if comp_src and comp_src.exists():
            shutil.move(str(comp_src), str(dest_dir / comp_src.name))

    return jsonify({"ok": True})


@app.route("/api/restore", methods=["POST"])
def api_restore():
    req = request.json
    char_key = req.get("key")
    file_type = req.get("type")
    seed = req.get("seed")

    if file_type not in ("portrait", "background", "keyvisual"):
        return jsonify({"error": "Type must be 'portrait', 'background', or 'keyvisual'"}), 400

    avatars = _scan_avatars()
    if char_key not in avatars:
        return jsonify({"error": "Character not found"}), 404

    char_data = avatars[char_key]
    filename = _build_filename(file_type, char_data, seed)
    src = _avatars_dir / "tobedeleted" / filename
    if not src.exists():
        return jsonify({"error": "File not found in tobedeleted"}), 404

    subdir_map = {"portrait": "portraits", "background": "backgrounds",
                  "keyvisual": "key-visuals"}
    dest_dir = _avatars_dir / subdir_map[file_type]
    dest_dir.mkdir(parents=True, exist_ok=True)
    shutil.move(str(src), str(dest_dir / filename))

    return jsonify({"ok": True})


@app.route("/api/regenerate", methods=["POST"])
def api_regenerate():
    req = request.json
    char_key = req.get("key")
    file_type = req.get("type")
    new_seed = req.get("seed")

    if file_type not in ("portrait", "background", "keyvisual"):
        return jsonify({"error": "Type must be 'portrait', 'background', or 'keyvisual'"}), 400

    api_key = _get_api_key()
    if not api_key:
        return jsonify({
            "error": "No Leonardo.ai API key configured. "
                     "Set LEONARDO_AI_API_KEY environment variable."
        }), 400

    avatars = _scan_avatars()
    if char_key not in avatars:
        return jsonify({"error": "Character not found"}), 404

    char_data = avatars[char_key]
    char_name = char_data["name"]

    valid_names = {c["name"] for c in _all_characters}
    if char_name not in valid_names:
        return jsonify({"error": "Invalid character name"}), 400

    if new_seed is None:
        new_seed = random.randint(1, 999999)

    mode_map = {"portrait": "portrait", "background": "background",
                "keyvisual": "key_visual"}
    mode = mode_map[file_type]
    generate_script = AVATAR_GEN_DIR / "generate.py"
    char_file = _character_data.get("_source_path", "")

    cmd = [
        sys.executable,
        str(generate_script),
        "--characters", str(char_file),
        "--character", char_name,
        "--mode", mode,
        "--seed", str(new_seed),
        "--output", str(_avatars_dir),
    ]

    env = os.environ.copy()
    env["LEONARDO_AI_API_KEY"] = api_key

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, env=env, timeout=120,
        )
        output = result.stdout + result.stderr

        if result.returncode != 0:
            return jsonify({
                "error": f"Generation failed (exit code {result.returncode})",
                "output": output,
            }), 500

        if file_type == "portrait":
            post_cmd = [
                sys.executable,
                str(generate_script),
                "--characters", str(char_file),
                "--character", char_name,
                "--post-process-only",
                "--seed", str(new_seed),
                "--output", str(_avatars_dir),
            ]
            post_result = subprocess.run(
                post_cmd, capture_output=True, text=True, env=env, timeout=60,
            )
            output += post_result.stdout + post_result.stderr

        return jsonify({
            "ok": True,
            "seed": new_seed,
            "output": output,
        })

    except subprocess.TimeoutExpired:
        return jsonify({"error": "Generation timed out (120s)"}), 504
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/api/auto-generate", methods=["POST"])
def api_auto_generate():
    """Generate all missing assets (portrait/key_visual + background) for a character."""
    req = request.json
    char_key = req.get("key")

    api_key = _get_api_key()
    if not api_key:
        return jsonify({
            "error": "No Leonardo.ai API key configured. "
                     "Set LEONARDO_AI_API_KEY environment variable."
        }), 400

    avatars = _scan_avatars()
    if char_key not in avatars:
        return jsonify({"error": "Character not found"}), 404

    char_data = avatars[char_key]
    char_name = char_data["name"]

    valid_names = {c["name"] for c in _all_characters}
    if char_name not in valid_names:
        return jsonify({"error": "Invalid character name"}), 400

    # Determine which assets are missing
    has_portrait = len(char_data["portraits"]) > 0
    has_kv = len(char_data["key_visuals"]) > 0
    has_bg = len(char_data["backgrounds"]) > 0
    # Determine portrait type: use key_visual if this character has kv_prompt
    char_def = next((c for c in _all_characters if c["name"] == char_name), None)
    uses_kv = bool(char_def and char_def.get("kv_prompt"))
    needs_visual = not has_portrait and not has_kv
    needs_bg = not has_bg

    if not needs_visual and not needs_bg:
        return jsonify({"ok": True, "output": "Nothing to generate — all assets exist."})

    generate_script = AVATAR_GEN_DIR / "generate.py"
    char_file = _character_data.get("_source_path", "")
    env = os.environ.copy()
    env["LEONARDO_AI_API_KEY"] = api_key
    combined_output = ""
    new_seed = random.randint(1, 999999)

    # Generate visual (portrait or key_visual)
    if needs_visual:
        mode = "key_visual" if uses_kv else "portrait"
        cmd = [
            sys.executable,
            str(generate_script),
            "--characters", str(char_file),
            "--character", char_name,
            "--mode", mode,
            "--seed", str(new_seed),
            "--output", str(_avatars_dir),
        ]
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, env=env, timeout=120,
            )
            combined_output += result.stdout + result.stderr
            if result.returncode != 0:
                return jsonify({
                    "error": f"{mode} generation failed (exit code {result.returncode})",
                    "output": combined_output,
                }), 500
            # Post-process for portraits (circle crop, composite)
            if mode == "portrait":
                post_cmd = [
                    sys.executable,
                    str(generate_script),
                    "--characters", str(char_file),
                    "--character", char_name,
                    "--post-process-only",
                    "--seed", str(new_seed),
                    "--output", str(_avatars_dir),
                ]
                post_result = subprocess.run(
                    post_cmd, capture_output=True, text=True, env=env, timeout=60,
                )
                combined_output += post_result.stdout + post_result.stderr
        except subprocess.TimeoutExpired:
            return jsonify({"error": "Visual generation timed out (120s)"}), 504

    # Generate background
    if needs_bg:
        bg_seed = random.randint(1, 999999)
        cmd = [
            sys.executable,
            str(generate_script),
            "--characters", str(char_file),
            "--character", char_name,
            "--mode", "background",
            "--seed", str(bg_seed),
            "--output", str(_avatars_dir),
        ]
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, env=env, timeout=120,
            )
            combined_output += result.stdout + result.stderr
            if result.returncode != 0:
                return jsonify({
                    "error": f"Background generation failed (exit code {result.returncode})",
                    "output": combined_output,
                }), 500
        except subprocess.TimeoutExpired:
            return jsonify({"error": "Background generation timed out (120s)"}), 504

    return jsonify({
        "ok": True,
        "output": combined_output,
    })


@app.route("/api/set-api-key", methods=["POST"])
def api_set_api_key():
    global _api_key
    req = request.json
    key = req.get("key", "").strip()
    if not key:
        return jsonify({"error": "API key cannot be empty"}), 400
    _api_key = key
    return jsonify({"ok": True})


@app.route("/api/api-key-status")
def api_key_status():
    key = _get_api_key()
    return jsonify({
        "configured": key is not None,
        "source": (
            "environment" if os.environ.get("LEONARDO_AI_API_KEY")
            else "runtime" if _api_key
            else None
        ),
    })


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def _open_browser(port: int):
    webbrowser.open(f"http://127.0.0.1:{port}")


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Avatar Selector GUI — review, select, and manage generated avatars",
    )
    parser.add_argument(
        "--characters", type=str, required=True,
        help="Path to JSON character definition file",
    )
    parser.add_argument(
        "--port", type=int, default=5050,
        help="Port to run the server on (default: 5050)",
    )
    parser.add_argument(
        "--avatars-dir", type=str, default=None,
        help="Path to generated-avatars directory",
    )
    parser.add_argument(
        "--no-browser", action="store_true",
        help="Don't open browser automatically",
    )
    args = parser.parse_args()

    # Load character definitions
    char_path = Path(args.characters)
    if not char_path.exists():
        print(f"ERROR: Character file not found: {char_path}", file=sys.stderr)
        sys.exit(1)

    _load_characters(char_path)
    _character_data["_source_path"] = str(char_path.resolve())
    project = _character_data.get("project", "unknown")

    global _avatars_dir
    if args.avatars_dir:
        _avatars_dir = Path(args.avatars_dir).resolve()
    else:
        _avatars_dir = Path(f"{project}/generated-avatars").resolve()

    _avatars_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print(f"🎨 Avatar Selector GUI — {project}")
    print("=" * 60)
    print(f"  Characters:   {len(_all_characters)} from {char_path}")
    print(f"  Avatars dir:  {_avatars_dir}")
    print(f"  Server URL:   http://127.0.0.1:{args.port}")
    print(f"  API key:      {'✅ configured' if _get_api_key() else '❌ not set'}")
    print()
    print("  Press Ctrl+C to stop the server.")
    print("=" * 60)

    if not args.no_browser:
        Timer(1.5, _open_browser, args=[args.port]).start()

    app.run(host="127.0.0.1", port=args.port, debug=False)


if __name__ == "__main__":
    main()
