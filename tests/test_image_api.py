"""Tests for the TokensFactory-compatible image API generator."""

import base64
import io

from PIL import Image

from backend.generators.image_api import ImageApiGenerator


class FakeResponse:
    def __init__(self, image_data: bytes, status_code: int = 200):
        self.status_code = status_code
        self._image_data = image_data
        self.text = "ok"

    def json(self):
        return {
            "data": [{
                "b64_json": base64.b64encode(self._image_data).decode("ascii")
            }]
        }


def make_png(width: int = 300, height: int = 400) -> bytes:
    output = io.BytesIO()
    Image.new("RGB", (width, height), "blue").save(output, format="PNG")
    return output.getvalue()


def make_generator() -> ImageApiGenerator:
    return ImageApiGenerator({
        "api_key": "test-key",
        "base_url": "https://tokensfactory.cc/v1",
        "endpoint_type": "/v1/images/generations",
        "edit_endpoint": "/v1/images/edits",
        "model": "gpt-image-2-plus",
        "default_aspect_ratio": "3:4",
        "image_size": "2048x2048",
        "output_size": "1536x2048",
        "quality": "low",
        "response_format": "url",
        "output_format": "png",
        "create_retry_count": 0,
    })


def test_generation_uses_sync_images_endpoint(monkeypatch):
    calls = []

    def fake_post(url, headers, **kwargs):
        calls.append((url, headers, kwargs))
        return FakeResponse(make_png())

    monkeypatch.setattr("backend.generators.image_api.requests.post", fake_post)

    result = make_generator().generate_image("test poster", aspect_ratio="3:4")

    assert result.startswith(b"\x89PNG")
    url, headers, kwargs = calls[0]
    assert url == "https://tokensfactory.cc/v1/images/generations"
    assert headers["Authorization"] == "Bearer test-key"
    assert kwargs["json"]["model"] == "gpt-image-2-plus"
    assert kwargs["json"]["size"] == "2048x2048"
    assert kwargs["json"]["quality"] == "low"
    assert kwargs["json"]["response_format"] == "url"
    assert kwargs["json"]["output_format"] == "png"
    assert "format" not in kwargs["json"]
    assert "files" not in kwargs


def test_references_use_multipart_edits_endpoint(monkeypatch):
    calls = []

    def fake_post(url, headers, **kwargs):
        calls.append((url, headers, kwargs))
        return FakeResponse(make_png())

    monkeypatch.setattr("backend.generators.image_api.requests.post", fake_post)
    references = [make_png(80, 80), make_png(90, 90)]

    make_generator().generate_image(
        "test poster",
        aspect_ratio="3:4",
        reference_images=references,
    )

    url, headers, kwargs = calls[0]
    assert url == "https://tokensfactory.cc/v1/images/edits"
    assert "Content-Type" not in headers
    assert kwargs["data"]["model"] == "gpt-image-2-plus"
    assert kwargs["data"]["response_format"] == "url"
    assert kwargs["data"]["output_format"] == "png"
    assert [name for name, _ in kwargs["files"]] == ["image[]", "image[]"]
    assert "json" not in kwargs


def test_output_is_center_cropped_to_requested_ratio(monkeypatch):
    def fake_post(url, headers, **kwargs):
        return FakeResponse(make_png(900, 1600))

    monkeypatch.setattr("backend.generators.image_api.requests.post", fake_post)

    result = make_generator().generate_image("test poster", aspect_ratio="3:4")

    with Image.open(io.BytesIO(result)) as image:
        assert image.size == (1536, 2048)


def test_cloudflare_524_is_retried(monkeypatch):
    calls = []

    def fake_post(url, headers, **kwargs):
        calls.append((url, headers, kwargs))
        if len(calls) == 1:
            return FakeResponse(b"", status_code=524)
        return FakeResponse(make_png(2048, 2048))

    generator = make_generator()
    generator.create_retry_count = 1
    monkeypatch.setattr("backend.generators.image_api.requests.post", fake_post)
    monkeypatch.setattr("backend.generators.image_api.time.sleep", lambda _: None)

    result = generator.generate_image("test poster", aspect_ratio="3:4")

    assert len(calls) == 2
    with Image.open(io.BytesIO(result)) as image:
        assert image.size == (1536, 2048)
