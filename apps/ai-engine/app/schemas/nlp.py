"""Schémas pour l'extraction NLP."""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, model_validator


class ExtractedInformation(BaseModel):
    """Informations extraites du message utilisateur par l'Agent NLP."""
    
    # Réservation
    date: Optional[datetime] = Field(
        default=None,
        description="Date de réservation extraite"
    )
    time: Optional[str] = Field(
        default=None,
        pattern=r"^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$",
        description="Heure de réservation (HH:MM)"
    )
    guests_count: Optional[int] = Field(
        default=None,
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
        description="Budget estimé"
    )
    currency: Optional[str] = Field(
        default=None,
        pattern="^(USD|CDF)$",
        description="Devise (USD ou CDF)"
    )
    
    # ⚠️ AJOUT: Zone et occasion (c'était l'erreur)
    preferred_zone: Optional[str] = Field(
        default=None,
        description="Zone préférée (VIP, Terrasse, Intérieur)"
    )
    special_occasion: Optional[str] = Field(
        default=None,
        description="Occasion spéciale (anniversaire, etc.)"
    )
    
    # Réservation existante
    reservation_id: Optional[str] = Field(
        default=None,
        description="ID de réservation existante (pour modification/annulation)"
    )
    
    # Autres
    notes: Optional[str] = Field(
        default=None,
        description="Notes supplémentaires"
    )
    
    # Métadonnées d'extraction
    raw_text: str = Field(
        description="Texte original analysé"
    )
    confidence: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Niveau de confiance de l'extraction"
    )
    extracted_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Date d'extraction"
    )
    
    @model_validator(mode="after")
    def validate_currency(self) -> "ExtractedInformation":
        """Valide que la devise est correcte."""
        if self.currency and self.currency not in ["USD", "CDF"]:
            self.currency = "USD"
        return self
    
    def has_complete_reservation_info(self) -> bool:
        """Vérifie si toutes les informations de réservation sont présentes."""
        return all([
            self.date is not None,
            self.time is not None,
            self.guests_count is not None,
        ])
    
    def missing_fields(self) -> List[str]:
        """Retourne la liste des champs manquants pour une réservation."""
        missing = []
        if self.date is None:
            missing.append("date")
        if self.time is None:
            missing.append("time")
        if self.guests_count is None:
            missing.append("guests_count")
        return missing


class MissingInformation(BaseModel):
    """Information manquante à demander à l'utilisateur."""
    
    field: str = Field(
        description="Nom du champ manquant"
    )
    question: str = Field(
        description="Question à poser à l'utilisateur"
    )
    example: Optional[str] = Field(
        default=None,
        description="Exemple de réponse attendue"
    )
    possible_values: Optional[List[str]] = Field(
        default=None,
        description="Valeurs possibles si applicable"
    )


class NLPResult(BaseModel):
    """Résultat complet de l'analyse NLP."""
    
    extracted: ExtractedInformation = Field(
        description="Informations extraites"
    )
    missing: List[MissingInformation] = Field(
        default_factory=list,
        description="Informations manquantes à demander"
    )
    is_complete: bool = Field(
        description="Toutes les informations nécessaires sont présentes"
    )
    next_question: Optional[str] = Field(
        default=None,
        description="Prochaine question à poser si incomplet"
    )
    
    @classmethod
    def from_extracted(cls, extracted: ExtractedInformation) -> "NLPResult":
        """Crée un NLPResult à partir d'une extraction."""
        missing_fields = extracted.missing_fields()
        missing = [
            MissingInformation(
                field=field,
                question=cls._get_question_for_field(field),
                example=cls._get_example_for_field(field),
            )
            for field in missing_fields
        ]
        return cls(
            extracted=extracted,
            missing=missing,
            is_complete=len(missing) == 0,
            next_question=missing[0].question if missing else None,
        )
    
    @staticmethod
    def _get_question_for_field(field: str) -> str:
        """Retourne la question appropriée pour un champ."""
        questions = {
            "date": "Pour quelle date souhaitez-vous réserver ?",
            "time": "À quelle heure souhaitez-vous venir ?",
            "guests_count": "Pour combien de personnes ?",
        }
        return questions.get(field, f"Pouvez-vous me donner plus d'informations sur {field} ?")
    
    @staticmethod
    def _get_example_for_field(field: str) -> str:
        """Retourne un exemple pour un champ."""
        examples = {
            "date": "Par exemple : demain, vendredi, 25/12/2026",
            "time": "Par exemple : 19h, 20h30, 20:00",
            "guests_count": "Par exemple : 4, 2 personnes",
        }
        return examples.get(field, "")