"""Schémas pour les informations client."""

from typing import Optional
from pydantic import BaseModel, Field, EmailStr


class CustomerContext(BaseModel):
    """Informations sur le client."""
    
    customer_id: Optional[str] = Field(
        default=None,
        description="Identifiant du client si connu"
    )
    name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="Nom du client"
    )
    phone: Optional[str] = Field(
        default=None,
        pattern=r"^\+?[0-9]{8,15}$",
        description="Numéro de téléphone (format international)"
    )
    email: Optional[EmailStr] = Field(
        default=None,
        description="Adresse email"
    )
    preferred_language: str = Field(
        default="fr",
        description="Langue préférée"
    )
    
    def is_identified(self) -> bool:
        """Vérifie si le client est identifié."""
        return bool(self.name and self.phone)