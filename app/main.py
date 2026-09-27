import os 
import io 
import json 
from fastapi import FastAPI, UploadFile, File, Form, Request, HTTPException 
from fastapi.staticfiles import StaticFiles 
from fastapi.templating import Jinja2Templates 
from fastapi.responses import JSONResponse 
import pdf2image 
import pytesseract 
from PIL import Image 
from app.analyze import analyze_document_with_ai 
 
app = FastAPI() 
 
app.mount("/static", StaticFiles(directory="app/static"), name="static") 
templates = Jinja2Templates(directory="app/templates") 
 
@app.get("/") 
async def read_root(request: Request): 
    return templates.TemplateResponse("index.html", {"request": request}) 
 
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
            return JSONResponse(status_code=400, content={"detail": "Could not extract text."}) 
 
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
