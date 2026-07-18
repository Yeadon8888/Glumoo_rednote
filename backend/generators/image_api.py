"""Image API 图片生成器"""
import logging
import base64
import io
import time
import random
import requests
from typing import Dict, Any, Optional, List, Union
from PIL import Image
from .base import ImageGeneratorBase
from ..utils.image_compressor import compress_image

logger = logging.getLogger(__name__)


class ImageApiGenerator(ImageGeneratorBase):
    """Image API 生成器"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        logger.debug("初始化 ImageApiGenerator...")
        self.base_url = config.get('base_url', 'https://api.example.com').rstrip('/').rstrip('/v1')
        self.model = config.get('model', 'default-model')
        self.default_aspect_ratio = config.get('default_aspect_ratio', '3:4')
        self.image_size = config.get('image_size', '4K')
        self.quality = config.get('quality', 'low')
        self.output_format = config.get('format', 'png')
        self.edit_endpoint = config.get('edit_endpoint', '/v1/images/edits')
        self.reference_mode = config.get('reference_mode', 'multipart_edit')
        self.include_output_options = bool(config.get('include_output_options', True))
        self.create_retry_count = int(config.get('create_retry_count', 4))
        self.create_retry_base_delay = float(config.get('create_retry_base_delay', 12))

        # 支持自定义端点路径
        endpoint_type = config.get('endpoint_type', '/v1/images/generations')
        # 兼容旧的简写格式
        if endpoint_type == 'images':
            endpoint_type = '/v1/images/generations'
        elif endpoint_type == 'chat':
            endpoint_type = '/v1/chat/completions'
        # 确保以 / 开头
        if not endpoint_type.startswith('/'):
            endpoint_type = '/' + endpoint_type
        self.endpoint_type = endpoint_type

        logger.info(f"ImageApiGenerator 初始化完成: base_url={self.base_url}, model={self.model}, endpoint={self.endpoint_type}")

    def validate_config(self) -> bool:
        """验证配置是否有效"""
        if not self.api_key:
            logger.error("Image API Key 未配置")
            raise ValueError(
                "Image API Key 未配置。\n"
                "解决方案：在系统设置页面编辑该服务商，填写 API Key"
            )
        return True

    def get_supported_sizes(self) -> List[str]:
        """获取支持的图片尺寸"""
        return ["1K", "2K", "4K"]

    def get_supported_aspect_ratios(self) -> List[str]:
        """获取支持的宽高比"""
        return ["1:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9", "21:9"]

    def generate_image(
        self,
        prompt: str,
        aspect_ratio: str = None,
        temperature: float = 1.0,
        model: str = None,
        reference_image: Optional[bytes] = None,
        reference_images: Optional[List[bytes]] = None,
        **kwargs
    ) -> bytes:
        """
        生成图片

        Args:
            prompt: 图片描述
            aspect_ratio: 宽高比
            temperature: 创意度（未使用，保留接口兼容）
            model: 模型名称
            reference_image: 单张参考图片数据（向后兼容）
            reference_images: 多张参考图片数据列表

        Returns:
            生成的图片二进制数据
        """
        self.validate_config()

        if aspect_ratio is None:
            aspect_ratio = self.default_aspect_ratio

        if model is None:
            model = self.model

        logger.info(f"Image API 生成图片: model={model}, aspect_ratio={aspect_ratio}, endpoint={self.endpoint_type}")

        # 根据端点类型选择不同的生成方式
        if 'videos' in self.endpoint_type:
            image_data = self._generate_via_videos_api(
                prompt, aspect_ratio, model, reference_image, reference_images
            )
        elif 'chat' in self.endpoint_type or 'completions' in self.endpoint_type:
            image_data = self._generate_via_chat_api(
                prompt, aspect_ratio, model, reference_image, reference_images
            )
        else:
            image_data = self._generate_via_images_api(
                prompt, aspect_ratio, model, reference_image, reference_images
            )
        return self._normalize_output_aspect_ratio(image_data, aspect_ratio)

    def _collect_reference_image_uris(
        self,
        reference_image: Optional[bytes] = None,
        reference_images: Optional[List[bytes]] = None
    ) -> List[str]:
        all_reference_images = []
        if reference_images and len(reference_images) > 0:
            all_reference_images.extend(reference_images)
        if reference_image and reference_image not in all_reference_images:
            all_reference_images.append(reference_image)

        image_uris = []
        for idx, img_data in enumerate(all_reference_images):
            compressed_img = compress_image(img_data, max_size_kb=200)
            logger.debug(f"  参考图 {idx}: {len(img_data)} -> {len(compressed_img)} bytes")
            base64_image = base64.b64encode(compressed_img).decode('utf-8')
            image_uris.append(f"data:{self._image_mime(compressed_img)};base64,{base64_image}")
        return image_uris

    def _generate_via_images_api(
        self,
        prompt: str,
        aspect_ratio: str,
        model: str,
        reference_image: Optional[bytes] = None,
        reference_images: Optional[List[bytes]] = None
    ) -> bytes:
        """通过同步 generations 端点生成图片，必要时兼容 edits。"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 TokensFactory-Glumoo/1.0"
        }

        size = self._generation_size(aspect_ratio)
        safe_prompt = (
            f"{prompt}\n\n输出构图要求：竖版 {aspect_ratio}；所有标题、正文、产品和关键信息"
            f"都放在中央 {aspect_ratio} 安全区内，四周保留可裁切留白。"
        )
        all_reference_images = self._collect_reference_images(
            reference_image, reference_images
        )

        if all_reference_images and self.reference_mode == 'multipart_edit':
            api_url = f"{self.base_url}{self.edit_endpoint}"
            data = {
                "model": model,
                "prompt": safe_prompt,
                "n": "1",
                "size": size,
                "quality": self.quality,
                "format": self.output_format,
            }
            files = []
            for index, image in enumerate(all_reference_images):
                compressed = compress_image(image, max_size_kb=200)
                files.append((
                    "image[]",
                    (
                        f"reference-{index + 1}.{self._image_extension(compressed)}",
                        compressed,
                        self._image_mime(compressed),
                    ),
                ))
            logger.info(f"Images Edits API: {api_url}, references={len(files)}")
            response = self._post_with_retry(
                api_url, headers, model, data=data, files=files, timeout=300
            )
        else:
            api_url = f"{self.base_url}{self.endpoint_type}"
            payload: Dict[str, Any] = {
                "model": model,
                "prompt": safe_prompt,
                "n": 1,
                "size": size,
            }
            if self.include_output_options:
                payload.update({
                    "quality": self.quality,
                    "format": self.output_format,
                })
            if all_reference_images:
                payload["images"] = self._collect_reference_image_uris(
                    reference_image, reference_images
                )
            json_headers = {**headers, "Content-Type": "application/json"}
            logger.info(
                f"Images Generations API: {api_url}, size={size}, "
                f"references={len(all_reference_images)}"
            )
            response = self._post_with_retry(
                api_url, json_headers, model, json=payload, timeout=300
            )

        if response.status_code != 200:
            error_detail = response.text[:500]
            logger.error(f"Image API 请求失败: status={response.status_code}, error={error_detail}")
            raise Exception(
                f"Image API 请求失败 (状态码: {response.status_code})\n"
                f"错误详情: {error_detail}\n"
                f"请求地址: {api_url}\n"
                "可能原因：\n"
                "1. API密钥无效或已过期\n"
                "2. 请求参数不符合API要求\n"
                "3. API服务端错误\n"
                "4. Base URL配置错误\n"
                "建议：检查API密钥和base_url配置"
            )

        result = response.json()
        image_data = self._extract_sync_image_data(result)
        if image_data:
            logger.info(f"✅ Image API 图片生成成功: {len(image_data)} bytes")
            return image_data

        logger.error(f"无法从响应中提取图片数据: {str(result)[:200]}")
        raise Exception(
            f"图片数据提取失败：未找到 b64_json 数据。\n"
            f"API响应片段: {str(result)[:500]}\n"
            "可能原因：\n"
            "1. API返回格式与预期不符\n"
            "2. response_format 参数未生效\n"
            "3. 该模型不支持 b64_json 格式\n"
            "建议：检查API文档确认返回格式要求"
        )

    @staticmethod
    def _collect_reference_images(
        reference_image: Optional[bytes],
        reference_images: Optional[List[bytes]],
    ) -> List[bytes]:
        images = list(reference_images or [])
        if reference_image and reference_image not in images:
            images.append(reference_image)
        return images

    @staticmethod
    def _image_mime(data: bytes) -> str:
        if data.startswith(b"\x89PNG\r\n\x1a\n"):
            return "image/png"
        if data.startswith(b"\xff\xd8\xff"):
            return "image/jpeg"
        if data.startswith(b"RIFF") and data[8:12] == b"WEBP":
            return "image/webp"
        return "application/octet-stream"

    @classmethod
    def _image_extension(cls, data: bytes) -> str:
        return {
            "image/png": "png",
            "image/jpeg": "jpg",
            "image/webp": "webp",
        }.get(cls._image_mime(data), "bin")

    def _post_with_retry(
        self,
        api_url: str,
        headers: Dict[str, str],
        model: str,
        **request_kwargs,
    ) -> requests.Response:
        last_response = None
        for attempt in range(self.create_retry_count + 1):
            response = requests.post(api_url, headers=headers, **request_kwargs)
            last_response = response
            if response.status_code not in [429, 500, 502, 503, 504]:
                return response
            if attempt >= self.create_retry_count:
                return response
            wait_seconds = self._retry_delay_seconds(attempt)
            logger.warning(
                f"Images API 暂时失败: status={response.status_code}, model={model}, "
                f"等待 {wait_seconds:.1f}s 后重试"
            )
            time.sleep(wait_seconds)
        return last_response

    def _extract_sync_image_data(self, result: Dict[str, Any]) -> Optional[bytes]:
        data = result.get("data")
        if not isinstance(data, list) or not data or not isinstance(data[0], dict):
            return None
        item = data[0]
        b64_value = item.get("b64_json")
        if isinstance(b64_value, str) and b64_value:
            return base64.b64decode(b64_value.split(',', 1)[-1])
        url = item.get("url")
        if isinstance(url, str) and url:
            return self._download_image(url)
        return None

    def _generation_size(self, aspect_ratio: str) -> str:
        if self.model == "gpt-image-2-all":
            return {
                "1:1": "1024x1024",
                "3:4": "1200x1600",
                "4:3": "1600x1200",
                "9:16": "864x1536",
                "16:9": "1536x864",
            }.get(aspect_ratio, "1200x1600")
        if aspect_ratio in {"1:1"}:
            return "1024x1024"
        if aspect_ratio in {"16:9", "3:2", "4:3", "5:4"}:
            return "1536x1024"
        return "1024x1536"

    @staticmethod
    def _normalize_output_aspect_ratio(image_data: bytes, aspect_ratio: str) -> bytes:
        try:
            width_text, height_text = aspect_ratio.split(':', 1)
            target_ratio = float(width_text) / float(height_text)
            with Image.open(io.BytesIO(image_data)) as image:
                current_ratio = image.width / image.height
                if abs(current_ratio - target_ratio) <= 0.005:
                    return image_data
                if current_ratio > target_ratio:
                    crop_width = max(1, round(image.height * target_ratio))
                    left = max(0, (image.width - crop_width) // 2)
                    box = (left, 0, left + crop_width, image.height)
                else:
                    crop_height = max(1, round(image.width / target_ratio))
                    top = max(0, (image.height - crop_height) // 2)
                    box = (0, top, image.width, top + crop_height)
                cropped = image.crop(box).convert("RGB")
                output = io.BytesIO()
                cropped.save(output, format="PNG", optimize=True)
                logger.info(
                    f"图片比例已校正: {image.width}x{image.height} -> "
                    f"{cropped.width}x{cropped.height} ({aspect_ratio})"
                )
                return output.getvalue()
        except (ValueError, ZeroDivisionError, OSError):
            logger.warning(f"无法校正图片比例，保留原图: aspect_ratio={aspect_ratio}")
            return image_data

    def _generate_via_videos_api(
        self,
        prompt: str,
        aspect_ratio: str,
        model: str,
        reference_image: Optional[bytes] = None,
        reference_images: Optional[List[bytes]] = None
    ) -> bytes:
        """通过 /v1/videos 异步任务端点生成图片。"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": model,
            "prompt": prompt,
            "seconds": "4",
            "aspect_ratio": aspect_ratio
        }

        image_uris = self._collect_reference_image_uris(reference_image, reference_images)
        if image_uris:
            logger.debug(f"  添加 {len(image_uris)} 张参考图片到 videos 任务")
            payload["images"] = image_uris

        api_url = f"{self.base_url}{self.endpoint_type}"
        response = self._create_video_task_with_retry(api_url, headers, payload, model)

        if response.status_code not in [200, 201, 202]:
            error_detail = response.text[:500]
            logger.error(f"Videos API 创建任务失败: status={response.status_code}, error={error_detail}")
            self._raise_video_task_error(response.status_code, error_detail, api_url, model)

        result = response.json()
        image_data = self._extract_image_data_from_task_result(result)
        if image_data:
            return image_data

        task_id = result.get("task_id") or result.get("id") or result.get("data", {}).get("id")
        if not task_id:
            raise Exception(
                f"Videos API 响应中未找到 task_id。\n"
                f"API响应片段: {str(result)[:500]}"
            )

        status_url = f"{self.base_url}{self.endpoint_type.rstrip('/')}/{task_id}"
        logger.info(f"Videos API 轮询任务: {task_id}")

        deadline = time.time() + 360
        last_result = result
        while time.time() < deadline:
            time.sleep(5)
            poll_response = requests.get(status_url, headers=headers, timeout=60)
            if poll_response.status_code != 200:
                raise Exception(
                    f"Videos API 查询任务失败 (状态码: {poll_response.status_code})\n"
                    f"错误详情: {poll_response.text[:300]}"
                )

            last_result = poll_response.json()
            image_data = self._extract_image_data_from_task_result(last_result)
            if image_data:
                logger.info("✅ Videos API 图片生成成功")
                return image_data

            status = str(last_result.get("status") or last_result.get("state") or "").lower()
            if status in ["failed", "failure", "error", "cancelled", "canceled"]:
                raise Exception(
                    f"Videos API 图片任务失败: {status}\n"
                    f"任务响应片段: {str(last_result)[:500]}"
                )

        raise Exception(
            "Videos API 图片任务超时。\n"
            f"最后响应片段: {str(last_result)[:500]}"
        )

    def _create_video_task_with_retry(
        self,
        api_url: str,
        headers: Dict[str, str],
        payload: Dict[str, Any],
        model: str
    ) -> requests.Response:
        last_response = None

        for attempt in range(self.create_retry_count + 1):
            logger.info(
                f"Videos API 创建图片任务: {api_url}, model={model}, "
                f"attempt={attempt + 1}/{self.create_retry_count + 1}"
            )
            response = requests.post(api_url, headers=headers, json=payload, timeout=60)
            last_response = response

            if response.status_code not in [429, 500, 502, 503, 504]:
                return response

            if attempt >= self.create_retry_count:
                return response

            wait_seconds = self._retry_delay_seconds(attempt)
            logger.warning(
                f"Videos API 创建任务暂时失败: status={response.status_code}, "
                f"等待 {wait_seconds:.1f}s 后重试，error={response.text[:200]}"
            )
            time.sleep(wait_seconds)

        return last_response

    def _retry_delay_seconds(self, attempt: int) -> float:
        return self.create_retry_base_delay * (attempt + 1) + random.uniform(0, 3)

    def _raise_video_task_error(self, status_code: int, error_detail: str, api_url: str, model: str):
        if status_code == 429:
            raise Exception(
                "图片服务上游繁忙，已多次自动重试但仍未排到任务。\n"
                f"服务返回: {error_detail}\n"
                "建议：稍等 1-3 分钟后重试，或切换到更空闲/更高配额的图片模型。"
            )

        if status_code in [500, 502, 503, 504]:
            raise Exception(
                f"图片服务临时不可用 (状态码: {status_code})，已自动重试但仍失败。\n"
                f"服务返回: {error_detail}\n"
                "建议：稍后重试。"
            )

        raise Exception(
            f"Videos API 创建任务失败 (状态码: {status_code})\n"
            f"错误详情: {error_detail}\n"
            f"请求地址: {api_url}\n"
            f"模型: {model}"
        )

    def _extract_image_data_from_task_result(self, result: Dict[str, Any]) -> Optional[bytes]:
        """从异步图片任务响应中提取图片 URL 或 data URL。"""
        url = self._extract_image_url(result)
        if not url:
            return None

        if url.startswith("data:image"):
            return base64.b64decode(url.split(",", 1)[1])
        return self._download_image(url)

    def _extract_image_url(self, result: Any) -> Optional[str]:
        if isinstance(result, str):
            if result.startswith("http://") or result.startswith("https://") or result.startswith("data:image"):
                return result
            return None

        if isinstance(result, list):
            for item in result:
                found = self._extract_image_url(item)
                if found:
                    return found
            return None

        if not isinstance(result, dict):
            return None

        for key in ["image_url", "url", "output_url", "result_url"]:
            value = result.get(key)
            if isinstance(value, str) and (
                value.startswith("http://") or value.startswith("https://") or value.startswith("data:image")
            ):
                return value

        metadata = result.get("metadata")
        if isinstance(metadata, dict):
            found = self._extract_image_url(metadata.get("result_urls"))
            if found:
                return found

        for key in ["data", "output", "result", "results", "images"]:
            found = self._extract_image_url(result.get(key))
            if found:
                return found

        return None

    def _generate_via_chat_api(
        self,
        prompt: str,
        aspect_ratio: str,
        model: str,
        reference_image: Optional[bytes] = None,
        reference_images: Optional[List[bytes]] = None
    ) -> bytes:
        """通过 /v1/chat/completions 端点生成图片（如即梦 API）"""
        import re

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # 构建用户消息内容
        user_content: Any = prompt

        # 收集所有参考图片
        all_reference_images = []
        if reference_images and len(reference_images) > 0:
            all_reference_images.extend(reference_images)
        if reference_image and reference_image not in all_reference_images:
            all_reference_images.append(reference_image)

        # 如果有参考图片，构建多模态消息
        if all_reference_images:
            logger.debug(f"  添加 {len(all_reference_images)} 张参考图片到 chat 消息")
            content_parts = [{"type": "text", "text": prompt}]

            for idx, img_data in enumerate(all_reference_images):
                compressed_img = compress_image(img_data, max_size_kb=200)
                logger.debug(f"  参考图 {idx}: {len(img_data)} -> {len(compressed_img)} bytes")
                base64_image = base64.b64encode(compressed_img).decode('utf-8')
                content_parts.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{base64_image}"}
                })

            user_content = content_parts

        payload = {
            "model": model,
            "messages": [{"role": "user", "content": user_content}],
            "max_tokens": 4096,
            "temperature": 1.0
        }

        api_url = f"{self.base_url}{self.endpoint_type}"
        logger.info(f"Chat API 生成图片: {api_url}, model={model}")

        response = requests.post(api_url, headers=headers, json=payload, timeout=300)

        if response.status_code != 200:
            error_detail = response.text[:500]
            status_code = response.status_code

            if status_code == 401:
                raise Exception(
                    "❌ API Key 认证失败\n\n"
                    "【可能原因】\n"
                    "1. API Key 无效或已过期\n"
                    "2. API Key 格式错误\n\n"
                    "【解决方案】\n"
                    "在系统设置页面检查 API Key 是否正确"
                )
            elif status_code == 429:
                raise Exception(
                    "⏳ API 配额或速率限制\n\n"
                    "【解决方案】\n"
                    "1. 稍后再试\n"
                    "2. 检查 API 配额使用情况"
                )
            else:
                raise Exception(
                    f"❌ Chat API 请求失败 (状态码: {status_code})\n\n"
                    f"【错误详情】\n{error_detail[:300]}\n\n"
                    f"【请求地址】{api_url}\n"
                    f"【模型】{model}"
                )

        result = response.json()
        logger.debug(f"Chat API 响应: {str(result)[:500]}")

        # 解析响应
        if "choices" in result and len(result["choices"]) > 0:
            choice = result["choices"][0]
            if "message" in choice and "content" in choice["message"]:
                content = choice["message"]["content"]

                if isinstance(content, str):
                    # Markdown 图片链接: ![xxx](url)
                    pattern = r'!\[.*?\]\((https?://[^\s\)]+)\)'
                    urls = re.findall(pattern, content)
                    if urls:
                        logger.info(f"从 Markdown 提取到 {len(urls)} 张图片，下载第一张...")
                        return self._download_image(urls[0])

                    # Markdown 图片 Base64: ![xxx](data:image/...)
                    base64_pattern = r'!\[.*?\]\((data:image\/[^;]+;base64,[^\s\)]+)\)'
                    base64_urls = re.findall(base64_pattern, content)
                    if base64_urls:
                        logger.info("从 Markdown 提取到 Base64 图片数据")
                        base64_data = base64_urls[0].split(",")[1]
                        return base64.b64decode(base64_data)

                    # 纯 Base64 data URL
                    if content.startswith("data:image"):
                        logger.info("检测到 Base64 图片数据")
                        base64_data = content.split(",")[1]
                        return base64.b64decode(base64_data)

                    # 纯 URL
                    if content.startswith("http://") or content.startswith("https://"):
                        logger.info("检测到图片 URL")
                        return self._download_image(content.strip())

        raise Exception(
            "❌ 无法从 Chat API 响应中提取图片数据\n\n"
            f"【响应内容】\n{str(result)[:500]}\n\n"
            "【可能原因】\n"
            "1. 该模型不支持图片生成\n"
            "2. 响应格式与预期不符\n"
            "3. 提示词被安全过滤\n\n"
            "【解决方案】\n"
            "1. 确认模型名称正确\n"
            "2. 修改提示词后重试"
        )

    def _download_image(self, url: str) -> bytes:
        """下载图片并返回二进制数据"""
        logger.info(f"下载图片: {url[:100]}...")
        try:
            headers = {}
            if self.base_url and url.startswith(self.base_url):
                headers["Authorization"] = f"Bearer {self.api_key}"

            response = requests.get(url, headers=headers, timeout=60)
            if response.status_code == 200:
                content_type = response.headers.get("Content-Type", "")
                if "application/json" in content_type:
                    raise Exception(f"下载结果不是图片: {response.text[:300]}")
                logger.info(f"✅ 图片下载成功: {len(response.content)} bytes")
                return response.content
            else:
                raise Exception(f"下载图片失败: HTTP {response.status_code}")
        except requests.exceptions.Timeout:
            raise Exception("❌ 下载图片超时，请重试")
        except Exception as e:
            raise Exception(f"❌ 下载图片失败: {str(e)}")
