"""Select references by visible features on numbered contact sheets."""
import base64
import hashlib
import io
import json
import os
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


def pick_references(topic, style):
    token = os.getenv("TOKENSFACTORY_API_KEY")
    if not token:
        raise ValueError("自动选图需要 TokensFactory 视觉服务，也可以手动上传参考图")
    files = list(library_files().items())
    if len(files) < 6:
        raise ValueError("参考库可用图片不足六张")
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
            picks[key] = {"id":key, "url":"/api/studio/references/"+key,"reason":reason[:240]}
    return list(picks.values())[:6]
