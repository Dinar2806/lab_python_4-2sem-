import pytest
from src.task.task import Task, TaskStatus
from src.task_queue.queue import TaskQueue

# Фикстуры

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
def base_queue(sample_tasks):
    """Базовая очередь из списка задач."""
    return TaskQueue(sample_tasks)

@pytest.fixture
def large_task_list():
    """
    Генерирует список из count задач
    """
    count = 100_000
    tasks = []
    for i in range(count):
        status = TaskStatus.TODO if i % 2 == 0 else TaskStatus.DONE
        priority = (i % 10) + 1
        
        tasks.append(Task(
            id=i,
            payload=f"Task payload number {i}",
            priority=priority,
            status=status
        ))
    return tasks

@pytest.fixture
def large_queue(large_task_list):
    """Очередь, обернутая вокруг большого списка."""
    return TaskQueue(large_task_list)

@pytest.fixture
def large_factory():
    """
    Фабрика, которая генерирует задачи по ходу выполнения.
    Имитирует потоковую обработку без хранения всего списка в памяти изначально.
    """
    def _generator():
        count = 100_000
        for i in range(count):
            status = TaskStatus.TODO if i % 2 == 0 else TaskStatus.DONE
            yield Task(
                id=i,
                payload=f"Stream task {i}",
                priority=(i % 10) + 1,
                status=status
            )
    return _generator

@pytest.fixture
def large_stream_queue(large_factory):
    """Очередь, использующая фабрику вместо списка."""
    return TaskQueue(large_factory)

# Тесты базовой итерации

class TestTaskQueueIteration:
    def test_iterate_all_tasks(self, base_queue):
        """Проверка, что очередь отдает все задачи."""
        tasks_list = list(base_queue)
        assert len(tasks_list) == 5

    def test_repeatable_iteration(self, base_queue):
        """Критический тест: проверка повторного обхода."""
        # Первый проход
        count1 = sum(1 for _ in base_queue)
        # Второй проход
        count2 = sum(1 for _ in base_queue)
        
        assert count1 == 5
        assert count2 == 5
        assert count1 == count2

    def test_empty_queue_iteration(self):
        """Проверка итерации по пустой очереди."""
        empty_queue = TaskQueue([])
        assert list(empty_queue) == []
        assert list(empty_queue) == [] # И снова пусто (повторный обход работает)

# Тесты фильтрации

class TestTaskQueueFiltering:
    def test_filter_by_status_todo(self, base_queue):
        """Фильтрация по статусу TODO."""
        filtered = base_queue.filter_by_status(TaskStatus.TODO)
        result = list(filtered)
        
        assert len(result) == 3
        for task in result:
            assert task.status == TaskStatus.TODO

    def test_filter_by_priority_range(self, base_queue):
        """Фильтрация по диапазону приоритета."""
        # Приоритет >= 5 и <= 9
        filtered = base_queue.filter_by_priority(highest_prior=5, lowest_prior=9)
        result = list(filtered)
        
        assert len(result) == 2
        for task in result:
            assert 5 <= task.priority <= 9

    def test_filter_repeatable_iteration(self, base_queue):
        """Критический тест: повторный обход отфильтрованной очереди."""
        filtered = base_queue.filter_by_status(TaskStatus.DONE)
        
        list1 = list(filtered)
        list2 = list(filtered)
        
        assert len(list1) == 1
        assert len(list2) == 1
        assert list1[0].id == list2[0].id

    def test_chained_filters(self, base_queue):
        """Проверка цепочки фильтров: Статус TODO И Приоритет > 5."""
        chained = (base_queue
                   .filter_by_status(TaskStatus.TODO)
                   .filter_by_priority(highest_prior=5))
        
        result = list(chained)
        assert len(result) == 1
        assert result[0].id == "2"

    def test_chain_repeatable_iteration(self, base_queue):
        """Повторный обход цепочки фильтров."""
        chained = base_queue.filter_by_status(TaskStatus.TODO).filter_by_priority(highest_prior=5)
        
        count1 = sum(1 for _ in chained)
        count2 = sum(1 for _ in chained)
        
        assert count1 == 1
        assert count2 == 1

    def test_generic_filter_lambda(self, base_queue):
        """Проверка универсального фильтра с lambda."""
        # Фильтруем задачи, у которых в payload есть слово "priority"
        filtered = base_queue.filter(lambda t: "priority" in str(t.payload))
        result = list(filtered)
        
        # В наших тестовых данных это ID 1 и ID 2
        assert len(result) == 2

    def test_reg_filter_by_id_string_in_int(self, base_queue):
        """Проверка поиска подстроки в числовом ID (безопасность типов)."""
        filtered = base_queue.reg_filter_by_id("1")
        result = list(filtered)
        
        ids = [t.id for t in result]
        assert "1" in ids


    def test_reg_filter_by_payload_dict(self, sample_tasks):
        """Проверка поиска в payload, если там словарь (безопасность типов)."""
        # Добавим задачу со словарем в payload
        task_dict = Task(id=99, payload={"key": "secret"}, priority=5, status=TaskStatus.TODO)
        queue = TaskQueue([task_dict])
        
        filtered = queue.reg_filter_by_payload("secret")
        assert len(list(filtered)) == 1

# Тесты агрегаторов

class TestTaskQueueAggregators:
    def test_count(self, base_queue):
        """Проверка метода count()."""
        assert base_queue.count() == 5
        
        filtered = base_queue.filter_by_status(TaskStatus.TODO)
        assert filtered.count() == 3

    def test_to_list(self, base_queue):
        """Проверка материализации в список."""
        lst = base_queue.to_list()
        assert isinstance(lst, list)
        assert len(lst) == 5

# Тесты граничных случаев

class TestEdgeCases:
    def test_filter_no_matches(self, base_queue):
        """Фильтр, который ничего не находит."""

        filtered_pri = base_queue.filter_by_priority(highest_prior=100) # Приоритет только от 1 до 10
        
        assert list(filtered_pri) == []
        assert list(filtered_pri) == [] # Повторный обход пустой очереди

    def test_factory_source_iteration(self):
        """Проверка, что очередь работает с функцией-фабрикой как источником."""
        def my_factory():
            yield Task(id=1, payload="A", priority=1, status=TaskStatus.TODO)
            yield Task(id=2, payload="B", priority=2, status=TaskStatus.TODO)
            
        queue = TaskQueue(my_factory)
        
        # Первый проход
        l1 = list(queue)
        # Второй проход
        l2 = list(queue)
        
        assert len(l1) == 2
        assert len(l2) == 2
        assert l1[0].id == l2[0].id
        
        
class TestLargeVolume:
    
    def test_iteration_speed_large_list(self, large_queue):
        """Проверка, что итерация по 100k задачам не зависает."""
        count = 0
        for _ in large_queue:
            count += 1
        assert count == 100_000
    
    def test_filter_for_large_queue(self, large_queue):
        
        count = 0
        filtered = large_queue.filter_by_status(TaskStatus.DONE) # Должно остаться 50к задач
        for _ in filtered:
            count += 1
            
        assert count == 50000
        
        # Пробежимся еще пару раз
        assert len(list(filtered)) == 50000
        assert len(list(filtered.filter_by_priority(highest_prior=1, lowest_prior=5))) == 20000
        
    