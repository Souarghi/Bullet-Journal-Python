"""Organisation du journal : stockage et cycle de vie des entrées."""

from __future__ import annotations

import logging
from datetime import date

from bujo.entry import Entry, Task, TaskState
from bujo.exceptions import EntryNotFoundError, InvalidStateTransitionError

logger = logging.getLogger("bujo")


def setup_logging(
    debug_file: str = "bujo_debug.log",
    error_file: str = "bujo_error.log",
) -> None:
    """Configure les fichiers de log : debug complet et erreurs seules."""
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )
    debug_handler = logging.FileHandler(debug_file, encoding="utf-8")
    debug_handler.setLevel(logging.DEBUG)
    debug_handler.setFormatter(formatter)
    error_handler = logging.FileHandler(error_file, encoding="utf-8")
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    logger.addHandler(debug_handler)
    logger.addHandler(error_handler)


class Journal:
    """Journal personnel contenant des entrées indexées par identifiant."""

    def __init__(self, name: str = "Mon journal") -> None:
        """Initialise un journal vide portant le nom donné."""
        self.name: str = name
        self._entries: dict[str, Entry] = {}

    def __len__(self) -> int:
        """Nombre d'entrées dans le journal."""
        return len(self._entries)

    def ids(self) -> list[str]:
        """Retourne les identifiants de toutes les entrées."""
        return list(self._entries)

    def add_entry(self, entry: Entry) -> str:
        """Ajoute une entrée et retourne son identifiant unique."""
        if not isinstance(entry, Entry):
            raise TypeError("Seules des entrées du journal peuvent être "
                            "ajoutées.")
        self._entries[entry.id] = entry
        logger.debug("Entrée %s (%s) ajoutée au journal « %s ».",
                     entry.id, entry.name, self.name)
        return entry.id

    def add_task(
        self,
        name: str,
        description: str = "",
        log_date: date | None = None,
        signifier: str | None = None,
    ) -> Task:
        """Crée une tâche, l'ajoute au journal et la retourne."""
        task = Task(name, description, log_date, signifier)
        self.add_entry(task)
        return task

    def get_entry(self, entry_id: str) -> Entry:
        """Retourne l'entrée correspondant à l'identifiant donné."""
        try:
            return self._entries[entry_id]
        except KeyError:
            logger.error("Entrée introuvable : %s.", entry_id)
            raise EntryNotFoundError(
                f"Aucune entrée avec l'identifiant {entry_id}."
            ) from None

    def remove_entry(self, entry_id: str) -> Entry:
        """Supprime et retourne l'entrée correspondant à l'identifiant."""
        entry = self.get_entry(entry_id)
        del self._entries[entry_id]
        logger.debug("Entrée %s supprimée.", entry_id)
        return entry

    def _task(self, entry_id: str) -> Task:
        """Retourne l'entrée demandée après avoir vérifié sa nature."""
        entry = self.get_entry(entry_id)
        if not isinstance(entry, Task):
            raise InvalidStateTransitionError(
                "Seule une tâche peut changer d'état."
            )
        return entry

    def complete_task(self, entry_id: str) -> Task:
        """Marque une tâche comme terminée (symbole ×)."""
        task = self._task(entry_id)
        task.complete()
        logger.debug("Tâche %s terminée.", entry_id)
        return task

    def migrate_task(self, entry_id: str) -> Task:
        """Marque une tâche comme migrée (symbole >)."""
        task = self._task(entry_id)
        task.migrate()
        logger.debug("Tâche %s migrée.", entry_id)
        return task

    def plan_task(self, entry_id: str) -> Task:
        """Marque une tâche comme planifiée (symbole <)."""
        task = self._task(entry_id)
        task.plan()
        logger.debug("Tâche %s planifiée.", entry_id)
        return task

    def discard_task(self, entry_id: str) -> Task:
        """Marque une tâche comme abandonnée (symbole ~)."""
        task = self._task(entry_id)
        task.discard()
        logger.debug("Tâche %s abandonnée.", entry_id)
        return task

    def open_tasks(self) -> list[Task]:
        """Retourne les tâches restant à faire, dans l'ordre d'ajout."""
        return [
            entry
            for entry in self._entries.values()
            if isinstance(entry, Task) and entry.state is TaskState.TODO
        ]

    def entries_of_day(self, day: date) -> list[Entry]:
        """Retourne les entrées du log de la journée donnée."""
        if not isinstance(day, date):
            raise TypeError("day doit être un datetime.date.")
        return [
            entry for entry in self._entries.values()
            if entry.log_date == day
        ]

    def search_by_name(self, keyword: str) -> list[Entry]:
        """Recherche les entrées dont le nom contient le mot-clé.

        Recherche secondaire (insensible à la casse) qui retourne
        toutes les entrées correspondantes.
        """
        needle = keyword.casefold()
        return [
            entry for entry in self._entries.values()
            if needle in entry.name.casefold()
        ]
