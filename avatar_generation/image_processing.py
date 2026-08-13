"""
Shared Avatar Generation — Image Processing (Pillow)

Functions for circle cropping, neon ring overlay, and avatar compositing.
Requires Pillow (``pip install Pillow``).
"""
from __future__ import annotations

from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFilter
    HAS_PILLOW = True
    # Image.LANCZOS was moved to Image.Resampling.LANCZOS in Pillow 10+
    _LANCZOS = getattr(Image, "Resampling", Image).LANCZOS
except ImportError:
    HAS_PILLOW = False
    _LANCZOS = None  # type: ignore[assignment]


def create_circle_mask(size: int, radius_pct: float = 0.48) -> "Image.Image":
    """Create an anti-aliased circular mask.

    Args:
        size: Canvas size in pixels (square).
        radius_pct: Circle radius as fraction of canvas size (0.48 = 96 % diameter).
    """
    scale = 4
    big = size * scale
    mask = Image.new("L", (big, big), 0)
    draw = ImageDraw.Draw(mask)
    radius = int(big * radius_pct)
    cx, cy = big // 2, big // 2
    draw.ellipse(
        [cx - radius, cy - radius, cx + radius, cy + radius],
        fill=255,
    )
    return mask.resize((size, size), _LANCZOS)


def create_neon_ring(
    size: int,
    rgb: tuple,
    radius_pct: float = 0.48,
    stroke_width: int = 6,
    glow_radius: int = 12,
) -> "Image.Image":
    """Create a glowing neon ring overlay as RGBA image.

    Args:
        size: Canvas size in pixels.
        rgb: ``(R, G, B)`` neon colour.
        radius_pct: Ring radius as fraction of canvas size.
        stroke_width: Ring stroke width in pixels.
        glow_radius: Gaussian blur radius for the glow effect.
    """
    scale = 4
    big = size * scale
    sw = stroke_width * scale

    ring = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    draw = ImageDraw.Draw(ring)
    radius = int(big * radius_pct)
    cx, cy = big // 2, big // 2

    outer = [cx - radius, cy - radius, cx + radius, cy + radius]
    inner_r = radius - sw
    inner = [cx - inner_r, cy - inner_r, cx + inner_r, cy + inner_r]

    draw.ellipse(outer, fill=(*rgb, 255))
    draw.ellipse(inner, fill=(0, 0, 0, 0))

    ring = ring.resize((size, size), _LANCZOS)

    glow = ring.copy()
    glow = glow.filter(ImageFilter.GaussianBlur(radius=glow_radius))

    result = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    result = Image.alpha_composite(result, glow)
    result = Image.alpha_composite(result, ring)
    return result


def circle_crop_portrait(
    portrait_path: Path,
    output_path: Path,
    radius_pct: float = 0.48,
) -> None:
    """Circle-crop a portrait image with transparent background."""
    img = Image.open(portrait_path).convert("RGBA")
    size = img.width
    mask = create_circle_mask(size, radius_pct)

    result = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    result.paste(img, (0, 0), mask)
    result.save(output_path, "PNG")


def composite_avatar(
    portrait_path: Path,
    background_path: Path,
    output_path: Path,
    neon_rgb: tuple = (100, 200, 255),
    radius_pct: float = 0.48,
) -> None:
    """Composite background + circle-cropped portrait + neon ring.

    Args:
        portrait_path: Path to the portrait image.
        background_path: Path to the background image.
        output_path: Path for the composited result.
        neon_rgb: ``(R, G, B)`` neon ring colour.
        radius_pct: Circle radius as fraction of canvas size.
    """
    bg = Image.open(background_path).convert("RGBA")
    portrait = Image.open(portrait_path).convert("RGBA")
    size = bg.width

    if portrait.size != bg.size:
        portrait = portrait.resize(bg.size, _LANCZOS)

    mask = create_circle_mask(size, radius_pct)
    cropped = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    cropped.paste(portrait, (0, 0), mask)

    ring = create_neon_ring(size, neon_rgb, radius_pct)

    result = Image.alpha_composite(bg, cropped)
    result = Image.alpha_composite(result, ring)
    result.save(output_path, "PNG")
