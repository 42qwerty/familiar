# Исправленная версия файла: command_dispatcher.py
# -*- coding: utf-8 -*-

import shutil
import time

# Импортируем утилиты и обработчики интентов
import utils
from intent_handlers import handle_manage_app # Импортируем первый обработчик
# TODO: Добавить импорты для handle_close_app, handle_add_alias и т.д.

# Глобальная переменная для алиасов
APP_ALIASES = {}

# Словарь маршрутизации интентов к функциям-обработчикам
INTENT_HANDLERS = {
    # Используем 'run_app' как ключ, как договорились
    "run_app": handle_manage_app.handle,
    # --- Заглушки для других интентов ---
    # "close_app": handle_close_app.handle,
    # "add_alias": handle_add_alias.handle,
    # ... и т.д. ...
}

def initialize_dispatcher():
    """Загружает алиасы при старте."""
    global APP_ALIASES
    APP_ALIASES = utils.load_aliases()
    if APP_ALIASES:
        print(f"[DISPATCHER][INFO] Алиасы успешно загружены ({len(APP_ALIASES)} шт).")
    else:
        print("[DISPATCHER][WARN] Алиасы не загружены или файл пуст.")

# --- Функция теперь снова принимает debug_mode ---
def dispatch_command(parsed_nlu, debug_mode=False):
    """
    Маршрутизирует команду к обработчику ИЛИ выводит NLU результат в дебаг-режиме.
    """
    global APP_ALIASES

    if not parsed_nlu or "intent" not in parsed_nlu:
        # Добавим префикс DEBUG/ERROR в зависимости от режима
        log_prefix = "[DISPATCHER_DEBUG]" if debug_mode else "[DISPATCHER][ERROR]"
        print(f"{log_prefix} Получены невалидные NLU данные.")
        return "Не удалось распознать команду."

    intent = parsed_nlu.get("intent")
    parameters = parsed_nlu.get("parameters", {})
    print(f"[DISPATCHER][INFO] Получен интент: '{intent}', параметры: {parameters}")

    # --- РЕЖИМ ДЕБАГА ---
    if debug_mode:
        print("="*20 + " DEBUG MODE " + "="*20)
        print(f"[DISPATCHER_DEBUG] Распознанный интент: {intent}")
        print(f"[DISPATCHER_DEBUG] Распознанные параметры: {parameters}")
        # Нормализуем имя даже в дебаге, чтобы видеть, как оно будет передано
        if intent in ["run_app", "close_app", "add_alias"] and "app_name" in parameters:
             app_name_raw = parameters.get("app_name")
             canonical_name = APP_ALIASES.get(app_name_raw.lower(), app_name_raw.lower())
             print(f"[DISPATCHER_DEBUG] Нормализованное имя (для справки): '{canonical_name}'")
        print("="*52)
        return f"ДЕБАГ: Распознано: интент='{intent}', параметры={parameters}"
    # --- КОНЕЦ РЕЖИМА ДЕБАГА ---

    # --- РАБОЧИЙ РЕЖИМ (блок else) ---
    else:
        print(f"[DISPATCHER][INFO] Маршрутизация интента: '{intent}'")
        handler_function = INTENT_HANDLERS.get(intent)

        if handler_function:
            try:
                # --- Логика вызова обработчиков ---
                if intent == "run_app": # Ключ 'run_app'
                     app_name_raw = parameters.get("app_name")
                     if not app_name_raw: return "Не поняла, какое приложение нужно."
                     # Нормализация имени ПЕРЕД вызовом обработчика
                     canonical_name = APP_ALIASES.get(app_name_raw.lower(), app_name_raw.lower())
                     # Вызываем обработчик с нормализованным именем
                     return handler_function(canonical_name) # handle_manage_app ожидает canonical_name

                # TODO: Добавить elif для close_app, add_alias и т.д., передавая нужные параметры
                # elif intent == "close_app":
                #    app_name_raw = parameters.get("app_name")
                #    if not app_name_raw: return "Не поняла, какое приложение закрыть."
                #    canonical_name = APP_ALIASES.get(app_name_raw.lower(), app_name_raw.lower())
                #    return handler_function(canonical_name) # handle_close_app ожидает canonical_name
                # elif intent == "add_alias":
                #    alias_name = parameters.get("alias_name")
                #    canonical_name_param = parameters.get("canonical_name")
                #    if not alias_name or not canonical_name_param: return "Не поняла, какой алиас и для какого приложения добавить."
                #    # Передаем оба параметра, обработчик сам обновит глобальные алиасы
                #    return handler_function(alias_name, canonical_name_param)

                else:
                     # Для других интентов (когда они будут) передаем весь словарь параметров
                     return handler_function(parameters) # Пример

            except Exception as e:
                print(f"[DISPATCHER][ERROR] Ошибка при выполнении обработчика для интента '{intent}': {e}")
                import traceback
                traceback.print_exc()
                return f"Произошла ошибка при выполнении команды '{intent}'."
        else:
            # Обработчик не найден
            print(f"[DISPATCHER][WARN] Обработчик для интента '{intent}' не найден.")
            unknown_handler = INTENT_HANDLERS.get("unknown")
            if unknown_handler:
                return unknown_handler(parameters)
            else:
                return "Извините, я пока не умею обрабатывать такую команду."

# --- Инициализация при импорте ---
initialize_dispatcher()