# Restaurant SaaS

Projet SaaS de gestion et de réservation pour restaurants.

## 🛠 Commandes courantes

### 📁 Backend

Se placer dans le backend :

```powershell
cd D:\Mon_projet\web\SaaS\apps\api-core
```

Activer l'environnement virtuel :

```powershell
.\.venv\Scripts\Activate.ps1
```

Si `(base)` apparaît dans le terminal :

```powershell
conda deactivate
```

### 🚀 Lancer l'API

Depuis `apps/api-core` :

```powershell
uvicorn src.main:app --reload
```

Documentation Swagger :

```text
http://127.0.0.1:8000/docs
```

Documentation ReDoc :

```text
http://127.0.0.1:8000/redoc
```

Health check :

```text
http://127.0.0.1:8000/health
```

## 🐳 Docker

Démarrer PostgreSQL et Redis :

```powershell
docker compose up -d
```

Vérifier les conteneurs :

```powershell
docker ps
```

Arrêter les conteneurs :

```powershell
docker compose stop
```

Voir les logs :

```powershell
docker compose logs
```

Vérifier PostgreSQL :

```powershell
docker exec restaurant-postgres pg_isready -U restaurant_user -d restaurant_db
```

Vérifier Redis :

```powershell
docker exec restaurant-redis redis-cli ping
```

## 🗄️ Alembic

Vérifier la migration actuelle :

```powershell
alembic current
```

Vérifier les migrations :

```powershell
alembic check
```

Appliquer les migrations :

```powershell
alembic upgrade head
```

Voir l'historique :

```powershell
alembic history
```

Créer une nouvelle migration :

```powershell
alembic revision --autogenerate -m "description"
```

## 🔧 Python

Vérifier Python :

```powershell
python --version
```

Vérifier l'environnement :

```powershell
where.exe python
```

Vérifier FastAPI :

```powershell
python -c "import fastapi; print(fastapi.__version__)"
```

Vérifier SQLAlchemy :

```powershell
python -c "import sqlalchemy; print(sqlalchemy.__version__)"
```

## 🔎 Rechercher dans les fichiers

Rechercher un fichier :

```powershell
Get-ChildItem -Recurse -Filter "nom_du_fichier"
```

Afficher le contenu d'un fichier :

```powershell
Get-Content .\README.md
```

## 🌿 Git

Vérifier l'état du projet :

```powershell
git status
```

Voir les modifications :

```powershell
git diff
```

Ajouter les modifications :

```powershell
git add .
```

Créer un commit :

```powershell
git commit -m "message du commit"
```

Envoyer vers GitHub :

```powershell
git push origin main
```

Récupérer les modifications :

```powershell
git pull origin main
```

Voir l'historique :

```powershell
git log --oneline
```

## 🔄 Workflow recommandé

```text
1. Activer .venv
2. Démarrer Docker
3. Vérifier PostgreSQL et Redis
4. Lancer FastAPI
5. Tester avec Swagger
6. Vérifier git status
7. git add
8. git commit
9. git push
```

## ⚠️ Attention

Ne pas utiliser :

```powershell
docker compose down -v
```

car cette commande peut supprimer les volumes et donc les données PostgreSQL.
