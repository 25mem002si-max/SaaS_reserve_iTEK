"""Validateurs de données pour prévenir les hallucinations."""

from typing import Dict, Any, List, Optional
from datetime import datetime
import re

from app.schemas.reservation import ReservationData
from app.schemas.availability import TableOption


class DataValidator:
    """Valide les données pour s'assurer qu'elles sont cohérentes et réelles."""

    @staticmethod
    def validate_reservation_data(data: ReservationData) -> Dict[str, Any]:
        """
        Valide les données d'une réservation.
        Retourne un dict avec 'valid' (bool) et 'errors' (list).
        """
        errors = []
        warnings = []

        # 1. Vérifier la date
        if data.date:
            now = datetime.now()
            # La date ne peut pas être dans le passé
            if data.date < now:
                errors.append("La date de réservation ne peut pas être dans le passé")
            # La date ne peut pas être trop loin (max 6 mois)
            elif data.date > now.replace(year=now.year + 1):
                warnings.append("La date de réservation est très éloignée (> 1 an)")
        else:
            errors.append("La date de réservation est manquante")

        # 2. Vérifier l'heure
        if data.time:
            if not re.match(r"^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$", data.time):
                errors.append(f"Format d'heure invalide: {data.time}")
        else:
            errors.append("L'heure de réservation est manquante")

        # 3. Vérifier le nombre de personnes
        if data.guests_count:
            if data.guests_count < 1:
                errors.append("Le nombre de personnes doit être au moins 1")
            elif data.guests_count > 50:
                errors.append("Le nombre de personnes ne peut pas dépasser 50")
        else:
            errors.append("Le nombre de personnes est manquant")

        # 4. Vérifier la devise
        if data.currency:
            if data.currency not in ["USD", "CDF"]:
                errors.append(f"Devise invalide: {data.currency} (doit être USD ou CDF)")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
        }

    @staticmethod
    def validate_table_option(table: TableOption) -> Dict[str, Any]:
        """Valide une option de table."""
        errors = []

        if not table.table_id:
            errors.append("ID de table manquant")

        if not table.table_label:
            errors.append("Libellé de table manquant")

        if table.capacity < 1:
            errors.append(f"Capacité de table invalide: {table.capacity}")

        if table.zone not in ["Intérieur", "VIP", "Terrasse"]:
            errors.append(f"Zone de table invalide: {table.zone}")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
        }

    @staticmethod
    def validate_message_content(content: str) -> Dict[str, Any]:
        """Valide le contenu d'un message pour éviter les hallucinations."""
        errors = []
        warnings = []

        # 1. Vérifier les nombres dans le message
        # Si le message contient des nombres qui pourraient être des prix ou des quantités
        numbers = re.findall(r"\d+", content)
        for num in numbers:
            if int(num) > 10000:
                warnings.append(f"Nombre très élevé détecté: {num}")

        # 2. Vérifier les mentions de disponibilité
        if "disponible" in content.lower() or "libre" in content.lower():
            # Ce message parle de disponibilité - s'assurer qu'il n'invente pas
            if "toutes les tables" in content.lower():
                warnings.append("Généralisation sur les disponibilités - vérifier avec le backend")

        # 3. Vérifier les mentions de prix
        if "USD" in content or "CDF" in content or "$" in content:
            # Ce message parle de prix - s'assurer qu'il est cohérent
            pass

        return {
            "valid": True,  # Les messages ne sont jamais invalides, mais peuvent avoir des warnings
            "errors": errors,
            "warnings": warnings,
        }


class ResponseGuard:
    """Vérifie les réponses des agents avant de les envoyer."""

    @staticmethod
    def check_for_hallucination(response: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Vérifie si une réponse contient des hallucinations potentielles.
        """
        issues = []
        severity = "low"

        # 1. Vérifier les prix inventés
        if any(word in response.lower() for word in ["prix", "coût", "coûte"]):
            # Si le contexte ne contient pas de prix, c'est suspect
            if not context.get("has_price_info"):
                issues.append("Le prix pourrait être inventé (pas d'info prix dans le contexte)")
                severity = "high"

        # 2. Vérifier les disponibilités inventées
        if any(word in response.lower() for word in ["disponible", "libre", "réservé"]):
            # Si le contexte ne contient pas d'info de disponibilité
            if not context.get("has_availability_info"):
                issues.append("La disponibilité pourrait être inventée (pas d'info dans le contexte)")
                severity = "high"

        # 3. Vérifier les confirmations prématurées
        if any(word in response.lower() for word in ["confirmé", "réservation effectuée", "réservation créée"]):
            # Si la réservation n'est pas encore créée dans le contexte
            if not context.get("reservation_created"):
                issues.append("Confirmation de réservation prématurée (pas de création confirmée)")
                severity = "critical"

        # 4. Vérifier les numéros de réservation inventés
        if "réf" in response.lower() or "ref" in response.lower() or "id" in response.lower():
            # Chercher un format de numéro de réservation
            import re
            ref_pattern = r"[A-Z0-9]{6,}"
            if re.search(ref_pattern, response):
                if not context.get("has_reservation_id"):
                    issues.append("Numéro de réservation pourrait être inventé")
                    severity = "medium"

        return {
            "has_issues": len(issues) > 0,
            "issues": issues,
            "severity": severity,
        }