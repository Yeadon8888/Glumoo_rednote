from io import BytesIO


def test_brand_asset_upload_list_and_read(client, tmp_path, monkeypatch):
    monkeypatch.setenv("HISTORY_DIR", str(tmp_path))

    upload = client.post(
        "/api/brand-assets",
        data={"images": (BytesIO(b"fake-image"), "product.png")},
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
    assert image.data == b"fake-image"
