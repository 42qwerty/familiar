# Файл: intent_handlers/handle_manage_app.py
# -*- coding: utf-8 -*-

import shutil # Для shutil.which
import time   # Для time.sleep

# Импортируем наши низкоуровневые функции действий
# Используем точку, так как manage_app_action.py теперь в той же папке actions,
# а этот файл в intent_handlers. Python найдет через sys.path.
# Если будут проблемы, вернемся к относительным или настроим PYTHONPATH.
# UPDATE: Правильный импорт будет абсолютным от корня проекта, если запускать через python -m
# или если главная папка в sys.path
from actions import manage_app_action # Имя файла изменено

def handle(parameters, aliases):
    """
    Обрабатывает интент manage_app: запускает/фокусирует или закрывает приложение.
    parameters: Словарь с параметрами от NLU (должен содержать 'action' и 'app_name').
    aliases: Словарь с алиасами приложений.
    Возвращает строку с результатом для пользователя.
    """
    action = parameters.get("action")
    app_name_raw = parameters.get("app_name")

    if not action or not app_name_raw:
        print("[HANDLER_MANAGE_APP][ERROR] Отсутствует 'action' или 'app_name' в параметрах.")
        return "Не поняла, что сделать с приложением или каким именно."

    # Нормализуем имя здесь, внутри хендлера
    canonical_name = aliases.get(app_name_raw.lower(), app_name_raw.lower())
    print(f"[HANDLER_MANAGE_APP][INFO] Действие: '{action}', Приложение: '{canonical_name}' (raw: '{app_name_raw}')")

    # --- Логика для action: "open" ---
    if action == "open":
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
                    time.sleep(1.5)
                    activated_successfully = manage_app_action.activate_window_by_class(canonical_name)
                    if activated_successfully: return f"Приложение '{canonical_name}' запущено и активировано."
                    else: return f"Приложение '{canonical_name}' запущено (но окно не активировано)."
                else: return f"Не удалось запустить '{canonical_name}'."
            else: return f"Приложение '{canonical_name}' не найдено в системе."

    # --- Логика для action: "close" ---
    elif action == "close":
        # Здесь нам понадобится функция close_application_by_name
        # Предположим, она тоже будет в manage_app_action для простоты сейчас
        # Либо нужно будет создать actions/close_app_action.py и импортировать оттуда
        try:
            # Заглушка - нужно импортировать реальную функцию закрытия!
            # from actions.manage_app_action import close_application_by_name # Пример
            # if close_application_by_name(canonical_name):
            #     return f"Попытка закрыть '{canonical_name}' выполнена."
            # else:
            #     return f"Не удалось закрыть '{canonical_name}' или оно не было запущено."
            print(f"[HANDLER_MANAGE_APP][TODO] Вызов закрытия для '{canonical_name}' еще не реализован!")
            return f"Команда закрыть '{canonical_name}' получена, но функция еще не подключена." # Заглушка
        except ImportError:
             print(f"[HANDLER_MANAGE_APP][ERROR] Функция закрытия не найдена! Нужно реализовать и импортировать.")
             return f"Ошибка: функция закрытия приложения не найдена."
        except Exception as e:
            print(f"[HANDLER_MANAGE_APP][ERROR] Ошибка при попытке закрыть '{canonical_name}': {e}")
            return f"Ошибка при закрытии '{canonical_name}'."

    # --- Обработка неизвестного action ---
    else:
        print(f"[HANDLER_MANAGE_APP][WARN] Неизвестное действие '{action}' для интента 'manage_app'.")
        return f"Неизвестное действие '{action}' для приложения."