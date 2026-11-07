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
    MonthlyLog,
    Note,
    Signifier,
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


# =============================================================================
# 5. TESTS DES SIGNIFIANTS (NIVEAU 2)
# =============================================================================

class TestSignifiers:
    """Vérifie la gestion des signifiants (priorité, idée) de Ryder Carroll."""

    def test_signifier_enum_properties(self) -> None:
        """Contrôle les symboles et libellés des signifiants."""
        assert Signifier.PRIORITY.symbol == "*"
        assert Signifier.IDEA.symbol == "!"
        assert "Prioritaire" in Signifier.PRIORITY.label
        assert "Idée" in Signifier.IDEA.label

    def test_signifier_from_value_conversion(self) -> None:
        """from_value convertit correctement chaînes, enums et None."""
        assert Signifier.from_value("*") == Signifier.PRIORITY
        assert Signifier.from_value("!") == Signifier.IDEA
        assert Signifier.from_value("priority") == Signifier.PRIORITY
        assert Signifier.from_value("idea") == Signifier.IDEA
        assert Signifier.from_value(None) is None
        assert Signifier.from_value("   ") is None

    def test_invalid_signifier_raises_validation_error(self) -> None:
        """Un signifiant inconnu lève une ValidationError."""
        with pytest.raises(ValidationError, match="Signifiant invalide"):
            Signifier.from_value("?")

    def test_task_with_priority_signifier_display(self) -> None:
        """Une tâche prioritaire affiche le symbole '*' devant sa puce."""
        task = Task(title="Rapport urgent", signifier=Signifier.PRIORITY)
        assert task.signifier == Signifier.PRIORITY
        assert task.signifier_prefix == "* "
        rendered = task.display()
        assert rendered.startswith("* • [")
        assert "Rapport urgent" in rendered

    def test_note_with_idea_signifier_display(self) -> None:
        """Une note d'inspiration affiche le symbole '!' devant son tiret."""
        note = Note(title="Idée de startup", signifier="!")
        assert note.signifier == Signifier.IDEA
        assert note.signifier_prefix == "! "
        rendered = note.display()
        assert rendered.startswith("! – [")

    def test_dynamically_modify_signifier(self) -> None:
        """Le signifiant d'une tâche peut être modifié ou retiré à la volée."""
        task = Task(title="Vérifier les serveurs")
        assert task.signifier is None
        assert task.signifier_prefix == ""

        task.signifier = "*"
        assert task.signifier == Signifier.PRIORITY
        assert task.signifier_prefix == "* "

        task.signifier = None
        assert task.signifier is None
        assert task.signifier_prefix == ""


# =============================================================================
# 6. TESTS DU MONTHLY LOG (NIVEAU 2)
# =============================================================================

class TestMonthlyLog:
    """Vérifie le fonctionnement de la vue mensuelle (MonthlyLog)."""

    def test_monthly_log_initialization(self) -> None:
        """Initialisation nominale d'un Monthly Log."""
        month_log = MonthlyLog(year=2026, month=11)
        assert month_log.year == 2026
        assert month_log.month == 11
        assert "Novembre 2026" in month_log.name
        assert len(month_log) == 0

    def test_invalid_month_raises_validation_error(self) -> None:
        """Un mois hors de l'intervalle 1-12 est refusé."""
        with pytest.raises(ValidationError, match="Mois invalide"):
            MonthlyLog(year=2026, month=13)
        with pytest.raises(ValidationError, match="Mois invalide"):
            MonthlyLog(year=2026, month=0)

    def test_monthly_log_add_task_event_note(self) -> None:
        """Ajout de différents types d'entrées dans le MonthlyLog."""
        m_log = MonthlyLog(year=2026, month=11)
        t = m_log.add_task(title="Objectif du mois", signifier="*")
        ev = m_log.add_event(title="Séminaire", event_date=date(2026, 11, 15))
        n = m_log.add_note(title="Bilan intermédiaire")

        assert len(m_log) == 3
        assert len(m_log.get_tasks()) == 1
        assert len(m_log.get_events()) == 1
        assert len(m_log.get_notes()) == 1
        assert m_log.get_entry(t.id).id == t.id
        assert ev.event_date == date(2026, 11, 15)
        assert n.title == "Bilan intermédiaire"

    def test_event_date_mismatch_raises_validation_error(self) -> None:
        """Un événement dont la date ne correspond pas au mois du log est rejeté."""
        m_log = MonthlyLog(year=2026, month=11)
        with pytest.raises(ValidationError, match="ne correspond pas au mois"):
            m_log.add_event(title="Noël", event_date=date(2026, 12, 25))

    def test_monthly_log_calendar_and_task_views(self) -> None:
        """Vérifie la génération des pages Calendrier et Tâches."""
        m_log = MonthlyLog(year=2026, month=11)
        m_log.add_event(title="Réunion client", event_date=date(2026, 11, 10))
        m_log.add_task(title="Préparer le bilan", signifier="*")

        cal_view = m_log.calendar_view()
        assert "Page Calendrier" in cal_view
        assert "10" in cal_view
        assert "Réunion client" in cal_view

        task_view = m_log.task_view()
        assert "Page Tâches" in task_view
        assert "Préparer le bilan" in task_view

        full_display = m_log.display()
        assert "Monthly Log" in full_display

    def test_monthly_log_mark_done_and_remove(self) -> None:
        """Accomplissement et suppression d'une tâche dans le MonthlyLog."""
        m_log = MonthlyLog(year=2026, month=11)
        t = m_log.add_task(title="Finir le rapport")
        assert t.is_pending is True

        m_log.mark_task_done(t.id)
        assert t.is_done is True
        assert len(m_log.get_pending_tasks()) == 0

        m_log.remove_entry(t.id)
        assert len(m_log) == 0


