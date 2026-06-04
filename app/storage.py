from typing import List
from app.schemas import Task

class Storage:
    def __init__(self):
        self.tasks: List[Task] = []
        self.task_counter = 1

    def add_task(self, task_data: dict, owner_id: int) -> Task:
        task = Task(id=self.task_counter, owner_id=owner_id, **task_data)
        self.tasks.append(task)
        self.task_counter += 1
        return task

    def get_tasks(self, owner_id: int = None) -> List[Task]:
        if owner_id is not None:
            return [t for t in self.tasks if t.owner_id == owner_id]
        return self.tasks

    def get_task(self, task_id: int) -> Task:
        for t in self.tasks:
            if t.id == task_id:
                return t
        return None

    def delete_task(self, task_id: int):
        self.tasks = [t for t in self.tasks if t.id != task_id]

storage = Storage()

def get_storage():
    return storage
