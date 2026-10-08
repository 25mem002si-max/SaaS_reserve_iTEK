"""Configuration du logging structuré.

Utilise structlog pour des logs JSON structurés,
facilement exploitables par des outils comme Datadog, ELK, etc.
"""

import logging
import sys
from typing import Dict, Any, Optional
from datetime import datetime
import json
from pathlib import Path

import structlog
from structlog.types import Processor

from app.config.settings import settings, LogLevel


def add_environment(
    logger: logging.Logger, method_name: str, event_dict: Dict[str, Any]
) -> Dict[str, Any]:
    """Ajoute l'environnement et la version à chaque log."""
    event_dict["environment"] = settings.environment
    event_dict["app_version"] = settings.app_version
    event_dict["service"] = "ai-engine"
    return event_dict


def add_timestamp(
    logger: logging.Logger, method_name: str, event_dict: Dict[str, Any]
) -> Dict[str, Any]:
    """Ajoute un timestamp ISO à chaque log."""
    event_dict["timestamp"] = datetime.utcnow().isoformat() + "Z"
    return event_dict


def _json_serializer(*args, **kwargs) -> str:
    """Serialiseur JSON personnalisé."""
    return json.dumps(*args, **kwargs, default=str)


def setup_logging():
    """Configure le logging structuré avec structlog."""
    
    # Créer le dossier logs s'il n'existe pas
    logs_dir = settings.logs_dir
    if not logs_dir.exists():
        logs_dir.mkdir(parents=True, exist_ok=True)
    
    # Configurer les processors structlog
    processors: list[Processor] = [
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        add_timestamp,
        add_environment,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]
    
    if settings.log_format == "json":
        processors.append(structlog.processors.JSONRenderer(serializer=_json_serializer))
    else:
        processors.append(structlog.dev.ConsoleRenderer())
    
    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Configurer le logging standard
    log_level = getattr(logging, settings.log_level.value.upper())
    
    # Handler console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(logging.Formatter("%(message)s"))
    
    # Handler fichier (si nécessaire)
    file_handlers = []
    if settings.environment in ["staging", "production"]:
        log_file = logs_dir / "ai_engine.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(logging.Formatter("%(message)s"))
        file_handlers.append(file_handler)
    
    # Configurer le root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.handlers = []
    root_logger.addHandler(console_handler)
    for fh in file_handlers:
        root_logger.addHandler(fh)
    
    # Réduire les logs des bibliothèques tierces
    for lib in ["httpx", "httpcore", "urllib3", "redis"]:
        logging.getLogger(lib).setLevel(logging.WARNING)
        logging.getLogger(lib).propagate = False
    
    # Logger structlog pour l'application
    logger = structlog.get_logger()
    logger.info(
        "logging_configured",
        log_level=settings.log_level.value,
        environment=settings.environment,
        log_format=settings.log_format,
    )
    
    return logger


# Logger global
def get_logger() -> structlog.BoundLogger:
    """Retourne un logger structlog."""
    return structlog.get_logger()


# Pour compatibilité avec les modules qui utilisent logging.getLogger
def get_standard_logger(name: str) -> logging.Logger:
    """Retourne un logger standard (pour la compatibilité)."""
    return logging.getLogger(name)