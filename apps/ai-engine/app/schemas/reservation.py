"""Schémas pour la gestion des réservations."""

from typing import Optional, List
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, model_validator


class ReservationStatus(str, Enum):
    """Statuts possibles d'une réservation."""
    PENDING_PAYMENT = "PENDING_PAYMENT"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"
    COMPLETED = "COMPLETED"
    NO_SHOW = "NO_SHOW"
    WAITING_LIST = "WAITING_LIST"


class ReservationData(BaseModel):
    """Données d'une réservation en cours de création."""
    
    # Informations de base
    date: datetime = Field(
        description="Date de réservation"
    )
    time: str = Field(
        pattern=r"^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$",
        description="Heure de réservation (HH:MM)"
    )
    guests_count: int = Field(
        ge=1,
        le=50,
        description="Nombre de personnes"
    )
    
    # Préférences
    preferences: List[str] = Field(
        default_factory=list,
        description="Préférences alimentaires"
    )
    allergies: List[str] = Field(
        default_factory=list,
        description="Allergies déclarées"
    )
    
    # Budget
    budget: Optional[float] = Field(
        default=None,
        ge=0,
        description="Budget estimé par personne ou total"
    )
    currency: str = Field(
        default="USD",
        pattern="^(USD|CDF)$",
        description="Devise (USD ou CDF)"
    )
    
    # Table
    table_id: Optional[str] = Field(
        default=None,
        description="ID de la table réservée"
    )
    table_label: Optional[str] = Field(
        default=None,
        description="Libellé de la table"
    )
    
    # Acompte
    deposit_required: bool = Field(
        default=False,
        description="Un acompte est-il requis ?"
    )
    deposit_amount: Optional[float] = Field(
        default=None,
        ge=0,
        description="Montant de l'acompte"
    )
    
    # Client
    customer_name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="Nom du client"
    )
    customer_phone: Optional[str] = Field(
        default=None,
        pattern=r"^\+?[0-9]{8,15}$",
        description="Téléphone du client"
    )
    
    # Métadonnées
    notes: Optional[str] = Field(
        default=None,
        description="Notes supplémentaires"
    )
    source: str = Field(
        default="ai_engine",
        description="Source de la réservation"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Date de création"
    )
    
    def is_complete(self) -> bool:
        """Vérifie si toutes les données de réservation sont complètes."""
        return all([
            self.date is not None,
            self.time is not None,
            self.guests_count is not None,
            self.table_id is not None,
            self.customer_name is not None,
            self.customer_phone is not None,
        ])
    
    def to_request(self) -> "ReservationRequest":
        """Convertit en ReservationRequest pour l'API."""
        return ReservationRequest(
            restaurant_id="",  # Sera rempli par le contexte
            table_id=self.table_id or "",
            customer_name=self.customer_name or "",
            customer_phone=self.customer_phone or "",
            reservation_date=self.date,
            guests_count=self.guests_count,
            preferences=self.preferences,
            allergies=self.allergies,
            deposit_amount=self.deposit_amount or 0.0,
            notes=self.notes,
        )


class ReservationRequest(BaseModel):
    """Requête de création de réservation pour le backend (Dev2)."""
    
    restaurant_id: str = Field(
        description="ID du restaurant"
    )
    table_id: str = Field(
        description="ID de la table à réserver"
    )
    customer_name: str = Field(
        min_length=1,
        max_length=100,
        description="Nom du client"
    )
    customer_phone: str = Field(
        pattern=r"^\+?[0-9]{8,15}$",
        description="Téléphone du client"
    )
    reservation_date: datetime = Field(
        description="Date et heure de réservation"
    )
    guests_count: int = Field(
        ge=1,
        le=50,
        description="Nombre de personnes"
    )
    preferences: List[str] = Field(
        default_factory=list,
        description="Préférences alimentaires"
    )
    allergies: List[str] = Field(
        default_factory=list,
        description="Allergies"
    )
    deposit_amount: float = Field(
        default=0.0,
        ge=0.0,
        description="Montant de l'acompte en USD"
    )
    notes: Optional[str] = Field(
        default=None,
        description="Notes supplémentaires"
    )


class ReservationConfirmation(BaseModel):
    """Confirmation de réservation finale."""
    
    reservation_id: str = Field(
        description="ID de la réservation créée"
    )
    table_id: str = Field(
        description="ID de la table réservée"
    )
    table_label: str = Field(
        description="Libellé de la table"
    )
    customer_name: str = Field(
        description="Nom du client"
    )
    date: datetime = Field(
        description="Date de réservation"
    )
    guests_count: int = Field(
        description="Nombre de personnes"
    )
    status: ReservationStatus = Field(
        description="Statut de la réservation"
    )
    qr_code_token: Optional[str] = Field(
        default=None,
        description="Token du QR Code pour l'entrée"
    )
    pdf_url: Optional[str] = Field(
        default=None,
        description="URL du PDF de confirmation"
    )
    deposit_paid: bool = Field(
        default=False,
        description="L'acompte a-t-il été payé ?"
    )
    deposit_amount: float = Field(
        default=0.0,
        description="Montant de l'acompte"
    )
    currency: str = Field(
        default="USD",
        description="Devise"
    )
    confirmed_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Date de confirmation"
    )
    message: str = Field(
        description="Message de confirmation pour le client"
    )
    
    @classmethod
    def create_confirmation_message(cls, data: "ReservationConfirmation") -> str:
        """Crée un message de confirmation formaté."""
        status_text = "✅ confirmée" if data.status == ReservationStatus.CONFIRMED else "⏳ en attente de paiement"
        deposit_text = f" - Acompte: {data.deposit_amount} {data.currency}" if data.deposit_amount > 0 else ""
        
        return f"""
🎉 Réservation {status_text} !

📅 Date: {data.date.strftime('%d/%m/%Y')}
⏰ Heure: {data.date.strftime('%H:%M')}
👥 {data.guests_count} personnes
📍 Table: {data.table_label}
{deposit_text}

Un QR Code vous sera envoyé pour l'entrée.
À très bientôt !
"""