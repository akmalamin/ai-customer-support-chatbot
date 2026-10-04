"""
app/routers/chat_router.py — Chat endpoints with rate limiting.
"""

import time
from collections import defaultdict
from fastapi import APIRouter, HTTPException, Request, status
from app.schemas.chat_schema import ChatRequest, ChatResponse
from app.services.chat_service import ChatService
from config import settings

router = APIRouter(prefix="/chat", tags=["Customer Support Chat"])

# Simple rate limiter
_rate_store: dict[str, list[float]] = defaultdict(list)


def check_rate_limit(ip: str):
    now = time.time()
    _rate_store[ip] = [t for t in _rate_store[ip] if now - t < 60]
    if len(_rate_store[ip]) >= settings.RATE_LIMIT_PER_MINUTE:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Try again in 60 seconds.",
        )
    _rate_store[ip].append(now)


@router.post("", response_model=ChatResponse)
def chat(request: ChatRequest, req: Request):
    """Send a customer query and receive an AI-generated response."""
    ip = req.client.host if req.client else "unknown"
    check_rate_limit(ip)

    result = ChatService.chat(request.query, request.conversation_id)
    return result