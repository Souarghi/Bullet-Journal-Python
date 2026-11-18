"""Persistance du journal : sauvegarde et chargement au format JSON."""

from __future__ import annotations

import json
import logging
from datetime import date, datetime, time

from bujo.entry import Entry, Event, Note, Task, TaskState
from bujo.exceptions import PersistenceError
from bujo.journal import Journal

logger = logging.getLogger("bujo")

# Version du format de fichier, à incrémenter en cas de rupture.
FORMAT_VERSION = 1

# Méthode publique à rejouer pour sortir une tâche restaurée de TODO.
_STATE_METHODS: dict[TaskState, str] = {
    TaskState.DONE: "complete",
    TaskState.MIGRATED: "migrate",
    TaskState.PLANNED: "plan",
    TaskState.DISCARDED: "discard",
}


def _kind_of(entry: Entry) -> str:
    """Retourne l'étiquette de type persistée pour une entrée."""
    if isinstance(entry, Task):
        return "task"
    if isinstance(entry, Event):
        return "event"
    if isinstance(entry, Note):
        return "note"
    raise PersistenceError(
        f"Type d'entrée non sauvegardable : {type(entry).__name__}."
    )


def _entry_to_dict(entry: Entry) -> dict:
    """Convertit une entrée en données JSON sérialisables."""
    data: dict = {
        "type": _kind_of(entry),
        "id": entry.id,
        "name": entry.name,
        "description": entry.description,
        "created_at": entry.created_at.isoformat(),
        "log_date": entry.log_date.isoformat(),
        "signifier": entry.signifier,
    }
    if isinstance(entry, Task):
        data["state"] = entry.state.name
    if isinstance(entry, Event):
        data["at"] = entry.at.isoformat() if entry.at is not None else None
    return data


def _entry_from_dict(data: dict) -> Entry:
    """Reconstruit une entrée à partir des données lues du fichier."""
    try:
        kind = data["type"]
        entry_id = data["id"]
        name = data["name"]
        description = data.get("description", "")
        log_date = date.fromisoformat(data["log_date"])
        signifier = data.get("signifier")
        if not isinstance(entry_id, str) or not entry_id:
            raise ValueError("identifiant absent ou vide")
        if kind == "task":
            entry: Entry = Task(name, description, log_date, signifier,
                                entry_id=entry_id)
            state = TaskState[data.get("state", TaskState.TODO.name)]
            method = _STATE_METHODS.get(state)
            if method is not None:
                getattr(entry, method)()
        elif kind == "event":
            at_raw = data.get("at")
            at = time.fromisoformat(at_raw) if at_raw is not None else None
            entry = Event(name, description, log_date, at, signifier,
                          entry_id=entry_id)
        elif kind == "note":
            entry = Note(name, description, log_date, signifier,
                         entry_id=entry_id)
        else:
            raise PersistenceError(
                f"Type d'entrée inconnu dans le fichier : {kind!r}."
            )
        entry.created_at = datetime.fromisoformat(data["created_at"])
    except PersistenceError:
        raise
    except (KeyError, TypeError, ValueError) as error:
        raise PersistenceError(
            f"Entrée invalide dans le fichier : {error}."
        ) from error
    return entry


def save_journal(journal: Journal, path: str) -> None:
    """Sauvegarde le journal complet dans un fichier JSON."""
    payload = {
        "version": FORMAT_VERSION,
        "name": journal.name,
        "entries": [
            _entry_to_dict(journal.get_entry(entry_id))
            for entry_id in journal.ids()
        ],
    }
    try:
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
    except OSError as error:
        raise PersistenceError(
            f"Sauvegarde impossible dans {path} : {error}."
        ) from error
    logger.debug("Journal « %s » sauvegardé dans %s (%d entrées).",
                 journal.name, path, len(journal))


def load_journal(path: str) -> Journal:
    """Charge un journal depuis un fichier JSON et le retourne."""
    try:
        with open(path, encoding="utf-8") as handle:
            payload = json.load(handle)
    except OSError as error:
        raise PersistenceError(
            f"Chargement impossible depuis {path} : {error}."
        ) from error
    except json.JSONDecodeError as error:
        raise PersistenceError(
            f"Fichier JSON invalide : {path} ({error})."
        ) from error
    if not isinstance(payload, dict):
        raise PersistenceError(f"Format non reconnu dans {path}.")
    version = payload.get("version")
    if version != FORMAT_VERSION:
        raise PersistenceError(
            f"Version de fichier non gérée : {version!r} "
            f"(version attendue : {FORMAT_VERSION})."
        )
    entries = payload.get("entries")
    if not isinstance(entries, list):
        raise PersistenceError(
            f"Le fichier {path} ne contient pas de liste « entries »."
        )
    journal = Journal(str(payload.get("name", "Mon journal")))
    for data in entries:
        journal.add_entry(_entry_from_dict(data))
    logger.debug("Journal « %s » chargé depuis %s (%d entrées).",
                 journal.name, path, len(journal))
    return journal
