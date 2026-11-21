"""Deterministic Glumoo delivery sizing and post-rendered typography."""

from __future__ import annotations

import re
from pathlib import Path
from typing import BinaryIO

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps, ImageStat

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


def cover_copy(page_content: str, legacy_topic: str, products=()) -> tuple[str, str]:
    """Read the editable cover page; old outlines may only have a page sentence."""
    from backend.services.glumoo_product_scope import OFFICIAL_PRODUCTS

    def field(names):
        match = re.search(
            rf"(?m)^[ \t]*(?:[-·*][ \t]+)?(?:\*\*)?(?:{names})(?:\*\*)?[ \t]*[：:][ \t]*(.+?)[ \t]*$",
            page_content or "",
        )
        return match.group(1).strip(' *“”"') if match else ""

    title = field("封面主标题|主标题|标题") or field("上图短句") or legacy_topic
    subtitle = field("封面副标题|副标题")
    if not subtitle:
        labels = [OFFICIAL_PRODUCTS.get(Path(name).name, "") for name in products]
        identities = {re.sub(r"独立条装|圆罐|袋装|盒装", "", label) for label in labels}
        if len(identities) == 1 and all(labels):
            identity = identities.pop()
            subtitle = identity if identity.startswith("Glumoo") else f"Glumoo {identity}"
        else:
            subtitle = "Glumoo PRO" if labels and all("PRO" in label for label in labels) else "Glumoo"
    return (title or "").strip(), subtitle


def _cover_font(size, bold):
    weight = "Bold" if bold else "Regular"
    mac_weight = "Medium" if bold else "Light"
    for path, index in (
        (f"/usr/share/fonts/opentype/noto/NotoSansCJK-{weight}.ttc", 2),
        (f"/System/Library/Fonts/STHeiti {mac_weight}.ttc", 1),
    ):
        if Path(path).is_file():
            return ImageFont.truetype(path, size=size, index=index)
    raise ValueError("封面缺少可用的简体中文字体，请检查服务字体配置。")


def _headline_layout(text):
    # Keep English names together and give natural Chinese phrase boundaries priority.
    tokens = re.findall(r"[A-Za-z0-9]+|\s+|.", text)
    max_width = 816
    for size in (100, 96, 92, 88):
        font = _cover_font(size, True)
        options = []
        if font.getlength(text) <= max_width:
            options.append((0, [text]))
        for index in range(1, len(tokens)):
            left = "".join(tokens[:index]).rstrip()
            right = "".join(tokens[index:]).lstrip()
            if not left or not right or right[0] in "，。！？、；：,.!?）】”" or left[-1] in "（【“":
                continue
            a, b = font.getlength(left), font.getlength(right)
            if max(a, b) > max_width:
                continue
            natural = left[-1] in "，。！？、；：,.!?:"
            cost = abs(a-b) / size + (0 if natural else 6)
            if natural and min(a, b) >= 2 * size:
                cost -= 5
            options.append((cost, [left, right]))
        if options:
            return font, min(options, key=lambda item: item[0])[1]
    raise ValueError("封面主标题在安全区内放不下，请在大纲中精简为一个可分两行的短句。")


def _cover_position(canvas, width, height):
    # Evaluate the whole type block to avoid choosing a bright spot in a busy scene.
    gray = canvas.convert("L").resize((270, 360), Image.Resampling.BOX)
    edges = gray.filter(ImageFilter.FIND_EDGES)
    best = None
    for y in (76, 120, 164):
        for x in (80, (1080 - width) // 2, 1000 - width):
            box = (x // 4, y // 4, (x + width + 3) // 4, (y + height + 3) // 4)
            histogram = gray.crop(box).histogram()
            dark_fraction = sum(histogram[:155]) / sum(histogram)
            detail = ImageStat.Stat(edges.crop(box)).mean[0]
            if dark_fraction > 0.28 or detail > 39:
                continue
            # Prefer a common left edge higher on the page when backgrounds read equally well.
            score = dark_fraction * 120 + detail + (x - 80) / 100 + (y - 76) / 28
            if best is None or score < best[0]:
                best = score, x, y
    if best is None:
        raise ValueError("这张底图上方缺少能读清品牌蓝文字的留白，请重做第 1 张正文并留出明亮空位，再重试封面。")
    return best[1:]


def render_cover(source_path: str | Path, output_path: str | Path | BinaryIO, title: str, subtitle: str) -> None:
    """Set two levels of brand-blue type directly on the clean photograph."""
    title = " ".join(title.split())
    if not title:
        raise ValueError("请先在封面大纲填写主标题。")
    if len(title) > 64:
        raise ValueError("请在封面大纲中将主标题精简为一至两行。")
    title_font, lines = _headline_layout(title)
    sub_font = _cover_font(38, False)
    if sub_font.getlength(subtitle) > 816:
        raise ValueError("请在封面大纲中将副标题精简为一行产品名或系列名。")
    with Image.open(source_path) as source:
        canvas = _fit_delivery(source)
    draw = ImageDraw.Draw(canvas)
    runs = []
    top = 0
    for line in lines:
        runs.append((line, title_font, top))
        top += title_font.size + 7
    last = runs[-1]
    sub_top = last[2] + title_font.getbbox(last[0], anchor="lt")[3] + 24
    runs.append((subtitle, sub_font, sub_top))
    boxes = [font.getbbox(text, anchor="lt") for text, font, _ in runs]
    width = max(box[2] - min(0, box[0]) for box in boxes)
    height = sub_top + boxes[-1][3]
    x, y = _cover_position(canvas, width, height)
    for (text, font, offset), box in zip(runs, boxes):
        draw.text((x - box[0], y + offset), text, font=font, fill=BRAND_BLUE, anchor="lt")
    canvas.save(output_path, format="PNG", optimize=True)
