# Конституция проекта Pulse

> Этот документ является главным архитектурным законом платформы Pulse.
> Все решения по дизайну, коду и интеграциям ДОЛЖНЫ соответствовать этому документу.
> Нарушение конституции является блокирующим ревью.

---

## 1. Идентификация проекта

| Параметр | Значение |
|----------|----------|
| **Название** | Pulse — Финансово-коммерческая аналитика |
| **Целевая аудитория** | Оптово-розничный бизнес Казахстана |
| **Язык UI** | Русский |
| **Язык кода** | Английский |
| **Временная зона** | Asia/Almaty (UTC+5) |
| **Валюта** | KZT (с поддержкой USD, EUR) |
| **Методология** | Spec-Driven Development (SDD) |

---

## 2. Технологический стек

### Backend

```
Python         3.12+
FastAPI        0.115+      (Async, с Lifespan events)
Uvicorn        0.30+       (ASGI server)
SQLAlchemy     2.0+        (asyncio mode, mapped_column)
Alembic        1.13+       (автогенерация миграций)
httpx          0.27+       (async HTTP для МойСклад API)
pydantic       2.7+        (settings + schemas)
pydantic-settings 2.3+
python-jose    3.3+        (JWT)
passlib        1.7+        (bcrypt хэши)
apscheduler    3.10+       (фоновые задачи синхронизации)
```

### Frontend

```
Node.js        20+ (LTS)
React          19+         (использовать как React 20-style)
Vite           6+
Tailwind CSS   4.x         (строго utility-first, без JIT legacy)
Lucide React   0.400+      (иконки)
Recharts       2.12+       (графики и диаграммы)
Framer Motion  11+         (micro-animations)
@tanstack/react-query 5+  (серверное состояние, кеш, infinite scroll)
react-router-dom 6+
@tanstack/react-virtual     (виртуализация списков для infinite scroll)
```

### База данных

```
SQLite 3.45+
WAL (Write-Ahead Logging) — ОБЯЗАТЕЛЬНО
Strict mode PRAGMA
Async driver: aiosqlite
```

### Infrastructure

```
Nginx          (reverse proxy)
GitHub Actions (CI/CD)
```

---

## 3. Конфигурация SQLite WAL

Каждое подключение к базе данных ОБЯЗАНО устанавливать следующие PRAGMA при старте:

```python
from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import create_async_engine

DATABASE_URL = "sqlite+aiosqlite:///./pulse.db"

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
)

@event.listens_for(engine.sync_engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Настройка SQLite PRAGMA при каждом подключении."""
    cursor = dbapi_connection.cursor()
    # WAL режим для конкурентного чтения/записи
    cursor.execute("PRAGMA journal_mode=WAL")
    # Синхронизация — баланс производительности и надёжности
    cursor.execute("PRAGMA synchronous=NORMAL")
    # Размер кеша — 64 МБ
    cursor.execute("PRAGMA cache_size=-65536")
    # Внешние ключи
    cursor.execute("PRAGMA foreign_keys=ON")
    # Таймаут при блокировке для конкурентного доступа
    cursor.execute("PRAGMA busy_timeout=5000")
    # Оптимизатор мемори-мэп
    cursor.execute("PRAGMA mmap_size=268435456")
    # Временные таблицы в памяти
    cursor.execute("PRAGMA temp_store=MEMORY")
    cursor.close()
```

---

## 4. Дизайн-система «Indigo Glass»

### 4.1 Концепция

**Indigo Glass** — высококонтрастная тёмная тема с:
- **Mesh gradients**: Фоновые градиентные сетки (indigo + violet + slate)
- **Glassmorphism**: Полупрозрачные компоненты с `backdrop-blur`
- **Micro-animations**: Плавные переходы 200-400ms на все интерактивные элементы
- **Неон-акценты**: Тонкие свечения на primary-элементах

### 4.2 Переменные темы (Tailwind CSS v4 `@theme`)

```css
@theme {
  /* === ЦВЕТОВАЯ ПАЛИТРА === */

  /* Основные цвета — Indigo */
  --color-primary-50:  #eef2ff;
  --color-primary-100: #e0e7ff;
  --color-primary-200: #c7d2fe;
  --color-primary-300: #a5b4fc;
  --color-primary-400: #818cf8;
  --color-primary-500: #6366f1;  /* Основной */
  --color-primary-600: #4f46e5;
  --color-primary-700: #4338ca;
  --color-primary-800: #3730a3;
  --color-primary-900: #312e81;
  --color-primary-950: #1e1b4b;

  /* Фоновые цвета — Slate dark */
  --color-bg-base:     #020617;  /* slate-950 */
  --color-bg-surface:  #0f172a;  /* slate-900 */
  --color-bg-elevated: #1e293b;  /* slate-800 */
  --color-bg-glass:    rgba(15, 23, 42, 0.6);

  /* Акценты */
  --color-accent-violet: #7c3aed;
  --color-accent-cyan:   #06b6d4;
  --color-accent-emerald:#10b981;
  --color-accent-amber:  #f59e0b;
  --color-accent-rose:   #f43f5e;

  /* Текст */
  --color-text-primary:  #f1f5f9;  /* slate-100 */
  --color-text-secondary:#94a3b8;  /* slate-400 */
  --color-text-muted:    #475569;  /* slate-600 */

  /* Границы */
  --color-border-glass:  rgba(99, 102, 241, 0.2);
  --color-border-subtle: rgba(148, 163, 184, 0.1);

  /* === ТИПОГРАФИКА === */
  --font-display: "Inter", "SF Pro Display", system-ui, sans-serif;
  --font-mono:    "JetBrains Mono", "Fira Code", monospace;

  /* === ЭФФЕКТЫ === */
  --blur-glass:   blur(16px);
  --blur-heavy:   blur(32px);

  /* Mesh gradient — фоновый узор */
  --gradient-mesh:
    radial-gradient(at 20% 20%, hsla(252, 100%, 25%, 0.4) 0px, transparent 50%),
    radial-gradient(at 80% 0%,  hsla(263, 100%, 30%, 0.3) 0px, transparent 50%),
    radial-gradient(at 0%  50%, hsla(244, 100%, 20%, 0.3) 0px, transparent 50%),
    radial-gradient(at 80% 50%, hsla(273, 100%, 25%, 0.2) 0px, transparent 50%),
    radial-gradient(at 0% 100%, hsla(252, 100%, 20%, 0.3) 0px, transparent 50%),
    radial-gradient(at 70% 90%, hsla(240, 100%, 15%, 0.4) 0px, transparent 50%);

  /* === АНИМАЦИИ === */
  --animate-fade-in:    fade-in 200ms ease-out;
  --animate-slide-up:   slide-up 300ms cubic-bezier(0.34, 1.56, 0.64, 1);
  --animate-shimmer:    shimmer 2s linear infinite;
  --animate-pulse-glow: pulse-glow 2s ease-in-out infinite;

  /* === РАДИУСЫ === */
  --radius-glass: 16px;
  --radius-card:  12px;
  --radius-btn:   8px;
}
```

