import asyncio
import logging
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session

# --- Project Module Imports ---
# Import robust services, schemas, models, and exceptions
from cv_parser import parse_cv, CVParserError
from llm_service import LLMService, LLMServiceError
from rag_service import RAGService, RAGServiceError
from database import get_session, create_db_and_tables
from models import UserProgress
import schemas

# --- 1. Service Initialization (Fail-Fast at Startup) ---
# Services are instantiated ONCE when the module is loaded.
# If any service fails to initialize (e.g., missing API key, DB not found),
# the entire application will fail to start. This is the desired behavior.
try:
    llm_service = LLMService()
    rag_service = RAGService()
except (LLMServiceError, RAGServiceError) as e:
    logging.critical(f"A critical service failed to initialize: {e}")
    # In a real-world scenario, you might exit or prevent the app from being served.
    raise


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Handles application startup: database initialization."""
    logging.info("Application startup: Initializing database...")
    create_db_and_tables()
    logging.info("Database initialized successfully.")
    yield
    logging.info("Application shutdown.")


# --- 2. FastAPI App Instantiation & Dependencies ---
app = FastAPI(
    title="AI Career Compass API",
    description="A service to analyze CVs and generate personalized career roadmaps.",
    version="2.0.0",  # Version bump to reflect major refactoring
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    # In production, restrict this to your actual frontend URL
    allow_origins=["http://localhost:3000", "YOUR_FRONTEND_URL"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Dependencies to provide service singletons to endpoints
def get_llm_service():
    return llm_service


def get_rag_service():
    return rag_service


# --- 3. API Endpoints (Refactored and Hardened) ---

@app.post("/cv/parse", response_model=schemas.CVUploadResponse, tags=["1. CV Processing"])
async def parse_cv_endpoint(file: UploadFile = File(...)):
    """Uploads a CV (PDF or DOCX) and extracts its text content."""
    try:
        contents = await file.read()
        # Use the robust, centralized parser function
        text = parse_cv(file.filename, contents)
        return {"filename": file.filename, "text": text}
    except CVParserError as e:
        raise HTTPException(status_code=422, detail=str(e))  # Unprocessable Entity


@app.post("/profile/extract", response_model=schemas.ProfileAnalysisResponse, tags=["1. CV Processing"])
async def extract_profile_endpoint(
        data: schemas.ProfileAnalysisRequest,
        llm: LLMService = Depends(get_llm_service)
):
    """Takes raw CV text and uses an LLM to parse it into a structured profile."""
    try:
        # Offload the synchronous, CPU-bound LLM call to a thread
        profile_model = await asyncio.to_thread(llm.extract_profile_from_cv, data.cv_text)
        return {"profile": profile_model}
    except LLMServiceError as e:
        raise HTTPException(status_code=503, detail=f"AI service error: {e}")


@app.post("/advice/generate", response_model=schemas.AdviceResponse, tags=["2. Career Path"])
async def generate_advice_endpoint(
        data: schemas.AdviceRequest,
        llm: LLMService = Depends(get_llm_service),
        rag: RAGService = Depends(get_rag_service)
):
    """Validates the role, then generates a full career advice plan."""
    try:
        # 1. Generate the base career plan
        advice_response = await asyncio.to_thread(
            llm.generate_career_advice, data.profile, data.role, data.level
        )
        plan = advice_response.career_advice

        # 2. Concurrently fetch resources for all learning objectives
        tasks = []
        for week in plan.personalized_learning_path:
            for objective in week.get("learning_objectives", []):
                # Correctly wrap the synchronous call in to_thread for each task
                tasks.append(asyncio.to_thread(rag.query_sources, objective, k=2))

        if tasks:
            rag_results = await asyncio.gather(*tasks, return_exceptions=True)

            # 3. Carefully merge RAG results back into the plan
            result_index = 0
            for week in plan.personalized_learning_path:
                week["resources"] = []  # Ensure the key exists
                for _ in week.get("learning_objectives", []):
                    if result_index < len(rag_results):
                        result = rag_results[result_index]
                        if isinstance(result, list):
                            week["resources"].extend(result)
                        else:  # An exception was caught by gather
                            logging.error(f"RAG query failed for an objective in week {week.get('week')}: {result}")
                        result_index += 1

        return {"advice": advice_response}

    except LLMServiceError as e:
        raise HTTPException(status_code=503, detail=f"AI service error during advice generation: {e}")
    except Exception as e:
        logging.error(f"Unexpected error in advice generation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An unexpected internal error occurred.")


@app.post("/progress", response_model=schemas.UserProgressResponse, status_code=201, tags=["3. User Progress"])
async def create_user_progress(
        progress_data: schemas.UserProgressCreate,
        session: Session = Depends(get_session)
):
    """Creates a new user progress entry and returns its unique ID."""
    new_progress = UserProgress.model_validate(progress_data)  # Create DB model from schema
    session.add(new_progress)
    session.commit()
    session.refresh(new_progress)
    return new_progress


@app.get("/progress/{progress_id}", response_model=schemas.UserProgressResponse, tags=["3. User Progress"])
async def get_user_progress(progress_id: uuid.UUID, session: Session = Depends(get_session)):
    """Retrieves a user's progress using their unique ID."""
    user_progress = session.get(UserProgress, progress_id)
    if not user_progress:
        raise HTTPException(status_code=404, detail="Progress not found for the given ID.")
    return user_progress


@app.put("/progress/{progress_id}", response_model=schemas.UserProgressResponse, tags=["3. User Progress"])
async def update_user_progress(
        progress_id: uuid.UUID,
        update_data: schemas.UserProgressUpdate,
        session: Session = Depends(get_session)
):
    """Updates the completed weeks for a user."""
    user_progress = session.get(UserProgress, progress_id)
    if not user_progress:
        raise HTTPException(status_code=404, detail="Progress not found for the given ID.")

    user_progress.completed_weeks = update_data.completed_weeks
    session.add(user_progress)
    session.commit()
    session.refresh(user_progress)
    return user_progress


@app.post(
    "/role/validate",
    response_model=schemas.RoleValidationResponse,
    tags=["0. Pre-flight Checks"]
)
async def validate_role_endpoint(
        data: schemas.RoleValidationRequest,
        llm: LLMService = Depends(get_llm_service)
):
    """
    Checks if a user-provided role is within the application's scope.
    This is used for real-time validation on the frontend.
    """
    try:
        validation_result = await asyncio.to_thread(
            llm.validate_role_is_in_scope, data.role
        )
        return validation_result

    except LLMServiceError as e:
        raise HTTPException(status_code=503, detail=f"AI service error: {e}")