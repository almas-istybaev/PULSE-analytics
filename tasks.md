# Pulse — План реализации (Implementation Tasks)

> **Дата**: 2026-03-13
> **Базис**: spec.md v1.1.0 + constitution.md
> **Подход**: Spec-Driven Development (SDD) + TDD

---

## Phase 0: Инфраструктура и фундамент

- [ ] **0.1** Настроить SQLite WAL + все PRAGMA (включая `busy_timeout`)
- [ ] **0.2** Реализовать JWT-аутентификацию (`/api/v1/auth/*`)
  - [ ] RS256 ключи (генерация + хранение)
  - [ ] Login / Refresh / Logout / Me эндпоинты
  - [ ] `get_current_user` + `require_role()` dependencies
- [ ] **0.3** Реализовать RBAC (6 ролей: admin, ceo, cfo, cco, buyer, investor)
- [ ] **0.4** Настроить единый Error Handler (формат ошибок из sec. 13)
- [ ] **0.5** Создать базовые Pydantic-схемы (`PeriodParams`, `GroupByParams`)
- [ ] **0.6** Настроить CORS, Rate Limiting (`slowapi`), Security Headers
- [ ] **0.7** Frontend: Scaffolding Atomic Design (ui/, common/, charts/, layout/)
- [ ] **0.8** Frontend: Настроить `react-query`, роутинг, apiClient

---

## Phase 1: Синхронизация МойСклад (Модуль 11 + 17)

- [ ] **1.1** SQLAlchemy модели для всех 14 сущностей (см. sec. 10)
  - [ ] Invoice, Payment, Order, Demand, Supply
  - [ ] SalesReturn, PurchaseReturn, CashIn, CashOut
  - [ ] Product, ProductFolder, Counterparty
  - [ ] StockSnapshot, SyncLog, SyncState, ManualInput
- [ ] **1.2** Alembic миграции (initial + индексы из sec. 15.3)
- [ ] **1.3** МойСклад API клиент (`httpx`, async)
  - [ ] Аутентификация (Basic Auth)
  - [ ] Пагинация (limit/offset)
  - [ ] Retry-логика с exponential backoff
- [ ] **1.4** Full Sync (первоначальная синхронизация, 14 шагов по порядку)
- [ ] **1.5** Incremental Sync (APScheduler, каждые 15 мин, `updatedFrom`)
- [ ] **1.6** Webhook endpoint (`POST /api/v1/sync/webhook`)
  - [ ] HMAC-верификация подписи
  - [ ] Обработка 13 типов событий
  - [ ] Идемпотентный upsert
- [ ] **1.7** Daily Stock Snapshot (Cron, 23:59 Asia/Almaty)
- [ ] **1.8** Тесты: `test_sync.py` (mocked МойСклад API)

---

## Phase 2: Финансовые отчёты (Модуль 1)

- [ ] **2.1** ОДДС — Cash Flow
  - [ ] Repository: `CashFlowRepository`
  - [ ] Service: `CashFlowService` (группировка по МСФО-секциям)
  - [ ] Router: `GET /api/v1/financial/cash-flow`
  - [ ] Pydantic: `CashFlowParams`, `CashFlowResponse`
  - [ ] Тесты: `test_financial.py::test_cash_flow_*`
- [ ] **2.2** ОПиУ — Income Statement
  - [ ] Repository: `IncomeStatementRepository`
  - [ ] Service: `IncomeStatementService` (Выручка → COGS → Gross → EBITDA → Net)
  - [ ] Router: `GET /api/v1/financial/income-statement`
  - [ ] Pydantic: `IncomeStatementParams`, `IncomeStatementResponse`
  - [ ] compare_prev_period логика
  - [ ] Тесты
- [ ] **2.3** Баланс — Balance Sheet
  - [ ] Repository: `BalanceSheetRepository`
  - [ ] Service: `BalanceSheetService` (формулы из sec. 2.3)
  - [ ] Router: `GET /api/v1/financial/balance-sheet`
  - [ ] Тесты

---

## Phase 3: Оборотный капитал (Модуль 2)

- [ ] **3.1** CCC — Cash Conversion Cycle
  - [ ] Service: расчёт DIO, DSO, DPO
  - [ ] Router: `GET /api/v1/working-capital/ccc`
  - [ ] Тесты
- [ ] **3.2** A/R Aging — Дебиторская задолженность
  - [ ] Service: группировка по buckets (0-30, 31-60, 61-90, 91-120, >120)
  - [ ] Router: `GET /api/v1/working-capital/ar-aging`
  - [ ] Тесты