### 4.3 Glassmorphism utilities

```css
/* Стеклянная карточка */
.glass-card {
  background: var(--color-bg-glass);
  backdrop-filter: var(--blur-glass);
  -webkit-backdrop-filter: var(--blur-glass);
  border: 1px solid var(--color-border-glass);
  border-radius: var(--radius-glass);
}

/* Интенсивное стекло для модалей */
.glass-modal {
  background: rgba(15, 23, 42, 0.8);
  backdrop-filter: var(--blur-heavy);
  border: 1px solid var(--color-border-glass);
}

/* Неоновое свечение на кнопках */
.glow-primary {
  box-shadow: 0 0 20px rgba(99, 102, 241, 0.4),
              0 0 40px rgba(99, 102, 241, 0.1);
}
```

### 4.4 Keyframe-анимации

```css
@keyframes fade-in {
  from { opacity: 0; transform: translateY(4px); }
  to   { opacity: 1; transform: translateY(0); }
}

@keyframes slide-up {
  from { opacity: 0; transform: translateY(20px); }
  to   { opacity: 1; transform: translateY(0); }
}

@keyframes shimmer {
  from { background-position: -200% 0; }
  to   { background-position: 200% 0; }
}

@keyframes pulse-glow {
  0%, 100% { box-shadow: 0 0 10px rgba(99, 102, 241, 0.3); }
  50%       { box-shadow: 0 0 25px rgba(99, 102, 241, 0.6); }
}
```

---

## 5. PWA-требования

### 5.1 Mobile-first дизайн

- **Контрольные точки**: Mobile (< 640px), Tablet (640-1024px), Desktop (> 1024px)
- **Нижняя навигация**: На мобильных — `fixed bottom-0` с 5 основными разделами
- **Touch targets**: Минимум 48×48px для всех интерактивных элементов
- **Safe areas**: Поддержка `env(safe-area-inset-*)` для устройств с вырезами

### 5.2 Infinite Scroll

- Использовать `@tanstack/react-query` с `useInfiniteQuery`
- Реализовывать через `IntersectionObserver` или `@tanstack/react-virtual`
- Skeleton-заглушки при загрузке новой страницы
- `pageSize = 50` по умолчанию

### 5.3 PWA Manifest & Service Worker

```json
{
  "name": "Pulse Analytics",
  "short_name": "Pulse",
  "theme_color": "#6366f1",
  "background_color": "#020617",
  "display": "standalone",
  "orientation": "portrait-primary",
  "start_url": "/"
}
```

---

## 6. API-архитектура

```
/api/v1/
├── /auth          — Аутентификация (JWT)
├── /sync          — Синхронизация МойСклад
├── /financial     — Финансовые отчёты (ОДДС, ОПиУ, Баланс)
├── /working-capital — Оборотный капитал (CCC, A/R, A/P)
├── /inventory     — Складская аналитика (ABC/XYZ, GMROI)
├── /analytics     — Клиентская аналитика (LTV/CAC, Когорты)
├── /supply-chain  — Цепи поставок (OTIF)
├── /profitability — Стратегическая рентабельность (EBITDA)
├── /investor      — Инвесторские отчёты (CAPEX, ROE)
└── /dashboards    — Сводные дашборды
```

---

## 7. Правила качества кода

1. **Покрытие тестами**: ≥ 80% для services/, ≥ 60% для repositories/
2. **Линтеры**: `ruff` (Python), `eslint` (TypeScript)
3. **Форматирование**: `black` (Python), `prettier` (TypeScript)
4. **Типизация**: `mypy --strict` для Python, `tsc --noEmit` для TypeScript
5. **Нет магических чисел**: Все константы именованы и задокументированы
6. **Логирование**: `structlog` в JSON-формате для production

---

## 8. Информационная безопасность

- JWT-токены: RS256, expire 15 минут (access) + 7 дней (refresh)
- Все API-ключи МойСклад хранятся в `.env` файле (никогда в git)
- CORS: Разрешён только конкретный frontend origin
- Rate limiting: 60 запросов/минута на пользователя (через slowapi)
- SQL-инъекции: Только параметризованные запросы через SQLAlchemy
