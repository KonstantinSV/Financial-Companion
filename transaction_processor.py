"""
AI-ассистент для обработки межбанковских транзакций (улучшенная версия)
=====================================================================

Этот модуль предоставляет функциональность для:
- Извлечения структурированных данных из текста транзакций
- Валидации транзакций по бизнес-правилам
- Интеграции с LLM через LangChain
- Обработки ошибок и логирования

"""

import pandas as pd
import json
import logging
import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import os
from pathlib import Path

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('transactions.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class TransactionData:
    """
    Структура данных для хранения информации о транзакции
    
    Атрибуты:
        amount (float): Сумма транзакции
        currency (str): Валюта (USD, EUR, RUB и т.д.)
        recipient (str): Имя получателя
        account_number (Optional[str]): Номер счета получателя
        iban (Optional[str]): IBAN код (для международных переводов)
        description (Optional[str]): Описание транзакции
        timestamp (datetime): Время создания записи
    """
    amount: float
    currency: str
    recipient: str
    account_number: Optional[str] = None
    iban: Optional[str] = None
    description: Optional[str] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        """Инициализация временной метки при создании объекта"""
        if self.timestamp is None:
            self.timestamp = datetime.now()

class TransactionParser:
    """
    Парсер для извлечения структурированных данных из текста транзакций
    
    Работает как с ответами LLM, так и с обычным текстом через regex
    """
    
    def parse(self, text: str) -> TransactionData:
        """
        Парсит текст и извлекает данные транзакции
        
        Args:
            text (str): Текст для анализа (ответ LLM или обычный текст)
            
        Returns:
            TransactionData: Структурированные данные транзакции
            
        Raises:
            ValueError: Если не удается извлечь обязательные поля
        """
        try:
            # Пытаемся найти JSON в ответе
            if '{' in text and '}' in text:
                start = text.find('{')
                end = text.rfind('}') + 1
                json_str = text[start:end]
                data = json.loads(json_str)
            else:
                # Если JSON не найден, извлекаем данные с помощью регулярных выражений
                data = self._extract_with_regex(text)
            
            # Валидация обязательных полей
            if 'amount' not in data or 'currency' not in data or 'recipient' not in data:
                raise ValueError("Отсутствуют обязательные поля: amount, currency, recipient")
            
            return TransactionData(
                amount=float(data['amount']),
                currency=data['currency'].upper(),
                recipient=data['recipient'],
                account_number=data.get('account_number'),
                iban=data.get('iban'),
                description=data.get('description')
            )
            
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            logger.error(f"Ошибка парсинга ответа: {e}")
            raise ValueError(f"Не удалось извлечь данные из текста: {text}")

    def _extract_with_regex(self, text: str) -> Dict[str, Any]:
        """
        Извлекает данные с помощью улучшенных регулярных выражений
        
        Args:
            text (str): Текст для анализа
            
        Returns:
            Dict[str, Any]: Извлеченные данные
        """
        
        # Улучшенные паттерны для извлечения данных
        patterns = {
            'amount_rub': r'(\d+(?:\.\d+)?)\s*(?:рубл|₽|руб|RUB)',
            'amount_usd': r'(\d+(?:\.\d+)?)\s*(?:доллар|\$|USD)',
            'amount_eur': r'(\d+(?:\.\d+)?)\s*(?:евро|€|EUR)',
            'recipient': r'(?:получател[ьюя]|кому|для|на имя|recipient|to)[:\s]*([А-Яа-яA-Za-z\s]+?)(?:\s|$|,|на счет|счет|IBAN)',
            'account': r'(?:счет|счёт|account)[:\s]*(\d{10,20})',
            'iban': r'(?:IBAN|iban)[:\s]*([A-Z]{2}\d{2}[A-Z0-9]{4,30})',
            'description': r'(?:назначение|описание|комментарий|цель|для|purpose)[:\s]*([^,\n]+)'
        }
        
        # Извлечение суммы и валюты
        amount = None
        currency = None
        
        for curr_type, pattern in [('RUB', patterns['amount_rub']), 
                                  ('USD', patterns['amount_usd']), 
                                  ('EUR', patterns['amount_eur'])]:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amount = float(match.group(1))
                currency = curr_type
                break
        
        # Если не найдена валюта, ищем просто число
        if amount is None:
            amount_match = re.search(r'(\d+(?:\.\d+)?)', text)
            if amount_match:
                amount = float(amount_match.group(1))
                currency = 'RUB'  # По умолчанию рубли
        
        if amount is None:
            raise ValueError("Не удалось извлечь сумму из текста")
        
        # Извлечение получателя
        recipient_match = re.search(patterns['recipient'], text, re.IGNORECASE)
        recipient = recipient_match.group(1).strip() if recipient_match else 'Неизвестный получатель'
        
        # Очистка имени получателя
        recipient = re.sub(r'\s+', ' ', recipient)
        recipient = recipient.strip('.,!?;:')
        
        # Извлечение номера счета
        account_match = re.search(patterns['account'], text, re.IGNORECASE)
        account_number = account_match.group(1) if account_match else None
        
        # Извлечение IBAN
        iban_match = re.search(patterns['iban'], text, re.IGNORECASE)
        iban = iban_match.group(1) if iban_match else None
        
        # Извлечение описания
        description_match = re.search(patterns['description'], text, re.IGNORECASE)
        description = description_match.group(1).strip() if description_match else None
        
        return {
            'amount': amount,
            'currency': currency,
            'recipient': recipient,
            'account_number': account_number,
            'iban': iban,
            'description': description
        }

class TransactionValidator:
    """
    Класс для валидации транзакций по бизнес-правилам
    """
    
    def __init__(self):
        """Инициализация правил валидации"""
        # Максимальные суммы для разных валют
        self.max_amounts = {
            'USD': 10000,
            'EUR': 8500,
            'RUB': 750000
        }
        
        # Запрещенные получатели (ключевые слова)
        self.blocked_recipients = [
            'санкции', 'санкционный', 'blocked', 'forbidden',
            'террор', 'экстремизм', 'наркотик', 'оружие'
        ]
        
        # Минимальные суммы
        self.min_amounts = {
            'USD': 1,
            'EUR': 1,
            'RUB': 100
        }
        
        # Поддерживаемые валюты
        self.supported_currencies = ['USD', 'EUR', 'RUB', 'GBP', 'CHF', 'JPY']
    
    def validate_transaction(self, transaction: TransactionData) -> Dict[str, Any]:
        """
        Валидирует транзакцию по всем правилам
        
        Args:
            transaction (TransactionData): Данные транзакции для проверки
            
        Returns:
            Dict[str, Any]: Результат валидации с деталями
        """
        errors = []
        warnings = []
        
        # Проверка валюты
        if transaction.currency not in self.supported_currencies:
            warnings.append(f"Валюта {transaction.currency} не входит в список поддерживаемых")
        
        # Проверка суммы
        currency = transaction.currency
        if currency in self.max_amounts:
            if transaction.amount > self.max_amounts[currency]:
                errors.append(f"Сумма {transaction.amount} {currency} превышает лимит {self.max_amounts[currency]} {currency}")
            
            if transaction.amount < self.min_amounts[currency]:
                errors.append(f"Сумма {transaction.amount} {currency} меньше минимальной {self.min_amounts[currency]} {currency}")
        
        # Проверка получателя
        recipient_lower = transaction.recipient.lower()
        for blocked in self.blocked_recipients:
            if blocked in recipient_lower:
                errors.append(f"Получатель '{transaction.recipient}' содержит недопустимые ключевые слова")
                break
        
        # Проверка длины имени получателя
        if len(transaction.recipient) < 2:
            errors.append("Имя получателя слишком короткое")
        elif len(transaction.recipient) > 100:
            warnings.append("Имя получателя очень длинное")
        
        # Проверка IBAN (если есть)
        if transaction.iban:
            if not self._validate_iban(transaction.iban):
                warnings.append(f"IBAN {transaction.iban} может быть некорректным")
        
        # Проверка номера счета
        if transaction.account_number:
            if not self._validate_account_number(transaction.account_number):
                warnings.append(f"Номер счета {transaction.account_number} может быть некорректным")
        
        # Проверка на подозрительные суммы
        if currency == 'RUB' and transaction.amount > 100000:
            warnings.append("Крупная сумма перевода, возможна дополнительная проверка")
        elif currency in ['USD', 'EUR'] and transaction.amount > 5000:
            warnings.append("Крупная валютная операция, возможна дополнительная проверка")
        
        return {
            'is_valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'transaction': transaction
        }
    
    def _validate_iban(self, iban: str) -> bool:
        """
        Улучшенная валидация IBAN
        
        Args:
            iban (str): IBAN для проверки
            
        Returns:
            bool: True если IBAN корректен
        """
        # Убираем пробелы
        iban = iban.replace(' ', '').upper()
        
        # Проверка длины
        if len(iban) < 15 or len(iban) > 34:
            return False
        
        # Проверка формата: 2 буквы (код страны) + 2 цифры (контрольные) + остальное
        if not re.match(r'^[A-Z]{2}\d{2}[A-Z0-9]+$', iban):
            return False
        
        # Дополнительная проверка для известных стран
        country_lengths = {
            'RU': 33,  # Россия
            'DE': 22,  # Германия
            'FR': 27,  # Франция
            'GB': 22,  # Великобритания
            'US': 0,   # США не используют IBAN
        }
        
        country_code = iban[:2]
        if country_code in country_lengths:
            expected_length = country_lengths[country_code]
            if expected_length > 0 and len(iban) != expected_length:
                return False
        
        return True
    
    def _validate_account_number(self, account: str) -> bool:
        """
        Улучшенная валидация номера счета
        
        Args:
            account (str): Номер счета для проверки
            
        Returns:
            bool: True если номер корректен
        """
        # Убираем пробелы и дефисы
        clean_account = re.sub(r'[\s-]', '', account)
        
        # Проверяем что только цифры
        if not clean_account.isdigit():
            return False
        
        # Проверяем длину (для российских счетов обычно 20 цифр)
        if len(clean_account) < 10 or len(clean_account) > 25:
            return False
        
        # Для российских счетов дополнительная проверка
        if len(clean_account) == 20:
            # Проверяем что начинается с правильных цифр
            if clean_account.startswith(('408', '407', '405', '423', '426')):
                return True
        
        return len(clean_account) >= 10

class TransactionProcessor:
    """
    Основной класс для обработки транзакций с поддержкой LLM и fallback-режима
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Инициализация процессора транзакций
        
        Args:
            api_key (Optional[str]): API ключ для Hugging Face
        """
        self.api_key = api_key or os.getenv("HUGGINGFACEHUB_API_TOKEN")
        
        # Пытаемся инициализировать LLM
        self.llm = None
        if self.api_key:
            try:
                # Попытка импорта LangChain компонентов
                from langchain.llms import HuggingFaceHub
                from langchain.prompts import PromptTemplate
                
                self.llm = HuggingFaceHub(
                    repo_id="mistralai/Mixtral-8x7B-Instruct-v0.1",
                    model_kwargs={"temperature": 0.3},
                    huggingfacehub_api_token=self.api_key
                )
                logger.info("LLM успешно инициализирован")
                
                # Шаблон промпта для извлечения данных
                self.prompt_template = PromptTemplate(
                    input_variables=["text"],
                    template="""
Извлеки из следующего текста информацию о банковской транзакции и верни результат в формате JSON.

Текст транзакции: {text}

Верни JSON со следующими полями:
- amount: сумма (число)
- currency: валюта (USD, EUR, RUB и т.д.)
- recipient: имя получателя
- account_number: номер счета (если есть)
- iban: IBAN код (если есть)
- description: описание платежа (если есть)

Ответ должен содержать только валидный JSON без дополнительного текста.
"""
                )
                
            except ImportError:
                logger.warning("LangChain не найден, работаем без LLM")
                self.llm = None
            except Exception as e:
                logger.error(f"Ошибка инициализации LLM: {e}")
                self.llm = None
        else:
            logger.warning("API ключ не найден. Используется режим без LLM.")
        
        # Инициализация компонентов
        self.parser = TransactionParser()
        self.validator = TransactionValidator()
    
    def process_transaction(self, text: str) -> Dict[str, Any]:
        """
        Обрабатывает транзакцию: извлекает данные и валидирует
        
        Args:
            text (str): Текст транзакции для обработки
            
        Returns:
            Dict[str, Any]: Результат обработки с данными и валидацией
        """
        try:
            logger.info(f"Обработка транзакции: {text[:100]}...")
            
            # Извлечение данных
            if self.llm:
                # Используем LLM для извлечения данных
                transaction_data = self._extract_with_llm(text)
            else:
                # Используем regex парсер
                transaction_data = self.parser.parse(text)
            
            # Валидация транзакции
            validation_result = self.validator.validate_transaction(transaction_data)
            
            logger.info(f"Транзакция обработана: {'успешно' if validation_result['is_valid'] else 'с ошибками'}")
            
            return {
                'transaction_data': transaction_data,
                'validation_result': validation_result,
                'processing_method': 'LLM' if self.llm else 'Regex',
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            logger.error(f"Ошибка обработки транзакции: {e}")
            return {
                'transaction_data': None,
                'validation_result': None,
                'error': str(e),
                'processing_method': 'Error',
                'timestamp': datetime.now()
            }
    
    def _extract_with_llm(self, text: str) -> TransactionData:
        """
        Извлекает данные транзакции с помощью LLM
        
        Args:
            text (str): Текст транзакции
            
        Returns:
            TransactionData: Извлеченные данные
        """
        try:
            # Формируем промпт
            prompt = self.prompt_template.format(text=text)
            
            # Получаем ответ от LLM
            response = self.llm(prompt)
            
            # Парсим ответ
            return self.parser.parse(response)
            
        except Exception as e:
            logger.error(f"Ошибка LLM обработки: {e}")
            # Fallback на regex парсер
            return self.parser.parse(text)
    
    def batch_process(self, texts: List[str]) -> List[Dict[str, Any]]:
        """
        Пакетная обработка множества транзакций
        
        Args:
            texts (List[str]): Список текстов транзакций
            
        Returns:
            List[Dict[str, Any]]: Список результатов обработки
        """
        results = []
        
        for i, text in enumerate(texts):
            logger.info(f"Обработка транзакции {i+1}/{len(texts)}")
            result = self.process_transaction(text)
            results.append(result)
        
        return results
    
    def get_statistics(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Вычисляет статистику по результатам обработки
        
        Args:
            results (List[Dict[str, Any]]): Результаты обработки транзакций
            
        Returns:
            Dict[str, Any]: Статистика обработки
        """
        total = len(results)
        successful = sum(1 for r in results if r['transaction_data'] is not None)
        valid = sum(1 for r in results if r['validation_result'] and r['validation_result']['is_valid'])
        
        currencies = {}
        total_amounts = {}
        
        for result in results:
            if result['transaction_data']:
                currency = result['transaction_data'].currency
                amount = result['transaction_data'].amount
                
                currencies[currency] = currencies.get(currency, 0) + 1
                total_amounts[currency] = total_amounts.get(currency, 0) + amount
        
        return {
            'total_transactions': total,
            'successful_extractions': successful,
            'valid_transactions': valid,
            'success_rate': successful / total * 100 if total > 0 else 0,
            'validation_rate': valid / total * 100 if total > 0 else 0,
            'currencies': currencies,
            'total_amounts': total_amounts,
            'processing_timestamp': datetime.now()
        }
