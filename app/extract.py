"""Turn an uploaded file into plain text."""
from __future__ import annotations

import base64
import io
import mimetypes
from dataclasses import dataclass

from pypdf import PdfReader

IMAGE_TYPES = {"image/png", "image/jpeg", "image/webp", "image/gif", "image/bmp"}
TEXT_SUFFIXES = {".txt", ".md", ".csv", ".srt", ".vtt", ".json"}


@dataclass
class Extraction:
    text: str
    kind: str
    image_data_url: str | None = None


def _guess_type(filename: str, content_type: str | None) -> str:
    if content_type and content_type != "application/octet-stream":
        return content_type
    return mimetypes.guess_type(filename)[0] or "application/octet-stream"


def local_ocr(data: bytes, languages: str = "eng") -> str:
    """Best-effort OCR with tesseract; returns '' when unavailable."""
    try:
        import pytesseract
        from PIL import Image

        return pytesseract.image_to_string(Image.open(io.BytesIO(data)), lang=languages).strip()
    except Exception:
        return ""


def extract(filename: str, content_type: str | None, data: bytes, ocr_lang: str = "eng") -> Extraction:
    mime = _guess_type(filename, content_type)
    suffix = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if mime in IMAGE_TYPES or suffix in {".png", ".jpg", ".jpeg", ".webp"}:
        data_url = f"data:{mime if mime in IMAGE_TYPES else 'image/png'};base64,{base64.b64encode(data).decode()}"
        return Extraction(text=local_ocr(data, ocr_lang), kind="image", image_data_url=data_url)

    if mime == "application/pdf" or suffix == ".pdf":
        reader = PdfReader(io.BytesIO(data))
        pages = [page.extract_text() or "" for page in reader.pages[:30]]
        return Extraction(text="\n\n".join(pages).strip(), kind="pdf")

    if mime.startswith("text/") or suffix in TEXT_SUFFIXES:
        return Extraction(text=data.decode("utf-8", errors="replace").strip(), kind="text")

    raise ValueError(f"Unsupported file type: {mime or suffix or 'unknown'}")
