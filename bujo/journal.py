import uuid
from typing import List
from datetime import datetime

from .entries import Entry, Task, TaskState

class DailyLog:
    """
    Représente le journal d'une journée spécifique.
    """

    def __init__(self, date: datetime = None):
        self.date = date or datetime.now()
        self.entries: List[Entry] = []

    def add_entry(self, entry: Entry) -> None:
        """
        Ajoute une entrée (tâche, événement ou note).
        :param entry:
        :return:
        """
        self.entries.append(entry)

    def remove_entry(self, entry_id: uuid.UUID) -> bool:
        """
        Supprime une entrée avec identifiant.
        :param entry_id:
        :return: True = OK / False = KO
        """
        for entry in self.entries:
            if entry.id == entry_id:
                self.entries.remove(entry)
                return True
        return False

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