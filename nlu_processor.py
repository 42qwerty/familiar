# -*- coding: utf-8 -*-

import json
import requests
import os

# --- Константы (можно вынести в конфиг позже) ---
# Используем переменную окружения для URL, если она есть, иначе дефолт
DEFAULT_API_URL = 'http://localhost:11434/api/generate'
API_URL = os.environ.get('OLLAMA_API_URL', DEFAULT_API_URL)
DEFAULT_MODEL_NAME = "mistral" # Модель по умолчанию
# Новая версия константы NLU_INSTRUCTION_TEMPLATE в nlu_processor.py

# Новая версия NLU_INSTRUCTION_TEMPLATE (v4) в nlu_processor.py

NLU_INSTRUCTION_TEMPLATE = """Тебе будет предоставлена пользовательская команда. Твоя задача - извлечь из нее основное намерение (intent) и параметры (parameters), включая конкретное действие (action), если оно применимо, и вернуть результат ТОЛЬКО в виде чистого JSON объекта.

Возможные намерения (intent) и действия (action):

* intent: manage_app
    * action: "open" (Запустить или сфокусировать приложение)
    * action: "close" (Закрыть приложение)
    * Обязательный параметр: "app_name".
* intent: manage_system
    * action: "reboot" (Перезагрузить)
    * action: "update" (Обновить)
    * action: "shutdown" (Выключить) - (Добавил на всякий случай)
    * Параметры не требуются.
* intent: manage_sound
    * action: "up" (Громче)
    * action: "down" (Тише)
    * action: "mute" (Выключить звук)
    * action: "unmute" (Включить звук) - (Добавил для ясности)
    * Опциональный параметр: "amount".
* intent: add_alias
    * Параметры: "alias_name", "canonical_name".
* intent: ask_time
    * Параметров нет.
* intent: web_search
    * Обязательный параметр: "query".
* intent: set_reminder
    * Параметры: "reminder_text", "time_spec".
* intent: set_alarm
    * Параметр: "time_spec".
* intent: unknown
    * Намерение не распознано.

Примеры:

Команда: запусти стим
Результат:
{{"intent": "manage_app", "parameters": {{"action": "open", "app_name": "Steam"}}}}

Команда: открой телегу
Результат:
{{"intent": "manage_app", "parameters": {{"action": "open", "app_name": "Telegram"}}}}

Команда: закрой хром
Результат:
{{"intent": "manage_app", "parameters": {{"action": "close", "app_name": "Chrome"}}}}

Команда: убей процесс firefox
Результат:
{{"intent": "manage_app", "parameters": {{"action": "close", "app_name": "Firefox"}}}}

Команда: запомни тг это telegram
Результат:
{{"intent": "add_alias", "parameters": {{"alias_name": "тг", "canonical_name": "Telegram"}}}}

Команда: сделай погромче
Результат:
{{"intent": "manage_sound", "parameters": {{"action": "up"}}}}

Команда: звук тише на 20 процентов
Результат:
{{"intent": "manage_sound", "parameters": {{"action": "down", "amount": "20%"}}}}

Команда: выключи звук
Результат:
{{"intent": "manage_sound", "parameters": {{"action": "mute"}}}}

Команда: включи звук
Результат:
{{"intent": "manage_sound", "parameters": {{"action": "unmute"}}}}

Команда: который час?
Результат:
{{"intent": "ask_time", "parameters": {{}}}}

Команда: ребут
Результат:
{{"intent": "manage_system", "parameters": {{"action": "reboot"}}}}

Команда: выключи компьютер
Результат:
{{"intent": "manage_system", "parameters": {{"action": "shutdown"}}}}

Команда: запусти обновление
Результат:
{{"intent": "manage_system", "parameters": {{"action": "update"}}}}

Команда: найди как приготовить пиццу
Результат:
{{"intent": "web_search", "parameters": {{"query": "как приготовить пиццу"}}}}

Команда: напомни вынести мусор вечером
Результат:
{{"intent": "set_reminder", "parameters": {{"reminder_text": "вынести мусор", "time_spec": "вечером"}}}}

Команда: будильник на 7 утра
Результат:
{{"intent": "set_alarm", "parameters": {{"time_spec": "7 утра"}}}}

Команда: какая погода?
Результат:
{{"intent": "unknown", "parameters": {{}}}}

Команда: {user_command}
Результат:
"""

