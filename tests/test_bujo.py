"""Suite complète de tests unitaires pour le Bullet Journal (Niveau 1).

Tous les tests du projet sont regroupés ici :
1. Test des modèles et de la POO (Entry, Task, Event, Note, TaskStatus).
2. Test du cycle de vie des tâches et des exceptions de transition interdite.
3. Test du Daily Log (journal du jour) et de ses opérations (ajout, suppression, filtres).
4. Test du Bullet Journal (gestionnaire global, recherche transversale, homonymes).
5. Test de la journalisation (fichiers logs/debug.log et logs/errors.log).
"""

from datetime import date, datetime, time
from pathlib import Path
import pytest

from bujo import (
    BulletJournal,
    DailyLog,
    Entry,
    EntryNotFoundError,
    Event,
    InvalidStatusTransitionError,
    Note,
    Task,
    TaskStatus,
    ValidationError,
    setup_logging,
)


# =============================================================================
# 1. TESTS DES MODÈLES ET DE LA POO
# =============================================================================

class TestEntryBase:
    """Vérifie le comportement de la classe de base abstraite Entry."""

    def test_cannot_instantiate_abstract_entry(self) -> None:
        """La classe Entry étant abstraite, son instanciation directe doit être bloquée."""
        with pytest.raises(TypeError):
            Entry(title="Test")  # type: ignore[abstract]

    def test_empty_title_raises_validation_error(self) -> None:
        """Un titre vide ou avec uniquement des espaces doit lever une ValidationError."""
        with pytest.raises(ValidationError, match="ne peut pas être vide"):
            Task(title="")

        with pytest.raises(ValidationError, match="ne peut pas être vide"):
            Task(title="   ")

    def test_whitespace_is_stripped_from_title(self) -> None:
        """Les espaces superflus autour du titre doivent être nettoyés."""
        task = Task(title="  Faire le rapport  ")
        assert task.title == "Faire le rapport"

    def test_unique_identifier_generation(self) -> None:
        """Deux entrées créées consécutivement doivent recevoir des identifiants distincts."""
        t1 = Task(title="Tâche 1")
        t2 = Task(title="Tâche 2")
        assert t1.id != t2.id
        assert isinstance(t1.id, str)
        assert len(t1.id) > 0

    def test_custom_entry_id(self) -> None:
        """Un identifiant personnalisé explicite peut être passé lors de l'instanciation."""
        task = Task(title="Tâche", entry_id="custom-123")
        assert task.id == "custom-123"

    def test_log_date_validation(self) -> None:
        """Modifier log_date avec un type non-date doit lever une ValidationError."""
        task = Task(title="Tâche")
        with pytest.raises(ValidationError):
            task.log_date = "2026-11-05"  # type: ignore[assignment]


