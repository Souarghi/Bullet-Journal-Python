# Bullet Journal Python (BuJo)

Bibliothèque Python modulaire, testée et documentée implémentant la méthode du **Bullet Journal (BuJo)** créée par Ryder Carroll.

Ce projet répond aux exigences du **Niveau 1 (Le socle)** dans une architecture **compacte et épurée** : un minimum de fichiers, un maximum de lisibilité.

> 📖 **Pour une explication approfondie de l'architecture, des choix de conception et du guide de soutenance**, consultez le fichier [DOCUMENTATION.md](DOCUMENTATION.md).

---

## Sommaire

1. [Fonctionnalités (Niveau 1)](#fonctionnalités-niveau-1)
2. [Structure du Projet Épurée](#structure-du-projet-épurée)
3. [Installation & Environnement](#installation--environnement)
4. [Guide d'Utilisation](#guide-dutilisation)
5. [Tests Unitaires](#tests-unitaires)
6. [Qualité du Code (PEP 8) & Logs](#qualité-du-code-pep-8--logs)
7. [Intégration Continue (CI)](#intégration-continue-ci)

---

## Fonctionnalités (Niveau 1)

- **Gestion des 3 types d'entrées** :
  - **Tâches (`Task`)** : intitulé, description, date, statut et historique de transition.
  - **Événements (`Event`)** : date, heure optionnelle et localisation.
  - **Notes (`Note`)** : réflexions et faits consignés.
- **Identifiants uniques** : Chaque entrée possède un identifiant unique indépendant de son titre, évitant toute collision lors de tâches homonymes ou répétées.
- **Cycle de vie strict d'une tâche** :
  - États : `À faire` (`•`), `Terminée` (`×`), `Migrée` (`>`), `Planifiée` (`<`), `Abandonnée` (`~`).
  - Contrôle des transitions d'état interdites (ex: interdiction de terminer une tâche abandonnée).
- **Opérations sur le journal du jour (`DailyLog`)** :
  - Ajouter une tâche avec nom et description.
  - Marquer une tâche comme terminée.
  - Supprimer une tâche.
  - Afficher la liste des tâches en cours.
- **Système de journalisation (Logging)** :
  - `logs/debug.log` : traçabilité complète de l'application (DEBUG et supérieur).
  - `logs/errors.log` : enregistrement ciblé des anomalies et erreurs (ERROR et CRITICAL).
- **Exceptions personnalisées** : `BujoError`, `ValidationError`, `EntryNotFoundError`, `InvalidStatusTransitionError`.

---

## Structure du Projet Épurée

Le projet a été concentré sur **5 fichiers de code source** et **1 seul fichier de tests**, sans sous-dossiers inutiles :

```text
Bullet-Journal-Python/
├── src/bujo/
│   ├── __init__.py      # Point d'entrée de la bibliothèque
│   ├── models.py        # Modèles (Entry, Task, Event, Note) + Exceptions métier
│   ├── journal.py       # Organisation temporelle (DailyLog et BulletJournal)
│   ├── logger.py        # Configuration des fichiers debug.log et errors.log
│   └── cli.py           # Interface interactive pour manipuler le carnet
├── tests/
│   ├── __init__.py
│   └── test_bujo.py     # TOUS les 34 tests unitaires dans un seul fichier
├── run_bujo.py          # Script exécutable direct pour lancer et tester le carnet
├── pyproject.toml       # Configuration du packaging et des outils
├── requirements.txt     # Dépendances du projet (pytest, flake8, pydocstyle)
├── .flake8              # Configuration linter PEP 8
├── .gitignore
├── .github/workflows/
│   └── ci.yml           # Pipeline GitHub Actions (PEP 8, docstrings, pytest)
└── README.md
```

---

## Installation & Environnement

Le projet s'appuie sur la chaîne d'outils standard et officielle de Python :
- **`venv`** : Crée un environnement virtuel isolé (`.venv/`) afin que les bibliothèques installées ne polluent pas votre système d'exploitation et n'entrent pas en conflit avec d'autres projets.
- **`pip`** : Gestionnaire de paquets officiel qui télécharge et installe les outils depuis PyPI.
- **`pyproject.toml`** : Standard moderne (PEP 517 / 621) déclarant les métadonnées de la bibliothèque et permettant l'installation directe en mode éditable.
- **`requirements.txt`** : Fichier recensant les dépendances nécessaires au développement et aux tests.

### 1. Création et activation de l'environnement virtuel (`venv`)

```bash
# Créer l'environnement virtuel .venv
# - Sur Windows (PowerShell / CMD) :
python -m venv .venv --clear
# (ou : py -m venv .venv --clear)

# - Sur Linux / macOS :
python3 -m venv .venv

# Activer l'environnement :
# - Sur Windows (PowerShell) :
.venv\Scripts\Activate.ps1
# - Sur Windows (cmd.exe) :
.venv\Scripts\activate.bat
# - Sur Linux / macOS :
source .venv/bin/activate
```

### 2. Installation des dépendances et du package

```bash
pip install --upgrade pip
pip install -r requirements.txt
pip install -e . --no-build-isolation
```

---

## Guide d'Utilisation

### 🎮 Lancer le Bullet Journal interactif en direct

Pour interagir directement avec votre carnet :

```bash
python3 run_bujo.py
```

Vous obtenez immédiatement le carnet de bord :

```text
============================================================
📖 BULLET JOURNAL DE ÉTUDIANT
🗓️  Date du jour : Jeudi 05 Novembre 2026
============================================================

--- ENTRÉES DU JOUR ---
 [1] • [49b5e978] Découvrir la méthode Bullet Journal - Rapid logging
 [2] ○ [cbf72f61] Point d'avancement de projet (14:30 @ Salle B204)
 [3] – [71bc0c35] Principe clé BuJo - Vivre de manière intentionnelle.
------------------------------------------------------------

📋 ACTIONS DISPONIBLES :
  1. Ajouter une tâche (•)
  2. Ajouter un événement (○)
  3. Ajouter une note (–)
  4. Marquer une tâche comme terminée (×)
  5. Changer le statut d'une tâche (migrer, abandonner...)
  6. Supprimer une entrée
  7. Rafraîchir l'affichage
  0. Quitter le journal
```

### Utilisation dans un script Python

```python
from bujo import BulletJournal

# 1. Ouvrir le carnet
journal = BulletJournal(owner="Mon Nom")

# 2. Ajouter une tâche dans le journal du jour
task = journal.add_task(
    title="Rédiger le rapport",
    description="Détailler l'architecture et les règles du cycle de vie",
)

# 3. Marquer la tâche comme accomplie
journal.mark_task_done(task.id)

# 4. Afficher la journée complète
print(journal.display_today())
```

---

## Tests Unitaires

Tous les tests (34 tests) sont exécutés avec `pytest` :

```bash
pytest -v
```

Sortie attendue :
```text
============================== test session starts ==============================
collected 34 items

tests/test_bujo.py ..................................                    [100%]

============================== 34 passed in 0.21s ==============================
```

---

## Qualité du Code (PEP 8) & Logs

### Vérification PEP 8 avec Flake8

```bash
flake8 src tests run_bujo.py
```

### Fichiers de Logs

Toutes les actions et erreurs sont automatiquement consignées :
- `logs/debug.log` : Traçabilité fine (créations, ajouts, transitions).
- `logs/errors.log` : Violations de règles métier et anomalies critiques.

---

## Intégration Continue (CI)

Le pipeline GitHub Actions ([`.github/workflows/ci.yml`](.github/workflows/ci.yml)) valide automatiquement à chaque push :
1. Le respect de **PEP 8** via `flake8`.
2. La présence des **docstrings** via `pydocstyle`.
3. L'exécution de **tous les tests** via `pytest`.
