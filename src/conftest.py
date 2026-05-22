import pytest

# Настраиваем режим asyncio для всех тестов
pytest_plugins = ['pytest_asyncio']

@pytest.fixture(scope="session")
def event_loop():
    """Создает экземпляр event loop для всей сессии тестов."""
    import asyncio
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()