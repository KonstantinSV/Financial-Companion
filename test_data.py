"""
Тестовые данные для проверки AI-ассистента банковских транзакций
===============================================================

Содержит наборы тестовых транзакций для проверки различных сценариев:
- Корректные транзакции разных типов
- Транзакции с ошибками валидации  
- Граничные случаи и сложные форматы
- Многоязычные транзакции

Версия: 1.0
"""

from typing import List, Dict, Any
from datetime import datetime

def get_sample_transactions() -> List[str]:
    """
    Возвращает список тестовых транзакций для массового тестирования
    
    Returns:
        List[str]: Список текстов транзакций
    """
    
    return [
        # Стандартные российские переводы
        "Перевести 15000 рублей на счет Иванова Ивана Ивановича номер счета 40817810123456789012",
        "Отправить 50000₽ получателю Петрова Анна Сергеевна счет 40817810987654321098 назначение зарплата",
        "Банковский перевод 25000 рублей на счет ООО Ромашка 40702810555666777888 назначение оплата по договору",
        
        # Валютные переводы USD
        "Transfer 2500 USD to Johnson Smith account 1234567890123456789 for consulting services",
        "Отправить 5000 долларов США получателю Miller & Co на счет 9876543210987654321",
        "Перевести $3000 на счет 1111222233334444 получателю David Brown описание payment for software",
        
        # Переводы в евро
        "Перевод 1200 евро получателю Hans Weber счет DE89370400440532013000 назначение equipment purchase",
        "Отправить 800€ на IBAN FR1420041010050500013M02606 получателю Pierre Dubois",
        "Transfer 2000 EUR to Maria Garcia IBAN ES9121000418450200051332 for real estate services",
        
        # Переводы с IBAN
        "Перевод 1500 долларов на IBAN GB29NWBK60161331926819 получателю Robert Wilson назначение freelance work",
        "Отправить 3500 рублей на IBAN RU0204452560040702810412345678901234567890 получателю Сидоров С.С.",
        "Transfer 900 CHF to IBAN CH9300762011623852957 recipient Mueller AG purpose machinery payment",
        
        # Короткие форматы
        "500 рублей Козлову П.А. счет 40817810111222333444",
        "1000$ Smith J. account 5555666677778888",
        "300€ Weber H. DE12345678901234567890",
        
        # Сложные описания
        "Банковский перевод на сумму 75000 российских рублей получателю Индивидуальный предприниматель Александров Михаил Владимирович ИНН 123456789012 КПП 123456789 расчетный счет 40802810123456789012 в банке ПАО Сбербанк БИК 044525225 корреспондентский счет 30101810400000000225 назначение платежа: оплата за оказанные консультационные услуги по договору №157 от 15 января 2024 года НДС не облагается",
        
        # Переводы с символами и форматированием
        "Перевести двадцать тысяч (20 000) рублей получателю \"ООО Технические решения\" счет: 407.028.10.123.456.789.012, назначение: Оплата поставки оборудования согласно спецификации №5",
        "Send Five Thousand US Dollars ($5,000.00) to recipient: Johnson & Associates LLC, Account: 1234-5678-9012-3456, Reference: Invoice #INV-2024-001",
        
        # Международные переводы
        "International wire transfer 7500 USD to beneficiary Zhang Wei, Bank of China account 6228480123456789012 SWIFT BKCHCNBJ purpose business partnership investment",
        "SWIFT перевод 4000 евро получателю Tokyo Trading Co Ltd счет 1234567890 банк Sumitomo Mitsui Banking Corporation SWIFT SMBCJPJT назначение import payment",
        
        # Переводы физических лиц
        "Перевести 12000 рублей маме Ивановой Марии Петровне на карту 4276123456789012 с любовью от сына",
        "Отправить 500 долларов брату Michael на PayPal account michael.smith@email.com for birthday gift",
        "Перевод 2000 рублей другу Алексею Сергеевичу на Qiwi кошелек +79161234567 за помощь с ремонтом",
        
        # Коммунальные платежи
        "Оплата коммунальных услуг 8500 рублей управляющей компании ЖКХ-Сервис счет 40702810123456789012 лицевой счет 123456789 за квартиру 45",
        "Платеж за электричество 3200₽ получателю Мосэнергосбыт номер лицевого счета 1234567890 период январь 2024",
        
        # Интернет и связь
        "Пополнить баланс телефона +79161234567 на сумму 500 рублей оператор МТС",
        "Оплата интернета 1200 рублей провайдер Ростелеком договор №12345 за февраль 2024",
        
        # Штрафы и налоги
        "Оплата штрафа ГИБДД 5000 рублей постановление №12345678901234567890 УИН 12345678901234567890",
        "Уплата налога на доходы физических лиц 15600 рублей ИФНС России №1 по г.Москве КБК 18210102010011000110",
        
        # Благотворительность
        "Благотворительный взнос 10000 рублей фонду Подари жизнь счет 40703810123456789012 для помощи больным детям",
        "Donation 1000$ to Red Cross account 1234567890123456789 for disaster relief",
        
        # Образование
        "Оплата обучения 45000 рублей МГУ им. М.В.Ломоносова счет 40701810123456789012 студент Иванов И.И. группа 101",
        "Tuition payment 15000 USD Harvard University account 9876543210987654321 student John Smith ID 12345",
        
        # Медицина
        "Оплата медицинских услуг 25000 рублей клинике Здоровье счет 40702810555777888999 пациент Петров П.П.",
        "Medical payment 3000 EUR to Dr. Mueller practice IBAN DE12345678901234567890 patient treatment",
        
        # Ошибочные/проблемные транзакции для тестирования валидации
        "Перевести 2000000 рублей неизвестному получателю",  # Превышение лимита
        "Transfer 50000 USD to suspicious account 123",  # Превышение лимита USD + короткий счет
        "Отправить 50 рублей получателю террористическая организация",  # Блокированный получатель
        "Перевод -1000 рублей получателю Иванов",  # Отрицательная сумма
        "Send money to account",  # Отсутствует сумма
        "Перевести рублей получателю Петров счет 40817810123456789012",  # Отсутствует сумма
        "Transfer 1000 UNKNOWN_CURRENCY to Smith account 123456789",  # Неизвестная валюта
        
        # Граничные случаи
        "Перевести 1 рубль получателю Тестовый счет 40817810123456789012",  # Минимальная сумма
        "Transfer 9999 USD to Maximum Limit Test account 1234567890123456789",  # Близко к лимиту
        "Перевод 749999 рублей получателю Граничный тест счет 40817810987654321098",  # Близко к лимиту RUB
        
        # Различные форматы записи сумм
        "Перевести одну тысячу рублей получателю Словесная сумма",
        "Transfer one thousand five hundred dollars to Word Amount Test",
        "Отправить 1,500.50 долларов получателю Decimal Test account 1234567890",
        "Перевод 2 500,75 рублей получателю Запятая Тест счет 40817810111111111111",
        
        # Сложные имена получателей
        "Перевести 5000 рублей получателю Де-ла-Круз Мария-Хосефина Антониетта",
        "Transfer 2000 USD to recipient Van Der Berg-Johnson III account 5555666677778888",
        "Отправить 1500 евро получателю ООО \"Рога и копыта\" (ИНН 1234567890)",
        
        # Переводы с разными валютными символами
        "Отправить ¥50000 получателю Yamamoto Takeshi account 1234567890123456 Japan",
        "Transfer £2000 to recipient Cambridge University account GB29NWBK60161331926819",
        "Перевод 3000 швейцарских франков получателю Swiss Bank AG IBAN CH9300762011623852957",
        
        # Мультиязычные транзакции
        "Virement de 1500 euros au bénéficiaire Pierre Dubois compte FR1420041010050500013M02606",
        "Überweisung von 2000 Euro an Hans Weber Konto DE89370400440532013000",
        "Transferencia de 1000 dólares a Maria Garcia cuenta ES9121000418450200051332",
        
        # Переводы с дополнительной информацией
        "Срочный перевод 10000 рублей получателю Экстренная помощь Иванов И.И. счет 40817810123456789012 телефон +79161234567 адрес Москва ул.Тверская д.1",
        "URGENT: Transfer 5000 USD to Emergency Contact John Smith account 1234567890123456789 phone +1234567890 ref EMERGENCY001",
        
        # Переводы с процентами и комиссиями
        "Перевести 10000 рублей получателю Комиссия Тест счет 40817810123456789012 комиссия 1% итого к переводу 10100 рублей",
        "Transfer 1000 USD plus 2% fee total 1020 USD to Fee Test recipient account 9876543210",
        
        # Переводы с временными ограничениями
        "Отложенный перевод на 15.03.2024 сумма 20000 рублей получателю Будущий платеж счет 40817810123456789012",
        "Scheduled transfer for March 15th: 3000 USD to Future Payment account 1234567890123456789",
        
        # Переводы с условиями
        "Условный перевод 15000 рублей получателю Условный тест счет 40817810123456789012 при условии подтверждения документов",
        "Conditional transfer 2000 EUR to Conditional Test IBAN DE12345678901234567890 subject to approval",
    ]

