# 📘 Documentation Complète du Projet : Bullet Journal Python

Ce document est un **guide de référence complet** conçu pour vous aider à comprendre, maîtriser et expliquer l'ensemble du projet : son architecture, ses choix techniques, le rôle de chaque fichier, et la démarche suivie pour répondre au cahier des charges.

---

## 📑 Sommaire

1. [Comprendre le Domaine : Qu'est-ce que le Bullet Journal ?](#1-comprendre-le-domaine--quest-ce-que-le-bullet-journal-)
2. [L'Arborescence du Projet et l'Objectif de Chaque Fichier](#2-larborescence-du-projet-et-lobjectif-de-chaque-fichier)
3. [Architecture Orientée Objet (POO)](#3-architecture-orientée-objet-poo)
4. [Le Cycle de Vie d'une Tâche et les Règles Métier](#4-le-cycle-de-vie-dune-tâche-et-les-règles-métier)
5. [Le Système de Journalisation (Logs)](#5-le-système-de-journalisation-logs)
6. [Chronologie des Étapes de Travail (Niveau 1)](#6-chronologie-des-étapes-de-travail-niveau-1)
7. [Architecture de l'Environnement et Outils (venv, pip, pyproject.toml)](#7-architecture-de-lenvironnement-et-outils-venv-pip-pyprojecttoml)
8. [Foire Aux Questions pour la Soutenance](#8-foire-aux-questions-pour-la-soutenance)

---

## 1. Comprendre le Domaine : Qu'est-ce que le Bullet Journal ?

Créé par **Ryder Carroll**, le **Bullet Journal (BuJo)** dépasse la simple liste de choses à faire (*to-do list*). C'est une méthode d'organisation personnelle qui repose sur :

1. **Le Rapid Logging** : Une prise de note courte et rapide grâce à des symboles visuels normalisés.
2. **La distinction de 3 types d'entrées fondamentales** :
   - **Tâches (`•`)** : Des actions concrètes à accomplir.
   - **Événements (`○`)** : Des rendez-vous ou faits datés dans le temps.
   - **Notes (`–`)** : Des pensées, idées, réflexions ou informations sans action directe.
3. **L'Intentionnalité & la Migration** : À la fin de chaque journée ou mois, chaque tâche non terminée doit être examinée : soit elle est accomplie (`×`), soit elle est reportée (`>`), soit planifiée plus tard (`<`), soit abandonnée (`~`) car devenue sans intérêt.

> **Pourquoi la POO est-elle idéale pour ce sujet ?**  
> Une *to-do list* basique n'a qu'un type d'objet (la tâche). Le BuJo manipule 3 types d'entrées partageant une base commune mais avec des comportements différents : c'est le cas d'école parfait pour **l'héritage**, **le polymorphisme** et **l'encapsulation**.

---

## 2. L'Arborescence du Projet et l'Objectif de Chaque Fichier

Pour éviter d'avoir des dizaines de fichiers et sous-dossiers éparpillés, le projet a été structuré de manière **compacte et logique** :

```text
Bullet-Journal-Python/
│
├── src/bujo/                  # Le cœur de la bibliothèque Python réutilisable
│   ├── __init__.py            # Point d'entrée public du package
│   ├── models.py              # Les modèles de données (POO) + Exceptions métier
│   ├── journal.py             # L'organisation du carnet (DailyLog et BulletJournal)
│   ├── logger.py              # La configuration du système de double logs
│   └── cli.py                 # L'interface utilisateur interactive en console
│
├── tests/
│   ├── __init__.py
│   └── test_bujo.py           # Les 34 tests unitaires complets (pytest)
│
├── run_bujo.py                # Script pour lancer et tester le carnet directement
├── pyproject.toml             # Configuration du package, build et pytest
├── requirements.txt           # Liste des dépendances (pytest, flake8, pydocstyle)
├── .flake8                    # Règles de style du linter PEP 8
├── .gitignore                 # Fichiers à ne pas commiter (logs/, .venv/, etc.)
├── .github/workflows/
│   └── ci.yml                 # Pipeline d'Intégration Continue (GitHub Actions)
├── README.md                  # Documentation utilisateur générale
└── DOCUMENTATION.md           # Ce guide complet d'architecture et de conception
```

### Rôle détaillé des fichiers :

| Fichier | Objectif et Contenu |
| :--- | :--- |
| **`src/bujo/models.py`** | Définit la classe de base abstraite `Entry`, les classes dérivées `Task`, `Event`, `Note`, l'énumération `TaskStatus`, ainsi que les exceptions (`BujoError`, `ValidationError`, `EntryNotFoundError`, `InvalidStatusTransitionError`). |
| **`src/bujo/journal.py`** | Gère l'organisation temporelle du carnet. Contient `DailyLog` (le journal d'un jour précis) et `BulletJournal` (le carnet global qui supervise tous les jours et permet les recherches transversales). |
| **`src/bujo/logger.py`** | Configure le module standard `logging` pour écrire automatiquement dans deux fichiers cibles : `logs/debug.log` et `logs/errors.log`. |
| **`src/bujo/cli.py`** | Offre une interface interactive en terminal avec un menu numéroté pour ajouter, afficher, terminer et supprimer des entrées sans écrire de code Python. |
| **`src/bujo/__init__.py`** | Expose proprement les classes publiques pour que l'utilisateur puisse faire `from bujo import BulletJournal, Task...`. |
| **`tests/test_bujo.py`** | Regroupe les **34 tests unitaires** testant chaque règle métier, cas nominal et cas d'erreur. |
| **`run_bujo.py`** | Point d'entrée direct pour lancer le carnet interactif en une seule commande (`python3 run_bujo.py`). |

---

## 3. Architecture Orientée Objet (POO)

### 3.1. Le Diagramme de Classes

```text
               +-------------------------------------+
               |             <<abstract>>            |
               |                Entry                |
               +-------------------------------------+
               | - _id: str (UUID unique)            |
               | - _title: str                       |
               | - _description: str                 |
               | - _created_at: datetime             |
               | - _log_date: date                   |
               | - _category: str | None             |
               +-------------------------------------+
               | + @property id -> str               |
               | + @property title -> str            |
               | + @title.setter (valide non vide)   |
               | + @property abstract symbol -> str  |
               | + @abstractmethod display() -> str  |
               +------------------+------------------+
                                  ^
                                  | (héritage)
        +-------------------------+-------------------------+
        |                                                   |
+-------+--------------------+            +-----------------+-----------------+
|            Task            |            |              Event                |
+----------------------------+            +-----------------------------------+
| - _status: TaskStatus      |            | - _event_date: date               |
| - _completed_at: datetime  |            | - _event_time: time | None        |
| - _history: list[tuple]    |            | - _location: str | None           |
+----------------------------+            +-----------------------------------+
| + mark_done()              |            | + symbol = "○"                    |
| + mark_migrated()          |            | + display() -> str                |
| + mark_scheduled()         |            +-----------------------------------+
| + mark_cancelled()         |                              |
| + reopen()                 |            +-----------------+-----------------+
| + symbol: •, ×, >, <, ~    |            |               Note                |
+----------------------------+            +-----------------------------------+
                                          | - _description: str (content)     |
                                          +-----------------------------------+
                                          | + symbol = "–"                    |
                                          | + display() -> str                |
                                          +-----------------------------------+
```

### 3.2. Les Piliers POO appliqués dans le code

1. **L'Abstraction (`ABC`, `@abstractmethod`)** :  
   `Entry` est une classe abstraite. On ne peut pas créer une instance brute `Entry()` : on doit instancier une `Task`, un `Event` ou une `Note`.
2. **L'Encapsulation (`@property`)** :  
   Les attributs sont protégés avec un tiret bas (`_id`, `_title`, `_status`). On ne peut pas corrompre les données : le setter `title` lève une `ValidationError` si quelqu'un essaie d'assigner une chaîne vide. L'identifiant `id` n'a pas de setter, il est immuable.
3. **Le Polymorphisme** :  
   Chaque classe concrète implémente sa propre propriété `symbol` et sa méthode `display()`. Le gestionnaire `DailyLog` peut afficher indifféremment n'importe quelle entrée en faisant simplement `entry.display()`.
4. **Choix de Structure de Données** :  
   Dans `DailyLog`, les entrées sont stockées dans un dictionnaire ordonné `_entries: dict[str, Entry]` indexé par l'ID unique. Cela garantit :
   - L'ordre d'insertion chronologique des entrées.
   - Un accès, une modification ou une suppression instantanée en **temps constant $\mathcal{O}(1)$**.

---

## 4. Le Cycle de Vie d'une Tâche et les Règles Métier

### 4.1. Les États (`TaskStatus`)

| Statut | Symbole | Signification dans le Bullet Journal |
| :--- | :---: | :--- |
| `TO_DO` | `•` | Tâche à faire, en attente d'action. |
| `DONE` | `×` | Tâche accomplie avec succès. |
| `MIGRATED` | `>` | Tâche reportée vers un autre jour ou mois. |
| `SCHEDULED` | `<` | Tâche planifiée dans le calendrier futur (Future Log). |
| `CANCELLED` | `~` | Tâche abandonnée car devenue sans intérêt. |

### 4.2. Les Règles de Transition Métier

Toutes les transitions d'état sont contrôlées par la méthode `_transition_to` dans [`Task`](src/bujo/models.py) :

```text
                  +-------------------+
                  |   TO_DO (•)       | <-------+ (reopen)
                  +---------+---------+         |
                            |                   |
        +-------------------+-------------------+
        |                   |                   |
        v                   v                   v
+---------------+   +---------------+   +---------------+
|   DONE (×)    |   | MIGRATED (>)  |   | CANCELLED (~) |
+---------------+   +---------------+   +---------------+
        |                   |                   |
        X                   X                   X
   (Interdit :         (Interdit :         (Interdit :
   ne peut plus        figée sur           ne peut JAMAIS
   être migrée)        ce log)             être terminée)
```

- **Règle n°1 (Explicite dans le sujet)** : *Il est strictement interdit de terminer une tâche abandonnée.*  
  Si le code tente d'appeler `task.mark_done()` sur une tâche en statut `CANCELLED`, le système refuse et lève une exception `InvalidStatusTransitionError`.
- **Règle n°2** : Une tâche déjà terminée (`DONE`) ne peut pas être abandonnée ou migrée sans être explicitement réouverte avec `reopen()`.
- **Règle n°3** : L'historique complet des transitions est conservé dans `task.history` avec l'horodatage précis de chaque étape.

---

## 5. Le Système de Journalisation (Logs)

Le module [`src/bujo/logger.py`](src/bujo/logger.py) implémente un système de traçabilité complet à deux niveaux :

```text
                        Application BuJo
                               |
               +---------------+---------------+
               |                               |
       Niveau DEBUG et +               Niveau ERROR et +
               |                               |
               v                               v
       [logs/debug.log]               [logs/errors.log]
  (Créations, ajouts d'entrées,     (Transitions interdites,
   changements d'état de tâches)      recherches introuvables)
```

1. **`logs/debug.log`** : Journal exhaustif pour le développeur. Il enregistre chaque événement (initialisation, création d'une tâche, complétion, suppression).
2. **`logs/errors.log`** : Journal filtré réservé aux administrateurs. Il n'enregistre **que** les anomalies critiques (`ERROR` et `CRITICAL`), par exemple une tentative illégale de changer l'état d'une tâche.

---

## 6. Chronologie des Étapes de Travail (Niveau 1)

Pour construire ce Niveau 1, la démarche a suivi les bonnes pratiques du génie logiciel :

```text
1. Modélisation POO & Exceptions (models.py)
   └── Définition d'Entry, Task, Event, Note et des exceptions métier

2. Organisation temporelle (journal.py)
   └── Implémentation de DailyLog et BulletJournal en accès O(1)

3. Journalisation robuste (logger.py)
   └── Configuration de debug.log et errors.log

4. Tests Unitaires approfondis (tests/test_bujo.py)
   └── 34 tests couvrant les cas nominaux et d'erreurs

5. Interface Interactive (cli.py / run_bujo.py)
   └── Console interactive permettant de jouer avec le carnet

6. Qualité de Code & Intégration Continue (CI)
   └── Linter PEP 8 (flake8), vérification docstrings (pydocstyle) et CI GitHub Actions
```

---

## 7. Architecture de l'Environnement et Outils (venv, pip, pyproject.toml)

Pour garantir la portabilité, l'isolation et la reproductibilité du projet sans dépendances externes lourdes, la chaîne d'outils s'articule autour des standards officiels de Python :

```text
+-------------------------------------------------------------------------------+
|                                MACHINE HÔTE                                   |
|                                                                               |
|  +-------------------------------------------------------------------------+  |
|  |                 ENVIRONNEMENT VIRTUEL : venv (.venv/)                   |  |
|  |                                                                         |  |
|  |   - Interpréteur Python isolé (Scripts/python.exe ou bin/python)        |  |
|  |   - Isolation complète : aucun conflit avec les packages de l'OS       |  |
|  |                                                                         |  |
|  |   +-----------------------------------------------------------------+   |  |
|  |   |                  GESTIONNAIRE DE PAQUETS : pip                  |   |  |
|  |   |                                                                 |   |  |
|  |   |   1. Télécharge & installe depuis PyPI                          |   |  |
|  |   |      via `requirements.txt` :                                   |   |  |
|  |   |      └── pytest, flake8, pydocstyle, setuptools                 |   |  |
|  |   |                                                                 |   |  |
|  |   |   2. Installe le projet en mode éditable                        |   |  |
|  |   |      via `pip install -e .` en s'appuyant sur                   |   |  |
|  |   |      `pyproject.toml` (standard PEP 517 / 621)                  |   |  |
|  |   +-----------------------------------------------------------------+   |  |
|  |                                                                         |  |
|  |   +-----------------------------------------------------------------+   |  |
|  |   |                      MOTEUR DE BUILD : setuptools               |   |  |
|  |   |   - Analyse la structure `src/bujo`                             |   |  |
|  |   |   - Génère les métadonnées et connecte le package en direct     |   |  |
|  |   +-----------------------------------------------------------------+   |  |
|  +-------------------------------------------------------------------------+  |
+-------------------------------------------------------------------------------+
```

### Rôles respectifs de chaque outil :

| Outil / Fichier | Rôle précis | Pourquoi ce choix ? |
| :--- | :--- | :--- |
| **`venv`** | **Gestionnaire d'environnement virtuel** : crée un dossier `.venv/` isolé contenant son propre interpréteur Python et son propre dossier `site-packages`. | Module natif standard de Python (zéro installation externe nécessaire, ultra-léger face aux plusieurs Go d'Anaconda). |
| **`pip`** | **Gestionnaire de paquets (*Package Installer*)** : télécharge, résout et installe les bibliothèques depuis l'index officiel PyPI. | Outil de référence universel de Python pour installer des packages. |
| **`requirements.txt`** | **Liste déclarative des dépendances de développement** : liste les outils tiers nécessaires (`pytest`, `flake8`, `pydocstyle`, `setuptools`). | Permet à tout développeur d'installer tous les outils en une seule commande : `pip install -r requirements.txt`. |
| **`pyproject.toml`** | **Configuration standard moderne (PEP 517/518/621)** : définit les métadonnées du projet (nom, version, auteur, version Python minimale) et configure les outils (`pytest`). | Remplace les anciens fichiers `setup.py` monolithiques selon les recommandations actuelles de la *Python Packaging Authority (PyPA)*. |
| **`setuptools`** | **Moteur de construction (*Build Backend*)** : lit `pyproject.toml`, découvre les packages du dossier `src/` et produit le lien éditable (`pip install -e .`). | Backend stable et éprouvé pour la création et distribution de packages Python. |

---

## 8. Foire Aux Questions pour la Soutenance

### Q1 : Pourquoi utiliser des UUID pour les identifiants plutôt que le nom de la tâche ?
> **Réponse :** Dans un Bullet Journal, une personne peut très bien avoir deux tâches portant le même nom (par exemple *"Faire du sport"* le matin et le soir, ou migrer la même tâche de jour en jour). Si on utilisait le nom comme identifiant, supprimer ou terminer une tâche risquerait d'altérer l'autre. L'UUID garantit une unicité absolue sans collision.

### Q2 : Pourquoi `Entry` est-elle abstraite ?
> **Réponse :** Dans la méthode BuJo, une "entrée" n'existe pas seule dans la réalité : c'est soit une Tâche, soit un Événement, soit une Note. Rendre la classe abstraite avec `ABC` empêche d'instancier un objet générique sans sens métier et oblige chaque sous-classe à définir son symbole (`symbol`) et son affichage (`display`).

### Q3 : Comment lance-t-on les tests unitaires ?
> **Réponse :** Dans le terminal, à la racine du projet :
> ```bash
> pytest -v
> ```
> Les 34 tests s'exécutent en moins d'une demi-seconde et valident l'intégralité du socle.

### Q4 : Comment vérifie-t-on le respect de PEP 8 ?
> **Réponse :** Avec la commande :
> ```bash
> flake8 src tests run_bujo.py
> ```
> Le retour est vide (code de sortie 0), ce qui prouve une conformité totale aux normes PEP 8.

### Q5 : Comment jouer concrètement avec le carnet ?
> **Réponse :** En lançant :
> ```bash
> python3 run_bujo.py
> ```
> Le menu interactif permet d'ajouter des tâches, de les cocher, de les abandonner ou de les supprimer directement dans le terminal.

### Q6 : Quel gestionnaire d'environnement virtuel avez-vous choisi et pourquoi ?
> **Réponse :** Le projet utilise exclusivement **`venv`** (le module standard natif de Python) avec **`pip`**. Contrairement à Anaconda qui nécessite une installation externe lourde, `venv` est directement intégré à Python, portable, sans dépendance tierce, et représente le standard recommandé par la *Python Packaging Authority (PyPA)* pour les bibliothèques logicielles.


