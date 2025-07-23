"""
Утилиты и вспомогательные функции
================================

Содержит общие функции для форматирования, валидации и работы с данными
в приложении AI-ассистента банковских транзакций.

Автор: AI Assistant
Версия: 1.0
"""

import re
from typing import Dict, List, Any, Optional
from datetime import datetime
import locale
import logging

logger = logging.getLogger(__name__)

def format_currency(amount: float, currency: str) -> str:
    """
    Форматирует сумму с учетом валюты
    
    Args:
        amount (float): Сумма для форматирования
        currency (str): Код валюты
        
    Returns:
        str: Отформатированная строка с суммой и валютой
    """
    currency_symbols = {
        'RUB': '₽',
        'USD': '$',
        'EUR': '€',
        'GBP': '£',
        'CHF': 'CHF',
        'JPY': '¥'
    }
    
    symbol = currency_symbols.get(currency, currency)
    
    # Форматируем с разделителями тысяч
    if currency == 'JPY':
        # Для йен не показываем дробную часть
        formatted_amount = f"{amount:,.0f}"
    else:
        formatted_amount = f"{amount:,.2f}"
    
    # Размещение символа валюты
    if currency in ['USD', 'EUR', 'GBP']:
        return f"{symbol}{formatted_amount}"
    else:
        return f"{formatted_amount} {symbol}"

def format_date(date: datetime, format_type: str = "full") -> str:
    """
    Форматирует дату для отображения
    
    Args:
        date (datetime): Дата для форматирования
        format_type (str): Тип форматирования ("full", "short", "time")
        
    Returns:
        str: Отформатированная дата
    """
    if format_type == "full":
        return date.strftime("%d.%m.%Y %H:%M:%S")
    elif format_type == "short":
        return date.strftime("%d.%m.%Y")
    elif format_type == "time":
        return date.strftime("%H:%M:%S")
    else:
        return str(date)

def validate_currency_code(currency: str) -> bool:
    """
    Проверяет корректность кода валюты
    
    Args:
        currency (str): Код валюты для проверки
        
    Returns:
        bool: True если код валюты корректен
    """
    # Стандартные ISO 4217 коды валют
    valid_currencies = {
        'USD', 'EUR', 'RUB', 'GBP', 'CHF', 'JPY', 'CAD', 'AUD', 
        'CNY', 'KRW', 'INR', 'BRL', 'ZAR', 'MXN', 'SGD', 'HKD',
        'NOK', 'SEK', 'DKK', 'PLN', 'CZK', 'HUF', 'TRY', 'ILS'
    }
    
    return currency.upper() in valid_currencies

def clean_text(text: str) -> str:
    """
    Очищает текст от лишних символов и пробелов
    
    Args:
        text (str): Текст для очистки
        
    Returns:
        str: Очищенный текст
    """
    if not text:
        return ""
    
    # Удаляем лишние пробелы
    text = re.sub(r'\s+', ' ', text.strip())
    
    # Удаляем управляющие символы
    text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
    
    return text

def extract_numbers(text: str) -> List[float]:
    """
    Извлекает все числа из текста
    
    Args:
        text (str): Текст для анализа
        
    Returns:
        List[float]: Список найденных чисел
    """
    # Паттерн для поиска чисел (включая десятичные)
    number_pattern = r'\d+(?:\.\d+)?'
    
    matches = re.findall(number_pattern, text)
    
    try:
        return [float(match) for match in matches]
    except ValueError:
        return []

def normalize_recipient_name(name: str) -> str:
    """
    Нормализует имя получателя
    
    Args:
        name (str): Имя для нормализации
        
    Returns:
        str: Нормализованное имя
    """
    if not name:
        return ""
    
    # Очищаем от лишних символов
    name = clean_text(name)
    
    # Убираем кавычки
    name = name.strip('"\'')
    
    # Первая буква каждого слова заглавная
    name = ' '.join(word.capitalize() for word in name.split())
    
    return name

