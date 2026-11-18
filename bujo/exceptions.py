"""Exceptions personnalisées de la bibliothèque Bullet Journal."""


class BujoError(Exception):
    """Erreur de base de la bibliothèque Bullet Journal."""


class EntryNotFoundError(BujoError):
    """L'identifiant demandé ne correspond à aucune entrée du journal."""


class EmptyNameError(BujoError):
    """Le nom d'une entrée ne peut pas être vide."""


class InvalidDateError(BujoError):
    """La date fournie est invalide."""


class InvalidStateTransitionError(BujoError):
    """La transition d'état demandée est interdite pour une tâche."""


class InvalidSignifierError(BujoError):
    """Le signifiant demandé ne fait pas partie des signifiants connus."""


class PersistenceError(BujoError):
    """Le journal n'a pu être sauvegardé ou chargé depuis son fichier."""
