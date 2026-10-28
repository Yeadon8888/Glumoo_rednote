from backend.style_profiles import (
    GLUMOO_STYLES,
    get_content_style_instruction,
    get_image_style_instruction,
    get_outline_style_instruction,
    get_style_instruction,
    is_glumoo_style,
)


def test_current_sop_has_free_mode_and_eleven_numbered_styles():
    assert is_glumoo_style("glumoo")
    assert len(GLUMOO_STYLES) == 11
    assert all(is_glumoo_style(f"glumoo_{number}") for number in range(1, 12))


def test_outline_is_six_dynamic_body_pages_then_derived_cover():
    instruction = get_outline_style_instruction("glumoo", "新品")
    assert "前 6 页" in instruction
    assert "最后 1 页" in instruction
    assert "不得先生成封面" in instruction
    assert "一页仅一张" in instruction
    assert "多巴胺家居/商业摄影/自然风光/户外生活" in instruction


def test_image_prompt_enforces_clean_input_and_product_lock():
    instruction = get_image_style_instruction("glumoo_5", "content", 2, 7, "露营")
    assert "清洁输入" in instruction
    assert "排除其他五张" in instruction
    assert "产品" in instruction
    assert "户外机能远征" in instruction
    assert "A/B/C" in instruction


def test_cover_is_derived_last_with_brand_blue():
    instruction = get_image_style_instruction("glumoo", "cover", 6, 7)
    assert "最后派生封面" in instruction
    assert "#074BBC" in instruction


def test_copy_is_restrained_and_branded():
    instruction = get_content_style_instruction("glumoo_6")
    assert "#NAGLUMOO" in instruction
    assert "不承诺疗效" in instruction
    assert "成分证据编辑" in instruction


def test_non_glumoo_styles_keep_backward_compatible_lookup():
    assert get_outline_style_instruction("pet_lifestyle") == get_style_instruction("pet_lifestyle")
    assert get_image_style_instruction("general") == ""
