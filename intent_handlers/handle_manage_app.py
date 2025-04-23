# Файл: intent_handlers/handle_manage_app.py
# -*- coding: utf-8 -*-

import shutil # Для shutil.which
import time   # Для time.sleep

# Используем абсолютные импорты от корня проекта
from actions import manage_app_action
from actions import close_app_action

def handle(parameters, aliases):
    """
    Обрабатывает интент manage_app: запускает/фокусирует или закрывает приложение
    в зависимости от параметра 'action'.
    parameters: Словарь с параметрами от NLU (должен содержать 'action' и 'app_name').
    aliases: Словарь с алиасами приложений.
    Возвращает строку с результатом для пользователя.
    """
    action = parameters.get("action")
    app_name_raw = parameters.get("app_name")

    if not action or not app_name_raw:
        print("[HANDLER_MANAGE_APP][ERROR] Отсутствует 'action' или 'app_name' в параметрах.")
        return "Не поняла, что сделать с приложением или каким именно."

    # Нормализуем имя приложения
    canonical_name = aliases.get(app_name_raw.lower(), app_name_raw.lower())
    print(f"[HANDLER_MANAGE_APP][INFO] Действие: '{action}', Приложение: '{canonical_name}' (raw: '{app_name_raw}')")

    # --- Логика ветвления по действию ---
    if action == "open":
        # Логика "запустить или сфокусировать"
        running_pid = manage_app_action.find_running_process_pid(canonical_name)
        activated_successfully = False

        if running_pid:
            print(f"[HANDLER_MANAGE_APP][INFO] Приложение '{canonical_name}' уже запущено. Активируем...")
            activated_successfully = manage_app_action.activate_window_by_class(canonical_name)
            if activated_successfully: return f"Окно '{canonical_name}' активировано."
            else: return f"Приложение '{canonical_name}' запущено, но не удалось активировать окно."
        else:
            executable_path = shutil.which(canonical_name)
            if executable_path:
                print(f"[HANDLER_MANAGE_APP][INFO] Запускаем '{canonical_name}'...")
                if manage_app_action.run_application(executable_path):
                    print(f"[HANDLER_MANAGE_APP][INFO] Ждем и пытаемся активировать...")
                    time.sleep(1.5) # Пауза, чтобы окно успело появиться
                    activated_successfully = manage_app_action.activate_window_by_class(canonical_name)
                    if activated_successfully: return f"Приложение '{canonical_name}' запущено и активировано."
                    else: return f"Приложение '{canonical_name}' запущено (но окно не активировано)."
                else: return f"Не удалось запустить '{canonical_name}'."
            else: return f"Приложение '{canonical_name}' не найдено в системе."

    elif action == "close":
        # Логика закрытия приложения
        print(f"[HANDLER_MANAGE_APP][INFO] Вызов закрытия для '{canonical_name}'...")
        if close_app_action.close_application_by_name(canonical_name):
             return f"Попытка закрыть '{canonical_name}' выполнена." # Функция залогирует детали
        else:
             return f"Не удалось закрыть '{canonical_name}' или оно не было запущено." # Функция залогировала детали

    # --- Обработка неизвестного action ---
    else:
        print(f"[HANDLER_MANAGE_APP][WARN] Неизвестное действие '{action}' для интента 'manage_app'.")
        return f"Неизвестное действие '{action}' для приложения."