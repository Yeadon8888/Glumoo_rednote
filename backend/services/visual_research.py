"""Select references by visible features on numbered contact sheets."""
import base64
import hashlib
import io
import json
import os
import re
from functools import lru_cache
from pathlib import Path
from PIL import Image, ImageDraw, ImageOps
import requests
from backend.services.glumoo_reference_library import GlumooReferenceLibrary
from backend.style_profiles import get_glumoo_style_instruction


def library_files():
    library = GlumooReferenceLibrary()
    return {hashlib.sha256(str(p.relative_to(library.history_root)).encode()).hexdigest(): p
            for p in library.library_candidates()}


def reference_bytes(ids):
    from backend.utils.image_compressor import compress_image
    files = library_files()
    if len(ids) != 6 or any(not isinstance(i,str) or i not in files for i in ids) or len(set(ids)) != 6:
        return []
    return [compress_image(files[i].read_bytes(), max_size_kb=450) for i in ids]


@lru_cache(maxsize=1)
def feature_index():
    path = Path(__file__).resolve().parents[1] / "prompts" / "glumoo_reference_features.json"
    return json.loads(path.read_text())


def indexed_picks(files, topic, style):
    number = int(style.split("_")[1]) if style != "glumoo" else None
    query = re.sub(r"\s+", "", topic.casefold().replace("犬", "狗"))
    terms = {query[i:i+2] for i in range(len(query)-1)}
    terms.update(word for word in ("猫", "狗", "罐", "碗", "光", "窗") if word in query)
    candidates = []
    for key, _ in files:
        entry = feature_index().get(key)
        if not entry or number is not None and number not in entry["styles"]:
            continue
        description = entry["reason"].replace("犬", "狗")
        score = sum(len(term) for term in terms if term in description)
        tie = hashlib.sha256((query + style + key).encode()).digest()
        candidates.append((score, tie, key, entry))
    groups = set()
    result = []
    for _, _, key, entry in sorted(candidates, reverse=True):
        if entry["group"] in groups:
            continue
        groups.add(entry["group"])
        result.append({"id": key, "url": "/api/studio/references/"+key,
                       "reason": entry["reason"], "basis": "审核库逐图特征"})
        if len(result) == 6:
            break
    return result


def pick_references(topic, style):
    files = list(library_files().items())
    picks = indexed_picks(files, topic, style)
    token = os.getenv("TOKENSFACTORY_API_KEY")
    if len(picks) == 6 or not files or not token:
        return picks
    try:
        live = vision_picks(files, topic, style, token)
    except (requests.RequestException, ValueError, TypeError, KeyError, IndexError):
        return picks
    return list({p["id"]:p for p in live + picks}.values())[:6]


def vision_picks(files, topic, style, token):
    brief = get_glumoo_style_instruction(style)
    content = [{"type": "text", "text": (
        "为品牌摄影选择六张主参考。看每幅照片的编号，按主题和风格选镜头、构图、光线或动作有根据且互补的照片。"
        "返回 JSON 数组，每项含 index（图片编号）和 reason（中文描述一个可见、可借鉴的特征）。"
        "找不到足够合适的图就少选。主题与风格如下：" + json.dumps([topic, brief], ensure_ascii=False))}]
    for offset in range(0, len(files), 24):
        board = Image.new("RGB", (6*180,4*216), "white")
        draw = ImageDraw.Draw(board)
        for i, (_, path) in enumerate(files[offset:offset+24]):
            with Image.open(path) as src:
                tile = ImageOps.contain(src.convert("RGB"), (176,189))
            x, y = i%6*180, i//6*216
            board.paste(tile,(x,y))
            draw.text((x+4,y+190), str(offset+i+1),fill="black",stroke_width=0)
        out = io.BytesIO()
        board.save(out, "JPEG", quality=85)
        content.append({"type":"image_url","image_url":{"url":"data:image/jpeg;base64,"+
                        base64.b64encode(out.getvalue()).decode()}})
    res = requests.post("https://tokensfactory.cc/v1/chat/completions",
                        headers={"Authorization":"Bearer "+token, "User-Agent":"curl/8.7.1"},
                        json={"model":"gemini-3.8-flash","temperature":0.2,"max_tokens":4096,
                              "messages":[{"role":"user","content":content}]},timeout=(6,85))
    res.raise_for_status()
    raw = res.json()["choices"][0]["message"]["content"]
    rows = json.loads(raw[raw.index("["):raw.rindex("]")+1])
    picks = {}
    for row in rows:
        index = row.get("index")
        reason = row.get("reason")
        if type(index) == int and 1<=index<=len(files) and isinstance(reason,str) and reason.strip():
            key = files[index-1][0]
            picks[key] = {"id":key, "url":"/api/studio/references/"+key,"reason":reason[:240],"basis":"Gemini 当次看图"}
    return list(picks.values())[:6]
