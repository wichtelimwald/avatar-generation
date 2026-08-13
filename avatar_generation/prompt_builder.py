"""
Shared Avatar Generation — Prompt Builder

Builds portrait and background prompts from JSON character definitions.
The JSON file contains project-wide style blocks, optional archetype themes,
and per-character prompt text.
"""
from __future__ import annotations

import json
from pathlib import Path


def load_character_file(path: str | Path) -> dict:
    """Load and return a character definition JSON file.

    Args:
        path: Path to the JSON character definition file.

    Returns:
        Parsed JSON as a dictionary.
    """
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_characters(data: dict, *,
                   names: list[str] | None = None,
                   archetype: str | None = None,
                   test_only: bool = False) -> list[dict]:
    """Select characters from a loaded character definition.

    Args:
        data: Parsed character definition dictionary.
        names: Filter by character name(s).
        archetype: Filter by archetype key (e.g. ``"WILD"``).
        test_only: Return only test characters (listed in ``test_characters``).

    Returns:
        List of character dictionaries.
    """
    characters = data.get("characters", [])

    if test_only:
        test_names = {n.lower() for n in data.get("test_characters", [])}
        if test_names:
            characters = [c for c in characters if c["name"].lower() in test_names]
        else:
            characters = characters[:5]

    if names:
        name_set = {n.lower() for n in names}
        characters = [c for c in characters if c["name"].lower() in name_set]

    if archetype:
        arch = archetype.upper()
        characters = [c for c in characters if c.get("archetype", "").upper() == arch]

    return characters


def build_portrait_negative(character: dict, data: dict) -> str:
    """Assemble negative prompt for portrait generation.

    Combines the project-wide portrait negative with group-specific additions
    based on character properties.

    Args:
        character: Character dictionary from the JSON file.
        data: Full character definition dictionary (for ``negative_prompt_groups``).

    Returns:
        Assembled negative prompt combining style-level and group-specific
        exclusions, joined by ``", "``.
    """
    style = data.get("style", {})
    groups = data.get("negative_prompt_groups", {})

    parts = [style.get("portrait_negative", "")]

    age_group = character.get("age_group", "")
    if age_group in groups:
        parts.append(groups[age_group])

    archetype = character.get("archetype", "").upper()
    arch_lower = archetype.lower()
    if arch_lower in groups:
        parts.append(groups[arch_lower])

    # Combined group keys (e.g. "climb_wild" applies to both CLIMB and WILD)
    for group_key, group_neg in groups.items():
        if "_" in group_key and group_key not in (age_group, arch_lower):
            sub_keys = group_key.split("_")
            if arch_lower in sub_keys:
                parts.append(group_neg)

    if character.get("has_glasses", False) and "glasses" in groups:
        parts.append(groups["glasses"])

    return ", ".join(p for p in parts if p)


def build_portrait_prompt(character: dict, data: dict) -> str:
    """Assemble portrait positive prompt.

    Combines the project-wide style prompt with the character-specific prompt
    and background colour line.

    Args:
        character: Character dictionary.
        data: Full character definition dictionary.

    Raises:
        ValueError: If the combined prompt exceeds ``prompt_max_length``.
    """
    style = data.get("style", {})
    archetypes = data.get("archetypes", {})
    max_len = style.get("prompt_max_length", 1500)

    style_prompt = style.get("portrait_prompt", "").strip()

    # Resolve background colours (character-level overrides archetype-level)
    if "bg_colours" in character:
        c1, c2 = character["bg_colours"]
    else:
        archetype = character.get("archetype", "")
        theme = archetypes.get(archetype, {})
        colours = theme.get("colours", ["blue", "purple"])
        c1, c2 = colours[0], colours[1]

    bg_line = f"On soft {c1} to {c2} gradient background."

    char_prompt = character["character_prompt"]

    prompt = (
        f"{style_prompt}\n\n"
        f"{char_prompt}\n{bg_line}"
    )

    if len(prompt) > max_len:
        raise ValueError(
            f"Portrait prompt for {character['name']} is {len(prompt)} chars "
            f"(limit {max_len}). "
            f"Style={len(style_prompt)}, "
            f"Character={len(char_prompt)}, "
            f"Background={len(bg_line)}. "
            f"Shorten the character prompt by {len(prompt) - max_len} chars."
        )
    return prompt


