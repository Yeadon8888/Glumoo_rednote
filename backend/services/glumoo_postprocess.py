"""Deterministic Glumoo delivery sizing and post-rendered typography."""

from __future__ import annotations

import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

BRAND_BLUE = "#074BBC"
DELIVERY_SIZE = (1080, 1440)
FONT_CANDIDATES = (
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/System/Library/Fonts/PingFang.ttc",
    "/System/Library/Fonts/STHeiti Medium.ttc",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
)


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = FONT_CANDIDATES if bold else FONT_CANDIDATES[1:] + FONT_CANDIDATES[:1]
    for candidate in candidates:
        if Path(candidate).is_file():
            return ImageFont.truetype(candidate, size=size)
    return ImageFont.load_default()


def _font_to_fit(text: str, max_width: int, start_size: int, min_size: int, bold: bool = False):
    """Choose the largest configured font that keeps one approved line inside its card."""
    for size in range(start_size, min_size - 1, -2):
        font = _font(size, bold=bold)
        box = font.getbbox(text)
        if box[2] - box[0] <= max_width:
            return font
    return _font(min_size, bold=bold)


def extract_overlay_text(page_content: str, fallback: str = "把日常照护，做得更有依据") -> str:
    """Extract the approved per-page sentence without exposing internal planning fields."""
    match = re.search(r"(?:上图短句|正文短句|页面短句)\s*[：:]\s*([^\n]+)", page_content or "")
    text = match.group(1) if match else ""
    text = re.sub(r"[#*_<>]+", "", text).strip(" \t\"'“”‘’。")
    return (text or fallback)[:28]


def _fit_delivery(image: Image.Image) -> Image.Image:
    return ImageOps.fit(
        image.convert("RGB"),
        DELIVERY_SIZE,
        method=Image.Resampling.LANCZOS,
        centering=(0.5, 0.5),
    )


def render_body_text(image_path: str | Path, page_content: str) -> None:
    """Add one restrained text layer after generation and normalize to 1080×1440."""
    path = Path(image_path)
    with Image.open(path) as source:
        canvas = _fit_delivery(source)
    draw = ImageDraw.Draw(canvas, "RGBA")
    text = extract_overlay_text(page_content)
    font = _font(34)
    box = draw.textbbox((0, 0), text, font=font)
    width, height = box[2] - box[0], box[3] - box[1]
    x, y = 64, DELIVERY_SIZE[1] - height - 82
    draw.rounded_rectangle(
        (x - 18, y - 12, x + width + 18, y + height + 12),
        radius=14,
        fill=(255, 255, 255, 218),
    )
    draw.text((x, y), text, font=font, fill=BRAND_BLUE)
    canvas.save(path, format="PNG", optimize=True)


def render_cover(
    source_path: str | Path,
    output_path: str | Path,
    title: str,
    subtitle: str = "Glumoo · 科学营养融入每一天",
) -> None:
    """Derive a cover from an accepted body image without regenerating its pixels."""
    with Image.open(source_path) as source:
        canvas = _fit_delivery(source)
    draw = ImageDraw.Draw(canvas, "RGBA")
    title = re.sub(r"\s+", " ", title or "Glumoo 宠物生活指南").strip()[:18]
    subtitle = re.sub(r"\s+", " ", subtitle).strip()[:30]
    title_font = _font_to_fit(title, 900, 72, 44, bold=True)
    subtitle_font = _font_to_fit(subtitle, 890, 32, 24)
    draw.rounded_rectangle((48, 52, 1032, 292), radius=30, fill=(255, 255, 255, 224))
    draw.text((82, 88), title, font=title_font, fill=BRAND_BLUE)
    draw.text((84, 210), subtitle, font=subtitle_font, fill=BRAND_BLUE)
    canvas.save(output_path, format="PNG", optimize=True)
