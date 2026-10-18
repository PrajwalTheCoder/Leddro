from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional
import os

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    PROJECT_NAME: str = "Leddro Prospect & Audit Engine"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    
    # Database
    DATABASE_URL: str = "sqlite:///./leddro.db"
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ]
    
    # Audit Security & Limits
    AUDIT_CONNECT_TIMEOUT: float = 5.0
    AUDIT_READ_TIMEOUT: float = 10.0
    AUDIT_MAX_REDIRECTS: int = 5
    AUDIT_MAX_RESPONSE_BYTES: int = 5 * 1024 * 1024  # 5 MB maximum
    AUDIT_ALLOWED_PORTS: List[int] = [80, 443, 8080, 8443]
    AUDIT_USER_AGENT: str = "LeddroAuditor/3.0 (+https://github.com/leddro/audit-engine; security-verified)"
    
    APP_NAME: str = "Leddro Website Audit Engine"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Discovery Provider Settings
    OSM_OVERPASS_URL: str = "https://overpass-api.de/api/interpreter"
    OSM_NOMINATIM_URL: str = "https://nominatim.openstreetmap.org/search"
    OSM_USER_AGENT: str = "LeddroBusinessDiscovery/1.0 (+https://github.com/leddro/leddro; contact@leddro.local)"
    GOOGLE_PLACES_API_KEY: str = ""
    DISCOVERY_MAX_RESULTS: int = 100
    DISCOVERY_DEFAULT_TIMEOUT: float = 25.0
    DISCOVERY_RATE_LIMIT_COOLDOWN: float = 1.0

    # Phase 5: AI Providers & Generation Settings
    AI_PROVIDER: str = "gemini"  # "gemini" | "openai" | "anthropic" | "compatible"
    
    # Google Gemini (Free tier available via Google AI Studio)
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-3.5-flash-lite"
    GEMINI_BASE_URL: str = "https://generativelanguage.googleapis.com/v1beta"

    # OpenAI
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"

    # Anthropic
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-3-5-haiku-20241022"
    ANTHROPIC_BASE_URL: str = "https://api.anthropic.com/v1"

    # Local / OpenAI-Compatible (Ollama, vLLM, OpenRouter, LocalAI)
    COMPATIBLE_API_KEY: str = ""
    COMPATIBLE_MODEL: str = "llama3"
    COMPATIBLE_BASE_URL: str = "http://localhost:11434/v1"

    def model_post_init(self, __context):
        if not self.GEMINI_API_KEY:
            self.GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY", "")

    # Safety limits
    AI_REQUEST_TIMEOUT: float = 60.0
    AI_MAX_OUTPUT_TOKENS: int = 1000

    # Phase 6: Google OAuth 2.0 & Gmail API Settings
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/google/callback"
    GOOGLE_OAUTH_SCOPES: str = "https://www.googleapis.com/auth/gmail.send https://www.googleapis.com/auth/userinfo.email openid"
    FRONTEND_URL: str = "http://localhost:5173"
    CREDENTIAL_ENCRYPTION_KEY: str = ""

    # Developer Profile (Outreach sender identity & context - operator customizable)
    DEV_NAME: str = ""
    DEV_TITLE: str = "Independent Web Consultant & Technical Auditor"
    DEV_SERVICES: str = "Website performance tuning, responsive fixes, SSL/DNS remediation, and accessibility audits"
    DEV_PORTFOLIO_URL: str = ""
    DEV_EMAIL: str = ""
    DEV_SIGNATURE: str = "Best regards,\nTechnical Consultant"

    @property
    def cors_origins_list(self) -> List[str]:
        origins = list(self.BACKEND_CORS_ORIGINS)
        if self.FRONTEND_URL and self.FRONTEND_URL not in origins:
            origins.append(self.FRONTEND_URL)
        return origins

settings = Settings()