def build_background_prompt(character: dict, data: dict) -> str:
    """Build background generation prompt for a specific character.

    If the character has a ``background_prompt_override``, it replaces the
    style-level background prompt entirely. Otherwise, per-character colours
    and symbols are combined with the project-wide style.

    Args:
        character: Character dictionary.
        data: Full character definition dictionary.

    Raises:
        ValueError: If the combined prompt exceeds ``prompt_max_length``.
    """
    style = data.get("style", {})
    archetypes = data.get("archetypes", {})
    max_len = style.get("prompt_max_length", 1500)

    # Full override (used by org-spirits where each character has a unique scene)
    if "background_prompt_override" in character:
        bg_style = style.get("background_prompt", "").strip()
        override = character["background_prompt_override"].strip()
        prompt = f"{bg_style}\n\n{override}" if bg_style else override
        if len(prompt) > max_len:
            raise ValueError(
                f"Background prompt for {character['name']} is {len(prompt)} chars "
                f"(limit {max_len})."
            )
        return prompt

    # Default: use archetype/character colours + symbols
    bg_style = style.get("background_prompt", "").strip()

    if "bg_colours" in character:
        c1, c2 = character["bg_colours"]
        symbols = character.get("bg_symbols", "abstract shapes")
    else:
        archetype = character.get("archetype", "")
        theme = archetypes.get(archetype, {})
        colours = theme.get("colours", ["blue", "purple"])
        c1, c2 = colours[0], colours[1]
        symbols = theme.get("symbols", "abstract shapes")

    bg_char = (
        f"{c1} to {c2} gradient background, atmospheric, calm, no people. "
        f"Very faint abstract shapes inspired by {symbols}, soft bokeh glow. "
        f"Minimal detail, suitable as mobile app background with text overlay."
    )
    prompt = f"{bg_style}\n\n{bg_char}"

    if len(prompt) > max_len:
        raise ValueError(
            f"Background prompt for {character['name']} is {len(prompt)} chars "
            f"(limit {max_len})."
        )
    return prompt


def build_key_visual_prompt(character: dict, data: dict) -> str:
    """Build key visual generation prompt for a specific character/category.

    Combines the project-wide ``key_visual_prompt`` style with the per-entry
    ``kv_prompt`` and a gradient background line derived from ``bg_colours``.

    Args:
        character: Character/category dictionary with ``kv_prompt`` and
            ``bg_colours`` fields.
        data: Full character definition dictionary.

    Raises:
        ValueError: If the entry has no ``kv_prompt`` or the combined prompt
            exceeds ``prompt_max_length``.
    """
    style = data.get("style", {})
    max_len = style.get("prompt_max_length", 1500)

    kv_style = style.get("key_visual_prompt", "").strip()
    kv_prompt = character.get("kv_prompt", "").strip()

    if not kv_prompt:
        raise ValueError(
            f"Character '{character['name']}' has no 'kv_prompt' field. "
            f"Key visual generation requires a per-entry kv_prompt."
        )

    # Resolve gradient colours for the background line
    if "bg_colours" in character:
        c1, c2 = character["bg_colours"]
    else:
        c1, c2 = "blue", "purple"

    bg_line = f"On soft {c1} to {c2} gradient background."

    prompt = f"{kv_style}\n\n{kv_prompt}\n{bg_line}"

    if len(prompt) > max_len:
        raise ValueError(
            f"Key visual prompt for {character['name']} is {len(prompt)} chars "
            f"(limit {max_len}). "
            f"Style={len(kv_style)}, "
            f"KV={len(kv_prompt)}, "
            f"Background={len(bg_line)}. "
            f"Shorten the kv_prompt by {len(prompt) - max_len} chars."
        )
    return prompt


def build_key_visual_negative(data: dict) -> str:
    """Return the key visual negative prompt from style configuration.

    Falls back to the background negative prompt if ``key_visual_negative``
    is not defined.

    Args:
        data: Full character definition dictionary.

    Returns:
        Negative prompt string for key visual generation.
    """
    style = data.get("style", {})
    return style.get(
        "key_visual_negative",
        style.get("background_negative", ""),
    )
