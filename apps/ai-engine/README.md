# AI Engine - Réservations de restaurants

Service FastAPI en Python qui orchestre les agents conversationnels et les opérations de réservation.

## Prérequis

- Python 3.11 ou supérieur. Python 3.11 est la version utilisée par le Dockerfile et les scripts d'installation.
- Git, si le projet est récupéré depuis un dépôt.
- Redis 7 si le service Redis est utilisé. Docker Compose peut le démarrer.
- L'API Backend Dev2 si les réservations, disponibilités et paiements doivent être connectés. L'AI Engine ne se connecte pas directement à PostgreSQL.
- Une clé API du fournisseur LLM choisi si `USE_LLM=true`.

Docker Desktop avec Compose est nécessaire uniquement pour le démarrage par conteneurs. Pour un démarrage Python local, Redis et le backend sont des services séparés.

## Dépendances

Les dépendances Python déclarées du projet sont dans [`requirements.txt`](requirements.txt). Elles comprennent FastAPI/Uvicorn, LangGraph/LangChain, les intégrations OpenAI/Anthropic/Gemini, Pydantic, HTTPX, Redis, les utilitaires et les outils de test.

Les plages de versions du fichier sont des contraintes de compatibilité, pas un verrouillage exact de chaque version installée. Une nouvelle installation peut donc résoudre des versions plus récentes à l'intérieur de ces plages. Le fichier `pyproject.toml` ne déclare pas ces dépendances : pour cette application, installer `requirements.txt` est nécessaire.

PostgreSQL n'est pas une dépendance Python de l'AI Engine. Il est destiné au backend Dev2. Redis et PostgreSQL sont des services externes, pas des bibliothèques Python à installer avec `pip`.

## Installation locale - Windows PowerShell

Depuis le dossier racine du projet :

```powershell
py -3.11 --version
py -3.11 -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -e .
```

Si PowerShell bloque l'activation pour cette session, exécuter d'abord :

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
```

Puis relancer la commande d'activation. Le script `scripts\setup.bat` automatise également l'installation sur Windows :

```powershell
.\\scripts\\setup.bat
```

## Installation locale - Linux ou macOS

Depuis le dossier racine du projet :

```bash
python3.11 --version
python3.11 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -e .
```

Le script `scripts/setup.sh` automatise ces étapes sur les systèmes Unix :

```bash
bash scripts/setup.sh
```

## Configuration

Créer le fichier local `.env` à partir du modèle, puis renseigner uniquement les services utilisés :

```powershell
Copy-Item .env.example .env
```

Sur Linux/macOS :

```bash
cp .env.example .env
```

Paramètres habituels :

- `USE_LLM=true` active les appels au modèle. Configurer la clé correspondant à `LLM_PROVIDER` (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY` ou `GEMINI_API_KEY`).
- `BACKEND_ENABLED=true` active les appels à l'API du backend. Définir `BACKEND_API_URL` et, si demandé par le backend, `BACKEND_API_KEY`.
- `REDIS_URL` indique l'adresse Redis. En local, la valeur par défaut est `redis://localhost:6379/0`.
- Les variables `WHATSAPP_*` ne sont nécessaires que pour intégrer WhatsApp.

Ne jamais placer de vrais secrets dans `.env.example` ni les committer. Le fichier `.env` est exclu par `.gitignore`.

Pour une exécution locale, lancer les services dont l'application dépend dans leurs propres projets ou avec Docker Compose. Le service backend Dev2 et ses migrations PostgreSQL ne sont pas fournis par ce dépôt.

## Démarrage

Avec l'environnement virtuel activé :

```powershell
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

L'API est disponible sur `http://localhost:8001`. La documentation interactive se trouve sur `http://localhost:8001/docs`, la vérification de santé sur `http://localhost:8001/health` et la page de test sur `http://localhost:8001/test`.

## Démarrage avec Docker Compose

Depuis le dossier racine :

```powershell
docker compose up --build redis postgres
```

Cette commande démarre Redis et PostgreSQL. Le service backend est commenté dans `docker-compose.yml` et doit être lancé séparément par Dev2. Pour lancer également l'AI Engine en conteneur :

```powershell
docker compose up --build redis postgres ai-engine
```

Vérifier que les URLs et les secrets de backend/LLM sont disponibles dans l'environnement du conteneur avant d'activer ces intégrations. Le service `ai-engine` de Compose utilise `http://backend:8000`; ce nom d'hôte ne fonctionne que lorsque le backend est présent sur le même réseau Docker.

Pour arrêter les services sans supprimer les données :

```powershell
docker compose down
```

Les données PostgreSQL et Redis sont conservées dans les volumes nommés. Pour les supprimer volontairement, `docker compose down -v` efface ces volumes et leurs données.

## Vérification et tests

Avec l'environnement virtuel activé :

```powershell
python scripts/check_install.py
python -m pytest
```

Le même `python -m pytest` fonctionne dans PowerShell, Linux et macOS. Les options de test sont configurées dans `pyproject.toml`.

## Réinstallation propre

Pour reconstruire l'environnement Python sans supprimer les fichiers du projet :

```powershell
deactivate
Remove-Item -Recurse -Force venv
py -3.11 -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -e .
Copy-Item .env.example .env
```

Ne recopier `.env.example` que si aucun `.env` n'existe : cette opération ne restaure pas les clés API et paramètres privés de l'ancienne machine. Les données de Redis/PostgreSQL sont indépendantes du dossier `venv` et sont conservées dans leurs services ou volumes Docker.

Pour obtenir des versions Python strictement identiques entre les machines, le projet devra ajouter et maintenir un fichier de verrouillage (par exemple généré avec `pip-compile`). `requirements.txt` seul garantit aujourd'hui les plages compatibles déclarées, pas des résolutions identiques dans le temps.
