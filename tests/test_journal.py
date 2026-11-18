"""Tests unitaires du module bujo.journal (journal et recherche)."""

from datetime import date

import pytest

from bujo.entry import Event, Note, TaskState
from bujo.exceptions import (
    EntryNotFoundError,
    InvalidStateTransitionError,
)
from bujo.journal import Journal


@pytest.fixture
def journal():
    """Journal vide pour les tests."""
    return Journal("Test")


class TestJournal:
    """Tests d'ajout, de lecture et de suppression d'entrées."""

    def test_ajout_et_lecture(self, journal):
        task = journal.add_task("Courses", "Lait et pain")
        assert len(journal) == 1
        assert journal.get_entry(task.id) is task

    def test_entree_introuvable(self, journal):
        with pytest.raises(EntryNotFoundError):
            journal.get_entry("inconnu")

    def test_suppression(self, journal):
        task = journal.add_task("A supprimer")
        journal.remove_entry(task.id)
        assert len(journal) == 0
        with pytest.raises(EntryNotFoundError):
            journal.get_entry(task.id)

    def test_suppression_inconnue(self, journal):
        with pytest.raises(EntryNotFoundError):
            journal.remove_entry("inconnu")

    def test_deux_taches_meme_nom_coexistent(self, journal):
        t1 = journal.add_task("Appeler le medecin")
        t2 = journal.add_task("Appeler le medecin")
        assert t1.id != t2.id
        assert len(journal) == 2

    def test_terminer_une_note_est_interdit(self, journal):
        note = Note("Pensee")
        journal.add_entry(note)
        with pytest.raises(InvalidStateTransitionError):
            journal.complete_task(note.id)

    def test_complete_task_via_journal(self, journal):
        task = journal.add_task("Tache")
        journal.complete_task(task.id)
        assert task.state is TaskState.DONE

    def test_add_task_avec_signifiant(self, journal):
        task = journal.add_task("Urgent", signifier="*")
        assert task.signifier == "*"
        assert str(task) == "\u2022* Urgent"


class TestTransitionsViaJournal:
    """Tests des changements d'etat demandes depuis le journal."""

    @pytest.mark.parametrize(
        ("methode", "attendu", "symbole"),
        [
            ("migrate_task", TaskState.MIGRATED, ">"),
            ("plan_task", TaskState.PLANNED, "<"),
            ("discard_task", TaskState.DISCARDED, "~"),
        ],
    )
    def test_transition_depuis_le_journal(self, journal, methode, attendu,
                                          symbole):
        task = journal.add_task("Tache")
        result = getattr(journal, methode)(task.id)
        assert result is task
        assert task.state is attendu
        assert task.symbol == symbole

    @pytest.mark.parametrize(
        "methode",
        ["complete_task", "migrate_task", "plan_task", "discard_task"],
    )
    def test_transition_interdite_sur_une_note(self, journal, methode):
        note = Note("Pensee")
        journal.add_entry(note)
        with pytest.raises(InvalidStateTransitionError):
            getattr(journal, methode)(note.id)

    def test_transition_sur_entree_inconnue(self, journal):
        with pytest.raises(EntryNotFoundError):
            journal.migrate_task("inconnu")

    def test_taches_transitionnees_quittent_en_cours(self, journal):
        t1 = journal.add_task("Une")
        t2 = journal.add_task("Deux")
        journal.migrate_task(t1.id)
        journal.discard_task(t2.id)
        assert journal.open_tasks() == []


class TestRecherche:
    """Tests des listes et de la recherche secondaire par nom."""

    def test_taches_en_cours(self, journal):
        faite = journal.add_task("Faite")
        journal.add_task("En cours")
        journal.complete_task(faite.id)
        en_cours = journal.open_tasks()
        assert [t.name for t in en_cours] == ["En cours"]

    def test_les_notes_ne_sont_pas_des_taches(self, journal):
        journal.add_entry(Note("Pensee"))
        assert journal.open_tasks() == []

    def test_recherche_par_mot_cle_insensible(self, journal):
        journal.add_task("Appeler le MEDECIN")
        journal.add_task("Rendez-vous medecin")
        journal.add_task("Courses")
        resultats = journal.search_by_name("medecin")
        assert len(resultats) == 2

    def test_recherche_retourne_une_liste(self, journal):
        assert journal.search_by_name("absent") == []

    def test_entrées_du_jour(self, journal):
        jour = date(2026, 12, 16)
        journal.add_task("Tache du jour", log_date=jour)
        journal.add_entry(Event("Event d'hier",
                                log_date=date(2026, 12, 15)))
        du_jour = journal.entries_of_day(jour)
        assert [e.name for e in du_jour] == ["Tache du jour"]

    def test_entrées_du_jour_jour_invalide(self, journal):
        with pytest.raises(TypeError):
            journal.entries_of_day("2026-12-16")

    def test_types_d_entrees_mixtes(self, journal):
        journal.add_task("T")
        journal.add_entry(Event("E"))
        journal.add_entry(Note("N"))
        symboles = {journal.get_entry(i).symbol for i in journal.ids()}
        assert symboles == {"•", "○", "–"}


class TestObjetsInvalides:
    """Tests des gardes de type à l'ajout."""

    def test_refuser_un_objet_non_entree(self, journal):
        with pytest.raises(TypeError):
            journal.add_entry("pas une entree")

    def test_refuser_tache_deja_terminee_comme_en_cours(self, journal):
        t = journal.add_task("F")
        t.complete()
        assert journal.open_tasks() == []
