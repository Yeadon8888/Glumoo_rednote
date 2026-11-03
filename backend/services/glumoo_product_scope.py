"""Product scope for a Glumoo job, derived from the chosen asset identities."""
import re
from pathlib import Path

OFFICIAL_PRODUCTS = {
    "glumoo_official_01_multivitamin_box.png": "多维力盒装",
    "glumoo_official_02_jump_bag.png": "跃力袋装",
    "glumoo_official_02_jump_stick.png": "跃力独立条装",
    "glumoo_official_03_digest_bag.png": "畅清袋装",
    "glumoo_official_04_bonemax.png": "Glumoo PRO 强骨力圆罐",
    "glumoo_official_05_flexmax.png": "Glumoo PRO 灵动力圆罐",
    "glumoo_official_06_gutmax.png": "Glumoo PRO 舒肠力圆罐",
    "glumoo_official_07_urimax.png": "Glumoo PRO 净尿力圆罐",
    "glumoo_official_08_furmax.png": "Glumoo PRO 焕毛力圆罐",
    "glumoo_official_09_immumax.png": "Glumoo PRO 益免力圆罐",
}


def product_scope_instruction(names):
    labels = [OFFICIAL_PRODUCTS.get(Path(name).name, f"用户所选产品图{index}（以该图真实包装为准，不猜测型号）")
              for index, name in enumerate(names, 1)]
    result = ("【本次产品范围，优先级最高】只允许使用用户选中的产品母图所示的包装形态与产品身份：\n"
              + "\n".join(f"产品{index}：{label}" for index, label in enumerate(labels, 1))
              + "\n参考图中的包装不得作为产品来源；主题出现全家桶、全系列等词也不能扩大产品范围。"
                "不得捏造未选中的袋装、盒装、条装或其他产品；每页可使用所选产品的子集。")
    if labels and all("PRO" in label and "圆罐" in label for label in labels):
        result += "\n本次仅允许上述 Glumoo PRO 圆罐，禁止自立袋、袋装、盒装、条包及其他包装。"
    return result


def find_scope_conflict(names, pages):
    """Block explicit positive bag/box/stick instructions for known can-only sets."""
    if not names or not all(OFFICIAL_PRODUCTS.get(Path(name).name, "").endswith("圆罐") for name in names):
        return None
    forbidden = re.compile(r"自立袋|袋装|包装袋|外袋|盒装|条包|条装")
    for page in pages:
        text = page.get("content", "") if isinstance(page, dict) else ""
        # Scope negation to the relevant clause: an unrelated “无遮挡” must not
        # excuse “摆放盒装”, and “不要袋装” is not a request to add a bag.
        for clause in re.split(r"[。；;，,\n]", text):
            for match in forbidden.finditer(clause):
                before, after = clause[:match.start()], clause[match.end():]
                negative = re.search(
                    r"禁止|不得|不能|不要|不使用|不出现|不含|不包括|不添加|不增加|不摆放|"
                    r"不展示|不引入|不生成|不允许|不沿用|不继承|不复制|不采用|不借用|不带入|"
                    r"不是|而非|并非|排除|避免|未选|未提供|没有|无需", before
                ) or re.search(r"^\s*(?:为?零|为?0|(?:均|一律)?(?:禁止|不得|不)(?:出现|使用|添加|展示))", after)
                if negative:
                    continue
                # “无袋装” is negative; “无遮挡的袋装” is still a product request.
                if before.rstrip().endswith("无"):
                    continue
                excerpt = clause.strip()[:180]
                return f"第 {page.get('index', 0) + 1} 页产品范围冲突：{excerpt}。本次只选择了圆罐产品。"
    return None
