"""
历史记录服务

负责管理绘本生成历史记录的存储、查询、更新和删除。
支持草稿、生成中、完成等多种状态流转。
"""

import os
import json
import uuid
import errno
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
from functools import wraps
from tempfile import NamedTemporaryFile
import shutil
from filelock import FileLock

from backend.services.history_image_merger import HistoryImageMerger

logger = logging.getLogger(__name__)


def history_transaction(fn):
    @wraps(fn)
    def locked(self, *args, **kwargs):
        with FileLock(os.path.join(self.history_dir, ".history.lock"), is_singleton=True):
            return fn(self, *args, **kwargs)
    return locked


def atomic_json(path, data):
    with NamedTemporaryFile("w", encoding="utf-8", dir=Path(path).parent, delete=False) as out:
        try:
            json.dump(data, out, ensure_ascii=False)
            out.flush()
            os.fsync(out.fileno())
            out.close()
            os.replace(out.name, path)
        finally:
            Path(out.name).unlink(missing_ok=True)


class RecordStatus:
    """历史记录状态常量"""
    DRAFT = "draft"          # 草稿：已创建大纲，未开始生成
    GENERATING = "generating"  # 生成中：正在生成图片
    PARTIAL = "partial"       # 部分完成：有部分图片生成
    COMPLETED = "completed"   # 已完成：所有图片已生成
    ERROR = "error"          # 错误：生成过程中出现错误


