from backend.style_profiles import (
    get_content_style_instruction,
    get_glumoo_reference_calibration,
    get_image_style_instruction,
    get_outline_style_instruction,
    get_style_instruction,
)


def test_glumoo_outline_requires_exact_seven_page_story():
    instruction = get_outline_style_instruction("glumoo", "彩色新品系列")
    assert "恰好 7 页" in instruction
    assert "画面意图" in instruction
    assert "真实问题 → 观察判断" in instruction
    assert instruction.count("参考锚点 ") == 6


def test_glumoo_image_prompt_matches_railway_history_photography():
    instruction = get_image_style_instruction("glumoo", "content", 4, 7, "户外露营")
    assert "Pinterest" in instruction
    assert "产品身份锁定" in instruction
    assert "图片上不叠加标题" in instruction
    assert "第 5 页·细节场景" in instruction
    assert "不要给矩阵套用预设风格名" in instruction


def test_glumoo_page_direction_changes_across_sequence():
    cover = get_image_style_instruction("glumoo", "cover", 0, 7)
    action = get_image_style_instruction("glumoo", "content", 3, 7)
    summary = get_image_style_instruction("glumoo", "summary", 6, 7)
    assert "品牌锚点" in cover
    assert "正在取用" in action
    assert "全家福" in summary


def test_glumoo_copy_is_restrained_and_branded():
    instruction = get_content_style_instruction("glumoo")
    assert "#NAGLUMOO" in instruction
    assert "不要把产品写成药品" in instruction


def test_non_glumoo_styles_keep_backward_compatible_lookup():
    assert get_outline_style_instruction("pet_lifestyle") == get_style_instruction("pet_lifestyle")
    assert get_image_style_instruction("general") == ""


def test_reference_calibration_is_deterministic_and_unlabelled():
    first = get_glumoo_reference_calibration("秋日露营")
    second = get_glumoo_reference_calibration("秋日露营")

    assert first == second
    assert first.count("参考锚点 ") == 6
    assert "无标签参考矩阵" in first
    assert "动态归纳" in first
    assert "本套唯一视觉路线" not in first
    assert "多巴胺家居商业摄影" not in first
