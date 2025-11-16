from __future__ import annotations

import logging
from typing import Dict, Any, List
from chromadb import Client
from sentence_transformers import SentenceTransformer
import os
import json

from config import settings
from schemas import RAGDocument

logger = logging.getLogger(__name__)


class RAGServiceError(Exception):
    """Custom exception for RAG Service related errors."""
    pass


class RAGService:
    _instance = None

    def __init__(self):
        """
        Initializes the RAGService with None for client and model.
        These will be loaded lazily on first use to save memory on startup.
        """
        self.client: Client | None = None
        self.model: SentenceTransformer | None = None
        self.collection = None

    def _lazy_initialize(self):
        """
        Performs the heavy lifting of loading the model and initializing the DB client.
        This method is called only on the first actual use of the RAG service.
        """
        if self.model is None:
            try:
                logger.info("RAGService: First use detected, initializing client and model...")

                logger.info(f"Loading sentence-transformer model ('{settings.EMBEDDING_MODEL_NAME}') into memory...")
                self.model = SentenceTransformer(settings.EMBEDDING_MODEL_NAME)
                logger.info("Sentence-transformer model loaded successfully.")

                self.client = Client(settings={"persist_directory": settings.CHROMA_DB_PATH})

                self._load_or_create_db()

            except Exception as e:
                logger.critical(f"Failed to lazy-initialize RAG Service: {e}", exc_info=True)
                raise RAGServiceError(e)

    def _load_or_create_db(self):
        """Loads an existing ChromaDB collection or creates a new one if not found."""
        if not self.client: return

        collection_names = [c.name for c in self.client.list_collections()]
        if settings.RAG_COLLECTION_NAME in collection_names:
            logger.info(f"Loading existing ChromaDB collection: '{settings.RAG_COLLECTION_NAME}'")
            self.collection = self.client.get_collection(name=settings.RAG_COLLECTION_NAME)
        else:
            logger.info(f"Creating new ChromaDB collection: '{settings.RAG_COLLECTION_NAME}'")
            self.collection = self.client.create_collection(name=settings.RAG_COLLECTION_NAME)
            self._populate_db()

    def _populate_db(self):
        """Reads JSON files from rag_data and populates the ChromaDB collection."""
        if not self.collection or not self.model: return

        logger.info("Populating collection with data from rag_data directory...")
        documents: List[RAGDocument] = []
        for filename in os.listdir(settings.RAG_DATA_PATH):
            if filename.endswith(".json"):
                filepath = os.path.join(settings.RAG_DATA_PATH, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for item in data:
                        item['source_file'] = filename
                        documents.append(RAGDocument(**item))

        if not documents:
            logger.warning("No documents found to populate the RAG database.")
            return

        self.collection.add(
            ids=[f"doc_{i}" for i in range(len(documents))],
            documents=[doc.content for doc in documents],
            metadatas=[doc.model_dump(exclude={'content'}) for doc in documents]
        )
        logger.info(f"Successfully added {len(documents)} documents to the collection.")

    def query_and_assess_sources(self, query: str, k: int = 2) -> Dict[str, Any]:
        """
        Queries the vector DB, assesses relevance, and returns sources with a confidence level.
        This is the main public method for this service.
        """
        self._lazy_initialize()

        if not self.collection:
            logger.error("RAG collection is not available for querying.")
            return {"relevant_sources": [], "confidence": "low"}

        logger.info(f"Querying RAG for: '{query}'")
        results = self.collection.query(
            query_texts=[query],
            n_results=k,
            include=["metadatas", "documents", "distances"]
        )

        sources = []
        distances = results.get('distances', [[]])[0]

        RELEVANCE_THRESHOLD = 1.0

        if not distances or distances[0] > RELEVANCE_THRESHOLD:
            logger.warning(
                f"Low confidence for RAG query: '{query}'. Best distance: {distances[0] if distances else 'N/A'}")
            return {"relevant_sources": [], "confidence": "low"}

        for i, doc_content in enumerate(results['documents'][0]):
            meta = results['metadatas'][0][i]
            sources.append({
                "title": meta.get("title", "Unknown Source"),
                "url": meta.get("url", "#"),
                "content": doc_content
            })

        return {"relevant_sources": sources, "confidence": "high"}