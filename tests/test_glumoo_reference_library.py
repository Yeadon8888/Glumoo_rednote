from pathlib import Path

from PIL import Image

from backend.services.glumoo_reference_library import GlumooReferenceLibrary


def _seed_images(directory: Path, count: int = 10):
    directory.mkdir(parents=True)
    for index in range(count):
        Image.new("RGB", (40, 40), (index, index, index)).save(directory / f"ref_{index:02d}.png")


def test_reference_selection_is_stable_for_same_topic_and_style(tmp_path: Path):
    _seed_images(tmp_path / "reference_library")
    library = GlumooReferenceLibrary(tmp_path)

    first = library.select_paths("宠物日常营养", "glumoo_12")
    second = library.select_paths("宠物日常营养", "glumoo_12")

    assert len(first) == 6
    assert first == second
    assert len(set(first)) == 6


def test_reference_selection_falls_back_to_history_pages(tmp_path: Path):
    task_dir = tmp_path / "task_example"
    task_dir.mkdir()
    for index in range(7):
        Image.new("RGB", (40, 40), (index, 0, 0)).save(task_dir / f"{index}.png")

    selected = GlumooReferenceLibrary(tmp_path).select_paths("主题", "glumoo_1")

    assert len(selected) == 6
    assert all(path.name != "0.png" for path in selected)
