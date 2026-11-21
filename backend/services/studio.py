"""Persistent editorial settings, research and versioned human feedback."""
import hashlib
import json
import os
import re
import shutil
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from backend.services.history import get_history_service


def now():
    return datetime.now(timezone.utc).isoformat()


@contextmanager
def database():
    root = Path(get_history_service().history_dir)
    path = root / "studio.sqlite3"
    db = sqlite3.connect(path, timeout=15)
    try:
        os.chmod(path, 0o600)
        db.row_factory = sqlite3.Row
        db.executescript("""
            CREATE TABLE IF NOT EXISTS settings (name TEXT PRIMARY KEY, value TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS research (id TEXT PRIMARY KEY, data TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS samples (sha TEXT PRIMARY KEY, image BLOB NOT NULL);
            CREATE TABLE IF NOT EXISTS reviews (
                record_id TEXT, version TEXT, reviewed_at TEXT, data TEXT,
                PRIMARY KEY(record_id,version)
            );
        """)
        if not db.execute("SELECT 1 FROM sqlite_master WHERE name='review_events'").fetchone():
            db.executescript("""
                BEGIN IMMEDIATE;
                CREATE TABLE IF NOT EXISTS review_events (
                    record_id TEXT, version TEXT, reviewed_at TEXT, data TEXT,
                    PRIMARY KEY(record_id, version, reviewed_at)
                );
                INSERT OR IGNORE INTO review_events SELECT * FROM reviews;
                CREATE TRIGGER IF NOT EXISTS save_review_event AFTER INSERT ON reviews
                BEGIN
                    INSERT INTO review_events VALUES (NEW.record_id, NEW.version, NEW.reviewed_at, NEW.data);
                END;
                COMMIT;
            """)
        with db:
            yield db
    finally:
        db.close()


def setting(name, default=None):
    with database() as db:
        row = db.execute("SELECT value FROM settings WHERE name=?", (name,)).fetchone()
    return json.loads(row[0]) if row else default


def save_settings(values):
    with database() as db:
        db.executemany("INSERT OR REPLACE INTO settings VALUES (?,?)",
                       [(k, json.dumps(v)) for k, v in values.items()])


def research_by_id(key):
    with database() as db:
        row = db.execute("SELECT data FROM research WHERE id=?", (key,)).fetchone()
    return json.loads(row[0]) if row else None


def review_revision(record):
    info = record.get("images") or {}
    task = info.get("task_id") or ""
    if not re.fullmatch(r"[\w-]+", task):
        return None
    root = Path(get_history_service().history_dir) / task
    state = [record.get("updated_at")]
    for name in info.get("generated") or []:
        if not name or Path(name).name != name:
            continue
        try:
            st = (root/name).stat()
            state.append((name, st.st_size, st.st_mtime_ns))
        except FileNotFoundError:
            state.append((name, None))
    return hashlib.sha256(json.dumps(state).encode()).hexdigest()


def review_record(record, rating, reason, revision, score=None):
    task = (record.get("images") or {}).get("task_id") or ""
    if not re.fullmatch(r"[\w-]+", task):
        raise ValueError("这条记录还没有成品图")
    root = Path(get_history_service().history_dir)
    task_dir = root / task
    if revision != review_revision(record):
        raise ValueError("作品已更新，请重新打开成品后点评")
    images = []
    with database() as db:
        db.execute("BEGIN IMMEDIATE")
        for index, name in enumerate(record["images"].get("generated") or []):
            if not name:
                continue
            if Path(name).name != name or Path(name).suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp"}:
                raise ValueError("图片记录无效")
            path = task_dir / name
            if not path.is_file():
                raise ValueError("成品已变更，请刷新后再点评")
            image = path.read_bytes()
            sha = hashlib.sha256(image).hexdigest()
            if not db.execute("SELECT 1 FROM samples WHERE sha=?", (sha,)).fetchone():
                if shutil.disk_usage(root).free < 96*1024**2 + 2*len(image):
                    raise ValueError("存储空间不足，未写入点评")
                db.execute("INSERT OR IGNORE INTO samples VALUES (?,?)", (sha, image))
            receipt = task_dir / f"{Path(name).stem}.model.json"
            images.append({"page": index+1, "file": name, "sha256": sha,
                           "image_url": f"/api/studio/samples/{sha}",
                           "generation": json.loads(receipt.read_text()) if receipt.is_file() else None})
        if not images:
            raise ValueError("这条记录还没有成品图")
        item = {"schema_version": 1, "record_id": record["id"], "title": record["title"],
                "task_id": task, "outline": record.get("outline"), "content": record.get("content"),
                "images": images}
        current = get_history_service().get_record(record["id"], sync_images=False)
        if not current or revision != review_revision(current):
            raise ValueError("保存期间作品已更新，请重新打开后点评")
        version = hashlib.sha256(json.dumps(item, sort_keys=True).encode()).hexdigest()
        prior = db.execute("SELECT data FROM reviews WHERE record_id=? AND version=?",
                           (record["id"], version)).fetchone()
        if prior:
            last = json.loads(prior[0])
            if (last.get("score"), last["rating"], last["reason"]) == (score, rating, reason):
                return last
        item.update(version=version, rating=rating, reason=reason, reviewed_at=now())
        if score is not None:
            item.update(score=score, score_max=5)
        db.execute("INSERT OR REPLACE INTO reviews VALUES (?,?,?,?)",
                   (record["id"], version, item["reviewed_at"], json.dumps(item, ensure_ascii=False)))
    return item


def comparable_works(topic, product_names):
    """Surface nearby published drafts from our own delivery history for the outline."""
    history = get_history_service()
    recent = history.list_records(page_size=100, status="completed")["records"]

    def phrases(value):
        value = re.sub(r"\s+", "", value.casefold())
        return {value[i:i+2] for i in range(len(value)-1)}

    query = phrases(topic)
    ranked = []
    for row in recent:
        title = row.get("title", "")
        score = len(query & phrases(title))
        record = history.get_record(row["id"], sync_images=False)
        if not record:
            continue
        outline = record.get("outline") or {}
        assets = (outline.get("context") or {}).get("products") or []
        score += len(set(product_names or []) & set(assets))
        if score:
            ranked.append((score, {"id": row["id"], "title": title, "date": row.get("created_at"),
                                   "excerpt": str(outline.get("raw") or "")[:450]}))
    return [r for _, r in sorted(ranked, key=lambda pair: pair[0], reverse=True)[:3]]
