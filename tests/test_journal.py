from bujo.entries import Task, TaskState
from bujo.journal import DailyLog

def test_add_and_list_pending_tasks() -> None:
    """
    Vérifie que l'on peut ajouter une tâche et la retrouver dans les tâches en cours.
    :return:
    """
    journal = DailyLog()
    task1 = Task(name="Réviser Python")
    task2 = Task(name="Finir TD math")

    journal.add_entry(task1)
    journal.add_entry(task2)

    pending = journal.get_pending_tasks()

    assert len(pending) == 2
    assert pending[0].name == "Réviser Python"
    assert pending[1].name == "Finir TD math"

def test_complete_task_remove_it_from_pending() -> None:
    """
    Vérifie qu'une tâche terminée n'est plus considéré comme TODO.
    :return:
    """
    journal = DailyLog()
    task1 = Task(name="Faire les courses")
    journal.add_entry(task1)

    task1.complete()

    assert task1.state == TaskState.DONE
    assert len(journal.get_pending_tasks()) == 0
