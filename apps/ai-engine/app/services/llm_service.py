"""Service unifié de gestion des fournisseurs LLM."""

from typing import Optional, Dict, Any, List
import logging
from enum import Enum

from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

from app.config.settings import settings, LLMProvider

logger = logging.getLogger("ai_engine.services.llm")


class LLMService:
    """Service unifié pour les appels LLM."""

    def __init__(self):
        self._model: Optional[BaseChatModel] = None

    def _initialize_model(self) -> None:
        """Initialise le modèle LLM selon la configuration."""
        if settings.llm_provider == LLMProvider.OPENAI:
            if not settings.openai_api_key:
                raise ValueError("OPENAI_API_KEY non configurée")
            
            self._model = ChatOpenAI(
                api_key=settings.openai_api_key,
                model=settings.openai_model,
                temperature=settings.llm_temperature,
                max_tokens=settings.llm_max_tokens,
            )
            logger.info(f"✅ OpenAI initialisé: {settings.openai_model}")
            
        elif settings.llm_provider == LLMProvider.ANTHROPIC:
            if not settings.anthropic_api_key:
                raise ValueError("ANTHROPIC_API_KEY non configurée")
            
            self._model = ChatAnthropic(
                api_key=settings.anthropic_api_key,
                model=settings.anthropic_model,
                temperature=settings.llm_temperature,
                max_tokens=settings.llm_max_tokens,
            )
            logger.info(f"✅ Anthropic initialisé: {settings.anthropic_model}")
        elif settings.llm_provider == LLMProvider.GEMINI:
            if not settings.gemini_api_key:
                raise ValueError("GEMINI_API_KEY non configurée")

            self._model = ChatGoogleGenerativeAI(
                google_api_key=settings.gemini_api_key,
                model=settings.gemini_model,
                temperature=settings.llm_temperature,
                max_output_tokens=settings.llm_max_tokens,
            )
            logger.info("Gemini initialisé: %s", settings.gemini_model)
        else:
            raise ValueError(f"Fournisseur LLM non supporté: {settings.llm_provider}")

    def get_model(self) -> BaseChatModel:
        """Retourne le modèle LLM."""
        if self._model is None:
            self._initialize_model()
        return self._model

    @staticmethod
    def _content_to_text(content: Any) -> str:
        """Normalise les réponses texte et les blocs Gemini en chaîne."""
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts = []
            for block in content:
                if isinstance(block, str):
                    parts.append(block)
                elif isinstance(block, dict) and block.get("text"):
                    parts.append(str(block["text"]))
            return "".join(parts)
        return str(content)

    async def ainvoke(
        self,
        system_prompt: str,
        user_message: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """Appel asynchrone au LLM."""
        try:
            model = self.get_model()
            
            # Configurer la température si spécifiée
            if temperature is not None:
                model.temperature = temperature
            
            # Créer les messages
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_message),
            ]
            
            # Appeler le modèle
            response = await model.ainvoke(messages)
            
            content = self._content_to_text(response.content)
            logger.debug("LLM response: %s...", content[:200])
            return content
            
        except Exception as e:
            logger.error(f"Erreur LLM: {e}")
            raise

    def invoke(
        self,
        system_prompt: str,
        user_message: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """Appel synchrone au LLM."""
        try:
            model = self.get_model()
            
            if temperature is not None:
                model.temperature = temperature
            
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_message),
            ]
            
            response = model.invoke(messages)
            
            content = self._content_to_text(response.content)
            logger.debug("LLM response: %s...", content[:200])
            return content
            
        except Exception as e:
            logger.error(f"Erreur LLM: {e}")
            raise


# Instance globale
_llm_service: Optional[LLMService] = None


def get_llm_service() -> LLMService:
    """Retourne l'instance du service LLM (singleton)."""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service