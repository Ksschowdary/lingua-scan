from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import analyze
from .extract import extract
from .languages import LANGUAGES, tesseract_for
from .spell import spell
from .themes import THEMES, persona_for

MAX_BYTES = 12 * 1024 * 1024
STATIC_DIR = Path(__file__).resolve().parent.parent / "static"

app = FastAPI(title="LinguaScan")


class GradeRequest(BaseModel):
    question: str
    expected: str
    given: str
    target_lang: str = "ja"
    native_lang: str = "en"


class SpellRequest(BaseModel):
    word: str
    target_lang: str = "ja"


@app.get("/api/config")
def config() -> dict:
    return {
        "languages": LANGUAGES,
        "themes": THEMES,
        "ai_enabled": analyze.has_key(),
        "model": analyze.MODEL,
    }


@app.post("/api/scan")
async def scan(
    file: UploadFile = File(...),
    target_lang: str = Form("ja"),
    native_lang: str = Form("en"),
    level: str = Form("beginner"),
    instructor: str = Form(""),
) -> dict:
    data = await file.read()
    if not data:
        raise HTTPException(400, "The uploaded file is empty.")
    if len(data) > MAX_BYTES:
        raise HTTPException(413, "File is larger than 12 MB.")

    try:
        extracted = extract(file.filename or "upload", file.content_type, data, tesseract_for(target_lang))
    except ValueError as exc:
        raise HTTPException(415, str(exc)) from exc

    if not os.environ.get("OPENAI_API_KEY"): 
        if not extracted.text:
            raise HTTPException(
                503,
                "No OPENAI_API_KEY is configured and no text could be read locally. "
                "Add an API key to scan images.",
            )
        return analyze.demo_pack(extracted.text, target_lang, native_lang)

    if extracted.kind != "image" and not extracted.text:
        raise HTTPException(422, "No readable text found in that file.")

    try:
        pack = analyze.analyze(
            text=extracted.text,
            image_data_url=extracted.image_data_url,
            target_lang=target_lang,
            native_lang=native_lang,
            level=level,
            persona=persona_for(instructor),
        )
    except Exception as exc:
        raise HTTPException(502, f"Analysis failed: {exc}") from exc
    pack["demo"] = False
    return pack


@app.post("/api/grade")
def grade_answer(req: GradeRequest) -> dict:
    try:
        return analyze.grade(
            question=req.question,
            expected=req.expected,
            given=req.given,
            target_lang=req.target_lang,
            native_lang=req.native_lang,
        )
    except Exception as exc:
        raise HTTPException(502, f"Grading failed: {exc}") from exc


@app.post("/api/spell")
def spell_word(req: SpellRequest) -> dict:
    return spell(req.word, req.target_lang)


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
