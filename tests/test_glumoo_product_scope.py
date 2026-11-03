from backend.services.glumoo_product_scope import find_scope_conflict, product_scope_instruction
from backend.style_profiles import GLUMOO_STYLES, get_glumoo_style_instruction
from backend.services.outline import OutlineService
from unittest.mock import Mock
import pytest


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


@pytest.mark.parametrize("content", [
    "产品合约：不要袋装或盒装，只使用六款圆罐。",
    "产品合约：不是盒装，而是圆罐。",
    "产品合约：未选择袋装，禁止盒装和条包。",
    "产品合约：袋装不得出现。",
    "产品合约：禁止袋装、盒装、条包。",
    "不沿用参考图中的盒装产品、品牌文字或包装。",
])
def test_negative_packaging_mentions_are_not_product_requests(content):
    assert find_scope_conflict(CANS, [{"index": 0, "content": content}]) is None


@pytest.mark.parametrize("content", [
    "产品无遮挡，盒装一盒放在桌上。",
    "不遮挡宠物；摆放自立袋一袋。",
    "产品合约：无遮挡的袋装一袋。",
])
def test_unrelated_negation_does_not_hide_real_scope_conflicts(content):
    assert find_scope_conflict(CANS, [{"index": 0, "content": content}])


def _outline_service_with_responses(*responses):
    service = OutlineService.__new__(OutlineService)
    service.text_config = {"active_provider": "test", "providers": {"test": {"model": "test"}}}
    service.client = Mock()
    service.client.generate_text.side_effect = responses
    return service


def test_outline_repairs_wrong_products_once_and_returns_corrected_pages():
    service = _outline_service_with_responses(
        "[内容]\n产品合约：盒装一盒。",
        "[内容]\n产品合约：强骨力圆罐一罐。",
    )
    result = service.generate_outline("全家桶", [b"reference"], style_id="glumoo_7",
                                      product_images=[b"product"], product_names=CANS[:1])
    assert result["success"]
    assert "圆罐" in result["pages"][0]["content"]
    assert service.client.generate_text.call_count == 2
    assert service.client.generate_text.call_args.kwargs["images"] == [b"reference", b"product"]


def test_failed_scope_repair_is_retryable_generation_error_not_bad_user_input():
    service = _outline_service_with_responses(*(["[内容]\n产品合约：盒装一盒。"] * 2))
    result = service.generate_outline("全家桶", style_id="glumoo_7", product_names=CANS)
    assert not result["success"]
    assert result["error"]["code"] == "PRODUCT_SCOPE_CONFLICT"
    assert result["error"]["status"] == 502
    assert result["error"]["retryable"]
    assert service.client.generate_text.call_count == 2
