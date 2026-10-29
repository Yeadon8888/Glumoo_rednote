"""Stable six-image selection for the Glumoo dynamic reference workflow."""

from __future__ import annotations

import hashlib
import os
import random
from pathlib import Path
from typing import List

from backend.utils.image_compressor import compress_image

IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}


class GlumooReferenceLibrary:
    def __init__(self, history_root: str | Path | None = None):
        self.history_root = Path(history_root or os.getenv("HISTORY_DIR") or Path(__file__).resolve().parents[2] / "history")
        self.library_dir = self.history_root / "reference_library"

    def _library_candidates(self) -> List[Path]:
        if not self.library_dir.is_dir():
            return []
        return sorted(
            path for path in self.library_dir.iterdir()
            if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES
        )

    def _history_candidates(self) -> List[Path]:
        """Fallback for an unseeded installation; only use completed page images."""
        candidates = []
        for task_dir in sorted(self.history_root.glob("task_*")):
            if not task_dir.is_dir():
                continue
            for path in sorted(task_dir.iterdir()):
                if (
                    path.is_file()
                    and path.suffix.lower() in IMAGE_SUFFIXES
                    and path.stem.isdigit()
                    and path.stem != "0"
                ):
                    candidates.append(path)
        return candidates

    def select_paths(self, topic: str, style_id: str, count: int = 6) -> List[Path]:
        candidates = self._library_candidates()
        if len(candidates) < count:
            candidates = self._history_candidates()
        if len(candidates) < count:
            return []

        seed = int.from_bytes(
            hashlib.sha256(f"{style_id}\0{topic.strip()}".encode("utf-8")).digest()[:8],
            "big",
        )
        return random.Random(seed).sample(candidates, count)

    def select_images(self, topic: str, style_id: str, count: int = 6) -> List[bytes]:
        return [
            compress_image(path.read_bytes(), max_size_kb=260)
            for path in self.select_paths(topic, style_id, count)
        ]


def select_glumoo_references(topic: str, style_id: str, count: int = 6) -> List[bytes]:
    return GlumooReferenceLibrary().select_images(topic, style_id, count)