class TestTaskLifecycle:
    """Vérifie le cycle de vie complet d'une tâche et les règles métier BuJo."""

    def test_default_task_status_is_to_do(self) -> None:
        """À la création, une tâche doit être à l'état initial 'À faire' (symbole •)."""
        task = Task(title="Apprendre le BuJo", description="Lire le livre de Ryder Carroll")
        assert task.status == TaskStatus.TO_DO
        assert task.is_pending is True
        assert task.is_done is False
        assert task.symbol == "•"
        assert task.completed_at is None
        assert "Apprendre le BuJo" in task.display()

    def test_mark_task_as_done(self) -> None:
        """Une tâche terminée passe au statut DONE avec le symbole × et sa date de fin."""
        task = Task(title="Acheter un carnet")
        task.mark_done()
        assert task.status == TaskStatus.DONE
        assert task.is_done is True
        assert task.is_pending is False
        assert task.symbol == "×"
        assert isinstance(task.completed_at, datetime)

    def test_task_status_history_tracking(self) -> None:
        """Chaque changement d'état doit être mémorisé dans l'historique."""
        task = Task(title="Réviser les cours")
        assert len(task.history) == 1
        assert task.history[0][0] == TaskStatus.TO_DO

        task.mark_done()
        assert len(task.history) == 2
        assert task.history[1][0] == TaskStatus.DONE

    def test_task_migration_and_scheduling(self) -> None:
        """Test des états Migrée (>) et Planifiée (<)."""
        task_migrated = Task(title="Tâche à reporter")
        task_migrated.mark_migrated()
        assert task_migrated.status == TaskStatus.MIGRATED
        assert task_migrated.symbol == ">"

        task_scheduled = Task(title="Tâche future")
        task_scheduled.mark_scheduled()
        assert task_scheduled.status == TaskStatus.SCHEDULED
        assert task_scheduled.symbol == "<"

    def test_task_cancellation(self) -> None:
        """Une tâche peut être abandonnée (symbole ~)."""
        task = Task(title="Idée inutile")
        task.mark_cancelled()
        assert task.status == TaskStatus.CANCELLED
        assert task.symbol == "~"

    def test_cannot_complete_cancelled_task(self) -> None:
        """Règle métier explicite : interdiction de terminer une tâche abandonnée."""
        task = Task(title="Tâche abandonnée")
        task.mark_cancelled()

        with pytest.raises(
            InvalidStatusTransitionError,
            match="Impossible de marquer comme terminée",
        ):
            task.mark_done()

    def test_cannot_cancel_already_done_task(self) -> None:
        """Une tâche déjà terminée ne peut pas être abandonnée directement."""
        task = Task(title="Tâche terminée")
        task.mark_done()

        with pytest.raises(InvalidStatusTransitionError):
            task.mark_cancelled()

    def test_cannot_migrate_already_done_task(self) -> None:
        """Une tâche déjà terminée ne peut pas être migrée."""
        task = Task(title="Tâche terminée")
        task.mark_done()

        with pytest.raises(InvalidStatusTransitionError):
            task.mark_migrated()

    def test_reopen_task(self) -> None:
        """Une tâche terminée peut être réouverte si l'utilisateur s'est trompé."""
        task = Task(title="Tâche réouverte")
        task.mark_done()
        assert task.is_done is True
        task.reopen()
        assert task.status == TaskStatus.TO_DO
        assert task.completed_at is None


class TestEventAndNoteModels:
    """Vérifie les modèles Event et Note."""

    def test_event_creation_with_valid_data(self) -> None:
        """Création complète d'un événement avec date, heure et lieu."""
        ev_date = date(2026, 12, 16)
        ev_time = time(14, 30)
        event = Event(
            title="Soutenance de projet",
            event_date=ev_date,
            event_time=ev_time,
            location="Salle B204",
            description="Présentation BuJo",
        )
        assert event.title == "Soutenance de projet"
        assert event.event_date == ev_date
        assert event.event_time == ev_time
        assert event.location == "Salle B204"
        assert event.symbol == "○"
        assert "14:30" in event.display()
        assert "Salle B204" in event.display()

    def test_invalid_event_date_raises_error(self) -> None:
        """Fournir une chaîne au lieu d'un objet date doit lever une ValidationError."""
        with pytest.raises(ValidationError):
            Event(title="Invalide", event_date="demain")  # type: ignore[arg-type]

    def test_invalid_event_time_raises_error(self) -> None:
        """Fournir une valeur invalide pour l'heure doit lever une ValidationError."""
        event = Event(title="Test", event_date=date.today())
        with pytest.raises(ValidationError):
            event.event_time = "14:00"  # type: ignore[assignment]

    def test_note_creation(self) -> None:
        """Création d'une note avec symbole – et contenu textuel."""
        note = Note(
            title="Citation inspirante",
            description="Le secret pour avancer est de commencer.",
        )
        assert note.title == "Citation inspirante"
        assert note.content == "Le secret pour avancer est de commencer."
        assert note.symbol == "–"
        assert "Citation inspirante" in note.display()


