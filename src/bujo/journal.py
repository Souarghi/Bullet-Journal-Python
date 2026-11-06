"""Organisation temporelle du Bullet Journal : DailyLog et BulletJournal.

Ce fichier regroupe l'organisation du carnet :
1. `DailyLog` : le journal quotidien d'une journée précise, rempli au fil de l'eau.
2. `BulletJournal` : le gestionnaire global de tout le carnet (accès au jour d'aujourd'hui,
   création automatique des jours manquants, recherche d'une entrée sur tout le journal).
"""

from __future__ import annotations

from datetime import date, time
from typing import Iterator

from bujo.logger import get_logger
from bujo.models import (
    Entry,
    EntryNotFoundError,
    Event,
    Note,
    Task,
    TaskStatus,
    ValidationError,
)

logger = get_logger("journal")


# =============================================================================
# 1. JOURNAL DU JOUR : DailyLog
# =============================================================================

class DailyLog:
    """Représente la page d'une journée spécifique dans le Bullet Journal."""

    def __init__(self, log_date: date | None = None) -> None:
        """Initialise le journal du jour (date courante par défaut)."""
        self._log_date: date = log_date or date.today()
        # Dictionnaire ordonné id_unique -> Entry (accès rapide en O(1))
        self._entries: dict[str, Entry] = {}
        logger.debug("Initialisation du DailyLog pour le %s", self._log_date)

    @property
    def log_date(self) -> date:
        """Retourne la date du Daily Log."""
        return self._log_date

    @property
    def entries(self) -> list[Entry]:
        """Retourne la liste de toutes les entrées de la journée."""
        return list(self._entries.values())

    def __len__(self) -> int:
        """Nombre d'entrées aujourd'hui."""
        return len(self._entries)

    def __iter__(self) -> Iterator[Entry]:
        """Itération facile sur les entrées du jour."""
        return iter(self._entries.values())

    def add_entry(self, entry: Entry) -> Entry:
        """Ajoute une entrée générique (tâche, événement ou note)."""
        if not isinstance(entry, Entry):
            raise ValidationError("L'élément à ajouter doit être une sous-classe d'Entry.")
        entry.log_date = self._log_date
        self._entries[entry.id] = entry
        logger.info(
            "Entrée ajoutée au log du %s : [%s] id=%s, titre=%r",
            self._log_date,
            entry.__class__.__name__,
            entry.id,
            entry.title,
        )
        return entry

    def add_task(
        self,
        title: str,
        description: str = "",
        category: str | None = None,
    ) -> Task:
        """Crée et ajoute une tâche dans le journal du jour."""
        task = Task(
            title=title,
            description=description,
            log_date=self._log_date,
            category=category,
        )
        self.add_entry(task)
        return task

    def add_event(
        self,
        title: str,
        event_date: date | None = None,
        event_time: time | None = None,
        description: str = "",
        location: str | None = None,
        category: str | None = None,
    ) -> Event:
        """Crée et ajoute un événement dans le journal du jour."""
        target_date = event_date or self._log_date
        event = Event(
            title=title,
            event_date=target_date,
            event_time=event_time,
            description=description,
            location=location,
            log_date=self._log_date,
            category=category,
        )
        self.add_entry(event)
        return event

    def add_note(
        self,
        title: str,
        description: str = "",
        category: str | None = None,
    ) -> Note:
        """Crée et ajoute une note dans le journal du jour."""
        note = Note(
            title=title,
            description=description,
            log_date=self._log_date,
            category=category,
        )
        self.add_entry(note)
        return note

    def get_entry(self, entry_id: str) -> Entry:
        """Retrouve une entrée par son identifiant unique en O(1)."""
        if entry_id not in self._entries:
            logger.warning(
                "Entrée id=%s introuvable dans le log du %s", entry_id, self._log_date
            )
            raise EntryNotFoundError(entry_id)
        return self._entries[entry_id]

    def remove_entry(self, entry_id: str) -> Entry:
        """Supprime une entrée du journal par son identifiant unique."""
        entry = self.get_entry(entry_id)
        del self._entries[entry_id]
        logger.info(
            "Entrée supprimée du log du %s : id=%s, titre=%r",
            self._log_date,
            entry.id,
            entry.title,
        )
        return entry

    def get_tasks(self, status: TaskStatus | None = None) -> list[Task]:
        """Retourne les tâches du jour (filtrables par statut)."""
        tasks = [e for e in self._entries.values() if isinstance(e, Task)]
        if status is not None:
            tasks = [t for t in tasks if t.status == status]
        return tasks

    def get_pending_tasks(self) -> list[Task]:
        """Retourne les tâches en cours / à faire (statut TO_DO)."""
        return self.get_tasks(status=TaskStatus.TO_DO)

    def get_events(self) -> list[Event]:
        """Retourne tous les événements du jour."""
        return [e for e in self._entries.values() if isinstance(e, Event)]

    def get_notes(self) -> list[Note]:
        """Retourne toutes les notes du jour."""
        return [e for e in self._entries.values() if isinstance(e, Note)]

    def mark_task_done(self, task_id: str) -> Task:
        """Marque une tâche comme accomplie (×)."""
        entry = self.get_entry(task_id)
        if not isinstance(entry, Task):
            raise ValidationError(
                f"L'entrée avec l'id '{task_id}' est un(e) {entry.__class__.__name__}, "
                f"pas une tâche."
            )
        entry.mark_done()
        return entry

    def mark_task_cancelled(self, task_id: str) -> Task:
        """Marque une tâche comme abandonnée (~)."""
        entry = self.get_entry(task_id)
        if not isinstance(entry, Task):
            raise ValidationError(f"L'entrée '{task_id}' n'est pas une tâche.")
        entry.mark_cancelled()
        return entry

    def mark_task_migrated(self, task_id: str) -> Task:
        """Marque une tâche comme migrée (>)."""
        entry = self.get_entry(task_id)
        if not isinstance(entry, Task):
            raise ValidationError(f"L'entrée '{task_id}' n'est pas une tâche.")
        entry.mark_migrated()
        return entry

    def mark_task_scheduled(self, task_id: str) -> Task:
        """Marque une tâche comme planifiée (<)."""
        entry = self.get_entry(task_id)
        if not isinstance(entry, Task):
            raise ValidationError(f"L'entrée '{task_id}' n'est pas une tâche.")
        entry.mark_scheduled()
        return entry

    def display(self) -> str:
        """Affichage complet du Daily Log avec symboles BuJo."""
        header = f"=== Daily Log : {self._log_date.strftime('%A %d %B %Y')} ==="
        if not self._entries:
            return f"{header}\n(Aucune entrée pour cette journée)"
        lines = [header]
        for entry in self._entries.values():
            lines.append(entry.display())
        return "\n".join(lines)

    def __str__(self) -> str:
        """Affichage par défaut."""
        return self.display()


