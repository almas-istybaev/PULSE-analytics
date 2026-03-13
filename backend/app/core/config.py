"""
Конфигурация приложения Pulse через переменные окружения.

Использует pydantic-settings для типизированной валидации настроек.
Значения загружаются из .env файла.
"""
from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Настройки приложения Pulse Backend.

    Все переменные могут быть переопределены через .env файл
    или переменные окружения.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Приложение ──
    ENVIRONMENT: str = Field(default="development", description="Среда (development/production)")
    DEBUG: bool = Field(default=True, description="Режим отладки")
    SECRET_KEY: str = Field(
        default="CHANGE_ME_IN_PRODUCTION_USE_OPENSSL_RAND_HEX_32",
        description="Секретный ключ для подписи refresh-токенов",
    )

    # ── База данных ──
    DATABASE_URL: str = Field(
        default="sqlite+aiosqlite:///./pulse.db",
        description="URL подключения к SQLite",
    )

    # ── CORS ──
    ALLOWED_ORIGINS: list[str] = Field(
        default=["http://localhost:5173", "http://localhost:3000"],
        description="Разрешённые origins для CORS",
    )

    # ── МойСклад API ──
    MOYSKLAD_TOKEN: str = Field(
        default="",
        description="Bearer-токен МойСклад API",
    )
    MOYSKLAD_BASE_URL: str = Field(
        default="https://api.moysklad.ru/api/remap/1.2",
        description="Базовый URL МойСклад API",
    )
    MOYSKLAD_RATE_LIMIT: int = Field(
        default=100,
        description="Максимум запросов в минуту к МойСклад",
    )
    MOYSKLAD_WEBHOOK_SECRET: str = Field(
        default="",
        description="Секрет для верификации HMAC подписи вебхуков МойСклад",
    )

    # ── JWT (HS256 для простоты; в prod можно заменить на RS256) ──
    JWT_ALGORITHM: str = Field(default="HS256", description="Алгоритм подписи JWT")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=15,
        description="Срок действия access-токена в минутах",
    )
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = Field(
        default=7,
        description="Срок действия refresh-токена в днях",
    )

    # ── Rate Limiting ──
    RATE_LIMIT_PER_MINUTE: int = Field(
        default=60,
        description="Лимит запросов в минуту на пользователя",
    )

    # ── Синхронизация ──
    SYNC_INTERVAL_MINUTES: int = Field(
        default=15,
        description="Интервал инкрементальной синхронизации (минуты)",
    )
    STOCK_SNAPSHOT_CRON: str = Field(
        default="59 23 * * *",
        description="Cron для ежедневного снимка запасов",
    )


settings = Settings()
