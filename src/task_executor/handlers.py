import asyncio
import logging
from typing import Any
from src.task.task import Task, TaskStatus
from src.task_executor.protocol import TaskHandler

logger = logging.getLogger(__name__)

class DataProcessorHandler:
    async def handle(self, task: Task, resource: Any) -> None:
        logger.info("Обработка данных: %s", task.payload)
        await asyncio.sleep(0.05)
        task.status = TaskStatus.DONE

class NotificationHandler:
    async def handle(self, task: Task, resource: Any) -> None:
        logger.info("Отправка уведомления: %s", task.payload)
        await asyncio.sleep(0.1)
        task.status = TaskStatus.DONE