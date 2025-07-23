# Руководство по развертыванию FinancialCompanion Production

## 🚀 Быстрый старт

### 1. Подготовка окружения

```bash
# Создайте виртуальное окружение
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate     # Windows

# Установите зависимости
pip install -r requirements.txt
```

### 2. Настройка конфигурации

```bash
# Скопируйте пример конфигурации
cp env_example.txt .env

# Отредактируйте .env файл
# ОБЯЗАТЕЛЬНО измените SECURITY_SECRET_KEY и SECURITY_ENCRYPTION_KEY!
```

### 3. Создание необходимых папок

```bash
mkdir logs
mkdir backups
mkdir static
mkdir templates
```

### 4. Инициализация базы данных

```bash
python -c "from database import DatabaseManager; DatabaseManager()._init_database()"
```

### 5. Запуск приложения

```bash
streamlit run app_production.py
```

## 🔧 Подробное развертывание

### Требования к системе

#### Минимальные требования
- **CPU:** 2 ядра
- **RAM:** 4 GB
- **Диск:** 20 GB свободного места
- **ОС:** Linux, Windows, macOS
- **Python:** 3.8+

#### Рекомендуемые требования
- **CPU:** 4+ ядра
- **RAM:** 8+ GB
- **Диск:** 50+ GB SSD
- **ОС:** Ubuntu 20.04+, CentOS 8+
- **Python:** 3.9+

### Установка зависимостей

#### Системные зависимости (Ubuntu/Debian)

```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv
sudo apt install -y redis-server  # для кэширования
sudo apt install -y nginx         # для прокси
sudo apt install -y supervisor    # для управления процессами
```

#### Системные зависимости (CentOS/RHEL)

```bash
sudo yum update
sudo yum install -y python3 python3-pip
sudo yum install -y redis
sudo yum install -y nginx
sudo yum install -y supervisor
```

#### Python зависимости

```bash
# Создание виртуального окружения
python3 -m venv /opt/financial-companion/venv
source /opt/financial-companion/venv/bin/activate

# Установка зависимостей
pip install --upgrade pip
pip install -r requirements.txt
```

### Настройка безопасности

#### 1. Генерация секретных ключей

```bash
# Генерация секретного ключа для JWT
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Генерация ключа шифрования
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

#### 2. Настройка файла .env

```bash
# Отредактируйте .env файл с вашими ключами
nano .env

# Пример содержимого:
SECURITY_SECRET_KEY=ваш-сгенерированный-секретный-ключ
SECURITY_ENCRYPTION_KEY=ваш-сгенерированный-ключ-шифрования
```

#### 3. Настройка прав доступа

```bash
# Создание пользователя для приложения
sudo useradd -r -s /bin/false financial-companion

# Настройка прав на файлы
sudo chown -R financial-companion:financial-companion /opt/financial-companion
sudo chmod 600 /opt/financial-companion/.env
sudo chmod 755 /opt/financial-companion/logs
```

### Настройка базы данных

#### SQLite (по умолчанию)

```bash
# Инициализация базы данных
python3 -c "from database import DatabaseManager; DatabaseManager()._init_database()"

# Проверка прав доступа
sudo chown financial-companion:financial-companion financial_companion_production.db
sudo chmod 640 financial_companion_production.db
```

#### PostgreSQL (рекомендуется для продакшена)

```bash
# Установка PostgreSQL
sudo apt install -y postgresql postgresql-contrib

# Создание базы данных
sudo -u postgres createdb financial_companion
sudo -u postgres createuser financial_companion_user

# Настройка прав
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE financial_companion TO financial_companion_user;"

# Обновление .env файла
DB_DATABASE_URL=postgresql://financial_companion_user:password@localhost/financial_companion
```

### Настройка Redis (для кэширования)

```bash
# Установка Redis
sudo apt install -y redis-server

# Настройка Redis
sudo nano /etc/redis/redis.conf

# Добавьте/измените следующие строки:
maxmemory 256mb
maxmemory-policy allkeys-lru
requirepass ваш-пароль-redis

# Перезапуск Redis
sudo systemctl restart redis
sudo systemctl enable redis

# Обновление .env файла
DB_REDIS_PASSWORD=ваш-пароль-redis
```

### Настройка Nginx (обратный прокси)

#### Конфигурация Nginx

```bash
sudo nano /etc/nginx/sites-available/financial-companion
```

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # Редирект на HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    # SSL сертификаты
    ssl_certificate /path/to/your/certificate.crt;
    ssl_certificate_key /path/to/your/private.key;

    # SSL настройки
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    # Безопасность
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # Проксирование к Streamlit
    location / {
        proxy_pass http://127.0.0.1:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    # Статические файлы
    location /static/ {
        alias /opt/financial-companion/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

#### Активация конфигурации

```bash
sudo ln -s /etc/nginx/sites-available/financial-companion /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Настройка Supervisor (управление процессами)

#### Конфигурация Supervisor

```bash
sudo nano /etc/supervisor/conf.d/financial-companion.conf
```

```ini
[program:financial-companion]
command=/opt/financial-companion/venv/bin/streamlit run app_production.py --server.port 8501 --server.address 127.0.0.1
directory=/opt/financial-companion
user=financial-companion
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/opt/financial-companion/logs/supervisor.log
environment=HOME="/opt/financial-companion",USER="financial-companion"
```

#### Запуск Supervisor

```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start financial-companion
```

### Настройка мониторинга

#### Prometheus (метрики)

