"""Organisation temporelle du Bullet Journal : DailyLog, MonthlyLog et BulletJournal.

Ce fichier regroupe l'organisation du carnet :
1. `DailyLog` : le journal quotidien d'une journée précise, rempli au fil de l'eau.
2. `MonthlyLog` : le journal mensuel (page calendrier + page tâches).
3. `BulletJournal` : le gestionnaire global de tout le carnet (accès au jour d'aujourd'hui,
   mois en cours, migrations de tâches, et recherche sur tout le journal).
"""

from __future__ import annotations

import calendar
from datetime import date, time, timedelta
from typing import Iterator

from bujo.logger import get_logger
from bujo.models import (
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
        signifier: Signifier | str | None = None,
    ) -> Task:
        """Crée et ajoute une tâche dans le journal du jour."""
        task = Task(
            title=title,
            description=description,
            log_date=self._log_date,
            category=category,
            signifier=signifier,
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
        signifier: Signifier | str | None = None,
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
            signifier=signifier,
        )
        self.add_entry(event)
        return event

    def add_note(
        self,
        title: str,
        description: str = "",
        category: str | None = None,
        signifier: Signifier | str | None = None,
    ) -> Note:
        """Crée et ajoute une note dans le journal du jour."""
        note = Note(
            title=title,
            description=description,
            log_date=self._log_date,
            category=category,
            signifier=signifier,
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

    def migrate_task(self, task_id: str, target_daily_log: DailyLog) -> Task:
        """Migre une tâche non terminée vers un autre DailyLog.

        Règles métier (Niveau 2) :
        - La tâche d'origine doit avoir le statut À faire (TO_DO).
        - Une tâche Terminée (DONE) ou Abandonnée (CANCELLED) ne peut pas être migrée.
        - La tâche d'origine passe au statut Migrée (MIGRATED, '>').
        - Une nouvelle tâche est créée sur le log cible avec le statut À faire (TO_DO, '•'),
          en conservant le titre, la description, la catégorie et le signifiant.
        - Les deux tâches sont reliées par leurs attributs `migrated_from_id` et `migrated_to_id`.
        """
        if not isinstance(target_daily_log, DailyLog):
            raise ValidationError("Le journal cible de migration doit être un DailyLog.")

        origin_task = self.get_entry(task_id)
        if not isinstance(origin_task, Task):
            raise ValidationError(f"L'entrée '{task_id}' n'est pas une tâche.")

        if origin_task.status != TaskStatus.TO_DO:
            raise InvalidStatusTransitionError(
                current_status=origin_task.status.label,
                target_status=TaskStatus.MIGRATED.label,
                message=(
                    f"Impossible de migrer la tâche '{origin_task.title}' : "
                    f"seules les tâches à faire (TO_DO) peuvent être migrées "
                    f"(statut actuel : {origin_task.status.label})."
                ),
            )

        # 1. Marquer la tâche d'origine comme migrée (symbole '>')
        origin_task.mark_migrated()

        # 2. Créer la nouvelle tâche sur le log cible (symbole '•')
        new_task = target_daily_log.add_task(
            title=origin_task.title,
            description=origin_task.description,
            category=origin_task.category,
            signifier=origin_task.signifier,
        )
        new_task._migrated_from_id = origin_task.id
        origin_task.migrated_to_id = new_task.id

        logger.info(
            "Tâche migrée avec succès : id=%s (%s) -> nouveau id=%s (%s)",
            origin_task.id,
            self._log_date,
            new_task.id,
            target_daily_log.log_date,
        )
        return new_task

    def migrate_pending_tasks(self, target_daily_log: DailyLog) -> list[Task]:
        """Migre toutes les tâches non terminées (TO_DO) vers le journal cible."""
        migrated: list[Task] = []
        for task in self.get_pending_tasks():
            migrated_task = self.migrate_task(task.id, target_daily_log)
            migrated.append(migrated_task)
        return migrated

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
# 2. JOURNAL MENSUEL : MonthlyLog (Niveau 2)
# =============================================================================

class MonthlyLog:
    """Représente la vue mensuelle dans le Bullet Journal (Ryder Carroll).

    Dans la méthode Bullet Journal classique, le Monthly Log est constitué de :
    1. Une page Calendrier (Calendar View) : les jours du mois pour noter les événements datés.
    2. Une page Tâches (Task View) : les tâches globales à accomplir durant le mois.
    """

    def __init__(self, year: int | None = None, month: int | None = None) -> None:
        """Initialise un journal mensuel pour une année et un mois donnés."""
        today = date.today()
        self._year: int = year if year is not None else today.year
        self._month: int = month if month is not None else today.month

        if not (1 <= self._month <= 12):
            raise ValidationError(
                f"Mois invalide : {self._month}. Le mois doit être compris entre 1 et 12."
            )

        # Dictionnaire ordonné id_unique -> Entry (accès rapide en O(1))
        self._entries: dict[str, Entry] = {}
        logger.debug("Initialisation du MonthlyLog pour %04d-%02d", self._year, self._month)

    @property
    def year(self) -> int:
        """Retourne l'année du journal mensuel."""
        return self._year

    @property
    def month(self) -> int:
        """Retourne le mois du journal mensuel."""
        return self._month

    @property
    def name(self) -> str:
        """Nom du mois et année en français (ex: 'Novembre 2026')."""
        french_months = [
            "",
            "Janvier",
            "Février",
            "Mars",
            "Avril",
            "Mai",
            "Juin",
            "Juillet",
            "Août",
            "Septembre",
            "Octobre",
            "Novembre",
            "Décembre",
        ]
        return f"{french_months[self._month]} {self._year}"

    @property
    def entries(self) -> list[Entry]:
        """Retourne la liste de toutes les entrées du mois."""
        return list(self._entries.values())

    def __len__(self) -> int:
        """Nombre total d'entrées dans le mois."""
        return len(self._entries)

    def __iter__(self) -> Iterator[Entry]:
        """Itérateur sur les entrées du mois."""
        return iter(self._entries.values())

    def add_entry(self, entry: Entry) -> Entry:
        """Ajoute une entrée générique (tâche, événement ou note)."""
        if not isinstance(entry, Entry):
            raise ValidationError("L'élément à ajouter doit être une sous-classe d'Entry.")
        self._entries[entry.id] = entry
        logger.info(
            "Entrée ajoutée au MonthlyLog %04d-%02d : [%s] id=%s, titre=%r",
            self._year,
            self._month,
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
        signifier: Signifier | str | None = None,
    ) -> Task:
        """Crée et ajoute une tâche mensuelle."""
        d = date(self._year, self._month, 1)
        task = Task(
            title=title,
            description=description,
            log_date=d,
            category=category,
            signifier=signifier,
        )
        self.add_entry(task)
        return task

    def add_event(
        self,
        title: str,
        event_date: date,
        event_time: time | None = None,
        description: str = "",
        location: str | None = None,
        category: str | None = None,
        signifier: Signifier | str | None = None,
    ) -> Event:
        """Crée et ajoute un événement rattaché à ce mois."""
        if not isinstance(event_date, date):
            raise ValidationError("La date de l'événement doit être un objet date valide.")
        if not (event_date.year == self._year and event_date.month == self._month):
            raise ValidationError(
                f"L'événement du {event_date} ne correspond pas au mois "
                f"{self._month:02d}/{self._year} du MonthlyLog."
            )
        event = Event(
            title=title,
            event_date=event_date,
            event_time=event_time,
            description=description,
            location=location,
            log_date=event_date,
            category=category,
            signifier=signifier,
        )
        self.add_entry(event)
        return event

    def add_note(
        self,
        title: str,
        description: str = "",
        category: str | None = None,
        signifier: Signifier | str | None = None,
    ) -> Note:
        """Crée et ajoute une note mensuelle."""
        d = date(self._year, self._month, 1)
        note = Note(
            title=title,
            description=description,
            log_date=d,
            category=category,
            signifier=signifier,
        )
        self.add_entry(note)
        return note

    def get_entry(self, entry_id: str) -> Entry:
        """Retrouve une entrée par son identifiant unique."""
        if entry_id not in self._entries:
            raise EntryNotFoundError(entry_id)
        return self._entries[entry_id]

    def remove_entry(self, entry_id: str) -> Entry:
        """Supprime une entrée du mois."""
        entry = self.get_entry(entry_id)
        del self._entries[entry_id]
        logger.info(
            "Entrée supprimée du MonthlyLog %04d-%02d : id=%s, titre=%r",
            self._year,
            self._month,
            entry.id,
            entry.title,
        )
        return entry

    def get_tasks(self, status: TaskStatus | None = None) -> list[Task]:
        """Retourne les tâches du mois (filtrables par statut)."""
        tasks = [e for e in self._entries.values() if isinstance(e, Task)]
        if status is not None:
            tasks = [t for t in tasks if t.status == status]
        return tasks

    def get_pending_tasks(self) -> list[Task]:
        """Retourne les tâches non terminées du mois."""
        return self.get_tasks(status=TaskStatus.TO_DO)

    def get_events(self) -> list[Event]:
        """Retourne tous les événements du mois triés par date chronologique."""
        events = [e for e in self._entries.values() if isinstance(e, Event)]
        return sorted(events, key=lambda ev: (ev.event_date, ev.event_time or time.min))

    def get_notes(self) -> list[Note]:
        """Retourne toutes les notes du mois."""
        return [e for e in self._entries.values() if isinstance(e, Note)]

    def mark_task_done(self, task_id: str) -> Task:
        """Marque une tâche du mois comme terminée."""
        entry = self.get_entry(task_id)
        if not isinstance(entry, Task):
            raise ValidationError(f"L'entrée '{task_id}' n'est pas une tâche.")
        entry.mark_done()
        return entry

    def mark_task_cancelled(self, task_id: str) -> Task:
        """Marque une tâche du mois comme abandonnée."""
        entry = self.get_entry(task_id)
        if not isinstance(entry, Task):
            raise ValidationError(f"L'entrée '{task_id}' n'est pas une tâche.")
        entry.mark_cancelled()
        return entry

    def mark_task_migrated(self, task_id: str) -> Task:
        """Marque une tâche du mois comme migrée."""
        entry = self.get_entry(task_id)
        if not isinstance(entry, Task):
            raise ValidationError(f"L'entrée '{task_id}' n'est pas une tâche.")
        entry.mark_migrated()
        return entry

    def calendar_view(self) -> str:
        """Affiche la page Calendrier du mois avec les événements."""
        header = f"--- Page Calendrier : {self.name} ---"
        events_by_day: dict[int, list[Event]] = {}
        for ev in self.get_events():
            events_by_day.setdefault(ev.event_date.day, []).append(ev)

        num_days = calendar.monthrange(self._year, self._month)[1]
        lines = [header]
        for day in range(1, num_days + 1):
            day_date = date(self._year, self._month, day)
            day_abbr = day_date.strftime("%a")
            day_events = events_by_day.get(day, [])
            if day_events:
                ev_str = " | ".join(ev.display() for ev in day_events)
                lines.append(f"{day:02d} {day_abbr} {ev_str}")
            else:
                lines.append(f"{day:02d} {day_abbr}")
        return "\n".join(lines)

    def task_view(self) -> str:
        """Affiche la page Tâches du mois avec les symboles Rapid Logging."""
        header = f"--- Page Tâches : {self.name} ---"
        tasks = self.get_tasks()
        notes = self.get_notes()
        if not tasks and not notes:
            return f"{header}\n(Aucune tâche ou note ce mois-ci)"
        lines = [header]
        for task in tasks:
            lines.append(task.display())
        for note in notes:
            lines.append(note.display())
        return "\n".join(lines)

    def display(self) -> str:
        """Affichage complet du Monthly Log en notation Rapid Logging."""
        header = f"=== Monthly Log : {self.name} ==="
        return f"{header}\n\n{self.calendar_view()}\n\n{self.task_view()}"

    def __str__(self) -> str:
        """Affichage par défaut."""
        return self.display()

    def migrate_task(self, task_id: str, target_monthly_log: MonthlyLog) -> Task:
        """Migre une tâche de ce mois vers un autre MonthlyLog (ex: mois suivant)."""
        if not isinstance(target_monthly_log, MonthlyLog):
            raise ValidationError("Le journal cible doit être une instance de MonthlyLog.")

        origin_task = self.get_entry(task_id)
        if not isinstance(origin_task, Task):
            raise ValidationError(f"L'entrée '{task_id}' n'est pas une tâche.")

        if origin_task.status != TaskStatus.TO_DO:
            raise InvalidStatusTransitionError(
                current_status=origin_task.status.label,
                target_status=TaskStatus.MIGRATED.label,
                message=(
                    f"Impossible de migrer la tâche '{origin_task.title}' : "
                    f"seules les tâches à faire (TO_DO) peuvent être migrées."
                ),
            )

        origin_task.mark_migrated()
        new_task = target_monthly_log.add_task(
            title=origin_task.title,
            description=origin_task.description,
            category=origin_task.category,
            signifier=origin_task.signifier,
        )
        new_task._migrated_from_id = origin_task.id
        origin_task.migrated_to_id = new_task.id

        logger.info(
            "Tâche mensuelle migrée : id=%s (%04d-%02d) -> nouveau id=%s (%04d-%02d)",
            origin_task.id,
            self._year,
            self._month,
            new_task.id,
            target_monthly_log.year,
            target_monthly_log.month,
        )
        return new_task

    def migrate_pending_tasks(self, target_monthly_log: MonthlyLog) -> list[Task]:
        """Migre toutes les tâches non faites vers le MonthlyLog cible."""
        migrated: list[Task] = []
        for task in self.get_pending_tasks():
            migrated_task = self.migrate_task(task.id, target_monthly_log)
            migrated.append(migrated_task)
        return migrated


# =============================================================================
# 3. GESTIONNAIRE GLOBAL : BulletJournal
# =============================================================================

class BulletJournal:
    """Gestionnaire principal centralisant l'ensemble des journées et mois du carnet."""

    def __init__(self, owner: str = "Utilisateur") -> None:
        """Initialise un Bullet Journal."""
        self.owner: str = owner
        self._daily_logs: dict[date, DailyLog] = {}
        self._monthly_logs: dict[tuple[int, int], MonthlyLog] = {}
        logger.info("Nouveau BulletJournal initialisé pour %r", self.owner)

    @property
    def daily_logs(self) -> dict[date, DailyLog]:
        """Retourne le registre des Daily Logs."""
        return dict(self._daily_logs)

    @property
    def monthly_logs(self) -> dict[tuple[int, int], MonthlyLog]:
        """Retourne le registre des Monthly Logs."""
        return dict(self._monthly_logs)

    def get_daily_log(self, target_date: date | None = None) -> DailyLog:
        """Récupère le Daily Log d'une date (le crée automatiquement si inexistant)."""
        day = target_date or date.today()
        if day not in self._daily_logs:
            self._daily_logs[day] = DailyLog(day)
            logger.debug("Création automatique d'un DailyLog pour le %s", day)
        return self._daily_logs[day]

    def get_monthly_log(self, year: int | None = None, month: int | None = None) -> MonthlyLog:
        """Récupère le Monthly Log d'un mois (le crée automatiquement si inexistant)."""
        today = date.today()
        y = year if year is not None else today.year
        m = month if month is not None else today.month
        key = (y, m)
        if key not in self._monthly_logs:
            self._monthly_logs[key] = MonthlyLog(y, m)
            logger.debug("Création automatique d'un MonthlyLog pour %04d-%02d", y, m)
        return self._monthly_logs[key]

    def today(self) -> DailyLog:
        """Accès direct au Daily Log d'aujourd'hui."""
        return self.get_daily_log(date.today())

    def current_month(self) -> MonthlyLog:
        """Accès direct au Monthly Log du mois en cours."""
        today = date.today()
        return self.get_monthly_log(today.year, today.month)

    def add_task(
        self,
        title: str,
        description: str = "",
        log_date: date | None = None,
        category: str | None = None,
        signifier: Signifier | str | None = None,
    ) -> Task:
        """Ajoute une tâche dans le journal du jour (ou à une date spécifique)."""
        daily_log = self.get_daily_log(log_date)
        return daily_log.add_task(
            title=title,
            description=description,
            category=category,
            signifier=signifier,
        )

    def add_event(
        self,
        title: str,
        event_date: date | None = None,
        event_time: time | None = None,
        description: str = "",
        location: str | None = None,
        log_date: date | None = None,
        category: str | None = None,
        signifier: Signifier | str | None = None,
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
            signifier=signifier,
        )

    def add_note(
        self,
        title: str,
        description: str = "",
        log_date: date | None = None,
        category: str | None = None,
        signifier: Signifier | str | None = None,
    ) -> Note:
        """Ajoute une note dans le journal."""
        daily_log = self.get_daily_log(log_date)
        return daily_log.add_note(
            title=title,
            description=description,
            category=category,
            signifier=signifier,
        )

    def add_monthly_task(
        self,
        title: str,
        description: str = "",
        year: int | None = None,
        month: int | None = None,
        category: str | None = None,
        signifier: Signifier | str | None = None,
    ) -> Task:
        """Ajoute une tâche directement dans un Monthly Log."""
        monthly_log = self.get_monthly_log(year, month)
        return monthly_log.add_task(
            title=title,
            description=description,
            category=category,
            signifier=signifier,
        )

    def find_entry(self, entry_id: str) -> tuple[DailyLog | MonthlyLog, Entry]:
        """Recherche une entrée par son ID unique dans tous les DailyLogs et MonthlyLogs."""
        # 1. Recherche dans les journaux du jour
        for daily_log in self._daily_logs.values():
            try:
                return daily_log, daily_log.get_entry(entry_id)
            except EntryNotFoundError:
                continue

        # 2. Recherche dans les journaux du mois
        for monthly_log in self._monthly_logs.values():
            try:
                return monthly_log, monthly_log.get_entry(entry_id)
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
            log_container, _ = self.find_entry(task_id)
            entry = log_container.remove_entry(task_id)

        if not isinstance(entry, Task):
            log_container.add_entry(entry)
            msg = f"L'élément supprimé n'était pas une tâche mais un {type(entry)}."
            raise ValidationError(msg)
        return entry

    def migrate_task(self, task_id: str, target_date: date) -> Task:
        """Migre une tâche quotidienne vers une date cible."""
        log_container, entry = self.find_entry(task_id)
        if not isinstance(log_container, DailyLog) or not isinstance(entry, Task):
            raise ValidationError(f"L'entrée '{task_id}' doit être une tâche d'un DailyLog.")
        target_log = self.get_daily_log(target_date)
        return log_container.migrate_task(task_id, target_log)

    def migrate_monthly_task(
        self,
        task_id: str,
        target_year: int,
        target_month: int,
    ) -> Task:
        """Migre une tâche de MonthlyLog vers un autre mois."""
        log_container, entry = self.find_entry(task_id)
        if not isinstance(log_container, MonthlyLog) or not isinstance(entry, Task):
            raise ValidationError(f"L'entrée '{task_id}' doit être une tâche d'un MonthlyLog.")
        target_log = self.get_monthly_log(target_year, target_month)
        return log_container.migrate_task(task_id, target_log)

    def migrate_day_to_next(self, from_date: date | None = None) -> list[Task]:
        """Migre toutes les tâches non terminées d'une date vers le jour suivant."""
        current_date = from_date or date.today()
        next_date = current_date + timedelta(days=1)
        source_log = self.get_daily_log(current_date)
        target_log = self.get_daily_log(next_date)
        return source_log.migrate_pending_tasks(target_log)

    def get_pending_tasks(self, log_date: date | None = None) -> list[Task]:
        """Retourne la liste des tâches à faire (TO_DO)."""
        target_date = log_date or date.today()
        daily_log = self.get_daily_log(target_date)
        return daily_log.get_pending_tasks()

    def get_all_pending_tasks(self) -> list[Task]:
        """Retourne toutes les tâches en attente de tout le carnet (jours + mois)."""
        all_pending: list[Task] = []
        for daily_log in self._daily_logs.values():
            all_pending.extend(daily_log.get_pending_tasks())
        for monthly_log in self._monthly_logs.values():
            all_pending.extend(monthly_log.get_pending_tasks())
        return all_pending

    def display_today(self) -> str:
        """Affichage du journal du jour."""
        return self.today().display()

    def display_current_month(self) -> str:
        """Affichage du journal du mois en cours."""
        return self.current_month().display()
