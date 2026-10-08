#!/usr/bin/env python
"""Script pour vérifier que l'installation fonctionne."""

import sys


def check_imports():
    """Vérifie que tous les imports essentiels fonctionnent."""
    required = [
        "langgraph",
        "langchain",
        "langchain_openai",
        "langchain_anthropic",
        "pydantic",
        "pydantic_settings",
        "fastapi",
        "httpx",
        "redis",
    ]
    
    missing = []
    for module in required:
        try:
            __import__(module.replace("-", "_"))
            print(f"✅ {module}")
        except ImportError as e:
            print(f"❌ {module}: {e}")
            missing.append(module)
    
    if missing:
        print(f"\n❌ Modules manquants: {', '.join(missing)}")
        return False
    else:
        print("\n✅ Tous les modules sont installés !")
        return True


def check_env_file():
    """Vérifie que le fichier .env existe."""
    import os
    if os.path.exists(".env"):
        print("✅ .env existe")
        return True
    else:
        print("⚠️  .env n'existe pas. Copiez .env.example vers .env")
        return False


def main():
    print("🔍 Vérification de l'installation...\n")
    
    # Vérification Python
    print(f"Python: {sys.version}")
    
    # Vérification des imports
    imports_ok = check_imports()
    
    # Vérification du .env
    env_ok = check_env_file()
    
    if imports_ok and env_ok:
        print("\n✅ Installation prête !")
        return 0
    else:
        print("\n⚠️  Installation incomplète. Vérifiez les messages ci-dessus.")
        return 1


if __name__ == "__main__":
    sys.exit(main())