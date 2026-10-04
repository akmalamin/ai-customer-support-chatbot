from fastapi import APIRouter, status
from datetime import datetime, timezone

router = APIRouter(tags=["Health"])

@router.get("/health", status_code=status.HTTP_200_OK)
def health_check():
    return {
        "status": "healthy",
        "service": "AI Customer Support Chatbot",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }