"""Product-level content styles shared by outline, copy, and image generation."""

import hashlib
from typing import Optional


STYLE_PROFILES = {
    "general": "",
    "glumoo": "Glumoo Pinterest 宠物生活编辑风格",
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


GLUMOO_OUTLINE_INSTRUCTION = """
这是 Glumoo 专属的 Pinterest 宠物生活编辑套系，必须遵守以下规则：

一、固定输出恰好 7 页，不多也不少：
1. 封面：确定本套的主视觉；人、宠物和产品形成一个完整生活场景，不在图片上叠加标题。
2. 日常观察：从宠物一个可观察的小变化或真实痛点切入，不制造焦虑。
3. 方法建议：给出温和、可执行的生活管理方法，画面是宠物正在行动的瞬间。
4. 产品角色：解释产品怎样自然进入日常，不把它写成万能答案。
5. 看包装/用法：只讲最值得确认的 2 到 3 个信息点，不堆参数。
6. 适用边界：提醒适用对象、使用注意和必要时咨询兽医，避免医疗承诺。
7. 总结收藏：用一个有完成感的全家福或产品群像收束。

二、每页内容描述都要明确写出以下四项，方便后续逐页生图：
- 画面意图：这一页要传达的一个核心信息，但该信息不直接印在图片上。
- 场景与动作：具体到家中/户外位置、人物与宠物动作、产品如何自然入镜。
- 镜头：从环境中景、低机位跟拍、动作特写、俯拍静物、产品近景中选择；连续两页不得相同。
- 美术方向：先从本次六参考矩阵动态归纳共同的色彩、材质、光线和空间语言，再写明本页背景、道具和光线；不得套用预设风格名称。

三、内容逻辑：真实问题 → 观察判断 → 可执行方法 → 产品自然出现 → 适用边界 → 克制总结。不要写成硬广、诊断书或功能参数清单。产品名、包装文字和品牌信息只使用参考图中能确认的内容，不能编造。
"""


GLUMOO_CONTENT_INSTRUCTION = """
按 Glumoo 的克制种草口吻写发布文案：先写一个具体养宠场景，再给可执行建议，最后自然提到产品；不要把产品写成药品或承诺疗效。语气像认真做过功课的养宠人，不像品牌公告。

- 标题要有明确问题或收藏价值，避免“震惊、必买、神奇、治愈”等夸张词。
- 正文使用短段落，保留真实观察、使用边界和必要的兽医提醒。
- 标签自然包含 #NAGLUMOO，并补充与主题直接相关的宠物标签；不要堆无关热词。
"""


GLUMOO_VISUAL_BASE = """
【最高优先级：Glumoo Pinterest 宠物生活编辑视觉】
这不是图文信息卡，也不是带标题的海报。成片应像 Railway 历史记录里的 Glumoo 品牌摄影：一组会被收藏到 Pinterest 的商业级宠物生活方式照片。图片上不叠加标题、说明、便签、编号、图标或装饰文字；唯一允许出现的文字是参考产品包装自身真实存在的印刷文字。

不要预设“多巴胺、自然、商业、户外”等固定分类。每个任务都必须先读取本次六参考矩阵，动态归纳它们真正共同的色彩、材质、光线、空间、人物关系和产品位置；若参考之间存在冲突，以用户主题、产品参考图和多数参考的共同特征为准，形成一套可执行的临时视觉规则，并在七页中保持一致。

产品可以靠近前景形成清晰视觉锚点，但必须真正落在桌面、木桩、岩石、长凳或地面上；人宠互动仍是故事主体。曝光通透、毛发细节真实、肤色自然、广告摄影级清晰度和景深。

构图语言：竖版 3:4，单一完整摄影场景，不做拼贴。使用前中后景、视线关系和轻微不对称平衡；人物、宠物、产品三者关系自然。产品包装正面尽量朝向镜头且完整可见，不遮挡宠物脸和人的关键动作。

产品身份锁定：参考图中的包装形状、长宽比例、主色、Logo、品名、标签布局、封口/瓶盖和合理尺寸必须保持一致；禁止改字、换色、重画 Logo、凭空增加包装或让产品悬浮。若文字无法可靠复现，宁可减少包装小字，也不能伪造。

整套连续性：宠物品种与外观、人物身份、空间气质、产品包装和动态归纳出的视觉规则保持一致；但每页必须更换景别、机位或动作，不能把同一构图复制七次。

明确禁止：任何后加标题或说明文字、便签贴纸、信息卡、拼贴、纯白棚拍、产品悬浮、廉价霓虹色、塑料 3D 渲染、卡通宠物、错误肢体、对称海报模板、错误 Logo 和错误包装比例。画面中不得出现小红书 Logo、用户 ID 或水印。
"""


GLUMOO_PAGE_DIRECTIONS = (
    "封面页：人物与宠物亲密互动的环境中景，产品在稳固前景台面形成清晰品牌锚点；完整摄影，不叠加任何标题。",
    "第 2 页·日常观察：捕捉梳毛、抚摸、玩耍或进食等自然动作，产品在场景中合理可见；使用侧面或斜侧机位。",
    "第 3 页·方法建议：低机位跟拍室内活动、散步或户外陪伴，让人物和宠物视线产生关系，保留环境纵深。",
    "第 4 页·产品角色：人物正在取用、添加或摆放产品，宠物在旁自然回应；产品正面清楚但不变成孤立静物。",
    "第 5 页·细节场景：近景表现手、宠物毛发/爪子、喂养道具与产品的真实关系，使用浅景深但包装仍可辨认。",
    "第 6 页·生活扩展：把同一人物、宠物和产品带到厨房、窗边、公园或露营场景，用更宽的环境镜头扩展故事。",
    "总结页：人物与一只或多只宠物的全家福/群像，产品系列稳定陈列在前景；画面有庆祝感或安静完成感，不叠加文字。",
)


# Distilled from a 117-image Pinterest scan plus the user's Railway campaign
# history. These are composition briefs, not copied images or copyrighted assets.
GLUMOO_REFERENCE_ARCHETYPES = (
        "钴蓝墙面 + 番茄红几何门洞；人物蹲坐拥抱犬只，圆罐产品落在红色矮台前景。",
        "橙黄宠物帐篷 + 蓝粉抽象墙；主人用量勺准备食物，宠物在中景期待，产品正面朝镜头。",
        "蓝色沙发 + 红黄地毯 + 条纹织物；主人梳毛，产品位于低矮蓝色边桌，形成三角构图。",
        "粉色墙面 + 蓝色猫爬架；猫狗并排看向画外，产品系列沿前景石材台面整齐陈列。",
        "彩色餐厨场景；主人弯身照顾宠物，黄色食盆与蓝色包装形成冷暖对比，动作自然。",
        "红色画框式背景；主人从后方拥抱两只宠物，两款产品在蓝色圆台上形成群像锚点。",
        "蓝橙色块背景 + 柔软地毯；犬只向镜头跑近，产品稳定落在侧前景，使用轻微运动凝固。",
        "高饱和客厅全家福；一猫一犬居中，产品系列在前景等高排布，毛绒玩具只做少量点缀。",
        "大窗边侧逆光；主人读书或整理植物，猫在窗台，产品落在不同高度的木凳前景。",
        "温暖木地板客厅；主人给犬只梳毛，散落少量毛发保留真实感，产品在背景凳上清晰可见。",
        "晨光厨房；主人打开低柜取用产品，宠物从画面下方靠近，利用柜门形成天然画框。",
        "城市公园长椅；主人抚摸犬只，牵引绳形成引导线，产品放在长椅一侧且比例合理。",
        "山湖露营餐桌；主人准备宠物餐，犬只在身侧，产品与杯具落在木桌上，远山形成纵深。",
        "岩石观景点；猫或犬佩戴户外胸背，产品放在稳固岩面，背景山湖轻微虚化。",
        "帐篷入口第一视角；犬只侧脸迎着日光，产品落在蓝色户外箱上，前景有人腿增强在场感。",
        "斑驳日光的安静室内；猫在猫爬架上，产品分别位于原木矮凳，深阴影与暖高光并存。",
)


# Twelve reusable six-reference sets. They deliberately have no style labels.
# The model must infer the temporary visual language from the six observations.
GLUMOO_REFERENCE_MATRICES = (
    (0, 1, 2, 3, 4, 5),
    (1, 3, 4, 5, 6, 7),
    (0, 2, 3, 4, 6, 7),
    (8, 9, 10, 11, 12, 13),
    (9, 10, 11, 12, 14, 15),
    (8, 10, 12, 13, 14, 15),
    (0, 1, 8, 9, 10, 15),
    (2, 4, 8, 9, 11, 15),
    (3, 5, 8, 10, 12, 15),
    (1, 6, 9, 11, 12, 14),
    (0, 7, 8, 10, 13, 15),
    (4, 5, 9, 11, 12, 14),
)


def get_glumoo_reference_calibration(topic: str, count: int = 6) -> str:
    """Return a deterministic six-reference preflight matrix for one suite."""
    digest = hashlib.sha256((topic or "glumoo-default").encode("utf-8")).digest()
    matrix_index = int.from_bytes(digest[:2], "big") % len(GLUMOO_REFERENCE_MATRICES)
    matrix = GLUMOO_REFERENCE_MATRICES[matrix_index][:count]
    selected = [GLUMOO_REFERENCE_ARCHETYPES[index] for index in matrix]
    rows = "\n".join(f"参考锚点 {index + 1}：{brief}" for index, brief in enumerate(selected))
    return (
        f"本次使用无标签参考矩阵 {matrix_index + 1}/{len(GLUMOO_REFERENCE_MATRICES)}。以下 6 个锚点来自 100+ 张 "
        f"Pinterest 同类图与 Railway 历史成片的归纳，只学习构图规律，不复制具体作品：\n{rows}\n"
        "不要给矩阵套用预设风格名。先结合用户主题和产品参考图，动态归纳六张共同的色彩、材质、光线、空间、"
        "人物关系、产品位置和景深；冲突特征不进入最终规则。第一张图作为最高风险证明图，"
        "产品身份和整体视觉通过后，其余页面沿用同一人物/宠物/产品和美术路线。"
    )


def get_style_instruction(style_id: str) -> str:
    """Backward-compatible generic style lookup."""
    if style_id == "glumoo":
        return GLUMOO_VISUAL_BASE.strip()
    return STYLE_PROFILES.get(style_id, STYLE_PROFILES["general"]).strip()


def get_outline_style_instruction(style_id: str, topic: str = "") -> str:
    if style_id == "glumoo":
        return (
            f"{GLUMOO_OUTLINE_INSTRUCTION.strip()}\n\n"
            f"【制作前六参考校准】\n{get_glumoo_reference_calibration(topic)}"
        )
    return get_style_instruction(style_id)


def get_content_style_instruction(style_id: str) -> str:
    if style_id == "glumoo":
        return GLUMOO_CONTENT_INSTRUCTION.strip()
    return get_style_instruction(style_id)


def get_image_style_instruction(
    style_id: str,
    page_type: str = "content",
    page_index: int = 0,
    total_count: Optional[int] = None,
    topic: str = "",
) -> str:
    if style_id != "glumoo":
        return get_style_instruction(style_id)

    last_index = (total_count - 1) if total_count else 6
    if page_type == "cover" or page_index <= 0:
        direction = GLUMOO_PAGE_DIRECTIONS[0]
    elif page_type == "summary" or page_index >= last_index:
        direction = GLUMOO_PAGE_DIRECTIONS[-1]
    else:
        direction_index = min(max(page_index, 1), len(GLUMOO_PAGE_DIRECTIONS) - 2)
        direction = GLUMOO_PAGE_DIRECTIONS[direction_index]

    return (
        f"{GLUMOO_VISUAL_BASE.strip()}\n\n"
        f"【制作前六参考校准】\n{get_glumoo_reference_calibration(topic)}\n\n"
        f"【本页专属导演指令】\n{direction}\n\n"
        "生成前请内部检查：产品身份是否与参考图一致、人物与宠物互动是否自然、是否完全没有后加文字和信息卡、"
        "是否与上一页更换了镜头、是否像同一品牌摄影企划。只输出最终图片。"
    )
