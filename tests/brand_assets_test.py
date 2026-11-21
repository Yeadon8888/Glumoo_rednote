from io import BytesIO
from PIL import Image


def test_brand_asset_upload_list_and_read(client, tmp_path, monkeypatch):
    monkeypatch.setenv("HISTORY_DIR", str(tmp_path))

    content = BytesIO()
    Image.new("RGB", (640, 960), "blue").save(content, "PNG")
    original = content.getvalue()
    upload = client.post(
        "/api/brand-assets",
        data={"images": (BytesIO(original), "product.png")},
        content_type="multipart/form-data",
    )

    assert upload.status_code == 201
    asset = upload.get_json()["assets"][0]
    assert asset["filename"].endswith(".png")

    listing = client.get("/api/brand-assets")
    assert listing.status_code == 200
    assert listing.get_json()["assets"][0]["filename"] == asset["filename"]

    image = client.get(asset["url"])
    assert image.status_code == 200
    assert image.data == original
    preview = client.get(asset["url"] + "?preview=1")
    assert preview.mimetype == "image/jpeg"
    assert max(Image.open(BytesIO(preview.data)).size) == 320
    cached = client.get(asset["url"] + "?preview=1", headers={"If-None-Match": preview.headers["ETag"]})
    assert cached.status_code == 304


def test_invalid_upload_does_not_leave_an_asset(client, tmp_path, monkeypatch):
    monkeypatch.setenv("HISTORY_DIR", str(tmp_path))
    result = client.post("/api/brand-assets", data={"images": (BytesIO(b"invalid"), "photo.png")})
    assert result.status_code == 400
    assert client.get("/api/brand-assets").get_json()["assets"] == []
