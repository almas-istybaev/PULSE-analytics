# Pulse — Главная спецификация (Master Specification)

> **Версия**: 1.1.0  
> **Дата**: 2026-03-13  
> **Статус**: Полная спецификация Phase 1 (Post-Audit)  
> **Язык документа**: Русский  
> **Стек**: FastAPI + SQLite WAL + React 19 + Tailwind CSS v4

---

## Содержание

1. [Контекст и цели](#1-контекст-и-цели)
2. [Модуль 1: Основные финансовые отчёты](#2-модуль-1-основные-финансовые-отчёты)
3. [Модуль 2: Управление оборотным капиталом](#3-модуль-2-управление-оборотным-капиталом)
4. [Модуль 3: Складская и продажная эффективность](#4-модуль-3-складская-и-продажная-эффективность)
5. [Модуль 4: Юнит-экономика и клиентская аналитика](#5-модуль-4-юнит-экономика-и-клиентская-аналитика)
6. [Модуль 5: Управление цепями поставок](#6-модуль-5-управление-цепями-поставок)
7. [Модуль 6: Стратегическая рентабельность](#7-модуль-6-стратегическая-рентабельность)
8. [Модуль 7: Инвесторские показатели](#8-модуль-7-инвесторские-показатели)
9. [Модуль 8: Управленческие дашборды](#9-модуль-8-управленческие-дашборды)
10. [Модели данных](#10-модели-данных)
11. [Синхронизация МойСклад](#11-синхронизация-мойсклад)
12. [Безопасность и авторизация](#12-безопасность-и-авторизация)
13. [Обработка ошибок API](#13-обработка-ошибок-api)
14. [Pydantic-схемы](#14-pydantic-схемы)
15. [Кеширование и производительность](#15-кеширование-и-производительность)
16. [Экспорт отчётов](#16-экспорт-отчётов)
17. [Webhook-обработка](#17-webhook-обработка)
18. [Frontend-архитектура](#18-frontend-архитектура)
19. [DevOps и инфраструктура](#19-devops-и-инфраструктура)
20. [Глоссарий](#20-глоссарий)

---

## 1. Контекст и цели

### Миссия
Pulse — это B2B SaaS-платформа финансово-коммерческой аналитики для оптово-розничного бизнеса Казахстана, получающая данные напрямую из учётной системы МойСклад.

### Ключевые пользователи
| Роль | Потребность |
|------|-------------|
| **Генеральный директор** | Стратегические KPI, EBITDA, ROE |
| **Финансовый директор** | ОДДС, Баланс, Оборотный капитал |
| **Коммерческий директор** | Продажи, LTV/CAC, ABC-анализ клиентов |
| **Директор по закупкам** | OTIF, ABC/XYZ товаров, GMROI |
| **Инвестор** | CAPEX, ROE, Дивиденды |

### Принципы проектирования API
- **RESTful**: Ресурсно-ориентированные эндпоинты
- **Версионирование**: `/api/v1/`
- **Параметры периода**: Все отчёты принимают `start_date` и `end_date` (ISO 8601)
- **Пагинация**: Курсорная пагинация для списков (`cursor`, `limit`)
- **Кеш**: ETag + Cache-Control для тяжёлых отчётов
- **Формат чисел**: Decimal с 2 знаками для KZT, 4 знака для процентов

---

## 2. Модуль 1: Основные финансовые отчёты

### 2.1 ОДДС — Отчёт о движении денежных средств

**Бизнес-цель**: Анализ источников и использования денежных средств компании за период.

**Источник данных МойСклад**:
- `paymentin` — входящие платежи (от покупателей)
- `paymentout` — исходящие платежи (поставщикам, расходы)
- `cashin` — приходные кассовые ордера
- `cashout` — расходные кассовые ордера

**Структура отчёта по МСФО**:
```
ОДДС (Отчёт о движении денежных средств)
├── Операционная деятельность
│   ├── Поступления от покупателей
│   ├── Выплаты поставщикам
│   ├── Прочие операционные поступления
│   └── Прочие операционные выплаты
│   └── ИТОГО операционная деятельность (Net Operating CF)
├── Инвестиционная деятельность  
│   ├── Покупка основных средств (CAPEX)
│   ├── Поступления от продажи ОС
│   └── ИТОГО инвестиционная деятельность (Net Investing CF)
└── Финансовая деятельность
    ├── Поступления от займов
    ├── Погашение займов
    ├── Выплата дивидендов
    └── ИТОГО финансовая деятельность (Net Financing CF)
ИТОГОВОЕ ИЗМЕНЕНИЕ денежных средств
```

**API эндпоинты**:

```
GET /api/v1/financial/cash-flow
  Параметры:
    - start_date: date (обязательный)
    - end_date:   date (обязательный)
    - store_id:   uuid (опциональный, фильтр по магазину)
    - currency:   string = "KZT"
    - group_by:   enum["day","week","month"] = "month"

  Ответ:
    {
      "period": { "start": "2024-01-01", "end": "2024-12-31" },
      "currency": "KZT",
      "operating": {
        "inflows": [{ "category": "customers", "amount": 15000000 }],
        "outflows": [{ "category": "suppliers", "amount": 10000000 }],
        "net": 5000000
      },
      "investing": { "net": -2000000 },
      "financing": { "net": -500000 },
      "net_change": 2500000,
      "by_period": [{ "period": "2024-01", "net_operating": 400000, ... }]
    }
```

---

### 2.2 ОПиУ — Отчёт о прибылях и убытках

**Бизнес-цель**: Оценка прибыльности бизнеса за период.

**Источник данных МойСклад**:
- `demand` — отгрузки (выручка)
- `salesreturn` — возвраты от покупателей (корректировка выручки)
- `supply` — поставки (себестоимость)
- `purchasereturn` — возвраты поставщикам

**Формула**:
```
Выручка = SUM(demand.sum) - SUM(salesreturn.sum)
Себестоимость = SUM(demand.positions.buyPrice * demand.positions.quantity)
Валовая прибыль = Выручка - Себестоимость
Валовая маржа = Валовая прибыль / Выручка × 100%
EBIT = Валовая прибыль - Операционные расходы
EBITDA = EBIT + Амортизация
Чистая прибыль = EBIT - Налоги - Проценты по кредитам
```

**API эндпоинты**:
```
GET /api/v1/financial/income-statement
  Параметры:
    - start_date, end_date, store_id, currency, group_by, compare_prev_period: bool

  Ответ:
    {
      "revenue": { "gross": 15000000, "returns": 300000, "net": 14700000 },
      "cogs": 9000000,
      "gross_profit": { "amount": 5700000, "margin_pct": 38.78 },
      "operating_expenses": { "total": 1500000, "breakdown": [...] },
      "ebit": 4200000,
      "ebitda": 4500000,
      "depreciation": 300000,
      "interest_expense": 200000,
      "taxes": 840000,
      "net_profit": { "amount": 3160000, "margin_pct": 21.5 },
      "by_period": [...],
      "prev_period": { ... }  // если compare_prev_period=true
    }
```

---

### 2.3 Баланс — Балансовый отчёт

**Бизнес-цель**: Снимок финансового здоровья компании на дату.

**Структура**:
```
АКТИВЫ
├── Оборотные активы
│   ├── Денежные средства (paymentin - paymentout накопительно)
│   ├── Дебиторская задолженность (invoiceout без оплаты)
│   └── Запасы (stock × buyPrice)
└── Внеоборотные активы (вводятся вручную или через spendingcategory)

ПАССИВЫ
├── Краткосрочные обязательства
│   ├── Кредиторская задолженность (invoicein без оплаты)
│   └── Краткосрочные кредиты
└── Долгосрочные обязательства

СОБСТВЕННЫЙ КАПИТАЛ = АКТИВЫ - ОБЯЗАТЕЛЬСТВА
```

**Формулы расчёта**:
```
Денежные средства = SUM(paymentin.sum) + SUM(cashin.sum)
                   - SUM(paymentout.sum) - SUM(cashout.sum)
                   (кумулятивно от начала учёта до as_of_date)

Дебиторская задолженность = SUM(invoiceout.sum)
                           - SUM(связанных paymentin.sum)
                           WHERE invoiceout.moment <= as_of_date
                           AND NOT fully_paid

Запасы = SUM(stock.quantity × product.buyPrice)
         (из последнего StockSnapshot <= as_of_date)
         Группировка: по всем складам или по store_id

Кредиторская задолженность = SUM(invoicein.sum)
                            - SUM(связанных paymentout.sum)
                            WHERE invoicein.moment <= as_of_date
                            AND NOT fully_paid

Собственный капитал = Сумма активов - Сумма обязательств
```

**API эндпоинты**:
```
GET /api/v1/financial/balance-sheet
  Параметры: as_of_date: date (обязательный), currency

  Ответ:
    {
      "as_of_date": "2024-12-31",
      "assets": {
        "current": {
          "cash": 5000000,
          "receivables": 3000000,
          "inventory": 8000000,
          "total": 16000000
        },
        "non_current": { "total": 2000000 },
        "total": 18000000
      },
      "liabilities": {
        "current": { "payables": 4000000, "total": 4000000 },
        "non_current": { "total": 1000000 },
        "total": 5000000
      },
      "equity": 13000000
    }
```

---

## 3. Модуль 2: Управление оборотным капиталом

### 3.1 CCC — Цикл конвертации денежных средств

**Бизнес-цель**: Измерение времени от вложения денег в запасы до получения оплаты.

**Формулы**:
```
DIO (Days Inventory Outstanding) = (Средние запасы / Себестоимость) × Дни периода
DSO (Days Sales Outstanding)     = (Средняя деб. задолженность / Выручка) × Дни периода
DPO (Days Payable Outstanding)   = (Средняя кред. задолженность / Закупки) × Дни периода

CCC = DIO + DSO - DPO

Интерпретация:
  CCC < 0  = Отличное управление (деньги поступают до оплаты поставщикам)
  CCC 0-30 = Норма для оптовой торговли
  CCC > 60 = Риск кассовых разрывов
```

**API эндпоинты**:
```
GET /api/v1/working-capital/ccc
  Параметры: start_date, end_date, store_id

  Ответ:
    {
      "ccc_days": 23.5,
      "components": {
        "dio": { "days": 45.2, "avg_inventory": 8000000 },
        "dso": { "days": 32.1, "avg_receivables": 3000000 },
        "dpo": { "days": 53.8, "avg_payables": 4000000 }
      },
      "trend": [{ "period": "2024-01", "ccc_days": 28.5 }, ...],
      "benchmark": { "industry_avg": 30.0 }
    }
```

---

### 3.2 A/R Aging — Анализ дебиторской задолженности по срокам

**Бизнес-цель**: Выявление просроченной дебиторки и риска невозврата.

**Источник данных**: `invoiceout` без связанных `paymentin`.

**Группировка по срокам (buckets)**:
```
Текущая (0-30 дней)
Просрочка 31-60 дней
Просрочка 61-90 дней
Просрочка 91-120 дней
Критическая просрочка (> 120 дней)
```

**API эндпоинты**:
```
GET /api/v1/working-capital/ar-aging
  Параметры: as_of_date, currency, counterparty_id (опционально)

  Ответ:
    {
      "as_of_date": "2024-12-31",
      "total_outstanding": 3000000,
      "buckets": [
        { "label": "0-30 дней", "amount": 1800000, "pct": 60.0, "count": 45 },
        { "label": "31-60 дней", "amount": 600000, "pct": 20.0, "count": 12 },
        ...
      ],
      "top_debtors": [
        { "counterparty": "ТОО Алем Трейд", "amount": 500000, "days_overdue": 45 }
      ]
    }
```

---

### 3.3 A/P Aging — Анализ кредиторской задолженности

**Зеркальное отображение A/R для кредиторской задолженности.**

```
GET /api/v1/working-capital/ap-aging
  (аналогичная структура ответа)
```

---

## 4. Модуль 3: Складская и продажная эффективность

### 4.1 ABC/XYZ-анализ товаров

**Бизнес-цель**: Классификация товаров по вкладу в выручку и стабильности спроса.

**ABC по выручке**:
```
A: топ 80% выручки (как правило, 20% SKU)
B: следующие 15% выручки
C: оставшиеся 5% выручки
```

**XYZ по стабильности (коэффициент вариации)**:
```
X: CV < 10%  (стабильный, предсказуемый спрос)
Y: CV 10-25% (умеренно нестабильный)
Z: CV > 25%  (нестабильный, непредсказуемый)

CV = (Стандартное отклонение продаж / Среднее продаж) × 100%
```

**Матрица ABC/XYZ (9 сегментов)**:
```
     X (стабильный)   Y (умеренный)   Z (нестабильный)
A    AX — приоритет   AY — план        AZ — управлять
B    BX — норма       BY — мониторинг  BZ — оптимиз.
C    CX — авто        CY — пересмотр   CZ — ликвидация?
```

**API эндпоинты**:
```
GET /api/v1/inventory/abc-xyz
  Параметры: start_date, end_date, store_id, min_periods: int = 3

  Ответ:
    {
      "analysis_period": { "start": ..., "end": ..., "months": 12 },
      "summary": {
        "total_skus": 1250,
        "by_abc": { "A": 250, "B": 375, "C": 625 },
        "by_xyz": { "X": 400, "Y": 500, "Z": 350 }
      },
      "segments": {
        "AX": { "count": 120, "revenue_pct": 65.2, "items": [...] },
        ...
      },
      "items": [
        {
          "product_id": "uuid",
          "name": "Название товара",
          "abc_class": "A",
          "xyz_class": "X",
          "segment": "AX",
          "revenue": 1500000,
          "revenue_pct": 5.2,
          "cv": 7.3,
          "monthly_sales": [150000, 140000, ...]
        }
      ],
      "cursor": "next_page_cursor",
      "has_more": true
    }
```

---

### 4.2 GMROI — Gross Margin Return on Inventory Investment

**Бизнес-цель**: Измерение эффективности инвестиций в товарные запасы.

**Формула**:
```
GMROI = Валовая прибыль / Средние запасы (по себестоимости)

Интерпретация:
  GMROI > 2.0 = Хорошо (каждый тенге запасов приносит 2 тенге прибыли)
  GMROI 1-2   = Удовлетворительно
  GMROI < 1   = Неэффективно (запасы «съедают» прибыль)
```

**API эндпоинты**:
```
GET /api/v1/inventory/gmroi
  Параметры: start_date, end_date, store_id, category_id, group_by

  Ответ:
    {
      "overall": { "gmroi": 2.45, "gross_profit": 5700000, "avg_inventory": 2326530 },
      "by_category": [{ "name": "Электроника", "gmroi": 3.2, ... }],
      "by_product": [{ "product_id": "uuid", "name": "...", "gmroi": 4.1, ... }],
      "trend": [{ "period": "2024-01", "gmroi": 2.3 }, ...]
    }
```

---

## 5. Модуль 4: Юнит-экономика и клиентская аналитика

### 5.1 LTV/CAC — Пожизненная ценность клиента и стоимость привлечения

**Бизнес-цель**: Оценка долгосрочной прибыльности клиентской базы.

**Формулы**:
```
ARPU (средняя выручка/клиент/мес) = Выручка / Кол-во клиентов / Месяцы
Churn Rate = Отток клиентов за период / Клиенты начала периода
LTV = ARPU × Gross Margin % / Churn Rate
CAC = Маркетинг расходы / Новые клиенты (вводится вручную)
LTV/CAC Ratio = LTV / CAC (норма: > 3)
Payback Period = CAC / (ARPU × Gross Margin %)
```

**API эндпоинты**:
```
GET /api/v1/analytics/ltv-cac
  Параметры: start_date, end_date, segment_by: enum["region","category","channel"]

  Ответ:
    {
      "arpu": 125000,
      "churn_rate_pct": 8.5,
      "ltv": 570000,
      "cac": 20000,
      "ltv_cac_ratio": 28.5,
      "payback_months": 0.47,
      "by_segment": [...]
    }
```

```
POST /api/v1/analytics/cac-input
  Body:
    {
      "period": "2024-01",
      "channel": "direct",
      "spend": 500000,
      "new_customers": 25
    }

  Ответ: { "id": "uuid", "status": "created" }
```

---

### 5.2 Когортный анализ — Удержание клиентов

**Бизнес-цель**: Анализ удержания клиентов по когортам (месяц первой покупки).

**Алгоритм**:
```
1. Группировать клиентов по месяцу первой покупки (когорта)
2. Для каждой когорты считать % клиентов, вернувшихся в M+1, M+2, ...M+N
3. Построить треугольную матрицу удержания
```

**API эндпоинты**:
```
GET /api/v1/analytics/cohort-retention
  Параметры: cohort_start, cohort_end, max_months: int = 12

  Ответ:
    {
      "cohorts": [
        {
          "cohort_month": "2024-01",
          "initial_customers": 120,
          "retention": [100, 65, 50, 42, 38, 35, 33, ...]  // процент по месяцам
        },
        ...
      ],
      "avg_retention": [100, 58, 45, 40, 35, 32, 30, ...]
    }
```

---

## 6. Модуль 5: Управление цепями поставок

### 6.1 OTIF — On Time In Full

**Бизнес-цель**: Измерение надёжности выполнения заказов.

**Формулы**:
```
On Time = Заказы, доставленные в срок / Все заказы × 100%
In Full = Заказы, выполненные полностью / Все заказы × 100%
OTIF    = On Time AND In Full / Все заказы × 100%

Норма для B2B: OTIF > 95%
```

**Источник данных**:
- `customerorder` — планируемая дата отгрузки (`deliveryPlannedMoment`)
- `demand` — фактическая дата отгрузки (`moment`)
- `demand.positions` — фактические qty vs заказанные qty

**API эндпоинты**:
```
GET /api/v1/supply-chain/otif
  Параметры: start_date, end_date, store_id, counterparty_id

  Ответ:
    {
      "overall": { "otif_pct": 87.5, "on_time_pct": 91.2, "in_full_pct": 94.8 },
      "by_period": [...],
      "by_customer": [{ "name": "ТОО ...", "otif_pct": 72.0, "orders": 25 }],
      "failures": [{ "order_id": "...", "reason": "late|partial|both", "delay_days": 3 }]
    }
```

---

## 7. Модуль 6: Стратегическая рентабельность

### 7.1 EBITDA Margin

**Бизнес-цель**: Оценка операционной прибыльности до влияния финансирования и учётных решений.

**Формулы**:
```
EBITDA = Чистая прибыль + Процентные расходы + Налоги + Амортизация
       = EBIT + Амортизация

EBITDA Margin = EBITDA / Выручка × 100%

Ориентиры для торговли в Казахстане:
  < 5%    = Слабо
  5-10%   = Среднерыночно
  10-20%  = Хорошо
  > 20%   = Отлично
```

**API эндпоинты**:
```
GET /api/v1/profitability/ebitda
  Параметры: start_date, end_date, store_id, group_by, compare_periods

  Ответ:
    {
      "ebitda": 4500000,
      "ebitda_margin_pct": 15.2,
      "components": {
        "net_profit": 3160000,
        "interest": 200000,
        "taxes": 840000,
        "depreciation": 300000
      },
      "trend": [...],
      "bridge": [  // Waterfall chart данные
        { "label": "Выручка", "value": 14700000, "type": "total" },
        { "label": "Себестоимость", "value": -9000000, "type": "decrease" },
        { "label": "Операционные расходы", "value": -1500000, "type": "decrease" },
        { "label": "EBITDA", "value": 4500000, "type": "total" }
      ]
    }
```

---

## 8. Модуль 7: Инвесторские показатели

### 8.1 CAPEX-анализ

**Бизнес-цель**: Планирование и контроль капитальных вложений.

**Источник**: Исходящие платежи с тегом/категорией "CAPEX" в МойСклад.

```
GET /api/v1/investor/capex
  Параметры: start_date, end_date

  Ответ:
    {
      "total_capex": 2000000,
      "by_category": [{ "name": "Оборудование", "amount": 1500000 }],
      "by_period": [...],
      "capex_intensity": 6.8  // CAPEX / Выручка %
    }
```

---

### 8.2 ROE — Return on Equity

**Формула (DuPont)**:
```
ROE = Чистая прибыль / Средний собственный капитал × 100%

DuPont разложение:
ROE = Чистая маржа × Оборачиваемость активов × Финансовый рычаг
    = (Прибыль/Выручка) × (Выручка/Активы) × (Активы/Капитал)
```

```
GET /api/v1/investor/roe
  Ответ: { "roe_pct": 24.3, "dupont": { "net_margin": 21.5, "asset_turnover": 0.82, "leverage": 1.38 } }
```

---

### 8.3 Дивиденды

```
GET /api/v1/investor/dividends
  Источник: paymentout с тегом "dividends"
  Ответ: { "total": 1000000, "by_period": [...], "payout_ratio_pct": 31.6 }
```

---

## 9. Модуль 8: Управленческие дашборды

### 9.1 Финансовый дашборд (CFO)

**Виджеты**:
- KPI-карточки: Выручка, Валовая прибыль, EBITDA, Чистая прибыль (текущий месяц vs пред.)
- График ОДДС: Area chart по неделям
- Waterfall EBITDA Bridge
- A/R vs A/P Aging: Side-by-side bar charts
- Топ-10 должников / кредиторов

```
GET /api/v1/dashboards/financial
  Параметры: period_type: enum["month","quarter","year"], store_id

  Ответ: { "kpis": {...}, "cash_flow_chart": {...}, "aging": {...} }
```

---

### 9.2 Коммерческий дашборд (CCO)

**Виджеты**:
- KPI: Заказы, Средний чек, Новые клиенты, Конверсия повторных покупок
- График продаж: Line chart с прогнозом
- ABC Heat Map (матрица 3×3 ABC/XYZ)
- LTV/CAC Gauge
- Топ-20 товаров по выручке и марже
- Когортная таблица удержания (heat map)

```
GET /api/v1/dashboards/commercial
```

---

### 9.3 Логистический дашборд (Цепи поставок)

**Виджеты**:
- OTIF Gauge (красный/жёлтый/зелёный)
- GMROI по категориям: Bar chart
- CCC Trend: Line chart
- Просроченные поставки: Таблица с сортировкой
- Оборачиваемость запасов по складам

```
GET /api/v1/dashboards/logistics
```

---

## 10. Модели данных

### Ключевые SQLAlchemy-модели

```python
# Синхронизированные из МойСклад:
class Invoice(Base):          # invoiceout / invoicein
class Payment(Base):          # paymentin / paymentout
class Order(Base):            # customerorder / purchaseorder
class Demand(Base):           # demand (отгрузки)
class Supply(Base):           # supply (поставки)
class SalesReturn(Base):      # salesreturn (возвраты от покупателей)
class PurchaseReturn(Base):   # purchasereturn (возвраты поставщикам)
class CashIn(Base):           # cashin (приходные кассовые ордера)
class CashOut(Base):          # cashout (расходные кассовые ордера)
class Product(Base):          # product
class ProductFolder(Base):    # productfolder
class Counterparty(Base):     # counterparty (клиенты/поставщики)
class StockSnapshot(Base):    # Снимок запасов (ежедневный)
class SyncLog(Base):          # Лог синхронизации

# Вводимые вручную:
class ManualInput(Base):      # CAPEX, CAC, амортизация
class SyncState(Base):        # Cursor для инкрементальной синхронизации
```

### Общие поля для всех синхронизированных моделей
```python
moysklad_id: str (unique index)   # ID из МойСклад
moysklad_href: str                # meta.href
synced_at: datetime               # Последняя синхронизация
created_at: datetime              # Создан в МойСклад
updated_at: datetime              # Обновлён в МойСклад
```

---

## 11. Синхронизация МойСклад

### Стратегия

| Тип данных | Метод | Частота |
|-----------|-------|---------|
| Изменения сущностей | Webhook | Реал-тайм |
| Снимки запасов | Scheduled (Cron) | Ежедневно в 23:59 |
| Исторические данные | Full sync при первом запуске | Однократно |
| Инкрементальная синхр. | `updatedFrom` filter | Каждые 15 минут |

### Порядок первоначальной синхронизации

```
1. currencies        (справочник)
2. stores            (склады)
3. productfolders    (категории)
4. products          (товары)
5. counterparties    (клиенты/поставщики)
6. customerorders    (заказы покупателей, с пагинацией)
7. demands           (отгрузки)
8. invoiceout        (счета покупателям)
9. paymentin         (платежи от покупателей)
10. purchaseorders   (заказы поставщикам)
11. supply           (поставки)
12. invoicein        (счета поставщиков)
13. paymentout       (платежи поставщикам)
14. stock snapshot   (текущие остатки)
```

### Webhook-события для регистрации

```json
[
  { "entityType": "customerorder",  "action": ["CREATE", "UPDATE"] },
  { "entityType": "demand",         "action": ["CREATE", "UPDATE"] },
  { "entityType": "supply",         "action": ["CREATE", "UPDATE"] },
  { "entityType": "paymentin",      "action": ["CREATE", "UPDATE"] },
  { "entityType": "paymentout",     "action": ["CREATE", "UPDATE"] },
  { "entityType": "cashin",         "action": ["CREATE", "UPDATE"] },
  { "entityType": "cashout",        "action": ["CREATE", "UPDATE"] },
  { "entityType": "invoiceout",     "action": ["CREATE", "UPDATE"] },
  { "entityType": "invoicein",      "action": ["CREATE", "UPDATE"] },
  { "entityType": "salesreturn",    "action": ["CREATE", "UPDATE"] },
  { "entityType": "purchasereturn", "action": ["CREATE", "UPDATE"] },
  { "entityType": "counterparty",   "action": ["CREATE", "UPDATE", "DELETE"] },
  { "entityType": "product",        "action": ["CREATE", "UPDATE", "DELETE"] }
]
```

---

## 12. Безопасность и авторизация

### 12.1 Аутентификация (JWT)

| Параметр | Значение |
|----------|----------|
| **Алгоритм** | RS256 |
| **Access Token TTL** | 15 минут |
| **Refresh Token TTL** | 7 дней |
| **Хранение (frontend)** | HttpOnly cookie (предпочтительно) или in-memory |
| **Хранение (localStorage)** | ❌ Запрещено |

**API эндпоинты аутентификации**:
```
POST /api/v1/auth/login
  Body: { "email": "admin@pulse.kz", "password": "..." }
  Ответ: { "access_token": "...", "token_type": "bearer", "expires_in": 900 }

POST /api/v1/auth/refresh
  Body: { "refresh_token": "..." }
  Ответ: { "access_token": "...", "expires_in": 900 }

POST /api/v1/auth/logout
GET  /api/v1/auth/me → текущий пользователь с ролью
```

### 12.2 Авторизация (RBAC)

| Роль | Модули доступа |
|------|---------------|
| **admin** | Все модули + управление пользователями |
| **ceo** | Все отчёты (read-only) |
| **cfo** | Модули 1-3, 6-8, Дашборды |
| **cco** | Модули 3-5, Дашборды |
| **buyer** | Модули 3, 5, Дашборды |
| **investor** | Модули 6-8, Дашборды |

**Реализация**:
- Каждый роут ОБЯЗАН использовать `Depends(get_current_user)`
- Проверка роли через `Depends(require_role("cfo", "admin"))`
- Запрещены роуты без аутентификации (кроме `POST /auth/login`)

### 12.3 Защита API

| Мера | Реализация |
|------|-----------|
| **CORS** | Только конкретный origin (production URL) |
| **Rate Limiting** | 60 req/min на пользователя (`slowapi`) |
| **SQL-инъекции** | Только SQLAlchemy ORM, никаких raw-запросов |
| **XSS** | React по умолчанию, запрет `dangerouslySetInnerHTML` |
| **Секреты** | Все через `.env` + `pydantic-settings`, никаких `VITE_SECRET_*` |
| **Debug** | `DEBUG=False` в production |

---

## 13. Обработка ошибок API

### 13.1 Единый формат ответа ошибки

Все API-ошибки возвращаются в стандартном формате:

```json
{
  "error": {
    "code": "INVALID_PERIOD",
    "message": "end_date must be after start_date",
    "details": {
      "start_date": "2024-12-31",
      "end_date": "2024-01-01"
    }
  }
}
```

### 13.2 Стандартные HTTP-коды

| Код | Применение |
|-----|-----------|
| **400** | Невалидные параметры запроса |
| **401** | Отсутствует или истёк токен |
| **403** | Нет прав на данный модуль (RBAC) |
| **404** | Ресурс не найден |
| **422** | Ошибка валидации Pydantic |
| **429** | Rate limit exceeded |
| **500** | Внутренняя ошибка сервера |
| **503** | МойСклад API недоступен |

### 13.3 Коды ошибок бизнес-логики

```
INVALID_PERIOD         — end_date <= start_date
PERIOD_TOO_LONG        — Период > 366 дней
INSUFFICIENT_DATA      — Нет данных для расчёта (напр., нет отгрузок)
SYNC_IN_PROGRESS       — Синхронизация ещё не завершена
STORE_NOT_FOUND        — Указанный store_id не существует
MANUAL_INPUT_REQUIRED  — Для расчёта нужны ручные данные (CAPEX, CAC)
```

---

## 14. Pydantic-схемы

### 14.1 Общие параметры

```python
class PeriodParams(BaseModel):
    """Параметры периода для всех отчётов."""
    start_date: date
    end_date: date
    store_id: UUID | None = None
    currency: str = "KZT"

    @model_validator(mode="after")
    def validate_period(self) -> Self:
        if self.end_date <= self.start_date:
            raise ValueError("end_date must be after start_date")
        if (self.end_date - self.start_date).days > 366:
            raise ValueError("Period too long (max 366 days)")
        return self

class GroupByParams(PeriodParams):
    group_by: Literal["day", "week", "month"] = "month"
```

### 14.2 Маппинг эндпоинтов → схемы

| Эндпоинт | Request | Response |
|----------|---------|----------|
| `GET /financial/cash-flow` | `CashFlowParams(GroupByParams)` | `CashFlowResponse` |
| `GET /financial/income-statement` | `IncomeStatementParams(GroupByParams)` | `IncomeStatementResponse` |
| `GET /financial/balance-sheet` | `BalanceSheetParams` | `BalanceSheetResponse` |
| `GET /working-capital/ccc` | `PeriodParams` | `CCCResponse` |
| `GET /working-capital/ar-aging` | `AgingParams` | `AgingResponse` |
| `GET /working-capital/ap-aging` | `AgingParams` | `AgingResponse` |
| `GET /inventory/abc-xyz` | `ABCXYZParams(PeriodParams)` | `ABCXYZResponse` |
| `GET /inventory/gmroi` | `GMROIParams(GroupByParams)` | `GMROIResponse` |
| `GET /analytics/ltv-cac` | `LTVCACParams(PeriodParams)` | `LTVCACResponse` |
| `POST /analytics/cac-input` | `CACInputCreate` | `CACInputResponse` |
| `GET /analytics/cohort-retention` | `CohortParams` | `CohortResponse` |
| `GET /supply-chain/otif` | `OTIFParams(PeriodParams)` | `OTIFResponse` |
| `GET /profitability/ebitda` | `EBITDAParams(GroupByParams)` | `EBITDAResponse` |
| `GET /investor/capex` | `PeriodParams` | `CAPEXResponse` |
| `GET /investor/roe` | `PeriodParams` | `ROEResponse` |
| `GET /investor/dividends` | `PeriodParams` | `DividendsResponse` |
| `GET /dashboards/*` | `DashboardParams` | `DashboardResponse` |

### 14.3 Формат числовых значений

```python
# KZT суммы
amount: Decimal = Field(..., decimal_places=2, description="Сумма в KZT")

# Проценты
margin_pct: Decimal = Field(..., decimal_places=4, description="Процент (напр. 15.2345)")

# Дни
days: Decimal = Field(..., decimal_places=1, description="Дни (напр. 23.5)")
```

---

## 15. Кеширование и производительность

### 15.1 Стратегия кеширования

| Тип данных | Механизм | TTL | Инвалидация |
|-----------|----------|-----|------------|
| Завершённые периоды | `ETag + Cache-Control` | Immutable (1 год) | — |
| Текущий период | `Cache-Control: max-age` | 5 минут | При новой синхронизации |
| Дашборды | Server-side cache | 2 минуты | Webhook-триггер |
| Справочники (products, counterparties) | In-memory | 15 минут | При CRUD-операциях |

**Определение «завершённого периода»**: Месяц считается завершённым, если `now() > last_day_of_month + 1 day`.

### 15.2 Заголовки ответов

```
# Для завершённого периода (immutable):
Cache-Control: public, max-age=31536000, immutable
ETag: "sha256_of_response"

# Для текущего периода:
Cache-Control: private, max-age=300
ETag: "sha256_of_response"
```

### 15.3 Индексы SQLite

Обязательные индексы для оптимизации отчётов:
```sql
-- Быстрый поиск по moysklad_id
CREATE UNIQUE INDEX ix_<table>_moysklad_id ON <table>(moysklad_id);

-- Диапазонные запросы по дате
CREATE INDEX ix_demand_moment ON demand(moment);
CREATE INDEX ix_paymentin_moment ON paymentin(moment);
CREATE INDEX ix_paymentout_moment ON paymentout(moment);

-- Составные индексы для фильтров
CREATE INDEX ix_demand_store_moment ON demand(store_id, moment);
CREATE INDEX ix_invoiceout_paid_moment ON invoiceout(is_paid, moment);
```

---

## 16. Экспорт отчётов

### 16.1 Поддерживаемые форматы

| Формат | Библиотека | Применение |
|--------|-----------|-----------|
| **PDF** | `weasyprint` или `reportlab` | Формальные отчёты для руководства |
| **Excel (.xlsx)** | `openpyxl` | Данные для дальнейшего анализа |

### 16.2 API эндпоинты

```
GET /api/v1/export/{report_type}
  Параметры:
    - report_type: enum["cash-flow", "income-statement", "balance-sheet", "abc-xyz"]
    - format: enum["pdf", "xlsx"]
    - start_date, end_date, store_id
    - language: str = "ru"

  Ответ: binary file (Content-Type: application/pdf или application/vnd.openxmlformats)
```

### 16.3 Брендирование PDF

- Логотип компании (из ManualInput)
- Название компании, ИИН/БИН
- Дата генерации, период отчёта
- Нумерация страниц

---

## 17. Webhook-обработка

### 17.1 Приём webhook от МойСклад

```
POST /api/v1/sync/webhook
  Headers:
    - X-Lognex-Webhook-Signature: HMAC подпись
  Body: { "events": [{ "meta": {...}, "action": "CREATE", "accountId": "..." }] }
```

### 17.2 Верификация подписи

```python
import hmac, hashlib

def verify_webhook_signature(body: bytes, signature: str, secret: str) -> bool:
    """Проверка HMAC-SHA256 подписи от МойСклад."""
    expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)
```

### 17.3 Обработка событий

| Шаг | Действие |
|-----|---------|
| 1 | Верификация подписи |
| 2 | Парсинг `events[]` из тела запроса |
| 3 | Для каждого event: запрос актуальной сущности из МойСклад API |
| 4 | Upsert в SQLite (по `moysklad_id`) |
| 5 | Инвалидация кеша связанных отчётов |
| 6 | Ответ `200 OK` немедленно (обработка в фоне) |

### 17.4 Идемпотентность и устойчивость

- Повторная обработка одного события — безопасна (upsert)
- При ошибке обработки — записать в `SyncLog` со статусом `FAILED`
- Retry-очередь: повторять failed-события каждые 5 минут (макс. 3 попытки)

---

## 18. Frontend-архитектура

### 18.1 Atomic Design (структура компонентов)

```
src/
├── components/
│   ├── ui/            # Atoms: Button, Badge, Input, Spinner, Skeleton
│   ├── common/        # Molecules: KPICard, DateRangePicker, GlassCard, SearchBar
│   ├── charts/        # Organisms: WaterfallChart, HeatMap, LineChart, GaugeChart
│   └── layout/        # Templates: PageLayout, Sidebar, BottomNav, Header
├── features/
│   ├── financial/     # Страницы: CashFlow, IncomeStatement, BalanceSheet
│   ├── working-capital/
│   ├── inventory/
│   ├── analytics/
│   ├── supply-chain/
│   ├── profitability/
│   ├── investor/
│   └── dashboards/
├── hooks/             # Custom hooks: useReport, useDateRange, useExport
├── services/          # API layer: apiClient.ts, отдельные service-файлы
├── stores/            # Client state (Zustand / Context)
└── utils/             # Форматирование, валидация, constants
```

### 18.2 Паттерны React

| Паттерн | Правило |
|---------|---------|
| **Data Fetching** | Только через `@tanstack/react-query` (`useQuery`, `useInfiniteQuery`) |
| **Client State** | Минимум: `useState` для UI-state, `Zustand` для глобального |
| **Smart vs Dumb** | Pages/Features = Smart (фетчат), ui/common = Dumb (получают props) |
| **Custom Hooks** | Если `useQuery` дублируется — извлечь в `hooks/useReport.ts` |

### 18.3 Дизайн-система «Indigo Glass»

Все компоненты ОБЯЗАНЫ следовать дизайн-системе из `constitution.md` (раздел 4):
- **Тёмная тема** с mesh-градиентами
- **Glassmorphism** карточки (`glass-card` класс)
- **Micro-animations**: `fade-in`, `slide-up` на mount
- **Touch targets**: min 48×48px
- **Charts**: Recharts с кастомной темой (indigo-палитра)

### 18.4 Адаптивность виджетов дашборда

| Виджет | Mobile | Tablet | Desktop |
|--------|--------|--------|---------|
| KPI Cards | 2×2 grid | 4×1 row | 4×1 row |
| Charts | Full width, свайп | 1×2 grid | 2×2 grid |
| Tables | Скрыть колонки, bottom sheet для деталей | Горизонтальный scroll | Полная таблица |
| Filters | Bottom sheet | Sidebar | Inline |

---

## 19. DevOps и инфраструктура

### 19.1 Docker Compose

```yaml
services:
  backend:
    build: ./backend
    environment:
      - DATABASE_URL=sqlite+aiosqlite:///./data/pulse.db
    volumes:
      - db-data:/app/data
    networks:
      - internal

  frontend:
    build: ./frontend
    networks:
      - internal

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./certbot/conf:/etc/letsencrypt
    depends_on:
      - backend
      - frontend
    networks:
      - internal

volumes:
  db-data:

networks:
  internal:
    driver: bridge
```

### 19.2 Nginx конфигурация

```
/               → frontend (static build)
/api/v1/        → backend:8000 (FastAPI Uvicorn)
```

Обязательные заголовки безопасности:
- `server_tokens off`
- `X-Frame-Options: DENY`
- `X-Content-Type-Options: nosniff`
- `Strict-Transport-Security: max-age=31536000`

### 19.3 CI/CD (GitHub Actions)

| Событие | Действия |
|---------|---------|
| Push to `main` | Build → Test → Deploy to production |
| Pull Request | Lint → Type-check → Test |

### 19.4 UFW Firewall

Открытые порты на production-сервере:
- `22` (SSH)
- `80` (HTTP)
- `443` (HTTPS)
- Все остальные — `DENY`

---

## 20. Глоссарий

| Термин | Расшифровка | Модуль |
|--------|-------------|--------|
| **ОДДС** | Отчёт о движении денежных средств | 1 |
| **ОПиУ** | Отчёт о прибылях и убытках | 1 |
| **EBIT** | Earnings Before Interest and Taxes | 1, 6 |
| **EBITDA** | Earnings Before Interest, Taxes, Depreciation and Amortization | 1, 6 |
| **CCC** | Cash Conversion Cycle (цикл конвертации денежных средств) | 2 |
| **DIO** | Days Inventory Outstanding (оборачиваемость запасов в днях) | 2 |
| **DSO** | Days Sales Outstanding (дебиторка в днях) | 2 |
| **DPO** | Days Payable Outstanding (кредиторка в днях) | 2 |
| **A/R** | Accounts Receivable (дебиторская задолженность) | 2 |
| **A/P** | Accounts Payable (кредиторская задолженность) | 2 |
| **ABC/XYZ** | Классификация товаров по доходности (ABC) и стабильности (XYZ) | 3 |
| **GMROI** | Gross Margin Return on Inventory Investment | 3 |
| **CV** | Coefficient of Variation (коэффициент вариации) | 3 |
| **LTV** | Lifetime Value (пожизненная ценность клиента) | 4 |
| **CAC** | Customer Acquisition Cost (стоимость привлечения клиента) | 4 |
| **ARPU** | Average Revenue Per User (средний доход на клиента) | 4 |
| **Churn** | Показатель оттока клиентов | 4 |
| **OTIF** | On Time In Full (своевременность и полнота поставки) | 5 |
| **ROE** | Return on Equity (рентабельность собственного капитала) | 7 |
| **CAPEX** | Capital Expenditure (капитальные затраты) | 7 |
| **DuPont** | Метод декомпозиции ROE на 3 компонента | 7 |
| **KZT** | Казахстанский тенге (основная валюта) | — |
| **МСФО** | Международные стандарты финансовой отчётности | 1 |