# =============================================================================
# 2. TESTS DU DAILY LOG (JOURNAL DU JOUR)
# =============================================================================

class TestDailyLog:
    """Tests pour la classe DailyLog (le journal d'une journée)."""

    def test_add_task_to_daily_log(self) -> None:
        """Vérifie l'ajout d'une tâche et l'alignement automatique de la date de log."""
        log = DailyLog(date(2026, 11, 5))
        task = log.add_task(title="Rédiger le code", description="Implémenter le Niveau 1")
        assert len(log) == 1
        assert task.id in [e.id for e in log.entries]
        assert task.log_date == date(2026, 11, 5)

    def test_add_event_and_note(self) -> None:
        """Vérifie la coexistence des 3 types d'entrées (tâches, événements, notes)."""
        log = DailyLog(date(2026, 11, 5))
        event = log.add_event(
            title="Réunion d'équipe",
            event_time=time(10, 0),
            location="Discord",
        )
        note = log.add_note(title="Remarque importante", description="Prévoir les tests")

        assert len(log) == 2
        assert len(log.get_events()) == 1
        assert len(log.get_notes()) == 1
        assert log.get_events()[0] == event
        assert log.get_notes()[0] == note

    def test_get_entry_by_id(self) -> None:
        """Accès direct en temps constant O(1) à une entrée par son identifiant unique."""
        log = DailyLog()
        task = log.add_task(title="Tâche A")
        retrieved = log.get_entry(task.id)
        assert retrieved == task

    def test_get_unknown_entry_raises_error(self) -> None:
        """Rechercher un identifiant inexistant doit lever EntryNotFoundError."""
        log = DailyLog()
        with pytest.raises(EntryNotFoundError):
            log.get_entry("id-inexistant")

    def test_remove_entry(self) -> None:
        """Suppression d'une entrée et vérification qu'elle n'est plus accessible."""
        log = DailyLog()
        task = log.add_task(title="À supprimer")
        assert len(log) == 1
        removed = log.remove_entry(task.id)
        assert removed.id == task.id
        assert len(log) == 0

        with pytest.raises(EntryNotFoundError):
            log.remove_entry(task.id)

    def test_get_pending_tasks(self) -> None:
        """Le filtre des tâches en cours ne doit garder que celles avec le statut TO_DO."""
        log = DailyLog()
        t1 = log.add_task(title="Tâche 1")
        t2 = log.add_task(title="Tâche 2")
        t3 = log.add_task(title="Tâche 3")

        log.mark_task_done(t2.id)

        pending = log.get_pending_tasks()
        assert len(pending) == 2
        assert t1 in pending
        assert t3 in pending
        assert t2 not in pending

    def test_mark_task_done_on_non_task_raises_validation_error(self) -> None:
        """Tenter d'appeler mark_task_done sur une Note doit lever une ValidationError."""
        log = DailyLog()
        note = log.add_note(title="Une note simple")
        with pytest.raises(ValidationError, match="pas une tâche"):
            log.mark_task_done(note.id)

    def test_display_daily_log(self) -> None:
        """L'affichage formaté doit contenir la date et le titre de la tâche."""
        log = DailyLog(date(2026, 11, 5))
        log.add_task(title="Tâche test")
        output = log.display()
        assert "Daily Log" in output
        assert "Tâche test" in output


# =============================================================================
# 3. TESTS DU BULLET JOURNAL (GESTIONNAIRE GLOBAL)
# =============================================================================

