"""Vérifications de sécurité pour les entrées/sorties des agents."""

import re
from typing import Dict, Any, List, Optional


class SafetyGuard:
    """Vérifie la sécurité des entrées et sorties."""

    @staticmethod
    def sanitize_input(text: str) -> str:
        """
        Nettoie une entrée utilisateur.
        """
        if not isinstance(text, str):
            return ""

        # Retirer les caractères de contrôle tout en conservant les retours à la ligne.
        text = "".join(char for char in text if char in "\n\r\t" or ord(char) >= 32)

        # Supprimer les caractères dangereux
        dangerous_chars = ["<", ">", "&", "'", '"']
        for char in dangerous_chars:
            text = text.replace(char, "")
        
        # Limiter la longueur
        if len(text) > 1000:
            text = text[:1000]
        
        return text

    @staticmethod
    def validate_phone_number(phone: str) -> bool:
        """
        Valide un numéro de téléphone.
        """
        # Format international
        if re.match(r"^\+?[0-9]{8,15}$", phone):
            return True
        
        # Format local congolais
        if re.match(r"^(0|\+243)[0-9]{9}$", phone):
            return True
        
        return False

    @staticmethod
    def validate_email(email: str) -> bool:
        """
        Valide une adresse email.
        """
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return bool(re.match(pattern, email))

    @staticmethod
    def validate_payment_amount(amount: float, currency: str) -> bool:
        """
        Valide un montant de paiement.
        """
        if amount <= 0:
            return False
        
        if currency == "USD":
            if amount > 1000:
                return False  # Montant trop élevé
        elif currency == "CDF":
            if amount > 500000:
                return False  # Montant trop élevé
        
        return True


class PIIGuard:
    """Protège les données personnelles."""

    @staticmethod
    def mask_phone_number(phone: str) -> str:
        """Masque un numéro de téléphone."""
        if not phone:
            return phone
        if len(phone) >= 8:
            return phone[:3] + "****" + phone[-3:]
        return phone

    @staticmethod
    def mask_email(email: str) -> str:
        """Masque une adresse email."""
        if not email:
            return email
        parts = email.split("@")
        if len(parts) == 2:
            return parts[0][:2] + "****" + "@" + parts[1]
        return email

    @staticmethod
    def remove_pii(text: str) -> str:
        """Supprime les informations personnelles d'un texte."""
        # Masquer les téléphones
        text = re.sub(r"\+?[0-9]{8,15}", "📱 [NUMÉRO MASQUÉ]", text)
        
        # Masquer les emails
        text = re.sub(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", "[EMAIL MASQUÉ]", text)
        
        return text


# Instance globale
_safety_guard: Optional[SafetyGuard] = None
_pii_guard: Optional[PIIGuard] = None


def get_safety_guard() -> SafetyGuard:
    """Retourne l'instance du garde de sécurité."""
    global _safety_guard
    if _safety_guard is None:
        _safety_guard = SafetyGuard()
    return _safety_guard


def get_pii_guard() -> PIIGuard:
    """Retourne l'instance du garde PII."""
    global _pii_guard
    if _pii_guard is None:
        _pii_guard = PIIGuard()
    return _pii_guard