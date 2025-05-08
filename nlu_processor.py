# File: nlu_processor.py
# -*- coding: utf-8 -*-

import json
import requests
import os

# --- Constants (Can be moved to config later) ---
DEFAULT_API_URL = os.environ.get('OLLAMA_API_URL', 'http://localhost:11434/api/generate')
DEFAULT_MODEL_NAME = "mistral" # Default model for all LLM calls
DEFAULT_TIMEOUT = 90 # Default timeout for API requests

# --- NLU INSTRUCTION TEMPLATE (v8 - из предыдущих шагов) ---
# (Этот шаблон остается здесь, так как он нужен для get_nlu_intent_from_text)
NLU_INSTRUCTION_TEMPLATE = """Тебе будет предоставлена пользовательская команда. Твоя задача - извлечь из нее основное намерение (intent) и параметры (parameters), включая конкретное действие (action), если оно применимо, и вернуть результат ТОЛЬКО в виде чистого JSON объекта.

**Важно: при извлечении параметров `entity1` и `entity2` для интента `add_alias`, не включай в них глаголы действия (например, 'сохрани', 'свяжи', 'запомни') или лишние уточняющие слова ('себе', 'у', 'это', 'будет'). Извлекай только сами имена или псевдонимы.**
Извлеки **псевдоним (обычно короткое имя X)** и **каноническое имя команды (обычно Y)** из фраз, устанавливающих связь, например: "X это Y", "свяжи X и Y", "пусть X будет Y", "запомни X как Y". Важно: не включай сами глаголы 'свяжи', 'запомни' или слова 'это', 'пусть', 'будет', 'себе', 'у себя' и т.д.)

Возможные намерения (intent) и действия (action):

* intent: manage_app
    * action: "open" (Запустить или сфокусировать приложение)
    * action: "close" (Закрыть приложение)
    * Обязательный параметр: "app_name".
* intent: manage_system
    * action: "reboot" (Перезагрузить)
    * action: "update" (Обновить систему - запуск apt update && apt upgrade -y && apt dist-upgrade -y)
    * action: "shutdown" (Выключить)
    * action: "uptime" (Показать время работы системы)
    * Параметры не требуются.
* intent: manage_sound
    * action: "up" (Громче)
    * action: "down" (Тише)
    * action: "mute" (Выключить звук)
    * action: "unmute" (Включить звук)
    * Опциональный параметр: "amount".
* intent: add_alias
    * Параметры: "entity1", "entity2".
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
{{"intent": "add_alias", "parameters": {{"entity1": "тг", "entity2": "telegram"}}}}

Команда: свяжи браузер и google-chrome
Результат:
{{"intent": "add_alias", "parameters": {{"entity1": "браузер", "entity2": "google-chrome"}}}}

Команда: сохрани тг это telegram
Результат:
{{"intent": "add_alias", "parameters": {{"entity1": "тг", "entity2": "telegram"}}}}

Команда: запомни у себя, редактор это subl
Результат:
{{"intent": "add_alias", "parameters": {{"entity1": "редактор", "entity2": "subl"}}}}

Команда: пусть фаер будет firefox
Результат:
{{"intent": "add_alias", "parameters": {{"entity1": "фаер", "entity2": "firefox"}}}}

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

Команда: перезагрузи компьютер
Результат:
{{"intent": "manage_system", "parameters": {{"action": "reboot"}}}}

Команда: выключи комп
Результат:
{{"intent": "manage_system", "parameters": {{"action": "shutdown"}}}}

Команда: обнови систему
Результат:
{{"intent": "manage_system", "parameters": {{"action": "update"}}}}

Команда: аптайм
Результат:
{{"intent": "manage_system", "parameters": {{"action": "uptime"}}}}

Команда: сколько система работает?
Результат:
{{"intent": "manage_system", "parameters": {{"action": "uptime"}}}}

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

# --- Вспомогательная функция для вызова LLM ---
def _call_ollama_api(full_prompt_text: str,
                     model_name: str = DEFAULT_MODEL_NAME,
                     api_url: str = DEFAULT_API_URL,
                     timeout: int = DEFAULT_TIMEOUT) -> str | None:
    """
    Внутренняя функция для отправки запроса к Ollama API.
    Принимает уже полностью сформированный текст инструкции (prompt).
    Возвращает текстовый ответ от модели или None в случае ошибки.
    """
    if not api_url:
        print("[NLU_PROCESSOR][ERROR] Ollama API URL is not set.")
        return None

    payload = {
        "model": model_name,
        "prompt": full_prompt_text,
        "stream": False,
        "options": {
            "temperature": 0.3, # Низкая температура для NLU и более предсказуемых ответов
            "repeat_penalty": 1.15,
            "num_predict": 200 # Лимит длины ответа (можно настроить)
        }
    }

    print(f"[NLU_PROCESSOR][DEBUG] Sending request to {api_url} for model '{model_name}'...")
    # print(f"[NLU_PROCESSOR][DEBUG] Payload prompt (first 100 chars): {full_prompt_text[:100]}...") # Для отладки

    try:
        response = requests.post(api_url, json=payload, timeout=timeout)
        response.raise_for_status()
        data = response.json()

        if 'response' in data:
            result_text = data['response'].strip()
            print(f"[NLU_PROCESSOR][DEBUG] Raw response from model: '{result_text}'")
            return result_text
        else:
            print(f"[NLU_PROCESSOR][ERROR] 'response' field not found in API response. Full response: {data}")
            return None
    except requests.exceptions.Timeout:
        print(f"[NLU_PROCESSOR][ERROR] Network Error: Timeout ({timeout}s) for {api_url}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"[NLU_PROCESSOR][ERROR] Network Error during Ollama API request: {e}")
        return None
    except json.JSONDecodeError:
        print(f"[NLU_PROCESSOR][ERROR] Ollama API response is not valid JSON. Status: {response.status_code}, Text: {response.text[:200]}...")
        return None
    except Exception as e:
        print(f"[NLU_PROCESSOR][ERROR] Unknown error during Ollama API call: {e}")
        return None

# --- Функция для извлечения NLU (интент + параметры) ---
def get_nlu_intent_from_text(user_command: str,
                             model_name: str = DEFAULT_MODEL_NAME,
                             api_url: str = DEFAULT_API_URL,
                             timeout: int = DEFAULT_TIMEOUT) -> str | None:
    """
    Отправляет команду пользователя и NLU_INSTRUCTION_TEMPLATE в LLM для извлечения интента.
    Возвращает сырой текстовый ответ от модели (ожидается JSON).
    """
    if not user_command:
        print("[NLU_PROCESSOR][WARN] Empty user command received for NLU.")
        return None

    full_nlu_prompt = NLU_INSTRUCTION_TEMPLATE.format(user_command=user_command)
    return _call_ollama_api(full_nlu_prompt, model_name, api_url, timeout)

# --- НОВАЯ ФУНКЦИЯ: Для генерации ответа LLM на основе готовой инструкции ---
def generate_llm_response_from_template(full_prompt_text: str,
                                        model_name: str = DEFAULT_MODEL_NAME,
                                        api_url: str = DEFAULT_API_URL,
                                        timeout: int = DEFAULT_TIMEOUT) -> str | None:
    """
    Отправляет уже полностью сформированный текст инструкции (prompt) в LLM.
    Используется для генерации ответов, когда инструкция формируется в другом месте (например, в familiar.py).
    Возвращает текстовый ответ от модели.
    """
    if not full_prompt_text:
        print("[NLU_PROCESSOR][WARN] Empty prompt text received for LLM response generation.")
        return None
    return _call_ollama_api(full_prompt_text, model_name, api_url, timeout)

# --- Функция для извлечения JSON из ответа NLU ---
def extract_json_from_response(response_text: str | None) -> dict | None:
    """Извлекает первый валидный JSON объект из строки ответа NLU."""
    if not response_text:
        return None

    text_to_parse = response_text.strip()
    start_index = text_to_parse.find('{')
    end_index = text_to_parse.rfind('}')

    if start_index != -1 and end_index != -1 and end_index > start_index:
        json_str = text_to_parse[start_index:end_index + 1]
        # print(f"[NLU_PROCESSOR][DEBUG] Attempting to parse JSON: {json_str}") # Можно раскомментировать для детальной отладки
        try:
            parsed_json = json.loads(json_str)
            if "intent" in parsed_json or "status" in parsed_json: # Проверяем наличие ключевых полей
                 print(f"[NLU_PROCESSOR][DEBUG] JSON parsed successfully.")
                 return parsed_json
            else:
                 print(f"[NLU_PROCESSOR][WARN] Parsed JSON missing 'intent' or 'status' key: {parsed_json}")
                 return None
        except json.JSONDecodeError:
            print(f"[NLU_PROCESSOR][ERROR] Failed to parse JSON string: {json_str}")
            return None
        except Exception as e:
             print(f"[NLU_PROCESSOR][ERROR] Unknown error during JSON parsing: {e}")
             return None
    else:
        print(f"[NLU_PROCESSOR][WARN] Could not find a valid JSON object in the string: '{text_to_parse}'")
        return None

# --- Старая функция get_nlu_from_ollama теперь переименована в get_nlu_intent_from_text ---
# Для обратной совместимости, если где-то еще используется старое имя, можно добавить алиас:
# get_nlu_from_ollama = get_nlu_intent_from_text
