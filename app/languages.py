LANGUAGES = [
    {"code": "ja", "name": "Japanese", "tesseract": "jpn"},
    {"code": "zh", "name": "Chinese", "tesseract": "chi_sim"},
    {"code": "ko", "name": "Korean", "tesseract": "kor"},
    {"code": "es", "name": "Spanish", "tesseract": "spa"},
    {"code": "fr", "name": "French", "tesseract": "fra"},
    {"code": "de", "name": "German", "tesseract": "deu"},
    {"code": "it", "name": "Italian", "tesseract": "ita"},
    {"code": "pt", "name": "Portuguese", "tesseract": "por"},
    {"code": "ru", "name": "Russian", "tesseract": "rus"},
    {"code": "hi", "name": "Hindi", "tesseract": "hin"},
    {"code": "ar", "name": "Arabic", "tesseract": "ara"},
    {"code": "en", "name": "English", "tesseract": "eng"},
]

BY_CODE = {lang["code"]: lang for lang in LANGUAGES}


def name_for(code: str) -> str:
    return BY_CODE.get(code, {}).get("name", code)


def tesseract_for(code: str) -> str:
    return BY_CODE.get(code, {}).get("tesseract", "eng")
