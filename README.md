# LinguaScan

Upload a screenshot, photo, PDF, or text file of the language material you're studying and get back a
study pack: a summary, notes to copy into your notebook, a vocabulary table, and practice questions
that are graded with feedback.

- Target language, explanation language, and level are selectable (Japanese, Chinese, Korean, Spanish,
  French, German, Italian, Portuguese, Russian, Hindi, Arabic, English).
- Images are read by the vision model directly; local Tesseract OCR is used as a hint and as a fallback.
- Short-answer questions are graded by the model, which accepts different wording and corrects mistakes.
- Pick an anime world (background) and an instructor character; the instructor's voice is used in the study pack.
- Spelling help breaks a word into characters with per-character readings, converts typed romaji to kana,
  and speaks the word with the browser's speech synthesis.

## Run locally

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
export OPENAI_API_KEY=sk-...
.venv/bin/uvicorn app.main:app --reload --port 8000
```

Open http://localhost:8000.

System dependency for local OCR (optional but recommended):

```bash
sudo apt-get install -y tesseract-ocr tesseract-ocr-jpn
```

Without `OPENAI_API_KEY` the app runs in demo mode: it OCRs the upload and builds a placeholder pack
locally, with no AI summary or grading.

## Layout

| Path | Purpose |
| --- | --- |
| `app/main.py` | FastAPI routes: `/api/config`, `/api/scan`, `/api/grade`, `/api/spell` |
| `app/themes.py` | Anime worlds and their instructor characters |
| `app/spell.py` | Character-by-character spelling and reading help (kana, hangul, cyrillic, latin) |
| `app/extract.py` | File → text (image OCR, PDF, plain text) |
| `app/analyze.py` | Prompting and JSON schema for the study pack, plus answer grading |
| `static/` | Single-page frontend (no build step) |
