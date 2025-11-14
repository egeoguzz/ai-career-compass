
from __future__ import annotations
from typing import List, Dict, Any
from openai import OpenAI, OpenAIError
from pydantic import ValidationError
from schemas import ExtractedProfile, CareerAdviceResponse, ResourceRecommendation
import json
import logging
import functools
import os

# Import the single source of truth for configuration
from config import settings

logger = logging.getLogger(__name__)

# --- 1. CUSTOM EXCEPTION ---
class LLMServiceError(Exception):
    """Custom exception for all LLM Service related errors."""
    pass

# --- REBUILT DECORATOR FOR ROBUST LLM INTERACTION ---
def handle_llm_errors(func):
    @functools.wraps(func)
    def wrapper(self: 'LLMService', *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except (OpenAIError, IOError) as e:
            logger.error(f"API or File error in '{func.__name__}': {e}")
            raise LLMServiceError(f"A remote API or file system error occurred: {e}")
        except (json.JSONDecodeError, ValidationError) as e:
            logger.error(f"LLM response validation failed in '{func.__name__}': {e}")
            raise LLMServiceError("The LLM returned an invalid or unexpected data structure.")
        except Exception as e:
            logger.error(f"An unexpected error occurred in '{func.__name__}': {e}", exc_info=True)
            raise LLMServiceError("An unexpected internal error occurred.")
    return wrapper

# --- CORE SERVICE CLASS ---
class LLMService:
    def __init__(self):
        if not settings.GROQ_API_KEY:
            logger.critical("GROQ_API_KEY is not set in environment variables.")
            # Fail fast and loud.
            raise ValueError("API key for LLM service is missing.")
        try:
            self.client = OpenAI(api_key=settings.GROQ_API_KEY, base_url=settings.LLM_BASE_URL)
            self.client.models.list()  # Make a simple test call to validate credentials
            logger.info("LLMService initialized and connection verified successfully.")
        except OpenAIError as e:
            logger.critical(f"OpenAI client could not be initialized or authenticated. Error: {e}")
            raise LLMServiceError(f"Failed to connect to LLM provider: {e}")

    def _load_prompt_template(self, filename: str) -> str:
        filepath = os.path.join(settings.PROMPTS_PATH, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            logger.error(f"Prompt file not found: {filepath}")
            raise  # Re-raise to be caught by the decorator
        except IOError as e:
            logger.error(f"Could not read prompt file: {filepath}. Error: {e}")
            raise # Re-raise

    @handle_llm_errors
    def extract_profile_from_cv(self, cv_text: str) -> ExtractedProfile:
        logger.info("Starting profile extraction from CV.")
        template = self._load_prompt_template('extract_profile_from_cv.txt')
        prompt = template.format(cv_text=cv_text)

        response = self.client.chat.completions.create(
            model=settings.MODEL_PROFILE_EXTRACTION,
            messages=[{"role": "user", "content": prompt}],
            temperature=settings.TEMPERATURE_PROFILE_EXTRACTION,
            response_format={"type": "json_object"}
        )
        content = response.choices[0].message.content
        return ExtractedProfile.model_validate_json(content)

    @handle_llm_errors
    def generate_career_advice(self, profile: ExtractedProfile, role: str, level: str) -> CareerAdviceResponse:
        logger.info(f"Generating career advice for role: {role}")
        template = self._load_prompt_template('generate_career_advice.txt')
        # Pass the Pydantic object, serialize to JSON inside the method.
        profile_json = profile.model_dump_json(indent=2)
        prompt = template.format(profile_json=profile_json, role=role, level=level)

        response = self.client.chat.completions.create(
            model=settings.MODEL_CONTENT_GENERATION,
            messages=[{"role": "user", "content": prompt}],
            temperature=settings.TEMPERATURE_CONTENT_GENERATION,
            response_format={"type": "json_object"}
        )
        content = response.choices[0].message.content
        return CareerAdviceResponse.model_validate_json(content)

    @handle_llm_errors
    def generate_resource_recommendation(self, learning_objective: str, sources: List[Dict[str, Any]]) -> ResourceRecommendation:
        logger.info(f"Generating resource recommendation for: '{learning_objective}'")
        if not sources:
            logger.warning(f"No sources provided for learning objective: '{learning_objective}'")
            # Return a default, valid object instead of None or erroring
            return ResourceRecommendation(
                recommended_title="No Relevant Resources Found",
                recommended_url="#",
                reason="No internal resources were available to analyze for this topic."
            )

        source_texts = [f"Title: {s.get('title', 'N/A')}\nContent: {s.get('content', '')[:1000]}" for s in sources]
        source_text = "\n\n".join(source_texts)
        template = self._load_prompt_template('generate_resource_recommendation.txt')
        prompt = template.format(learning_objective=learning_objective, source_text=source_text)

        response = self.client.chat.completions.create(
            model=settings.MODEL_CONTENT_GENERATION,
            messages=[{"role": "user", "content": prompt}],
            temperature=settings.TEMPERATURE_CONTENT_GENERATION,
            response_format={"type": "json_object"}
        )
        content = response.choices[0].message.content
        return ResourceRecommendation.model_validate_json(content)

    @handle_llm_errors
    def validate_role_is_in_scope(self, role: str) -> Dict[str, Any]:
        """
        Uses an LLM to check if the user's target role is within the app's scope.
        """
        logger.info(f"Validating scope for role: '{role}'")
        template = self._load_prompt_template('validate_role_scope.txt')
        prompt = template.format(role=role)

        response = self.client.chat.completions.create(
            model=settings.MODEL_CONTENT_GENERATION,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            response_format={"type": "json_object"}
        )
        content = response.choices[0].message.content
        return json.loads(content)