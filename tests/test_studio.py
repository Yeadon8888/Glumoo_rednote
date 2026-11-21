import io
import json
from datetime import datetime, timezone

import pytest
from PIL import Image

from backend.services.history import get_history_service
from backend.services.studio import review_revision, save_settings
from backend.services.tikhub import research
from tests.history_and_image_service_test import make_history_service


@pytest.fixture
def history(tmp_path, monkeypatch):
    store = make_history_service(tmp_path)
    monkeypatch.setattr("backend.services.history._service_instance", store)
    return store


def png(color):
    buf = io.BytesIO()
    Image.new("RGB", (4, 5), color).save(buf, "PNG")
    return buf.getvalue()


def test_review_versions_and_immutable_export(client, history, tmp_path):
    key = history.create_record("六罐", {"pages": [{"index": 0, "content":"备餐"}]})
    folder = tmp_path / "task_1"
    folder.mkdir()
    path = folder / "0.png"
    first = png("red")
    path.write_bytes(first)
    history.merge_generated_image(key, folder.name, 0, path.name)
    url = "/api/studio/reviews/" + key
    revision = review_revision(history.get_record(key, sync_images=False))
    data = {"rating":"good", "reason":"罐身正面清楚", "revision": revision}
    assert client.put(url, json={**data, "reason":"  "}).status_code == 400
    item = client.put(url, json=data).get_json()["review"]
    assert client.put(url, json={**data,"reason":"包装清楚"}).status_code == 200
    path.write_bytes(png("blue"))
    assert client.put(url, json=data).status_code == 409
    data.update(rating="bad", reason="标签模糊", revision=review_revision(history.get_record(key, sync_images=False)))
    assert client.put(url, json=data).status_code == 200
    rows = [json.loads(line) for line in client.get("/api/studio/reviews.jsonl").data.splitlines()]
    assert {r["reason"] for r in rows} == {"包装清楚", "标签模糊"}
    assert client.get(item["images"][0]["image_url"]).data == first


def test_cpa_order_and_private_key(client, history, monkeypatch):
    monkeypatch.setattr("backend.routes.studio_routes.cpa_models",lambda: ["gpt-image-2","gpt-image-2.6-flare"])
    url = "/api/studio/settings"
    assert client.put(url,json={"models":["invented"]}).status_code == 400
    r = client.put(url,json={"models":["gpt-image-2.6-flare","gpt-image-2"],"tikhub_key":"secret-fixture"})
    assert r.status_code == 200 and "secret-fixture" not in r.text
    assert client.get(url).get_json()["tikhub_configured"]


def test_research_rank_and_no_invented_counts(history, monkeypatch):
    timestamp = int(datetime.now(timezone.utc).timestamp()) - 3600
    class Reply:
        def raise_for_status(self): pass
        def json(self):
            return {"data":{"data":{"items":[{"note":{"id":f"test-{i}", "title":str(i),
                "timestamp":timestamp, "liked_count":i, "collected_count":i if i<10 else None}}
                for i in range(11)]}}}
    save_settings({"tikhub_key":"test"})
    monkeypatch.setattr("backend.services.tikhub.requests.get",lambda *args,**kwargs: Reply())
    result = research("宠物备餐")
    assert result["valid_count"] == 10
    assert result["selected"] == ["test-9","test-8"]
    assert result["basis"] == "细分样本前 20%"


def test_model_order_is_used_and_native_output_survives(tmp_path, history):
    from backend.services.image import ImageService
    from backend.services.image_rate_limiter import ImageRateLimiter
    from backend.generators.image_api import ImageModelUnavailable
    image = png("green")
    class Generator:
        def generate_image(self, model, generation_trace, **kwargs):
            if model == "first":
                raise ImageModelUnavailable("unavailable")
            generation_trace.update(source=image, format="png", native_size=[4,5])
            return image
    svc = ImageService.__new__(ImageService)
    svc.generator = Generator()
    svc.provider_config = {"type":"image_api", "model_order":["first","second"]}
    svc.use_short_prompt = False
    svc.prompt_template = "{page_content}"
    svc.rate_limiter = ImageRateLimiter(max_concurrent=1, interval_seconds=0)
    svc.history_root_dir = str(tmp_path)
    svc.current_task_dir = str(tmp_path/"task_fixture")
    svc.history_service = history
    result = svc._generate_single_image({"index":0,"type":"content","content":"test"}, "task_fixture")
    assert result[1], result
    receipt = json.loads((tmp_path/"task_fixture/0.model.json").read_text())
    assert receipt["attempted"] == ["first","second"] and receipt["model"] == "second"
    assert (tmp_path/"task_fixture/native/0.png").read_bytes() == image
