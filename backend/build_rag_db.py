import os
import json
import glob
import chromadb
import logging
from typing import List
from pydantic import ValidationError

# Import centralized configuration and data schemas
from config import settings
from schemas import RAGDocument

# --- 1. SETUP ---
# Configure logging to get logger by name, which is a best practice.
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def load_and_validate_documents(path: str) -> List[RAGDocument]:
    """
    Loads all JSON files from a directory, validates their content against the
    RAGDocument schema, and returns a list of valid document objects.
    """
    validated_docs: List[RAGDocument] = []
    json_files = glob.glob(os.path.join(path, "*.json"))
    logger.info(f"Found {len(json_files)} JSON source files in '{path}'.")

    for file_path in json_files:
        file_name = os.path.basename(file_path)
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if not isinstance(data, list):
                    logger.warning(f"Skipping file '{file_name}': content is not a JSON list.")
                    continue

                for i, doc_dict in enumerate(data):
                    if isinstance(doc_dict, dict):
                        # Add metadata about the source file for better traceability
                        doc_dict['source_file'] = file_name
                        # Validate and create the Pydantic model
                        validated_docs.append(RAGDocument(**doc_dict))
                    else:
                        logger.warning(f"Skipping item #{i} in '{file_name}': it's not a valid object.")

        except json.JSONDecodeError:
            logger.error(f"Failed to decode JSON from '{file_name}'. Please check for syntax errors.")
        except ValidationError as e:
            logger.error(f"Data validation failed for file '{file_name}'. Please check schema. Details: {e}")
        except Exception as e:
            logger.error(f"An unexpected error occurred while processing '{file_name}': {e}", exc_info=True)

    return validated_docs


def main():
    """
    Main function to build or rebuild the ChromaDB vector database.
    This script is designed to be idempotent.
    """
    logger.info("--- Starting RAG Vector Database Build Process ---")

    if not os.path.exists(settings.RAG_DATA_PATH) or not os.listdir(settings.RAG_DATA_PATH):
        logger.critical(f"Data source directory '{settings.RAG_DATA_PATH}' is missing or empty. Aborting.")
        raise FileNotFoundError(f"RAG data directory not found or empty at {settings.RAG_DATA_PATH}")

    docs = load_and_validate_documents(settings.RAG_DATA_PATH)
    if not docs:
        logger.critical("No valid documents could be loaded from source files. Aborting database build.")
        raise ValueError("Failed to load any valid RAG documents. Please check the logs and your JSON files.")

    logger.info(f"Initializing ChromaDB client at '{settings.CHROMA_DB_PATH}'...")
    client = chromadb.PersistentClient(path=settings.CHROMA_DB_PATH)

    # Use get_or_create_collection for a cleaner and more robust approach.
    # This single command handles both cases:
    # 1. If the collection exists, it returns it.
    # 2. If it does not exist, it creates and returns it.
    logger.info(f"Getting or creating collection: '{settings.RAG_COLLECTION_NAME}'")
    collection = client.get_or_create_collection(name=settings.RAG_COLLECTION_NAME)

    # Since we want to ensure a fresh build every time, we will "upsert" the data.
    # "Upsert" means "update if exists, insert if not". By providing all documents,
    # we effectively overwrite the collection's content with the latest data.
    logger.info("Preparing documents for upserting into the database...")

    documents_to_add = [doc.content for doc in docs]
    metadatas_to_add = [{"title": doc.title, "url": doc.url, "source": doc.source_file} for doc in docs]
    ids_to_add = [f"doc_{i}_{doc.title.replace(' ', '_').lower()[:50]}" for i, doc in enumerate(docs)]

    if not documents_to_add:
        logger.critical("No valid documents to add to the collection after processing.")
        raise ValueError("Document processing resulted in an empty list; cannot build database.")

    logger.info(f"Upserting {len(documents_to_add)} validated documents into the collection...")
    try:
        # The 'upsert' method is idempotent. It ensures that the documents with these IDs
        # are present in the collection with the specified content and metadata.
        collection.upsert(
            documents=documents_to_add,
            metadatas=metadatas_to_add,
            ids=ids_to_add
        )
        logger.info(f"Successfully built/updated database. Collection now contains {collection.count()} items.")
    except Exception as e:
        logger.critical(f"A critical error occurred during batch upsert into ChromaDB: {e}", exc_info=True)
        raise

    logger.info("--- RAG Vector Database Build Process Completed Successfully ---")


if __name__ == "__main__":
    try:
        main()
    except (FileNotFoundError, ValueError) as e:
        # Catch our own specific, critical errors and exit with a non-zero code
        # to signal failure to any automated scripts (like CI/CD).
        logger.critical(f"Build process failed: {e}")
        exit(1)
    except Exception as e:
        logger.critical(f"An unexpected fatal error stopped the build process: {e}")
        exit(1)