class HistoryService:
    def __init__(self):
        """
        初始化历史记录服务

        创建历史记录存储目录和索引文件
        """
        # 历史记录存储目录（项目根目录/history）
        self.history_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "history"
        )
        os.makedirs(self.history_dir, exist_ok=True)

        # 索引文件路径
        self.index_file = os.path.join(self.history_dir, "index.json")
        self._init_index()

    @history_transaction
    def _init_index(self):
        try:
            old = self._read_index()
        except FileNotFoundError:
            old = None
        except (ValueError, UnicodeError):
            shutil.copyfile(self.index_file, self.index_file + ".corrupt-" + uuid.uuid4().hex)
            old = None
        summaries = {r["id"]: r for r in (old or {}).get("records", [])}
        for path in Path(self.history_dir).glob("*.json"):
            try:
                uuid.UUID(path.stem)
            except ValueError:
                continue
            try:
                record = json.loads(path.read_text(encoding="utf-8"))
                if record["id"] == path.stem:
                    summaries[path.stem] = self._summary(record)
            except (ValueError, TypeError, KeyError):
                logger.exception("作品记录无法读取，保留现有索引与文件: %s", path.name)
        for removed in (Path(self.history_dir) / ".trash").glob("*.json"):
            if not Path(self._get_record_path(removed.stem)).exists():
                summaries.pop(removed.stem, None)
        records = sorted(summaries.values(), key=lambda r: r.get("created_at") or "", reverse=True)
        rebuilt = {"records": records}
        if rebuilt != old:
            try:
                self._save_index(rebuilt)
            except OSError as exc:
                if exc.errno != errno.ENOSPC:
                    raise
                logger.warning("存储已满，使用内存中的作品索引供浏览和备份")
        return rebuilt

    @staticmethod
    def _summary(record):
        return {**{key: record.get(key) for key in
                   ("id", "title", "created_at", "updated_at", "status", "thumbnail")},
                "page_count": len((record.get("outline") or {}).get("pages") or []),
                "task_id": (record.get("images") or {}).get("task_id")}

    def _read_index(self):
        with open(self.index_file, encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict) or not isinstance(data.get("records"), list) or any(
            not isinstance(r, dict) or not isinstance(r.get("id"), str) for r in data["records"]
        ):
            raise ValueError("无效的历史索引")
        return data

    def _load_index(self):
        try:
            return self._read_index()
        except (FileNotFoundError, ValueError, UnicodeError):
            return self._init_index()

    def _catalog(self):
        index = self._load_index()
        ids = {row["id"] for row in index["records"]}
        for path in Path(self.history_dir).glob("*.json"):
            if path.stem not in ids and len(path.stem) == 36:
                return self._init_index()
        return index

    def _save_index(self, index):
        atomic_json(self.index_file, index)

    def _get_record_path(self, record_id: str) -> str:
        """
        获取历史记录文件路径

        Args:
            record_id: 记录 ID

        Returns:
            str: 记录文件的完整路径
        """
        return os.path.join(self.history_dir, f"{record_id}.json")

    @history_transaction
    def create_record(
        self,
        topic: str,
        outline: Dict,
        task_id: Optional[str] = None
    ) -> str:
        """
        创建新的历史记录

        初始状态为 draft（草稿），表示大纲已创建但尚未开始生成图片。

        Args:
            topic: 绘本主题/标题
            outline: 大纲内容，包含 pages 数组等信息
            task_id: 关联的生成任务 ID（可选）

        Returns:
            str: 新创建的记录 ID（UUID 格式）

        状态流转：
            新建 -> draft（草稿状态）
        """
        # 生成唯一记录 ID
        record_id = str(uuid.uuid4())
        now = datetime.now().isoformat()

        # 创建完整的记录对象
        record = {
            "id": record_id,
            "title": topic,
            "created_at": now,
            "updated_at": now,
            "outline": outline,  # 保存完整的大纲数据
            "images": {
                "task_id": task_id,
                "generated": []  # 初始无生成图片
            },
            "content": None,  # 文案内容（标题、文案、标签）
            "status": RecordStatus.DRAFT,  # 初始状态：草稿
            "thumbnail": None  # 初始无缩略图
        }

        # 保存完整记录到独立文件
        record_path = self._get_record_path(record_id)
        atomic_json(record_path, record)

        # 更新索引（用于快速列表查询）
        index = self._load_index()
        index["records"] = [self._summary(record)] + [r for r in index["records"] if r["id"] != record_id]
        self._save_index(index)

        return record_id

    def get_record(self, record_id: str, sync_images: bool = False) -> Optional[Dict]:
        """
        获取历史记录详情

        Args:
            record_id: 记录 ID

        Returns:
            Optional[Dict]: 记录详情，如果不存在则返回 None

        返回数据包含：
            - id: 记录 ID
            - title: 标题
            - created_at: 创建时间
            - updated_at: 更新时间
            - outline: 大纲内容
            - images: 图片信息（task_id 和 generated 列表）
            - status: 当前状态
            - thumbnail: 缩略图文件名
        """
        record_path = self._get_record_path(record_id)

        if not os.path.exists(record_path):
            return None

        try:
            with open(record_path, "r", encoding="utf-8") as f:
                record = json.load(f)
        except Exception:
            return None

        if sync_images:
            synced = self.sync_record_images(record_id)
            if synced.get("success") and synced.get("updated"):
                return self.get_record(record_id, sync_images=False)

        return record

    def record_exists(self, record_id: str) -> bool:
        """
        检查历史记录是否存在

        Args:
            record_id: 记录 ID

        Returns:
            bool: 记录是否存在
        """
        record_path = self._get_record_path(record_id)
        return os.path.exists(record_path)

    @history_transaction
    def update_record(
        self,
        record_id: str,
        outline: Optional[Dict] = None,
        images: Optional[Dict] = None,
        content: Optional[Dict] = None,
        status: Optional[str] = None,
        thumbnail: Optional[str] = None
    ) -> bool:
        """
        更新历史记录

        支持部分更新，只更新提供的字段。
        每次更新都会自动刷新 updated_at 时间戳。

        Args:
            record_id: 记录 ID
            outline: 大纲内容（可选，用于修改大纲）
            images: 图片信息（可选，包含 task_id 和 generated 列表）
            content: 文案内容（可选，包含 titles, copywriting, tags）
            status: 状态（可选）
            thumbnail: 缩略图文件名（可选）

        Returns:
            bool: 更新是否成功，记录不存在时返回 False

        状态流转说明：
            draft -> generating: 开始生成图片
            generating -> partial: 部分图片生成完成
            generating -> completed: 所有图片生成完成
            generating -> error: 生成过程出错
            partial -> generating: 继续生成剩余图片
            partial -> completed: 剩余图片生成完成
        """
        # 获取现有记录
        record = self.get_record(record_id)
        if not record:
            return False

        # 更新时间戳
        now = datetime.now().isoformat()
        record["updated_at"] = now

        # 更新大纲内容（支持修改大纲）
        if outline is not None:
            record["outline"] = {**(record.get("outline") or {}), **outline}

        # 更新图片信息
        if images is not None:
            record["images"] = self._merge_safe_images(record.get("images"), images)

        # 更新文案内容
        if content is not None:
            record["content"] = content

        # 更新状态（状态流转）
        if status is not None:
            record["status"] = self._protect_status(record.get("status"), status, record)

        # 更新缩略图
        if thumbnail is not None:
            record["thumbnail"] = thumbnail

        # 保存完整记录
        record_path = self._get_record_path(record_id)
        atomic_json(record_path, record)

        # 同步更新索引
        index = self._load_index()
        for i, row in enumerate(index["records"]):
            if row["id"] == record_id:
                index["records"][i] = self._summary(record)
                break
        else:
            index["records"].insert(0, self._summary(record))

        self._save_index(index)
        return True

    @history_transaction
    def merge_generated_image(
        self,
        record_id: str,
        task_id: str,
        page_index: int,
        filename: str,
        total_count: Optional[int] = None
    ) -> bool:
        """按页面索引合并单张已生成图片。"""
        record = self.get_record(record_id)
        if not record:
            return False

        if total_count is None:
            total_count = len(record.get("outline", {}).get("pages", []))

        existing_images = record.get("images") or {}
        generated = HistoryImageMerger.merge_generated(
            existing_images.get("generated"),
            page_index,
            filename,
            total_count,
        )
        status = HistoryImageMerger.compute_status(generated, total_count)
        thumbnail = HistoryImageMerger.cover_thumbnail(generated, record.get("outline", {}).get("pages", []))

        return self.update_record(
            record_id,
            images={
                "task_id": task_id,
                "generated": generated,
            },
            status=status,
            thumbnail=thumbnail,
        )

    @history_transaction
    def sync_record_images(self, record_id: str, record: Optional[Dict] = None) -> Dict[str, Any]:
        """从任务目录扫描图片并合并回历史记录。"""
        if record is None:
            record = self.get_record(record_id)
        if not record:
            return {"success": False, "error": "历史记录不存在"}

        task_id = record.get("images", {}).get("task_id")
        if not task_id:
            return {"success": True, "updated": False}

        files_by_index = HistoryImageMerger.files_by_index(self.history_dir, task_id)
        if not files_by_index:
            return {"success": True, "updated": False}

        total_count = len(record.get("outline", {}).get("pages", []))
        existing_generated = record.get("images", {}).get("generated", [])
        generated = HistoryImageMerger.merge_many(
            existing_generated,
            files_by_index,
            total_count,
        )
        status = HistoryImageMerger.compute_status(generated, total_count)
        thumbnail = HistoryImageMerger.cover_thumbnail(generated, record.get("outline", {}).get("pages", []))

        if (
            generated == existing_generated
            and record.get("status") == status
            and record.get("thumbnail") == thumbnail
        ):
            return {"success": True, "updated": False}

        updated = self.update_record(
            record_id,
            images={
                "task_id": task_id,
                "generated": generated,
            },
            status=status,
            thumbnail=thumbnail,
        )
        return {
            "success": updated,
            "updated": updated,
            "record_id": record_id,
            "task_id": task_id,
            "images": generated,
            "status": status,
        }

    def _merge_safe_images(self, current_images: Optional[Dict], incoming_images: Dict) -> Dict:
        current = dict(current_images or {})
        incoming = dict(incoming_images or {})

        current_generated = current.get("generated") or []
        incoming_generated = incoming.get("generated")

        if (
            isinstance(incoming_generated, list)
            and not HistoryImageMerger.has_images(incoming_generated)
            and HistoryImageMerger.has_images(current_generated)
        ):
            incoming["generated"] = current_generated

        if not incoming.get("task_id") and current.get("task_id"):
            incoming["task_id"] = current.get("task_id")

        return {
            "task_id": incoming.get("task_id"),
            "generated": [item or "" for item in incoming.get("generated", current_generated)],
        }

    def _protect_status(self, current_status: Optional[str], incoming_status: str, record: Dict) -> str:
        if (
            incoming_status == RecordStatus.GENERATING
            and current_status in {RecordStatus.PARTIAL, RecordStatus.COMPLETED}
            and HistoryImageMerger.has_images(record.get("images", {}).get("generated"))
        ):
            logger.info("忽略历史状态回退: %s -> %s", current_status, incoming_status)
            return current_status
        return incoming_status

    @history_transaction
    def delete_record(self, record_id: str) -> bool:
        """
        删除历史记录

        将记录移出列表，并在备份中保留原始记录及图片。

        Args:
            record_id: 记录 ID

        Returns:
            bool: 删除是否成功，记录不存在时返回 False
        """
        record = self.get_record(record_id)
        if not record:
            return False

        # A task can be referenced by multiple works. Keep original files available for backup.
        trash = Path(self.history_dir) / ".trash"
        trash.mkdir(exist_ok=True)
        os.replace(self._get_record_path(record_id), trash / f"{record_id}.json")

        # 从索引中移除
        index = self._load_index()
        index["records"] = [r for r in index["records"] if r["id"] != record_id]
        self._save_index(index)

        return True

    def list_records(
        self,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None
    ) -> Dict:
        """
        分页获取历史记录列表

        Args:
            page: 页码，从 1 开始
            page_size: 每页记录数
            status: 状态过滤（可选），支持：draft/generating/partial/completed/error

        Returns:
            Dict: 分页结果
                - records: 当前页的记录列表
                - total: 总记录数
                - page: 当前页码
                - page_size: 每页大小
                - total_pages: 总页数
        """
        index = self._catalog()
        records = index.get("records", [])

        # 按状态过滤
        if status:
            records = [r for r in records if r.get("status") == status]

        # 分页计算
        total = len(records)
        start = (page - 1) * page_size
        end = start + page_size
        page_records = records[start:end]

        self._mark_missing_covers(page_records)
        return {
            "records": page_records,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }

    def search_records(self, keyword: str) -> List[Dict]:
        """
        根据关键词搜索历史记录

        Args:
            keyword: 搜索关键词（不区分大小写）

        Returns:
            List[Dict]: 匹配的记录列表（按创建时间倒序）
        """
        index = self._catalog()
        records = index.get("records", [])

        # 不区分大小写的标题搜索
        keyword_lower = keyword.lower()
        results = [
            r for r in records
            if keyword_lower in r.get("title", "").lower()
        ]

        self._mark_missing_covers(results)
        return results

    def _mark_missing_covers(self, rows):
        for row in rows:
            name, task = row.get("thumbnail"), row.get("task_id")
            if name and task and not (Path(self.history_dir) / task / name).is_file():
                row["missing_cover"] = True

    def get_statistics(self) -> Dict:
        """
        获取历史记录统计信息

        Returns:
            Dict: 统计数据
                - total: 总记录数
                - by_status: 各状态的记录数
                    - draft: 草稿数
                    - generating: 生成中数
                    - partial: 部分完成数
                    - completed: 已完成数
                    - error: 错误数
        """
        index = self._catalog()
        records = index.get("records", [])

        total = len(records)
        usage = shutil.disk_usage(self.history_dir)
        status_count = {}

        # 统计各状态的记录数
        for record in records:
            status = record.get("status", RecordStatus.DRAFT)
            status_count[status] = status_count.get(status, 0) + 1

        return {
            "total": total,
            "storage": {"free": usage.free, "total": usage.total,
                        "warning": usage.free <= max(256 * 1024**2, usage.total // 5)},
            "by_status": status_count
        }

    @history_transaction
    def scan_and_sync_task_images(self, task_id: str) -> Dict[str, Any]:
        """
        扫描任务文件夹，同步图片列表

        根据实际生成的图片数量自动更新记录状态：
        - 无图片 -> draft（草稿）
        - 部分图片 -> partial（部分完成）
        - 全部图片 -> completed（已完成）

        Args:
            task_id: 任务 ID

        Returns:
            Dict[str, Any]: 扫描结果
                - success: 是否成功
                - record_id: 关联的记录 ID
                - task_id: 任务 ID
                - images_count: 图片数量
                - images: 图片文件名列表
                - status: 更新后的状态
                - error: 错误信息（失败时）
        """
        task_dir = os.path.join(self.history_dir, task_id)

        if not os.path.exists(task_dir) or not os.path.isdir(task_dir):
            return {
                "success": False,
                "error": f"任务目录不存在: {task_id}"
            }

        try:
            files_by_index = HistoryImageMerger.files_by_index(self.history_dir, task_id)
            image_files = list(files_by_index.values())

            # 查找关联的历史记录
            index = self._load_index()
            record_id = next((row["id"] for row in index["records"] if row.get("task_id") == task_id), None)

            if record_id:
                # 更新历史记录
                record = self.get_record(record_id)
                if record:
                    expected_count = len(record.get("outline", {}).get("pages", []))
                    existing_generated = record.get("images", {}).get("generated", [])
                    merged_images = HistoryImageMerger.merge_many(
                        existing_generated,
                        files_by_index,
                        expected_count,
                    )
                    status = HistoryImageMerger.compute_status(merged_images, expected_count)

                    # 更新图片列表和状态
                    self.update_record(
                        record_id,
                        images={
                            "task_id": task_id,
                            "generated": merged_images
                        },
                        status=status,
                        thumbnail=HistoryImageMerger.cover_thumbnail(merged_images, record.get("outline", {}).get("pages", []))
                    )

                    return {
                        "success": True,
                        "record_id": record_id,
                        "task_id": task_id,
                        "images_count": len(image_files),
                        "images": merged_images,
                        "status": status
                    }

            # 没有关联的记录，返回扫描结果
            return {
                "success": True,
                "task_id": task_id,
                "images_count": len(image_files),
                "images": image_files,
                "no_record": True
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"扫描任务失败: {str(e)}"
            }

    def scan_all_tasks(self) -> Dict[str, Any]:
        """
        扫描所有任务文件夹，同步图片列表

        批量扫描 history 目录下的所有任务文件夹，
        同步图片列表并更新记录状态。

        Returns:
            Dict[str, Any]: 扫描结果统计
                - success: 是否成功
                - total_tasks: 扫描的任务总数
                - synced: 成功同步的任务数
                - failed: 失败的任务数
                - orphan_tasks: 孤立任务列表（有图片但无记录）
                - results: 详细结果列表
                - error: 错误信息（失败时）
        """
        if not os.path.exists(self.history_dir):
            return {
                "success": False,
                "error": "历史记录目录不存在"
            }

        try:
            synced_count = 0
            failed_count = 0
            orphan_tasks = []  # 没有关联记录的任务
            results = []

            # 遍历 history 目录
            for item in os.listdir(self.history_dir):
                item_path = os.path.join(self.history_dir, item)

                # 只处理目录（任务文件夹）
                if not os.path.isdir(item_path):
                    continue

                # 假设任务文件夹名就是 task_id
                task_id = item

                # 扫描并同步
                result = self.scan_and_sync_task_images(task_id)
                results.append(result)

                if result.get("success"):
                    if result.get("no_record"):
                        orphan_tasks.append(task_id)
                    else:
                        synced_count += 1
                else:
                    failed_count += 1

            return {
                "success": True,
                "total_tasks": len(results),
                "synced": synced_count,
                "failed": failed_count,
                "orphan_tasks": orphan_tasks,
                "results": results
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"扫描所有任务失败: {str(e)}"
            }


_service_instance = None


def get_history_service() -> HistoryService:
    """
    获取历史记录服务实例（单例模式）

    Returns:
        HistoryService: 历史记录服务实例
    """
    global _service_instance
    if _service_instance is None:
        _service_instance = HistoryService()
    return _service_instance
