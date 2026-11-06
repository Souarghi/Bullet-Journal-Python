"""Modèles de données et exceptions du Bullet Journal.

Ce fichier regroupe en un seul endroit :
1. Les exceptions personnalisées (erreurs métier du carnet).
2. La classe de base abstraite `Entry` (propriétés communes, id unique, dates).
3. La classe `Task` et l'énumération `TaskStatus` (gestion du cycle de vie •, ×, >, <, ~).
4. La classe `Event` (événements avec date, heure et lieu ○).
5. La classe `Note` (notes et réflexions –).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date, datetime, time
from enum import Enum
import uuid

from bujo.logger import get_logger

logger = get_logger("models")


# =============================================================================
# 1. EXCEPTIONS PERSONNALISÉES
# =============================================================================

class BujoError(Exception):
    """Exception de base pour toutes les erreurs spécifiques au Bullet Journal."""

    pass


class ValidationError(BujoError):
    """Levée lorsqu'une donnée est invalide (ex: nom vide, type de date incorrect)."""

    pass


class EntryNotFoundError(BujoError):
    """Levée lorsqu'un identifiant recherché n'existe dans aucun log."""

    def __init__(self, entry_id: str, message: str | None = None) -> None:
        """Enregistre l'ID introuvable pour faciliter le débogage."""
        self.entry_id = entry_id
        default_message = f"L'entrée avec l'identifiant '{entry_id}' est introuvable."
        super().__init__(message or default_message)


class InvalidStatusTransitionError(BujoError):
    """Levée lors d'un changement d'état interdit (ex: terminer une tâche abandonnée)."""

    def __init__(
        self,
        current_status: str,
        target_status: str,
        message: str | None = None,
    ) -> None:
        """Conserve le statut de départ et le statut visé pour expliquer le refus."""
        self.current_status = current_status
        self.target_status = target_status
        default_message = (
            f"Transition d'état invalide : impossible de passer de "
            f"'{current_status}' à '{target_status}'."
        )
        super().__init__(message or default_message)


# =============================================================================
# 2. CLASSE DE BASE ABSTRAITE : Entry
# =============================================================================

class Entry(ABC):
    """Classe abstraite représentant une entrée générique dans un Bullet Journal.

    Chaque entrée possède obligatoirement :
    - Un identifiant unique (`id`) généré automatiquement (UUID) pour distinguer
      les tâches ayant le même nom.
    - Un nom / titre (`title`) obligatoirement non vide.
    - Une description optionnelle (`description`).
    - Un horodatage de création (`created_at`).
    - Une date de rattachement au log (`log_date`).
    - Une catégorie ou collection optionnelle (`category`).
    """

    def __init__(
        self,
        title: str,
        description: str = "",
        log_date: date | None = None,
        category: str | None = None,
        entry_id: str | None = None,
        created_at: datetime | None = None,
    ) -> None:
        """Initialise une nouvelle entrée de journal."""
        # ID unique de 8 caractères hexadécimaux pour identifier sans ambiguïté chaque élément
        self._id: str = entry_id or uuid.uuid4().hex[:8]
        self._created_at: datetime = created_at or datetime.now()
        self._log_date: date = log_date or date.today()
        self._category: str | None = category
        self._description: str = description.strip()

        # Validation du titre via le setter @title.setter
        self._title: str = ""
        self.title = title

    @property
    def id(self) -> str:
        """Retourne l'identifiant unique de l'entrée."""
        return self._id

    @property
    def title(self) -> str:
        """Retourne le titre de l'entrée."""
        return self._title

    @title.setter
    def title(self, value: str) -> None:
        """Modifie le titre après validation obligatoire (interdiction d'un titre vide)."""
        if not isinstance(value, str) or not value.strip():
            raise ValidationError("Le nom ou titre d'une entrée ne peut pas être vide.")
        self._title = value.strip()

    @property
    def description(self) -> str:
        """Retourne la description détaillée."""
        return self._description

    @description.setter
    def description(self, value: str) -> None:
        """Modifie la description."""
        self._description = value.strip() if isinstance(value, str) else ""

    @property
    def created_at(self) -> datetime:
        """Retourne la date et l'heure de création."""
        return self._created_at

    @property
    def log_date(self) -> date:
        """Retourne la date du log auquel l'entrée appartient."""
        return self._log_date

    @log_date.setter
    def log_date(self, value: date) -> None:
        """Modifie la date du log avec contrôle de type."""
        if not isinstance(value, date):
            raise ValidationError("La date du log doit être un objet date valide.")
        self._log_date = value

    @property
    def category(self) -> str | None:
        """Retourne la catégorie ou collection optionnelle."""
        return self._category

    @category.setter
    def category(self, value: str | None) -> None:
        """Modifie la catégorie."""
        self._category = value.strip() if isinstance(value, str) and value.strip() else None

    # Méthodes abstraites polymorphes : obligatoires pour chaque sous-classe
    @property
    @abstractmethod
    def symbol(self) -> str:
        """Retourne le symbole conventionnel BuJo (ex: •, ○, –)."""
        pass

    @abstractmethod
    def display(self) -> str:
        """Retourne une représentation textuelle mise en forme."""
        pass

    def __str__(self) -> str:
        """Affichage par défaut via la méthode display()."""
        return self.display()

    def __repr__(self) -> str:
        """Affichage technique pour le débogage."""
        return (
            f"<{self.__class__.__name__} id={self._id!r} "
            f"title={self._title!r} log_date={self._log_date}>"
        )

    def __eq__(self, other: object) -> bool:
        """Deux entrées sont identiques si elles partagent le même identifiant."""
        if not isinstance(other, Entry):
            return False
        return self._id == other._id

    def __hash__(self) -> int:
        """Hash basé sur l'identifiant unique."""
        return hash(self._id)


