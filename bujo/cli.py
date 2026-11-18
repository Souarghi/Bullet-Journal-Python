"""Menu en ligne de commande de la bibliothèque Bullet Journal."""

from __future__ import annotations

import logging
import os

from bujo.entry import Note, Event
from bujo.exceptions import BujoError
from bujo.journal import Journal, setup_logging
from bujo.persistence import load_journal, save_journal

MENU = """
===== Bullet Journal =====
1. Ajouter une tâche
2. Ajouter un événement
3. Ajouter une note
4. Marquer une tâche comme terminée
5. Migrer une tâche (la reporter)
6. Planifier une tâche dans le Future Log
7. Abandonner une tâche
8. Supprimer une entrée
9. Afficher les tâches en cours
10. Sauvegarder le journal
11. Charger le journal
12. Quitter
"""

DEFAULT_FILE = "journal.json"


def clear_screen() -> None:
    """Vide le terminal."""
    os.system("cls" if os.name == "nt" else "clear")


def show_choice() -> None:
    """Affiche le menu des actions possibles."""
    print(MENU)


def take_choice(journal: Journal) -> bool:
    """Lit le choix de l'utilisateur et exécute l'action associée.

    Retourne False pour quitter le programme, True sinon.
    """
    choice = input("Votre choix : ").strip()
    try:
        if choice == "1":
            name = input("Nom de la tâche : ")
            description = input("Description : ")
            task = journal.add_task(name, description,
                                    signifier=_ask_signifier())
            print(f"Tâche ajoutée (id {task.id[:8]}…).")
        elif choice == "2":
            name = input("Nom de l'événement : ")
            event = Event(name, input("Description : "),
                          signifier=_ask_signifier())
            journal.add_entry(event)
            print(f"Événement ajouté (id {event.id[:8]}…).")
        elif choice == "3":
            name = input("Nom de la note : ")
            note = Note(name, input("Description : "),
                        signifier=_ask_signifier())
            journal.add_entry(note)
            print(f"Note ajoutée (id {note.id[:8]}…).")
        elif choice == "4":
            entry_id = _ask_id(journal)
            task = journal.complete_task(entry_id)
            print(f"Tâche terminée : {task}.")
        elif choice == "5":
            entry_id = _ask_id(journal)
            task = journal.migrate_task(entry_id)
            print(f"Tâche migrée : {task}.")
        elif choice == "6":
            entry_id = _ask_id(journal)
            task = journal.plan_task(entry_id)
            print(f"Tâche planifiée : {task}.")
        elif choice == "7":
            entry_id = _ask_id(journal)
            task = journal.discard_task(entry_id)
            print(f"Tâche abandonnée : {task}.")
        elif choice == "8":
            entry_id = _ask_id(journal)
            entry = journal.remove_entry(entry_id)
            print(f"Entrée supprimée : {entry}.")
        elif choice == "9":
            tasks = journal.open_tasks()
            if not tasks:
                print("Aucune tâche en cours.")
            for task in tasks:
                print(f"[{task.id[:8]}] {task}")
        elif choice == "10":
            path = _ask_path("Chemin de sauvegarde")
            save_journal(journal, path)
            print(f"Journal sauvegardé dans {path}.")
        elif choice == "11":
            path = _ask_path("Chemin du journal à charger")
            _reload_into(journal, load_journal(path))
            print(f"Journal « {journal.name} » chargé depuis {path} "
                  f"({len(journal)} entrées).")
        elif choice == "12":
            return False
        else:
            print("Choix inconnu, réessayez.")
    except BujoError as error:
        print(f"Erreur : {error}")
    return True


def _ask_path(label: str) -> str:
    """Demande un chemin de fichier, journal.json par défaut."""
    raw = input(f"{label} [{DEFAULT_FILE}] : ").strip()
    return raw or DEFAULT_FILE


def _reload_into(journal: Journal, loaded: Journal) -> None:
    """Remplace le contenu de journal par celui du journal chargé."""
    for entry_id in journal.ids():
        journal.remove_entry(entry_id)
    for entry_id in loaded.ids():
        journal.add_entry(loaded.get_entry(entry_id))
    journal.name = loaded.name


def _ask_signifier() -> str | None:
    """Demande un signifiant facultatif (* ou !) et le retourne.

    Une réponse vide signifie « aucun signifiant ».
    """
    raw = input(
        "Signifiant (* priorité, ! idée, Entrée = aucun) : "
    ).strip()
    return raw or None


def _ask_id(journal: Journal) -> str:
    """Demande un identifiant (début ou entier) et le résout."""
    raw = input("Identifiant de l'entrée : ").strip()
    for entry_id in journal.ids():
        if entry_id == raw or entry_id.startswith(raw):
            return entry_id
    return raw


def main() -> None:
    """Point d'entrée : initialise les logs puis lance la boucle du menu."""
    setup_logging()
    logger = logging.getLogger("bujo")
    logger.info("Démarrage du Bullet Journal.")
    journal = Journal()
    print("Bienvenue dans votre Bullet Journal !")
    running = True
    while running:
        show_choice()
        running = take_choice(journal)
        if running:
            input("Appuyez sur Entrée pour revenir au menu…")
            clear_screen()
    logger.info("Fin du programme.")


if __name__ == "__main__":
    main()