def get_validation_test_cases() -> List[Dict[str, Any]]:
    """
    Возвращает тестовые случаи для проверки валидации
    
    Returns:
        List[Dict[str, Any]]: Список тестовых случаев с ожидаемыми результатами
    """
    
    return [
        {
            'text': 'Перевести 15000 рублей получателю Иванов И.И. счет 40817810123456789012',
            'expected_valid': True,
            'expected_currency': 'RUB',
            'expected_amount': 15000.0,
            'description': 'Корректный российский перевод'
        },
        {
            'text': 'Transfer 2000000 USD to Smith account 1234567890',
            'expected_valid': False,
            'expected_errors': ['превышает лимит'],
            'description': 'Превышение лимита USD'
        },
        {
            'text': 'Перевести 50 рублей получателю санкционный список',
            'expected_valid': False,
            'expected_errors': ['черном списке'],
            'description': 'Заблокированный получатель'
        },
        {
            'text': 'Transfer 5000 EUR to Weber IBAN DE89370400440532013000',
            'expected_valid': True,
            'expected_currency': 'EUR',
            'expected_amount': 5000.0,
            'description': 'Корректный перевод в евро с IBAN'
        },
        {
            'text': 'Отправить 0.5 рублей получателю Микроплатеж',
            'expected_valid': False,
            'expected_errors': ['меньше минимальной'],
            'description': 'Сумма меньше минимальной'
        },
        {
            'text': 'Перевод получателю Иванов счет 40817810123456789012',
            'expected_valid': False,
            'expected_errors': ['amount'],
            'description': 'Отсутствует сумма'
        },
        {
            'text': 'Transfer 1000 UNKNOWN to Test account 123456789',
            'expected_valid': False,
            'expected_warnings': ['не входит в список поддерживаемых'],
            'description': 'Неподдерживаемая валюта'
        },
        {
            'text': 'Перевести 100000 рублей получателю Крупный перевод счет 40817810123456789012',
            'expected_valid': True,
            'expected_warnings': ['Крупная сумма'],
            'description': 'Крупная сумма с предупреждением'
        }
    ]

