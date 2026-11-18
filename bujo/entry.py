"""Modèle des entrées du journal : tâches, événements et notes."""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from datetime import date, datetime, time
from enum import Enum

from bujo.exceptions import (
    EmptyNameError,
    InvalidDateError,
    InvalidSignifierError,
    InvalidStateTransitionError,
)


class TaskState(Enum):
    """États possibles du cycle de vie d'une tâche."""

    TODO = "à faire"
    DONE = "terminée"
    MIGRATED = "migrée"
    PLANNED = "planifiée"
    DISCARDED = "abandonnée"


# Transitions autorisées depuis chaque état : une tâche part de TODO
# puis devient définitive (aucune sortie des autres états).
ALLOWED_TRANSITIONS: dict[TaskState, set[TaskState]] = {
    TaskState.TODO: {
        TaskState.DONE,
        TaskState.MIGRATED,
        TaskState.PLANNED,
        TaskState.DISCARDED,
    },
}


# Signifiants du rapid logging : symboles facultatifs ajoutés au
# symbole d'une entrée pour en souligner la portée.
SIGNIFIERS: dict[str, str] = {
    "*": "priorité",
    "!": "idée, inspiration",
}


# Symboles du rapid logging associés aux états d'une tâche.
SYMBOLS_BY_STATE: dict[TaskState, str] = {
    TaskState.TODO: "•",
    TaskState.DONE: "×",
    TaskState.MIGRATED: ">",
    TaskState.PLANNED: "<",
    TaskState.DISCARDED: "~",
}


class Entry(ABC):
    """Classe abstraite d'une entrée du journal.

    Une entrée possède un identifiant unique (uuid), un nom non vide,
    une description, une date de création et la date du log auquel
    elle appartient.
    """

    def __init__(
        self,
        name: str,
        description: str = "",
        log_date: date | None = None,
        signifier: str | None = None,
        entry_id: str | None = None,
    ) -> None:
        """Construire une entrée, avec un identifiant généré ou imposé."""
        self._id: str = entry_id if entry_id is not None else str(uuid.uuid4())
        self._name: str = self._check_name(name)
        self.description: str = description
        self.created_at: datetime = datetime.now()
        self.log_date: date = self._check_date(log_date) or date.today()
        self.signifier: str | None = self._check_signifier(signifier)

    @property
    def id(self) -> str:
        """Identifiant unique et immuable de l'entrée."""
        return self._id

    @property
    def name(self) -> str:
        """Nom de l'entrée."""
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        """Modifie le nom après validation."""
        self._name = self._check_name(value)

    @property
    def log_date(self) -> date:
        """Date du log auquel l'entrée appartient."""
        return self._log_date

    @log_date.setter
    def log_date(self, value: date) -> None:
        """Modifie la date du log après validation."""
        self._log_date = self._check_date(value) or date.today()

    @staticmethod
    def _check_signifier(value: str | None) -> str | None:
        """Valider le signifiant : None ou un symbole de SIGNIFIERS."""
        if value is None:
            return None
        if not isinstance(value, str) or value not in SIGNIFIERS:
            raise InvalidSignifierError(
                f"Signifiant inconnu : {value!r}. Signifiants admis : "
                + ", ".join(SIGNIFIERS) + "."
            )
        return value

    @staticmethod
    def _check_name(name: str) -> str:
        """Valider le nom : une chaîne non vide est obligatoire."""
        if not isinstance(name, str) or not name.strip():
            raise EmptyNameError("Le nom d'une entrée ne peut pas être vide.")
        return name.strip()

    @staticmethod
    def _check_date(value: date | None) -> date | None:
        """Valider une date de log (un datetime n'est pas accepté ici)."""
        if value is None:
            return None
        if not isinstance(value, date) or isinstance(value, datetime):
            raise InvalidDateError("log_date doit être un datetime.date.")
        return value

    @property
    @abstractmethod
    def symbol(self) -> str:
        """Symbole rapid logging de l'entrée."""
        ...

    def _display_name(self) -> str:
        """Nom tel qu'affiché par la représentation rapid logging."""
        return self.name

    def __str__(self) -> str:
        """Représentation rapid logging : symbole, signifiant, nom."""
        mark = self.signifier or ""
        return f"{self.symbol}{mark} {self._display_name()}"


class Task(Entry):
    """Tâche à faire, avec un cycle de vie complet."""

    def __init__(
        self,
        name: str,
        description: str = "",
        log_date: date | None = None,
        signifier: str | None = None,
        entry_id: str | None = None,
    ) -> None:
        """Construire une tâche, initialement à faire."""
        super().__init__(name, description, log_date, signifier, entry_id)
        self._state: TaskState = TaskState.TODO

    def _display_name(self) -> str:
        """Nom barré (~~texte~~) quand la tâche est abandonnée."""
        if self._state is TaskState.DISCARDED:
            return f"~~{self.name}~~"
        return self.name

    @property
    def state(self) -> TaskState:
        """État courant de la tâche."""
        return self._state

    @property
    def symbol(self) -> str:
        """Symbole rapid logging selon l'état de la tâche."""
        return SYMBOLS_BY_STATE[self._state]

    def _transition_to(self, new_state: TaskState) -> None:
        """Applique une transition d'état, sinon lève une exception."""
        allowed = ALLOWED_TRANSITIONS.get(self._state, set())
        if new_state not in allowed:
            raise InvalidStateTransitionError(
                f"Transition interdite : {self._state.value} -> "
                f"{new_state.value}."
            )
        self._state = new_state

    def complete(self) -> None:
        """Marque la tâche comme terminée."""
        self._transition_to(TaskState.DONE)

    def migrate(self) -> None:
        """Marque la tâche comme migrée vers un autre jour ou mois."""
        self._transition_to(TaskState.MIGRATED)

    def plan(self) -> None:
        """Marque la tâche comme planifiée dans le Future Log."""
        self._transition_to(TaskState.PLANNED)

    def discard(self) -> None:
        """Marque la tâche comme abandonnée, devenue sans objet."""
        self._transition_to(TaskState.DISCARDED)


class Event(Entry):
    """Événement daté, avec une heure facultative."""

    def __init__(
        self,
        name: str,
        description: str = "",
        log_date: date | None = None,
        at: time | None = None,
        signifier: str | None = None,
        entry_id: str | None = None,
    ) -> None:
        """Construire un événement daté, avec heure facultative."""
        super().__init__(name, description, log_date, signifier, entry_id)
        if at is not None and not isinstance(at, time):
            raise InvalidDateError("at doit être un datetime.time.")
        self.at: time | None = at

    @property
    def symbol(self) -> str:
        """Symbole rapid logging d'un événement."""
        return "○"


class Note(Entry):
    """Note simple, sans état ni date particulière."""

    @property
    def symbol(self) -> str:
        """Symbole rapid logging d'une note."""
        return "–"
