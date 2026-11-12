import sys
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, IntPrompt
from rich.table import Table

from bujo.entries import Task
from bujo.journal import DailyLog

console = Console()


def attendre_et_nettoyer():
    """Met le programme en pause pour laisser le temps de lire, puis nettoie l'écran."""
    console.print("\n[dim italic]Appuie sur Entrée pour retourner au menu...[/dim italic]")
    input()  # Attend que l'utilisateur appuie sur Entrée
    console.clear()


def afficher_menu():
    """Affiche le menu principal stylisé."""
    menu_table = Table(show_header=False, box=None)
    menu_table.add_column("Option", style="bold cyan")
    menu_table.add_column("Action", style="white")

    menu_table.add_row("[1]", "Ajouter une nouvelle tâche")
    menu_table.add_row("[2]", "Voir les tâches en cours")
    menu_table.add_row("[3]", "Terminer une tâche")
    menu_table.add_row("[4]", "[red]Quitter[/red]")

    panel = Panel(
        menu_table,
        title="[bold magenta]⚡ BULLET JOURNAL CLI ⚡[/bold magenta]",
        expand=False,
        border_style="magenta"
    )
    console.print(panel)


def main():
    journal = DailyLog()

    # Nettoyage initial au lancement
    console.clear()

    while True:
        # On affiche le message de bienvenue à chaque rafraîchissement du menu
        console.print(Panel("[bold cyan]Bienvenue dans ton environnement de productivité.[/bold cyan]", expand=False))
        afficher_menu()

        choix = Prompt.ask("[bold yellow]❯ Choisis une action[/bold yellow]", choices=["1", "2", "3", "4"])

        if choix == "1":
            console.print("\n")
            nom_tache = Prompt.ask("[bold green]❯ Nom de la tâche[/bold green]")
            nouvelle_tache = Task(name=nom_tache)
            journal.add_entry(nouvelle_tache)
            console.print(f"[green]✔ Tâche '{nom_tache}' ajoutée avec succès ![/green]")

            # On met en pause avant de clear l'écran
            attendre_et_nettoyer()

        elif choix == "2":
            console.print("\n")
            taches = journal.get_pending_tasks()
            if not taches:
                console.print(
                    Panel("[italic green]🎉 Aucune tâche en cours. Tu es à jour ![/italic green]", expand=False))
            else:
                table = Table(title="[bold cyan]Tâches du jour[/bold cyan]", border_style="cyan")
                table.add_column("N°", justify="right", style="cyan", no_wrap=True)
                table.add_column("Statut", justify="center")
                table.add_column("Description", style="bold white")

                for i, tache in enumerate(taches, 1):
                    table.add_row(str(i), "[red]TODO[/red]", tache.name)

                console.print(table)

            attendre_et_nettoyer()

        elif choix == "3":
            console.print("\n")
            taches = journal.get_pending_tasks()
            if not taches:
                console.print("[yellow]⚠ Aucune tâche à terminer pour le moment.[/yellow]")
                attendre_et_nettoyer()
                continue

            for i, tache in enumerate(taches, 1):
                console.print(f"[cyan]{i}.[/cyan] {tache.name}")

            console.print()
            index = IntPrompt.ask("[bold green]❯ Numéro de la tâche à terminer[/bold green]") - 1

            if 0 <= index < len(taches):
                tache_choisie = taches[index]
                tache_choisie.complete()
                console.print(
                    f"[bold green]✔ Bravo ! '{tache_choisie.name}' est maintenant marquée comme terminée.[/bold green]")
            else:
                console.print("[bold red]❌ Numéro invalide, cette tâche n'existe pas.[/bold red]")

            attendre_et_nettoyer()

        elif choix == "4":
            console.print("\n[bold magenta]Fermeture du terminal. À bientôt ![/bold magenta]\n")
            sys.exit(0)


if __name__ == "__main__":
    main()