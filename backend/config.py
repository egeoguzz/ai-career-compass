import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

# Determine the absolute path of the project's backend directory
# This makes all path configurations robust and independent of where you run the script from.
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))


class Settings(BaseSettings):
    """
    Manages all application settings using environment variables and a .env file.
    This class provides a single, validated source of truth for configuration.
    """

    # --- RAG and Vector DB Settings ---
    # Path to the directory containing JSON files for the RAG system.
    RAG_DATA_PATH: str = os.path.join(BACKEND_DIR, "rag_data")

    # Path where the ChromaDB persistent database is stored.
    CHROMA_DB_PATH: str = os.path.join(BACKEND_DIR, "chroma_db")

    # The name of the collection within ChromaDB. Must be consistent.
    RAG_COLLECTION_NAME: str = "career_sources"

    # The name of the sentence-transformer model for creating embeddings.
    EMBEDDING_MODEL_NAME: str = "all-MiniLM-L6-v2"

    # --- LLM Service Settings ---
    # The API key for the LLM provider (e.g., Groq).
    # This value MUST be set in your .env file. It has no default.
    GROQ_API_KEY: Optional[str] = None

    # The base URL for the LLM provider's API.
    LLM_BASE_URL: str = "https://api.groq.com/openai/v1"

    # The specific model to use for complex CV data extraction.
    MODEL_PROFILE_EXTRACTION: str = "llama-3.3-70b-versatile"

    # A faster, more efficient model for generating structured content.
    MODEL_CONTENT_GENERATION: str = "llama-3.1-8b-instant"

    # Temperature setting for the extraction model (low for factual tasks).
    TEMPERATURE_PROFILE_EXTRACTION: float = 0.2

    # Temperature setting for content generation (slightly higher for creativity).
    TEMPERATURE_CONTENT_GENERATION: float = 0.4

    # Absolute path to the directory containing LLM prompt templates.
    PROMPTS_PATH: str = os.path.join(BACKEND_DIR, "prompts")

    # Pydantic Settings Configuration
    model_config = SettingsConfigDict(
        # Load environment variables from a .env file.
        env_file=".env",
        # Specify the encoding of the .env file.
        env_file_encoding='utf-8',
        # Pydantic is case-insensitive when reading from env vars, which is helpful.
    )


# Create a single, importable instance of the settings to be used across the app.
settings = Settings()