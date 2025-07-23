"""
Модуль для работы с базой данных транзакций
==========================================

Обеспечивает сохранение, извлечение и управление данными транзакций
с использованием SQLite для локального хранения.

Версия: 1.0
"""

import sqlite3
import json
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from pathlib import Path

from transaction_processor import TransactionData

logger = logging.getLogger(__name__)

class DatabaseManager:
    """
    Менеджер базы данных для работы с транзакциями
    """
    
    def __init__(self, db_path: str = "transactions.db"):
        """
        Инициализация менеджера базы данных
        
        Args:
            db_path (str): Путь к файлу базы данных
        """
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Инициализация структуры базы данных"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Создание таблицы транзакций
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS transactions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        amount REAL NOT NULL,
                        currency TEXT NOT NULL,
                        recipient TEXT NOT NULL,
                        account_number TEXT,
                        iban TEXT,
                        description TEXT,
                        timestamp DATETIME NOT NULL,
                        original_text TEXT,
                        is_valid BOOLEAN,
                        validation_errors TEXT,
                        validation_warnings TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Создание индексов для быстрого поиска
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_timestamp 
                    ON transactions(timestamp)
                """)
                
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_currency 
                    ON transactions(currency)
                """)
                
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_recipient 
                    ON transactions(recipient)
                """)
                
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_is_valid 
                    ON transactions(is_valid)
                """)
                
                conn.commit()
                logger.info("База данных инициализирована успешно")
                
        except Exception as e:
            logger.error(f"Ошибка инициализации базы данных: {e}")
            raise
    
    def save_transaction(self, 
                        transaction: TransactionData, 
                        validation_result: Dict[str, Any], 
                        original_text: str) -> int:
        """
        Сохраняет транзакцию в базу данных
        
        Args:
            transaction (TransactionData): Данные транзакции
            validation_result (Dict[str, Any]): Результат валидации
            original_text (str): Исходный текст транзакции
            
        Returns:
            int: ID сохраненной записи
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO transactions (
                        amount, currency, recipient, account_number, iban, 
                        description, timestamp, original_text, is_valid,
                        validation_errors, validation_warnings
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    transaction.amount,
                    transaction.currency,
                    transaction.recipient,
                    transaction.account_number,
                    transaction.iban,
                    transaction.description,
                    transaction.timestamp,
                    original_text,
                    validation_result['is_valid'],
                    json.dumps(validation_result['errors'], ensure_ascii=False),
                    json.dumps(validation_result['warnings'], ensure_ascii=False)
                ))
                
                transaction_id = cursor.lastrowid
                conn.commit()
                
                logger.info(f"Транзакция сохранена с ID: {transaction_id}")
                return transaction_id
                
        except Exception as e:
            logger.error(f"Ошибка сохранения транзакции: {e}")
            raise
    
    def get_transaction(self, transaction_id: int) -> Optional[TransactionData]:
        """
        Получает транзакцию по ID
        
        Args:
            transaction_id (int): ID транзакции
            
        Returns:
            Optional[TransactionData]: Данные транзакции или None
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM transactions WHERE id = ?
                """, (transaction_id,))
                
                row = cursor.fetchone()
                
                if row:
                    return self._row_to_transaction(row)
                return None
                
        except Exception as e:
            logger.error(f"Ошибка получения транзакции {transaction_id}: {e}")
            return None
    
    def get_all_transactions(self, limit: Optional[int] = None) -> List[TransactionData]:
        """
        Получает список всех транзакций
        
        Args:
            limit (Optional[int]): Максимальное количество записей
            
        Returns:
            List[TransactionData]: Список транзакций
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                query = "SELECT * FROM transactions ORDER BY timestamp DESC"
                if limit:
                    query += f" LIMIT {limit}"
                
                cursor.execute(query)
                rows = cursor.fetchall()
                
                return [self._row_to_transaction(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Ошибка получения списка транзакций: {e}")
            return []
    
    def get_transactions_by_currency(self, currency: str) -> List[TransactionData]:
        """
        Получает транзакции по валюте
        
        Args:
            currency (str): Валюта для фильтрации
            
        Returns:
            List[TransactionData]: Список транзакций в указанной валюте
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM transactions 
                    WHERE currency = ? 
                    ORDER BY timestamp DESC
                """, (currency,))
                
                rows = cursor.fetchall()
                return [self._row_to_transaction(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Ошибка получения транзакций по валюте {currency}: {e}")
            return []
    
    def get_transactions_by_recipient(self, recipient: str) -> List[TransactionData]:
        """
        Получает транзакции по получателю
        
        Args:
            recipient (str): Имя получателя для поиска
            
        Returns:
            List[TransactionData]: Список транзакций для указанного получателя
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM transactions 
                    WHERE recipient LIKE ? 
                    ORDER BY timestamp DESC
                """, (f"%{recipient}%",))
                
                rows = cursor.fetchall()
                return [self._row_to_transaction(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Ошибка получения транзакций по получателю {recipient}: {e}")
            return []
    
    def get_transactions_by_date_range(self, 
                                     start_date: datetime, 
                                     end_date: datetime) -> List[TransactionData]:
        """
        Получает транзакции за период
        
        Args:
            start_date (datetime): Начальная дата
            end_date (datetime): Конечная дата
            
        Returns:
            List[TransactionData]: Список транзакций за период
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM transactions 
                    WHERE timestamp BETWEEN ? AND ?
                    ORDER BY timestamp DESC
                """, (start_date, end_date))
                
                rows = cursor.fetchall()
                return [self._row_to_transaction(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Ошибка получения транзакций за период: {e}")
            return []
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Получает статистику по всем транзакциям
        
        Returns:
            Dict[str, Any]: Статистические данные
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Общее количество транзакций
                cursor.execute("SELECT COUNT(*) FROM transactions")
                total_count = cursor.fetchone()[0]
                
                # Количество валидных транзакций
                cursor.execute("SELECT COUNT(*) FROM transactions WHERE is_valid = 1")
                valid_count = cursor.fetchone()[0]
                
                # Статистика по валютам
                cursor.execute("""
                    SELECT currency, COUNT(*), SUM(amount), AVG(amount)
                    FROM transactions 
                    GROUP BY currency
                """)
                currency_stats = {}
                for row in cursor.fetchall():
                    currency, count, total_amount, avg_amount = row
                    currency_stats[currency] = {
                        'count': count,
                        'total_amount': total_amount,
                        'average_amount': avg_amount
                    }
                
                # Топ получателей
                cursor.execute("""
                    SELECT recipient, COUNT(*), SUM(amount)
                    FROM transactions 
                    GROUP BY recipient 
                    ORDER BY COUNT(*) DESC 
                    LIMIT 10
                """)
                top_recipients = []
                for row in cursor.fetchall():
                    recipient, count, total_amount = row
                    top_recipients.append({
                        'recipient': recipient,
                        'transaction_count': count,
                        'total_amount': total_amount
                    })
                
                # Последняя транзакция
                cursor.execute("""
                    SELECT timestamp FROM transactions 
                    ORDER BY timestamp DESC 
                    LIMIT 1
                """)
                last_transaction = cursor.fetchone()
                last_transaction_date = last_transaction[0] if last_transaction else None
                
                return {
                    'total_transactions': total_count,
                    'valid_transactions': valid_count,
                    'invalid_transactions': total_count - valid_count,
                    'validation_rate': (valid_count / total_count * 100) if total_count > 0 else 0,
                    'currency_statistics': currency_stats,
                    'top_recipients': top_recipients,
                    'last_transaction_date': last_transaction_date,
                    'generated_at': datetime.now()
                }
                
        except Exception as e:
            logger.error(f"Ошибка получения статистики: {e}")
            return {}
    
    def delete_transaction(self, transaction_id: int) -> bool:
        """
        Удаляет транзакцию по ID
        
        Args:
            transaction_id (int): ID транзакции для удаления
            
        Returns:
            bool: True если удаление успешно
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("DELETE FROM transactions WHERE id = ?", (transaction_id,))
                deleted_count = cursor.rowcount
                conn.commit()
                
                if deleted_count > 0:
                    logger.info(f"Транзакция {transaction_id} удалена")
                    return True
                else:
                    logger.warning(f"Транзакция {transaction_id} не найдена")
                    return False
                    
        except Exception as e:
            logger.error(f"Ошибка удаления транзакции {transaction_id}: {e}")
            return False
    
    def clear_all_transactions(self) -> bool:
        """
        Удаляет все транзакции из базы данных
        
        Returns:
            bool: True если очистка успешна
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("DELETE FROM transactions")
                deleted_count = cursor.rowcount
                conn.commit()
                
                logger.info(f"Удалено {deleted_count} транзакций")
                return True
                
        except Exception as e:
            logger.error(f"Ошибка очистки базы данных: {e}")
            return False
    
    def _row_to_transaction(self, row: sqlite3.Row) -> TransactionData:
        """
        Преобразует строку из БД в объект TransactionData
        
        Args:
            row (sqlite3.Row): Строка из базы данных
            
        Returns:
            TransactionData: Объект транзакции
        """
        transaction = TransactionData(
            amount=row['amount'],
            currency=row['currency'],
            recipient=row['recipient'],
            account_number=row['account_number'],
            iban=row['iban'],
            description=row['description'],
            timestamp=datetime.fromisoformat(row['timestamp']) if isinstance(row['timestamp'], str) else row['timestamp']
        )
        
        # Добавляем дополнительные поля для отображения
        transaction.is_valid = bool(row['is_valid'])
        transaction.has_errors = bool(row['validation_errors']) and row['validation_errors'] != '[]'
        transaction.has_warnings = bool(row['validation_warnings']) and row['validation_warnings'] != '[]'
        transaction.id = row['id']
        transaction.original_text = row['original_text']
        
        try:
            transaction.validation_errors = json.loads(row['validation_errors']) if row['validation_errors'] else []
            transaction.validation_warnings = json.loads(row['validation_warnings']) if row['validation_warnings'] else []
        except json.JSONDecodeError:
            transaction.validation_errors = []
            transaction.validation_warnings = []
        
        return transaction
    
    def backup_database(self, backup_path: str) -> bool:
        """
        Создает резервную копию базы данных
        
        Args:
            backup_path (str): Путь для сохранения резервной копии
            
        Returns:
            bool: True если резервное копирование успешно
        """
        try:
            import shutil
            
            shutil.copy2(self.db_path, backup_path)
            logger.info(f"Резервная копия создана: {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка создания резервной копии: {e}")
            return False
    
    def get_database_info(self) -> Dict[str, Any]:
        """
        Получает информацию о базе данных
        
        Returns:
            Dict[str, Any]: Информация о БД
        """
        try:
            db_file_path = Path(self.db_path)
            
            info = {
                'database_path': str(db_file_path.absolute()),
                'database_exists': db_file_path.exists(),
                'database_size_bytes': db_file_path.stat().st_size if db_file_path.exists() else 0,
                'created_at': datetime.fromtimestamp(db_file_path.stat().st_ctime) if db_file_path.exists() else None,
                'modified_at': datetime.fromtimestamp(db_file_path.stat().st_mtime) if db_file_path.exists() else None
            }
            
            # Добавляем информацию о таблицах
            if db_file_path.exists():
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    
                    cursor.execute("SELECT COUNT(*) FROM transactions")
                    info['transaction_count'] = cursor.fetchone()[0]
                    
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                    info['tables'] = [row[0] for row in cursor.fetchall()]
            
            return info
            
        except Exception as e:
            logger.error(f"Ошибка получения информации о БД: {e}")
            return {'error': str(e)}
