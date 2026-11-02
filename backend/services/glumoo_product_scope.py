"""Product scope for a Glumoo job, derived from the chosen asset identities."""
import re
from pathlib import Path

OFFICIAL_PRODUCTS = {
    "glumoo_official_01_multivitamin_box.png": "多维力盒装",
    "glumoo_official_02_jump_bag.png": "跃力袋装",
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
        for sentence in re.split(r"[。；;\n]", text):
            if forbidden.search(sentence) and not re.search(r"(?:禁止|不得|不能|不使用|不出现|排除|无|没有|无需)", sentence):
                return f"第 {page.get('index', 0) + 1} 页提到未选择的袋装、盒装或条包；请修改或重新生成大纲。"
    return None
