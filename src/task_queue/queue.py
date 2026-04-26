from typing import Iterator, Callable, Optional, Any, Iterable, Union
from src.task.task import Task, TaskStatus

DataSource = Union[Iterable[Task], Callable[[], Iterator[Task]]]

class TaskQueue:
    """
    Ленивая коллекция (очередь) задач.
    Поддерживает итерацию, повторный обход и ленивую фильтрацию.
    Не хранит промежуточные результаты в памяти.
    """
    def __init__(self, source: DataSource):
        """
        Принимает любой итерируемый объект: list, generator, другой TaskQueue.
        """
        self._source = source

    def __iter__(self) -> Iterator[Task]:
        """
        Возвращает НОВЫЙ итератор если source Итерируем,
        Или, если атрибут Callable, вернет результат
        """
        if callable(self._source):
            return self._source()
        else:
            return iter(self._source)
    
    def __str__(self):
        output: str = ""
        num = 1
        for task in self._source:
            output += f"[{num}] id: {task.id}; payload: {task.payload}; priority: {task.priority}; status: {task.status}\n"
            num += 1
        return output

    
    def filter_by_status(self, status: TaskStatus) -> 'TaskQueue':
        """
        Ленивый фильтр. Возвращает новую очередь.
        Использует фабрику, чтобы обеспечить повторный обход.
        """
        # Запоминаем текущий источник в замыкании
        current_source = self._source
        
        def _factory():
            # Эта функция будет вызываться при каждом __iter__ новой очереди
            for task in TaskQueue(current_source): # Рекурсивно используем логику итерации
                if task.status == status:
                    yield task
                    
        return TaskQueue(_factory)

    def filter_by_priority(self, highest_prior: int = 1, lowest_prior: int = 10) -> "TaskQueue":
        """Ленивый фильтр по минимальному приоритету."""
        current_source = self._source
        
        def _factory():
            for task in TaskQueue(current_source):
                if task.priority >= highest_prior and task.priority <= lowest_prior:
                    yield task
        
        return TaskQueue(_factory)
    
    def reg_filter_by_payload(self, pattern: str):
        "Ленивый фильтр содержимого payload задачи"
        current_source = self._source
        
        def _factory():
            for task in TaskQueue(current_source):
                if pattern in str(task.payload):
                    yield task
        
        return TaskQueue(_factory)
    
    def reg_filter_by_id(self, pattern: str):
        "Ленивый фильтр содержимого в айди задачи"
        current_source = self._source
        
        def _factory():
            for task in TaskQueue(current_source):
                if pattern in str(task.id):
                    yield task
        
        return TaskQueue(_factory)
    
    
        

    def filter(self, predicate: Callable[[Task], bool]) -> "TaskQueue":
        """Универсальный ленивый фильтр. Принимает функцию-проверку"""
        current_source = self._source
        
        def _factory():
            
            for task in TaskQueue(current_source):
                if predicate(task):
                    yield task
        return TaskQueue(_factory)

    # Опционально: удобные методы-агрегаторы
    def to_list(self) -> list[Task]:
        return list(self)

    def count(self) -> int:
        return sum(1 for _ in self)
    












if __name__ == "__main__":
    task1 = Task(id=1, payload="строка", priority=4, status=TaskStatus.TODO)
    task2 = Task(id="123", payload=42, priority=8, status=TaskStatus.TODO)
    task3 = Task(id=3.14, payload={"key": "value"}, priority=5, status=TaskStatus.TODO)
    task4 = Task(id=1, payload="строка", priority=4, status=TaskStatus.TODO)


    tasks = [task1, task2, task3, task4]
    queue = TaskQueue(tasks)
    filt = queue.filter_by_priority(5)
    for task in filt:
        print(task)

    print(list(filt))