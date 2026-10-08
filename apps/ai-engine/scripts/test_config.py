#!/usr/bin/env python
"""Script pour tester la configuration."""

import sys
from pathlib import Path

# Ajouter le chemin du projet
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config.settings import settings
from app.config.logging import setup_logging, get_logger


def test_config():
    """Teste que la configuration est valide."""
    print("=" * 60)
    print("🔍 TEST DE CONFIGURATION")
    print("=" * 60)
    
    # 1. Settings
    print("\n📌 Configuration chargée :")
    print(f"   - LLM Provider: {settings.llm_provider}")
    print(f"   - OpenAI Model: {settings.openai_model}")
    print(f"   - Backend API: {settings.backend_api_url}")
    print(f"   - Redis URL: {settings.redis_url}")
    print(f"   - Environment: {settings.environment}")
    print(f"   - Log Level: {settings.log_level}")
    
    # 2. Vérification des clés API
    print("\n📌 Vérification des clés API :")
    if settings.openai_api_key:
        masked = settings.openai_api_key[:8] + "..." + settings.openai_api_key[-4:]
        print(f"   - OpenAI API Key: {masked} ✅")
    else:
        print("   - OpenAI API Key: Non définie ❌")
    
    # 3. Vérification du backend
    print("\n📌 Vérification du backend :")
    if settings.backend_api_url:
        print(f"   - Backend URL: {settings.backend_api_url} ✅")
    else:
        print("   - Backend URL: Non définie ❌")
    
    # 4. Vérification des paths
    print("\n📌 Vérification des paths :")
    print(f"   - Project Root: {settings.project_root}")
    print(f"   - Prompts Dir: {settings.prompts_dir}")
    print(f"   - Logs Dir: {settings.logs_dir}")
    
    # 5. Logging
    print("\n📌 Test du logging :")
    setup_logging()
    logger = get_logger()
    logger.info("test_message", test=True, user="dev1")
    print("   - Log envoyé ✅")
    
    print("\n" + "=" * 60)
    print("✅ Configuration valide !")
    print("=" * 60)
    
    return True


if __name__ == "__main__":
    try:
        success = test_config()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Erreur de configuration: {e}")
        sys.exit(1)