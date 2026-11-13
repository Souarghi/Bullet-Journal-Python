# Bullet Journal Python

Une bibliothèque Python et une interface en ligne de commande pour organiser sa journée selon la méthode du Bullet Journal (BuJo). Le projet permet de gérer des tâches et fournit également les bases pour représenter des événements et des notes.

## Fonctionnalités

- Ajouter des tâches au journal du jour.
- Afficher les tâches encore à faire.
- Marquer une tâche comme terminée.
- Utiliser des entrées de journal typées : tâches, événements et notes.
- Consulter les tests automatisés du projet.

> Les entrées sont conservées en mémoire pendant l’exécution du programme. Elles ne sont pas sauvegardées entre deux lancements.

## Prérequis

- Python 3.9 ou une version ultérieure
- `pip`

## Installation

Clonez le dépôt, puis placez-vous dans son répertoire :

```bash
git clone https://github.com/Souarghi/Bullet-Journal-Python.git
cd Bullet-Journal-Python
```

Créez et activez un environnement virtuel (recommandé) :

```bash
python -m venv .venv
```

Sous macOS ou Linux :

```bash
source .venv/bin/activate
```

Sous Windows PowerShell :

```powershell
.venv\Scripts\Activate.ps1
```

Installez les dépendances :

```bash
python -m pip install -r requirements.txt
```

## Lancer l’application

À la racine du dépôt, exécutez :

```bash
python main.py
```

Le menu interactif permet d’ajouter une tâche, de consulter les tâches en cours, d’en terminer une ou de quitter l’application. L’interface utilise [Rich](https://github.com/Textualize/rich) pour afficher les menus et les tableaux dans le terminal.

## Exécuter les tests

```bash
python -m pytest
```

## Structure du projet

```text
.
├── bujo/
│   ├── entries.py      # Entrées, tâches, événements et notes
│   ├── exceptions.py  # Exceptions du domaine
│   ├── journal.py     # Journal quotidien et gestion des entrées
│   └── logger.py      # Configuration des journaux
├── tests/
│   └── test_journal.py
├── main.py             # Interface en ligne de commande
└── requirements.txt
```

## Utilisation de la bibliothèque

Le journal et les tâches peuvent également être utilisés directement depuis Python :

```python
from bujo.entries import Task
from bujo.journal import DailyLog

journal = DailyLog()
tache = Task(name="Réviser Python")
journal.add_entry(tache)

for element in journal.get_pending_tasks():
    print(element.name)

tache.complete()
```

## État du projet

Ce projet est en développement. La branche `Diego-cli` contient l’interface CLI et les fonctionnalités décrites ci-dessus.