```bash
# Установка Prometheus
wget https://github.com/prometheus/prometheus/releases/download/v2.37.0/prometheus-2.37.0.linux-amd64.tar.gz
tar xvf prometheus-*.tar.gz
sudo mv prometheus-* /opt/prometheus

# Конфигурация Prometheus
sudo nano /opt/prometheus/prometheus.yml
```

```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'financial-companion'
    static_configs:
      - targets: ['localhost:9090']
```

#### Grafana (визуализация)

```bash
# Установка Grafana
sudo apt install -y grafana

# Запуск Grafana
sudo systemctl start grafana-server
sudo systemctl enable grafana-server
```

### Настройка резервного копирования

#### Автоматическое резервное копирование

```bash
sudo nano /opt/financial-companion/backup.sh
```

```bash
#!/bin/bash

# Настройки
BACKUP_DIR="/opt/financial-companion/backups"
DATE=$(date +%Y%m%d_%H%M%S)
DB_FILE="financial_companion_production.db"
LOG_FILE="/opt/financial-companion/logs/backup.log"

# Создание резервной копии базы данных
cp "$DB_FILE" "$BACKUP_DIR/${DB_FILE}.${DATE}"

# Создание резервной копии логов
tar -czf "$BACKUP_DIR/logs_${DATE}.tar.gz" logs/

# Удаление старых резервных копий (старше 30 дней)
find "$BACKUP_DIR" -name "*.${DATE}" -mtime +30 -delete
find "$BACKUP_DIR" -name "logs_*.tar.gz" -mtime +30 -delete

echo "Backup completed: $DATE" >> "$LOG_FILE"
```

#### Настройка cron

```bash
sudo crontab -e

# Добавьте строку для ежедневного бэкапа в 2:00
0 2 * * * /opt/financial-companion/backup.sh
```

### Настройка SSL сертификатов

#### Let's Encrypt (бесплатные сертификаты)

```bash
# Установка Certbot
sudo apt install -y certbot python3-certbot-nginx

# Получение сертификата
sudo certbot --nginx -d your-domain.com

# Автоматическое обновление
sudo crontab -e

# Добавьте строку для автоматического обновления
0 12 * * * /usr/bin/certbot renew --quiet
```

## 🔍 Проверка развертывания

### 1. Проверка статуса сервисов

```bash
# Проверка Supervisor
sudo supervisorctl status financial-companion

# Проверка Nginx
sudo systemctl status nginx

# Проверка Redis
sudo systemctl status redis

# Проверка базы данных
python3 -c "from database import DatabaseManager; print('Database OK')"
```

### 2. Проверка доступности

```bash
# Проверка HTTP
curl -I http://localhost:8501

# Проверка HTTPS
curl -I https://your-domain.com

# Проверка метрик
curl http://localhost:9090/metrics
```

### 3. Проверка логов

```bash
# Логи приложения
tail -f /opt/financial-companion/logs/financial_companion.log

# Логи аудита
tail -f /opt/financial-companion/logs/audit.log

# Логи Nginx
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

## 🚨 Устранение неполадок

### Частые проблемы

#### 1. Ошибка подключения к базе данных

```bash
# Проверка прав доступа
ls -la financial_companion_production.db

# Пересоздание базы данных
rm financial_companion_production.db
python3 -c "from database import DatabaseManager; DatabaseManager()._init_database()"
```

#### 2. Ошибка шифрования

```bash
# Проверка ключей в .env
grep SECURITY_ENCRYPTION_KEY .env

# Регенерация ключа
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

#### 3. Проблемы с производительностью

```bash
# Проверка использования ресурсов
htop
df -h
free -h

# Оптимизация Redis
redis-cli info memory
```

#### 4. Проблемы с SSL

```bash
# Проверка сертификатов
openssl s_client -connect your-domain.com:443

# Обновление сертификатов
sudo certbot renew
```

## 📊 Мониторинг в продакшене

### Метрики для отслеживания

- **CPU использование:** < 80%
- **Память:** < 80%
- **Диск:** < 85%
- **Время ответа:** < 5 секунд
- **Ошибки:** < 1%

### Алерты

Настройте алерты для:
- Высокого использования ресурсов
- Ошибок в логах
- Недоступности сервисов
- Проблем с базой данных

### Логирование

- **Уровень:** WARNING для продакшена
- **Ротация:** Ежедневно
- **Хранение:** 30 дней для логов, 7 лет для аудита

## 🔄 Обновления

### Процедура обновления

```bash
# 1. Создание резервной копии
/opt/financial-companion/backup.sh

# 2. Остановка приложения
sudo supervisorctl stop financial-companion

# 3. Обновление кода
cd /opt/financial-companion
git pull origin main

# 4. Обновление зависимостей
source venv/bin/activate
pip install -r requirements.txt

# 5. Миграция базы данных (если необходимо)
python3 -c "from database import DatabaseManager; DatabaseManager()._init_database()"

# 6. Запуск приложения
sudo supervisorctl start financial-companion

# 7. Проверка работоспособности
curl -I http://localhost:8501
```

## 📞 Поддержка

### Контакты
- **Email:** support@financialcompanion.com
- **Документация:** [docs.financialcompanion.com](https://docs.financialcompanion.com)
- **Issues:** [GitHub Issues](https://github.com/financialcompanion/issues)

### Полезные команды

```bash
# Перезапуск всех сервисов
sudo supervisorctl restart financial-companion
sudo systemctl restart nginx
sudo systemctl restart redis

# Просмотр логов в реальном времени
tail -f /opt/financial-companion/logs/financial_companion.log

# Проверка статуса системы
python3 -c "from monitoring import monitoring_manager; print(monitoring_manager.get_system_status())"
```

---

**⚠️ Важно:** Всегда тестируйте обновления в тестовой среде перед применением в продакшене! 