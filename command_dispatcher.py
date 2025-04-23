# Финальная версия: command_dispatcher.py (Рабочая + Debug)
# -*- coding: utf-8 -*-

import utils
# Импортируем обработчики из папки intent_handlers
from intent_handlers import handle_manage_app
# TODO: Импортировать обработчики для close_app, add_alias и т.д., когда они будут готовы
# from intent_handlers import handle_close_app # Пример - пока нет этого файла
# from intent_handlers import handle_add_alias # Пример - пока нет этого файла

# Глобальная переменная для алиасов
APP_ALIASES = {}

# Словарь маршрутизации интентов к функциям-обработчикам
INTENT_HANDLERS = {
    "manage_app": handle_manage_app.handle, # Связываем интент с функцией handle из нужного модуля
    # TODO: Добавить другие интенты и их обработчики
    # "close_app": handle_close_app.handle, # ОШИБКА: Не нужно, так как close - это action внутри manage_app
    # "add_alias": handle_add_alias.handle,
    # "manage_system": handle_manage_system.handle,
    # ... и т.д.
}

def initialize_dispatcher():
    """Загружает алиасы при старте."""
    global APP_ALIASES
    APP_ALIASES = utils.load_aliases()
    if APP_ALIASES:
        print(f"[DISPATCHER][INFO] Алиасы успешно загружены ({len(APP_ALIASES)} шт).")
    else:
        print("[DISPATCHER][WARN] Алиасы не загружены или файл пуст.")

# --- Функция СНОВА принимает debug_mode ---
def dispatch_command(parsed_nlu, debug_mode=False):
    """
    Маршрутизирует команду к обработчику ИЛИ выводит NLU результат в дебаг-режиме.
    """
    if not parsed_nlu or "intent" not in parsed_nlu:
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
        # Показываем нормализацию для релевантных интентов
        if intent == "manage_app" and "app_name" in parameters:
             app_name_raw = parameters.get("app_name")
             canonical_name = APP_ALIASES.get(app_name_raw.lower(), app_name_raw.lower())
             print(f"[DISPATCHER_DEBUG] Нормализованное имя app_name (для справки): '{canonical_name}'")
        elif intent == "add_alias" and "alias_name" in parameters:
             alias_name = parameters.get("alias_name")
             print(f"[DISPATCHER_DEBUG] Имя алиаса (для справки): '{alias_name.lower()}'")
        print("="*52)
        return f"ДЕБАГ: Распознано: интент='{intent}', параметры={parameters}"
    # --- КОНЕЦ РЕЖИМА ДЕБАГА ---

    # --- РАБОЧИЙ РЕЖИМ (блок else) ---
    else:
        print(f"[DISPATCHER][INFO] Маршрутизация интента: '{intent}'")
        handler_function = INTENT_HANDLERS.get(intent)

        if handler_function:
            try:
                # Вызываем найденный обработчик, передавая ему параметры и алиасы
                # Обработчик сам разберется с параметрами (включая 'action')
                return handler_function(parameters, APP_ALIASES) # Передаем параметры и алиасы

            except Exception as e:
                print(f"[DISPATCHER][ERROR] Ошибка при выполнении обработчика для интента '{intent}': {e}")
                import traceback
                traceback.print_exc()
                return f"Произошла ошибка при выполнении команды '{intent}'."
        else:
            # Обработчик не найден
            print(f"[DISPATCHER][WARN] Обработчик для интента '{intent}' не найден.")
            # Можно добавить обработку 'unknown' интента здесь, если нужно
            return "Извините, я пока не умею обрабатывать такую команду."

# --- Инициализация при импорте ---
initialize_dispatcher()