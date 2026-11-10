"""In-memory task storage."""

from dataclasses import asdict, dataclass
from threading import Lock


@dataclass
class Task:
    id: int
    title: str
    done: bool = False

    def to_dict(self) -> dict:
        return asdict(self)


class TaskStore:
    def __init__(self) -> None:
        self._tasks: dict[int, Task] = {}
        self._next_id = 1
        self._lock = Lock()

    def seed(self, titles: list[str]) -> None:
        for title in titles:
            self.add(title)

    def add(self, title: str) -> Task:
        with self._lock:
            task = Task(id=self._next_id, title=title)
            self._tasks[task.id] = task
            self._next_id += 1
            return task

    def complete(self, task_id: int) -> Task | None:
        with self._lock:
            task = self._tasks.get(task_id)
            if task is not None:
                task.done = True
            return task

    def list(self, status: str = "all") -> list[Task]:
        tasks = list(self._tasks.values())
        if status == "open":
            return [t for t in tasks if not t.done]
        if status == "done":
            return [t for t in tasks if t.done]
        return tasks

    def counts(self) -> dict[str, int]:
        done = sum(1 for t in self._tasks.values() if t.done)
        return {"all": len(self._tasks), "open": len(self._tasks) - done, "done": done}
