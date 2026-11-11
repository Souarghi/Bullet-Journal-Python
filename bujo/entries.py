import uuid
from datetime import datetime
from typing import Optional

from enum import Enum

class Entry:
    """
    Classe de base pour toutes entrées du journal.
    """

    def __init__(self, name: str, description: str = "", log_date: Optional[datetime] = None):
        self.id: uuid.UUID = uuid.uuid4()
        self.name: str = name
        self.description: str = description
        self.create_at: datetime = datetime.now()
        self.log_date: datetime = log_date or datetime.now()


class TaskState(Enum):
    """
    Les différents états du cycle de vie d'une tâche.
    """
    TODO = "à faire"
    DONE = "terminée"
    MIGRATED = "migrée"
    SCHEDULED = "planifiée"
    ABANDONED = "abandonée"


class Task(Entry):
    """
    Une tâche à accomplir, avec gestion de son êtat.
    """

    def __init__(self, name: str, description: str = "", log_date: Optional[datetime] = None):
        super().__init__(name, description, log_date)
        self.state: TaskState = TaskState.TODO

    def complete(self) -> None:
        """
        Marque la tâche comme terminée.
        :return:
        """
        self.state = TaskState.DONE


class Event(Entry):
    """
    Un événement ponctuel dans le temps.
    """

    def __init__(self, name: str, description: str = "", log_date: Optional[datetime] = None,
                 event_time: Optional[datetime] = None):
        super().__init__(name, description, log_date)
        self.event_time: Optional[datetime] = event_time


class Note(Entry):
    """
    Simple note, sans état ni heure.
    """
    pass