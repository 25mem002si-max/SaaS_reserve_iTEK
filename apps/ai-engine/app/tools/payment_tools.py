"""Outils de paiement."""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

from app.tools.base import BaseTool, ToolResult


class CreatePaymentParams(BaseModel):
    """Paramètres pour create_payment."""
    reservation_id: str = Field(description="ID de la réservation")
    amount: float = Field(description="Montant à payer", ge=0.01)
    currency: str = Field(default="USD", description="Devise (USD ou CDF)")
    phone_number: str = Field(description="Numéro de téléphone Mobile Money")
    provider: str = Field(description="Fournisseur (m_pesa, orange_money, airtel_money)")


class CreatePaymentTool(BaseTool):
    """Outil pour créer une demande de paiement Mobile Money."""
    
    name = "create_payment"
    description = "Crée une demande de paiement Mobile Money pour un acompte."
    
    def get_parameters_schema(self) -> Dict[str, Any]:
        return CreatePaymentParams.model_json_schema()
    
    def execute(self, **kwargs) -> ToolResult:
        try:
            params = CreatePaymentParams(**kwargs)
            
            self.logger.info(f"Création paiement - {params.reservation_id}, {params.amount} {params.currency}")
            
            # TODO: Appeler le backend Dev2 (Mobile Money)
            # Pour l'instant, simulation
            from datetime import datetime
            payment_id = f"pay-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            return ToolResult(
                success=True,
                data={
                    "payment_id": payment_id,
                    "status": "PENDING",
                    "provider_reference": f"ref-{payment_id}",
                    "message": "Demande de paiement envoyée. Veuillez confirmer sur votre téléphone.",
                },
                message="Demande de paiement créée avec succès",
            )
                
        except Exception as e:
            self.logger.error(f"Erreur create_payment: {e}")
            return ToolResult(success=False, error=str(e), message="Erreur lors de la création du paiement")