# =============================================================================
# 7. TESTS DES MIGRATIONS DE TÂCHES (NIVEAU 2)
# =============================================================================

class TestMigration:
    """Vérifie les mécanismes de migration de tâches quotidiennes et mensuelles."""

    def test_daily_task_migration_nominal(self) -> None:
        """Migration nominale d'une tâche d'un jour vers le jour suivant."""
        day1 = DailyLog(log_date=date(2026, 11, 5))
        day2 = DailyLog(log_date=date(2026, 11, 6))

        t1 = day1.add_task(
            title="Acheter un livre",
            description="Édition de poche",
            category="Personnel",
            signifier="*",
        )

        assert t1.status == TaskStatus.TO_DO
        assert t1.symbol == "•"

        # Exécuter la migration vers day2
        t2 = day1.migrate_task(t1.id, day2)

        # 1. Vérification de la tâche d'origine : passée en MIGRATED ('>')
        assert t1.status == TaskStatus.MIGRATED
        assert t1.symbol == ">"
        assert t1.migrated_to_id == t2.id

        # 2. Vérification de la tâche cible : nouvelle tâche TO_DO ('•') sur day2
        assert t2.status == TaskStatus.TO_DO
        assert t2.symbol == "•"
        assert t2.title == "Acheter un livre"
        assert t2.description == "Édition de poche"
        assert t2.category == "Personnel"
        assert t2.signifier == Signifier.PRIORITY
        assert t2.log_date == date(2026, 11, 6)
        assert t2.migrated_from_id == t1.id

        # Les deux tâches ont des identifiants uniques distincts
        assert t1.id != t2.id
        assert len(day1) == 1
        assert len(day2) == 1

    def test_cannot_migrate_done_or_cancelled_task(self) -> None:
        """Une tâche terminée ou abandonnée ne peut pas être migrée."""
        day1 = DailyLog(log_date=date(2026, 11, 5))
        day2 = DailyLog(log_date=date(2026, 11, 6))

        t_done = day1.add_task(title="Tâche finie")
        t_done.mark_done()

        with pytest.raises(InvalidStatusTransitionError, match="Impossible de migrer"):
            day1.migrate_task(t_done.id, day2)

        t_cancelled = day1.add_task(title="Tâche annulée")
        t_cancelled.mark_cancelled()

        with pytest.raises(InvalidStatusTransitionError, match="Impossible de migrer"):
            day1.migrate_task(t_cancelled.id, day2)

    def test_daily_batch_migration_pending_tasks(self) -> None:
        """migrate_pending_tasks migre toutes les tâches non terminées d'un coup."""
        day1 = DailyLog(log_date=date(2026, 11, 5))
        day2 = DailyLog(log_date=date(2026, 11, 6))

        t1 = day1.add_task(title="Tâche 1 à faire")
        t2 = day1.add_task(title="Tâche 2 terminée")
        t3 = day1.add_task(title="Tâche 3 à faire")
        t2.mark_done()

        migrated_list = day1.migrate_pending_tasks(day2)

        assert len(migrated_list) == 2
        assert t1.status == TaskStatus.MIGRATED
        assert t2.status == TaskStatus.DONE
        assert t3.status == TaskStatus.MIGRATED

        assert len(day2.get_pending_tasks()) == 2
        titles_day2 = [t.title for t in day2.get_pending_tasks()]
        assert "Tâche 1 à faire" in titles_day2
        assert "Tâche 3 à faire" in titles_day2

    def test_monthly_task_migration_nominal(self) -> None:
        """Migration d'une tâche d'un mois vers le mois suivant."""
        nov_log = MonthlyLog(year=2026, month=11)
        dec_log = MonthlyLog(year=2026, month=12)

        m_task = nov_log.add_task(title="Projet long terme", signifier="!")
        new_task = nov_log.migrate_task(m_task.id, dec_log)

        assert m_task.status == TaskStatus.MIGRATED
        assert new_task.status == TaskStatus.TO_DO
        assert new_task.title == "Projet long terme"
        assert new_task.signifier == Signifier.IDEA
        assert new_task.migrated_from_id == m_task.id
        assert m_task.migrated_to_id == new_task.id

    def test_bullet_journal_coordination(self) -> None:
        """BulletJournal gère la création automatique et la migration transversale."""
        journal = BulletJournal(owner="Sheryne")
        today = date(2026, 11, 7)
        tomorrow = date(2026, 11, 8)

        t = journal.add_task(title="Préparer le rendu", log_date=today)
        assert t.is_pending is True

        # Migration via la méthode globale du journal
        migrated_task = journal.migrate_task(t.id, target_date=tomorrow)
        assert t.status == TaskStatus.MIGRATED
        assert migrated_task.status == TaskStatus.TO_DO
        assert migrated_task.log_date == tomorrow

        # Recherche de la tâche migrée dans le MonthlyLog
        m_task = journal.add_monthly_task(title="Tâche mensuelle novembre", year=2026, month=11)
        container, entry = journal.find_entry(m_task.id)
        assert isinstance(container, MonthlyLog)
        assert entry.id == m_task.id

        # Migration groupée vers le lendemain
        journal.add_task(title="Autre tâche", log_date=today)
        migrated_batch = journal.migrate_day_to_next(from_date=today)
        assert len(migrated_batch) == 1
