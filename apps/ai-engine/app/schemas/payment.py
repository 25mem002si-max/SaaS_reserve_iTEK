"""Schémas pour les paiements Mobile Money."""

from typing import Optional
from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field


class PaymentStatus(str, Enum):
    """Statuts possibles d'un paiement."""
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"


class PaymentProvider(str, Enum):
    """Fournisseurs de paiement Mobile Money."""
    M_PESA = "m_pesa"
    ORANGE_MONEY = "orange_money"
    AIRTEL_MONEY = "airtel_money"


class PaymentRequest(BaseModel):
    """Requête de paiement."""
    
    reservation_id: str = Field(
        description="ID de la réservation associée"
    )
    restaurant_id: str = Field(
        description="ID du restaurant"
    )
    amount: float = Field(
        ge=0.01,
        description="Montant à payer"
    )
    currency: str = Field(
        default="USD",
        pattern="^(USD|CDF)$",
        description="Devise"
    )
    phone_number: str = Field(
        pattern=r"^\+?[0-9]{8,15}$",
        description="Numéro de téléphone Mobile Money"
    )
    provider: PaymentProvider = Field(
        description="Fournisseur Mobile Money"
    )
    description: str = Field(
        default="Acompte réservation restaurant",
        description="Description du paiement"
    )


class PaymentResult(BaseModel):
    """Résultat d'un paiement."""
    
    payment_id: str = Field(
        description="ID du paiement"
    )
    reservation_id: str = Field(
        description="ID de la réservation associée"
    )
    status: PaymentStatus = Field(
        description="Statut du paiement"
    )
    amount: float = Field(
        description="Montant payé"
    )
    currency: str = Field(
        description="Devise"
    )
    provider: PaymentProvider = Field(
        description="Fournisseur utilisé"
    )
    provider_reference: Optional[str] = Field(
        default=None,
        description="Référence du fournisseur"
    )
    transaction_id: Optional[str] = Field(
        default=None,
        description="ID de transaction"
    )
    message: Optional[str] = Field(
        default=None,
        description="Message d'information"
    )
    paid_at: Optional[datetime] = Field(
        default=None,
        description="Date de paiement"
    )
    
    def is_successful(self) -> bool:
        """Vérifie si le paiement a réussi."""
        return self.status == PaymentStatus.SUCCESS
    
    def is_pending(self) -> bool:
        """Vérifie si le paiement est en attente."""
        return self.status == PaymentStatus.PENDING
    
    def needs_action(self) -> bool:
        """Vérifie si le paiement nécessite une action."""
        return self.status in [PaymentStatus.PENDING, PaymentStatus.FAILED]