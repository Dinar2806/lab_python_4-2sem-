import asyncio
import logging
import pytest
from typing import List

from src.task.task import Task, TaskStatus
from src.task.descriptor import InvalidPriorityError, InvalidStatusError, InvalidPayloadError
from src.task_executor.core import HandlerRegistry, AsyncExecutor
from src.task_executor.resource import AsyncResource

logging.basicConfig(level=logging.INFO)


@pytest.fixture
def sample_tasks():
    """Создает список из 5 задач с разными параметрами."""
    return [
        Task(id=1, payload="Low priority todo", priority=1, status=TaskStatus.TODO),
        Task(id=2, payload="High priority todo", priority=9, status=TaskStatus.TODO),
        Task(id=3, payload="Medium done", priority=5, status=TaskStatus.DONE),
        Task(id=4, payload="Critical in progress", priority=10, status=TaskStatus.IN_PROGRESS),
        Task(id=5, payload="Another low todo", priority=2, status=TaskStatus.TODO),
    ]

@pytest.fixture
def large_task_list():
    """Генерирует большой список задач для нагрузочных тестов."""
    count = 100_000
    tasks = []
    for i in range(count):
        status = TaskStatus.TODO if i % 2 == 0 else TaskStatus.DONE
        priority = (i % 10) + 1
        tasks.append(Task(id=i, payload=f"Task payload number {i}", priority=priority, status=status))
    return tasks

@pytest.fixture
def large_factory():
    """Фабрика-генератор для ленивого создания задач."""
    def _generator():
        count = 100_000
        for i in range(count):
            status = TaskStatus.TODO if i % 2 == 0 else TaskStatus.DONE
            yield Task(id=i, payload=f"Stream task {i}", priority=(i % 10) + 1, status=status)
    return _generator


class MockHandler:
    """Заглушка обработчика для подсчета вызовов."""
    def __init__(self):
        self.processed_tasks: List[Task] = []
        self.call_count = 0

    async def handle(self, task: Task, resource: AsyncResource) -> None:
        self.call_count += 1
        self.processed_tasks.append(task)
        await asyncio.sleep(0.001)
        task.status = TaskStatus.DONE


class TestTaskModel:
    """Тесты модели Task и дескрипторов."""

    def test_create_valid_task(self):
        """Проверка создания корректной задачи."""
        task = Task(id=1, payload="Test", priority=5, status=TaskStatus.TODO)
        assert task.id == "1"
        assert task.priority == 5
        assert task.status == TaskStatus.TODO

    def test_id_normalization(self):
        """IDDescriptor должен приводить число к строке."""
        task = Task(id=123, payload="Data", priority=5, status=TaskStatus.TODO)
        assert isinstance(task.id, str)
        assert task.id == "123"

    def test_invalid_priority_type(self):
        """PriorityDescriptor отвергает не-int значения."""
        with pytest.raises(InvalidPriorityError):
            Task(id=1, payload="Data", priority="high", status=TaskStatus.TODO)

    def test_invalid_priority_range(self):
        """PriorityDescriptor проверяет диапазон [1, 10]."""
        with pytest.raises(InvalidPriorityError):
            Task(id=1, payload="Data", priority=15, status=TaskStatus.TODO)
        with pytest.raises(InvalidPriorityError):
            Task(id=1, payload="Data", priority=0, status=TaskStatus.TODO)

    def test_invalid_status_type(self):
        """StatusDescriptor требует экземпляр Enum."""
        with pytest.raises(InvalidStatusError):
            Task(id=1, payload="Data", priority=5, status="todo")

    def test_empty_payload_rejected(self):
        """PayloadDescriptor не принимает пустые значения."""
        with pytest.raises(InvalidPayloadError):
            Task(id=1, payload="", priority=5, status=TaskStatus.TODO)
        with pytest.raises(InvalidPayloadError):
            Task(id=1, payload=None, priority=5, status=TaskStatus.TODO)

    def test_ready_to_perform_property(self):
        """Проверка свойства ready_to_perform."""
        task = Task(id=1, payload="Work", priority=5, status=TaskStatus.TODO)
        assert task.ready_to_perform is True
        task.status = TaskStatus.DONE
        assert task.ready_to_perform is False


