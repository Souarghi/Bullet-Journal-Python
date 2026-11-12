class EntryNotFoundError(Exception):
    """
    Levée lorsqu'une entrée n'est pas trouvée dans le journal.
    """
    pass

class StateTransitionError(Exception):
    """
    Levée lorsqu'une transition d'état est interdite (ex: terminer une tâche abandonnée).
    """
    pass