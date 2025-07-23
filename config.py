"""
Конфигурация для продакшен версии FinancialCompanion
==================================================

Содержит все настройки приложения для продакшена:
- Безопасность и аутентификация
- База данных и кэширование
- Логирование и мониторинг
- Настройки производительности

Автор: AI Assistant
Версия: 2.0 (Production)
"""

import os
from typing import Optional, Dict, Any
from pydantic import BaseSettings, Field
from pathlib import Path

class SecuritySettings(BaseSettings):
    """Настройки безопасности"""
    
    # JWT токены
    SECRET_KEY: str = Field(default="your-secret-key-change-in-production", env="SECRET_KEY")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Пароли
    MIN_PASSWORD_LENGTH: int = 8
    REQUIRE_SPECIAL_CHARS: bool = True
    PASSWORD_HISTORY_SIZE: int = 5
    
    # Блокировка аккаунтов
    MAX_LOGIN_ATTEMPTS: int = 5
    LOCKOUT_DURATION_MINUTES: int = 15
    
    # Шифрование
    ENCRYPTION_KEY: str = Field(default="your-encryption-key", env="ENCRYPTION_KEY")
    
    class Config:
        env_prefix = "SECURITY_"

class DatabaseSettings(BaseSettings):
    """Настройки базы данных"""
    
    # Основная БД
    DATABASE_URL: str = Field(default="sqlite:///./financial_companion.db", env="DATABASE_URL")
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    
    # Redis для кэширования
    REDIS_URL: str = Field(default="redis://localhost:6379", env="REDIS_URL")
    REDIS_PASSWORD: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    REDIS_DB: int = 0
    
    # Резервное копирование
    BACKUP_ENABLED: bool = True
    BACKUP_INTERVAL_HOURS: int = 24
    BACKUP_RETENTION_DAYS: int = 30
    BACKUP_PATH: str = "./backups"
    
    class Config:
        env_prefix = "DB_"

class LoggingSettings(BaseSettings):
    """Настройки логирования"""
    
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE: str = "./logs/financial_companion.log"
    LOG_MAX_SIZE_MB: int = 100
    LOG_BACKUP_COUNT: int = 5
    
    # Структурированное логирование
    STRUCTURED_LOGGING: bool = True
    JSON_LOGS: bool = True
    
    # Аудит
    AUDIT_LOG_ENABLED: bool = True
    AUDIT_LOG_FILE: str = "./logs/audit.log"
    
    class Config:
        env_prefix = "LOG_"

class MonitoringSettings(BaseSettings):
    """Настройки мониторинга"""
    
    # Prometheus метрики
    METRICS_ENABLED: bool = True
    METRICS_PORT: int = 9090
    
    # Sentry для отслеживания ошибок
    SENTRY_DSN: Optional[str] = Field(default=None, env="SENTRY_DSN")
    SENTRY_ENVIRONMENT: str = "production"
    
    # Алерты
    ALERTS_ENABLED: bool = True
    ALERT_EMAIL: Optional[str] = Field(default=None, env="ALERT_EMAIL")
    ALERT_WEBHOOK: Optional[str] = Field(default=None, env="ALERT_WEBHOOK")
    
    # Здоровье системы
    HEALTH_CHECK_INTERVAL_SECONDS: int = 30
    
    class Config:
        env_prefix = "MONITORING_"

class PerformanceSettings(BaseSettings):
    """Настройки производительности"""
    
    # Кэширование
    CACHE_ENABLED: bool = True
    CACHE_TTL_SECONDS: int = 3600
    CACHE_MAX_SIZE: int = 1000
    
    # Асинхронная обработка
    ASYNC_PROCESSING: bool = True
    MAX_CONCURRENT_TASKS: int = 10
    
    # Ограничения
    MAX_TRANSACTIONS_PER_REQUEST: int = 100
    MAX_FILE_SIZE_MB: int = 10
    REQUEST_TIMEOUT_SECONDS: int = 30
    
    class Config:
        env_prefix = "PERF_"

class BankingComplianceSettings(BaseSettings):
    """Настройки соответствия банковским стандартам"""
    
    # PCI DSS
    PCI_COMPLIANCE_ENABLED: bool = True
    MASK_SENSITIVE_DATA: bool = True
    
    # Аудит транзакций
    AUDIT_ALL_TRANSACTIONS: bool = True
    AUDIT_RETENTION_YEARS: int = 7
    
    # Валидация
    STRICT_VALIDATION: bool = True
    SANCTIONS_CHECK_ENABLED: bool = True
    
    # Отчетность
    REGULATORY_REPORTS_ENABLED: bool = True
    REPORT_GENERATION_INTERVAL_HOURS: int = 24
    
    class Config:
        env_prefix = "COMPLIANCE_"

class Settings(BaseSettings):
    """Основные настройки приложения"""
    
    # Основные настройки
    APP_NAME: str = "FinancialCompanion Production"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "production"
    
    # Пути
    BASE_DIR: Path = Path(__file__).parent
    STATIC_DIR: Path = BASE_DIR / "static"
    TEMPLATES_DIR: Path = BASE_DIR / "templates"
    
    # Порт и хост
    HOST: str = "0.0.0.0"
    PORT: int = 8501
    
    # Настройки компонентов
    security: SecuritySettings = SecuritySettings()
    database: DatabaseSettings = DatabaseSettings()
    logging: LoggingSettings = LoggingSettings()
    monitoring: MonitoringSettings = MonitoringSettings()
    performance: PerformanceSettings = PerformanceSettings()
    compliance: BankingComplianceSettings = BankingComplianceSettings()
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# Глобальный экземпляр настроек
settings = Settings()

def get_settings() -> Settings:
    """Возвращает экземпляр настроек"""
    return settings

def validate_settings() -> Dict[str, Any]:
    """Проверяет корректность настроек"""
    errors = []
    warnings = []
    
    # Проверка критических настроек
    if settings.security.SECRET_KEY == "your-secret-key-change-in-production":
        errors.append("SECRET_KEY должен быть изменен в продакшене")
    
    if settings.security.ENCRYPTION_KEY == "your-encryption-key":
        errors.append("ENCRYPTION_KEY должен быть изменен в продакшене")
    
    # Проверка путей
    if not settings.BASE_DIR.exists():
        errors.append(f"Базовый каталог не существует: {settings.BASE_DIR}")
    
    # Проверка опциональных настроек
    if not settings.monitoring.SENTRY_DSN:
        warnings.append("SENTRY_DSN не настроен - ошибки не будут отслеживаться")
    
    if not settings.monitoring.ALERT_EMAIL:
        warnings.append("ALERT_EMAIL не настроен - алерты не будут отправляться")
    
    return {
        "errors": errors,
        "warnings": warnings,
        "is_valid": len(errors) == 0
    } 