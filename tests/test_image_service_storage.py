"""Storage safety tests for image generation batches."""

from backend.services.image import ImageService


def make_service(tmp_path):
    service = ImageService.__new__(ImageService)
    service.history_root_dir = str(tmp_path)
    service.current_task_dir = None
    service.provider_config = {"high_concurrency": True}
    service.max_concurrent = 5
    service.heartbeat_interval = 1
    service._task_states = {}
    service._active_task_ids = set()
    service.orphan_grace_seconds = 0
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


def test_storage_cleanup_preserves_indexed_and_active_tasks(tmp_path, monkeypatch):
    service = make_service(tmp_path)
    service._active_task_ids.add("task_active")

    (tmp_path / "task_indexed").mkdir()
    (tmp_path / "task_active").mkdir()
    (tmp_path / "task_orphan").mkdir()
    (tmp_path / "task_orphan" / "0.png").write_bytes(b"orphan")
    (tmp_path / "index.json").write_text(
        '{"records":[{"task_id":"task_indexed"}]}',
        encoding="utf-8",
    )

    monkeypatch.setattr(
        service,
        "_get_free_storage_bytes",
        lambda: 0 if (tmp_path / "task_orphan").exists() else 1024,
    )

    freed = service._cleanup_orphan_task_dirs(required_free_bytes=1024)

    assert freed > 0
    assert (tmp_path / "task_indexed").exists()
    assert (tmp_path / "task_active").exists()
    assert not (tmp_path / "task_orphan").exists()


def test_storage_cleanup_does_not_delete_tasks_when_index_is_invalid(tmp_path):
    service = make_service(tmp_path)
    task_dir = tmp_path / "task_unknown"
    task_dir.mkdir()
    (tmp_path / "index.json").write_text("not-json", encoding="utf-8")

    freed = service._cleanup_orphan_task_dirs(required_free_bytes=10**30)

    assert freed == 0
    assert task_dir.exists()
