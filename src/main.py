from src.task_sources.generator_source import *
from src.task_collector.collector import demo_collector
from src.task.descriptor import (
    InvalidPriorityError, 
    InvalidStatusError, 
    InvalidPayloadError,
    InvalidIdError
)
from src.task.task import Task, TaskStatus

def print_separator(title):
    print(f"\n{'='*60}")
    print(f" {title}")
    print('='*60)

def demo_descriptor():
    print("--- ДЕМОНСТРАЦИЯ РАБОТЫ ДЕСКРИПТОРОВ ---")

    # 1. Успешное создание корректной задачи
    print("\n1. Создание корректной задачи:")
    try:
        task = Task(
            id=101,
            payload="Изучить дескрипторы",
            priority=5,
            status=TaskStatus.TODO
        )
        print(f"   Задача создана успешно!")
        print(f"   ID: {task.id} (тип: {type(task.id).__name__})")
        print(f"   Priority: {task.priority}")
        print(f"   Status: {task.status.value}")
        print(f"   Payload: {task.payload}")
    except Exception as e:
        print(f"   Ошибка: {e}")

    # 2. Демонстрация валидации PriorityDescriptor
    print_separator("2. Тестирование PriorityDescriptor")
    
    # А. Некорректный тип (строка вместо int)
    print("\nА. Попытка установить приоритет строкой 'high':")
    try:
        task.priority = "high"
    except InvalidPriorityError as e:
        print(f"   [ОЖИДАЕМО] Перехвачено исключение: {e}")

    # Б. Выход за диапазон (слишком большой)
    print("\nБ. Попытка установить приоритет 15 (максимум 10):")
    try:
        task.priority = 15
    except InvalidPriorityError as e:
        print(f"   [ОЖИДАЕМО] Перехвачено исключение: {e}")

    # В. Выход за диапазон (слишком маленький)
    print("\nВ. Попытка установить приоритет 0 (минимум 1):")
    try:
        task.priority = 0
    except InvalidPriorityError as e:
        print(f"   [ОЖИДАЕМО] Перехвачено исключение: {e}")

    # 3. Демонстрация валидации StatusDescriptor
    print_separator("3. Тестирование StatusDescriptor")
    
    print("\nА. Попытка установить статус строкой 'todo' (нужен Enum):")
    try:
        task.status = "todo"
    except InvalidStatusError as e:
        print(f"   [ОЖИДАЕМО] Перехвачено исключение: {e}")

    print("\nБ. Корректная смена статуса через Enum:")
    task.status = TaskStatus.IN_PROGRESS
    print(f"   Статус успешно изменен на: {task.status.value}")

    # 4. Демонстрация валидации PayloadDescriptor
    print_separator("4. Тестирование PayloadDescriptor")
    
    print("\nА. Попытка установить пустой payload:")
    try:
        task.payload = ""
    except InvalidPayloadError as e:
        print(f"   [ОЖИДАЕМО] Перехвачено исключение: {e}")

    print("\nБ. Попытка установить None в payload:")
    try:
        task.payload = None
    except InvalidPayloadError as e:
        print(f"   [ОЖИДАЕМО] Перехвачено исключение: {e}")

    # # 5. Демонстрация IDDescriptor (нормализация типов)
    # print_separator("5. Тестирование IDDescriptor")
    
    # print("\nА. Создание задачи с числовым ID:")
    # t_num = Task(id=55, payload="Test", priority=5, status=TaskStatus.TODO)
    # print(f"   ID: {t_num.id} (тип внутри: {type(t_num.id).__name__})") # Должен стать str
    
    # print("\nБ. Создание задачи со строковым ID:")
    # t_str = Task(id="ABC-123", payload="Test", priority=5, status=TaskStatus.TODO)
    # print(f"   ID: {t_str.id} (тип внутри: {type(t_str.id).__name__})")


def main():
    demo_collector()
    demo_descriptor()


if __name__ == "__main__":
    main()
