"""Downloadable works and editorial feedback, streamed without a second copy on the volume."""
import io
import json
import re
import zipfile
import zlib
from pathlib import Path

from backend.services.studio import database, now


class ZipBuffer(io.BytesIO):
    """A drainable, non-seekable output for ZipFile's data descriptor mode."""
    consumed = 0

    def tell(self):
        return self.consumed + super().tell()

    def seek(self, *args):
        raise io.UnsupportedOperation("stream")

    def take(self):
        data = self.getvalue()
        self.consumed += len(data)
        super().seek(0)
        self.truncate()
        return data


def backup_chunks(history, part=1, parts=1):
    def included(key):
        return zlib.crc32(key.encode()) % parts == part - 1

    root = Path(history.history_dir)
    buffer = ZipBuffer()
    missing = []
    records = 0
    sources = set()
    started = now()
    with zipfile.ZipFile(buffer, "w", allowZip64=True) as archive:
        # Capture record JSON as read, including drafts and manually removed records.
        for path in sorted([*root.glob("*.json"), *(root / ".trash").glob("*.json")]):
            if path.is_symlink() or path.name == "index.json":
                continue
            raw = path.read_bytes()
            try:
                item = json.loads(raw)
                images = item.get("images") or {}
                task = images.get("task_id")
            except (ValueError, AttributeError):
                item, images, task = {}, {}, None
            if task and re.fullmatch(r"[\w-]+", task):
                sources.add(task)
            if not included(task or path.stem):
                continue
            archive.writestr("history/" + path.relative_to(root).as_posix(), raw, zipfile.ZIP_DEFLATED)
            yield buffer.take()
            if item.get("id") == path.stem:
                records += 1
                if task and re.fullmatch(r"[\w-]+", task):
                    for name in images.get("generated") or []:
                        if name and Path(name).name == name and not (root / task / name).is_file():
                            missing.append({"record_id": item["id"], "task": task, "file": name})

        # Include unindexed task images, native originals and generation receipts as well.
        for folder in sorted(root.iterdir()):
            if not included(folder.name) or folder.is_symlink() or not folder.is_dir():
                continue
            if folder.name not in sources and not folder.name.startswith("task_"):
                continue
            for path in sorted(folder.rglob("*")):
                if path.is_symlink() or not path.is_file():
                    continue
                if path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp"} and not path.name.endswith(".model.json"):
                    continue
                with path.open("rb") as source, archive.open("history/" + path.relative_to(root).as_posix(), "w", force_zip64=True) as target:
                    while chunk := source.read(256 * 1024):
                        target.write(chunk)
                        yield buffer.take()

        with database() as db:
            db.execute("BEGIN")
            with archive.open("training/reviews.jsonl", "w", force_zip64=True) as out:
                for record_id, data in db.execute("SELECT record_id,data FROM review_events ORDER BY reviewed_at"):
                    if not included(record_id):
                        continue
                    out.write((data + "\n").encode())
                    yield buffer.take()
            for (sha,) in db.execute("SELECT sha FROM samples"):
                if not included(sha):
                    continue
                data = db.execute("SELECT image FROM samples WHERE sha=?", (sha,)).fetchone()[0]
                archive.writestr("training/samples/" + sha, data)
                yield buffer.take()
        archive.writestr("manifest.json", json.dumps({
            "format_version": 1, "part": part, "parts": parts, "started_at": started, "finished_at": now(),
            "record_count_including_trash": records, "missing_images": missing,
            "sample_path": "training/samples/{sha256}",
        }, ensure_ascii=False), zipfile.ZIP_DEFLATED)
    yield buffer.take()
