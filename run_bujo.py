#!/usr/bin/env python3
"""Point d'entrée direct pour lancer le Bullet Journal (GUI Tkinter ou Console CLI).

Utilisation :
    python run_bujo.py          # Lance l'interface graphique Tkinter (par défaut)
    python run_bujo.py --cli    # Lance l'interface interactive en console
"""

import sys

from bujo.cli import main as run_cli


def main() -> None:
    """Lance l'interface appropriée selon les arguments."""
    if "--cli" in sys.argv:
        run_cli()
        return

    try:
        from bujo.gui import launch_gui
        launch_gui()
    except Exception as exc:
        print(f"Impossible de démarrer l'interface graphique ({exc}). Bascule en console...")
        run_cli()


if __name__ == "__main__":
    main()
