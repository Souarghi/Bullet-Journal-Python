"""Tests unitaires du module bujo.cli (menu en ligne de commande)."""

import os

import pytest

from bujo.cli import (
    DEFAULT_FILE,
    _ask_id,
    _ask_path,
    _ask_signifier,
    clear_screen,
    main,
    show_choice,
    take_choice,
)
from bujo.journal import Journal


def _feed(monkeypatch, answers):
    """Remplace input() par une file de réponses préparées."""
    iterator = iter(answers)
    monkeypatch.setattr("builtins.input", lambda prompt="": next(iterator))


@pytest.fixture
def journal():
    """Journal vide pour piloter le menu."""
    return Journal("Test")


class TestInvites:
    """Tests des petites fonctions d'invite du menu."""

    def test_ask_signifier_vide_est_aucun(self, monkeypatch):
        _feed(monkeypatch, [""])
        assert _ask_signifier() is None

    def test_ask_signifier_valide(self, monkeypatch):
        _feed(monkeypatch, ["*"])
        assert _ask_signifier() == "*"

    def test_ask_path_defaut(self, monkeypatch):
        _feed(monkeypatch, [""])
        assert _ask_path("Chemin") == DEFAULT_FILE

    def test_ask_path_personnalise(self, monkeypatch):
        _feed(monkeypatch, ["/tmp/mon_journal.json"])
        assert _ask_path("Chemin") == "/tmp/mon_journal.json"

    def test_ask_id_par_prefixe(self, journal, monkeypatch):
        task = journal.add_task("Tache")
        _feed(monkeypatch, [task.id[:6]])
        assert _ask_id(journal) == task.id

    def test_ask_id_inconnu_renvoie_la_saisie(self, journal, monkeypatch):
        _feed(monkeypatch, ["inconnu"])
        assert _ask_id(journal) == "inconnu"


class TestMenu:
    """Tests des actions du menu via take_choice."""

    def test_ajouter_une_tache(self, journal, monkeypatch):
        _feed(monkeypatch, ["1", "Courses", "Lait", "!"])
        assert take_choice(journal) is True
        assert len(journal) == 1
        assert journal.open_tasks()[0].signifier == "!"

    def test_ajouter_un_evenement(self, journal, monkeypatch):
        _feed(monkeypatch, ["2", "Reunion", "", "*"])
        take_choice(journal)
        assert str(journal.get_entry(journal.ids()[0]))[:2] == "\u25cb*"

    def test_ajouter_une_note(self, journal, monkeypatch):
        _feed(monkeypatch, ["3", "Idee", "", "!"])
        take_choice(journal)
        assert len(journal) == 1

    def test_signifiant_invalide_affiche_une_erreur(
        self, journal, monkeypatch, capsys
    ):
        _feed(monkeypatch, ["1", "Tache", "", "?"])
        assert take_choice(journal) is True
        assert "Erreur" in capsys.readouterr().out
        assert len(journal) == 0

    @pytest.mark.parametrize(
        ("choix", "attendu"),
        [("4", "\u00d7"), ("5", ">"), ("6", "<"), ("7", "~")],
    )
    def test_transitions_depuis_le_menu(
        self, journal, monkeypatch, choix, attendu
    ):
        task = journal.add_task("Tache")
        _feed(monkeypatch, [choix, task.id[:6]])
        take_choice(journal)
        assert task.symbol == attendu

    def test_supprimer_une_entree(self, journal, monkeypatch):
        task = journal.add_task("A supprimer")
        _feed(monkeypatch, ["8", task.id])
        take_choice(journal)
        assert len(journal) == 0

    def test_afficher_les_taches_en_cours(self, journal, monkeypatch, capsys):
        journal.add_task("Une")
        _feed(monkeypatch, ["9"])
        take_choice(journal)
        assert "Une" in capsys.readouterr().out

    def test_aucune_tache_en_cours(self, journal, monkeypatch, capsys):
        _feed(monkeypatch, ["9"])
        take_choice(journal)
        assert "Aucune tâche en cours." in capsys.readouterr().out

    def test_identifiant_inconnu_affiche_une_erreur(
        self, journal, monkeypatch, capsys
    ):
        _feed(monkeypatch, ["4", "inconnu"])
        assert take_choice(journal) is True
        assert "Erreur" in capsys.readouterr().out

    def test_sauvegarde_puis_chargement(self, journal, monkeypatch, tmp_path):
        chemin = str(tmp_path / "journal.json")
        task = journal.add_task("A conserver")
        _feed(monkeypatch, ["10", chemin, "11", chemin])
        take_choice(journal)
        take_choice(journal)
        assert journal.ids() == [task.id]

    def test_charger_un_fichier_invalide_affiche_une_erreur(
        self, journal, monkeypatch, capsys, tmp_path
    ):
        chemin = str(tmp_path / "casse.json")
        _feed(monkeypatch, ["11", chemin])
        assert take_choice(journal) is True
        assert "Erreur" in capsys.readouterr().out

    def test_choix_inconnu(self, journal, monkeypatch, capsys):
        _feed(monkeypatch, ["abc"])
        assert take_choice(journal) is True
        assert "Choix inconnu" in capsys.readouterr().out

    def test_quitter(self, journal, monkeypatch):
        _feed(monkeypatch, ["12"])
        assert take_choice(journal) is False


class TestEcrans:
    """Tests de l'affichage et du point d'entrée complet."""

    def test_show_choice(self, capsys):
        show_choice()
        assert "Bullet Journal" in capsys.readouterr().out

    def test_clear_screen(self, monkeypatch):
        appelee = []
        monkeypatch.setattr(os, "system", lambda cmd: appelee.append(cmd))
        clear_screen()
        assert appelee == ["clear"] or appelee == ["cls"]

    def test_main_ajoute_puis_quitte(self, monkeypatch, tmp_path, capsys):
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(os, "system", lambda cmd: 0)
        _feed(monkeypatch, ["1", "Tache", "desc", "*", "", "12"])
        main()
        out = capsys.readouterr().out
        assert "Bienvenue" in out
        assert "Tâche ajoutée" in out
        assert (tmp_path / "bujo_debug.log").exists()
