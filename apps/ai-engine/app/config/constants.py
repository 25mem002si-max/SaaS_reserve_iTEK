"""Constantes métier partagées par tous les agents.

Ces constantes sont utilisées pour la validation,
les prompts, et la logique métier.
"""

from enum import Enum
from typing import List, Dict, Any


class ReservationStatus(str, Enum):
    """Statuts possibles d'une réservation."""
    PENDING_PAYMENT = "PENDING_PAYMENT"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"
    COMPLETED = "COMPLETED"
    NO_SHOW = "NO_SHOW"
    WAITING_LIST = "WAITING_LIST"


class PaymentStatus(str, Enum):
    """Statuts possibles d'un paiement."""
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"
    CANCELLED = "CANCELLED"


class TableStatus(str, Enum):
    """Statuts possibles d'une table."""
    AVAILABLE = "available"
    RESERVED = "reserved"
    OCCUPIED = "occupied"
    LOCKED = "locked"  # Verrouillage temporaire Redis


class ChannelType(str, Enum):
    """Types de canaux."""
    CHAT = "chat"
    WHATSAPP = "whatsapp"
    SMS = "sms"
    VOICE = "voice"


class Currency(str, Enum):
    """Devises supportées."""
    USD = "USD"
    CDF = "CDF"


# ============================================
# Prompts génériques
# ============================================

SYSTEM_PROMPT_BASE = """
Tu es un assistant IA professionnel et chaleureux pour un restaurant en République Démocratique du Congo.
Tu parles français avec un ton convivial, respectueux et professionnel.
Tu t'adaptes au contexte local (Kinshasa, Lubumbashi, etc.).

IMPORTANT - RÈGLES D'OR :
1. Tu ne DOIS JAMAIS inventer d'informations (disponibilité, prix, menu, etc.).
2. Toutes les informations opérationnelles doivent provenir des outils (Function Calling).
3. Si tu ne sais pas, tu demandes ou tu utilises un outil.
4. Tu n'inventes pas de plats, de promotions ou de politiques qui n'existent pas.

DEVISE :
- Le restaurant accepte les paiements en USD et en CDF.
- Les prix peuvent être affichés dans l'une ou l'autre devise.
"""

# ============================================
# Messages d'erreur standardisés
# ============================================

ERROR_MESSAGES = {
    "availability_check_failed": "Je n'arrive pas à vérifier les disponibilités pour le moment. Pouvez-vous réessayer ?",
    "lock_failed": "Cette table vient d'être réservée par un autre client. Puis-je vous proposer un autre créneau ?",
    "payment_failed": "Le paiement n'a pas pu être traité. Voulez-vous réessayer ou contacter le restaurant ?",
    "reservation_failed": "Je n'ai pas pu enregistrer la réservation. Voulez-vous réessayer ?",
    "menu_not_available": "Je n'ai pas pu récupérer le menu actuel. Voulez-vous que je vous redirige vers le restaurant ?",
    "handoff_triggered": "Je vais vous transférer à l'équipe du restaurant. Ils vous répondront dans quelques instants.",
}

# ============================================
# Configuration des agents
# ============================================

AGENT_CONFIG = {
    "orchestrator": {
        "max_retries": 3,
        "timeout_seconds": 30,
    },
    "nlp": {
        "max_retries": 2,
        "timeout_seconds": 15,
    },
    "reservation": {
        "max_retries": 3,
        "timeout_seconds": 20,
    },
    "recommendation": {
        "max_retries": 2,
        "timeout_seconds": 15,
    },
    "payment": {
        "max_retries": 3,
        "timeout_seconds": 30,
    },
    "notification": {
        "max_retries": 2,
        "timeout_seconds": 10,
    },
}

# ============================================
# Requêtes de confirmation
# ============================================

CONFIRMATION_TEMPLATES = {
    "reservation": """
✅ Réservation confirmée !

📅 Date: {date}
⏰ Heure: {time}
👥 Couverts: {guests}
📍 Table: {table_label}
💰 Acompte: {deposit} {currency}

Un QR Code vous sera envoyé pour l'entrée.
À bientôt !
""",
    "waiting_list": """
📋 Vous êtes sur liste d'attente.

📅 Date: {date}
⏰ Heure: {time}
👥 Couverts: {guests}

Nous vous contacterons dès qu'une table se libère.
""",
}

# ============================================
# Classification des intentions
# ============================================

INTENT_CLASSIFICATION_PROMPT = """
Analyse le message du client et détermine son intention principale.

Catégories :
- new_reservation : Le client veut faire une nouvelle réservation
- check_availability : Le client veut vérifier les disponibilités
- get_recommendations : Le client demande des recommandations de plats
- modify_reservation : Le client veut modifier une réservation existante
- cancel_reservation : Le client veut annuler une réservation
- payment : Le client veut effectuer un paiement
- human_handoff : Le client demande explicitement un humain
- greeting : Le client salue
- goodbye : Le client dit au revoir
- chitchat : Conversation informelle
- unknown : Intention non identifiée

Message: {message}
"""