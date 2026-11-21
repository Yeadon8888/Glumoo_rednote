"""Brand studio settings and authenticated editorial data APIs."""
import io
import json
import os
import re
from pathlib import Path
import requests
from flask import Blueprint, Response, jsonify, request, send_file
from backend.config import Config
from backend.services.history import get_history_service
from backend.services.studio import database, review_record, save_settings, setting
from backend.services.tikhub import import_note, research

studio = Blueprint("studio", __name__, url_prefix="/studio")


def cpa_models():
    provider = Config.get_image_provider_config("cpa_gpt_image")
    base = provider["base_url"].rstrip("/").removesuffix("/v1")
    r = requests.get(base + "/v1/models", headers={"Authorization": "Bearer " + provider["api_key"]},
                     timeout=(5,15))
    r.raise_for_status()
    return [m["id"] for m in r.json()["data"] if re.fullmatch(r"gpt-image-[\w.-]+", m.get("id", ""))]


@studio.get("/models")
def models():
    try:
        return jsonify(models=cpa_models())
    except (ValueError, KeyError, requests.RequestException):
        return jsonify(error="无法读取 CPA 模型目录，请检查图片服务连接"), 502


@studio.route("/settings", methods=["GET", "PUT"])
def settings():
    config = Config.load_image_providers_config().get("providers", {}).get("cpa_gpt_image", {})
    if request.method == "PUT":
        data = request.get_json()
        values = {}
        if "models" in data:
            order = data["models"]
            if not isinstance(order, list) or not 1 <= len(order) <= 8 or not all(isinstance(x,str) for x in order):
                return jsonify(error="请选择 1 至 8 个图片模型"), 400
            try:
                catalog = cpa_models()
            except (ValueError, KeyError, requests.RequestException):
                return jsonify(error="无法向 CPA 核对模型，本次配置未保存"), 502
            if len(set(order)) != len(order) or set(order)-set(catalog):
                return jsonify(error="模型须在 CPA 目录中且不能重复"), 400
            values["cpa_models"] = order
        if "tikhub_key" in data:
            key = data["tikhub_key"]
            if not isinstance(key,str) or len(key)>1024:
                return jsonify(error="密钥格式无效"), 400
            values["tikhub_key"] = key.strip()
        save_settings(values)
    return jsonify(tikhub_configured=bool(setting("tikhub_key") or os.getenv("TIKHUB_API_KEY")),
                   models=setting("cpa_models", config.get("model_order", [])))


@studio.post("/research/note")
def read_note():
    try:
        return jsonify(note=import_note((request.get_json() or {}).get("url")))
    except ValueError as exc:
        return jsonify(error=str(exc)[:200]), 400
    except requests.RequestException:
        return jsonify(error="TikHub 暂时无法读取这篇笔记，可重试或填写参考摘录"), 502


@studio.post("/research")
def search():
    topic = (request.get_json().get("topic") or "").strip()
    if not 1 <= len(topic) <= 180:
        return jsonify(error="请输入 1 至 180 字的调研词"), 400
    try:
        return jsonify(research(topic))
    except ValueError as exc:
        return jsonify(error=str(exc)[:160]), 400
    except requests.RequestException as exc:
        code = exc.response.status_code if exc.response is not None else "超时或无法连接"
        return jsonify(error=f"TikHub 请求失败（{code}）"), 502