# =============================================================================
# 2. GESTIONNAIRE GLOBAL : BulletJournal
# =============================================================================

class BulletJournal:
    """Gestionnaire principal centralisant l'ensemble des journées du Bullet Journal."""

    def __init__(self, owner: str = "Utilisateur") -> None:
        """Initialise un Bullet Journal."""
        self.owner: str = owner
        self._daily_logs: dict[date, DailyLog] = {}
        logger.info("Nouveau BulletJournal initialisé pour %r", self.owner)

    @property
    def daily_logs(self) -> dict[date, DailyLog]:
        """Retourne le registre des Daily Logs."""
        return dict(self._daily_logs)

    def get_daily_log(self, target_date: date | None = None) -> DailyLog:
        """Récupère le Daily Log d'une date (le crée automatiquement si inexistant)."""
        day = target_date or date.today()
        if day not in self._daily_logs:
            self._daily_logs[day] = DailyLog(day)
            logger.debug("Création automatique d'un DailyLog pour le %s", day)
        return self._daily_logs[day]

    def today(self) -> DailyLog:
        """Accès direct au Daily Log d'aujourd'hui."""
        return self.get_daily_log(date.today())

    def add_task(
        self,
        title: str,
        description: str = "",
        log_date: date | None = None,
        category: str | None = None,
    ) -> Task:
        """Ajoute une tâche dans le journal du jour (ou à une date spécifique)."""
        daily_log = self.get_daily_log(log_date)
        return daily_log.add_task(title=title, description=description, category=category)

    def add_event(
        self,
        title: str,
        event_date: date | None = None,
        event_time: time | None = None,
        description: str = "",
        location: str | None = None,
        log_date: date | None = None,
        category: str | None = None,
    ) -> Event:
        """Ajoute un événement dans le journal."""
        target_log_date = log_date or event_date or date.today()
        daily_log = self.get_daily_log(target_log_date)
        return daily_log.add_event(
            title=title,
            event_date=event_date or target_log_date,
            event_time=event_time,
            description=description,
            location=location,
            category=category,
        )

    def add_note(
        self,
        title: str,
        description: str = "",
        log_date: date | None = None,
        category: str | None = None,
    ) -> Note:
        """Ajoute une note dans le journal."""
        daily_log = self.get_daily_log(log_date)
        return daily_log.add_note(title=title, description=description, category=category)

    def find_entry(self, entry_id: str) -> tuple[DailyLog, Entry]:
        """Recherche une entrée par son ID unique à travers l'ensemble des pages du journal."""
        for daily_log in self._daily_logs.values():
            try:
                entry = daily_log.get_entry(entry_id)
                return daily_log, entry
            except EntryNotFoundError:
                continue

        logger.warning("Entrée id=%s introuvable dans tout le journal", entry_id)
        raise EntryNotFoundError(entry_id)

    def mark_task_done(self, task_id: str, log_date: date | None = None) -> Task:
        """Marque une tâche comme terminée (×) via son ID unique."""
        if log_date is not None:
            daily_log = self.get_daily_log(log_date)
            return daily_log.mark_task_done(task_id)

        _, entry = self.find_entry(task_id)
        if not isinstance(entry, Task):
            raise ValidationError(f"L'entrée avec l'id '{task_id}' n'est pas une tâche.")
        entry.mark_done()
        return entry

    def remove_task(self, task_id: str, log_date: date | None = None) -> Task:
        """Supprime une tâche du journal."""
        if log_date is not None:
            daily_log = self.get_daily_log(log_date)
            entry = daily_log.remove_entry(task_id)
        else:
            daily_log, _ = self.find_entry(task_id)
            entry = daily_log.remove_entry(task_id)

        if not isinstance(entry, Task):
            daily_log.add_entry(entry)
            msg = f"L'élément supprimé n'était pas une tâche mais un {type(entry)}."
            raise ValidationError(msg)
        return entry

    def get_pending_tasks(self, log_date: date | None = None) -> list[Task]:
        """Retourne la liste des tâches à faire (TO_DO)."""
        target_date = log_date or date.today()
        daily_log = self.get_daily_log(target_date)
        return daily_log.get_pending_tasks()

    def get_all_pending_tasks(self) -> list[Task]:
        """Retourne toutes les tâches en attente de tout le carnet."""
        all_pending: list[Task] = []
        for daily_log in self._daily_logs.values():
            all_pending.extend(daily_log.get_pending_tasks())
        return all_pending

    def display_today(self) -> str:
        """Affichage du journal du jour."""
        return self.today().display()