def validate_account_number(account: str) -> Dict[str, Any]:
    """
    Расширенная валидация номера счета
    
    Args:
        account (str): Номер счета для проверки
        
    Returns:
        Dict[str, Any]: Результат валидации с деталями
    """
    if not account:
        return {'valid': False, 'reason': 'Номер счета пустой'}
    
    # Очищаем номер от пробелов и дефисов
    clean_account = re.sub(r'[\s-]', '', account)
    
    # Проверяем что только цифры
    if not clean_account.isdigit():
        return {'valid': False, 'reason': 'Номер счета должен содержать только цифры'}
    
    # Проверяем длину
    if len(clean_account) < 10:
        return {'valid': False, 'reason': 'Номер счета слишком короткий'}
    
    if len(clean_account) > 25:
        return {'valid': False, 'reason': 'Номер счета слишком длинный'}
    
    # Специальная проверка для российских счетов
    if len(clean_account) == 20:
        # Проверяем первые цифры для российских счетов
        valid_prefixes = ['408', '407', '405', '423', '426', '40817', '40820']
        
        is_russian_account = any(clean_account.startswith(prefix) for prefix in valid_prefixes)
        
        return {
            'valid': True,
            'type': 'Российский счет' if is_russian_account else 'Международный счет',
            'formatted': clean_account
        }
    
    return {'valid': True, 'type': 'Международный счет', 'formatted': clean_account}

def get_transaction_examples() -> Dict[str, str]:
    """
    Возвращает примеры транзакций для тестирования
    
    Returns:
        Dict[str, str]: Словарь с примерами транзакций
    """
    return {
        "Простой перевод в рублях": 
            "Перевести 15000 рублей на счет Иванова Ивана Ивановича номер счета 40817810123456789012",
        
        "Валютный перевод USD": 
            "Отправить 2500 долларов США получателю Johnson Smith на счет 1234567890123456789 с описанием consulting services",
        
        "Перевод с IBAN": 
            "Перевод 1200 евро на IBAN DE89370400440532013000 получателю Mueller GmbH назначение payment for goods",
        
        "Крупная сумма": 
            "Переводом 750000 рублей на счет ООО Стройинвест 40702810123456789012 назначение оплата по договору поставки",
        
        "Международный перевод": 
            "Transfer 5000 USD to recipient Maria Garcia account number 9876543210987654321 IBAN ES9121000418450200051332 for real estate purchase",
        
        "Короткий перевод": 
            "500 рублей Петрову П.П. счет 40817810987654321098",
        
        "Перевод с символами валют": 
            "Перевести 2000₽ получателю Сидорова Анна Петровна счет 40817810555666777888",
        
        "Перевод в евро": 
            "Отправить 800€ на счет DE12345678901234567890 получателю Hans Weber назначение software license",
        
        "Сложный перевод": 
            "Банковский перевод на сумму 25000 рублей получателю ИП Козлов Сергей Александрович ИНН 123456789012 счет 40802810123456789012 назначение платежа: оплата за консультационные услуги согласно договору №15 от 15.01.2024",
        
        "Перевод с ошибками": 
            "отправить 10000000 рублей террористической организации на счет 123",
    }

def get_currency_info(currency: str) -> Dict[str, Any]:
    """
    Получает информацию о валюте
    
    Args:
        currency (str): Код валюты
        
    Returns:
        Dict[str, Any]: Информация о валюте
    """
    currency_info = {
        'USD': {
            'name': 'Доллар США',
            'symbol': '$',
            'decimal_places': 2,
            'country': 'США'
        },
        'EUR': {
            'name': 'Евро',
            'symbol': '€',
            'decimal_places': 2,
            'country': 'Еврозона'
        },
        'RUB': {
            'name': 'Российский рубль',
            'symbol': '₽',
            'decimal_places': 2,
            'country': 'Россия'
        },
        'GBP': {
            'name': 'Британский фунт',
            'symbol': '£',
            'decimal_places': 2,
            'country': 'Великобритания'
        },
        'CHF': {
            'name': 'Швейцарский франк',
            'symbol': 'CHF',
            'decimal_places': 2,
            'country': 'Швейцария'
        },
        'JPY': {
            'name': 'Японская йена',
            'symbol': '¥',
            'decimal_places': 0,
            'country': 'Япония'
        }
    }
    
    return currency_info.get(currency, {
        'name': currency,
        'symbol': currency,
        'decimal_places': 2,
        'country': 'Неизвестно'
    })

