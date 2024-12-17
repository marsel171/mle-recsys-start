# Шаг 1. Шаблон сервиса
# Создадим шаблон сервиса, который пока что умеет только возвращать пустой список.

import logging
from fastapi import FastAPI
from contextlib import asynccontextmanager
from rec_sys_offline_utils_3 import rec_store

logger = logging.getLogger("uvicorn.error")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # код ниже (до yield) выполнится только один раз при запуске сервиса
    logger.info("Starting")
    yield
    # этот код выполнится только один раз при остановке сервиса
    logger.info("Stopping")
    
# создаём приложение FastAPI
app = FastAPI(title="recommendations", lifespan=lifespan)

@app.post("/recommendations")
async def recommendations(user_id: int, k: int = 100):
    """
    Возвращает список рекомендаций длиной k для пользователя user_id
    """

    # recs = []

    # Шаг 3. Интеграция
    # Интегрируем класс Recommendations в наш сервис для дальнейшего использования. 
    # Задание 3 из 3
    # Интегрируйте код класса Recommendations в код сервиса так, чтобы через метод /recommendations можно было получать рекомендации.
    recs = rec_store.get(user_id, k)

    return {"recs": recs}