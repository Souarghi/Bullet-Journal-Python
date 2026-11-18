# Bullet-Journal-Python

Ce projet consiste à développer une bibliothèque Python fiable et réutilisable
permettant de gérer l'organisation personnelle selon la méthode du Bullet
Journal (BuJo), créée par Ryder Carroll.

# Le projet

## Architecture du projet

```
Bullet-Journal-PY/
├── bujo/                         # package principal de la bibliothèque
│   ├── __init__.py               # API publique : exports, __version__, recettes d'usage
│   ├── __main__.py               # point d'entrée : python -m bujo
│   ├── entry.py                  # modèle (abstraction, héritage) : Entry, Task, Event,
│   │                             #   Note, TaskState, ALLOWED_TRANSITIONS, SYMBOLS_BY_STATE,
│   │                             #   SIGNIFIERS
│   ├── journal.py                # journal : Journal (entrées indexées par id) + setup_logging
│   ├── persistence.py            # persistance : save_journal / load_journal (format JSON)
│   ├── exceptions.py             # exceptions : BujoError, EntryNotFoundError, EmptyNameError,
│   │                             #   InvalidDateError, InvalidStateTransitionError,
│   │                             #   InvalidSignifierError, PersistenceError
│   └── cli.py                    # affichage / CLI : main(), MENU, show_choice(),
│                                 #   take_choice(), clear_screen()
├── tools/                        # outils de la qualité
│   └── check_docstrings.py       # contrôle CI : docstrings de toute l'API publique
├── tests/                        # tests unitaires pytest
│   ├── test_entry.py             # cycle de vie des tâches, cas d'erreur du modèle
│   ├── test_journal.py           # ajout, suppression, recherche, transitions, entrées du jour
│   ├── test_persistence.py       # aller-retour JSON, états conservés, fichiers invalides
│   └── test_cli.py               # menu complet piloté, invites, point d'entrée main()
├── docs/                         # documentation Sphinx (autodoc des modules)
│   ├── conf.py                   # configuration Sphinx (autodoc, napoleon, langue fr)
│   ├── index.rst                 # page d'accueil : autodoc de tous les modules
│   ├── _static/                  # ressources statiques (répertoire réservé)
│   ├── _templates/               # templates de thèmes (répertoire réservé)
│   └── _build/                   # HTML généré (ignoré par Git)
├── .github/workflows/ci.yml      # pipeline GitHub Actions : PEP 8, docstrings,
│                                 #   tests + couverture > 90 %
├── setup.cfg                     # configuration de flake8 et pytest
├── Dockerfile                    # image Docker de l'application
├── requirements.txt              # dépendances (tests, lint, couverture, docs)
└── .gitignore                    # caches, logs, documentation générée, docx hors dépôt
```

Les modules attendus par le cahier des charges sont ainsi répartis : modèle
(`entry.py`), journal (`journal.py`), affichage (`cli.py`), exceptions
(`exceptions.py`), persistance (`persistence.py`). La persistance écrit le
journal complet dans un fichier JSON (par défaut `journal.json`) et le
recharge à l'identique : identifiants, états, signifiants, dates et heures.

## Exceptions

Toutes les erreurs de la bibliothèque héritent de `BujoError`, classe
marqueur sans corps (`pass`) : ce qui compte est le **type** levé, pas le
code. Un `except BujoError` capture ainsi toute la bibliothèque sans
avaler les erreurs Python tierces (`ValueError`, `TypeError`…).

| Exception | Levée quand… |
|---|---|
| `EntryNotFoundError` | l'identifiant ne correspond à aucune entrée |
| `EmptyNameError` | le nom d'une entrée est vide |
| `InvalidDateError` | la date ou l'heure fournie est invalide |
| `InvalidStateTransitionError` | la transition d'état d'une tâche est interdite |
| `InvalidSignifierError` | le signifiant n'est pas `*` ou `!` |
| `PersistenceError` | le fichier JSON du journal n'a pu être lu ou écrit |

```python
from bujo import Journal, BujoError, EntryNotFoundError

try:
    journal.complete_task("abc123")
except EntryNotFoundError:
    print("Entrée inconnue.")
except BujoError as exc:
    print(f"Erreur du journal : {exc}")
```

# Lancer l'application

## Installation et utilisation

Le projet s'utilise avec Docker (l'image `python:3.12-slim` fournit Python
et les dépendances de `requirements.txt`) :

```bash
docker build -t bujo .
docker run --rm -it bujo
```

Le menu permet d'ajouter une tâche, un événement ou une note (avec un
signifiant facultatif `*` ou `!`), de marquer une tâche comme terminée,
migrée, planifiée ou abandonnée, de supprimer une entrée, d'afficher les
tâches en cours, et de sauvegarder / charger le journal dans un fichier
JSON. Les identifiants (uuid) peuvent être saisis partiellement (préfixe).

### Symboles du rapid logging (utilisés par l'affichage CLI)

| Symbole | Signification |
|---|---|
| • | Tâche à faire |
| × | Tâche terminée |
| > | Tâche migrée (reportée à un autre jour ou mois) |
| < | Tâche planifiée dans le Future Log |
| ~~tâche~~ | Tâche abandonnée, devenue sans objet |
| ○ | Événement |
| – | Note |
| * | Signifiant : priorité |
| ! | Signifiant : idée, inspiration |

