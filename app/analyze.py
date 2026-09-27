import os
import json
import time
from openai import OpenAI

def analyze_document_with_ai(extracted_text: str, target_lang: str, native_lang: str, user_level: str, instructor_name: str) -> dict:
    base_url = os.environ.get("OPENAI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai/")
    api_key = os.environ.get("OPENAI_API_KEY")
    
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is not set.")

    client = OpenAI(
        base_url=base_url,
        api_key=api_key
    )

    system_prompt = f"""You are {instructor_name}, a language tutor teaching {target_lang} to a {user_level} level student whose native language is {native_lang}.
Analyze the provided document text and create a structured study pack in valid JSON format.

JSON structure required:
{{
    "title": "Title of the lesson/study pack",
    "summary": "Brief summary of the document text",
    "vocabulary": [
        {{
            "term": "Word in {target_lang}",
            "reading": "Pronunciation/Furigana/Romaji",
            "meaning": "Meaning in {native_lang}",
            "example": "Example sentence in {target_lang}",
            "example_translation": "Example sentence translation in {native_lang}"
        }}
    ],
    "grammar_points": [
        {{
            "point": "Grammar rule or pattern",
            "explanation": "Explanation in {native_lang}",
            "example": "Example in {target_lang}"
        }}
    ],
    "exercises": [
        {{
            "question": "Practice question",
            "options": ["Option A", "Option B", "Option C", "Option D"],
            "answer": "Correct option",
            "explanation": "Explanation in {native_lang}"
        }}
    ]
}}
Respond ONLY with raw JSON. No markdown backticks or commentary.
"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Document text to analyze:\n\n{extracted_text}"}
    ]

    max_retries = 3
    response_text = ""

    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model="gemini-3.8-flash",
                messages=messages
            )
            response_text = response.choices[0].message.content
            break
        except Exception as e:
            if ("503" in str(e) or "UNAVAILABLE" in str(e)) and attempt < max_retries - 1:
                time.sleep(2 * (attempt + 1))
                continue
            raise e

    # Clean potential markdown block formatting
    if response_text.startswith("```"):
        lines = response_text.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        response_text = "\n".join(lines)

    return json.loads(response_text)