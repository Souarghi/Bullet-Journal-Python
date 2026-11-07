"""Bibliothèque Python de Bullet Journal (BuJo).

Un package compact et complet :
- `models`  : Entry, Task, Event, Note, TaskStatus, Signifier, et exceptions métier.
- `journal` : DailyLog, MonthlyLog et BulletJournal.
- `logger`  : Configuration automatique des fichiers debug.log et errors.log.
- `cli`     : Interface utilisateur interactive pour jouer avec le carnet.
"""

from bujo.cli import BujoCLI
from bujo.journal import BulletJournal, DailyLog, MonthlyLog
from bujo.logger import get_logger, setup_logging
from bujo.models import (
    BujoError,
    Entry,
    EntryNotFoundError,
    Event,
    InvalidStatusTransitionError,
    Note,
    Signifier,
    Task,
    TaskStatus,
    ValidationError,
)

__version__ = "0.2.0"

__all__ = [
    # Classes principales
    "BulletJournal",
    "DailyLog",
    "MonthlyLog",
    "BujoCLI",
    # Modèles
    "Entry",
    "Task",
    "Event",
    "Note",
    "TaskStatus",
    "Signifier",
    # Exceptions
    "BujoError",
    "ValidationError",
    "EntryNotFoundError",
    "InvalidStatusTransitionError",
    # Outils de journalisation
    "setup_logging",
    "get_logger",
]
