"""Product-level content styles shared by outline, copy, and image generation."""

STYLE_PROFILES = {
    "general": "",
    "glumoo": """
Glumoo 专属内容系统：
- 用“真实宠物问题 → 可执行解法 → 产品自然入镜”的逻辑，不做生硬广告。
- 默认规划 7 页完整套图：1 页封面 + 5 页逐步讲解 + 1 页总结/行动建议。
- 保持宠物、产品包装、品牌色和比例的连续一致；有参考图时优先保真实产品身份。
- 画面是高级但真实的宠物生活摄影，温暖、干净、克制，每页只有一个信息重心。
- 每页图上小字必须简短、可读、不遮挡主体。
- 小红书文案自然包含品牌标签 #NAGLUMOO，避免医疗化和夸大承诺。
""",
    "pet_education": """
宠物科普模板：从一个常见误区切入，用简单原理、可观察信号、分步建议和安全提醒展开；不做诊断，明确异常情况需咨询专业兽医。
""",
    "pet_product": """
宠物产品种草模板：按“使用场景、真实痛点、产品细节、使用过程、宠物反应、适用边界”组织，让产品作为解法自然出现。
""",
    "pet_lifestyle": """
养宠日常模板：用具体时间、场景和宠物小动作讲故事，语气亲近、有生活感，保留少量不完美细节，避免摆拍感和过度营销。
""",
}


def get_style_instruction(style_id: str) -> str:
    return STYLE_PROFILES.get(style_id, STYLE_PROFILES["general"]).strip()