# =============================================================================
# 3. STATUT ET CYCLE DE VIE D'UNE TÂCHE : Task & TaskStatus
# =============================================================================

class TaskStatus(Enum):
    """Énumération des états possibles d'une tâche et symboles associés.

    Symboles officiels :
    - TO_DO     : • (tâche à faire)
    - DONE      : × (tâche accomplie)
    - MIGRATED  : > (tâche reportée)
    - SCHEDULED : < (tâche planifiée dans le Future Log)
    - CANCELLED : ~ (tâche abandonnée)
    """

    TO_DO = "to_do"
    DONE = "done"
    MIGRATED = "migrated"
    SCHEDULED = "scheduled"
    CANCELLED = "cancelled"

    @property
    def symbol(self) -> str:
        """Symbole graphique associé à l'état."""
        symbols = {
            TaskStatus.TO_DO: "•",
            TaskStatus.DONE: "×",
            TaskStatus.MIGRATED: ">",
            TaskStatus.SCHEDULED: "<",
            TaskStatus.CANCELLED: "~",
        }
        return symbols[self]

    @property
    def label(self) -> str:
        """Libellé en français."""
        labels = {
            TaskStatus.TO_DO: "À faire",
            TaskStatus.DONE: "Terminée",
            TaskStatus.MIGRATED: "Migrée",
            TaskStatus.SCHEDULED: "Planifiée",
            TaskStatus.CANCELLED: "Abandonnée",
        }
        return labels[self]