def get_parsing_test_cases() -> List[Dict[str, Any]]:
    """
    Возвращает тестовые случаи для проверки парсинга данных
    
    Returns:
        List[Dict[str, Any]]: Список тестовых случаев для парсинга
    """
    
    return [
        {
            'text': 'Перевести 15000 рублей получателю Иванов Иван Иванович счет 40817810123456789012',
            'expected_amount': 15000.0,
            'expected_currency': 'RUB',
            'expected_recipient': 'Иванов Иван Иванович',
            'expected_account': '40817810123456789012'
        },
        {
            'text': 'Transfer $2500 to John Smith account 1234567890123456789',
            'expected_amount': 2500.0,
            'expected_currency': 'USD',
            'expected_recipient': 'John Smith',
            'expected_account': '1234567890123456789'
        },
        {
            'text': 'Отправить 1200€ на IBAN DE89370400440532013000 получателю Hans Weber',
            'expected_amount': 1200.0,
            'expected_currency': 'EUR',
            'expected_recipient': 'Hans Weber',
            'expected_iban': 'DE89370400440532013000'
        },
        {
            'text': 'Перевод 5000₽ Петрову П.П. назначение зарплата за январь',
            'expected_amount': 5000.0,
            'expected_currency': 'RUB',
            'expected_recipient': 'Петрову П.П.',
            'expected_description': 'зарплата за январь'
        },
        {
            'text': '3000 долларов получателю Miller & Co для оплаты консультаций',
            'expected_amount': 3000.0,
            'expected_currency': 'USD',
            'expected_recipient': 'Miller & Co',
            'expected_description': 'оплаты консультаций'
        }
    ]

