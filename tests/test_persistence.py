"""Tests unitaires du module bujo.persistence (sauvegarde et chargement)."""

import json
from datetime import date, time

import pytest

from bujo.entry import Event, Note, TaskState
from bujo.exceptions import PersistenceError
from bujo.journal import Journal
from bujo.persistence import _kind_of, load_journal, save_journal


@pytest.fixture
def chemin(tmp_path):
    """Chemin d'un fichier JSON temporaire."""
    return str(tmp_path / "journal.json")


class TestSauvegarde:
    """Tests de l'écriture et de la relecture du journal."""

    def test_aller_retour_complet(self, chemin):
        journal = Journal("Mon journal")
        journal.add_task("Courses", "Lait", signifier="*")
        journal.add_entry(Event("Reunion", at=time(10, 30)))
        journal.add_entry(Note("Pensee"))
        save_journal(journal, chemin)
        relu = load_journal(chemin)
        assert relu.name == journal.name
        assert len(relu) == 3
        assert [str(relu.get_entry(i)) for i in relu.ids()] == [
            str(journal.get_entry(i)) for i in journal.ids()
        ]

    def test_identifiants_conservés(self, chemin):
        journal = Journal()
        task = journal.add_task("Tache")
        save_journal(journal, chemin)
        assert load_journal(chemin).ids() == [task.id]

    @pytest.mark.parametrize(
        ("action", "attendu"),
        [
            ("complete", TaskState.DONE),
            ("migrate", TaskState.MIGRATED),
            ("plan", TaskState.PLANNED),
            ("discard", TaskState.DISCARDED),
        ],
    )
    def test_etats_conservés(self, chemin, action, attendu):
        journal = Journal()
        getattr(journal.add_task("Tache"), action)()
        save_journal(journal, chemin)
        relu = load_journal(chemin)
        assert relu.get_entry(journal.ids()[0]).state is attendu

    def test_heure_evenement_conservée(self, chemin):
        journal = Journal()
        event = Event("Reunion", at=time(8, 15))
        journal.add_entry(event)
        save_journal(journal, chemin)
        relu = load_journal(chemin)
        assert relu.get_entry(event.id).at == time(8, 15)

    def test_date_de_log_conservée(self, chemin):
        journal = Journal()
        task = journal.add_task("Voyage", log_date=date(2026, 12, 16))
        save_journal(journal, chemin)
        relu = load_journal(chemin)
        assert relu.get_entry(task.id).log_date == date(2026, 12, 16)

    def test_signifiants_conservés(self, chemin):
        journal = Journal()
        task = journal.add_task("Urgent", signifier="*")
        note = Note("Idee", signifier="!")
        journal.add_entry(note)
        save_journal(journal, chemin)
        relu = load_journal(chemin)
        assert relu.get_entry(task.id).signifier == "*"
        assert relu.get_entry(note.id).signifier == "!"


class TestChargementInvalide:
    """Tests des fichiers absents, illisibles ou corrompus."""

    def test_fichier_inexistant(self, chemin):
        with pytest.raises(PersistenceError):
            load_journal(chemin)

    def test_fichier_non_json(self, chemin):
        with open(chemin, "w", encoding="utf-8") as handle:
            handle.write("ceci n'est pas du json")
        with pytest.raises(PersistenceError):
            load_journal(chemin)

    def test_version_non_geree(self, chemin):
        with open(chemin, "w", encoding="utf-8") as handle:
            json.dump({"version": 99, "entries": []}, handle)
        with pytest.raises(PersistenceError):
            load_journal(chemin)

    def test_fichier_non_dict(self, chemin):
        with open(chemin, "w", encoding="utf-8") as handle:
            json.dump(["pas", "un", "dictionnaire"], handle)
        with pytest.raises(PersistenceError):
            load_journal(chemin)

    def test_type_d_entree_inconnu(self, chemin):
        with open(chemin, "w", encoding="utf-8") as handle:
            json.dump(
                {
                    "version": 1,
                    "entries": [
                        {
                            "type": "carnet",
                            "id": "abc",
                            "name": "X",
                            "log_date": "2026-11-18",
                        }
                    ],
                },
                handle,
            )
        with pytest.raises(PersistenceError):
            load_journal(chemin)

    def test_entree_sans_identifiant(self, chemin):
        with open(chemin, "w", encoding="utf-8") as handle:
            json.dump(
                {
                    "version": 1,
                    "entries": [
                        {"type": "note", "name": "X",
                         "log_date": "2026-11-18"},
                    ],
                },
                handle,
            )
        with pytest.raises(PersistenceError):
            load_journal(chemin)


class TestSauvegardeImpossible:
    """Tests des erreurs d'écriture."""

    def test_ecriture_dans_un_repertoire_absent(self):
        journal = Journal()
        journal.add_task("Tache")
        with pytest.raises(PersistenceError):
            save_journal(journal, "/absent/du/disque/journal.json")

    def test_refuser_un_objet_non_persistable(self):
        with pytest.raises(PersistenceError):
            _kind_of(object())
