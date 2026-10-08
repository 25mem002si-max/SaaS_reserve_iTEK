@echo off
REM scripts/setup.bat
REM Script d'installation pour Windows

echo ========================================
echo AI Engine - Installation sur Windows
echo ========================================
echo.

REM 1. Vérifier Python
echo [1/7] Verification de Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERREUR: Python n'est pas installe ou n'est pas dans le PATH.
    echo Veuillez installer Python 3.11 ou superieur.
    pause
    exit /b 1
)
echo OK

REM 2. Créer l'environnement virtuel
echo [2/7] Creation de l'environnement virtuel...
if not exist venv (
    python -m venv venv
    echo Environnement virtuel cree
) else (
    echo Environnement virtuel existe deja
)

REM 3. Activer et installer
echo [3/7] Activation et installation des dependances...
call .\venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt

REM 4. Copier .env
echo [4/7] Configuration du fichier .env...
if not exist .env (
    copy .env.example .env
    echo Fichier .env cree
    echo VEUILLEZ EDITER .env AVEC VOS CLES API
) else (
    echo Fichier .env existe deja
)

REM 5. Créer les dossiers
echo [5/7] Creation des dossiers...
if not exist app\prompts mkdir app\prompts
if not exist logs mkdir logs
if not exist tests\conversations\fixtures mkdir tests\conversations\fixtures

REM 6. Vérification
echo [6/7] Verification de l'installation...
python -c "import langgraph, langchain, pydantic, fastapi; print('Tous les modules importes avec succes')"

REM 7. Installation en mode développement
echo [7/7] Installation en mode developpement...
pip install -e .

echo.
echo ========================================
echo Installation terminee !
echo ========================================
echo.
echo Pour activer l'environnement :
echo   .\venv\Scripts\activate
echo.
echo Pour demarrer le serveur :
echo   uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
echo.
pause