@studio.route("/reviews/<uuid:record_id>", methods=["GET", "PUT"])
def review(record_id):
    key = str(record_id)
    record = get_history_service().get_record(key, sync_images=False)
    if not record:
        return jsonify(error="找不到作品"), 404
    if request.method == "GET":
        with database() as db:
            row = db.execute("SELECT data FROM reviews WHERE record_id=? ORDER BY reviewed_at DESC LIMIT 1",
                             (key,)).fetchone()
        return jsonify(review=json.loads(row[0]) if row else None)
    data = request.get_json()
    reason = data.get("reason")
    score = data.get("score")
    rating = data.get("rating")
    if "score" in data:
        if type(score) is not int or not 1 <= score <= 5:
            return jsonify(error="请选择 1 至 5 分"), 400
        rating = "good" if score >= 4 else "bad" if score <= 2 else "neutral"
    elif rating not in ("good", "bad"):
        return jsonify(error="请选择评分"), 400
    if not isinstance(reason, str) or not 1 <= len(reason.strip()) <= 2000:
        return jsonify(error="请填写 1 至 2000 字的点评"), 400
    try:
        return jsonify(review=review_record(record, rating, reason.strip(), data.get("revision"), score))
    except ValueError as exc:
        return jsonify(error=str(exc)), 409


@studio.get("/reviews.jsonl")
def export():
    history = request.args.get("history") == "1"
    def lines():
        with database() as db:
            query = ("SELECT data FROM review_events ORDER BY reviewed_at" if history else
                     "SELECT data FROM reviews ORDER BY record_id,version")
            for row in db.execute(query):
                yield row[0] + "\n"
    return Response(lines(), mimetype="application/x-ndjson",
                    headers={"Content-Disposition": 'attachment; filename="glumoo-reviews.jsonl"'})


@studio.get("/samples/<sha>")
def sample(sha):
    if not re.fullmatch("[0-9a-f]{64}", sha):
        return jsonify(error="无效样本"), 404
    with database() as db:
        row = db.execute("SELECT image FROM samples WHERE sha=?", (sha,)).fetchone()
    if not row:
        return jsonify(error="找不到样本"), 404
    from PIL import Image
    data = io.BytesIO(row[0])
    mime = Image.MIME.get(Image.open(data).format, "application/octet-stream")
    data.seek(0)
    return send_file(data, mimetype=mime, etag=sha)


@studio.post("/references")
def references():
    from backend.style_profiles import is_glumoo_style
    from backend.services.visual_research import pick_references
    data = request.get_json()
    topic = (data.get("topic") or "").strip()
    style = data.get("style")
    if not topic or len(topic)>1000 or not is_glumoo_style(style):
        return jsonify(error="请先选择 Glumoo 风格并输入主题"), 400
    try:
        return jsonify(items=pick_references(topic, style))
    except (ValueError, KeyError, IndexError, requests.RequestException, OSError):
        return jsonify(error="参考库视觉匹配未完成，可重试或上传本次参考图"), 502


@studio.get("/references/<key>")
def reference_image(key):
    from backend.services.visual_research import library_files
    path = library_files().get(key)
    if not path:
        return jsonify(error="找不到这张参考图"), 404
    if request.args.get("preview") == "1":
        from PIL import Image, ImageOps
        out = io.BytesIO()
        with Image.open(path) as im:
            ImageOps.contain(im.convert("RGB"), (240,240)).save(out, "JPEG", quality=80)
        out.seek(0)
        return send_file(out, mimetype="image/jpeg", max_age=3600)
    from backend.utils.image_compressor import compress_image
    data = compress_image(path.read_bytes(), max_size_kb=450)
    return send_file(io.BytesIO(data), mimetype="image/jpeg" if data.startswith(b"\xff\xd8") else None,
                     download_name=path.name)


@studio.get("/native/<task>/<name>")
def native_image(task, name):
    if not re.fullmatch(r"[\w-]+", task) or not re.fullmatch(r"\d+\.(png|jpeg|webp)", name):
        return jsonify(error="原图不存在"), 404
    path = Path(get_history_service().history_dir) / task / "native" / name
    if not path.is_file():
        return jsonify(error="原图不存在"), 404
    return send_file(path)


@studio.get("/reference-library")
def reference_list():
    from backend.services.visual_research import library_files
    return jsonify(items=[{"id": key, "url": f"/api/studio/references/{key}"}
                          for key in library_files()])
