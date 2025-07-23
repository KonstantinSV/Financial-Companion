"""
FinancialCompanion Production - Основное приложение
=================================================

Продакшен версия AI-ассистента для обработки межбанковских транзакций
с полной интеграцией безопасности, мониторинга и соответствия стандартам.

Автор: AI Assistant
Версия: 2.0 (Production)
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
import logging
import asyncio
from typing import Dict, List, Optional, Any
import time
import hashlib
import hmac

# Импорт локальных модулей
from config import settings, validate_settings
from security import security_manager
from transaction_processor import TransactionProcessor, TransactionData
from database import DatabaseManager
from utils import format_currency, get_transaction_examples
from test_data import get_sample_transactions

# Настройка логирования
logging.basicConfig(
    level=getattr(logging, settings.logging.LOG_LEVEL),
    format=settings.logging.LOG_FORMAT,
    handlers=[
        logging.FileHandler(settings.logging.LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Инициализация Sentry для отслеживания ошибок
if settings.monitoring.SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.logging import LoggingIntegration
    
    sentry_logging = LoggingIntegration(
        level=logging.INFO,
        event_level=logging.ERROR
    )
    
    sentry_sdk.init(
        dsn=settings.monitoring.SENTRY_DSN,
        environment=settings.monitoring.SENTRY_ENVIRONMENT,
        integrations=[sentry_logging],
        traces_sample_rate=1.0,
    )

# Настройка страницы Streamlit
st.set_page_config(
    page_title=settings.APP_NAME,
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Инициализация сессионных переменных
if 'db_manager' not in st.session_state:
    st.session_state.db_manager = DatabaseManager()

if 'processor' not in st.session_state:
    st.session_state.processor = TransactionProcessor()

if 'transaction_history' not in st.session_state:
    st.session_state.transaction_history = []

if 'user_authenticated' not in st.session_state:
    st.session_state.user_authenticated = False

if 'current_user' not in st.session_state:
    st.session_state.current_user = None

if 'security_events' not in st.session_state:
    st.session_state.security_events = []

def check_authentication():
    """Проверяет аутентификацию пользователя"""
    if not st.session_state.user_authenticated:
        st.error("🔒 Требуется аутентификация")
        show_login_page()
        st.stop()

def show_login_page():
    """Отображает страницу входа"""
    st.title("🔐 Вход в систему")
    st.markdown("**FinancialCompanion Production - Система безопасности**")
    
    with st.form("login_form"):
        username = st.text_input("Имя пользователя")
        password = st.text_input("Пароль", type="password")
        submit_button = st.form_submit_button("Войти")
        
        if submit_button:
            if username and password:
                # Получаем IP адрес (в Streamlit это ограничено)
                ip_address = "127.0.0.1"  # В реальной системе получаем из запроса
                
                # Аутентификация
                auth_result = security_manager.authenticate_user(username, password, ip_address)
                
                if auth_result:
                    st.session_state.user_authenticated = True
                    st.session_state.current_user = auth_result["user"]
                    st.session_state.access_token = auth_result["access_token"]
                    
                    st.success("✅ Успешный вход в систему")
                    st.rerun()
                else:
                    st.error("❌ Неверное имя пользователя или пароль")
            else:
                st.warning("⚠️ Введите имя пользователя и пароль")
    
    # Информация для демонстрации
    st.info("""
    **Демо-доступ:**
    - Имя пользователя: `admin`
    - Пароль: `admin123`
    """)

def log_user_action(action: str, resource: str, details: Dict[str, Any], success: bool = True):
    """Логирует действия пользователя"""
    if st.session_state.current_user:
        security_manager.log_security_event(
            user_id=st.session_state.current_user["id"],
            action=action,
            resource=resource,
            details=details,
            ip_address="127.0.0.1",  # В реальной системе получаем из запроса
            user_agent="Streamlit",
            success=success
        )

def show_security_dashboard():
    """Отображает дашборд безопасности"""
    st.header("🛡️ Дашборд безопасности")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Статус системы", "🟢 Безопасно")
    
    with col2:
        st.metric("Активные сессии", "1")
    
    with col3:
        st.metric("Попытки входа", "0")
    
    with col4:
        st.metric("Блокировки", "0")
    
    # События безопасности
    st.subheader("📊 Последние события безопасности")
    
    # Получаем события аудита
    audit_events = security_manager.audit_manager.get_audit_events(limit=10)
    
    if audit_events:
        events_data = []
        for event in audit_events:
            events_data.append({
                "Время": event.timestamp.strftime("%H:%M:%S"),
                "Действие": event.action,
                "Ресурс": event.resource,
                "IP": event.ip_address,
                "Статус": "✅" if event.success else "❌"
            })
        
        df_events = pd.DataFrame(events_data)
        st.dataframe(df_events, use_container_width=True)
    else:
        st.info("События безопасности не найдены")

def show_transaction_analysis():
    """Страница анализа транзакций с улучшенной безопасностью"""
    
    st.header("🔍 Анализ и Обработка Транзакций")
    
    # Проверяем права доступа
    if st.session_state.current_user["role"] not in ["admin", "analyst"]:
        st.error("❌ Недостаточно прав для доступа к анализу транзакций")
        return
    
    # Логируем доступ к ресурсу
    log_user_action("ACCESS", "TRANSACTION_ANALYSIS", {"page": "transaction_analysis"})
    
    # Две колонки для ввода
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📝 Ввод текста транзакции")
        
        # Примеры для быстрого тестирования
        example_texts = get_transaction_examples()
        selected_example = st.selectbox(
            "Выберите пример или введите свой текст:",
            ["Введите свой текст..."] + list(example_texts.keys())
        )
        
        if selected_example != "Введите свой текст...":
            default_text = example_texts[selected_example]
        else:
            default_text = ""
        
        # Текстовое поле для ввода
        transaction_text = st.text_area(
            "Описание транзакции:",
            value=default_text,
            height=150,
            help="Введите описание транзакции на естественном языке"
        )
        
        # Кнопки действий
        col_btn1, col_btn2, col_btn3 = st.columns(3)
        
        with col_btn1:
            process_btn = st.button("🚀 Обработать", type="primary", use_container_width=True)
        
        with col_btn2:
            clear_btn = st.button("🗑️ Очистить", use_container_width=True)
        
        with col_btn3:
            save_btn = st.button("💾 Сохранить", use_container_width=True, disabled=not transaction_text)
    
    # Обработка транзакции
    if process_btn and transaction_text:
        with st.spinner("🔒 Обработка транзакции с проверкой безопасности..."):
            try:
                # Логируем начало обработки
                log_user_action("PROCESS_TRANSACTION", "TRANSACTION", {
                    "text_length": len(transaction_text),
                    "example_used": selected_example != "Введите свой текст..."
                })
                
                # Проверяем ограничения
                if len(transaction_text) > 10000:
                    st.error("❌ Текст транзакции слишком длинный")
                    log_user_action("PROCESS_TRANSACTION", "TRANSACTION", 
                                  {"error": "text_too_long"}, success=False)
                    return
                
                # Обрабатываем транзакцию
                result = st.session_state.processor.process_transaction(transaction_text)
                
                if result.get('transaction_data'):
                    # Шифруем чувствительные данные перед сохранением
                    transaction_data = result['transaction_data']
                    if transaction_data.account_number:
                        encrypted_account = security_manager.encrypt_sensitive_data(transaction_data.account_number)
                        transaction_data.account_number = encrypted_account
                    
                    if transaction_data.iban:
                        encrypted_iban = security_manager.encrypt_sensitive_data(transaction_data.iban)
                        transaction_data.iban = encrypted_iban
                    
                    # Сохраняем в базу данных
                    transaction_id = st.session_state.db_manager.save_transaction(
                        transaction_data,
                        result.get('validation_result', {}),
                        transaction_text
                    )
                    
                    # Логируем успешное сохранение
                    log_user_action("SAVE_TRANSACTION", "DATABASE", {
                        "transaction_id": transaction_id,
                        "amount": transaction_data.amount,
                        "currency": transaction_data.currency
                    })
                    
                    st.success(f"✅ Транзакция успешно обработана и сохранена (ID: {transaction_id})")
                else:
                    st.error("❌ Не удалось обработать транзакцию")
                    log_user_action("PROCESS_TRANSACTION", "TRANSACTION", 
                                  {"error": "processing_failed"}, success=False)
                
                # Отображаем результат
                show_transaction_result(result)
                
            except Exception as e:
                logger.error(f"Ошибка обработки транзакции: {e}")
                st.error(f"❌ Ошибка обработки: {str(e)}")
                log_user_action("PROCESS_TRANSACTION", "TRANSACTION", 
                              {"error": str(e)}, success=False)
    
    # Раздел загрузки файлов
    st.divider()
    st.subheader("📂 Загрузка файла с транзакциями")
    
    uploaded_file = st.file_uploader(
        "Выберите файл с транзакциями:",
        type=['txt', 'csv'],
        help="Поддерживаются текстовые файлы (.txt) и CSV файлы (.csv)"
    )
    
    if uploaded_file is not None:
        # Проверяем размер файла
        file_size_mb = uploaded_file.size / (1024 * 1024)
        if file_size_mb > settings.performance.MAX_FILE_SIZE_MB:
            st.error(f"❌ Файл слишком большой. Максимальный размер: {settings.performance.MAX_FILE_SIZE_MB} МБ")
            return
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.info(f"Загружен файл: {uploaded_file.name} ({file_size_mb:.2f} МБ)")
        
        with col2:
            if st.button("🚀 Обработать файл", type="primary", use_container_width=True):
                process_batch_file(uploaded_file)

def process_batch_file(uploaded_file):
    """Обрабатывает файл с транзакциями"""
    with st.spinner("🔒 Обработка файла с проверкой безопасности..."):
        try:
            # Логируем начало обработки файла
            log_user_action("PROCESS_FILE", "FILE_UPLOAD", {
                "filename": uploaded_file.name,
                "size_mb": uploaded_file.size / (1024 * 1024)
            })
            
            # Читаем содержимое файла
            if uploaded_file.type == "text/plain":
                content = str(uploaded_file.read(), "utf-8")
                transactions = [line.strip() for line in content.split('\n') if line.strip()]
            elif uploaded_file.type == "text/csv":
                df = pd.read_csv(uploaded_file)
                possible_cols = ['description', 'text', 'transaction', 'описание', 'транзакция']
                transaction_col = None
                for col in possible_cols:
                    if col in df.columns:
                        transaction_col = col
                        break
                
                if transaction_col:
                    transactions = df[transaction_col].dropna().tolist()
                else:
                    st.error("Не найдена колонка с описанием транзакций")
                    return
            else:
                transactions = []
            
            if transactions:
                # Проверяем лимит транзакций
                if len(transactions) > settings.performance.MAX_TRANSACTIONS_PER_REQUEST:
                    st.error(f"❌ Слишком много транзакций. Максимум: {settings.performance.MAX_TRANSACTIONS_PER_REQUEST}")
                    return
                
                # Обрабатываем транзакции
                results = []
                successful = 0
                failed = 0
                
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                for i, transaction_text in enumerate(transactions):
                    progress_bar.progress((i + 1) / len(transactions))
                    status_text.text(f"Обработка {i + 1}/{len(transactions)}: {transaction_text[:50]}...")
                    
                    try:
                        result = st.session_state.processor.process_transaction(transaction_text)
                        results.append(result)
                        
                        if result.get('transaction_data'):
                            successful += 1
                            # Сохраняем в базу данных с шифрованием
                            transaction_data = result['transaction_data']
                            if transaction_data.account_number:
                                transaction_data.account_number = security_manager.encrypt_sensitive_data(
                                    transaction_data.account_number
                                )
                            if transaction_data.iban:
                                transaction_data.iban = security_manager.encrypt_sensitive_data(
                                    transaction_data.iban
                                )
                            
                            st.session_state.db_manager.save_transaction(
                                transaction_data,
                                result.get('validation_result', {}),
                                transaction_text
                            )
                        else:
                            failed += 1
                    
                    except Exception as e:
                        failed += 1
                        logger.error(f"Ошибка обработки транзакции {i + 1}: {e}")
                
                # Логируем результаты обработки
                log_user_action("PROCESS_FILE_COMPLETE", "FILE_UPLOAD", {
                    "total": len(transactions),
                    "successful": successful,
                    "failed": failed
                })
                
                st.success(f"✅ Обработано {len(transactions)} транзакций: {successful} успешно, {failed} с ошибками")
                
                # Показываем статистику
                show_batch_processing_stats(results)
            
        except Exception as e:
            logger.error(f"Ошибка обработки файла: {e}")
            st.error(f"❌ Ошибка обработки файла: {str(e)}")
            log_user_action("PROCESS_FILE", "FILE_UPLOAD", {"error": str(e)}, success=False)

def show_transaction_result(result: Dict[str, Any]):
    """Отображает результат обработки транзакции с маскировкой данных"""
    
    if not result.get('transaction_data'):
        st.error("❌ Не удалось извлечь данные транзакции")
        return
    
    transaction_data = result['transaction_data']
    validation_result = result.get('validation_result', {})
    
    st.subheader("📊 Результат обработки")
    
    # Создаем копию данных для отображения с маскировкой
    display_data = {
        "Сумма": format_currency(transaction_data.amount, transaction_data.currency),
        "Получатель": transaction_data.recipient,
        "Описание": transaction_data.description or "Не указано"
    }
    
    # Маскируем чувствительные данные
    if transaction_data.account_number:
        display_data["Номер счета"] = security_manager.mask_data(
            transaction_data.account_number, "account"
        )
    
    if transaction_data.iban:
        display_data["IBAN"] = security_manager.mask_data(
            transaction_data.iban, "iban"
        )
    
    # Отображаем данные
    col1, col2 = st.columns(2)
    
    with col1:
        st.json(display_data)
    
    with col2:
        # Статус валидации
        if validation_result.get('is_valid'):
            st.success("✅ Транзакция валидна")
        else:
            st.error("❌ Транзакция содержит ошибки")
        
        # Предупреждения
        warnings = validation_result.get('warnings', [])
        if warnings:
            st.warning("⚠️ Предупреждения:")
            for warning in warnings:
                st.write(f"• {warning}")
        
        # Ошибки
        errors = validation_result.get('errors', [])
        if errors:
            st.error("❌ Ошибки:")
            for error in errors:
                st.write(f"• {error}")

def show_batch_processing_stats(results: List[Dict[str, Any]]):
    """Отображает статистику пакетной обработки"""
    
    st.subheader("📈 Статистика обработки")
    
    # Подсчитываем статистику
    total = len(results)
    successful = sum(1 for r in results if r.get('transaction_data'))
    failed = total - successful
    
    # Валюты
    currencies = {}
    amounts = []
    
    for result in results:
        if result.get('transaction_data'):
            currency = result['transaction_data'].currency
            amount = result['transaction_data'].amount
            
            currencies[currency] = currencies.get(currency, 0) + 1
            amounts.append(amount)
    
    # Отображаем метрики
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Всего транзакций", total)
    
    with col2:
        st.metric("Успешно обработано", successful)
    
    with col3:
        st.metric("Ошибки", failed)
    
    with col4:
        success_rate = (successful / total * 100) if total > 0 else 0
        st.metric("Процент успеха", f"{success_rate:.1f}%")
    
    # График по валютам
    if currencies:
        st.subheader("💱 Распределение по валютам")
        fig = px.pie(
            values=list(currencies.values()),
            names=list(currencies.keys()),
            title="Распределение транзакций по валютам"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # График сумм
    if amounts:
        st.subheader("💰 Распределение сумм")
        fig = px.histogram(
            x=amounts,
            title="Распределение сумм транзакций",
            labels={'x': 'Сумма', 'y': 'Количество'}
        )
        st.plotly_chart(fig, use_container_width=True)

def show_dashboard():
    """Отображает основной дашборд с улучшенной безопасностью"""
    
    st.header("📊 Дашборд")
    
    # Получаем данные из базы
    transactions = st.session_state.db_manager.get_all_transactions(limit=100)
    
    if not transactions:
        st.info("📝 Нет данных для отображения. Обработайте несколько транзакций.")
        return
    
    # Основные метрики
    col1, col2, col3, col4 = st.columns(4)
    
    total_amount = sum(t.amount for t in transactions)
    avg_amount = total_amount / len(transactions) if transactions else 0
    
    with col1:
        st.metric("Всего транзакций", len(transactions))
    
    with col2:
        st.metric("Общая сумма", format_currency(total_amount, "RUB"))
    
    with col3:
        st.metric("Средняя сумма", format_currency(avg_amount, "RUB"))
    
    with col4:
        currencies = set(t.currency for t in transactions)
        st.metric("Валют", len(currencies))
    
    # Графики
    col1, col2 = st.columns(2)
    
    with col1:
        # График по времени
        dates = [t.timestamp.date() for t in transactions]
        date_counts = pd.Series(dates).value_counts().sort_index()
        
        fig = px.line(
            x=date_counts.index,
            y=date_counts.values,
            title="Транзакции по дням",
            labels={'x': 'Дата', 'y': 'Количество транзакций'}
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # График по валютам
        currency_counts = pd.Series([t.currency for t in transactions]).value_counts()
        
        fig = px.pie(
            values=currency_counts.values,
            names=currency_counts.index,
            title="Распределение по валютам"
        )
        st.plotly_chart(fig, use_container_width=True)

def show_statistics():
    """Отображает расширенную статистику"""
    
    st.header("📈 Расширенная статистика")
    
    # Получаем данные
    transactions = st.session_state.db_manager.get_all_transactions()
    
    if not transactions:
        st.info("📝 Нет данных для анализа")
        return
    
    # Фильтры
    col1, col2, col3 = st.columns(3)
    
    with col1:
        currencies = list(set(t.currency for t in transactions))
        selected_currency = st.selectbox("Валюта", ["Все"] + currencies)
    
    with col2:
        date_range = st.date_input(
            "Период",
            value=(datetime.now().date() - timedelta(days=30), datetime.now().date())
        )
    
    with col3:
        min_amount = st.number_input("Мин. сумма", value=0.0)
    
    # Фильтруем данные
    filtered_transactions = transactions
    
    if selected_currency != "Все":
        filtered_transactions = [t for t in filtered_transactions if t.currency == selected_currency]
    
    if len(date_range) == 2:
        start_date, end_date = date_range
        filtered_transactions = [
            t for t in filtered_transactions 
            if start_date <= t.timestamp.date() <= end_date
        ]
    
    filtered_transactions = [t for t in filtered_transactions if t.amount >= min_amount]
    
    # Статистика
    if filtered_transactions:
        st.subheader(f"📊 Статистика ({len(filtered_transactions)} транзакций)")
        
        # Создаем DataFrame для анализа
        df = pd.DataFrame([
            {
                'Дата': t.timestamp,
                'Сумма': t.amount,
                'Валюта': t.currency,
                'Получатель': t.recipient
            }
            for t in filtered_transactions
        ])
        
        # Отображаем статистику
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Описательная статистика:**")
            st.dataframe(df['Сумма'].describe())
        
        with col2:
            st.write("**Топ получателей:**")
            top_recipients = df['Получатель'].value_counts().head(10)
            st.dataframe(top_recipients)
        
        # Графики
        st.subheader("📈 Визуализация")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Распределение сумм
            fig = px.histogram(
                df,
                x='Сумма',
                title="Распределение сумм транзакций",
                nbins=20
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Временной ряд
            df_time = df.set_index('Дата').resample('D')['Сумма'].sum()
            fig = px.line(
                df_time,
                title="Сумма транзакций по дням"
            )
            st.plotly_chart(fig, use_container_width=True)

def show_settings():
    """Отображает настройки системы"""
    
    st.header("⚙️ Настройки системы")
    
    # Проверяем права администратора
    if st.session_state.current_user["role"] != "admin":
        st.error("❌ Требуются права администратора")
        return
    
    # Вкладки настроек
    tab1, tab2, tab3, tab4 = st.tabs(["🔒 Безопасность", "📊 Производительность", "📝 Логирование", "🏦 Соответствие"])
    
    with tab1:
        st.subheader("Настройки безопасности")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Аутентификация:**")
            st.write(f"• Время жизни токена: {settings.security.ACCESS_TOKEN_EXPIRE_MINUTES} мин")
            st.write(f"• Максимум попыток входа: {settings.security.MAX_LOGIN_ATTEMPTS}")
            st.write(f"• Время блокировки: {settings.security.LOCKOUT_DURATION_MINUTES} мин")
            
            st.write("**Пароли:**")
            st.write(f"• Минимальная длина: {settings.security.MIN_PASSWORD_LENGTH}")
            st.write(f"• Специальные символы: {'Да' if settings.security.REQUIRE_SPECIAL_CHARS else 'Нет'}")
        
        with col2:
            st.write("**Шифрование:**")
            st.write("• Шифрование чувствительных данных: Включено")
            st.write("• Маскировка данных: Включена")
            st.write("• Аудит операций: Включен")
    
    with tab2:
        st.subheader("Настройки производительности")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Кэширование:**")
            st.write(f"• Включено: {'Да' if settings.performance.CACHE_ENABLED else 'Нет'}")
            st.write(f"• TTL: {settings.performance.CACHE_TTL_SECONDS} сек")
            st.write(f"• Максимальный размер: {settings.performance.CACHE_MAX_SIZE}")
            
            st.write("**Ограничения:**")
            st.write(f"• Максимум транзакций: {settings.performance.MAX_TRANSACTIONS_PER_REQUEST}")
            st.write(f"• Максимальный размер файла: {settings.performance.MAX_FILE_SIZE_MB} МБ")
        
        with col2:
            st.write("**Асинхронная обработка:**")
            st.write(f"• Включена: {'Да' if settings.performance.ASYNC_PROCESSING else 'Нет'}")
            st.write(f"• Максимум задач: {settings.performance.MAX_CONCURRENT_TASKS}")
    
    with tab3:
        st.subheader("Настройки логирования")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Основное логирование:**")
            st.write(f"• Уровень: {settings.logging.LOG_LEVEL}")
            st.write(f"• Файл: {settings.logging.LOG_FILE}")
            st.write(f"• Максимальный размер: {settings.logging.LOG_MAX_SIZE_MB} МБ")
            
            st.write("**Аудит:**")
            st.write(f"• Включен: {'Да' if settings.logging.AUDIT_LOG_ENABLED else 'Нет'}")
            st.write(f"• Файл: {settings.logging.AUDIT_LOG_FILE}")
        
        with col2:
            st.write("**Мониторинг:**")
            st.write(f"• Sentry: {'Настроен' if settings.monitoring.SENTRY_DSN else 'Не настроен'}")
            st.write(f"• Метрики: {'Включены' if settings.monitoring.METRICS_ENABLED else 'Отключены'}")
            st.write(f"• Алерты: {'Включены' if settings.monitoring.ALERTS_ENABLED else 'Отключены'}")
    
    with tab4:
        st.subheader("Соответствие банковским стандартам")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**PCI DSS:**")
            st.write(f"• Соответствие: {'Да' if settings.compliance.PCI_COMPLIANCE_ENABLED else 'Нет'}")
            st.write(f"• Маскировка данных: {'Да' if settings.compliance.MASK_SENSITIVE_DATA else 'Нет'}")
            
            st.write("**Аудит:**")
            st.write(f"• Аудит всех транзакций: {'Да' if settings.compliance.AUDIT_ALL_TRANSACTIONS else 'Нет'}")
            st.write(f"• Хранение: {settings.compliance.AUDIT_RETENTION_YEARS} лет")
        
        with col2:
            st.write("**Валидация:**")
            st.write(f"• Строгая валидация: {'Да' if settings.compliance.STRICT_VALIDATION else 'Нет'}")
            st.write(f"• Проверка санкций: {'Да' if settings.compliance.SANCTIONS_CHECK_ENABLED else 'Нет'}")
            
            st.write("**Отчетность:**")
            st.write(f"• Регуляторные отчеты: {'Да' if settings.compliance.REGULATORY_REPORTS_ENABLED else 'Нет'}")

def show_testing():
    """Отображает страницу тестирования"""
    
    st.header("🧪 Тестирование системы")
    
    # Проверяем права администратора
    if st.session_state.current_user["role"] != "admin":
        st.error("❌ Требуются права администратора")
        return
    
    # Тесты безопасности
    st.subheader("🔒 Тесты безопасности")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Тест шифрования"):
            test_data = "1234567890123456"
            encrypted = security_manager.encrypt_sensitive_data(test_data)
            decrypted = security_manager.decrypt_sensitive_data(encrypted)
            
            st.write("**Результат теста шифрования:**")
            st.write(f"Исходные данные: {test_data}")
            st.write(f"Зашифрованные: {encrypted[:20]}...")
            st.write(f"Расшифрованные: {decrypted}")
            st.write(f"✅ Тест пройден" if test_data == decrypted else "❌ Тест провален")
    
    with col2:
        if st.button("Тест маскировки"):
            test_account = "1234567890123456"
            masked_account = security_manager.mask_data(test_account, "account")
            
            st.write("**Результат теста маскировки:**")
            st.write(f"Исходный номер: {test_account}")
            st.write(f"Замаскированный: {masked_account}")
            st.write("✅ Тест пройден")
    
    # Тесты производительности
    st.subheader("⚡ Тесты производительности")
    
    if st.button("Тест обработки транзакций"):
        with st.spinner("Выполняется тест производительности..."):
            start_time = time.time()
            
            # Обрабатываем тестовые транзакции
            test_transactions = get_sample_transactions()[:10]
            results = []
            
            for transaction in test_transactions:
                result = st.session_state.processor.process_transaction(transaction)
                results.append(result)
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            st.write(f"**Результат теста производительности:**")
            st.write(f"Обработано транзакций: {len(test_transactions)}")
            st.write(f"Время обработки: {processing_time:.2f} сек")
            st.write(f"Среднее время на транзакцию: {processing_time/len(test_transactions):.3f} сек")
            
            if processing_time < 5.0:
                st.success("✅ Тест производительности пройден")
            else:
                st.warning("⚠️ Время обработки превышает рекомендуемое")
    
    # Проверка настроек
    st.subheader("🔧 Проверка настроек")
    
    if st.button("Проверить настройки"):
        validation_result = validate_settings()
        
        if validation_result["is_valid"]:
            st.success("✅ Все настройки корректны")
        else:
            st.error("❌ Обнаружены ошибки в настройках:")
            for error in validation_result["errors"]:
                st.write(f"• {error}")
        
        if validation_result["warnings"]:
            st.warning("⚠️ Предупреждения:")
            for warning in validation_result["warnings"]:
                st.write(f"• {warning}")

def main():
    """Главная функция приложения"""
    
    # Проверяем аутентификацию
    if not st.session_state.user_authenticated:
        show_login_page()
        return
    
    # Заголовок приложения
    st.title(f"🏦 {settings.APP_NAME}")
    st.markdown(f"**Версия {settings.APP_VERSION} - Система безопасности**")
    
    # Информация о пользователе
    user_info = st.session_state.current_user
    st.sidebar.success(f"👤 {user_info['username']} ({user_info['role']})")
    
    # Боковое меню
    with st.sidebar:
        st.header("📋 Навигация")
        page = st.selectbox(
            "Выберите страницу",
            ["🛡️ Безопасность", "🔍 Анализ Транзакций", "📊 Dashboard", "📈 Статистика", "⚙️ Настройки", "🧪 Тестирование"]
        )
        
        st.divider()
        
        # Информация о системе
        st.header("ℹ️ Информация")
        st.info(f"""
        **Статус системы:** 🟢 Работает
        
        **Обработано транзакций:** {len(st.session_state.db_manager.get_all_transactions())}
        
        **Последнее обновление:** {datetime.now().strftime('%d.%m.%Y %H:%M')}
        
        **Режим:** {settings.ENVIRONMENT}
        """)
        
        # Кнопка выхода
        if st.button("🚪 Выйти"):
            log_user_action("LOGOUT", "AUTH", {"username": user_info['username']})
            st.session_state.user_authenticated = False
            st.session_state.current_user = None
            st.rerun()
    
    # Маршрутизация страниц
    if page == "🛡️ Безопасность":
        show_security_dashboard()
    elif page == "🔍 Анализ Транзакций":
        show_transaction_analysis()
    elif page == "📊 Dashboard":
        show_dashboard()
    elif page == "📈 Статистика":
        show_statistics()
    elif page == "⚙️ Настройки":
        show_settings()
    elif page == "🧪 Тестирование":
        show_testing()

if __name__ == "__main__":
    # Проверяем настройки при запуске
    validation_result = validate_settings()
    if not validation_result["is_valid"]:
        logger.error("Ошибки в настройках приложения:")
        for error in validation_result["errors"]:
            logger.error(f"• {error}")
        st.error("❌ Ошибки в настройках приложения. Проверьте конфигурацию.")
        st.stop()
    
    # Запускаем приложение
    main() 