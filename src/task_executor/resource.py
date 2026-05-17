import logging

logger = logging.getLogger(__name__)

class AsyncResource:
    """Асинхронный контекстный менеджер для управления внешними ресурсами."""
    
    def __init__(self) -> None:
        self.is_connected = False

    async def __aenter__(self) -> "AsyncResource":
        self.is_connected = True
        logger.info("Ресурс инициализирован")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        self.is_connected = False
        logger.info("Ресурс освобожден")