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
        "reference_mode": "json_images",
        "include_output_options": False,
        "model": "gpt-image-2-all",
        "default_aspect_ratio": "3:4",
        "image_size": "1200x1600",
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
    assert kwargs["json"]["model"] == "gpt-image-2-all"
    assert kwargs["json"]["size"] == "1200x1600"
    assert "quality" not in kwargs["json"]
    assert "format" not in kwargs["json"]
    assert "files" not in kwargs


def test_references_use_json_images_on_generations_endpoint(monkeypatch):
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
    assert url == "https://tokensfactory.cc/v1/images/generations"
    assert headers["Content-Type"] == "application/json"
    assert kwargs["json"]["model"] == "gpt-image-2-all"
    assert len(kwargs["json"]["images"]) == 2
    assert all(value.startswith("data:image/png;base64,") for value in kwargs["json"]["images"])
    assert "files" not in kwargs


def test_output_is_center_cropped_to_requested_ratio(monkeypatch):
    def fake_post(url, headers, **kwargs):
        return FakeResponse(make_png(900, 1600))

    monkeypatch.setattr("backend.generators.image_api.requests.post", fake_post)

    result = make_generator().generate_image("test poster", aspect_ratio="3:4")

    with Image.open(io.BytesIO(result)) as image:
        assert image.size == (900, 1200)
