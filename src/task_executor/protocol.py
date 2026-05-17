from typing import Protocol, Any
from src.task.task import Task

class TaskHandler(Protocol):
    """Интерфейс для всех асинхронных обработчиков задач."""
    async def handle(self, task: Task, resource: Any) -> None:
        ...