"""Point d'entrée de l'application AI Engine."""

from contextlib import asynccontextmanager
from pathlib import Path
import re

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from app.config.logging import setup_logging
from app.config.settings import settings
from app.graph.workflow import get_graph


# Configuration des logs
setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestion du cycle de vie de l'application."""
    # Démarrage
    print("🚀 AI Engine démarré sur http://localhost:8001")
    print(f"📌 LLM Provider: {settings.llm_provider.value}")
    print(f"📌 Backend API: {settings.backend_api_url}")
    yield
    # Arrêt
    print("🛑 AI Engine arrêté")


# Création de l'application FastAPI
app = FastAPI(
    title="AI Engine - Réservations de restaurants",
    description="Moteur multi-agents LangGraph pour l'automatisation des réservations",
    version="0.1.0",
    lifespan=lifespan,
)


class ChatRequest(BaseModel):
    """Message envoyé depuis la page de test."""

    conversation_id: str = Field(min_length=1, max_length=100)
    restaurant_id: str = Field(min_length=1, max_length=100)
    message: str = Field(min_length=1, max_length=2000)
    customer_name: str | None = Field(default=None, max_length=100)
    customer_phone: str | None = Field(default=None, max_length=20)


@app.get("/test", include_in_schema=False)
async def test_page():
    """Sert la console de test chat/vocal."""
    page = Path(__file__).parent / "static" / "test.html"
    return FileResponse(page)


