import os
import io
import json
import sqlite3
from fastapi import FastAPI, UploadFile, File, Form, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse
import pdf2image
import pytesseract
from PIL import Image
from app.analyze import analyze_document_with_ai, generate_mascot_reply, dictionary_lookup

app = FastAPI()

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            mascot TEXT DEFAULT 'Ren',
            score INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

init_db()

@app.get("/")
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/api/auth/register")
async def register(username: str = Form(...), password: str = Form(...), mascot: str = Form("Ren")):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (username, password, mascot) VALUES (?, ?, ?)", (username, password, mascot))
        conn.commit()
        return {"status": "success", "username": username, "mascot": mascot}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Username already exists.")
    finally:
        conn.close()

@app.post("/api/auth/login")
async def login(username: str = Form(...), password: str = Form(...)):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT username, mascot, score FROM users WHERE username = ? AND password = ?", (username, password))
    user = cursor.fetchone()
    conn.close()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials.")
    return {"status": "success", "username": user[0], "mascot": user[1], "score": user[2]}

@app.post("/scan")
async def scan(
    file: UploadFile = File(...),
    target_lang: str = Form(...),
    native_lang: str = Form(...),
    user_level: str = Form(...),
    instructor_name: str = Form(...)
):
    if not os.environ.get("OPENAI_API_KEY"):
        raise HTTPException(status_code=500, detail="API key is not configured on the server.")

    try:
        contents = await file.read()
        extracted_text = ""

        if file.filename.lower().endswith(".pdf"):
            images = pdf2image.convert_from_bytes(contents)
            for img in images:
                extracted_text += pytesseract.image_to_string(img) + "\n"
        else:
            image = Image.open(io.BytesIO(contents))
            extracted_text = pytesseract.image_to_string(image)

        if not extracted_text.strip():
            return JSONResponse(status_code=400, content={"detail": "Could not extract text from document."})

        study_pack = analyze_document_with_ai(
            extracted_text=extracted_text,
            target_lang=target_lang,
            native_lang=native_lang,
            user_level=user_level,
            instructor_name=instructor_name
        )
        return study_pack

    except Exception as e:
        return JSONResponse(status_code=500, content={"detail": str(e)})

@app.post("/api/chat")
async def chat_with_mascot(request: Request):
    data = await request.json()
    messages = data.get("messages", [])
    mascot_name = data.get("mascot", "Ren")
    target_lang = data.get("target_lang", "Japanese")
    doc_context = data.get("document_context")

    reply = generate_mascot_reply(messages, mascot_name, target_lang, doc_context)
    return {"reply": reply}

@app.post("/api/dictionary")
async def dict_lookup(request: Request):
    data = await request.json()
    word = data.get("word")
    target_lang = data.get("target_lang", "Japanese")
    native_lang = data.get("native_lang", "English")

    result = dictionary_lookup(word, target_lang, native_lang)
    return result