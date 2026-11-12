import uuid
from typing import List
from datetime import datetime

from .entries import Entry, Task, TaskState
from .exceptions import EntryNotFoundError
from .logger import logger


class DailyLog:
    """
    Représente le journal d'une journée spécifique.
    """

    def __init__(self, date: datetime = None):
        self.date = date or datetime.now()
        self.entries: List[Entry] = []
        logger.debug(f"Création d'un DailyLog pour la date : {self.date.strftime('%d-%m-%Y')}")

    def add_entry(self, entry: Entry) -> None:
        """
        Ajoute une entrée (tâche, événement ou note).
        :param entry:
        :return:
        """
        self.entries.append(entry)
        logger.debug(f"Entrée ajoutée : {entry.name} (ID: {entry.id})")

    def remove_entry(self, entry_id: uuid.UUID) -> None:
        """
        Supprime une entrée avec identifiant.
        :param entry_id:
        :return: None = OK / EntryNotFoundError = KO
        """
        for entry in self.entries:
            if entry.id == entry_id:
                self.entries.remove(entry)
                logger.debug(f"Entrée supprimée : ID {entry_id}")
                return None
        logger.error(f"Tentative de suppression échouée : ID {entry_id} introuvable.")
        raise EntryNotFoundError(f"L'entrée avec ID {entry_id} n'existe pas")

    def get_pending_tasks(self) -> List[Task]:
        """
        Affiche la liste des tâches en cours.
        :return: Liste des tâches en cours.
        """
        pending_tasks = []
        for entry in self.entries:
            if isinstance(entry, Task) and entry.state == TaskState.TODO:
                pending_tasks.append(entry)
        return pending_tasks