# --- Функции ---

def get_nlu_from_ollama(user_command,
                        instruction_template=NLU_INSTRUCTION_TEMPLATE,
                        api_url=API_URL,
                        model_name=DEFAULT_MODEL_NAME,
                        timeout=90):
    """Отправляет команду в Ollama API и возвращает сырой текстовый ответ модели."""
    if not api_url:
        print("Ошибка: URL API Ollama не задан (проверьте OLLAMA_API_URL или константу DEFAULT_API_URL).")
        return None

    # Формируем полный промпт для модели
    full_instruction = instruction_template.format(user_command=user_command)

    # Параметры запроса к Ollama API
    payload = {
        "model": model_name,
        "prompt": full_instruction,
        "stream": False, # Получаем ответ целиком
        "options": {
            "temperature": 0.3, # Низкая температура для более предсказуемого JSON
            "repeat_penalty": 1.15,
            "num_predict": 150 # Ограничение длины ответа (подбирается)
        }
        # Убираем "raw": True - Ollama сам добавит системный промпт модели, если он есть
    }

    print(f"[NLU_PROCESSOR][DEBUG] Отправка запроса на {api_url} для модели '{model_name}'...")
    # print(f"[NLU_PROCESSOR][DEBUG] Payload: {payload}") # Раскомментировать для детальной отладки

    try:
        response = requests.post(api_url, json=payload, timeout=timeout)
        response.raise_for_status() # Проверка на HTTP ошибки (4xx, 5xx)

        data = response.json()

        if 'response' in data:
            result_text = data['response']
            print(f"[NLU_PROCESSOR][DEBUG] Сырой ответ от модели: '{result_text}'")
            return result_text.strip()
        else:
            print(f"[NLU_PROCESSOR][ERROR] Поле 'response' не найдено в ответе API.")
            print(f"[NLU_PROCESSOR][DEBUG] Полный ответ: {data}")
            return "" # Возвращаем пустую строку при ошибке структуры ответа

    except requests.exceptions.Timeout:
        print(f"Ошибка сети: Превышен таймаут ({timeout} сек) при запросе к {api_url}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Ошибка сети при запросе к Ollama API: {e}")
        return None
    except json.JSONDecodeError:
        print(f"Ошибка: Ответ от API Ollama не является валидным JSON.")
        print(f"Код статуса: {response.status_code}")
        print(f"Начало ответа: {response.text[:200]}...")
        return None
    except Exception as e:
        print(f"Неизвестная ошибка при вызове Ollama API: {e}")
        return None


def extract_json_from_response(response_text):
    """Извлекает первый валидный JSON объект из строки ответа NLU."""
    if not response_text:
        return None

    # Убираем лишние пробелы и возможные артефакты до/после JSON
    text_to_parse = response_text.strip()

    # Ищем начало и конец первого JSON объекта
    start_index = text_to_parse.find('{')
    end_index = text_to_parse.rfind('}')

    if start_index != -1 and end_index != -1 and end_index > start_index:
        json_str = text_to_parse[start_index:end_index + 1]
        print(f"[NLU_PROCESSOR][DEBUG] Пытаемся распарсить JSON: {json_str}")
        try:
            parsed_json = json.loads(json_str)
            # Простая проверка на ожидаемую структуру (наличие intent)
            if "intent" in parsed_json:
                 print(f"[NLU_PROCESSOR][DEBUG] JSON успешно распарсен.")
                 return parsed_json
            else:
                 print(f"[NLU_PROCESSOR][WARN] В распарсенном JSON отсутствует ключ 'intent': {parsed_json}")
                 return None # Считаем невалидным, если нет intent
        except json.JSONDecodeError:
            print(f"[NLU_PROCESSOR][ERROR] Ошибка парсинга JSON строки: {json_str}")
            # Можно попробовать более "грязный" парсинг, если модель часто добавляет текст после JSON,
            # но пока оставим так для строгости.
            return None
        except Exception as e:
             print(f"[NLU_PROCESSOR][ERROR] Неизвестная ошибка при парсинге JSON: {e}")
             return None
    else:
        print(f"[NLU_PROCESSOR][WARN] Не удалось найти валидный JSON объект в строке: '{text_to_parse}'")
        return None