# Шаг 3. Сервис Event Store
# Чтобы выполнить второй пункт алгоритма («для онлайн-взаимодействия пользователя с 
# каким-то объектом можно использовать список похожих на него объектов»), необходим компонент, 
# умеющий сохранять и выдавать последние события пользователя, — это Event Store. 
# Реализуем его также в виде сервиса. В данном случае под взаимодействием пользователя с 
# объектом будем подразумевать любое положительное событие, например: просмотр страницы с книгой, лайк, добавление в избранное и т. п.
# Задание 3 из 6
# Дополните код сервиса так, чтобы он по методу /put сохранял пару значений user_id и item_id как событие, а по методу /get возвращал события (первыми — самые последние).
# Сохраните код сервиса в файле events_service.py.

# Шаг 4. Доработка сервиса рекомендаций
# Доработаем уже имеющийся код сервиса из предыдущего урока так, 
# чтобы он позволял получить онлайн-рекомендации для последнего события пользователя.
# Задание 4 из 6
# Дополните код нового метода так, чтобы для последнего события пользователя, 
# если оно есть, возвращался список похожих объектов. Это и будут онлайн-рекомендации.

# Шаг 5. Добавим разнообразия в онлайн-рекомендации
# Текущая реализация онлайн-рекомендаций позволяет получать их только для последнего события, 
# что очень просто и прямолинейно: если пользователь просмотрит новую книгу, то у него сменятся все онлайн-рекомендации.
# Задание 5 из 6
# Дополните новую версию реализации метода /recommendations_online так, чтобы онлайн-рекомендации возвращались для трёх последних событий.

# Задание 6 из 6
# Доработайте код обновлённого метода /recommendations так, чтобы реализовать предложенную выше схему блендинга.

from fastapi import FastAPI
import requests
from rec_sys_offline_utils_3 import rec_store

class EventStore:

    def __init__(self, max_events_per_user=10):

        self.events = {}
        self.max_events_per_user = max_events_per_user

    def put(self, user_id, item_id):
        """
        Сохраняет событие
        """

        user_events = self.events.get(user_id,[])
        self.events[user_id] = [item_id] + user_events[: self.max_events_per_user]

    def get(self, user_id, k):
        """
        Возвращает события для пользователя
        """
        user_events = self.events.get(user_id,[])

        return user_events

events_store = EventStore()

# создаём приложение FastAPI
app = FastAPI(title="events")

@app.post("/put")
async def put(user_id: int, item_id: int):
    """
    Сохраняет событие для user_id, item_id
    """

    events_store.put(user_id, item_id)

    return {"result": "ok"}


@app.post("/get")
async def get(user_id: int, k: int = 10):
    """
    Возвращает список последних k событий для пользователя user_id
    """

    events = events_store.get(user_id, k)

    return {"events": events}


@app.post("/recommendations")
async def recommendations(user_id: int, k: int = 100):
    """
    Возвращает список рекомендаций длиной k для пользователя user_id
    """

    recs_offline = await recommendations_offline(user_id, k)
    recs_online = await recommendations_online(user_id, k)

    recs_offline = recs_offline["recs"]
    recs_online = recs_online["recs"]

    recs_blended = []

    min_length = min(len(recs_offline), len(recs_online))
    # чередуем элементы из списков, пока позволяет минимальная длина
    for i in range(min_length):
        recs_blended.append(recs_online[i])
        recs_blended.append(recs_offline[i])

    # добавляем оставшиеся элементы в конец
    recs_blended.append(recs_offline[min_length:])
    recs_blended.append(recs_online[min_length:])

    # удаляем дубликаты
    recs_blended = dedup_ids(recs_blended)

    # оставляем только первые k рекомендаций
    recs_blended[:k]

    return {"recs": recs_blended}


@app.post("/recommendations_offline")
async def recommendations_offline(user_id: int, k: int = 100):
    """
    Возвращает список рекомендаций длиной k для пользователя user_id
    """
    recs = rec_store.get(user_id, k)

    return {"recs": recs}
    

@app.post("/recommendations_online")
async def recommendations_online(user_id: int, k: int = 100):
    """
    Возвращает список онлайн-рекомендаций длиной k для пользователя user_id
    """

    features_store_url = "http://127.0.0.1:8010"
    events_store_url = "http://127.0.0.1:8020"

    headers = {"Content-type": "application/json", "Accept": "text/plain"}

    # получаем последнее событие пользователя
    # получаем список последних событий пользователя, возьмём три последних
    params = {"user_id": user_id, "k": 3}
    print("params: ", params)
    resp = requests.post(events_store_url + "/get", headers=headers, params=params)
    events = resp.json()
    events = events["events"]

    print("events: ", events)

    # получаем список похожих объектов
        # получаем список айтемов, похожих на последние три, с которыми 
        # взаимодействовал пользователь

    items = []
    scores = []
    for item_id in events:
        # для каждого item_id получаем список похожих в item_similar_items
        if len(events) > 0:
            item_id = events[0]
            params = {"item_id": item_id, "k": k}
            print("params: ", params)
            response = requests.post(features_store_url +"/similar_items", headers=headers, params=params)
            if response.status_code == 200:
                item_similar_items = resp.json()
                recs = item_similar_items[:k]

                items += recs["item_id_2"]
                scores += recs["score"]
            else:
                item_similar_items = None
                print(f"status code: {response.status_code}")
                recs = []
        else:
            recs = []

    # сортируем похожие объекты по scores в убывающем порядке
    # для старта это приемлемый подход
    combined = list(zip(items, scores))
    combined = sorted(combined, key=lambda x: x[1], reverse=True)
    combined = [item for item, _ in combined]

    # удаляем дубликаты, чтобы не выдавать одинаковые рекомендации
    recs = dedup_ids(combined)

    return {"recs": recs}

def dedup_ids(ids):
    """
    Дедублицирует список идентификаторов, оставляя только первое вхождение
    """
    seen = set()
    ids = [id for id in ids if not (id in seen or seen.add(id))]

    return ids