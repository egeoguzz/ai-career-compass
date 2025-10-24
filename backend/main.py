from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from cv_parser import extract_text_from_docx, extract_text_from_pdf
from dotenv import load_dotenv
from pydantic import BaseModel
from llm_utils import extract_profile_from_cv, generate_career_advice
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class OnboardingData(BaseModel):
    role: str
    level: str

class ProfileInput(BaseModel):
    profile: dict
    role: str
    level: str

@app.post("/upload_cv")
async def upload_cv(file: UploadFile = File(...)):
    contents = await file.read()

    if file.filename.endswith(".pdf"):
        text = extract_text_from_pdf(contents)
    elif file.filename.endswith(".docx"):
        text = extract_text_from_docx(contents)
    else:
        raise HTTPException(status_code=400, detail="Unsupported file type. Please use PDF or DOCX.")

    return {
        "filename": file.filename,
        "text": text
    }

@app.post("/analyze_profile")
async def analyze_profile(data: dict):
    cv_text = data.get("cv_text", "")
    if not cv_text:
        raise HTTPException(status_code=400, detail="CV text is required.")

    result = extract_profile_from_cv(cv_text)
    return {"profile": result}

@app.post("/generate_advice")
async def generate_advice(data: ProfileInput):
    try:
        result = generate_career_advice(data.profile, data.role, data.level)
        return {"advice": result}
    except Exception as e:
        print("Error generating advice:", e)
        raise HTTPException(status_code=500, detail="Failed to generate advice.")