class Task(Entry):
    """Représente une tâche et son cycle de vie dans le Bullet Journal."""

    def __init__(
        self,
        title: str,
        description: str = "",
        log_date: date | None = None,
        category: str | None = None,
        entry_id: str | None = None,
        created_at: datetime | None = None,
        status: TaskStatus = TaskStatus.TO_DO,
    ) -> None:
        """Initialise une tâche (statut initial À faire par défaut)."""
        super().__init__(
            title=title,
            description=description,
            log_date=log_date,
            category=category,
            entry_id=entry_id,
            created_at=created_at,
        )
        self._status: TaskStatus = status
        self._completed_at: datetime | None = None
        if status == TaskStatus.DONE:
            self._completed_at = self.created_at

        # Historique de vie : liste de tuples (statut, horodatage)
        self._history: list[tuple[TaskStatus, datetime]] = [(self._status, self.created_at)]
        logger.debug("Tâche créée : id=%s, titre=%r, statut=%s", self.id, self.title, self.status)

    @property
    def status(self) -> TaskStatus:
        """Retourne le statut actuel."""
        return self._status

    @property
    def completed_at(self) -> datetime | None:
        """Retourne l'horodatage de fin (ou None)."""
        return self._completed_at

    @property
    def history(self) -> list[tuple[TaskStatus, datetime]]:
        """Retourne l'historique des changements d'état."""
        return list(self._history)

    @property
    def symbol(self) -> str:
        """Symbole conventionnel correspondant au statut courant."""
        return self._status.symbol

    @property
    def is_pending(self) -> bool:
        """Indique si la tâche est en cours / à faire."""
        return self._status == TaskStatus.TO_DO

    @property
    def is_done(self) -> bool:
        """Indique si la tâche est terminée."""
        return self._status == TaskStatus.DONE

    def _transition_to(self, new_status: TaskStatus) -> None:
        """Valide et applique une transition d'état selon les règles métier."""
        if self._status == new_status:
            return

        # Règle métier explicite : interdiction de terminer une tâche abandonnée
        if self._status == TaskStatus.CANCELLED and new_status == TaskStatus.DONE:
            logger.error("Tentative interdite de terminer une tâche abandonnée (id=%s)", self.id)
            raise InvalidStatusTransitionError(
                current_status=self._status.label,
                target_status=new_status.label,
                message="Impossible de marquer comme terminée une tâche abandonnée.",
            )

        # Une tâche déjà terminée ne peut pas être migrée, planifiée ou annulée directement
        if self._status == TaskStatus.DONE and new_status in (
            TaskStatus.MIGRATED,
            TaskStatus.SCHEDULED,
            TaskStatus.CANCELLED,
        ):
            logger.error("Tentative interdite de modifier une tâche déjà terminée (id=%s)", self.id)
            raise InvalidStatusTransitionError(
                current_status=self._status.label,
                target_status=new_status.label,
                message=f"Une tâche déjà terminée ne peut pas être passée en '{new_status.label}'.",
            )

        # Une tâche migrée ne peut pas être modifiée directement
        if self._status == TaskStatus.MIGRATED and new_status != TaskStatus.TO_DO:
            logger.error("Tentative de modification d'une tâche déjà migrée (id=%s)", self.id)
            raise InvalidStatusTransitionError(
                current_status=self._status.label,
                target_status=new_status.label,
                message="Une tâche déjà migrée ne peut pas être modifiée directement.",
            )

        now = datetime.now()
        previous_status = self._status
        self._status = new_status
        self._history.append((new_status, now))

        if new_status == TaskStatus.DONE:
            self._completed_at = now
        elif previous_status == TaskStatus.DONE and new_status != TaskStatus.DONE:
            self._completed_at = None

        logger.debug("Transition tâche id=%s : %s -> %s", self.id, previous_status, new_status)

    def mark_done(self) -> None:
        """Marque la tâche comme terminée (×)."""
        self._transition_to(TaskStatus.DONE)

    def mark_migrated(self) -> None:
        """Marque la tâche comme reportée (symbole >)."""
        self._transition_to(TaskStatus.MIGRATED)

    def mark_scheduled(self) -> None:
        """Marque la tâche comme planifiée au Future Log (symbole <)."""
        self._transition_to(TaskStatus.SCHEDULED)

    def mark_cancelled(self) -> None:
        """Marque la tâche comme abandonnée (symbole ~)."""
        self._transition_to(TaskStatus.CANCELLED)

    def reopen(self) -> None:
        """Réactive la tâche à l'état À faire (symbole •)."""
        self._transition_to(TaskStatus.TO_DO)

    def display(self) -> str:
        """Affichage avec symbole BuJo (ex: • [id] Acheter du pain)."""
        desc = f" - {self.description}" if self.description else ""
        return f"{self.symbol} [{self.id}] {self.title}{desc}"


