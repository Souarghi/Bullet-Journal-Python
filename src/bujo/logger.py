"""Configuration du système de journalisation (logging) pour le Bullet Journal.

Pourquoi ce fichier ?
Le sujet impose deux fichiers de logs distincts :
1. `debug.log`  : contient TOUT ce qui se passe (création d'entrée, ajout, transitions...).
2. `errors.log` : ne contient QUE les anomalies graves (niveaux ERROR et CRITICAL).

Ce module configure automatiquement ces deux fichiers sans doublons, même si on
l'appelle plusieurs fois.
"""

from __future__ import annotations

import logging
from pathlib import Path

# Répertoire par défaut où seront créés debug.log et errors.log
DEFAULT_LOG_DIR = Path("logs")
# Nom du logger racine pour tout le projet BuJo
LOGGER_NAME = "bujo"


def setup_logging(
    log_dir: str | Path = DEFAULT_LOG_DIR,
    console_output: bool = False,
    level: int = logging.DEBUG,
    force_reconfigure: bool = False,
) -> logging.Logger:
    """Configure et retourne le logger principal de l'application BuJo.

    Args:
        log_dir: Répertoire de destination pour les fichiers de logs.
        console_output: Si True, affiche également les logs en direct dans la console.
        level: Niveau global minimal du logger (par défaut DEBUG).
        force_reconfigure: Si True, supprime les anciens handlers et recrée ceux du log_dir.

    Returns:
        Instance de logging.Logger configurée.
    """
    # Étape 1 : Créer le dossier "logs/" s'il n'existe pas encore sur le disque
    path = Path(log_dir)
    path.mkdir(parents=True, exist_ok=True)

    # Étape 2 : Récupérer le logger principal "bujo"
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(level)

    # Étape 3 : Gestion de la réinitialisation pour éviter d'écrire en double dans les fichiers
    if force_reconfigure:
        for handler in list(logger.handlers):
            handler.close()
            logger.removeHandler(handler)
    elif logger.hasHandlers():
        # Si le logger est déjà configuré, on ne rajoute pas de handlers pour éviter les doublons
        return logger

    # Étape 4 : Définir un format lisible et clair pour chaque ligne de log :
    # Exemple : 2026-11-05 10:30:00 [DEBUG] [bujo.task] Tâche créée : id=a1b2c3d4
    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Étape 5 : Handler 1 - Fichier complet de débogage (debug.log)
    # Reçoit tous les messages à partir du niveau DEBUG
    debug_file = path / "debug.log"
    debug_handler = logging.FileHandler(debug_file, encoding="utf-8")
    debug_handler.setLevel(logging.DEBUG)
    debug_handler.setFormatter(formatter)
    logger.addHandler(debug_handler)

    # Étape 6 : Handler 2 - Fichier dédié aux erreurs (errors.log)
    # Filtre strictement les événements critiques (ERROR et CRITICAL)
    errors_file = path / "errors.log"
    errors_handler = logging.FileHandler(errors_file, encoding="utf-8")
    errors_handler.setLevel(logging.ERROR)
    errors_handler.setFormatter(formatter)
    logger.addHandler(errors_handler)

    # Étape 7 : Handler optionnel pour afficher dans la console du terminal si souhaité
    if console_output:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    logger.debug("Système de journalisation BuJo initialisé avec succès.")
    return logger


def get_logger(child_name: str | None = None) -> logging.Logger:
    """Retourne le logger principal ou un sous-logger pour un module donné.

    Par exemple, dans le module `task.py`, appeler `get_logger("task")`
    permet d'écrire des logs identifiés sous le nom `[bujo.task]`.

    Args:
        child_name: Nom optionnel du sous-module (ex: "task", "event", "journal").

    Returns:
        Instance de logging.Logger.
    """
    base_logger = logging.getLogger(LOGGER_NAME)
    # Si le logger n'est pas encore initialisé, on lance la configuration par défaut
    if not base_logger.hasHandlers():
        setup_logging()

    # Si un nom d'enfant est demandé, on crée un sous-logger hiérarchique
    if child_name:
        return base_logger.getChild(child_name)
    return base_logger
