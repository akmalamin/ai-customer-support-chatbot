from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(case_sensitive=True, env_file=".env")

    PROJECT_NAME: str = "AI Customer Support Chatbot"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "RAG-powered customer support chatbot with knowledge base, confidence scoring, and escalation logic."
    DOCS_URL: str = "/docs"

    APP_ENV: str = "development"
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-3.5-turbo"

    # RAG Settings
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50
    TOP_K_RESULTS: int = 3

    # Confidence & Escalation
    CONFIDENCE_THRESHOLD: float = 0.70
    MAX_CONVERSATION_TURNS: int = 10
    MAX_QUERY_LENGTH: int = 500

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 10

    # Knowledge Base Path
    KNOWLEDGE_BASE_DIR: str = "knowledge_base"

    @property
    def is_development(self) -> bool:
        return self.APP_ENV == "development"

    @property
    def mock_mode(self) -> bool:
        return self.is_development and not self.OPENAI_API_KEY


settings = Settings()