from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import uuid

# --- 1. CORE DATA STRUCTURES ---
# These models define the core data structures returned by the LLM service.
# They are imported and used by llm_service.py, main.py, and models.py,
# making this file the Single Source of Truth for our data contracts.

class PersonalInfo(BaseModel):
    name: str

class Skill(BaseModel):
    name: str
    level: Optional[str] = None

class ExtractedProfile(BaseModel):
    """The detailed, validated structure of a user's profile extracted from a CV."""
    personal_info: PersonalInfo
    skills: List[Skill]
    experience_years: int = Field(0, alias="years_of_experience")
    contact_email: Optional[str] = None

class CareerAdvice(BaseModel):
    """The detailed, validated structure of the career advice content."""
    identified_skill_gaps: List[str]
    suggested_portfolio_projects: List[str]
    personalized_learning_path: List[Dict[str, Any]] # A list of weekly plans can still be flexible

class CareerAdviceResponse(BaseModel):
    """The complete advice object, including metadata like scores."""
    career_advice: CareerAdvice
    role_fit_score: Optional[int] = None

class ResourceRecommendation(BaseModel):
    """The detailed, validated structure for a resource recommendation."""
    recommended_title: str
    recommended_url: str
    reason: str


# --- 2. API REQUEST & RESPONSE SCHEMAS ---
# These schemas define the exact structure of what the client sends and receives.

# --- CV & Profile ---
class ProfileAnalysisRequest(BaseModel):
    """Request body to analyze the raw text of a CV."""
    cv_text: str

class ProfileAnalysisResponse(BaseModel):
    """Response containing the structured profile extracted from the CV."""
    # We now return the strongly-typed ExtractedProfile object.
    profile: ExtractedProfile


# --- Career Path ---
class AdviceRequest(BaseModel):
    """Request body for generating a personalized career plan."""
    # The client must send a profile that matches the ExtractedProfile structure.
    profile: ExtractedProfile
    role: str
    level: str

class AdviceResponse(BaseModel):
    """Response containing the full, generated career advice plan."""
    # We now return the strongly-typed CareerAdviceResponse object.
    advice: CareerAdviceResponse

class RoleValidationRequest(BaseModel):
    """Request body to check the role suitability for the task."""
    role: str

class RoleValidationResponse(BaseModel):
    """Response containing the result of the role validation."""
    is_in_scope: bool
    reason: str

class CVUploadResponse(BaseModel):
    """Response containing the raw text extracted from an uploaded CV."""
    filename: str
    text: str


# --- User Progress ---
# This reflects the client-facing contract for creating and retrieving progress.
class UserProgressCreate(BaseModel):
    """Schema for creating a new user progress entry via the API."""
    # The client sends the full advice object it received.
    advice: CareerAdviceResponse = Field(..., alias='advice')

class UserProgressUpdate(BaseModel):
    """Schema for updating the completed weeks for a user."""
    completed_weeks: List[int] = Field(..., alias='completedWeeks')

class UserProgressResponse(BaseModel):
    """Schema for returning user progress data to the client."""
    # The server generates the ID and sends it back to the client.
    id: uuid.UUID
    advice: CareerAdviceResponse
    completed_weeks: List[int]

    class Config:
        # Allows Pydantic to create this model from a database object (ORM object).
        from_attributes = True

class RAGDocument(BaseModel):
    """Schema for validating documents loaded from JSON for the RAG database."""
    title: str
    url: str
    content: str
    source_file: str = "unknown"