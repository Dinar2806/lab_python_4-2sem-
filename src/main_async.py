import asyncio
import logging
from src.task_collector.collector import TaskCollector
from src.task_sources.generator_source import GeneratorSource
from src.task_executor.core import AsyncExecutor, HandlerRegistry
from src.task_executor.handlers import DataProcessorHandler, NotificationHandler

# Настройка логирования (переопределяем формат для async)
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("AsyncApp")

async def main() -> None:
    """Асинхронная точка входа: исполнение задач."""
    
    # 1. Подготовка данных (используем старый синхронный код)
    collector = TaskCollector()
    sources = [GeneratorSource(count=10)]
    collected = collector.collect_from_sources(sources)
    
    # Преобразуем в плоский список и назначаем типы для маршрутизации
    tasks = []
    for idx, task_list in enumerate(collected.values()):
        for t in task_list:
            t.task_type = "process" if idx % 2 == 0 else "notify"
            tasks.append(t)
    
    # 2. Настройка асинхронного ядра
    queue = asyncio.Queue()
    registry = HandlerRegistry()
    registry.register("process", DataProcessorHandler())
    registry.register("notify", NotificationHandler())
    
    executor = AsyncExecutor(queue=queue, registry=registry, worker_count=5)
    
    # 3. Запуск
    await executor.start()
    
    # Наполнение очереди (неблокирующее)
    for task in tasks:
        await queue.put(task)
        logger.debug("Задача %s добавлена в очередь", task.id)
    
    # Ожидание завершения всех задач
    await queue.join()
    
    # Корректная остановка
    await executor.stop()
    logger.info("Работа асинхронного исполнителя завершена")

if __name__ == "__main__":
    # asyncio.run() - единственная точка входа для event loop
    asyncio.run(main())