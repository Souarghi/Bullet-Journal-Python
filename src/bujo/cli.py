"""Interface utilisateur en ligne de commande (CLI interactive) pour le Bullet Journal.

Ce fichier permet à un utilisateur de manipuler son carnet en direct dans son terminal :
- Il affiche la liste numérotée des entrées du jour avec les symboles officiels BuJo.
- L'utilisateur n'a pas besoin de copier-coller les longs identifiants UUID :
  il peut simplement taper le numéro affiché `[1]`, `[2]`, etc.
- Toutes les exceptions levées par la bibliothèque (titre vide, transition interdite)
  sont interceptées proprement pour afficher un message clair sans faire crasher le programme.
"""

from __future__ import annotations

from datetime import date, datetime, time
import sys

from bujo.journal import BulletJournal
from bujo.logger import setup_logging
from bujo.models import BujoError, Task


class BujoCLI:
    """Application console interactive pour manipuler un Bullet Journal au quotidien."""

    def __init__(self, owner: str = "Moi") -> None:
        """Initialise le carnet et prépare des exemples de bienvenue."""
        # Initialisation du logging (silencieux sur console pour ne pas polluer le menu)
        setup_logging(console_output=False)
        self.journal = BulletJournal(owner=owner)
        self._seed_example_data()

    def _seed_example_data(self) -> None:
        """Injecte quelques exemples concrets pour que le carnet ne soit pas vide au départ."""
        self.journal.add_task(
            title="Découvrir la méthode Bullet Journal",
            description="Comprendre le rapid logging et les symboles",
        )
        self.journal.add_event(
            title="Point d'avancement de projet",
            event_date=date.today(),
            event_time=time(14, 30),
            location="Salle B204",
        )
        self.journal.add_note(
            title="Principe clé BuJo",
            description="Vivre de manière intentionnelle plutôt que réactive.",
        )

    def display_banner(self) -> None:
        """Affiche une bannière visuelle accueillante en haut de l'écran."""
        today_str = date.today().strftime("%A %d %B %Y")
        print("\n" + "=" * 60)
        print(f"📖 BULLET JOURNAL DE {self.journal.owner.upper()}")
        print(f"🗓️  Date du jour : {today_str}")
        print("=" * 60)

    def display_current_log(self) -> list[str]:
        """Affiche les entrées de la journée avec un numéro [1..N] pour la sélection rapide.

        Returns:
            Liste ordonnée des identifiants réels (UUID), permettant de convertir
            le choix utilisateur `1` en son ID unique `9ba73a81`.
        """
        daily_log = self.journal.today()
        entries = daily_log.entries

        if not entries:
            print("\n  (Aucune entrée dans votre journal aujourd'hui.)")
            print("  Astuce : commencez par ajouter une tâche avec l'option [1] !\n")
            return []

        print("\n--- ENTRÉES DU JOUR ---")
        id_map: list[str] = []
        for index, entry in enumerate(entries, start=1):
            id_map.append(entry.id)
            print(f" [{index}] {entry.display()}")
        print("-" * 60)
        return id_map

    def prompt_add_task(self) -> None:
        """Assistant guidé pour saisir et ajouter une tâche."""
        print("\n📝 NOUVELLE TÂCHE (Symbole •)")
        title = input("Nom de la tâche (obligatoire) : ").strip()
        if not title:
            print("❌ Erreur : le nom de la tâche ne peut pas être vide.")
            return
        description = input("Description ou détails (optionnel) : ").strip()
        category = input("Catégorie / collection (optionnel) : ").strip() or None

        try:
            task = self.journal.add_task(
                title=title,
                description=description,
                category=category,
            )
            print(f"✅ Tâche ajoutée avec succès ! [id: {task.id}]")
        except BujoError as e:
            print(f"❌ Erreur lors de l'ajout : {e}")

    def prompt_add_event(self) -> None:
        """Assistant guidé pour ajouter un rendez-vous ou événement."""
        print("\n🗓️ NOUVEL ÉVÉNEMENT (Symbole ○)")
        title = input("Titre de l'événement (obligatoire) : ").strip()
        if not title:
            print("❌ Le titre ne peut pas être vide.")
            return

        time_input = input("Heure (format HH:MM, optionnel) : ").strip()
        event_time = None
        if time_input:
            try:
                parsed_time = datetime.strptime(time_input, "%H:%M").time()
                event_time = parsed_time
            except ValueError:
                print("⚠️ Format d'heure invalide. L'événement sera créé sans heure.")

        location = input("Lieu (optionnel) : ").strip() or None
        description = input("Précisions (optionnel) : ").strip()

        try:
            event = self.journal.add_event(
                title=title,
                event_time=event_time,
                location=location,
                description=description,
            )
            print(f"✅ Événement ajouté ! [id: {event.id}]")
        except BujoError as e:
            print(f"❌ Erreur : {e}")

    def prompt_add_note(self) -> None:
        """Assistant guidé pour enregistrer une note."""
        print("\n💡 NOUVELLE NOTE (Symbole –)")
        title = input("Titre ou première idée (obligatoire) : ").strip()
        if not title:
            print("❌ Le titre ne peut pas être vide.")
            return
        description = input("Contenu / détails : ").strip()

        try:
            note = self.journal.add_note(title=title, description=description)
            print(f"✅ Note consignée ! [id: {note.id}]")
        except BujoError as e:
            print(f"❌ Erreur : {e}")

    def _resolve_entry_id(self, choice: str, id_map: list[str]) -> str | None:
        """Convertit soit un numéro court [1..N] soit un identifiant brut en ID réel."""
        choice = choice.strip()
        if choice.isdigit():
            idx = int(choice)
            if 1 <= idx <= len(id_map):
                return id_map[idx - 1]
        elif choice in id_map:
            return choice
        return None

    def prompt_complete_task(self, id_map: list[str]) -> None:
        """Assistant guidé pour cocher et terminer une tâche."""
        if not id_map:
            print("Aucune entrée disponible.")
            return

        choice = input("Numéro [1..N] ou ID de la tâche terminée : ").strip()
        entry_id = self._resolve_entry_id(choice, id_map)
        if not entry_id:
            print("❌ Sélection introuvable.")
            return

        try:
            task = self.journal.mark_task_done(entry_id)
            print(f"🎉 Bravo ! Tâche terminée (×) : {task.title}")
        except BujoError as e:
            print(f"❌ Erreur : {e}")

    def prompt_delete_entry(self, id_map: list[str]) -> None:
        """Assistant guidé pour supprimer une entrée."""
        if not id_map:
            print("Aucune entrée à supprimer.")
            return

        choice = input("Numéro [1..N] ou ID de l'entrée à supprimer : ").strip()
        entry_id = self._resolve_entry_id(choice, id_map)
        if not entry_id:
            print("❌ Entrée introuvable.")
            return

        try:
            entry = self.journal.today().remove_entry(entry_id)
            print(f"🗑️ Entrée supprimée : {entry.title}")
        except BujoError as e:
            print(f"❌ Erreur : {e}")

    def prompt_change_task_status(self, id_map: list[str]) -> None:
        """Assistant guidé pour tester les transitions d'état du cycle de vie BuJo."""
        choice = input("Numéro [1..N] ou ID de la tâche : ").strip()
        entry_id = self._resolve_entry_id(choice, id_map)
        if not entry_id:
            print("❌ Sélection introuvable.")
            return

        daily_log = self.journal.today()
        try:
            entry = daily_log.get_entry(entry_id)
            if not isinstance(entry, Task):
                print(f"❌ L'entrée sélectionnée ({type(entry).__name__}) n'est pas une tâche.")
                return

            print(f"\nChangement d'état pour la tâche : {entry.title}")
            print(f"Statut actuel : {entry.status.label} ({entry.symbol})")
            print(" [1] Marquer terminée (×)")
            print(" [2] Marquer migrée (>)")
            print(" [3] Marquer planifiée (<)")
            print(" [4] Marquer abandonnée (~)")
            print(" [5] Réouvrir la tâche (•)")
            action = input("Votre choix : ").strip()

            if action == "1":
                entry.mark_done()
            elif action == "2":
                entry.mark_migrated()
            elif action == "3":
                entry.mark_scheduled()
            elif action == "4":
                entry.mark_cancelled()
            elif action == "5":
                entry.reopen()
            else:
                print("Action annulée.")
                return

            print(f"✅ Nouveau statut : {entry.status.label} ({entry.symbol})")
        except BujoError as e:
            # Si l'utilisateur tente de terminer une tâche abandonnée, il verra ce message !
            print(f"❌ Transition interdite par le BuJo : {e}")

    def run(self) -> None:
        """Boucle principale : affiche le menu et écoute les commandes de l'utilisateur."""
        self.display_banner()
        while True:
            id_map = self.display_current_log()
            print("\n📋 ACTIONS DISPONIBLES :")
            print("  1. Ajouter une tâche (•)")
            print("  2. Ajouter un événement (○)")
            print("  3. Ajouter une note (–)")
            print("  4. Marquer une tâche comme terminée (×)")
            print("  5. Changer le statut d'une tâche (migrer, abandonner...)")
            print("  6. Supprimer une entrée")
            print("  7. Rafraîchir l'affichage")
            print("  0. Quitter le journal")

            choice = input("\n👉 Que voulez-vous faire ? [0-7] : ").strip()

            if choice == "1":
                self.prompt_add_task()
            elif choice == "2":
                self.prompt_add_event()
            elif choice == "3":
                self.prompt_add_note()
            elif choice == "4":
                self.prompt_complete_task(id_map)
            elif choice == "5":
                self.prompt_change_task_status(id_map)
            elif choice == "6":
                self.prompt_delete_entry(id_map)
            elif choice == "7":
                continue
            elif choice == "0":
                print("\n👋 Au revoir et bonne journée dans votre Bullet Journal !\n")
                sys.exit(0)
            else:
                print("⚠️ Choix non reconnu. Veuillez choisir un chiffre entre 0 et 7.")


def main() -> None:
    """Point d'entrée du script exécutable."""
    app = BujoCLI(owner="Étudiant")
    app.run()


if __name__ == "__main__":
    main()
