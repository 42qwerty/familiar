# File: nlu_processor.py
# -*- coding: utf-8 -*-

import json
import requests
import os

# --- Constants (Can be moved to config later) ---
# Use environment variable for URL if available, otherwise default
DEFAULT_API_URL = 'http://localhost:11434/api/generate'
API_URL = os.environ.get('OLLAMA_API_URL', DEFAULT_API_URL)
DEFAULT_MODEL_NAME = "mistral" # Default model

# --- MODIFIED NLU INSTRUCTION TEMPLATE (v5) ---
# Changed 'add_alias' parameters from alias_name/canonical_name to entity1/entity2

NLU_INSTRUCTION_TEMPLATE = """Тебе будет предоставлена пользовательская команда. Твоя задача - извлечь из нее основное намерение (intent) и параметры (parameters), включая конкретное действие (action), если оно применимо, и вернуть результат ТОЛЬКО в виде чистого JSON объекта.

Возможные намерения (intent) и действия (action):

* intent: manage_app
    * action: "open" (Запустить или сфокусировать приложение)
    * action: "close" (Закрыть приложение)
    * Обязательный параметр: "app_name".
* intent: manage_system
    * action: "reboot" (Перезагрузить)
    * action: "update" (Обновить)
    * action: "shutdown" (Выключить)
    * Параметры не требуются.
* intent: manage_sound
    * action: "up" (Громче)
    * action: "down" (Тише)
    * action: "mute" (Выключить звук)
    * action: "unmute" (Включить звук)
    * Опциональный параметр: "amount".
* intent: add_alias
    * Параметры: "entity1", "entity2". (Извлеки две сопоставляемые сущности из строки вида: "сохрани у себя entity1 это entity2" или "свяжи X и Y", "пусть A будет B", "запомни C как D". Важно: не включай сами глаголы 'свяжи', 'запомни' или слова 'это', 'пусть', 'будет', 'себе', 'у себя' и т.д.)
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

Команда: убей процесс телеграм
Результат:
{{"intent": "manage_app", "parameters": {{"action": "close", "app_name": "Firefox"}}}}

Команда: запомни тг это telegram
Результат:
{{"intent": "add_alias", "parameters": {{"entity1": "тг", "entity2": "telegram"}}}}

Команда: свяжи браузер и google-chrome
Результат:
{{"intent": "add_alias", "parameters": {{"entity1": "браузер", "entity2": "google-chrome"}}}}

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

# --- Functions ---

def get_nlu_from_ollama(user_command,
                        instruction_template=NLU_INSTRUCTION_TEMPLATE,
                        api_url=API_URL,
                        model_name=DEFAULT_MODEL_NAME,
                        timeout=90):
    """Sends the command to the Ollama API and returns the raw text response."""
    if not api_url:
        print("Error: Ollama API URL is not set (check OLLAMA_API_URL or DEFAULT_API_URL constant).")
        return None

    # Format the full prompt for the model
    full_instruction = instruction_template.format(user_command=user_command)

    # Parameters for the Ollama API request
    payload = {
        "model": model_name,
        "prompt": full_instruction,
        "stream": False, # Get the full response at once
        "options": {
            "temperature": 0.3, # Low temperature for more predictable JSON
            "repeat_penalty": 1.15,
            "num_predict": 150 # Limit response length (adjust as needed)
        }
        # Removed "raw": True - Ollama will handle model's system prompt if it exists
    }

    print(f"[NLU_PROCESSOR][DEBUG] Sending request to {api_url} for model '{model_name}'...")
    # print(f"[NLU_PROCESSOR][DEBUG] Payload: {payload}") # Uncomment for detailed debugging

    try:
        response = requests.post(api_url, json=payload, timeout=timeout)
        response.raise_for_status() # Check for HTTP errors (4xx, 5xx)

        data = response.json()

        if 'response' in data:
            result_text = data['response']
            print(f"[NLU_PROCESSOR][DEBUG] Raw response from model: '{result_text}'")
            return result_text.strip()
        else:
            print(f"[NLU_PROCESSOR][ERROR] 'response' field not found in API response.")
            print(f"[NLU_PROCESSOR][DEBUG] Full response: {data}")
            return "" # Return empty string on response structure error

    except requests.exceptions.Timeout:
        print(f"Network Error: Timeout exceeded ({timeout} sec) while requesting {api_url}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Network Error during Ollama API request: {e}")
        return None
    except json.JSONDecodeError:
        print(f"Error: Ollama API response is not valid JSON.")
        print(f"Status Code: {response.status_code}")
        print(f"Response start: {response.text[:200]}...")
        return None
    except Exception as e:
        print(f"Unknown error during Ollama API call: {e}")
        return None


def extract_json_from_response(response_text):
    """Extracts the first valid JSON object from the NLU response string."""
    if not response_text:
        return None

    # Trim whitespace and potential artifacts before/after JSON
    text_to_parse = response_text.strip()

    # Find the start and end of the first JSON object
    start_index = text_to_parse.find('{')
    end_index = text_to_parse.rfind('}')

    if start_index != -1 and end_index != -1 and end_index > start_index:
        json_str = text_to_parse[start_index:end_index + 1]
        print(f"[NLU_PROCESSOR][DEBUG] Attempting to parse JSON: {json_str}")
        try:
            parsed_json = json.loads(json_str)
            # Simple check for expected structure (presence of 'intent')
            if "intent" in parsed_json:
                 print(f"[NLU_PROCESSOR][DEBUG] JSON parsed successfully.")
                 return parsed_json
            else:
                 print(f"[NLU_PROCESSOR][WARN] Parsed JSON missing 'intent' key: {parsed_json}")
                 return None # Consider invalid if no intent
        except json.JSONDecodeError:
            print(f"[NLU_PROCESSOR][ERROR] Failed to parse JSON string: {json_str}")
            # Could try more lenient parsing if model often adds text after JSON,
            # but keeping it strict for now.
            return None
        except Exception as e:
             print(f"[NLU_PROCESSOR][ERROR] Unknown error during JSON parsing: {e}")
             return None
    else:
        print(f"[NLU_PROCESSOR][WARN] Could not find a valid JSON object in the string: '{text_to_parse}'")
        return None

