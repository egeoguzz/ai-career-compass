from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from cv_parser import extract_text_from_docx, extract_text_from_pdf
from pydantic import BaseModel
from query_sources import query_sources
from llm_utils import extract_profile_from_cv, generate_career_advice, generate_resource_recommendation
from typing import List, Dict, Any, Optional


class LearningPathItem(BaseModel):
    week: int
    topic: str
    learning_objectives: List[str]
    project_idea: str


class UserProgress(BaseModel):
    adviceJson: Dict[str, Any]
    completedWeeks: Optional[List[int]] = []


db: Dict[str, UserProgress] = {}
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


class ResourceRequest(BaseModel):
    learning_objective: str


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


@app.post("/suggest_resources")
def suggest_resources(req: ResourceRequest):
    sources = query_sources(req.learning_objective)
    recommendation = generate_resource_recommendation(req.learning_objective, sources)
    return {"recommendation": recommendation}


@app.post("/users/{user_id}/progress")
async def save_user_progress(user_id: str, progress: UserProgress):
    db[user_id] = progress
    return {"message": "Progress saved successfully", "user_id": user_id}


@app.get("/users/{user_id}/progress")
async def load_user_progress(user_id: str):
    progress = db.get(user_id)
    if not progress:
        raise HTTPException(status_code=404, detail="No progress found for this user")
    return progress