# =============================================================================
# 4. ÉVÉNEMENT : Event
# =============================================================================

class Event(Entry):
    """Représente un événement dans le Bullet Journal (symbole ○)."""

    def __init__(
        self,
        title: str,
        event_date: date,
        event_time: time | None = None,
        description: str = "",
        location: str | None = None,
        log_date: date | None = None,
        category: str | None = None,
        entry_id: str | None = None,
        created_at: datetime | None = None,
    ) -> None:
        """Initialise un événement."""
        if not isinstance(event_date, date):
            raise ValidationError(
                "La date de l'événement (event_date) est obligatoire et invalide."
            )

        target_log_date = log_date or event_date
        super().__init__(
            title=title,
            description=description,
            log_date=target_log_date,
            category=category,
            entry_id=entry_id,
            created_at=created_at,
        )
        self._event_date: date = event_date
        self._event_time: time | None = event_time
        self._location: str | None = location.strip() if isinstance(location, str) else None
        logger.debug("Événement créé : id=%s, titre=%r", self.id, self.title)

    @property
    def event_date(self) -> date:
        """Date de l'événement."""
        return self._event_date

    @event_date.setter
    def event_date(self, value: date) -> None:
        """Modifie la date avec validation."""
        if not isinstance(value, date):
            raise ValidationError("La date de l'événement doit être un objet date valide.")
        self._event_date = value

    @property
    def event_time(self) -> time | None:
        """Heure optionnelle."""
        return self._event_time

    @event_time.setter
    def event_time(self, value: time | None) -> None:
        """Modifie l'heure."""
        if value is not None and not isinstance(value, time):
            raise ValidationError("L'heure de l'événement doit être un objet time valide.")
        self._event_time = value

    @property
    def location(self) -> str | None:
        """Lieu optionnel."""
        return self._location

    @location.setter
    def location(self, value: str | None) -> None:
        """Modifie le lieu."""
        self._location = value.strip() if isinstance(value, str) and value.strip() else None

    @property
    def symbol(self) -> str:
        """Symbole conventionnel ○."""
        return "○"

    def display(self) -> str:
        """Rendu textuel d'un événement (ex: ○ [id] Réunion (14:30) @ Salle B204)."""
        parts = [f"{self.symbol} [{self.id}] {self.title}"]
        time_str = f" à {self.event_time.strftime('%H:%M')}" if self.event_time else ""
        date_str = f" ({self.event_date.strftime('%Y-%m-%d')}{time_str})"
        parts.append(date_str)
        if self.location:
            parts.append(f" @ {self.location}")
        if self.description:
            parts.append(f" - {self.description}")
        return "".join(parts)


# =============================================================================
# 5. NOTE : Note
# =============================================================================

class Note(Entry):
    """Représente une note dans le Bullet Journal (symbole –)."""

    def __init__(
        self,
        title: str,
        description: str = "",
        log_date: date | None = None,
        category: str | None = None,
        entry_id: str | None = None,
        created_at: datetime | None = None,
    ) -> None:
        """Initialise une note."""
        super().__init__(
            title=title,
            description=description,
            log_date=log_date,
            category=category,
            entry_id=entry_id,
            created_at=created_at,
        )
        logger.debug("Note créée : id=%s, titre=%r", self.id, self.title)

    @property
    def content(self) -> str:
        """Contenu de la note (alias pour la description)."""
        return self._description

    @content.setter
    def content(self, value: str) -> None:
        """Modifie le contenu."""
        self.description = value

    @property
    def symbol(self) -> str:
        """Symbole conventionnel –."""
        return "–"

    def display(self) -> str:
        """Rendu textuel d'une note (ex: – [id] Idée de lecture)."""
        desc = f" - {self.description}" if self.description else ""
        return f"{self.symbol} [{self.id}] {self.title}{desc}"
