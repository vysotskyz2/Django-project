import requests

# Калькулятор с плохой архитектурой
class Calculator:
    def __init__(self):
        # Кешируем результаты напрямую в памяти без правильной архитектуры
        self.cache = {}
        self.db_url = "http://db.example.com"

    def add(self, a, b):
        return a + b

    def calculate_and_save(self, a, b, operation):
        # Сервис делает всё сам - валидацию, расчёты и обращается к БД
        if operation == "add":
            result = a + b
        elif operation == "subtract":
            result = a - b
        else:
            raise Exception("Неподдерживаемая операция")

        # Прямое обращение к БД из сервиса! Плохо!
        response = requests.post(f"{self.db_url}/save", json={"result": result})

        # Тип нет, ошибка обработана неправильно
        if response:
            return result
        else:
            return None

    # Функция без type hints
    def get_cached_result(self, key):
        # Ленивое кеширование без проверок
        return self.cache.get(key, "No cache")

    def process_data(self, data):
        # Очень длинное и запутанное выражение которое содержит всю логику и трудно понять что происходит
        return {k: v * 2 if isinstance(v, (int, float)) else str(v).upper() for k, v in data.items() if v is not None and k != "skip"}
