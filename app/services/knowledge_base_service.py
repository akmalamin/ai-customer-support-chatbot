"""
app/services/knowledge_base_service.py — Knowledge base ingestion and retrieval.

SPEC REFERENCE: FR-2, FR-10, NFR-8
"""

import os
import logging
from typing import List, Dict
from config import settings

logger = logging.getLogger(__name__)


class KnowledgeBaseService:
    def __init__(self):
        self.chunks: List[Dict] = []
        self._load_knowledge_base()

    def _load_knowledge_base(self):
        """Load and chunk all documents from the knowledge_base directory."""
        kb_dir = settings.KNOWLEDGE_BASE_DIR
        if not os.path.exists(kb_dir):
            os.makedirs(kb_dir, exist_ok=True)
            logger.warning("Knowledge base directory is empty.")
            return

        for filename in os.listdir(kb_dir):
            filepath = os.path.join(kb_dir, filename)
            if not os.path.isfile(filepath):
                continue

            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    text = f.read()

                chunks = self._chunk_text(text, filename)
                self.chunks.extend(chunks)
                logger.info("Indexed %d chunks from %s", len(chunks), filename)

            except Exception as e:
                logger.error("Failed to load %s: %s", filename, e)

        logger.info("Total knowledge base chunks: %d", len(self.chunks))

    def _chunk_text(self, text: str, source: str) -> List[Dict]:
        """Split text into overlapping chunks for retrieval."""
        chunk_size = settings.CHUNK_SIZE
        overlap = settings.CHUNK_OVERLAP
        chunks = []

        # Split by paragraphs first, then by size
        paragraphs = text.split("\n\n")
        current_chunk = ""

        for para in paragraphs:
            if len(current_chunk) + len(para) > chunk_size and current_chunk:
                chunks.append({
                    "text": current_chunk.strip(),
                    "source": source,
                })
                # Keep overlap from end of previous chunk
                current_chunk = current_chunk[-overlap:] + " " + para
            else:
                current_chunk += " " + para if current_chunk else para

        if current_chunk.strip():
            chunks.append({
                "text": current_chunk.strip(),
                "source": source,
            })

        return chunks

    def search(self, query: str, top_k: int = None) -> List[Dict]:
        """
        Search knowledge base for relevant chunks.
        Uses simple keyword matching for MVP (no vector DB needed).
        """
        if top_k is None:
            top_k = settings.TOP_K_RESULTS

        if not self.chunks:
            return []

        query_lower = query.lower()
        query_words = set(query_lower.split())

        scored_chunks = []
        for chunk in self.chunks:
            chunk_lower = chunk["text"].lower()
            # Simple relevance score: count matching words
            score = sum(1 for word in query_words if word in chunk_lower)
            if score > 0:
                scored_chunks.append({**chunk, "score": score})

        # Sort by relevance score (descending)
        scored_chunks.sort(key=lambda x: x["score"], reverse=True)
        return scored_chunks[:top_k]

    def get_context_string(self, query: str) -> str:
        """Get formatted context string for LLM prompt."""
        chunks = self.search(query)
        if not chunks:
            return ""

        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            context_parts.append(f"[Source {i}: {chunk['source']}]\n{chunk['text']}")

        return "\n\n".join(context_parts)