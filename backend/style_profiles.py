"""Glumoo SOP and product-level styles shared by outline, copy, and images."""

from typing import Optional

STYLE_PROFILES = {
    "general": "",
    "pet_education": "宠物科普：从误区切入，用原理、观察信号、分步建议和安全提醒展开；不做诊断。",
    "pet_product": "宠物产品种草：按使用场景、真实痛点、产品细节、使用过程、宠物反应和适用边界组织。",
    "pet_lifestyle": "养宠日常：用具体时间、场景和宠物小动作讲故事，保留少量不完美细节。",
}

GLUMOO_STYLES = {
    "glumoo_1": ("趣味波普社媒", "高饱和色彩、趣味造型、社媒感；保持真实摄影，不做廉价卡通或塑料 3D。"),
    "glumoo_2": ("日光家庭纪实", "自然日光、家庭生活瞬间、克制真实；保留生活细节，避免棚拍和过度磨皮。"),
    "glumoo_3": ("高饱和几何色块", "几何空间、明确色块、冷暖对比；产品必须落在可信表面，不得悬浮。"),
    "glumoo_4": ("品牌蓝雕塑静物", "以品牌蓝为主、雕塑式层次、精准静物摄影；产品几何和包装识别最高优先。"),
    "glumoo_5": ("户外机能远征", "真实户外地貌、机能装备、行动感；产品承托、比例和环境光必须合理。"),
    "glumoo_6": ("成分证据编辑", "用可核实的成分、用法或边界组织编辑叙事；不伪造数据、证书、疗效或包装文字。"),
    "glumoo_7": ("瑞士海报编辑", "网格、留白、尺度对比和克制编辑秩序；正文图不让模型生成文字，封面字后置。"),
    "glumoo_8": ("35mm 时装纪实", "35mm 现场感、时装摄影构图、自然颗粒和不刻意动作；不做过度摆拍。"),
    "glumoo_9": ("超现实冷幽默", "用一个可读的超现实反差制造冷幽默；产品身份、物理关系和生物解剖仍须真实。"),
    "glumoo_10": ("触感微距感官", "微距展示毛发、爪、手、材质和产品的触感关系；浅景深不牺牲关键包装识别。"),
    "glumoo_11": ("策展式编辑拼贴", "策展式并置、材料层次与编辑关系；仅本风格允许拼贴，且不得破坏产品身份。"),
    "glumoo_12": ("超广角亲密视角", "近距离超广角透视、强前后尺度与亲密镜头互动；避免鼻部失焦、暗背景和产品透视变形。"),
    "glumoo_13": ("俯拍生活图谱", "在一个连续真实场景中用俯拍组织宠物、产品、工具与人的局部使用线索；不是碎片拼贴或电商目录平铺。"),
    "glumoo_14": ("高速瞬间定格", "清晰冻结真实动作、耳毛运动与视线因果；禁止失焦拖影、速度线、夸张飞溅和悬空包装。"),
    "glumoo_15": ("节日生活方式", "按本次明确节日建立真实生活关系和克制庆祝氛围；不自动猜节日，不改产品配色，不堆促销贴纸。"),
}

def is_glumoo_style(style_id: str) -> bool:
    return style_id == "glumoo" or style_id in GLUMOO_STYLES

def get_glumoo_style_instruction(style_id: str) -> str:
    if style_id == "glumoo":
        return "Glumoo 自由创意：不预设场景类型，只从本次六张参考图动态归纳临时视觉规则。"
    name, boundary = GLUMOO_STYLES[style_id]
    return f"Glumoo 风格 {style_id.split('_')[-1]}·{name}：{boundary}"

GLUMOO_OUTLINE_INSTRUCTION = """
使用 Glumoo 当前版 SOP。输出恰好 7 页：前 6 页全部标记为[内容]，最后 1 页标记为[封面]。封面在执行阶段才从通过验收的正文图派生，不得先生成封面来约束正文。

六张正文不设固定页面角色。必须先对用户当次提供的 6 张独立主参考图做动态归纳，只提取多数图共同且与主题一致的色彩、光线、材质、空间、镜头、人物宠物关系与产品位置规律；不得使用预设的“多巴胺家居/商业摄影/自然风光/户外生活”分类。

六页整体必须覆盖：至少 2 个可识别的生活时刻，至少 1 页可信的产品使用，至少 1 页选择依据/使用边界/可核实证据；纯产品或抽象页最多 2 页。移除品牌名后，每页的生活任务仍应能被看懂。

每页必须写明：页面意图、生活时刻、消费决策中的作用、绑定的主参考图序号（1–6，一页仅一张）、镜头/光线/动作、产品合约（身份、形状、数量、位置、比例、角度、承托面、遮挡与安全区），以及“上图短句：”字段。短句为一句消费者可见的定稿小字，简洁、可核实、不出现内部 SKU 代号。第 1 页作为最高风险证明图，优先验证产品身份、物理关系和艺术方向。

内容只有一个传播目标，按真实问题→观察判断→可执行方法→产品自然出现→适用边界→克制总结展开，不写硬广、诊断或不可核实的疗效。
"""

