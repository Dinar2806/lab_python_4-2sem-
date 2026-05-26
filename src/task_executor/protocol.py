from typing import Protocol, Any, runtime_checkable
from src.task.task import Task

@runtime_checkable
class TaskHandler(Protocol):
    """Интерфейс для всех асинхронных обработчиков задач."""
    async def handle(self, task: Task, resource: Any) -> None:
        ...