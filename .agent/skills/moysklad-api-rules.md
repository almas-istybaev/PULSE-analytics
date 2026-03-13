---
name: moysklad-api-rules
description: Правила работы с МойСклад JSON API 1.2 — rate limiting, expand, обработка ошибок
---

# МойСклад API Rules

## Основные ограничения API

| Параметр | Значение |
|----------|----------|
| Лимит запросов | 100 запросов/минута |
| Макс. размер страницы | 1000 объектов |
| Базовый URL | `https://api.moysklad.ru/api/remap/1.2` |
| Аутентификация | Bearer Token (заголовок `Authorization`) |
| Формат данных | JSON (UTF-8) |

---

## Обязательная обработка Rate Limit (HTTP 429)

Каждый HTTP-клиент МойСклад ОБЯЗАН реализовывать экспоненциальный backoff.

```python
import asyncio
import httpx
from typing import Any

MOYSKLAD_BASE_URL = "https://api.moysklad.ru/api/remap/1.2"
MAX_RETRIES = 5
BASE_DELAY = 1.0  # секунд
MAX_DELAY = 60.0  # секунд

async def moysklad_request(
    client: httpx.AsyncClient,
    method: str,
    endpoint: str,
    **kwargs: Any,
) -> dict[str, Any]:
    """Выполняет запрос к МойСклад API с экспоненциальным backoff.

    Args:
        client: Настроенный httpx.AsyncClient с заголовками авторизации.
        method: HTTP-метод (GET, POST, PUT, DELETE).
        endpoint: Путь эндпоинта (например, "/entity/customerorder").
        **kwargs: Дополнительные параметры для httpx.

    Returns:
        Словарь с ответом от API.

    Raises:
        httpx.HTTPStatusError: При ошибке API после исчерпания попыток.
        MoySkladRateLimitError: При превышении лимита запросов.
    """
    url = f"{MOYSKLAD_BASE_URL}{endpoint}"

    for attempt in range(MAX_RETRIES):
        response = await client.request(method, url, **kwargs)

        if response.status_code == 429:
            # Уважаем Retry-After заголовок если есть
            retry_after = response.headers.get("Retry-After")
            delay = float(retry_after) if retry_after else min(
                BASE_DELAY * (2 ** attempt), MAX_DELAY
            )
            await asyncio.sleep(delay)
            continue

        if response.status_code == 503:
            # Временная недоступность сервера
            delay = min(BASE_DELAY * (2 ** attempt), MAX_DELAY)
            await asyncio.sleep(delay)
            continue

        response.raise_for_status()
        return response.json()

    raise MoySkladRateLimitError(
        f"Превышен лимит запросов после {MAX_RETRIES} попыток"
    )
```

---

## Правила использования параметра `expand`

**ВСЕГДА** раскрывать вложенные мета-сущности через `expand=`, а не делать дополнительные HTTP-запросы.

```python
# ❌ Запрещено — N+1 запросов:
orders = await fetch_orders()
for order in orders:
    agent = await fetch_agent(order["agent"]["meta"]["href"])  # Отдельный запрос!

# ✅ Правильно — один запрос с expand:
orders = await fetch_orders(
    params={
        "expand": "agent,positions,positions.assortment,store",
        "limit": 1000,
    }
)
# Данные agent уже доступны: order["agent"]["name"]
```

### Часто используемые expand-цепочки:

| Сущность | Рекомендуемый expand |
|----------|---------------------|
| Заказы покупателей | `agent,positions,positions.assortment,state,store` |
| Входящие платежи | `agent,operations` |
| Отгрузки | `agent,positions,positions.assortment,demand` |
| Счета (invoice) | `agent,positions,positions.assortment` |
| Товары | `productFolder,supplier,images` |
| Возвраты | `agent,positions,positions.assortment,demand` |

---

## Пагинация — обработка больших выборок

