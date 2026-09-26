import io

from fastapi.testclient import TestClient
from PIL import Image

from app.extract import extract
from app.main import app

client = TestClient(app)


def png_bytes() -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (40, 20), "white").save(buffer, format="PNG")
    return buffer.getvalue()


def test_config_lists_languages():
    body = client.get("/api/config").json()
    assert {lang["code"] for lang in body["languages"]} >= {"ja", "en"}


def test_extract_text_file():
    result = extract("notes.txt", "text/plain", "毎朝六時に起きます。".encode())
    assert result.kind == "text"
    assert "毎朝" in result.text


def test_extract_image_returns_data_url():
    result = extract("shot.png", "image/png", png_bytes())
    assert result.kind == "image"
    assert result.image_data_url.startswith("data:image/png;base64,")


def test_extract_rejects_unknown_type():
    try:
        extract("clip.mp4", "video/mp4", b"\x00\x01")
    except ValueError as exc:
        assert "Unsupported" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_scan_rejects_empty_upload():
    response = client.post("/api/scan", files={"file": ("empty.txt", b"", "text/plain")})
    assert response.status_code == 400


def test_scan_demo_mode_without_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    response = client.post(
        "/api/scan",
        files={"file": ("lesson.txt", "毎朝六時に起きます。\n学校へ行きます。".encode(), "text/plain")},
        data={"target_lang": "ja", "native_lang": "en"},
    )
    body = response.json()
    assert response.status_code == 200
    assert body["demo"] is True
    assert body["notes"]
