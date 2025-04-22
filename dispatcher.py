#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import requests
import os
import subprocess # Для wmctrl и запуска приложений
import shutil     # Для which
import psutil     # Для проверки запущенных процессов

# --- Константы ---
# Путь к файлу алиасов
ALIASES_FILE = 'app_aliases.json'

# URL API Ollama
API_URL = 'http://localhost:11434/api/generate'

# Шаблон инструкции для NLU модели (ПОЛНАЯ ВЕРСИЯ)
NLU_INSTRUCTION_TEMPLATE = """Проанализируй текстовую команду пользователя и верни результат анализа в формате JSON, содержащий намерение (intent) и параметры (parameters). В ответе должен быть ТОЛЬКО JSON объект и БОЛЬШЕ НИЧЕГО. Ориентируйся на примеры:

Пример 1:
Команда: Запусти браузер Хром
Результат: {{"intent": "run_app", "parameters": {{"app_name": "Chrome"}}}}

Пример 2:
Команда: Открой пожалуйста Телеграм
Результат: {{"intent": "run_app", "parameters": {{"app_name": "Telegram"}}}}

Пример 3:
Команда: Я хочу запустить Дискорд
Результат: {{"intent": "run_app", "parameters": {{"app_name": "Discord"}}}}

Пример 4:
Команда: run firefox
Результат: {{"intent": "run_app", "parameters": {{"app_name": "Firefox"}}}}

Пример 5:
Команда: Запусти Visual Studio Code
Результат: {{"intent": "run_app", "parameters": {{"app_name": "Visual Studio Code"}}}}

Пример 6:
Команда: открой мне Google Chrome, пожалуйста
Результат: {{"intent": "run_app", "parameters": {{"app_name": "Google Chrome"}}}}

Теперь проанализируй следующую команду:
Команда: {user_command}
Результат:"""

# --- Функции ---

