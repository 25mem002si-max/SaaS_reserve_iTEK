#!/bin/bash
# scripts/setup.sh

set -e  # Arrêt en cas d'erreur

echo "🚀 Installation du module AI Engine..."

# Couleurs pour les messages
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 1. Vérification de Python
echo -e "${YELLOW}📌 Vérification de Python...${NC}"
if ! command -v python3.11 &> /dev/null; then
    echo -e "${RED}❌ Python 3.11 non trouvé. Veuillez l'installer.${NC}"
    echo "   Ubuntu/Debian: sudo apt install python3.11 python3.11-venv"
    echo "   macOS: brew install python@3.11"
    exit 1
fi
echo -e "${GREEN}✅ Python $(python3.11 --version) trouvé${NC}"

# 2. Création de l'environnement virtuel
echo -e "${YELLOW}📌 Création de l'environnement virtuel...${NC}"
if [ ! -d "venv" ]; then
    python3.11 -m venv venv
    echo -e "${GREEN}✅ Environnement virtuel créé${NC}"
else
    echo -e "${GREEN}✅ Environnement virtuel existe déjà${NC}"
fi

# 3. Activation et installation
echo -e "${YELLOW}📌 Activation de l'environnement et installation des dépendances...${NC}"
source venv/bin/activate

# 4. Mise à jour de pip
pip install --upgrade pip

# 5. Installation des dépendances
echo -e "${YELLOW}📌 Installation des dépendances depuis requirements.txt...${NC}"
pip install -r requirements.txt

# 6. Installation en mode développement (pour les imports)
echo -e "${YELLOW}📌 Installation du module en mode développement...${NC}"
pip install -e .

# 7. Création des dossiers manquants
echo -e "${YELLOW}📌 Création des dossiers de l'application...${NC}"
mkdir -p app/prompts
mkdir -p tests/conversations/fixtures
mkdir -p logs

# 8. Copie du .env si absent
echo -e "${YELLOW}📌 Configuration du fichier .env...${NC}"
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo -e "${GREEN}✅ .env créé à partir de .env.example${NC}"
    echo -e "${YELLOW}⚠️  VEUILLEZ ÉDITER .env AVEC VOS CLÉS API${NC}"
else
    echo -e "${GREEN}✅ .env existe déjà${NC}"
fi

# 9. Vérification
echo -e "${YELLOW}📌 Vérification de l'installation...${NC}"
python -c "import langgraph, langchain, pydantic, fastapi; print('✅ Tous les modules importés avec succès')"

echo -e "${GREEN}✅ Installation terminée !${NC}"
echo ""
echo -e "Pour activer l'environnement :"
echo -e "  ${GREEN}source venv/bin/activate${NC}"
echo ""
echo -e "Pour démarrer le serveur :"
echo -e "  ${GREEN}uvicorn app.main:app --reload --host 0.0.0.0 --port 8001${NC}"