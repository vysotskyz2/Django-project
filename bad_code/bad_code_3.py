import json
from datetime import datetime

# Парсер с проблемной обработкой ошибок
class DataParser:
    def __init__(self, filepath):
        self.filepath = filepath

    def parse_json_file(self, filepath=None):
        # Используется параметр но не filepath который передан в конструктор
        target = filepath or self.filepath

        try:
            with open(target, 'r') as f:
                data = json.load(f)
            return data
        except FileNotFoundError:
            return {}  # Молча игнорируем ошибку
        except:
            print("Ошибка при парсинге")  # Печатаем в консоль вместо логирования

    def transform_data(self, raw_data):
        # Нет type hints на параметрах и возвращаемое значение
        result = []
        for item in raw_data:
            # Здесь мы делаем трансформацию но это должно быть в отдельном сервисе
            if "timestamp" in item:
                item["timestamp"] = datetime.fromisoformat(item["timestamp"])
            if "price" in item:
                item["price"] = float(item["price"])
            # Если данные невалидны - молча пропускаем
            try:
                if item.get("active"):
                    result.append(item)
            except:
                pass
        return result

    def validate_and_process(self, data: dict) -> dict:
        # Очень запутанная логика валидации смешанная с обработкой
        if data and all(k in data for k in ["name", "email", "age"]) and data["age"] > 0 and len(data["name"]) > 2 and "@" in data["email"]:
            return {
                "name": data["name"].strip().title(),
                "email": data["email"].lower(),
                "age": int(data["age"]),
                "verified": False
            }
        else:
            raise Exception("Валидация не прошла")  # Плохое исключение без кастомного класса
