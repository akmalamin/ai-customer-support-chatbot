"""
app/services/chat_service.py — Core chat logic with LLM integration.

SPEC REFERENCE: FR-1 through FR-12
"""

import uuid
import logging
from datetime import datetime, timezone
from typing import Dict, Optional
from config import settings
from app.services.knowledge_base_service import KnowledgeBaseService
from app.services.security_service import SecurityService
from app.db.conversation_db import conversation_db

logger = logging.getLogger(__name__)

kb_service = KnowledgeBaseService()


class ChatService:

    @staticmethod
    def chat(query: str, conversation_id: Optional[str] = None) -> Dict:
        """
        Main chat endpoint logic.
        1. Sanitize input
        2. Search knowledge base
        3. Build prompt with context
        4. Call LLM
        5. Validate response
        6. Check confidence
        7. Log conversation
        """
        # Generate conversation ID if new
        if not conversation_id:
            conversation_id = f"conv_{uuid.uuid4().hex[:12]}"

        # FR-8: Sanitize input
        clean_query = SecurityService.sanitize_input(query, settings.MAX_QUERY_LENGTH)
        if not clean_query:
            return {
                "conversation_id": conversation_id,
                "answer": "I can only help with product-related questions. How can I assist you?",
                "confidence": 0.0,
                "source_documents": [],
                "needs_escalation": True,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        # FR-2: Search knowledge base
        context = kb_service.get_context_string(clean_query)
        relevant_chunks = kb_service.search(clean_query)
        source_docs = list(set(c["source"] for c in relevant_chunks))

        # If no context found, escalate
        if not context:
            response_data = {
                "conversation_id": conversation_id,
                "answer": "I'm not confident I can answer this accurately. "
                          "Let me connect you with a human agent.",
                "confidence": 0.2,
                "source_documents": [],
                "needs_escalation": True,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            conversation_db.save_message(conversation_id, "user", clean_query)
            conversation_db.save_message(conversation_id, "assistant", response_data["answer"], 0.2)
            return response_data

        # Build prompt
        system_prompt = SecurityService.get_system_prompt()
        full_prompt = f"""{system_prompt}

CONTEXT DOCUMENTS:
{context}

CUSTOMER QUESTION: {clean_query}

Respond concisely using ONLY the context above."""

        # Call LLM (or mock)
        if settings.mock_mode:
            answer = ChatService._mock_response(clean_query, context)
            confidence = 0.85
        else:
            answer, confidence = ChatService._call_llm(system_prompt, full_prompt)

        # Validate response
        if not SecurityService.validate_response(answer):
            answer = "I'm not confident I can answer this accurately. Let me connect you with a human agent."
            confidence = 0.3

        # FR-5: Confidence check
        needs_escalation = confidence < settings.CONFIDENCE_THRESHOLD

        if needs_escalation:
            answer = "I'm not confident I can answer this accurately. Let me connect you with a human agent."

        # Log conversation
        conversation_db.save_message(conversation_id, "user", clean_query)
        conversation_db.save_message(conversation_id, "assistant", answer, confidence)

        return {
            "conversation_id": conversation_id,
            "answer": answer,
            "confidence": round(confidence, 2),
            "source_documents": source_docs,
            "needs_escalation": needs_escalation,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    @staticmethod
    def _call_llm(system_prompt: str, full_prompt: str) -> tuple:
        """Call OpenAI API and return (answer, confidence)."""
        try:
            from openai import OpenAI
            client = OpenAI(api_key=settings.OPENAI_API_KEY)

            response = client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": full_prompt},
                ],
                max_tokens=300,
                temperature=0.3,  # Low temperature for factual responses
            )

            answer = response.choices[0].message.content.strip()

            # Estimate confidence based on response quality
            # If response contains "I'm not sure" or "I don't know", lower confidence
            if any(phrase in answer.lower() for phrase in ["not sure", "don't know", "not confident", "cannot answer"]):
                confidence = 0.4
            elif len(answer) < 20:
                confidence = 0.5
            else:
                confidence = 0.85

            return answer, confidence

        except Exception as e:
            logger.error("LLM call failed: %s", e)
            return "We're experiencing technical difficulties. Please try again later.", 0.3

    @staticmethod
    def _mock_response(query: str, context: str) -> str:
        """Deterministic mock response for development without API key."""
        query_lower = query.lower()

        if "password" in query_lower:
            return "To reset your password, go to Settings > Security > Reset Password. Enter your email and we will send a reset link within 5 minutes."
        elif "refund" in query_lower:
            return "We offer a full refund within 30 days of purchase. Contact support@acmecorp.com with your order number."
        elif "cancel" in query_lower:
            return "Go to Settings > Billing > Cancel Subscription. Your subscription remains active until the end of your billing period."
        elif "contact" in query_lower or "support" in query_lower:
            return "Reach us at support@acmecorp.com or call 1-800-555-0199. Business hours: Mon-Fri, 9 AM - 6 PM EST."
        elif "payment" in query_lower:
            return "We accept Visa, Mastercard, American Express, and PayPal. All payments are processed through Stripe."
        else:
            return "Based on our documentation, I can help with password resets, refunds, subscriptions, and billing questions. Could you provide more details?"