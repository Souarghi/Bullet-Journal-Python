"""Bibliothèque Python de Bullet Journal (BuJo).

Un package compact et complet :
- `models`  : Entry, Task, Event, Note, TaskStatus, et exceptions métier.
- `journal` : DailyLog et BulletJournal.
- `logger`  : Configuration automatique des fichiers debug.log et errors.log.
- `cli`     : Interface utilisateur interactive pour jouer avec le carnet.
"""

from bujo.cli import BujoCLI
from bujo.journal import BulletJournal, DailyLog
from bujo.logger import get_logger, setup_logging
from bujo.models import (
    BujoError,
    Entry,
    EntryNotFoundError,
    Event,
    InvalidStatusTransitionError,
    Note,
    Task,
    TaskStatus,
    ValidationError,
)

__version__ = "0.1.0"

__all__ = [
    # Classes principales
    "BulletJournal",
    "DailyLog",
    "BujoCLI",
    # Modèles
    "Entry",
    "Task",
    "Event",
    "Note",
    "TaskStatus",
    # Exceptions
    "BujoError",
    "ValidationError",
    "EntryNotFoundError",
    "InvalidStatusTransitionError",
    # Outils de journalisation
    "setup_logging",
    "get_logger",
]