GLUMOO_CONTENT_INSTRUCTION = """
按 Glumoo 克制种草口吻写：具体养宠场景、可执行建议、产品自然出现、使用边界。不把产品写成药品，不承诺疗效，不伪造包装或检测信息。标签自然包含 #NAGLUMOO。
"""

GLUMOO_VISUAL_BASE = """
【Glumoo 当前版 SOP·清洁输入】
本页生图只允许使用：本页绑定的一张主参考图、本页必需的产品素材、明确启用的局部蒙版/恢复层、本页布局合约。排除其他五张主参考、旧生成图、失败图、QA 截图和临时拼图。只学习参考图的构图、光线、材质、景深和关系，不复制具体作品。

先锁定产品：包装形状与长宽比、主色、Logo/品名布局、封口或瓶盖、数量、位置、比例、角度、承托面、遮挡关系和安全区。禁止改字、换色、重画 Logo、增减包装、悬浮、错误投影或不合理比例。无法可靠复现小字时宁可弱化，不得伪造。

产品资产与摄影参考严格分轨：摄影参考只控制构图、光线、材质和关系；正式产品母图锁身份、几何和颜色；透明恢复层只允许兼容时局部保护或修复，不能代替主产品图。完整全家福必须是三款主包装加六款身份各不相同的 Glumoo PRO，共九件独立产品，禁止一款换色、复制或用旧拼图冒充。Glumoo PRO 圆罐保持高窄直筒；与大袋同一承重面时可见高度约为袋高 45%–55%，与横盒同画面时不高于盒高约 80%，无大包装对照时不超过整张竖图高度约 28%。

竖版 3:4，真实商业级摄影，毛发、皮肤、肢体、接触、重力、透视、光影可信。生图模型不得生成消费者文字、标题、便签、图标、水印或平台 Logo；六张正文各有一句来自本页定稿内容的消费者可见小字，由后期文字层准确排版，不能为加字重画照片或包装。除非编号风格明确允许，否则不做拼贴。

生成后按 A/B/C 处理：A 通过；B 只做一次局部蒙版修复；C（产品身份、几何、主要文字、清晰度、解剖或物理错误）必须回到清洁输入重生，不在失败图上链式修改。原图 100% 检查后缩放到 1080×1440，再复查成品与文件完整性。
"""

def get_style_instruction(style_id: str) -> str:
    if is_glumoo_style(style_id):
        return f"{get_glumoo_style_instruction(style_id)}\n\n{GLUMOO_VISUAL_BASE.strip()}"
    return STYLE_PROFILES.get(style_id, "").strip()

def get_outline_style_instruction(style_id: str, topic: str = "") -> str:
    if not is_glumoo_style(style_id):
        return get_style_instruction(style_id)
    return f"{GLUMOO_OUTLINE_INSTRUCTION.strip()}\n\n【本次启用】{get_glumoo_style_instruction(style_id)}"

def get_content_style_instruction(style_id: str) -> str:
    if not is_glumoo_style(style_id):
        return get_style_instruction(style_id)
    return f"{GLUMOO_CONTENT_INSTRUCTION.strip()}\n{get_glumoo_style_instruction(style_id)}"

def get_image_style_instruction(
    style_id: str,
    page_type: str = "content",
    page_index: int = 0,
    total_count: Optional[int] = None,
    topic: str = "",
) -> str:
    if not is_glumoo_style(style_id):
        return get_style_instruction(style_id)
    if page_type == "cover":
        page_rule = "最后派生封面：以一张已验收正文为底图，不改变人、宠物、产品和场景；标题/副标题后置，品牌蓝 #074BBC，两级信息。"
    else:
        page_rule = f"第 {page_index + 1} 张正文；只使用大纲绑定的那一张主参考。第 1 张是最高风险证明图。"
    return f"{GLUMOO_VISUAL_BASE.strip()}\n\n【本次美术方向】{get_glumoo_style_instruction(style_id)}\n\n【本页】{page_rule}"