def get_performance_test_data() -> List[str]:
    """
    Возвращает данные для тестирования производительности
    
    Returns:
        List[str]: Список транзакций для нагрузочного тестирования
    """
    
    base_transactions = [
        "Перевести {} рублей получателю Тест {} счет 40817810123456789012",
        "Transfer {} USD to Test {} account 1234567890123456789",
        "Отправить {}€ получателю Тест {} IBAN DE89370400440532013000",
        "Перевод {} рублей на счет ООО Тест {} 40702810555666777888",
        "Send {} dollars to Test Company {} account 9876543210987654321"
    ]
    
    test_data = []
    
    # Генерируем транзакции с разными суммами и получателями
    for i in range(100):
        amount = 1000 + (i * 100)  # Суммы от 1000 до 10900
        template = base_transactions[i % len(base_transactions)]
        transaction = template.format(amount, i + 1)
        test_data.append(transaction)
    
    return test_data

def get_edge_cases() -> List[Dict[str, Any]]:
    """
    Возвращает граничные и сложные случаи для тестирования
    
    Returns:
        List[Dict[str, Any]]: Список сложных тестовых случаев
    """
    
    return [
        {
            'text': '',
            'description': 'Пустая строка',
            'expected_error': True
        },
        {
            'text': '   ',
            'description': 'Только пробелы',
            'expected_error': True
        },
        {
            'text': 'abcdefg12345',
            'description': 'Случайный текст без структуры',
            'expected_error': True
        },
        {
            'text': 'Перевести миллион рублей',
            'description': 'Сумма прописью без цифр',
            'expected_error': True
        },
        {
            'text': 'Transfer money to someone',
            'description': 'Очень общее описание без деталей',
            'expected_error': True
        },
        {
            'text': 'Перевести 1000000000000 рублей получателю Тест',
            'description': 'Астрономическая сумма',
            'expected_error': False,
            'expected_warnings': True
        },
        {
            'text': 'Перевести 0.01 рублей получателю Микроплатеж',
            'description': 'Очень маленькая сумма',
            'expected_error': False
        },
        {
            'text': 'Перевести 1000 рублей получателю А счет 1',
            'description': 'Очень короткие данные',
            'expected_warnings': True
        },
        {
            'text': 'Перевести 1000 рублей получателю ' + 'А' * 200,
            'description': 'Очень длинное имя получателя',
            'expected_warnings': True
        },
        {
            'text': 'Перевести 1000 рублей получателю Иванов счет 40817810123456789012' + '0' * 100,
            'description': 'Очень длинный номер счета',
            'expected_warnings': True
        }
    ]