class TestBulletJournal:
    """Tests pour la classe BulletJournal (socle Niveau 1)."""

    def test_add_and_complete_task_in_today_log(self) -> None:
        """Exigence Niveau 1 : Ajouter une tâche au journal du jour et la marquer terminée."""
        journal = BulletJournal(owner="Testeur")
        task = journal.add_task(
            title="Acheter du pain",
            description="Baguette tradition",
        )
        assert task.status == TaskStatus.TO_DO

        pending = journal.get_pending_tasks()
        assert len(pending) == 1
        assert pending[0].id == task.id

        updated = journal.mark_task_done(task.id)
        assert updated.status == TaskStatus.DONE
        assert updated.is_done is True
        assert len(journal.get_pending_tasks()) == 0

    def test_remove_task_from_journal(self) -> None:
        """Exigence Niveau 1 : Supprimer une tâche du journal."""
        journal = BulletJournal(owner="Testeur")
        task = journal.add_task(title="Tâche éphémère")
        assert len(journal.get_pending_tasks()) == 1

        removed = journal.remove_task(task.id)
        assert removed.id == task.id
        assert len(journal.get_pending_tasks()) == 0

        with pytest.raises(EntryNotFoundError):
            journal.find_entry(task.id)

    def test_display_pending_tasks(self) -> None:
        """Exigence Niveau 1 : Afficher la liste des tâches en cours."""
        journal = BulletJournal(owner="Testeur")
        journal.add_task(title="Tâche Alpha")
        t2 = journal.add_task(title="Tâche Bêta")
        journal.add_task(title="Tâche Gamma")

        journal.mark_task_done(t2.id)

        pending = journal.get_pending_tasks()
        titles = [t.title for t in pending]
        assert "Tâche Alpha" in titles
        assert "Tâche Gamma" in titles
        assert "Tâche Bêta" not in titles

    def test_tasks_with_same_name_are_distinguished_by_unique_id(self) -> None:
        """Exigence clé : Deux tâches peuvent avoir le même nom avec des IDs distincts."""
        journal = BulletJournal(owner="Testeur")
        t1 = journal.add_task(title="Faire du sport")
        t2 = journal.add_task(title="Faire du sport")

        assert t1.title == t2.title
        assert t1.id != t2.id

        journal.mark_task_done(t1.id)
        assert t1.is_done is True
        assert t2.is_pending is True

    def test_find_entry_across_different_days(self) -> None:
        """find_entry retrouve une entrée même si elle a été créée un autre jour."""
        journal = BulletJournal(owner="Testeur")
        yesterday = date(2026, 11, 4)
        today = date(2026, 11, 5)

        t_yesterday = journal.add_task(title="Hier", log_date=yesterday)
        t_today = journal.add_task(title="Aujourd'hui", log_date=today)

        log_found, entry = journal.find_entry(t_yesterday.id)
        assert log_found.log_date == yesterday
        assert entry.id == t_yesterday.id

        log_found_today, entry_today = journal.find_entry(t_today.id)
        assert log_found_today.log_date == today
        assert entry_today.id == t_today.id

    def test_display_today(self) -> None:
        """Aperçu de la page d'aujourd'hui."""
        journal = BulletJournal(owner="Testeur")
        journal.add_task(title="Ma tâche du jour")
        journal.add_note(title="Une simple note")
        display = journal.display_today()
        assert "Ma tâche du jour" in display
        assert "Une simple note" in display


# =============================================================================
# 4. TESTS DU SYSTÈME DE LOGS
# =============================================================================

def test_logging_generates_debug_and_error_files(tmp_path: Path) -> None:
    """Vérifie la création conforme de debug.log et errors.log."""
    log_dir = tmp_path / "logs"
    logger = setup_logging(log_dir=log_dir, force_reconfigure=True)

    debug_file = log_dir / "debug.log"
    errors_file = log_dir / "errors.log"

    assert debug_file.exists()
    assert errors_file.exists()

    journal = BulletJournal(owner="TestUser")
    task = journal.add_task(title="Tâche de test log", description="Description")
    task.mark_cancelled()

    with pytest.raises(InvalidStatusTransitionError):
        task.mark_done()

    for handler in logger.handlers:
        handler.flush()

    debug_content = debug_file.read_text(encoding="utf-8")
    errors_content = errors_file.read_text(encoding="utf-8")

    assert "Tâche créée" in debug_content or "Initialisation" in debug_content
    assert "Tentative interdite" in errors_content
