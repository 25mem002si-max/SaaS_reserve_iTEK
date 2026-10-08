"""Chargement des prompts depuis les fichiers."""

from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger("ai_engine.prompts")


class PromptLoader:
    """Charge les prompts depuis les fichiers texte."""

    def __init__(self, prompts_dir: Optional[Path] = None):
        if prompts_dir is None:
            # Par défaut, utiliser le dossier prompts dans le même répertoire
            self.prompts_dir = Path(__file__).parent
        else:
            self.prompts_dir = Path(prompts_dir)
        
        self._cache: dict = {}

    def load(self, name: str) -> str:
        """Charge un prompt depuis un fichier."""
        if name in self._cache:
            return self._cache[name]
        
        file_path = self.prompts_dir / f"{name}.txt"
        
        if not file_path.exists():
            logger.warning(f"Prompt non trouvé: {file_path}")
            return self._get_default_prompt(name)
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                self._cache[name] = content
                logger.info(f"✅ Prompt chargé: {name}")
                return content
        except Exception as e:
            logger.error(f"Erreur chargement prompt {name}: {e}")
            return self._get_default_prompt(name)

    def _get_default_prompt(self, name: str) -> str:
        """Retourne un prompt par défaut."""
        defaults = {
            "nlp": "Tu es un agent NLP convivial et précis. Tu extrais les informations utiles d'un message client en français, dans un contexte de restaurant RDC, sans inventer d'informations.",
            "orchestrator": "Tu es un orchestrateur chaleureux et professionnel. Tu identifie l'intention du client, garde un ton naturel et humain, et choisis le bon agent spécialisé selon le contexte de réservation et de service restaurant.",
            "reservation": "Tu es un agent de réservation attentionné et efficace. Tu gères les demandes de réservation avec un ton naturel, précis et orienté client en français.",
            "recommendation": "Tu es un agent de recommandation de restaurant bienveillant. Tu proposes des plats adaptés aux goûts, allergies et budget du client, avec un ton chaleureux et humain.",
            "payment": "Tu es un agent de paiement fiable et rassurant. Tu guides le client sur le paiement avec clarté, sans ambiguïté et dans un contexte restaurant professionnel.",
            "notification": "Tu es un agent de notification utile et cordial. Tu envoies des confirmations de réservation et rappels de manière claire, naturelle et conviviale.",
        }
        return defaults.get(name, f"Prompt par défaut pour {name}")


# Instance globale
_loader: Optional[PromptLoader] = None


def get_prompt_loader() -> PromptLoader:
    """Retourne l'instance du chargeur de prompts."""
    global _loader
    if _loader is None:
        _loader = PromptLoader()
    return _loader


def load_prompt(name: str) -> str:
    """Charge un prompt par son nom."""
    return get_prompt_loader().load(name)