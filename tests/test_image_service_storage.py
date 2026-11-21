"""Storage safety tests for image generation batches."""
import errno
import pytest

from backend.services.image import ImageService


def make_service(tmp_path):
    service = ImageService.__new__(ImageService)
    service.history_root_dir = str(tmp_path)
    service.current_task_dir = None
    service.provider_config = {"high_concurrency": True}
    service.max_concurrent = 5
    service.heartbeat_interval = 1
    service._task_states = {}
    return service


def test_disk_full_on_cover_stops_paid_requests_for_remaining_pages(tmp_path, monkeypatch):
    service = make_service(tmp_path)
    calls = []
    pages = [
        {"index": 0, "type": "cover", "content": "cover"},
        {"index": 1, "type": "content", "content": "page 1"},
        {"index": 2, "type": "content", "content": "page 2"},
    ]

    monkeypatch.setattr(service, "_ensure_storage_available", lambda task_id: None)

    def fake_generate(page, *args, **kwargs):
        calls.append(page["index"])
        return (
            page["index"],
            False,
            None,
            "[Errno 28] No space left on device",
        )

    monkeypatch.setattr(service, "_generate_single_image", fake_generate)

    events = list(service.generate_images(pages, task_id="task_storage_full"))

    assert calls == [0]
    errors = [event["data"] for event in events if event["event"] == "error"]
    assert [error["index"] for error in errors] == [0, 1, 2]
    assert all("存储空间" in error["message"] for error in errors[1:])


@pytest.mark.parametrize("index", ['{"records":[]}', 'invalid-json'])
def test_low_disk_preserves_unindexed_images(tmp_path, monkeypatch, index):
    service = make_service(tmp_path)
    folder = tmp_path / "task_unindexed"
    folder.mkdir()
    original = folder / "0.png"
    original.write_bytes(b"original")
    (tmp_path / "index.json").write_text(index)
    monkeypatch.setattr(service, "_get_free_storage_bytes", lambda: 0)
    with pytest.raises(OSError) as exc:
        service._ensure_storage_available("task_next")
    assert exc.value.errno == errno.ENOSPC
    assert original.read_bytes() == b"original"


def test_cover_read_uses_its_own_task_directory(tmp_path, monkeypatch):
    service = make_service(tmp_path)
    pages = [{"index": 0, "type": "cover", "content": "cover"}]

    monkeypatch.setattr(service, "_ensure_storage_available", lambda task_id: None)
    monkeypatch.setattr(
        "backend.services.image.compress_image",
        lambda image_data, max_size_kb: image_data,
    )

    def fake_generate(page, task_id, *args, **kwargs):
        task_dir = tmp_path / task_id
        task_dir.mkdir(exist_ok=True)
        (task_dir / "0.png").write_bytes(b"cover-image")

        # Simulate another request starting while this cover request is in flight.
        service.current_task_dir = str(tmp_path / "task_other")
        (tmp_path / "task_other").mkdir(exist_ok=True)
        return page["index"], True, "0.png", None

    monkeypatch.setattr(service, "_generate_single_image", fake_generate)

    events = list(service.generate_images(pages, task_id="task_main"))

    assert any(event["event"] == "complete" for event in events)
    finish = next(event["data"] for event in events if event["event"] == "finish")
    assert finish["success"] is True


def test_glumoo_cover_retry_uses_clean_photo_and_edited_cover_after_restart(tmp_path):
    from PIL import Image
    from backend.services.glumoo_postprocess import render_cover

    service = make_service(tmp_path)
    folder = tmp_path / "task_editorial"
    folder.mkdir()
    source = folder / "_cover_source.png"
    Image.new("RGB", (810, 1080), "#e7e3df").save(source)
    page = {"index": 6, "type": "cover", "content": "[封面]\n封面主标题：出门前，看它怎么起步\n封面副标题：Glumoo 跃力"}
    result = service.retry_single_image("task_editorial", page, user_topic="内部草稿")
    assert result["success"]
    expected = tmp_path / "expected.png"
    render_cover(source, expected, "出门前，看它怎么起步", "Glumoo 跃力")
    with Image.open(folder / "6.png") as actual, Image.open(expected) as wanted:
        assert actual.tobytes() == wanted.tobytes()
