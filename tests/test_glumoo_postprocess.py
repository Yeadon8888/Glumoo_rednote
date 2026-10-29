from pathlib import Path

from PIL import Image

from backend.services.glumoo_postprocess import (
    BRAND_BLUE,
    DELIVERY_SIZE,
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
    render_cover(source, cover, "Glumoo 日常营养")

    with Image.open(body) as image:
        assert image.size == DELIVERY_SIZE
        assert image.getpixel((70, 1360)) != (0, 0, 0)
    with Image.open(cover) as image:
        assert image.size == DELIVERY_SIZE
        assert image.getpixel((60, 60)) != (0, 0, 0)
    assert BRAND_BLUE == "#074BBC"
