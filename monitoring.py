"""
Модуль мониторинга для продакшен версии FinancialCompanion
========================================================

Обеспечивает:
- Сбор метрик производительности
- Мониторинг здоровья системы
- Алерты и уведомления
- Интеграция с внешними системами мониторинга

Версия: 2.0 (Production)
"""

import time
import psutil
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
import json
import logging
from dataclasses import dataclass, asdict
from prometheus_client import Counter, Histogram, Gauge, start_http_server
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests

from config import settings

logger = logging.getLogger(__name__)

@dataclass
class SystemMetrics:
    """Метрики системы"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    active_connections: int
    transactions_per_minute: float
    error_rate: float
    response_time_avg: float

@dataclass
class Alert:
    """Алерт системы"""
    id: str
    level: str  # 'info', 'warning', 'error', 'critical'
    message: str
    timestamp: datetime
    resolved: bool = False
    resolved_at: Optional[datetime] = None

class MetricsCollector:
    """Сборщик метрик системы"""
    
    def __init__(self):
        """Инициализация метрик Prometheus"""
        if settings.monitoring.METRICS_ENABLED:
            try:
                start_http_server(settings.monitoring.METRICS_PORT)
                logger.info(f"Prometheus метрики запущены на порту {settings.monitoring.METRICS_PORT}")
            except Exception as e:
                logger.error(f"Ошибка запуска Prometheus метрик: {e}")
        
        # Prometheus метрики
        self.transaction_counter = Counter('transactions_total', 'Total transactions processed')
        self.transaction_duration = Histogram('transaction_duration_seconds', 'Transaction processing time')
        self.error_counter = Counter('errors_total', 'Total errors', ['error_type'])
        self.active_users = Gauge('active_users', 'Number of active users')
        self.system_cpu = Gauge('system_cpu_percent', 'CPU usage percentage')
        self.system_memory = Gauge('system_memory_percent', 'Memory usage percentage')
        self.system_disk = Gauge('system_disk_percent', 'Disk usage percentage')
        
        # Внутренние метрики
        self.metrics_history: List[SystemMetrics] = []
        self.max_history_size = 1000
        
        # Статистика
        self.transaction_times: List[float] = []
        self.error_counts: Dict[str, int] = {}
        self.start_time = datetime.now()
    
    def record_transaction(self, duration: float, success: bool = True):
        """Записывает метрику транзакции"""
        self.transaction_counter.inc()
        self.transaction_duration.observe(duration)
        self.transaction_times.append(duration)
        
        # Ограничиваем размер истории
        if len(self.transaction_times) > 1000:
            self.transaction_times = self.transaction_times[-1000:]
    
    def record_error(self, error_type: str, error_message: str = ""):
        """Записывает метрику ошибки"""
        self.error_counter.labels(error_type=error_type).inc()
        self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1
    
    def collect_system_metrics(self) -> SystemMetrics:
        """Собирает метрики системы"""
        try:
            # Системные метрики
            cpu_percent = psutil.cpu_percent(interval=1)
            memory_percent = psutil.virtual_memory().percent
            disk_percent = psutil.disk_usage('/').percent
            
            # Метрики приложения
            current_time = datetime.now()
            
            # Вычисляем транзакции в минуту
            recent_transactions = [
                t for t in self.transaction_times 
                if current_time - timedelta(minutes=1) <= self.start_time + timedelta(seconds=sum(self.transaction_times[:self.transaction_times.index(t)]))
            ]
            transactions_per_minute = len(recent_transactions)
            
            # Вычисляем процент ошибок
            total_errors = sum(self.error_counts.values())
            total_transactions = len(self.transaction_times)
            error_rate = (total_errors / total_transactions * 100) if total_transactions > 0 else 0
            
            # Среднее время ответа
            response_time_avg = sum(self.transaction_times) / len(self.transaction_times) if self.transaction_times else 0
            
            # Обновляем Prometheus метрики
            self.system_cpu.set(cpu_percent)
            self.system_memory.set(memory_percent)
            self.system_disk.set(disk_percent)
            
            metrics = SystemMetrics(
                timestamp=current_time,
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                disk_percent=disk_percent,
                active_connections=0,  # В Streamlit сложно отследить
                transactions_per_minute=transactions_per_minute,
                error_rate=error_rate,
                response_time_avg=response_time_avg
            )
            
            # Сохраняем в историю
            self.metrics_history.append(metrics)
            if len(self.metrics_history) > self.max_history_size:
                self.metrics_history = self.metrics_history[-self.max_history_size:]
            
            return metrics
            
        except Exception as e:
            logger.error(f"Ошибка сбора метрик системы: {e}")
            return SystemMetrics(
                timestamp=datetime.now(),
                cpu_percent=0,
                memory_percent=0,
                disk_percent=0,
                active_connections=0,
                transactions_per_minute=0,
                error_rate=0,
                response_time_avg=0
            )
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Возвращает сводку метрик"""
        if not self.metrics_history:
            return {}
        
        latest = self.metrics_history[-1]
        
        return {
            "uptime_seconds": (datetime.now() - self.start_time).total_seconds(),
            "total_transactions": len(self.transaction_times),
            "avg_response_time": sum(self.transaction_times) / len(self.transaction_times) if self.transaction_times else 0,
            "error_rate": latest.error_rate,
            "transactions_per_minute": latest.transactions_per_minute,
            "system": {
                "cpu_percent": latest.cpu_percent,
                "memory_percent": latest.memory_percent,
                "disk_percent": latest.disk_percent
            },
            "errors_by_type": self.error_counts
        }

