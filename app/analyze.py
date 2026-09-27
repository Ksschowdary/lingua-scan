import os
import json
import time
from openai import OpenAI

def get_ai_client():
    api_key = os.environ.get("OPENAI_API_KEY")
    base_url = os.environ.get("OPENAI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai/")
    return OpenAI(api_key=api_key, base_url=base_url)

def analyze_document_with_ai(extracted_text, target_lang, native_lang, user_level, instructor_name):
    client = get_ai_client()
    
    prompt = f"""
    You are an expert language tutor named {instructor_name}.
    Analyze the following extracted text from a language learning document.
    Target Language: {target_lang}
    Native Language: {native_lang}
    Learner Level: {user_level}

    Extracted Text:
    {extracted_text}

    Return a JSON object containing:
    1. "topic_title": A clear title for this lesson.
    2. "summary_notes": Array of key notes and concept explanations in {native_lang}.
    3. "vocabulary": Array of objects, each containing "word" (in {target_lang}), "reading" (phonetic/furigana/pinyin), "translation" (in {native_lang}), and "example" (sentence in {target_lang}).
    4. "grammar_points": Array of objects, each containing "pattern", "explanation", and "example".
    5. "quiz_questions": Array of objects, each containing "id" (1, 2, 3...), "question", "options" (array of 4 strings), "correct_answer", and "hint".
    """

    for attempt in range(3):
        try:
            response = client.chat.completions.create(
                model="gemini-3.8-flash",
                messages=[
                    {"role": "system", "content": "You are a helpful AI language tutor. Always output valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            if attempt == 2:
                raise e
            time.sleep(2)

def generate_mascot_reply(messages, mascot_name, target_lang, document_context=None):
    client = get_ai_client()
    
    mascot_personas = {
        "Ren": "You are Ren, an energetic anime rival mascot! You are super encouraging, competitive, and hype up the user.",
        "Aoi": "You are Aoi, a calm and polite sensei mascot. You give detailed, patient explanations and gentle encouragement.",
        "Kuro": "You are Kuro, a witty and playful mascot. You love clever puns, fun hints, and lighthearted teasing."
    }
    
    system_instruction = mascot_personas.get(mascot_name, mascot_personas["Ren"])
    system_instruction += f"\nThe user is learning {target_lang}. Keep responses conversational, short, and in-character."
    
    if document_context:
        system_instruction += f"\nDocument Context for Quiz Mode:\n{json.dumps(document_context)}"

    formatted_messages = [{"role": "system", "content": system_instruction}] + messages

    response = client.chat.completions.create(
        model="gemini-3.8-flash",
        messages=formatted_messages
    )
    return response.choices[0].message.content

def dictionary_lookup(word, target_lang, native_lang):
    client = get_ai_client()
    prompt = f"""
    Translate and break down the word/phrase '{word}' for a learner.
    Input Language: English / {native_lang}
    Target Language: {target_lang}

    Return JSON with:
    - "word": Word in {target_lang}
    - "reading": Pronunciation / Phonetics / Reading
    - "meaning": Meaning in {native_lang}
    - "example_target": Example sentence in {target_lang}
    - "example_native": Example sentence translation in {native_lang}
    """
    response = client.chat.completions.create(
        model="gemini-3.8-flash",
        messages=[
            {"role": "system", "content": "Return valid JSON."},
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"}
    )
    return json.loads(response.choices[0].message.content)