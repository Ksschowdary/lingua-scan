"""LLM analysis of study material: summary, notes, and practice questions."""
from __future__ import annotations

import json
import os
import re
from typing import Any

from openai import OpenAI

from .languages import name_for

MODEL = os.getenv("LINGUA_MODEL", "gemini-3.8-flash")

STUDY_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["title", "detected_text", "summary", "key_points", "vocabulary", "grammar", "notes", "questions"],
    "properties": {
        "title": {"type": "string"},
        "detected_text": {"type": "string"},
        "summary": {"type": "string"},
        "key_points": {"type": "array", "items": {"type": "string"}},
        "vocabulary": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["term", "reading", "meaning", "example"],
                "properties": {
                    "term": {"type": "string"},
                    "reading": {"type": "string"},
                    "meaning": {"type": "string"},
                    "example": {"type": "string"},
                },
            },
        },
        "grammar": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["pattern", "explanation", "example"],
                "properties": {
                    "pattern": {"type": "string"},
                    "explanation": {"type": "string"},
                    "example": {"type": "string"},
                },
            },
        },
        "notes": {"type": "array", "items": {"type": "string"}},
        "questions": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["type", "prompt", "options", "answer", "explanation"],
                "properties": {
                    "type": {"type": "string", "enum": ["mcq", "short"]},
                    "prompt": {"type": "string"},
                    "options": {"type": "array", "items": {"type": "string"}},
                    "answer": {"type": "string"},
                    "explanation": {"type": "string"},
                },
            },
        },
    },
}


def has_key() -> bool:
    return bool(os.getenv("OPENAI_API_KEY"))


def _client() -> OpenAI:
    return OpenAI()


def _system_prompt(target: str, native: str, level: str, persona: str = "") -> str:
    voice = (
        f"You are {persona}. Stay in character in the summary and notes, but keep every fact accurate. "
        if persona
        else ""
    )
    return (
        voice + f"You are a patient {target} tutor for a {level} learner whose base language is {native}. "
        f"You receive study material (a photo, screenshot, PDF page, or text) and produce a study pack.\n"
        "Rules:\n"
        f"- detected_text: transcribe the {target} text from the material exactly as it appears; keep line breaks. "
        "If the material is an image, read it yourself; any OCR text provided is only a noisy hint.\n"
        f"- summary: 3-6 sentences in {native} explaining what the material is about and what it teaches.\n"
        f"- key_points: the main ideas, in {native}.\n"
        f"- vocabulary: 6-12 useful items from the material. term in {target}; reading = pronunciation "
        f"(kana/romaji/pinyin/IPA as appropriate, empty string if not applicable); meaning in {native}; "
        f"example = a short new sentence in {target} using the term.\n"
        f"- grammar: 2-5 patterns actually present in the material, explained in {native} with one example each.\n"
        f"- notes: 8-15 short lines the learner should handwrite in their notebook. Mix {target} and {native}; "
        "keep each line under ~90 characters so it is quick to copy.\n"
        f"- questions: 5-8 items testing this material, written in {target} where natural with {native} help in "
        "parentheses. Mix 'mcq' (4 options, answer must be one of the options verbatim) and 'short' (free "
        "answer; give the model answer). Always include the 'options' key — an empty array for short answers. "
        f"explanation: why the answer is right, in {native}.\n"
        "Never invent content that is not supported by the material."
    )


def analyze(
    *,
    text: str,
    image_data_url: str | None,
    target_lang: str,
    native_lang: str,
    level: str,
    persona: str = "",
) -> dict[str, Any]:
    target, native = name_for(target_lang), name_for(native_lang)
    content: list[dict[str, Any]] = []
    if image_data_url:
        content.append({"type": "image_url", "image_url": {"url": image_data_url, "detail": "high"}})
        hint = f"OCR hint (may be wrong):\n{text}" if text else "No OCR text available; read the image."
        content.append({"type": "text", "text": hint})
    else:
        content.append({"type": "text", "text": f"Study material:\n\n{text[:20000]}"})

    response = _client().chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": _system_prompt(target, native, level, persona)},
            {"role": "user", "content": content},
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {"name": "study_pack", "schema": STUDY_SCHEMA, "strict": True},
        },
        temperature=0.4,
    )
    return json.loads(response.choices[0].message.content)


def grade(*, question: str, expected: str, given: str, target_lang: str, native_lang: str) -> dict[str, Any]:
    if not has_key():
        normalized = re.sub(r"\s+", "", given.lower())
        ok = bool(normalized) and normalized in re.sub(r"\s+", "", expected.lower())
        return {
            "correct": ok,
            "score": 100 if ok else 0,
            "feedback": "Matched the model answer." if ok else f"Model answer: {expected}",
        }

    response = _client().chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    f"You grade a {name_for(target_lang)} learner's answer. Be encouraging but honest. "
                    f"Accept answers that differ in wording but are correct in meaning. "
                    f"Write feedback in {name_for(native_lang)}, 1-3 sentences, and point out any grammar or "
                    "spelling mistakes with the corrected form."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Question: {question}\nModel answer: {expected}\nLearner answer: {given}\n\n"
                    'Reply as JSON: {"correct": bool, "score": 0-100, "feedback": string}'
                ),
            },
        ],
        response_format={"type": "json_object"},
        temperature=0.2,
    )
    return json.loads(response.choices[0].message.content)


def demo_pack(text: str, target_lang: str, native_lang: str) -> dict[str, Any]:
    """Offline fallback when no API key is configured."""
    target = name_for(target_lang)
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    tokens: list[str] = []
    for line in lines:
        for token in re.split(r"[\s、。,.!?！？]+", line):
            if len(token) > 1 and token not in tokens:
                tokens.append(token)
    preview = " / ".join(lines[:3]) or "(no text could be read from the upload)"
    return {
        "title": f"{target} study pack (demo mode)",
        "detected_text": text,
        "summary": (
            "Demo mode: no OPENAI_API_KEY is configured, so this pack was built locally from OCR text "
            f"without AI analysis. The material starts with: {preview}"
        ),
        "key_points": lines[:5],
        "vocabulary": [
            {"term": token, "reading": "", "meaning": "(add meaning)", "example": ""} for token in tokens[:8]
        ],
        "grammar": [],
        "notes": lines[:12],
        "questions": [
            {
                "type": "short",
                "prompt": f"What does this line mean? {line}",
                "options": [],
                "answer": "(configure an API key for model answers)",
                "explanation": "",
            }
            for line in lines[:4]
        ],
        "demo": True,
    }