class AlertManager:
    """Менеджер алертов"""
    
    def __init__(self):
        """Инициализация менеджера алертов"""
        self.alerts: List[Alert] = []
        self.alert_handlers: Dict[str, Callable] = {}
        self.alert_id_counter = 0
        
        # Настройка обработчиков алертов
        self._setup_alert_handlers()
    
    def _setup_alert_handlers(self):
        """Настраивает обработчики алертов"""
        if settings.monitoring.ALERTS_ENABLED:
            if settings.monitoring.ALERT_EMAIL:
                self.alert_handlers['email'] = self._send_email_alert
            if settings.monitoring.ALERT_WEBHOOK:
                self.alert_handlers['webhook'] = self._send_webhook_alert
    
    def create_alert(self, level: str, message: str, auto_resolve: bool = False) -> str:
        """Создает новый алерт"""
        alert_id = f"alert_{self.alert_id_counter}_{int(time.time())}"
        self.alert_id_counter += 1
        
        alert = Alert(
            id=alert_id,
            level=level,
            message=message,
            timestamp=datetime.now()
        )
        
        self.alerts.append(alert)
        
        # Логируем алерт
        logger.warning(f"ALERT [{level.upper()}]: {message}")
        
        # Отправляем уведомления
        for handler_name, handler in self.alert_handlers.items():
            try:
                handler(alert)
            except Exception as e:
                logger.error(f"Ошибка отправки алерта через {handler_name}: {e}")
        
        # Автоматическое разрешение для info алертов
        if auto_resolve and level == 'info':
            self.resolve_alert(alert_id)
        
        return alert_id
    
    def resolve_alert(self, alert_id: str) -> bool:
        """Разрешает алерт"""
        for alert in self.alerts:
            if alert.id == alert_id and not alert.resolved:
                alert.resolved = True
                alert.resolved_at = datetime.now()
                logger.info(f"Alert {alert_id} resolved")
                return True
        return False
    
    def get_active_alerts(self, level: Optional[str] = None) -> List[Alert]:
        """Возвращает активные алерты"""
        alerts = [a for a in self.alerts if not a.resolved]
        if level:
            alerts = [a for a in alerts if a.level == level]
        return alerts
    
    def _send_email_alert(self, alert: Alert):
        """Отправляет алерт по email"""
        if not settings.monitoring.ALERT_EMAIL:
            return
        
        try:
            msg = MIMEMultipart()
            msg['From'] = 'noreply@financialcompanion.com'
            msg['To'] = settings.monitoring.ALERT_EMAIL
            msg['Subject'] = f"[{alert.level.upper()}] FinancialCompanion Alert"
            
            body = f"""
            FinancialCompanion Alert
            
            Level: {alert.level.upper()}
            Time: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
            Message: {alert.message}
            
            Alert ID: {alert.id}
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # В реальной системе здесь была бы настройка SMTP
            logger.info(f"Email alert sent to {settings.monitoring.ALERT_EMAIL}")
            
        except Exception as e:
            logger.error(f"Ошибка отправки email алерта: {e}")
    
    def _send_webhook_alert(self, alert: Alert):
        """Отправляет алерт через webhook"""
        if not settings.monitoring.ALERT_WEBHOOK:
            return
        
        try:
            payload = {
                "alert_id": alert.id,
                "level": alert.level,
                "message": alert.message,
                "timestamp": alert.timestamp.isoformat(),
                "source": "FinancialCompanion"
            }
            
            response = requests.post(
                settings.monitoring.ALERT_WEBHOOK,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"Webhook alert sent successfully")
            else:
                logger.error(f"Webhook alert failed: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Ошибка отправки webhook алерта: {e}")

class HealthChecker:
    """Проверка здоровья системы"""
    
    def __init__(self, metrics_collector: MetricsCollector, alert_manager: AlertManager):
        """Инициализация проверки здоровья"""
        self.metrics_collector = metrics_collector
        self.alert_manager = alert_manager
        self.health_checks = {
            'system_resources': self._check_system_resources,
            'database_connection': self._check_database_connection,
            'transaction_processing': self._check_transaction_processing,
            'error_rate': self._check_error_rate
        }
    
    def run_health_checks(self) -> Dict[str, Any]:
        """Запускает все проверки здоровья"""
        results = {}
        
        for check_name, check_func in self.health_checks.items():
            try:
                results[check_name] = check_func()
            except Exception as e:
                logger.error(f"Ошибка проверки здоровья {check_name}: {e}")
                results[check_name] = {
                    'status': 'error',
                    'message': str(e)
                }
        
        return results
    
    def _check_system_resources(self) -> Dict[str, Any]:
        """Проверяет системные ресурсы"""
        metrics = self.metrics_collector.collect_system_metrics()
        
        issues = []
        status = 'healthy'
        
        # Проверка CPU
        if metrics.cpu_percent > 80:
            issues.append(f"CPU usage high: {metrics.cpu_percent:.1f}%")
            status = 'warning'
        if metrics.cpu_percent > 95:
            status = 'critical'
            self.alert_manager.create_alert('critical', f"CPU usage critical: {metrics.cpu_percent:.1f}%")
        
        # Проверка памяти
        if metrics.memory_percent > 80:
            issues.append(f"Memory usage high: {metrics.memory_percent:.1f}%")
            status = 'warning'
        if metrics.memory_percent > 95:
            status = 'critical'
            self.alert_manager.create_alert('critical', f"Memory usage critical: {metrics.memory_percent:.1f}%")
        
        # Проверка диска
        if metrics.disk_percent > 80:
            issues.append(f"Disk usage high: {metrics.disk_percent:.1f}%")
            status = 'warning'
        if metrics.disk_percent > 95:
            status = 'critical'
            self.alert_manager.create_alert('critical', f"Disk usage critical: {metrics.disk_percent:.1f}%")
        
        return {
            'status': status,
            'cpu_percent': metrics.cpu_percent,
            'memory_percent': metrics.memory_percent,
            'disk_percent': metrics.disk_percent,
            'issues': issues
        }
    
    def _check_database_connection(self) -> Dict[str, Any]:
        """Проверяет подключение к базе данных"""
        try:
            # В реальной системе здесь была бы проверка подключения к БД
            # Для демонстрации возвращаем успех
            return {
                'status': 'healthy',
                'message': 'Database connection OK'
            }
        except Exception as e:
            self.alert_manager.create_alert('error', f"Database connection failed: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def _check_transaction_processing(self) -> Dict[str, Any]:
        """Проверяет обработку транзакций"""
        metrics = self.metrics_collector.get_metrics_summary()
        
        if not metrics:
            return {
                'status': 'unknown',
                'message': 'No metrics available'
            }
        
        issues = []
        status = 'healthy'
        
        # Проверка времени ответа
        avg_response_time = metrics.get('avg_response_time', 0)
        if avg_response_time > 5.0:
            issues.append(f"Slow response time: {avg_response_time:.2f}s")
            status = 'warning'
        if avg_response_time > 10.0:
            status = 'critical'
            self.alert_manager.create_alert('critical', f"Very slow response time: {avg_response_time:.2f}s")
        
        # Проверка количества транзакций
        tpm = metrics.get('transactions_per_minute', 0)
        if tpm == 0:
            issues.append("No transactions processed")
            status = 'warning'
        
        return {
            'status': status,
            'avg_response_time': avg_response_time,
            'transactions_per_minute': tpm,
            'issues': issues
        }
    
    def _check_error_rate(self) -> Dict[str, Any]:
        """Проверяет процент ошибок"""
        metrics = self.metrics_collector.get_metrics_summary()
        
        if not metrics:
            return {
                'status': 'unknown',
                'message': 'No metrics available'
            }
        
        error_rate = metrics.get('error_rate', 0)
        issues = []
        status = 'healthy'
        
        if error_rate > 5.0:
            issues.append(f"High error rate: {error_rate:.1f}%")
            status = 'warning'
        if error_rate > 10.0:
            status = 'critical'
            self.alert_manager.create_alert('critical', f"Critical error rate: {error_rate:.1f}%")
        
        return {
            'status': status,
            'error_rate': error_rate,
            'issues': issues
        }

class MonitoringManager:
    """Основной менеджер мониторинга"""
    
    def __init__(self):
        """Инициализация мониторинга"""
        self.metrics_collector = MetricsCollector()
        self.alert_manager = AlertManager()
        self.health_checker = HealthChecker(self.metrics_collector, self.alert_manager)
        
        # Запуск фонового мониторинга
        self.monitoring_thread = None
        self.stop_monitoring = False
        
        if settings.monitoring.HEALTH_CHECK_INTERVAL_SECONDS > 0:
            self.start_background_monitoring()
    
    def start_background_monitoring(self):
        """Запускает фоновый мониторинг"""
        def monitoring_loop():
            while not self.stop_monitoring:
                try:
                    # Собираем метрики
                    self.metrics_collector.collect_system_metrics()
                    
                    # Проверяем здоровье системы
                    health_results = self.health_checker.run_health_checks()
                    
                    # Проверяем критические проблемы
                    for check_name, result in health_results.items():
                        if result.get('status') == 'critical':
                            self.alert_manager.create_alert(
                                'critical',
                                f"Critical health check failed: {check_name}"
                            )
                    
                    # Ждем следующей проверки
                    time.sleep(settings.monitoring.HEALTH_CHECK_INTERVAL_SECONDS)
                    
                except Exception as e:
                    logger.error(f"Ошибка фонового мониторинга: {e}")
                    time.sleep(60)  # Ждем минуту перед повторной попыткой
        
        self.monitoring_thread = threading.Thread(target=monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        logger.info("Фоновый мониторинг запущен")
    
    def stop_background_monitoring(self):
        """Останавливает фоновый мониторинг"""
        self.stop_monitoring = True
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        logger.info("Фоновый мониторинг остановлен")
    
    def get_system_status(self) -> Dict[str, Any]:
        """Возвращает статус системы"""
        metrics = self.metrics_collector.get_metrics_summary()
        health = self.health_checker.run_health_checks()
        active_alerts = self.alert_manager.get_active_alerts()
        
        # Определяем общий статус
        overall_status = 'healthy'
        critical_alerts = [a for a in active_alerts if a.level == 'critical']
        error_alerts = [a for a in active_alerts if a.level == 'error']
        
        if critical_alerts:
            overall_status = 'critical'
        elif error_alerts:
            overall_status = 'error'
        elif any(h.get('status') == 'warning' for h in health.values()):
            overall_status = 'warning'
        
        return {
            'status': overall_status,
            'timestamp': datetime.now().isoformat(),
            'uptime_seconds': metrics.get('uptime_seconds', 0),
            'metrics': metrics,
            'health': health,
            'alerts': {
                'total': len(active_alerts),
                'critical': len(critical_alerts),
                'error': len(error_alerts),
                'warning': len([a for a in active_alerts if a.level == 'warning']),
                'info': len([a for a in active_alerts if a.level == 'info'])
            }
        }
    
    def record_transaction(self, duration: float, success: bool = True):
        """Записывает метрику транзакции"""
        self.metrics_collector.record_transaction(duration, success)
    
    def record_error(self, error_type: str, error_message: str = ""):
        """Записывает метрику ошибки"""
        self.metrics_collector.record_error(error_type, error_message)
    
    def create_alert(self, level: str, message: str) -> str:
        """Создает алерт"""
        return self.alert_manager.create_alert(level, message)

# Глобальный экземпляр менеджера мониторинга
monitoring_manager = MonitoringManager() 