Les symboles d'état et de type sont portés par `entry.symbol` et rendus
par `print(entry)`. Les signifiants sont portés par `entry.signifier`
(validés par `SIGNIFIERS`, sinon `InvalidSignifierError`) et s'affichent
collés après le symbole (`•* Ranger le bureau`) ; le menu les demande à
la création de chaque entrée. Une tâche abandonnée s'affiche barrée :
`~ ~~Ranger le bureau~~`.

### En bibliothèque

```python
from datetime import time

from bujo import Event, Journal, Note, load_journal, save_journal

journal = Journal("Mon journal")
task = journal.add_task("Ranger le bureau", "Trier les papiers",
                        signifier="*")
journal.add_entry(Event("Réunion", at=time(10, 30)))
journal.add_entry(Note("Idée de projet"))
journal.complete_task(task.id)
print(*journal.open_tasks(), sep="\n")

save_journal(journal, "journal.json")
journal = load_journal("journal.json")
```

### Journalisation (logging)

Chaque exécution alimente deux fichiers de log créés dans le répertoire
courant (livrés avec le dépôt comme exemples de sortie) :

- `bujo_debug.log` : toutes les actions (DEBUG et plus)
- `bujo_error.log` : uniquement les erreurs (ERROR et CRITICAL)

# Qualité : tests, documentation et CI/CD

## Tests

```bash
docker run --rm bujo python -m pytest -v
docker run --rm bujo python -m coverage run -m pytest
docker run --rm bujo python -m coverage report --show-missing
```

Les tests unitaires (`tests/test_entry.py`, `tests/test_journal.py`,
`tests/test_persistence.py`, `tests/test_cli.py`) couvrent le modèle des
entrées, le journal, la persistance et le menu : cycle de vie des tâches,
signifiants, transitions interdites, aller-retour JSON, cas d'erreur,
recherche par nom. La couverture est mesurée par `coverage` et imposée
par le pipeline CI (`--fail-under=90`) : 102 tests, 99 % de couverture.

La présence des docstrings sur les modules, classes et fonctions publiques
de `bujo/` est vérifiée par `tools/check_docstrings.py` :

```bash
python tools/check_docstrings.py bujo
```

## Documentation

Générer la documentation HTML avec Sphinx (autodoc de tous les modules) :

```bash
docker run --rm -v "$PWD":/app bujo \
  sphinx-build -b html docs docs/_build/html
```

Puis ouvrir `docs/_build/html/index.html`.

## CI/CD

Le pipeline **GitHub Actions** (`.github/workflows/ci.yml`, exécuté à
chaque push et chaque pull request) vérifie :

1. le respect de PEP 8 (`flake8`) ;
2. la présence des docstrings sur toute l'API publique
   (`tools/check_docstrings.py`) ;
3. l'exécution de tous les tests unitaires sous `coverage`, avec un
   seuil minimal de 90 % (`--fail-under=90`).

La configuration des outils (flake8, pytest) est centralisée dans
`setup.cfg`.

# État d'avancement

## Statut — Niveau 1

- ✅ Ajouter une tâche (nom + description) dans le journal du jour
- ✅ Marquer une tâche comme terminée
- ✅ Supprimer une entrée
- ✅ Afficher les tâches en cours (symboles du rapid logging)
- ✅ Cycle de vie : à faire, terminée, migrée, planifiée, abandonnée
- ✅ Signifiants rapid logging : * priorité, ! idée (bibliothèque et menu)
- ✅ Trois types d'entrées : tâches, événements (date/heure), notes
- ✅ Identifiant unique par entrée, recherche par nom secondaire
- ✅ POO : classe abstraite `Entry`, héritage, encapsulation
- ✅ Type hinting, PEP 8, docstrings sur les modules, classes et méthodes
- ✅ Exceptions personnalisées héritant de `BujoError` (entrée introuvable,
  nom vide, date invalide, transition d'état interdite, signifiant inconnu,
  erreur de persistance)
- ✅ Logs debug + erreurs dédiés
- ✅ Persistance JSON : sauvegarde et chargement à l'identique
- ✅ Transitions complètes dans le menu : terminer, migrer, planifier, abandonner
- ✅ Tests pytest (cycle de vie, cas d'erreur, persistance) et couverture
  (99 %) imposée par la CI à chaque push
- ✅ Documentation Sphinx
- ✅ Pipeline CI GitHub Actions à chaque push (PEP 8, docstrings, tests)
- ✅ Environnement reproductible (Docker + requirements.txt)

## Perspective d'amélioration

Toutes les fonctionnalités du niveau 1 et les exigences techniques sont
livrées (voir le statut ci-dessus). Il reste :

### Exigences techniques
1. Étendre le workflow Git avec **branches et Pull Requests** pour le
   travail en équipe (les commits explicites et la CI à chaque push sont
   déjà en place)

### Livrable :
Dépôt **GitHub public** du projet (code source, documentation Sphinx,
fichiers de logs, tests unitaires, pipeline CI/CD GitHub Actions), dont
le lien est envoyé au formateur.
