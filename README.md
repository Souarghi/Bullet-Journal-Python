# Bullet Journal Python (BuJo) - Niveau 2 & Interface Graphique Tkinter

Bibliothèque Python modulaire, testée et documentée implémentant la méthode du **Bullet Journal (BuJo)** créée par Ryder Carroll.

Cette branche implémente l'intégralité du **Niveau 1 (Le socle)** et du **Niveau 2 (La méthode BuJo : Signifiants, MonthlyLog, Migration)**, enrichie d'une **Interface Graphique native moderne en Tkinter**.

> 📖 **Pour une explication approfondie de l'architecture, des choix de conception et du guide de soutenance**, consultez le fichier [DOCUMENTATION.md](DOCUMENTATION.md).

---

## Sommaire

1. [Fonctionnalités (Niveaux 1 & 2)](#fonctionnalités-niveaux-1--2)
2. [Structure du Projet Épurée](#structure-du-projet-épurée)
3. [Installation & Environnement](#installation--environnement)
4. [Guide d'Utilisation (GUI Tkinter & CLI)](#guide-dutilisation-gui-tkinter--cli)
5. [Tests Unitaires (51 tests)](#tests-unitaires)
6. [Qualité du Code (PEP 8) & Logs](#qualité-du-code-pep-8--logs)
7. [Intégration Continue (CI)](#intégration-continue-ci)

---

## Fonctionnalités (Niveaux 1 & 2)

### 🧱 Niveau 1 : Le Socle
- **Gestion des 3 types d'entrées fondamentales** :
  - **Tâches (`Task`)** : intitulé, description, statut et historique horodaté.
  - **Événements (`Event`)** : date, heure optionnelle et lieu.
  - **Notes (`Note`)** : réflexions et faits consignés.
- **Identifiants uniques (UUID)** : distinction absolue entre tâches homonymes ou récurrentes.
- **Cycle de vie strict des tâches** :
  - États : `À faire` (`•`), `Terminée` (`×`), `Migrée` (`>`), `Planifiée` (`<`), `Abandonnée` (`~`).
  - Interdiction stricte de terminer une tâche abandonnée (`InvalidStatusTransitionError`).
- **Journal quotidien (`DailyLog`)** : ajout, complétion, suppression, filtrage en temps constant $O(1)$.
- **Double système de journalisation (Logging)** : `logs/debug.log` (traçabilité) et `logs/errors.log` (anomalies).

### 🚀 Niveau 2 : La Méthode BuJo & Signifiants
- **Signifiants (*Signifiers*)** :
  - `*` : Priorité / Urgent (ex: `* • Rendre le projet`).
  - `!` : Inspiration / Idée (ex: `! – Idée de projet innovant`).
- **Organisation mensuelle (`MonthlyLog`)** :
  - **Page Calendrier** : vue chronologique de chaque jour du mois et de ses événements datés.
  - **Page Tâches** : liste de rapid logging des tâches et notes du mois.
- **Mécanisme complet de Migration** :
  - Migration d'une tâche d'un jour vers le suivant (l'originale passe en `>`, la nouvelle naît en `•` avec traçabilité croisée `migrated_from_id` / `migrated_to_id`).
  - Migration collective de toutes les tâches en attente du jour vers demain.
  - Migration mensuelle d'un mois vers le suivant.
- **🎨 Interface Graphique Tkinter (Bonus)** :
  - Interface visuelle native (zéro bibliothèque tierce lourde).
  - Navigation par onglets (*Vue du Jour*, *Vue du Mois*, *Recherche & Logs en direct*).
  - Boutons d'action en un clic pour cocher, migrer, ajouter ou supprimer des entrées.

---

## Structure du Projet Épurée

Le projet conserve une structure **compacte, sans dossiers inutiles** :

```text
Bullet-Journal-Python/
├── src/bujo/
│   ├── __init__.py      # Point d'entrée public du package
│   ├── models.py        # Modèles POO (Entry, Task, Event, Note, Signifier) + Exceptions
│   ├── journal.py       # Organisation temporelle (DailyLog, MonthlyLog, BulletJournal)
│   ├── logger.py        # Double journalisation (debug.log et errors.log)
│   ├── gui.py           # Interface visuelle native en Tkinter (Niveau 2)
│   └── cli.py           # Interface interactive en terminal
├── tests/
│   ├── __init__.py
│   └── test_bujo.py     # TOUS les 51 tests unitaires dans un SEUL fichier
├── run_bujo.py          # Script exécutable direct (lance la GUI ou la console)
├── pyproject.toml       # Métadonnées du package (PEP 517 / 621)
├── requirements.txt     # Dépendances de développement (pytest, flake8, pydocstyle)
├── .flake8              # Règles du linter PEP 8
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

## Guide d'Utilisation (GUI Tkinter & CLI)

### 🎨 1. Lancer l'Interface Graphique Tkinter (par défaut)

Pour ouvrir la fenêtre visuelle du Bullet Journal :

```bash
python run_bujo.py
```

L'interface graphique vous permet de :
- Consulter le **Daily Log** avec compteurs en temps réel (tâches à faire, finies, migrées, événements, notes).
- Ajouter des tâches en cochant directement les signifiants (`* Priorité`, `! Idée`).
- Cocher, abandonner ou supprimer des entrées en un clic.
- Reporter une tâche vers demain (`>`) ou migrer tout le journal en un seul clic (`📦 Tout migrer`).
- Parcourir le **Monthly Log** avec la page calendrier et la page tâches du mois.
- Consulter la traçabilité des fichiers `debug.log` et `errors.log` directement dans l'onglet Dédié.

### 💻 2. Lancer l'Interface en Console (CLI)

Si vous travaillez dans un terminal ou via SSH :

```bash
python run_bujo.py --cli
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
collected 51 items

tests/test_bujo.py ...................................................   [100%]

============================== 51 passed in 0.14s ==============================
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
