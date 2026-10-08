import os
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.api.dependencies import get_db
from src.enums.role import UserRole
from src.models.user import User


# Charger les variables d'environnement
load_dotenv()


# ============================================================
# Configuration JWT
# ============================================================

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")

try:
    ACCESS_TOKEN_EXPIRE_MINUTES = int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
    )
except ValueError:
    raise RuntimeError(
        "ACCESS_TOKEN_EXPIRE_MINUTES doit être un nombre entier."
    )


# Vérifier la présence de la clé secrète
if not SECRET_KEY:
    raise RuntimeError(
        "SECRET_KEY n'est pas configurée dans le fichier .env"
    )


# Vérifier que la durée du token est valide
if ACCESS_TOKEN_EXPIRE_MINUTES <= 0:
    raise RuntimeError(
        "ACCESS_TOKEN_EXPIRE_MINUTES doit être supérieur à zéro."
    )


# Schéma d'authentification Bearer
security = HTTPBearer()


# ============================================================
# Création du token JWT
# ============================================================

def create_access_token(user_id: str) -> str:
    """
    Crée un token JWT pour l'utilisateur fourni.

    Le token contient :
    - sub : identifiant de l'utilisateur
    - exp : date d'expiration du token
    """

    expire = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "sub": str(user_id),
        "exp": expire,
    }

    return jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM,
    )


# ============================================================
# Récupération de l'utilisateur connecté
# ============================================================

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """
    Vérifie le token JWT et retourne l'utilisateur connecté.

    Lève une erreur 401 si :
    - le token est invalide ;
    - le token est expiré ;
    - le token ne contient pas de sub ;
    - l'utilisateur n'existe plus en base.
    """

    token = credentials.credentials

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
        )

        user_id = payload.get("sub")

        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token invalide.",
            )

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide ou expiré.",
        )

    user = db.execute(
        select(User).where(User.id == user_id)
    ).scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Utilisateur introuvable.",
        )

    return user


# ============================================================
# Vérification du rôle ADMIN
# ============================================================

def get_current_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Vérifie que l'utilisateur connecté est administrateur.
    """

    if current_user.role != UserRole.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès réservé aux administrateurs.",
        )

    return current_user


# ============================================================
# Vérification du rôle MANAGER
# ============================================================

def get_current_manager(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Vérifie que l'utilisateur connecté est manager.
    """

    if current_user.role != UserRole.MANAGER.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès réservé aux managers.",
        )

    return current_user