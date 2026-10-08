"""Configuration centralisée de l'application."""

from enum import Enum
from pathlib import Path
from typing import Optional
from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMProvider(str, Enum):
    """Fournisseurs de LLM supportés."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"


class LogLevel(str, Enum):
    """Niveaux de log supportés."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class Settings(BaseSettings):
    """Configuration principale de l'application."""
    
    # ===== LLM =====
    llm_provider: LLMProvider = Field(default=LLMProvider.OPENAI)
    llm_temperature: float = Field(default=0.1)
    use_llm: bool = Field(default=False, alias="USE_LLM")
    llm_fallback_enabled: bool = Field(default=True, alias="LLM_FALLBACK_ENABLED")
    llm_max_calls_per_conversation: int = Field(default=3, alias="LLM_MAX_CALLS_PER_CONVERSATION", ge=0)
    
    # OpenAI
    openai_api_key: Optional[str] = Field(default=None)
    openai_model: str = Field(default="gpt-4o-mini")
    
    # Anthropic
    anthropic_api_key: Optional[str] = Field(default=None)
    anthropic_model: str = Field(default="claude-3-5-haiku-20241022")

    # Google Gemini
    gemini_api_key: Optional[str] = Field(default=None, alias="GEMINI_API_KEY")
    gemini_model: str = Field(default="gemini-1.5-flash", alias="GEMINI_MODEL")
    
    # ===== Backend =====
    backend_api_url: str = Field(default="http://localhost:8000")
    backend_api_key: Optional[str] = Field(default=None)
    backend_enabled: bool = Field(default=False, alias="BACKEND_ENABLED")
    
    # ===== Redis =====
    redis_url: str = Field(default="redis://localhost:6379/0")
    
    # ===== Application =====
    log_level: LogLevel = Field(default=LogLevel.INFO)
    environment: str = Field(default="development")
    debug: bool = Field(default=True)
    app_name: Optional[str] = Field(default="AI Engine", alias="APP_NAME")
    app_version: Optional[str] = Field(default="0.1.0", alias="APP_VERSION")
    
    # ===== Agent =====
    max_iterations: int = Field(default=10)
    handoff_threshold: int = Field(default=3)
    lock_duration_seconds: int = Field(default=300)

    # ===== Champs supplémentaires autorisés =====
    # Ces champs peuvent être dans le .env mais ne sont pas validés
    llm_max_tokens: Optional[int] = Field(default=1024, alias="LLM_MAX_TOKENS")
    backend_timeout_seconds: Optional[int] = Field(default=30, alias="BACKEND_TIMEOUT_SECONDS")
    backend_retry_count: Optional[int] = Field(default=3, alias="BACKEND_RETRY_COUNT")
    redis_session_ttl_seconds: Optional[int] = Field(default=3600, alias="REDIS_SESSION_TTL_SECONDS")
    redis_max_connections: Optional[int] = Field(default=10, alias="REDIS_MAX_CONNECTIONS")
    whatsapp_api_version: Optional[str] = Field(default="v18.0", alias="WHATSAPP_API_VERSION")
    app_name: Optional[str] = Field(default="AI Engine", alias="APP_NAME")
    app_version: Optional[str] = Field(default="0.1.0", alias="APP_VERSION")
    log_format: Optional[str] = Field(default="text", alias="LOG_FORMAT")
    min_guests_for_deposit: Optional[int] = Field(default=4, alias="MIN_GUESTS_FOR_DEPOSIT")
    default_currency: Optional[str] = Field(default="USD", alias="DEFAULT_CURRENCY")
    enable_guardrails: Optional[bool] = Field(default=True, alias="ENABLE_GUARDRAILS")
    enable_function_calling_validation: Optional[bool] = Field(default=True, alias="ENABLE_FUNCTION_CALLING_VALIDATION")
    max_confirmation_attempts: Optional[int] = Field(default=3, alias="MAX_CONFIRMATION_ATTEMPTS")

    @property
    def project_root(self) -> Path:
        """Retourne le dossier racine du projet."""
        return Path(__file__).resolve().parent.parent.parent

    @property
    def prompts_dir(self) -> Path:
        """Retourne le dossier des prompts."""
        return self.project_root / "app" / "prompts"

    @property
    def logs_dir(self) -> Path:
        """Retourne le dossier des logs de l'application."""
        return self.project_root / "logs"

    @model_validator(mode="after")
    def validate_llm(self) -> "Settings":
        """Vérifie que les clés API sont présentes.

        On laisse la config fonctionner en mode local sans clé si l'application
        utilise des données simulées. Cela évite de casser les tests de scripts
        et les démonstrations hors ligne.
        """
        if self.llm_provider == LLMProvider.OPENAI:
            if not self.openai_api_key:
                return self
        elif self.llm_provider == LLMProvider.ANTHROPIC:
            if not self.anthropic_api_key:
                return self
        elif self.llm_provider == LLMProvider.GEMINI:
            if not self.gemini_api_key:
                return self
        return self
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # Ignore les champs supplémentaires
    )


settings = Settings()