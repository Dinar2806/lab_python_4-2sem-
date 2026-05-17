from dataclasses import dataclass, field
from typing import Any, Union
from enum import Enum
from datetime import datetime, timezone,timedelta

from src.task.descriptor import *

class TaskStatus(Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"

@dataclass
class Task:
    task_type = "default"
    
    id: str = IDDescriptor()
    
    created_at: str = field(default_factory=lambda: datetime.now(timezone(timedelta(hours=3))))
    
    priority: int = PriorityDescriptor()
    status: Enum = StatusDescriptor(TaskStatus, TaskStatus.TODO)
    payload: Any = PayloadDescriptor(default_value="default")
    
    
    
    
    # Вычисляемое свойство: готовность к выполнению
    @property
    def ready_to_perform(self):
        return self.status == TaskStatus.TODO and self.payload is not None
    
    
        

    def __post_init__(self):
        """
        Валидация данных после инициализации
        """
        if self.id is None:
            raise ValueError("ID задачи не может быть None")
        
    def __str__(self):
        return f"Task(id={self.id}, payload={self.payload})"
        
    def to_dict(self) -> dict:
        dict = {
            "id": self.id,
            "payload":  self.payload
        }
        return dict
    