```python
async def fetch_all_entities(
    client: httpx.AsyncClient,
    endpoint: str,
    params: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Загружает все сущности с автоматической пагинацией.

    МойСклад лимитирует выборку на 1000 объектов за запрос.
    Функция автоматически итерирует через все страницы.

    Args:
        client: HTTP-клиент МойСклад.
        endpoint: Путь к эндпоинту.
        params: Дополнительные параметры запроса.

    Returns:
        Список всех объектов по всем страницам.
    """
    all_rows: list[dict[str, Any]] = []
    offset = 0
    limit = 1000

    while True:
        query_params = {**(params or {}), "limit": limit, "offset": offset}
        data = await moysklad_request(client, "GET", endpoint, params=query_params)
        rows = data.get("rows", [])
        all_rows.extend(rows)

        meta = data.get("meta", {})
        total = meta.get("size", 0)

        if offset + limit >= total:
            break

        offset += limit
        # Небольшая задержка для уважения rate limit
        await asyncio.sleep(0.1)

    return all_rows
```

---

## Обработка дат МойСклад

МойСклад возвращает даты в формате `2024-01-15 10:30:00.000` (UTC+5 Алматы).

```python
from datetime import datetime, timezone
import pytz

ALMATY_TZ = pytz.timezone("Asia/Almaty")

def parse_moysklad_date(date_str: str) -> datetime:
    """Парсит дату из формата МойСклад в UTC datetime.

    Args:
        date_str: Строка даты из API МойСклад.

    Returns:
        datetime объект в UTC.
    """
    # МойСклад возвращает время в UTC
    dt = datetime.strptime(date_str[:19], "%Y-%m-%d %H:%M:%S")
    return dt.replace(tzinfo=timezone.utc)
```

---

## Типы сущностей и их эндпоинты

```python
# Эндпоинты для ключевых сущностей Pulse:
ENDPOINTS = {
    # Финансы
    "customer_orders":    "/entity/customerorder",
    "invoices_out":       "/entity/invoiceout",
    "payments_in":        "/entity/paymentin",
    "payments_out":       "/entity/paymentout",
    "demands":            "/entity/demand",      # Отгрузки
    "returns_in":         "/entity/salesreturn", # Возвраты

    # Закупки
    "purchase_orders":    "/entity/purchaseorder",
    "invoices_in":        "/entity/invoicein",
    "supply":             "/entity/supply",       # Поставки

    # Склад
    "products":           "/entity/product",
    "product_folders":    "/entity/productfolder",
    "stock_current":      "/report/stock/all/current",
    "stock_by_store":     "/report/stock/bystore",

    # Справочники
    "agents":             "/entity/counterparty",
    "employees":          "/entity/employee",
    "stores":             "/entity/store",
    "currencies":         "/entity/currency",

    # Аналитика (агрегации)
    "turnover":           "/report/turnover/all",
    "profit_by_product":  "/report/profit/byproduct",
    "profit_by_employee": "/report/profit/byemployee",
}
```

---

## Работа с Webhook МойСклад

```python
# Конфигурация веб-хуков — обязательные поля:
WEBHOOK_CONFIG = {
    "url": "https://your-domain.kz/api/v1/webhooks/moysklad",
    "action": "CREATE",          # или UPDATE, DELETE
    "entityType": "customerorder",
    "enabled": True,
    "diffType": "FIELDS",        # Передавать изменённые поля
}

# Верификация входящих событий:
def verify_webhook_signature(payload: bytes, signature: str, secret: str) -> bool:
    """Проверяет подпись входящего веб-хука МойСклад."""
    import hmac, hashlib
    expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)
```

---

## Обязательные правила

1. **Rate Limit**: Всегда использовать экспоненциальный backoff при HTTP 429.
2. **Expand**: Никогда не делать N+1 запросов — использовать `expand=`.
3. **Пагинация**: Всегда обрабатывать пагинацию при `limit < total`.
4. **Asyncio**: Использовать `asyncio.sleep()` (не `time.sleep()`).
5. **Логирование**: Логировать каждый retry-attempt с уровнем WARNING.
6. **Таймауты**: Всегда устанавливать `timeout=30` для httpx.AsyncClient.
7. **Синхронизация**: Сохранять `moysklad_id` (из `meta.href`) во всех моделях БД.
8. **Webhook**: Верифицировать подпись перед обработкой событий.
