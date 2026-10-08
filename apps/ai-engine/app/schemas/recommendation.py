"""Schémas pour les recommandations de plats."""

from typing import Optional, List
from pydantic import BaseModel, Field


class RecommendedItem(BaseModel):
    """Item recommandé (plat, boisson, menu)."""
    
    id: str = Field(
        description="ID de l'item"
    )
    name: str = Field(
        description="Nom de l'item"
    )
    category: str = Field(
        description="Catégorie (entrée, plat, dessert, boisson, menu)"
    )
    description: Optional[str] = Field(
        default=None,
        description="Description de l'item"
    )
    price: float = Field(
        ge=0,
        description="Prix"
    )
    currency: str = Field(
        default="USD",
        pattern="^(USD|CDF)$",
        description="Devise"
    )
    match_reason: str = Field(
        description="Raison de la recommandation"
    )
    is_recommended: bool = Field(
        default=True,
        description="Est-ce une recommandation ?"
    )


class RecommendationRequest(BaseModel):
    """Requête de recommandation."""
    
    restaurant_id: str = Field(
        description="ID du restaurant"
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
        description="Allergies à éviter"
    )
    budget: Optional[float] = Field(
        default=None,
        ge=0,
        description="Budget par personne"
    )
    currency: str = Field(
        default="USD",
        pattern="^(USD|CDF)$",
        description="Devise"
    )
    special_occasion: Optional[str] = Field(
        default=None,
        description="Occasion spéciale"
    )
    max_items: int = Field(
        default=5,
        ge=1,
        le=10,
        description="Nombre maximum d'items à recommander"
    )


class RecommendationResult(BaseModel):
    """Résultat des recommandations."""
    
    restaurant_id: str = Field(
        description="ID du restaurant"
    )
    items: List[RecommendedItem] = Field(
        default_factory=list,
        description="Items recommandés"
    )
    total_estimated_price: Optional[float] = Field(
        default=None,
        description="Prix total estimé"
    )
    currency: str = Field(
        default="USD",
        description="Devise"
    )
    message: str = Field(
        description="Message d'introduction pour le client"
    )
    
    def get_by_category(self, category: str) -> List[RecommendedItem]:
        """Filtre les items par catégorie."""
        return [item for item in self.items if item.category == category]
    
    def get_recommendation_text(self) -> str:
        """Génère un texte de recommandation pour le client."""
        if not self.items:
            return "Je n'ai pas trouvé de recommandations correspondant à vos critères."
        
        lines = [self.message, ""]
        for item in self.items:
            lines.append(f"🍽️ **{item.name}** - {item.price} {item.currency}")
            if item.description:
                lines.append(f"   {item.description}")
            lines.append(f"   💡 {item.match_reason}")
            lines.append("")
        
        if self.total_estimated_price:
            lines.append(f"💵 Prix total estimé: {self.total_estimated_price} {self.currency}")
        
        return "\n".join(lines)