def load_aliases(filepath=ALIASES_FILE):
    """Загружает словарь алиасов из JSON-файла."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            aliases = json.load(f)
            return {k.lower(): v for k, v in aliases.items()}
    except FileNotFoundError:
        print(f"Предупреждение: Файл алиасов '{filepath}' не найден.")
        return {}
    except json.JSONDecodeError:
        print(f"Ошибка: Не удалось прочитать JSON из файла алиасов '{filepath}'.")
        return {}
    except Exception as e:
        print(f"Неизвестная ошибка при загрузке алиасов: {e}")
        return {}

def get_nlu_from_mistral(user_command, instruction_template=NLU_INSTRUCTION_TEMPLATE, api_url=API_URL, model_name="mistral"):
    """Отправляет команду NLU модели через Ollama API и возвращает ее текстовый ответ."""
    if not api_url:
        print("Ошибка: URL API не задан в константах.")
        return None
    full_instruction = instruction_template.format(user_command=user_command)
    payload = {
        "model": model_name,
        "prompt": full_instruction, # Используем ПОЛНУЮ инструкцию
        "stream": False,
        "options": { "temperature": 0.3, "repeat_penalty": 1.15, "num_predict": 150 }
    }
    print(f"[DEBUG] Отправка запроса на {api_url} для модели '{model_name}'...")
    try:
        response = requests.post(api_url, json=payload, timeout=90)
        response.raise_for_status()
        data = response.json()
        if 'response' in data:
            result_text = data['response']
            print(f"[DEBUG] Сырой ответ от модели: '{result_text}'")
            return result_text.strip()
        else:
            print(f"[DEBUG] Ошибка: Поле 'response' не найдено в ответе Ollama.")
            print(f"[DEBUG] Полный ответ: {data}")
            return ""
    except requests.exceptions.RequestException as e:
        print(f"Ошибка сети при обращении к API: {e}")
        return None
    except json.JSONDecodeError:
        print(f"Ошибка: API вернул не JSON ответ. Код: {response.status_code}. Ответ: {response.text[:200]}...")
        return None
    except Exception as e:
        print(f"Неизвестная ошибка при запросе к API: {e}")
        return None

def extract_json_from_response(response_text):
    """Пытается извлечь первый валидный JSON объект из текста."""
    if not response_text: return None
    text_to_parse = response_text.strip()
    try:
        start_index = text_to_parse.find('{'); end_index = text_to_parse.rfind('}')
        if start_index != -1 and end_index != -1 and end_index > start_index:
            json_str = text_to_parse[start_index:end_index+1]; print(f"[DEBUG] Парсим JSON: {json_str}"); return json.loads(json_str)
        else: print(f"Предупреждение: Не найден JSON в ответе '{text_to_parse}'"); return None
    except json.JSONDecodeError: print(f"Ошибка: Не удалось распарсить JSON: {json_str}"); return None
    except Exception as e: print(f"Неизвестная ошибка при извлечении JSON: {e}"); return None

def run_application(app_path_or_name):
    """Запускает приложение (без подтверждения)."""
    print(f"[ACTION] Запуск приложения: '{app_path_or_name}'")
    try:
        if os.name == 'nt':
           DETACHED_PROCESS = 0x00000008; CREATE_NEW_PROCESS_GROUP = 0x00000200
           subprocess.Popen([app_path_or_name], creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP, close_fds=True)
        else:
           subprocess.Popen([app_path_or_name], start_new_session=True)
        return True
    except FileNotFoundError: print(f"Ошибка запуска: Файл '{app_path_or_name}' не найден."); return False
    except Exception as e: print(f"Ошибка при запуске '{app_path_or_name}': {e}"); return False

def find_running_process(app_name):
    """Ищет запущенный процесс по имени/cmdline/exe. Возвращает PID или None."""
    app_name_lower = app_name.lower(); base_name = os.path.basename(app_name_lower)
    for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'exe']):
        try:
            proc_info = proc.info
            # Гибкое сравнение
            if proc_info['name'] and base_name in proc_info['name'].lower(): print(f"[DEBUG] psutil: Найдено по имени: PID={proc_info['pid']}, Name={proc_info['name']}"); return proc_info['pid']
            if proc_info['cmdline'] and any(app_name_lower in part.lower() for part in proc_info['cmdline']): print(f"[DEBUG] psutil: Найдено по cmdline: PID={proc_info['pid']}, Cmdline={proc_info['cmdline']}"); return proc_info['pid']
            if proc_info['exe'] and app_name_lower in proc_info['exe'].lower(): print(f"[DEBUG] psutil: Найдено по exe: PID={proc_info['pid']}, Exe={proc_info['exe']}"); return proc_info['pid']
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess): continue
        except Exception as e: print(f"[DEBUG] psutil: Ошибка доступа к процессу {proc.pid if proc else 'N/A'}: {e}"); continue
    print(f"[DEBUG] psutil: Процесс '{app_name}' не найден."); return None

def activate_window_by_class(window_class_or_name):
    """Пытается активировать окно по WM_CLASS или имени с помощью wmctrl -xa."""
    print(f"[ACTION] Попытка активации окна по классу/имени: '{window_class_or_name}' (wmctrl -xa)")
    try:
        # check=False, т.к. ненулевой код возврата - это ожидаемый результат (не найдено), а не ошибка
        result = subprocess.run(['wmctrl', '-xa', window_class_or_name], capture_output=True, text=True, check=False, encoding='utf-8')
        if result.returncode == 0:
            print(f"[ACTION] Окно для '{window_class_or_name}' успешно активировано (wmctrl вернул 0).")
            return True
        else:
            print(f"[DEBUG] Не удалось активировать '{window_class_or_name}'. wmctrl вернул {result.returncode}.")
            # print(f"[DEBUG] wmctrl stdout: {result.stdout.strip()}") # Обычно пусто при неуспехе
            # print(f"[DEBUG] wmctrl stderr: {result.stderr.strip()}") # Может содержать инфо об ошибке
            return False
    except FileNotFoundError: print("ОШИБКА: команда 'wmctrl' не найдена. Установите wmctrl."); return False
    except Exception as e: print(f"Неизвестная ОШИБКА при 'wmctrl -xa': {e}"); return False

# --- Основной цикл ---
if __name__ == "__main__":
    # Проверка наличия psutil при старте
    try:
        import psutil
    except ImportError:
        print("ОШИБКА: Модуль 'psutil' не найден. Пожалуйста, установите его: pip install psutil")
        exit(1) # Выходим, если psutil не установлен

    aliases = load_aliases()
    if aliases: print(f"Загружены алиасы: {len(aliases)} шт.")
    print("Введите команду или 'выход' для завершения.")

    while True:
        command = input(">>> Команда: ")
        if command.lower() in ['выход', 'exit', 'quit']: print("Завершение работы."); break
        if not command: continue

        # 1. NLU -> 2. JSON Extract -> 3. Params
        nlu_response_text = get_nlu_from_mistral(command)
        if not nlu_response_text: continue
        parsed_nlu = extract_json_from_response(nlu_response_text)
        if not parsed_nlu: continue
        print(f"Распознано NLU: {parsed_nlu}")

        intent = parsed_nlu.get("intent"); parameters = parsed_nlu.get("parameters", {}); app_name_raw = parameters.get("app_name")

        if intent in ["run_app", "open_app"] and app_name_raw:
            app_name_lower = app_name_raw.lower()
            canonical_name = aliases.get(app_name_lower, app_name_lower)
            print(f"Нормализованное имя для поиска/активации: '{canonical_name}'")

            # 4. Проверяем, запущен ли уже процесс
            running_pid = find_running_process(canonical_name) # PID нужен только как флаг "запущен/не запущен"

            if running_pid:
                # 4а. Если запущен, пытаемся активировать по классу/имени
                print(f"Приложение '{canonical_name}' уже запущено. Пытаемся активировать окно...")
                if activate_window_by_class(canonical_name):
                    print(f"Окно приложения '{canonical_name}' успешно активировано.")
                else:
                    print(f"Не удалось активировать окно для '{canonical_name}' с помощью 'wmctrl -xa'.")
                    # Можно добавить генерацию ответа Мистралем "Приложение уже запущено, но не могу переключиться"
            else:
                # 4б. Если не запущен, ищем и запускаем
                executable_path = shutil.which(canonical_name)
                if executable_path:
                    print(f"Найден исполняемый файл: {executable_path}")
                    if run_application(executable_path): print(f"Приложение '{canonical_name}' запущено.")
                    else: print(f"Не удалось запустить '{canonical_name}'.")
                else:
                    print(f"Ошибка: Приложение '{canonical_name}' не найдено в системе (в PATH).")
        else:
             print("Не удалось распознать команду запуска приложения в ответе NLU.")