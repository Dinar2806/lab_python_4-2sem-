import asyncio
import logging
from typing import Dict, Optional
from src.task.task import Task
from src.task_executor.protocol import TaskHandler
from src.task_executor.resource import AsyncResource

logger = logging.getLogger(__name__)

class HandlerRegistry:
    """Реестр обработчиков задач."""
    
    def __init__(self) -> None:
        self._handlers: Dict[str, TaskHandler] = {}

    def register(self, task_type: str, handler: TaskHandler) -> None:
        if not isinstance(handler, TaskHandler):
            raise TypeError(
                f"Объект {type(handler).__name__} не соответствует контракту TaskHandler. "
                f"должен быть метод 'async def handle(self, task, resource)'."
            )

        self._handlers[task_type] = handler
        logger.info("Зарегистрирован обработчик для типа: %s", task_type)

    def get_handler(self, task_type: str) -> Optional[TaskHandler]:
        return self._handlers.get(task_type)

class AsyncExecutor:
    """Асинхронный исполнитель задач с пулом воркеров."""
    
    def __init__(self, queue: asyncio.Queue[Task], registry: HandlerRegistry, worker_count: int = 2) -> None:
        self.queue = queue
        self.registry = registry
        self.worker_count = worker_count
        self._workers: list[asyncio.Task[None]] = []
        self._stop_event = asyncio.Event()

    async def _worker(self, worker_id: int) -> None:
        logger.info("Воркер %d запущен", worker_id)
        while not self._stop_event.is_set():
            try:
                task = await asyncio.wait_for(self.queue.get(), timeout=0.5)
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break

            handler = self.registry.get_handler(task.task_type)
            if handler is None:
                logger.error("Обработчик для типа '%s' не найден", task.task_type)
                self.queue.task_done()
                continue

            try:
                async with AsyncResource() as resource:
                    await handler.handle(task, resource)
                    logger.info("Задача %s успешно обработана", task.id)
            except Exception as exc:
                logger.error("Ошибка обработки задачи %s: %s", task.id, exc, exc_info=True)
            finally:
                self.queue.task_done()

        logger.info("Воркер %d остановлен", worker_id)

    async def start(self) -> None:
        self._stop_event.clear()
        self._workers = [
            asyncio.create_task(self._worker(i), name=f"worker-{i}")
            for i in range(self.worker_count)
        ]
        logger.info("Исполнитель запущен с %d воркерами", self.worker_count)

    async def stop(self) -> None:
        self._stop_event.set()
        for worker in self._workers:
            worker.cancel()
        await asyncio.gather(*self._workers, return_exceptions=True)
        logger.info("Исполнитель остановлен")

    async def wait_completion(self) -> None:
        await self.queue.join()