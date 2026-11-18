"""Tests unitaires du module bujo.entry (entrées et cycle de vie)."""

from datetime import date, datetime, time

import pytest

from bujo.entry import Event, Note, SIGNIFIERS, Task, TaskState
from bujo.exceptions import (
    EmptyNameError,
    InvalidDateError,
    InvalidSignifierError,
    InvalidStateTransitionError,
)


class TestEntry:
    """Tests de la classe de base et de l'identifiant unique."""

    def test_id_unique_meme_nom(self):
        t1 = Task("Appeler le medecin")
        t2 = Task("Appeler le medecin")
        assert t1.id != t2.id

    def test_id_immuable(self):
        task = Task("Tache")
        with pytest.raises(AttributeError):
            task.id = "autre"

    @pytest.mark.parametrize("nom", ["", "   ", None, 42])
    def test_nom_invalide(self, nom):
        with pytest.raises(EmptyNameError):
            Task(nom)

    def test_nom_nettoye(self):
        assert Task("  Tache  ").name == "Tache"

    def test_nom_modifier_par_setter(self):
        task = Task("Ancien")
        task.name = "Nouveau"
        assert task.name == "Nouveau"

    def test_dates_par_defaut(self):
        task = Task("Tache")
        assert task.log_date == date.today()
        assert isinstance(task.created_at, datetime)

    def test_log_date_invalide(self):
        with pytest.raises(InvalidDateError):
            Task("Tache", log_date="2026-12-16")

    def test_log_date_setter_invalide(self):
        task = Task("Tache")
        with pytest.raises(InvalidDateError):
            task.log_date = datetime.now()


class TestTaskCycle:
    """Tests du cycle de vie d'une tache."""

    def test_etat_initial(self):
        task = Task("Tache")
        assert task.state is TaskState.TODO
        assert task.symbol == "•"

    def test_complete(self):
        task = Task("Tache")
        task.complete()
        assert task.state is TaskState.DONE
        assert task.symbol == "×"

    def test_complete_deux_fois_interdit(self):
        task = Task("Tache")
        task.complete()
        with pytest.raises(InvalidStateTransitionError):
            task.complete()

    def test_abandonnee_puis_terminee_interdit(self):
        task = Task("Tache")
        task.discard()
        with pytest.raises(InvalidStateTransitionError):
            task.complete()

    @pytest.mark.parametrize(
        ("action", "attendu"),
        [
            ("migrate", TaskState.MIGRATED),
            ("plan", TaskState.PLANNED),
            ("discard", TaskState.DISCARDED),
        ],
    )
    def test_transitions_depuis_todo(self, action, attendu):
        task = Task("Tache")
        getattr(task, action)()
        assert task.state is attendu


class TestEventNote:
    """Tests des evenements et des notes."""

    def test_evenement_avec_heure(self):
        event = Event("Rendez-vous", at=time(14, 30))
        assert event.symbol == "○"
        assert event.at == time(14, 30)

    def test_evenement_sans_heure(self):
        assert Event("Sortie").at is None

    def test_heure_invalide(self):
        with pytest.raises(InvalidDateError):
            Event("Sortie", at="14h30")

    def test_note(self):
        note = Note("Pensee")
        assert note.symbol == "–"
        assert str(note) == "– Pensee"

    def test_note_n_a_pas_d_etat(self):
        assert not hasattr(Note("Pensee"), "complete")


class TestSignifiants:
    """Tests des signifiants de priorite et d'idee."""

    def test_signifiants_connus(self):
        assert set(SIGNIFIERS) == {"*", "!"}

    def test_signifiant_par_defaut_aucun(self):
        assert Task("Tache").signifier is None

    @pytest.mark.parametrize("signe", ["*", "!"])
    def test_signifiant_valide(self, signe):
        assert Task("Tache", signifier=signe).signifier == signe

    @pytest.mark.parametrize("signe", ["?", "", "!!", 42])
    def test_signifiant_invalide(self, signe):
        with pytest.raises(InvalidSignifierError):
            Task("Tache", signifier=signe)

    def test_signifiant_sur_note_et_evenement(self):
        assert Note("Idee", signifier="!").signifier == "!"
        assert Event("Reunion", signifier="*").signifier == "*"

    def test_str_affiche_signifiant_apres_symbole(self):
        assert str(Note("Idee", signifier="!")) == "\u2013! Idee"
        assert str(Task("Urgent", signifier="*")) == "\u2022* Urgent"

    def test_str_tache_abandonnee_est_barree(self):
        task = Task("Sans objet")
        task.discard()
        assert str(task) == "~ ~~Sans objet~~"