def get_multilingual_test_cases() -> List[Dict[str, Any]]:
    """
    Возвращает многоязычные тестовые случаи
    
    Returns:
        List[Dict[str, Any]]: Список многоязычных транзакций
    """
    
    return [
        {
            'text': 'Virement de 1500 euros au bénéficiaire Pierre Dubois compte FR1420041010050500013M02606',
            'language': 'fr',
            'expected_amount': 1500.0,
            'expected_currency': 'EUR',
            'description': 'Французский перевод'
        },
        {
            'text': 'Überweisung von 2000 Euro an Hans Weber Konto DE89370400440532013000',
            'language': 'de', 
            'expected_amount': 2000.0,
            'expected_currency': 'EUR',
            'description': 'Немецкий перевод'
        },
        {
            'text': 'Transferencia de 1000 dólares a Maria Garcia cuenta ES9121000418450200051332',
            'language': 'es',
            'expected_amount': 1000.0,
            'expected_currency': 'USD',
            'description': 'Испанский перевод'
        },
        {
            'text': 'Trasferimento di 800 euro a Marco Rossi conto IT60X0542811101000000123456',
            'language': 'it',
            'expected_amount': 800.0,
            'expected_currency': 'EUR',
            'description': 'Итальянский перевод'
        },
        {
            'text': '1000美元转账给张伟 账户1234567890123456789',
            'language': 'zh',
            'expected_amount': 1000.0,
            'expected_currency': 'USD',
            'description': 'Китайский перевод'
        }
    ]

def get_test_statistics() -> Dict[str, Any]:
    """
    Возвращает статистику по тестовым данным
    
    Returns:
        Dict[str, Any]: Статистика тестовых данных
    """
    
    sample_transactions = get_sample_transactions()
    validation_cases = get_validation_test_cases()
    parsing_cases = get_parsing_test_cases()
    edge_cases = get_edge_cases()
    multilingual_cases = get_multilingual_test_cases()
    performance_data = get_performance_test_data()
    
    return {
        'total_sample_transactions': len(sample_transactions),
        'validation_test_cases': len(validation_cases),
        'parsing_test_cases': len(parsing_cases),
        'edge_cases': len(edge_cases),
        'multilingual_cases': len(multilingual_cases),
        'performance_test_data': len(performance_data),
        'total_test_cases': (
            len(sample_transactions) + len(validation_cases) + 
            len(parsing_cases) + len(edge_cases) + len(multilingual_cases)
        ),
        'generated_at': datetime.now(),
        'currencies_covered': ['RUB', 'USD', 'EUR', 'GBP', 'CHF', 'JPY'],
        'languages_covered': ['ru', 'en', 'fr', 'de', 'es', 'it', 'zh'],
        'test_categories': [
            'standard_transfers',
            'currency_transfers', 
            'iban_transfers',
            'validation_errors',
            'parsing_edge_cases',
            'performance_tests',
            'multilingual_support'
        ]
    }

# Константы для быстрого доступа к часто используемым тестовым данным
QUICK_TEST_TRANSACTIONS = [
    "Перевести 15000 рублей получателю Иванов И.И. счет 40817810123456789012",
    "Transfer 2500 USD to John Smith account 1234567890123456789",
    "Отправить 1200€ на IBAN DE89370400440532013000 получателю Hans Weber",
    "Перевод 750000 рублей на счет ООО Тест 40702810555666777888",  # Превышение лимита
    "Отправить 50 рублей получателю санкции"  # Блокированный получатель
]

MINIMAL_TEST_SET = [
    "1000 рублей Петрову счет 40817810123456789012",
    "500$ Smith account 1234567890",
    "300€ Weber DE12345678901234567890"
]

if __name__ == "__main__":
    # Демонстрация тестовых данных
    print("=== Статистика тестовых данных ===")
    stats = get_test_statistics()
    for key, value in stats.items():
        if key != 'generated_at':
            print(f"{key}: {value}")
    
    print("\n=== Примеры тестовых транзакций ===")
    samples = get_sample_transactions()[:5]
    for i, transaction in enumerate(samples, 1):
        print(f"{i}. {transaction}")
    
    print(f"\n... и еще {len(samples)-5} транзакций")