@app.post("/api/chat")
async def chat(request: ChatRequest):
    """Traite un message via le workflow multi-agents."""
    from app.graph import add_user_message, create_initial_state
    from app.schemas.conversation import Message, MessageRole
    from app.schemas.customer import CustomerContext
    from app.services.conversation_memory import get_conversation_memory_service

    try:
        customer = CustomerContext(
            name=request.customer_name,
            phone=request.customer_phone,
        )
        config = {"configurable": {"thread_id": request.conversation_id}}
        workflow = get_graph()
        checkpoint = workflow.get_state(config)
        if checkpoint and checkpoint.values:
            current_restaurant_id = checkpoint.values.get("restaurant_id")
            if current_restaurant_id and current_restaurant_id != request.restaurant_id:
                raise HTTPException(status_code=409, detail="Cette conversation appartient à un autre restaurant")
            state = {"messages": [Message(role=MessageRole.USER, content=request.message)]}
            current_customer = checkpoint.values.get("customer")
            phone_match = re.fullmatch(r"\s*(\+?[0-9]{8,15})\s*", request.message)
            if phone_match and current_customer:
                state["customer"] = current_customer.model_copy(update={"phone": phone_match.group(1)})
            elif request.customer_name or request.customer_phone:
                state["customer"] = current_customer.model_copy(
                    update={
                        key: value
                        for key, value in {
                            "name": request.customer_name,
                            "phone": request.customer_phone,
                        }.items()
                        if value is not None
                    }
                ) if current_customer else customer
        else:
            context = get_conversation_memory_service().load_context(request.conversation_id)
            state = get_conversation_memory_service().restore_state(context)
            if state:
                saved_restaurant_id = state.get("restaurant_id")
                if saved_restaurant_id and saved_restaurant_id != request.restaurant_id:
                    raise HTTPException(status_code=409, detail="Cette conversation appartient à un autre restaurant")
                state["messages"] = state.get("messages") or [
                    Message.model_validate(message) for message in context.get("messages", [])
                ]
                state["conversation_summary"] = context.get("summary")
                current_customer = state.get("customer")
                if request.customer_name or request.customer_phone:
                    updates = {
                        key: value
                        for key, value in {
                            "name": request.customer_name,
                            "phone": request.customer_phone,
                        }.items()
                        if value is not None
                    }
                    state["customer"] = current_customer.model_copy(update=updates) if current_customer else customer
                phone_match = re.fullmatch(r"\s*(\+?[0-9]{8,15})\s*", request.message)
                if phone_match:
                    current_customer = state.get("customer")
                    if current_customer:
                        state["customer"] = current_customer.model_copy(update={"phone": phone_match.group(1)})
                    reservation = state.get("reservation")
                    if reservation:
                        state["reservation"] = reservation.model_copy(update={"customer_phone": phone_match.group(1)})
            else:
                state = create_initial_state(
                    conversation_id=request.conversation_id,
                    restaurant_id=request.restaurant_id,
                    channel="chat",
                    customer=customer,
                )
                state["messages"] = [
                    Message.model_validate(message) for message in context.get("messages", [])
                ]
            state.setdefault("conversation_id", request.conversation_id)
            state.setdefault("restaurant_id", request.restaurant_id)
            state.setdefault("channel", "chat")
            state.setdefault("customer", customer)
            add_user_message(state, request.message)
        result = workflow.invoke(state, config=config)
        response_message = _response_message(result)
        memory = get_conversation_memory_service()
        persisted_state = dict(result)
        persisted_messages = list(persisted_state.get("messages", []))
        last_message = persisted_messages[-1] if persisted_messages else None
        last_role = getattr(last_message, "role", None)
        last_role = getattr(last_role, "value", last_role)
        last_content = getattr(last_message, "content", None)
        if last_role != MessageRole.ASSISTANT.value or last_content != response_message:
            persisted_messages.append(Message(role=MessageRole.ASSISTANT, content=response_message))
        persisted_state["messages"] = persisted_messages
        memory.save_turn(
            request.conversation_id,
            user_message=request.message,
            assistant_message=response_message,
            metadata={
                "restaurant_id": request.restaurant_id,
                "agent": result.get("current_agent"),
                "next_action": result.get("next_action"),
            },
            state=persisted_state,
        )
        workflow.update_state(
            config,
            {
                "messages": [
                    Message(role=MessageRole.ASSISTANT, content=response_message)
                ]
            },
        )
        return {
            "conversation_id": request.conversation_id,
            "message": response_message,
            "agent": result.get("current_agent"),
            "next_action": result.get("next_action"),
            "requires_clarification": result.get("requires_clarification", False),
            "is_complete": result.get("is_complete", False),
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Le traitement du message a échoué") from exc


def _response_message(result: dict) -> str:
    """Extrait une réponse sûre et lisible depuis l'état du graphe."""
    if result.get("error"):
        return "Je rencontre un problème avec cette demande. Pouvez-vous me préciser ce que vous souhaitez faire ?"

    for key in ("clarification_question", "message"):
        value = result.get(key)
        if value:
            return str(value)
    confirmation = result.get("reservation_confirmation")
    if confirmation:
        return str(getattr(confirmation, "message", "Réservation traitée."))
    recommendation = result.get("recommendation")
    if recommendation and hasattr(recommendation, "get_recommendation_text"):
        return recommendation.get_recommendation_text()
    fallback_messages = {
        "greeting": "Bonjour ! Comment puis-je vous aider ?",
        "unknown": "Pouvez-vous préciser votre demande concernant le restaurant ou une réservation ?",
        "ask_missing": "Pouvez-vous me donner les informations manquantes pour continuer ?",
    }
    if result.get("current_agent") in fallback_messages:
        return fallback_messages[result["current_agent"]]
    return "Je n'ai pas pu déterminer la réponse. Un membre de l'équipe va vous aider."

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # À restreindre en production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Routes de base
@app.get("/")
async def root():
    """Route racine pour vérifier que le service fonctionne."""
    return {
        "service": "AI Engine",
        "version": "0.1.0",
        "status": "operational",
        "llm_provider": settings.llm_provider.value,
        "backend": settings.backend_api_url,
    }


@app.get("/health")
async def health():
    """Route de health check."""
    return {"status": "healthy"}


# Ici seront ajoutées les routes pour :
# - Webhooks WhatsApp
# - Chat Web
# - API interne pour Dev2