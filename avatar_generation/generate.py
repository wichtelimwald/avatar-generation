#!/usr/bin/env python3
from __future__ import annotations

"""
Shared Avatar Generation — Main CLI Entry Point

Project-agnostic avatar generation script that reads character definitions
from JSON files and generates images via the Leonardo.ai API.

Usage:
    # Dry-run (validate prompts, no API calls)
    python3 scripts/avatar-generation/generate.py \\
        --characters toogether/characters/toogether-avatars.json \\
        --dry-run

    # Generate portraits for all characters
    python3 scripts/avatar-generation/generate.py \\
        --characters toogether/characters/toogether-avatars.json \\
        --all --seed 42

    # Generate org-spirits portraits
    python3 scripts/avatar-generation/generate.py \\
        --characters org-spirits-app/characters/org-spirits.json \\
        --all --mode portrait

    # Generate a single character
    python3 scripts/avatar-generation/generate.py \\
        --characters toogether/characters/toogether-avatars.json \\
        --character Markus --mode composite --seed 42

Environment:
    LEONARDO_AI_API_KEY  — Required for generation (not needed for --dry-run).

Output:
    <output-dir>/portraits/       — AI portraits
    <output-dir>/backgrounds/     — Background images
    <output-dir>/circle-cropped/  — Circle-cropped portraits (transparent PNG)
    <output-dir>/composites/      — Background + portrait + neon ring
    <output-dir>/generation-log.json — Full generation metadata
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

# Ensure this script's directory is on the Python path
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from config import DEFAULT_GENERATION_PARAMS, RATE_LIMIT_DELAY_SECONDS  # noqa: E402
from image_processing import (  # noqa: E402
    HAS_PILLOW,
    circle_crop_portrait,
    composite_avatar,
)
from leonardo_api import (  # noqa: E402
    create_generation,
    download_image,
    poll_generation,
)
from prompt_builder import (  # noqa: E402
    build_background_prompt,
    build_key_visual_negative,
    build_key_visual_prompt,
    build_portrait_negative,
    build_portrait_prompt,
    get_characters,
    load_character_file,
)


# ---------------------------------------------------------------------------
# Generation orchestration
# ---------------------------------------------------------------------------

def _build_generation_params(data: dict) -> dict:
    """Build Leonardo.ai generation parameters from character data."""
    style = data.get("style", {})
    params = dict(DEFAULT_GENERATION_PARAMS)
    json_params = style.get("generation_params", {})

    if "model_id" in json_params:
        params["modelId"] = json_params["model_id"]
    if "width" in json_params:
        params["width"] = json_params["width"]
    if "height" in json_params:
        params["height"] = json_params["height"]
    if "guidance_scale" in json_params:
        params["guidance_scale"] = json_params["guidance_scale"]
    if "num_inference_steps" in json_params:
        params["num_inference_steps"] = json_params["num_inference_steps"]
    if "alchemy" in json_params:
        params["alchemy"] = json_params["alchemy"]

    return params


def _character_base(character: dict) -> str:
    """Build base filename segment for a character."""
    parts = []
    if "archetype" in character:
        parts.append(character["archetype"].lower())
    if "age_group" in character:
        parts.append(character["age_group"])
    if "gender" in character:
        parts.append(character["gender"])
    parts.append(character["name"].lower())
    return "_".join(parts)


def generate_portraits(api_key: str, characters: list[dict], data: dict,
                       output_dir: Path, seed: int | None = None) -> list[dict]:
    """Generate portrait images for characters."""
    gen_params = _build_generation_params(data)
    portraits_dir = output_dir / "portraits"
    portraits_dir.mkdir(parents=True, exist_ok=True)
    results = []

    for i, character in enumerate(characters, 1):
        name = character["name"]
        base = _character_base(character)
        seed_tag = f"_s{seed}" if seed is not None else ""
        filename = f"portrait_{base}{seed_tag}.png"
        img_path = portraits_dir / filename

        print(f"\n{'='*60}")
        print(f"[{i}/{len(characters)}] Portrait: {name}")
        if seed is not None:
            print(f"  Seed: {seed}")
        print(f"{'='*60}")

        if img_path.exists():
            print(f"  ⏭️  Already exists: {filename} — skipping")
            results.append({
                "character": name,
                "layer": "portrait",
                "generationId": None,
                "status": "skipped",
                "images": [{"filename": filename}],
            })
            continue

        try:
            positive = build_portrait_prompt(character, data)
            negative = build_portrait_negative(character, data)
            print(f"  Positive prompt: {len(positive)} chars")
            print(f"  Negative prompt: {len(negative)} chars")

            print("  Submitting to Leonardo.ai...")
            gen_info = create_generation(
                api_key, positive, negative, gen_params, seed=seed,
            )
            gen_id = gen_info["generationId"]
            print(f"  Generation ID: {gen_id}")

            print("  Waiting for completion...")
            result = poll_generation(api_key, gen_id)

            images = result.get("generated_images", [])
            print(f"  Generated {len(images)} image(s)")

            downloaded = []
            for img in images:
                img_url = img.get("url")
                if img_url:
                    download_image(img_url, img_path)
                    downloaded.append({
                        "filename": filename,
                        "url": img_url,
                        "seed": img.get("seed"),
                        "id": img.get("id"),
                    })

            results.append({
                "character": name,
                "layer": "portrait",
                "generationId": gen_id,
                "status": "success",
                "images": downloaded,
                "positive_prompt": positive,
                "negative_prompt": negative,
            })
            print(f"  ✅ {name} portrait complete!")

        except Exception as exc:
            error_msg = str(exc)
            print(f"  ❌ {name} portrait FAILED: {error_msg}")
            results.append({
                "character": name,
                "layer": "portrait",
                "generationId": None,
                "status": "failed",
                "error": error_msg,
                "images": [],
            })

        if i < len(characters):
            print(f"\n  ⏳ Waiting {RATE_LIMIT_DELAY_SECONDS}s before next "
                  f"generation (rate limit)...")
            time.sleep(RATE_LIMIT_DELAY_SECONDS)

    return results


def generate_backgrounds(api_key: str, characters: list[dict], data: dict,
                         output_dir: Path,
                         seed: int | None = None) -> list[dict]:
    """Generate background images for characters."""
    style = data.get("style", {})
    gen_params = _build_generation_params(data)
    bg_negative = style.get("background_negative", "")
    bg_dir = output_dir / "backgrounds"
    bg_dir.mkdir(parents=True, exist_ok=True)
    results = []

    for i, character in enumerate(characters, 1):
        name = character["name"]
        base = _character_base(character)
        seed_tag = f"_s{seed}" if seed is not None else ""
        filename = f"background_{base}{seed_tag}.png"
        img_path = bg_dir / filename

        print(f"\n{'='*60}")
        print(f"[{i}/{len(characters)}] Background: {name}")
        if seed is not None:
            print(f"  Seed: {seed}")
        print(f"{'='*60}")

        if img_path.exists():
            print(f"  ⏭️  Already exists: {filename} — skipping")
            results.append({
                "character": name,
                "layer": "background",
                "generationId": None,
                "status": "skipped",
                "images": [{"filename": filename}],
            })
            continue

        try:
            positive = build_background_prompt(character, data)
            print(f"  Positive prompt: {len(positive)} chars")

            print("  Submitting to Leonardo.ai...")
            gen_info = create_generation(
                api_key, positive, bg_negative, gen_params, seed=seed,
            )
            gen_id = gen_info["generationId"]
            print(f"  Generation ID: {gen_id}")

            print("  Waiting for completion...")
            result = poll_generation(api_key, gen_id)

            images = result.get("generated_images", [])
            print(f"  Generated {len(images)} image(s)")

            downloaded = []
            for img in images:
                img_url = img.get("url")
                if img_url:
                    download_image(img_url, img_path)
                    downloaded.append({
                        "filename": filename,
                        "url": img_url,
                        "seed": img.get("seed"),
                        "id": img.get("id"),
                    })

            results.append({
                "character": name,
                "layer": "background",
                "generationId": gen_id,
                "status": "success",
                "images": downloaded,
                "positive_prompt": positive,
                "negative_prompt": bg_negative,
            })
            print(f"  ✅ {name} background complete!")

        except Exception as exc:
            error_msg = str(exc)
            print(f"  ❌ {name} background FAILED: {error_msg}")
            results.append({
                "character": name,
                "layer": "background",
                "generationId": None,
                "status": "failed",
                "error": error_msg,
                "images": [],
            })

        if i < len(characters):
            print(f"\n  ⏳ Waiting {RATE_LIMIT_DELAY_SECONDS}s before next "
                  f"generation (rate limit)...")
            time.sleep(RATE_LIMIT_DELAY_SECONDS)

    return results


def generate_key_visuals(api_key: str, characters: list[dict], data: dict,
                         output_dir: Path,
                         seed: int | None = None) -> list[dict]:
    """Generate key visual images for categories/characters."""
    style = data.get("style", {})
    gen_params = _build_generation_params(data)
    kv_negative = build_key_visual_negative(data)
    kv_dir = output_dir / "key-visuals"
    kv_dir.mkdir(parents=True, exist_ok=True)
    results = []

    for i, character in enumerate(characters, 1):
        name = character["name"]
        base = _character_base(character)
        seed_tag = f"_s{seed}" if seed is not None else ""
        filename = f"keyvisual_{base}{seed_tag}.png"
        img_path = kv_dir / filename

        print(f"\n{'='*60}")
        print(f"[{i}/{len(characters)}] Key Visual: {name}")
        if seed is not None:
            print(f"  Seed: {seed}")
        print(f"{'='*60}")

        if img_path.exists():
            print(f"  ⏭️  Already exists: {filename} — skipping")
            results.append({
                "character": name,
                "layer": "key_visual",
                "generationId": None,
                "status": "skipped",
                "images": [{"filename": filename}],
            })
            continue

        try:
            positive = build_key_visual_prompt(character, data)
            print(f"  Positive prompt: {len(positive)} chars")
            print(f"  Negative prompt: {len(kv_negative)} chars")

            print("  Submitting to Leonardo.ai...")
            gen_info = create_generation(
                api_key, positive, kv_negative, gen_params, seed=seed,
            )
            gen_id = gen_info["generationId"]
            print(f"  Generation ID: {gen_id}")

            print("  Waiting for completion...")
            result = poll_generation(api_key, gen_id)

            images = result.get("generated_images", [])
            print(f"  Generated {len(images)} image(s)")

            downloaded = []
            for img in images:
                img_url = img.get("url")
                if img_url:
                    download_image(img_url, img_path)
                    downloaded.append({
                        "filename": filename,
                        "url": img_url,
                        "seed": img.get("seed"),
                        "id": img.get("id"),
                    })

            results.append({
                "character": name,
                "layer": "key_visual",
                "generationId": gen_id,
                "status": "success",
                "images": downloaded,
                "positive_prompt": positive,
                "negative_prompt": kv_negative,
            })
            print(f"  ✅ {name} key visual complete!")

        except Exception as exc:
            error_msg = str(exc)
            print(f"  ❌ {name} key visual FAILED: {error_msg}")
            results.append({
                "character": name,
                "layer": "key_visual",
                "generationId": None,
                "status": "failed",
                "error": error_msg,
                "images": [],
            })

        if i < len(characters):
            print(f"\n  ⏳ Waiting {RATE_LIMIT_DELAY_SECONDS}s before next "
                  f"generation (rate limit)...")
            time.sleep(RATE_LIMIT_DELAY_SECONDS)

    return results


def run_post_processing(characters: list[dict], data: dict,
                        output_dir: Path,
                        seed: int | None = None) -> list[str]:
    """Run circle-crop and compositing on generated images."""
    if not HAS_PILLOW:
        print("⚠️  Pillow not installed. Skipping post-processing.")
        print("   Install with: pip install Pillow")
        return []

    archetypes = data.get("archetypes", {})
    portraits_dir = output_dir / "portraits"
    bg_dir = output_dir / "backgrounds"
    circle_dir = output_dir / "circle-cropped"
    composite_dir = output_dir / "composites"
    circle_dir.mkdir(parents=True, exist_ok=True)
    composite_dir.mkdir(parents=True, exist_ok=True)

    seed_tag = f"_s{seed}" if seed is not None else ""
    processed = []

    for character in characters:
        name = character["name"]
        base = _character_base(character)
        archetype = character.get("archetype", "")

        portrait_path = portraits_dir / f"portrait_{base}{seed_tag}.png"
        bg_path = bg_dir / f"background_{base}{seed_tag}.png"
        circle_path = circle_dir / f"circle_{base}{seed_tag}.png"
        composite_path = composite_dir / f"composite_{base}{seed_tag}.png"

        # Fall back to non-seeded or other-seed portraits
        if not portrait_path.exists() and seed_tag:
            alt = portraits_dir / f"portrait_{base}.png"
            if alt.exists():
                portrait_path = alt
        if not portrait_path.exists():
            matches = list(portraits_dir.glob(f"portrait_{base}*.png"))
            if matches:
                portrait_path = matches[0]
            else:
                print(f"  ⚠️  Portrait not found: {portrait_path}")
                continue

        # Circle-crop
        print(f"  Circle-crop: {name}...")
        circle_crop_portrait(portrait_path, circle_path)
        processed.append(str(circle_path))

        # Composite (if background exists)
        if not bg_path.exists() and seed_tag:
            alt = bg_dir / f"background_{base}.png"
            if alt.exists():
                bg_path = alt
        if not bg_path.exists():
            matches = list(bg_dir.glob(f"background_{base}*.png"))
            if matches:
                bg_path = matches[0]

        if bg_path.exists():
            theme = archetypes.get(archetype, {})
            neon_rgb = tuple(theme.get("neon_rgb", [100, 200, 255]))
            print(f"  Composite: {name}...")
            composite_avatar(portrait_path, bg_path, composite_path, neon_rgb)
            processed.append(str(composite_path))
        else:
            print(f"  ⚠️  Background not found for {name}, skipping composite")

    return processed


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Generate avatar images via Leonardo.ai API (Shared Framework)"
    )
    parser.add_argument(
        "--characters", type=str, required=True,
        help="Path to JSON character definition file",
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--all", action="store_true",
                       help="Generate all characters in the file")
    group.add_argument("--test", action="store_true",
                       help="Generate test characters only")
    group.add_argument("--character", type=str,
                       help="Generate a specific character by name")
    group.add_argument("--archetype", type=str,
                       help="Generate all variants of a single archetype")
    parser.add_argument("--mode", choices=["portrait", "background", "composite",
                                            "key_visual"],
                        default="portrait",
                        help="Generation mode (default: portrait)")
    parser.add_argument("--seed", type=int, default=None,
                        help="Fixed seed for reproducible style")
    parser.add_argument("--output", type=str, default=None,
                        help="Output directory (default: <project>/generated-avatars)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show prompts without calling API")
    parser.add_argument("--post-process-only", action="store_true",
                        help="Run only circle-crop and compositing on existing images")
    args = parser.parse_args()

    # Load character definitions
    char_path = Path(args.characters)
    if not char_path.exists():
        print(f"ERROR: Character file not found: {char_path}", file=sys.stderr)
        print("  Character definition files are located in each project's "
              "characters/ directory (e.g. toogether/characters/).", file=sys.stderr)
        sys.exit(1)

    data = load_character_file(char_path)
    project = data.get("project", "unknown")
    max_len = data.get("style", {}).get("prompt_max_length", 1500)

    # Determine output directory
    if args.output:
        output_dir = Path(args.output)
    else:
        output_dir = Path(f"{project}/generated-avatars")

    # Get API key
    api_key = os.environ.get("LEONARDO_AI_API_KEY")
    if not api_key and not args.dry_run and not args.post_process_only:
        print("ERROR: LEONARDO_AI_API_KEY environment variable not set.",
              file=sys.stderr)
        print("Set it with: export LEONARDO_AI_API_KEY='your-key'",
              file=sys.stderr)
        sys.exit(1)

    # Select characters
    if args.all:
        characters = get_characters(data)
    elif args.archetype:
        characters = get_characters(data, archetype=args.archetype)
        if not characters:
            archetypes = data.get("archetypes", {})
            print(f"ERROR: Archetype '{args.archetype}' not found.",
                  file=sys.stderr)
            if archetypes:
                print(f"Available: {', '.join(sorted(archetypes.keys()))}",
                      file=sys.stderr)
            sys.exit(1)
    elif args.character:
        characters = get_characters(data, names=[args.character])
        if not characters:
            all_names = [c["name"] for c in data.get("characters", [])]
            print(f"ERROR: Character '{args.character}' not found.",
                  file=sys.stderr)
            print(f"Available: {', '.join(all_names)}", file=sys.stderr)
            sys.exit(1)
    elif args.test:
        characters = get_characters(data, test_only=True)
    else:
        characters = get_characters(data, test_only=True)

    # Post-process-only mode
    if args.post_process_only:
        if not HAS_PILLOW:
            print("ERROR: Pillow is required for post-processing.",
                  file=sys.stderr)
            sys.exit(1)
        print("=" * 60)
        print("POST-PROCESSING ONLY — Circle-crop + compositing")
        print(f"Characters: {len(characters)} | Project: {project}")
        print("=" * 60)
        processed = run_post_processing(characters, data, output_dir,
                                        seed=args.seed)
        print(f"\n✅ Post-processed {len(processed)} file(s)")
        return

    # Dry-run mode
    if args.dry_run:
        print("=" * 60)
        print(f"DRY RUN — Showing prompts ({project})")
        print(f"Mode: {args.mode} | Prompt limit: {max_len} chars")
        print(f"Characters: {len(characters)} | Seed: {args.seed or 'random'}")
        print("=" * 60)
        all_ok = True

        if args.mode in ("portrait", "composite"):
            print("\n── PORTRAIT PROMPTS ──")
            for character in characters:
                positive = build_portrait_prompt(character, data)
                negative = build_portrait_negative(character, data)
                remaining = max_len - len(positive)
                status = "✅" if remaining >= 0 else "❌"
                label = character["name"]
                arch = character.get("archetype", "")
                if arch:
                    label = f"{label} ({arch})"
                print(f"\n--- {label} ---")
                print(f"  Positive: {len(positive)} / {max_len} chars "
                      f"({remaining} remaining) {status}")
                print(f"  Negative: {len(negative)} chars")
                print(f"\nPOSITIVE PROMPT:\n{positive}")
                print(f"\nNEGATIVE PROMPT:\n{negative}")
                print()
                if remaining < 0:
                    all_ok = False

        if args.mode in ("background", "composite"):
            print("\n── BACKGROUND PROMPTS ──")
            bg_neg = data.get("style", {}).get("background_negative", "")
            for character in characters:
                positive = build_background_prompt(character, data)
                remaining = max_len - len(positive)
                status = "✅" if remaining >= 0 else "❌"
                print(f"\n--- {character['name']} background ---")
                print(f"  Positive: {len(positive)} / {max_len} chars "
                      f"({remaining} remaining) {status}")
                print(f"\nPOSITIVE PROMPT:\n{positive}")
                print(f"\nNEGATIVE PROMPT:\n{bg_neg}")
                print()
                if remaining < 0:
                    all_ok = False

        if args.mode == "key_visual":
            print("\n── KEY VISUAL PROMPTS ──")
            kv_neg = build_key_visual_negative(data)
            for character in characters:
                positive = build_key_visual_prompt(character, data)
                remaining = max_len - len(positive)
                status = "✅" if remaining >= 0 else "❌"
                print(f"\n--- {character['name']} key visual ---")
                print(f"  Positive: {len(positive)} / {max_len} chars "
                      f"({remaining} remaining) {status}")
                print(f"\nPOSITIVE PROMPT:\n{positive}")
                print(f"\nNEGATIVE PROMPT:\n{kv_neg}")
                print()
                if remaining < 0:
                    all_ok = False

        if not all_ok:
            print(f"❌ Some prompts exceed the {max_len}-char limit. "
                  "Fix before generating.")
            sys.exit(1)
        print(f"✅ All prompts within {max_len}-character limit.")
        return

    # Actual generation
    all_results = []

    if args.mode in ("portrait", "composite"):
        print(f"\nGenerating {len(characters)} portrait(s) for {project}...")
        print(f"Output directory: {output_dir}")
        if args.seed is not None:
            print(f"Using fixed seed: {args.seed}")
        portrait_results = generate_portraits(
            api_key, characters, data, output_dir, seed=args.seed,
        )
        all_results.extend(portrait_results)

    if args.mode in ("background", "composite"):
        print(f"\nGenerating backgrounds for {project}...")
        bg_results = generate_backgrounds(
            api_key, characters, data, output_dir, seed=args.seed,
        )
        all_results.extend(bg_results)

    if args.mode == "key_visual":
        print(f"\nGenerating key visuals for {project}...")
        print(f"Output directory: {output_dir}")
        if args.seed is not None:
            print(f"Using fixed seed: {args.seed}")
        kv_results = generate_key_visuals(
            api_key, characters, data, output_dir, seed=args.seed,
        )
        all_results.extend(kv_results)

    if args.mode == "composite" and HAS_PILLOW:
        print("\n── POST-PROCESSING ──")
        run_post_processing(characters, data, output_dir, seed=args.seed)
    elif args.mode == "composite" and not HAS_PILLOW:
        print("\n⚠️  Pillow not installed — skipping post-processing.")
        print("   Install with: pip install Pillow")

    # Save generation log
    log_path = output_dir / "generation-log.json"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "w") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    print(f"\nGeneration log saved to: {log_path}")

    # Summary
    print(f"\n{'='*60}")
    print(f"GENERATION SUMMARY ({project})")
    print(f"{'='*60}")
    success = sum(1 for r in all_results if r["status"] == "success")
    failed = sum(1 for r in all_results if r["status"] == "failed")
    skipped = sum(1 for r in all_results if r["status"] == "skipped")
    print(f"Total: {len(all_results)} | ✅ Success: {success} | "
          f"⏭️ Skipped: {skipped} | ❌ Failed: {failed}")
    print()

    for r in all_results:
        layer = r.get("layer", "?")
        label = r.get("character", "?")
        if r["status"] == "success":
            img_count = len(r.get("images", []))
            seeds = ", ".join(
                str(img.get("seed", "?")) for img in r.get("images", [])
            )
            print(f"  ✅ {label} [{layer}] — {img_count} image(s), "
                  f"seeds: [{seeds}]")
        elif r["status"] == "skipped":
            print(f"  ⏭️  {label} [{layer}] — already exists, skipped")
        else:
            error = r.get("error", "unknown error")
            if len(error) > 120:
                error = error[:120] + "..."
            print(f"  ❌ {label} [{layer}] — {error}")

    if failed > 0:
        print(f"\n💡 Tip: Re-run failed characters individually:")
        char_file = args.characters
        for r in all_results:
            if r["status"] == "failed" and r.get("character"):
                print(f"   python3 scripts/avatar-generation/generate.py "
                      f"--characters {char_file} "
                      f"--character {r['character']} "
                      f"--mode {r.get('layer', 'portrait')}")
        print(f"\n⚠️  Partial results saved to: {log_path}")
        sys.exit(1)


if __name__ == "__main__":
    main()