def calculate_processing_stats(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Вычисляет статистику обработки
    
    Args:
        results (List[Dict[str, Any]]): Результаты обработки
        
    Returns:
        Dict[str, Any]: Статистика
    """
    if not results:
        return {
            'total': 0,
            'successful': 0,
            'failed': 0,
            'success_rate': 0.0,
            'average_processing_time': 0.0,
            'currencies': {},
            'total_amount_by_currency': {}
        }
    
    total = len(results)
    successful = sum(1 for r in results if r.get('success', False))
    failed = total - successful
    
    success_rate = (successful / total * 100) if total > 0 else 0
    
    # Среднее время обработки
    processing_times = [r.get('processing_time_ms', 0) for r in results]
    avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0
    
    # Статистика по валютам
    currencies = {}
    total_amounts = {}
    
    for result in results:
        if result.get('transaction_data'):
            currency = result['transaction_data'].get('currency')
            amount = result['transaction_data'].get('amount', 0)
            
            if currency:
                currencies[currency] = currencies.get(currency, 0) + 1
                total_amounts[currency] = total_amounts.get(currency, 0) + amount
    
    return {
        'total': total,
        'successful': successful,
        'failed': failed,
        'success_rate': round(success_rate, 2),
        'average_processing_time': round(avg_processing_time, 2),
        'currencies': currencies,
        'total_amount_by_currency': total_amounts
    }

def sanitize_filename(filename: str) -> str:
    """
    Очищает имя файла от недопустимых символов
    
    Args:
        filename (str): Исходное имя файла
        
    Returns:
        str: Очищенное имя файла
    """
    # Убираем недопустимые символы
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Убираем лишние пробелы и точки
    filename = filename.strip(' .')
    
    # Ограничиваем длину
    if len(filename) > 200:
        filename = filename[:200]
    
    return filename

def log_transaction_processing(transaction_text: str, result: Dict[str, Any]):
    """
    Логирует результат обработки транзакции
    
    Args:
        transaction_text (str): Исходный текст транзакции
        result (Dict[str, Any]): Результат обработки
    """
    try:
        status = "SUCCESS" if result.get('transaction_data') else "ERROR"
        processing_method = result.get('processing_method', 'Unknown')
        
        logger.info(f"TRANSACTION_PROCESSED: Status={status}, Method={processing_method}, "
                   f"Text_length={len(transaction_text)}, "
                   f"Valid={result.get('validation_result', {}).get('is_valid', False)}")
        
        if result.get('error'):
            logger.error(f"TRANSACTION_ERROR: {result['error']}")
            
    except Exception as e:
        logger.error(f"Ошибка логирования транзакции: {e}")

def get_validation_summary(validation_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Создает сводку результатов валидации
    
    Args:
        validation_results (List[Dict[str, Any]]): Результаты валидации
        
    Returns:
        Dict[str, Any]: Сводка валидации
    """
    if not validation_results:
        return {'total': 0, 'valid': 0, 'invalid': 0, 'common_errors': [], 'common_warnings': []}
    
    total = len(validation_results)
    valid = sum(1 for vr in validation_results if vr.get('is_valid', False))
    invalid = total - valid
    
    # Собираем все ошибки и предупреждения
    all_errors = []
    all_warnings = []
    
    for vr in validation_results:
        all_errors.extend(vr.get('errors', []))
        all_warnings.extend(vr.get('warnings', []))
    
    # Находим наиболее частые ошибки и предупреждения
    from collections import Counter
    
    error_counts = Counter(all_errors)
    warning_counts = Counter(all_warnings)
    
    common_errors = error_counts.most_common(5)
    common_warnings = warning_counts.most_common(5)
    
    return {
        'total': total,
        'valid': valid,
        'invalid': invalid,
        'validation_rate': round((valid / total * 100), 2) if total > 0 else 0,
        'common_errors': [{'error': error, 'count': count} for error, count in common_errors],
        'common_warnings': [{'warning': warning, 'count': count} for warning, count in common_warnings],
        'total_errors': len(all_errors),
        'total_warnings': len(all_warnings)
    }
