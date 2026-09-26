import io

from fastapi.testclient import TestClient
from PIL import Image

from app.extract import extract
from app.main import app
from app.spell import spell
from app.themes import CHARACTERS, THEMES, persona_for

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


def test_config_lists_themes_and_characters():
    body = client.get("/api/config").json()
    assert {theme["id"] for theme in body["themes"]} == {"ocean", "sakura", "magic"}
    assert all(theme["characters"] for theme in body["themes"])


def test_theme_assets_exist():
    from pathlib import Path

    root = Path(__file__).resolve().parent.parent
    for theme in THEMES:
        assert (root / theme["background"].lstrip("/")).exists()
        for character in theme["characters"]:
            assert (root / character["image"].lstrip("/")).exists()


def test_persona_for_known_and_unknown():
    assert "Kaito" in persona_for("pirate-boy")
    assert persona_for("nobody") == ""
    assert len(CHARACTERS) == 6


def test_spell_japanese_kana_and_kanji():
    result = spell("きゃべつ", "ja")
    assert [letter["char"] for letter in result["letters"]] == ["きゃ", "べ", "つ"]
    assert result["letters"][0]["reading"] == "kya"
    assert spell("猫", "ja")["letters"][0]["script"] == "kanji"


def test_spell_endpoint_hangul_and_latin():
    body = client.post("/api/spell", json={"word": "한국", "target_lang": "ko"}).json()
    assert body["letters"][0]["reading"] == "han"
    latin = client.post("/api/spell", json={"word": "casa", "target_lang": "es"}).json()
    assert [letter["char"] for letter in latin["letters"]] == list("casa")


def test_spell_converts_typed_romaji_to_kana():
    from app.spell import romaji_to_kana

    assert romaji_to_kana("neko") == "ねこ"
    assert romaji_to_kana("shashin") == "しゃしん"
    assert romaji_to_kana("kitte") == "きって"
    result = spell("neko", "ja")
    assert result["word"] == "ねこ"
    assert result["romaji"] == "ne · ko"


def test_spell_yoon_reading_uses_standard_romaji():
    assert spell("しゃしん", "ja")["romaji"] == "sha · shi · n"


def test_spell_romaji_line_skips_kanji():
    result = spell("猫が好き", "ja")
    assert result["romaji"] == "ga · ki"
