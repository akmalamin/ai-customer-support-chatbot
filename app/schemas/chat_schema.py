from pydantic import BaseModel, Field
from typing import List, Optional


class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500, example="How do I reset my password?")
    conversation_id: Optional[str] = Field(default=None, example="conv_abc123")


class ChatResponse(BaseModel):
    conversation_id: str
    answer: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    source_documents: List[str]
    needs_escalation: bool
    timestamp: str


class KnowledgeBaseUploadResponse(BaseModel):
    message: str
    documents_indexed: int
    chunks_created: int