import os
import logging
import asyncio
from typing import List, Optional

import chromadb
from sentence_transformers import SentenceTransformer
from pydantic import BaseModel

# --- 1. CONFIGURATION ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

CUR_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(CUR_DIR, "chroma_db")
COLLECTION_NAME = "career_sources"
MODEL_NAME = "all-MiniLM-L6-v2"


# --- 2. DATA CONTRACT (Schema) ---
class Source(BaseModel):
    title: str
    url: str
    content: str


# --- 3. CORE SERVICE CLASS ---
class RAGService:
    def __init__(self):
        """
        Initializes RAG components on creation. This is an expensive operation
        and should only be done once at application startup.
        """
        self.model: Optional[SentenceTransformer] = None
        self.collection: Optional[chromadb.Collection] = None

        logging.info("Initializing RAGService...")
        try:
            # This is a CPU-bound operation, but it's okay to run it synchronously
            # in the constructor as it happens only once during app startup.
            self.model = SentenceTransformer(MODEL_NAME)

            client = chromadb.PersistentClient(path=DB_PATH)
            self.collection = client.get_collection(COLLECTION_NAME)
            logging.info("RAGService initialized successfully.")
        except Exception as e:
            logging.critical(f"FATAL: RAGService failed to initialize. Error: {e}")

    async def query_sources(self, learning_objective: str, k: int = 3) -> List[Source]:
        """
        Asynchronously queries the vector database for relevant sources.
        """
        if self.collection is None or self.model is None:
            logging.error("Cannot query sources because RAGService is not available.")
            return []

        try:
            # --- CRITICAL: Run blocking operations in a separate thread ---
            # model.encode is CPU-bound.
            query_embedding = await asyncio.to_thread(self.model.encode, learning_objective)

            # collection.query can be I/O-bound.
            results = await asyncio.to_thread(
                self.collection.query,
                query_embeddings=[query_embedding.tolist()],
                n_results=k
            )

            sources = []
            docs_list = results.get("documents", [[]])[0]
            metas_list = results.get("metadatas", [[]])[0]

            if docs_list and metas_list:
                for doc, meta in zip(docs_list, metas_list):
                    sources.append(Source(
                        title=meta.get("title", "No Title"),
                        url=meta.get("url", "#"),
                        content=doc
                    ))
            return sources
        except Exception as e:
            logging.error(f"Error during ChromaDB query for '{learning_objective}': {e}")
            return []