- [ ] **3.3** A/P Aging — Кредиторская задолженность
  - [ ] Router: `GET /api/v1/working-capital/ap-aging`
  - [ ] Тесты

---

## Phase 4: Складская и продажная эффективность (Модуль 3)

- [ ] **4.1** ABC/XYZ-анализ
  - [ ] Service: ABC-классификация по выручке (80/15/5)
  - [ ] Service: XYZ-классификация по CV (<10/10-25/>25)
  - [ ] Service: Матрица 9 сегментов
  - [ ] Router: `GET /api/v1/inventory/abc-xyz` (с курсорной пагинацией)
  - [ ] Тесты
- [ ] **4.2** GMROI
  - [ ] Service: Валовая прибыль / Средние запасы
  - [ ] Router: `GET /api/v1/inventory/gmroi`
  - [ ] Тесты

---

## Phase 5: Юнит-экономика и клиентская аналитика (Модуль 4)

- [ ] **5.1** LTV/CAC
  - [ ] Service: ARPU, Churn Rate, LTV, LTV/CAC Ratio, Payback Period
  - [ ] Router: `GET /api/v1/analytics/ltv-cac`
  - [ ] Router: `POST /api/v1/analytics/cac-input` (ручной ввод CAC)
  - [ ] Тесты
- [ ] **5.2** Когортный анализ
  - [ ] Service: Группировка по месяцу первой покупки → retention matrix
  - [ ] Router: `GET /api/v1/analytics/cohort-retention`
  - [ ] Тесты

---

## Phase 6: Цепи поставок (Модуль 5)

- [ ] **6.1** OTIF
  - [ ] Service: On Time %, In Full %, OTIF %
  - [ ] Router: `GET /api/v1/supply-chain/otif`
  - [ ] Тесты

---

## Phase 7: Стратегическая рентабельность (Модуль 6)

- [ ] **7.1** EBITDA Margin
  - [ ] Service: EBITDA, Margin %, Bridge (waterfall)
  - [ ] Router: `GET /api/v1/profitability/ebitda`
  - [ ] Тесты

---

## Phase 8: Инвесторские показатели (Модуль 7)

- [ ] **8.1** CAPEX-анализ
  - [ ] Router: `GET /api/v1/investor/capex`
- [ ] **8.2** ROE (DuPont)
  - [ ] Router: `GET /api/v1/investor/roe`
- [ ] **8.3** Дивиденды
  - [ ] Router: `GET /api/v1/investor/dividends`
- [ ] Тесты: `test_investor.py`

---

## Phase 9: Управленческие дашборды (Модуль 8)

- [ ] **9.1** Финансовый дашборд (CFO)
  - [ ] Backend: агрегированный endpoint
  - [ ] Frontend: KPI-карточки, ОДДС Area Chart, EBITDA Waterfall, A/R vs A/P
- [ ] **9.2** Коммерческий дашборд (CCO)
  - [ ] Frontend: График продаж, ABC HeatMap, LTV/CAC Gauge, Когортная таблица
- [ ] **9.3** Логистический дашборд
  - [ ] Frontend: OTIF Gauge, GMROI Bar Chart, CCC Trend Line

---

## Phase 10: Экспорт и кеширование (Модули 15-16)

- [ ] **10.1** Кеширование: ETag + Cache-Control (immutable vs текущий период)
- [ ] **10.2** Экспорт PDF (weasyprint/reportlab)
- [ ] **10.3** Экспорт Excel (openpyxl)
- [ ] **10.4** Router: `GET /api/v1/export/{report_type}`

---

## Phase 11: PWA и финальная полировка

- [ ] **11.1** PWA Manifest + Service Worker (vite-plugin-pwa)
- [ ] **11.2** Mobile Bottom Navigation (5 разделов)
- [ ] **11.3** Skeleton Loading для всех отчётов
- [ ] **11.4** Infinite Scroll для списков товаров/клиентов
- [ ] **11.5** Dark mode micro-animations (Indigo Glass)

---

## Phase 12: DevOps и деплой

- [ ] **12.1** Docker Compose: backend + frontend + nginx
- [ ] **12.2** Nginx: reverse proxy + security headers + SSL
- [ ] **12.3** GitHub Actions CI/CD pipeline
- [ ] **12.4** UFW firewall (22, 80, 443)
- [ ] **12.5** Production `.env` + secrets management
