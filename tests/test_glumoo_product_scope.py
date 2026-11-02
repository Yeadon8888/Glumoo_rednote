from backend.services.glumoo_product_scope import find_scope_conflict, product_scope_instruction
from backend.style_profiles import GLUMOO_STYLES, get_glumoo_style_instruction


CANS = [f"glumoo_official_0{i}_{name}.png" for i, name in enumerate(
    ("bonemax", "flexmax", "gutmax", "urimax", "furmax", "immumax"), 4
)]


def test_six_selected_cans_exclude_unselected_packages():
    assert "仅允许" in product_scope_instruction(CANS)
    assert find_scope_conflict(CANS, [{"index": 0, "content": "产品合约：圆罐一件、自立袋一袋。"}])
    assert find_scope_conflict(CANS, [{"index": 0, "content": "圆罐一件。禁止自立袋、盒装。"}]) is None


def test_mixed_or_unknown_products_do_not_trigger_can_only_assumption():
    assert find_scope_conflict(["asset_unknown.png"], [{"index": 0, "content": "一袋产品"}]) is None
    assert "不得捏造" in product_scope_instruction(["asset_unknown.png"])


def test_all_registered_styles_have_specific_sop_details():
    for style in GLUMOO_STYLES:
        instruction = get_glumoo_style_instruction(style)
        assert "视觉语言" in instruction
        assert "质量边界" in instruction
