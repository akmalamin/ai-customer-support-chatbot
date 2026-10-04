# AI Customer Support Chatbot (Day 131)

A RAG-powered customer support chatbot built with FastAPI, LangChain,
ChromaDB, and OpenAI GPT. Features knowledge base ingestion,
confidence scoring, prompt injection defense, and human escalation.

## Quick Start
```bash
cp .env.example .env
pip install -r requirements.txt
uvicorn main:app --reload --port 8000