from pathlib import Path

import pytest
from PIL import Image, ImageDraw

from backend.services.glumoo_postprocess import (
    BRAND_BLUE,
    DELIVERY_SIZE,
    cover_copy,
    _headline_layout,
    extract_overlay_text,
    render_body_text,
    render_cover,
)


def test_extract_overlay_text_uses_explicit_page_sentence():
    assert extract_overlay_text("页面意图：陪伴\n上图短句：把营养放进每一天") == "把营养放进每一天"


def test_body_and_cover_are_exact_delivery_size(tmp_path: Path):
    source = tmp_path / "source.png"
    body = tmp_path / "body.png"
    cover = tmp_path / "cover.png"
    Image.new("RGB", (900, 1200), "black").save(source)
    body.write_bytes(source.read_bytes())

    render_body_text(body, "上图短句：日常照护，也要有依据")
    Image.new("RGB", (900, 1200), "white").save(source)
    render_cover(source, cover, "出门前，看它怎么起步", "Glumoo 跃力")

    with Image.open(body) as image:
        assert image.size == DELIVERY_SIZE
        assert image.getpixel((70, 1360)) != (0, 0, 0)
    with Image.open(cover) as image:
        assert image.size == DELIVERY_SIZE
        assert image.getpixel((60, 60)) == (255, 255, 255)
        assert image.getpixel((800, 220)) == (255, 255, 255)
        assert any(color == (7, 75, 188) for _, color in image.getcolors(2048))
    assert BRAND_BLUE == "#074BBC"


def test_cover_uses_approved_fields_and_supports_older_outlines():
    page = "[封面]\n封面主标题：出门前，看它怎么起步\n封面副标题：Glumoo 跃力"
    assert cover_copy(page, "内部创作主题") == ("出门前，看它怎么起步", "Glumoo 跃力")
    assert cover_copy("上图短句：散步前看它的第一步", "内部创作主题", ["glumoo_official_02_jump_bag.png"]) == (
        "散步前看它的第一步", "Glumoo 跃力"
    )
    assert _headline_layout("出门前，看它怎么起步")[1] == ["出门前，", "看它怎么起步"]


def test_cover_uses_clear_side_and_preserves_unlettered_pixels(tmp_path):
    source, cover = tmp_path / "source.png", tmp_path / "cover.png"
    photo = Image.new("RGB", DELIVERY_SIZE, "#f2e6d8")
    ImageDraw.Draw(photo).rectangle((0, 0, 480, 600), fill="#172033")
    photo.save(source)
    render_cover(source, cover, "散步前", "Glumoo 跃力")
    with Image.open(cover) as rendered:
        assert rendered.crop((0, 0, 480, 600)).tobytes() == photo.crop((0, 0, 480, 600)).tobytes()
        assert rendered.getpixel((905, 280)) == photo.getpixel((905, 280))
    Image.new("RGB", DELIVERY_SIZE, "#172033").save(source)
    with pytest.raises(ValueError, match="留白"):
        render_cover(source, cover, "散步前", "Glumoo 跃力")
