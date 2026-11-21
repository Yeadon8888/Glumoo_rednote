"""Retrieve dated Xiaohongshu research with auditable engagement metrics."""
import json
import math
import os
import re
import uuid
from datetime import datetime, timezone
import requests
from .studio import database, now, setting

ENDPOINT = "https://api.tikhub.io/api/v1/xiaohongshu/app_v2/search_notes"


def metric(value):
    try:
        return int(str(value).replace(",", ""))
    except (TypeError, ValueError):
        return None


def parse_notes(items, today):
    for item in items:
        if not isinstance(item, dict):
            continue
        note = item.get("note") or item.get("note_card") or {}
        if not isinstance(note, dict):
            continue
        key = str(note.get("id") or note.get("note_id") or item.get("id") or "")
        if not re.fullmatch(r"[a-zA-Z0-9_-]{4,80}", key):
            continue
        timestamp = metric(note.get("timestamp") or note.get("publish_time") or note.get("time"))
        if not timestamp:
            continue
        if timestamp > 10**12:
            timestamp //= 1000
        if not 0 < timestamp <= today.timestamp():
            continue
        date = datetime.fromtimestamp(timestamp, timezone.utc)
        if (today-date).days > 90:
            continue
        counts = note.get("interact_info") or note
        title = str(note.get("title") or note.get("display_title") or note.get("desc") or "")[:160]
        if title:
            yield dict(id=key, title=title, date=date.date().isoformat(),
                       url=f"https://www.xiaohongshu.com/explore/{key}",
                       likes=metric(counts.get("liked_count")), saves=metric(counts.get("collected_count")))


def research(topic):
    token = setting("tikhub_key") or os.getenv("TIKHUB_API_KEY")
    if not token:
        raise ValueError("请先在系统设置保存 TikHub API Key")
    candidates = {}
    today = datetime.now(timezone.utc)
    for sort in ("collect_descending", "time_descending"):
        response = requests.get(ENDPOINT, headers={"Authorization": f"Bearer {token}"},
                                params={"keyword": topic, "sort_type": sort, "page": 1}, timeout=(5,25))
        response.raise_for_status()
        body = response.json()
        if body.get("code", 200) != 200:
            raise ValueError("TikHub 返回业务错误，请检查密钥、余额和请求状态")
        payload = body.get("data") or {}
        if isinstance(payload, dict):
            payload = payload.get("data", payload)
        items = payload.get("items", payload.get("notes", [])) if isinstance(payload, dict) else []
        for row in parse_notes(items, today):
            candidates[row["id"]] = row
        if sum(r['likes'] is not None and r['saves'] is not None for r in candidates.values()) >= 10:
            break
    notes = sorted(candidates.values(), key=lambda n: (n["saves"] or 0, n["likes"] or 0), reverse=True)
    valid = [n for n in notes if n["likes"] is not None and n["saves"] is not None]
    selected = [n for n in valid if n["likes"] >= 1000 and n["saves"] >= 300]
    basis = "高互动样本" if selected else "细分样本前 20%"
    if len(valid) < 10:
        selected, basis = [], "有效样本不足，仅供查阅"
    elif not selected:
        selected = valid[:math.ceil(len(valid)*.2)]
    result = dict(id=uuid.uuid4().hex, topic=topic, fetched_at=now(), source="TikHub 小红书",
                  basis=basis, valid_count=len(valid), selected=[n["id"] for n in selected], notes=notes)
    with database() as db:
        db.execute("INSERT INTO research VALUES (?,?)", (result["id"], json.dumps(result, ensure_ascii=False)))
    return result
