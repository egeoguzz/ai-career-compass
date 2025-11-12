import logging
from typing import List, Dict, Any
import chromadb
from sentence_transformers import SentenceTransformer

# Import the single source of truth for configuration
from config import settings

# Import a data schema if needed, though returning Dicts is fine for this internal service
# from schemas import RAGDocument

logger = logging.getLogger(__name__)


# --- 1. CUSTOM EXCEPTION ---
class RAGServiceError(Exception):
    """Custom exception for all RAG Service related errors."""
    pass


# --- 2. CORE SERVICE CLASS (Now fully synchronous and robust) ---
class RAGService:
    def __init__(self):
        """
        Initializes RAG components. This is an expensive, blocking operation
        that should happen only once at application startup.
        If it fails, it will raise an exception to prevent the app from starting
        in a broken state.
        """
        logger.info("Initializing RAGService...")
        try:
            logger.info(f"Loading SentenceTransformer model: '{settings.EMBEDDING_MODEL_NAME}'")
            self.model: SentenceTransformer = SentenceTransformer(settings.EMBEDDING_MODEL_NAME)

            logger.info(f"Connecting to ChromaDB at: '{settings.CHROMA_DB_PATH}'")
            client = chromadb.PersistentClient(path=settings.CHROMA_DB_PATH)

            # get_collection will raise an exception if the collection does not exist,
            # which is the desired "fail-fast" behavior.
            self.collection: chromadb.Collection = client.get_collection(settings.RAG_COLLECTION_NAME)

            count = self.collection.count()
            if count == 0:
                logger.warning(
                    f"RAG collection '{self.collection.name}' is empty. The service will run but may not find any documents.")

            logger.info(
                f"RAGService initialized successfully. Collection '{self.collection.name}' contains {count} documents.")

        except Exception as e:
            logger.critical(f"FATAL: RAGService failed to initialize. Error: {e}", exc_info=True)
            # Re-raise as a custom exception to be handled by the main application starter.
            raise RAGServiceError(f"RAGService could not be initialized: {e}")

    def query_sources(self, learning_objective: str, k: int = 3) -> List[Dict[str, Any]]:
        """
        Queries the vector database for relevant sources.
        This is a synchronous, potentially long-running (CPU/IO-bound) method.
        It should be called from an async context (like a FastAPI endpoint)
        using `asyncio.to_thread`.
        """
        logger.info(f"Querying RAG sources for: '{learning_objective}'")
        try:
            query_embedding = self.model.encode(learning_objective).tolist()

            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=k
            )

            # Safely unpack the results from ChromaDB
            if not results or not results.get("ids", [[]])[0]:
                logger.warning(f"No results returned from ChromaDB for query: '{learning_objective}'")
                return []

            sources: List[Dict[str, Any]] = []
            docs_list = results.get("documents", [[]])[0]
            metas_list = results.get("metadatas", [[]])[0]

            for doc, meta in zip(docs_list, metas_list):
                if doc is not None and meta is not None:
                    sources.append({
                        "title": meta.get("title", "No Title Available"),
                        "url": meta.get("url", "#"),
                        "content": doc
                    })

            logger.info(f"Found {len(sources)} relevant sources for query.")
            return sources

        except Exception as e:
            logger.error(f"An error occurred during ChromaDB query for '{learning_objective}': {e}", exc_info=True)
            # Do not return an empty list. Propagate the error upwards.
            raise RAGServiceError(f"Failed to query sources for: '{learning_objective}'")