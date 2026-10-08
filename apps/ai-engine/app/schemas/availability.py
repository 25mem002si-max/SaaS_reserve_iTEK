"""Schémas pour la vérification de disponibilité."""

from typing import Optional, List
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class TableStatus(str, Enum):
    """Statuts possibles d'une table."""
    AVAILABLE = "available"
    RESERVED = "reserved"
    OCCUPIED = "occupied"
    LOCKED = "locked"


class TableOption(BaseModel):
    """Option de table disponible."""
    
    table_id: str = Field(
        description="ID de la table"
    )
    table_label: str = Field(
        description="Libellé de la table"
    )
    capacity: int = Field(
        ge=1,
        description="Capacité de la table"
    )
    zone: str = Field(
        description="Zone (VIP, Terrasse, Intérieur)"
    )
    status: TableStatus = Field(
        description="Statut actuel de la table"
    )
    
    def can_accommodate(self, guests: int) -> bool:
        """Vérifie si la table peut accueillir ce nombre de personnes."""
        return self.capacity >= guests and self.status == TableStatus.AVAILABLE


class AvailabilityRequest(BaseModel):
    """Requête de vérification de disponibilité."""
    
    restaurant_id: str = Field(
        description="ID du restaurant"
    )
    date: datetime = Field(
        description="Date et heure souhaitées"
    )
    guests_count: int = Field(
        ge=1,
        le=50,
        description="Nombre de personnes"
    )
    preferred_zone: Optional[str] = Field(
        default=None,
        description="Zone préférée (VIP, Terrasse, Intérieur)"
    )
    time_window_minutes: int = Field(
        default=30,
        ge=0,
        le=120,
        description="Fenêtre de temps en minutes (+/-)"
    )


class AvailabilityResult(BaseModel):
    """Résultat de la vérification de disponibilité."""
    
    restaurant_id: str = Field(
        description="ID du restaurant"
    )
    date: datetime = Field(
        description="Date et heure vérifiées"
    )
    guests_count: int = Field(
        description="Nombre de personnes"
    )
    available: bool = Field(
        description="Au moins une table disponible ?"
    )
    tables: List[TableOption] = Field(
        default_factory=list,
        description="Tables disponibles"
    )
    suggested_time: Optional[datetime] = Field(
        default=None,
        description="Créneau alternatif suggéré"
    )
    message: Optional[str] = Field(
        default=None,
        description="Message d'information"
    )
    
    def get_best_table(self) -> Optional[TableOption]:
        """Retourne la meilleure table disponible."""
        if not self.tables:
            return None
        # Prioriser les tables les plus petites qui peuvent accueillir le groupe
        matching = [t for t in self.tables if t.can_accommodate(self.guests_count)]
        if matching:
            return min(matching, key=lambda t: t.capacity)
        return self.tables[0] if self.tables else None
    
    def get_tables_for_zone(self, zone: str) -> List[TableOption]:
        """Retourne les tables disponibles dans une zone spécifique."""
        return [t for t in self.tables if t.zone.lower() == zone.lower()]