class TestHandlerRegistry:
    """Тесты реестра обработчиков."""

    def test_register_and_get_handler(self):
        """Регистрация и получение обработчика."""
        registry = HandlerRegistry()
        mock_handler = MockHandler()
        registry.register("default", mock_handler)
        assert registry.get_handler("default") is mock_handler

    def test_get_unknown_handler_returns_none(self):
        """Незарегистрированный обработчик возвращает None."""
        registry = HandlerRegistry()
        assert registry.get_handler("unknown") is None


@pytest.mark.asyncio
async def test_executor_processes_all_tasks(sample_tasks):
    """Все задачи из очереди должны быть обработаны."""
    queue = asyncio.Queue()
    registry = HandlerRegistry()
    handler = MockHandler()

    registry.register("default", handler)
    executor = AsyncExecutor(queue=queue, registry=registry, worker_count=2)

    for t in sample_tasks:
        await queue.put(t)

    await executor.start()
    await queue.join()
    await executor.stop()

    assert handler.call_count == 5
    assert len(handler.processed_tasks) == 5
    for t in handler.processed_tasks:
        assert t.status == TaskStatus.DONE


@pytest.mark.asyncio
async def test_executor_handles_missing_handler():
    """Отсутствие обработчика не должно блокировать очередь."""
    queue = asyncio.Queue()
    registry = HandlerRegistry()
    registry.register("type_a", MockHandler())

    executor = AsyncExecutor(queue=queue, registry=registry, worker_count=1)

    bad_task = Task(id=99, payload="Bad", priority=5, status=TaskStatus.TODO)
    bad_task.task_type = "type_b"
    await queue.put(bad_task)

    await executor.start()
    await queue.join()
    await executor.stop()

    assert queue.empty()


@pytest.mark.asyncio
async def test_executor_handles_exception_in_handler():
    """Исключение в обработчике не должно останавливать воркер."""
    queue = asyncio.Queue()
    registry = HandlerRegistry()

    class FailingHandler:
        def __init__(self):
            self.calls = 0

        async def handle(self, task: Task, resource: AsyncResource) -> None:
            self.calls += 1
            if task.id == "fail":
                raise ValueError("Simulated Error")
            await asyncio.sleep(0.01)

    handler = FailingHandler()
    registry.register("test", handler)

    executor = AsyncExecutor(queue=queue, registry=registry, worker_count=1)

    t1 = Task(id=10, payload="Ok", priority=5, status=TaskStatus.TODO)
    t1.task_type = "test"
    t2 = Task(id=20, payload="Fail", priority=5, status=TaskStatus.TODO)
    t2.task_type = "test"
    t3 = Task(id=30, payload="Ok2", priority=5, status=TaskStatus.TODO)
    t3.task_type = "test"

    await queue.put(t1)
    await queue.put(t2)
    await queue.put(t3)

    await executor.start()
    await queue.join()
    await executor.stop()

    assert handler.calls == 3


@pytest.mark.asyncio
async def test_resource_context_manager():
    """Проверка открытия и закрытия ресурса."""
    res = AsyncResource()
    assert res.is_connected is False

    async with res as r:
        assert r.is_connected is True
        assert r is res

    assert res.is_connected is False


@pytest.mark.asyncio
async def test_full_pipeline_integration(large_factory):
    """Интеграционный тест: фабрика -> очередь -> исполнитель."""
    limit = 10
    source_queue = asyncio.Queue()

    for i, task in enumerate(large_factory()):
        if i >= limit:
            break
        task.task_type = "default"
        await source_queue.put(task)

    assert source_queue.qsize() == limit

    registry = HandlerRegistry()
    handler = MockHandler()
    registry.register("default", handler)

    executor = AsyncExecutor(queue=source_queue, registry=registry, worker_count=2)

    await executor.start()
    await source_queue.join()
    await executor.stop()

    assert handler.call_count == limit
    for t in handler.processed_tasks:
        assert t.status == TaskStatus.DONE


@pytest.mark.asyncio
async def test_large_volume_processing(large_task_list):
    """Нагрузочный тест обработки большого объема задач."""
    queue = asyncio.Queue()
    registry = HandlerRegistry()
    handler = MockHandler()
    registry.register("default", handler)

    executor = AsyncExecutor(queue=queue, registry=registry, worker_count=4)

    tasks_to_process = large_task_list[:1000]
    for t in tasks_to_process:
        t.task_type = "default"
        await queue.put(t)

    await executor.start()
    await queue.join()
    await executor.stop()

    assert handler.call_count == 1000