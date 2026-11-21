"""Inputs prepared in the creation center reach the very first outline request."""
import io
import json
from unittest.mock import Mock

import pytest

from backend.services import tikhub


LINK = "https://www.xiaohongshu.com/explore/697c0eee000000000a03c308"
NOTE = {"url": LINK, "title": "窗边的梳毛日常", "excerpt": "参考逆光下的毛发细节"}


@pytest.mark.parametrize("multipart", [False, True])
def test_first_outline_uses_and_records_prepared_references(client, monkeypatch, multipart):
    service = Mock()
    service.generate_outline.return_value = {"success": True, "pages": [], "outline": ""}
    monkeypatch.setattr("backend.routes.outline_routes.get_outline_service", lambda: service)
    monkeypatch.setattr("backend.services.studio.comparable_works", lambda *_: [])
    params = {"topic": "宠物梳毛", "style_id": "glumoo_2" if multipart else "general"}
    if multipart:
        response = client.post("/api/outline", data={**params, "note_references": json.dumps([NOTE]),
            "images": [(io.BytesIO(bytes([i])), f"{i}.png") for i in range(6)],
            "product_images": (io.BytesIO(b"product"), "can.png")})
    else:
        response = client.post("/api/outline", json={**params, "note_references": [NOTE]})
    assert response.status_code == 200
    args, kwargs = service.generate_outline.call_args
    assert args[3] == params["style_id"]
    assert kwargs["research_notes"] == [{"title": NOTE["title"], "excerpt": NOTE["excerpt"]}]
    assert response.json["context"]["note_references"] == [NOTE]


def test_import_short_link_before_choosing_topic(client, monkeypatch):
    monkeypatch.setattr(tikhub, "setting", lambda _: "test")
    reply = Mock()
    reply.json.return_value = {"code": 200, "data": {"data": [{"note_list": [{
        "title": NOTE["title"], "desc": NOTE["excerpt"]}]}]}}
    http = Mock(return_value=reply)
    monkeypatch.setattr(tikhub.requests, "get", http)
    link = "https://xhslink.com/a/demo"
    result = client.post("/api/studio/research/note", json={"url": f"复制分享 {link} 打开小红书"})
    assert result.json["note"] == {**NOTE, "url": link}
    assert http.call_args.kwargs["params"] == {"share_text": link}
    assert client.post("/api/studio/research/note", json={"url": "https://example.org/abc"}).status_code == 400
    assert http.call_count == 1


def test_outline_rejects_a_link_without_research_content(client):
    response = client.post("/api/outline", json={"topic": "draft", "note_references": [{"url": LINK}]})
    assert response.status_code == 400
